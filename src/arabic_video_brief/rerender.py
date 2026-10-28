from datetime import datetime
import json
import logging
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from .config import Settings, get_settings
from .media import download_youtube, render_video
from .utils import write_json
from .ending import resolve_ending_question, resolve_v2_footer

logger = logging.getLogger(__name__)


def rerender_folder(folder_path: Path | str, settings: Settings | None = None) -> dict[str, Any]:
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    manifest_path = folder / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json not found in: {folder}")

    if settings is None:
        settings = get_settings()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest.get("source")
    if not source:
        raise ValueError("manifest.json has no 'source' field")

    metadata = manifest.get("metadata", {})
    post_title = manifest.get("post_title")
    title_path = folder / "post-title.txt"
    if title_path.is_file():
        post_title = title_path.read_text(encoding="utf-8").strip()

    is_v2 = (folder / "summary-pages.json").exists() or manifest.get("render", {}).get("version") == "v2"
    question_file = folder / "ending-question-ar.txt"
    footer_file = folder / "ending-text-ar.txt"
    legacy_file = folder / "conclusion-ar.txt"
    summary_file = folder / "summary-ar.txt"
    resolver = resolve_v2_footer if is_v2 else resolve_ending_question
    question = resolver(
        {"ending_text_ar": footer_file.read_text(encoding="utf-8") if footer_file.exists() else "",
         "ending_question_ar": question_file.read_text(encoding="utf-8") if question_file.exists() else "",
         "conclusion": legacy_file.read_text(encoding="utf-8") if legacy_file.exists() else ""},
        metadata, summary_file.read_text(encoding="utf-8") if summary_file.exists() else " ".join(manifest.get("pages_ar", [])), settings,
    )
    question_file.write_text(question + "\n", encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="avbrief-rerender-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        print(f"[Rerender] Downloading source clip for: {source} ...")
        downloaded = download_youtube(source, temp_dir, download_seconds=40.0)
        local_video = Path(downloaded["video_path"])
        thumbnail = Path(downloaded["thumbnail_path"]) if downloaded.get("thumbnail_path") else None

        output_video_path = folder / "brief.mp4"

        if is_v2:
            print("[Rerender] Re-rendering V2 format (50.2s with 8s question ending and outro voiceover)...")
            from .v2.editorial import V2EditorialPackage, HookCandidate
            from .v2.renderer import render_v2_video

            pages_file = folder / "summary-pages.json"
            pages_data = json.loads(pages_file.read_text(encoding="utf-8")) if pages_file.exists() else []
            pages = [p["text"] for p in pages_data] if pages_data else []
            bounds = settings.v2_page_boundaries
            for i, page in enumerate(pages_data):
                page["timing"] = f"{bounds[i]:.1f}s - {bounds[i + 1]:.1f}s"
            if pages_data:
                write_json(pages_file, pages_data)
                manifest["pages"] = pages_data

            hook_ar = (folder / "hook-ar.txt").read_text(encoding="utf-8").strip() if (folder / "hook-ar.txt").exists() else post_title
            conclusion_ar = question
            legacy_file.write_text(question + "\n", encoding="utf-8")
            cta_ar = (folder / "cta-ar.txt").read_text(encoding="utf-8").strip() if (folder / "cta-ar.txt").exists() else ""
            summary_ar = (folder / "summary-ar.txt").read_text(encoding="utf-8").strip() if (folder / "summary-ar.txt").exists() else ""

            hook_cand = HookCandidate(
                display_hook=hook_ar,
                highlight_phrase="",
                tts_text="",
                category="",
                scores={},
                total_score=1.0,
                explanation="",
            )
            editorial = V2EditorialPackage(
                post_title_ar=post_title or "",
                summary_ar=summary_ar,
                pages=pages,
                hook=hook_cand,
                conclusion_ar=conclusion_ar,
                conclusion_highlights=[],
                cta_ar=cta_ar,
                cta_description="",
                creative_plan={},
            )

            hook_audio_path = folder / "hook-voice.mp3"
            selected_clip = manifest.get("selected_clip", {"start_seconds": 0.0, "end_seconds": settings.v2_page_boundaries[-1] - settings.hook_duration})

            render_details = render_v2_video(
                source=local_video,
                thumbnail=thumbnail,
                editorial=editorial,
                selected_clip=selected_clip,
                output=output_video_path,
                settings=settings,
                hook_audio_path=hook_audio_path if hook_audio_path.exists() else None,
                metadata=metadata,
            )
        else:
            print("[Rerender] Re-rendering V1 format (38s with 8s question ending and outro voiceover)...")
            pages_ar = manifest.get("pages_ar")
            if not pages_ar or len(pages_ar) < 2:
                summary_path = folder / "summary-ar.txt"
                if summary_path.exists():
                    from .utils import split_summary
                    summary_text = summary_path.read_text(encoding="utf-8").strip()
                    p1, p2 = split_summary(summary_text, settings.page_min_words, settings.page_max_words)
                    pages_ar = [p1, p2]
                else:
                    raise ValueError("Cannot find pages_ar or summary-ar.txt for V1 render")

            selected_clip = manifest.get("selected_clip", {"start_seconds": 0.0, "end_seconds": 15.0})

            render_details = render_video(
                source=local_video,
                thumbnail=thumbnail,
                page_one=pages_ar[0],
                page_two=pages_ar[1],
                selected_clip=selected_clip,
                output=output_video_path,
                settings=settings,
                metadata=metadata,
                post_title=post_title,
                ending_question=question,
            )

    if output_video_path.is_file():
        today_str = datetime.now().strftime("%Y%m%d")
        clean_slug = re.sub(r"[^\w\s-]", "", post_title or metadata.get("title", "")).strip()
        clean_slug = re.sub(r"[-\s]+", "-", clean_slug)
        short_slug = clean_slug[:40].strip("-")
        capcut_name = f"CapCut_1080p_{today_str}_{short_slug}.mp4"
        staged_video_path = folder / capcut_name
        for old_vid in folder.glob("CapCut_1080p_*.mp4"):
            if old_vid != staged_video_path:
                old_vid.unlink(missing_ok=True)
        if output_video_path != staged_video_path:
            shutil.move(str(output_video_path), str(staged_video_path))
        output_video_path = staged_video_path

    manifest["render"] = render_details
    manifest["ending_question_ar"] = question
    manifest.setdefault("files", {})["ending_question_ar"] = str(question_file)
    manifest.setdefault("files", {})["video"] = str(output_video_path)
    manifest["video_path"] = str(output_video_path)
    if is_v2:
        footer_file.write_text(question + "\n", encoding="utf-8")
        manifest["ending_text_ar"] = question
        manifest.setdefault("files", {})["ending_text_ar"] = str(footer_file)
        manifest.setdefault("conclusion", {})["text"] = question
    write_json(manifest_path, manifest)
    try:
        print(f"[Rerender] Successfully updated {output_video_path.name}")
    except Exception:
        pass
    return {
        "status": "success",
        "folder": str(folder),
        "video": str(output_video_path),
        "render": render_details,
    }
