from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

from .config import Settings, get_settings
from .media import download_youtube, render_video
from .utils import write_json

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

    with tempfile.TemporaryDirectory(prefix="avbrief-rerender-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        print(f"[Rerender] Downloading source clip for: {source} ...")
        downloaded = download_youtube(source, temp_dir, download_seconds=40.0)
        local_video = Path(downloaded["video_path"])
        thumbnail = Path(downloaded["thumbnail_path"]) if downloaded.get("thumbnail_path") else None

        output_video_path = folder / "brief.mp4"

        if is_v2:
            print("[Rerender] Re-rendering V2 format (36.5s with 8s conclusion and outro voiceover)...")
            from .v2.editorial import V2EditorialPackage, HookCandidate
            from .v2.renderer import render_v2_video

            pages_file = folder / "summary-pages.json"
            pages_data = json.loads(pages_file.read_text(encoding="utf-8")) if pages_file.exists() else []
            pages = [p["text"] for p in pages_data] if pages_data else []

            hook_ar = (folder / "hook-ar.txt").read_text(encoding="utf-8").strip() if (folder / "hook-ar.txt").exists() else post_title
            conclusion_ar = (folder / "conclusion-ar.txt").read_text(encoding="utf-8").strip() if (folder / "conclusion-ar.txt").exists() else ""
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
            selected_clip = manifest.get("selected_clip", {"start_seconds": 0.0, "end_seconds": 28.5})

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
            print("[Rerender] Re-rendering V1 format (28s with 8s CTA and outro voiceover)...")
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
            )

    manifest["render"] = render_details
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
