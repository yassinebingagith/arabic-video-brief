from __future__ import annotations

import json
import logging
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from ..config import Settings
from ..media import download_youtube, find_ffmpeg
from ..pipeline import (
    _retry_delay,
    _with_retries,
    generate_post_description,
    generate_post_title,
)
from ..utils import redact, slugify, source_hash, write_json, youtube_video_id
from ..youtube import fetch_video_details
from .editorial import build_v2_editorial_package
from .renderer import render_v2_video
from .tts import generate_hook_tts

logger = logging.getLogger(__name__)


def process_source_v2(
    source: str,
    output_root: Path,
    settings: Settings,
    keep_work: bool = False,
    force: bool = False,
    no_tts: bool = False,
    analysis_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Processes a source into a V2 Arabic Video Brief (26.0s timeline):
    - Dedicated hook with optional ElevenLabs TTS narration (graceful fallback)
    - 4 sentence-aligned summary pages (35-40 words each)
    - Full-page conclusion & CTA with Capsule Fikr branding
    - Output files saved into isolated `outputs/<video-slug>/v2/` directory
    """
    output_root.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = find_ffmpeg()

    temp_context: tempfile.TemporaryDirectory[str] | None = None
    if keep_work:
        work_parent = output_root / "work"
        work_parent.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(prefix="avbrief-v2-", dir=work_parent))
    else:
        temp_context = tempfile.TemporaryDirectory(prefix="avbrief-v2-")
        work_dir = Path(temp_context.name)

    try:
        video_id = youtube_video_id(source)
        if video_id:
            downloaded = _with_retries(lambda: download_youtube(source, work_dir, download_seconds=45.0))
            local_video = Path(downloaded["video_path"])
            thumbnail = Path(downloaded["thumbnail_path"]) if downloaded.get("thumbnail_path") else None
            title = str(downloaded.get("title") or "YouTube video")
            identifier = str(downloaded.get("id") or video_id)
            metadata = {k: v for k, v in downloaded.items() if k not in {"video_path", "thumbnail_path"}}

            if settings.youtube_api_key:
                details = fetch_video_details(video_id, settings.youtube_api_key)
                if details and details.get("title"):
                    metadata["title"] = details["title"]
                    metadata["original_title"] = details.get("original_title")
                    title = details["title"]
                    if details.get("channel"):
                        metadata["channel"] = details["channel"]
                    if details.get("description"):
                        metadata["description"] = details["description"]
        else:
            local_video = Path(source).expanduser().resolve()
            if not local_video.is_file():
                raise ValueError("Source must be a public YouTube URL or an existing local video file")
            title = local_video.stem
            identifier = source_hash(str(local_video))
            thumbnail = next((p for p in (local_video.with_suffix(".jpg"), local_video.with_suffix(".png"), local_video.with_suffix(".webp")) if p.exists()), None)
            metadata = {"title": title, "id": identifier, "local_path": str(local_video)}

        slug = f"{slugify(title)}-{identifier}"
        parent_dir = output_root / slug
        v2_dir = parent_dir / "v2"

        if v2_dir.exists() and (v2_dir / "brief.mp4").exists() and not force:
            logger.info("V2 output folder already exists: %s. Use --force to overwrite.", v2_dir)
            manifest_p = v2_dir / "manifest.json"
            if manifest_p.exists():
                try:
                    return json.loads(manifest_p.read_text(encoding="utf-8"))
                except Exception:
                    pass

        v2_dir.mkdir(parents=True, exist_ok=True)

        # Stage 1: Base Analysis (140-160 words, 2 semantic halves)
        analysis = analysis_override
        if analysis is None and (parent_dir / "summary-ar.txt").exists():
            try:
                v1_sum = (parent_dir / "summary-ar.txt").read_text(encoding="utf-8").strip()
                if v1_sum and len(v1_sum) >= 100:
                    analysis = {
                        "summary_ar": v1_sum,
                        "post_title_ar": (parent_dir / "post-title.txt").read_text(encoding="utf-8").strip() if (parent_dir / "post-title.txt").exists() else metadata.get("title", ""),
                        "post_description": (parent_dir / "post-description.txt").read_text(encoding="utf-8").strip() if (parent_dir / "post-description.txt").exists() else "",
                    }
            except Exception:
                analysis = None

        actual_model = (
            settings.apinex_model
            if settings.llm_provider == "apinex"
            else (settings.vyceai_model if settings.llm_provider == "vyceai" else ("antigravity-brainstorm" if analysis_override else settings.gemini_model))
        )

        if analysis is None and settings.llm_provider == "apinex":
            from ..apinex import analyze_video_apinex
            try:
                analysis = _with_retries(lambda: analyze_video_apinex(source, local_video, settings, metadata=metadata), attempts=2)
                actual_model = settings.apinex_model
            except Exception as apx_err:
                logger.warning("APInex provider error (%s); falling back to Gemini.", apx_err)
                analysis = None
        elif analysis is None and settings.llm_provider == "vyceai":
            from ..vyceai import analyze_video_vyceai
            try:
                analysis = _with_retries(lambda: analyze_video_vyceai(source, local_video, settings, metadata=metadata), attempts=2)
                actual_model = settings.vyceai_model
            except Exception as vyce_err:
                logger.warning("VyceAI provider error (%s); falling back to Gemini.", vyce_err)
                analysis = None
        elif analysis is None and settings.llm_provider == "seekai":
            from ..seekai import analyze_video_seekai
            try:
                analysis = _with_retries(lambda: analyze_video_seekai(source, local_video, settings, metadata=metadata), attempts=1)
                actual_model = settings.seekai_model
            except Exception as seek_err:
                logger.warning("SeekAI provider error (%s); falling back to Gemini.", seek_err)
                analysis = None

        if analysis is None:
            from ..gemini import analyze_video
            analysis = _with_retries(lambda: analyze_video(source, local_video, settings, metadata=metadata))
            actual_model = settings.gemini_model

        # Stage 2: Editorial Package (4 pages, hook candidate selection, conclusion, CTA)
        editorial = build_v2_editorial_package(analysis, metadata, settings)

        # Post title and description
        post_title = generate_post_title(metadata, editorial.post_title_ar)
        post_description = generate_post_description(
            metadata,
            editorial.summary_ar,
            narrative_desc=analysis.get("post_description", ""),
        )

        # Stage 3: Hook Voiceover (ElevenLabs TTS with graceful fallback)
        hook_audio_path = v2_dir / "hook-voice.mp3"
        tts_result: dict[str, Any] = {"status": "skipped", "reason": "--no-tts specified"}
        if not no_tts:
            tts_result = generate_hook_tts(
                editorial.hook.tts_text or editorial.hook.display_hook,
                hook_audio_path,
                settings,
                ffmpeg_bin,
            )

        has_hook_audio = (tts_result.get("status") == "success" and hook_audio_path.exists())

        # Stage 4: Video Render (36.5 seconds)
        selected_clip = {
            "start_seconds": 0.0,
            "end_seconds": min(28.5, float(metadata.get("duration") or 28.5)),
            "reason": "Top panel video stream playback",
        }

        final_video_path = v2_dir / "brief.mp4"
        render_details = render_v2_video(
            source=local_video,
            thumbnail=thumbnail,
            editorial=editorial,
            selected_clip=selected_clip,
            output=final_video_path,
            settings=settings,
            hook_audio_path=hook_audio_path if has_hook_audio else None,
            metadata=metadata,
        )

        # Stage 5: Write Output Files
        summary_path = v2_dir / "summary-ar.txt"
        summary_path.write_text(editorial.summary_ar, encoding="utf-8")

        summary_pages_path = v2_dir / "summary-pages.json"
        pages_timings = [
            "0.0s - 9.0s",
            "9.0s - 15.5s",
            "15.5s - 22.0s",
            "22.0s - 28.5s",
        ]
        pages_payload = [
            {
                "page": i + 1,
                "timing": pages_timings[i],
                "words": len(page_text.split()),
                "text": page_text,
            }
            for i, page_text in enumerate(editorial.pages)
        ]
        write_json(summary_pages_path, pages_payload)

        post_title_path = v2_dir / "post-title.txt"
        post_title_path.write_text(post_title, encoding="utf-8")

        post_desc_path = v2_dir / "post-description.txt"
        post_desc_path.write_text(post_description, encoding="utf-8")

        hook_ar_path = v2_dir / "hook-ar.txt"
        hook_ar_path.write_text(editorial.hook.display_hook, encoding="utf-8")

        hook_tts_path = v2_dir / "hook-tts.txt"
        hook_tts_path.write_text(editorial.hook.tts_text, encoding="utf-8")

        conclusion_ar_path = v2_dir / "conclusion-ar.txt"
        conclusion_ar_path.write_text(editorial.conclusion_ar, encoding="utf-8")

        cta_ar_path = v2_dir / "cta-ar.txt"
        cta_ar_path.write_text(f"{editorial.cta_ar}\n{editorial.cta_description}", encoding="utf-8")

        creative_plan_path = v2_dir / "creative-plan.json"
        write_json(creative_plan_path, editorial.creative_plan)

        transcript_path = v2_dir / "transcript.json"
        write_json(transcript_path, metadata.get("transcript") or [])

        manifest_path = v2_dir / "manifest.json"
        manifest = {
            "status": "success",
            "version": "v2",
            "source": source,
            "output_dir": str(v2_dir),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": metadata,
            "model": actual_model,
            "post_title": post_title,
            "post_description": post_description,
            "hook": {
                "display": editorial.hook.display_hook,
                "highlight_phrase": editorial.hook.highlight_phrase,
                "category": editorial.hook.category,
                "tts_status": tts_result.get("status"),
                "tts_duration": tts_result.get("duration", 0.0),
            },
            "pages": pages_payload,
            "conclusion": {
                "text": editorial.conclusion_ar,
                "highlights": editorial.conclusion_highlights,
                "cta_save": editorial.cta_ar,
                "cta_description": editorial.cta_description,
            },
            "render": render_details,
            "files": {
                "video": str(final_video_path),
                "summary": str(summary_path),
                "summary_pages": str(summary_pages_path),
                "post_title": str(post_title_path),
                "post_description": str(post_desc_path),
                "hook_ar": str(hook_ar_path),
                "hook_tts": str(hook_tts_path),
                "hook_voice": str(hook_audio_path) if has_hook_audio else None,
                "conclusion_ar": str(conclusion_ar_path),
                "cta_ar": str(cta_ar_path),
                "creative_plan": str(creative_plan_path),
                "transcript": str(transcript_path),
                "manifest": str(manifest_path),
            },
        }
        write_json(manifest_path, manifest)
        return manifest
    finally:
        if temp_context is not None:
            temp_context.cleanup()


def run_batch_v2(
    sources: list[str],
    output_root: Path,
    settings: Settings,
    keep_work: bool = False,
    force: bool = False,
    no_tts: bool = False,
    analysis_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ..utils import deduplicate_sources
    unique_sources = deduplicate_sources(sources)
    results: list[dict[str, Any]] = []
    for src in unique_sources:
        try:
            res = process_source_v2(
                src,
                output_root,
                settings,
                keep_work=keep_work,
                force=force,
                no_tts=no_tts,
                analysis_override=analysis_override,
            )
            results.append(res)
        except Exception as error:
            results.append({
                "status": "failed",
                "version": "v2",
                "source": src,
                "error": redact(str(error), [settings.gemini_api_key, settings.youtube_api_key, settings.seekai_api_key, settings.vyceai_api_key, settings.elevenlabs_api_key]),
            })
    report = {
        "status": "complete",
        "version": "v2",
        "requested": len(sources),
        "unique": len(unique_sources),
        "succeeded": sum(item.get("status") == "success" for item in results),
        "failed": sum(item.get("status") == "failed" for item in results),
        "results": results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    write_json(output_root / "job-report.json", report)
    return report
