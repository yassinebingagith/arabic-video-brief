from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Ensure project src is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from arabic_video_brief.config import get_settings
from arabic_video_brief.media import download_youtube, render_video, infer_category
from arabic_video_brief.utils import slugify, source_hash, write_json, word_count


def process_video_brief(
    source_url: str,
    page_one_ar: str,
    page_two_ar: str,
    post_title: str,
    post_desc: str,
    category_hint: str = "",
    output_root: Path | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    out_dir = output_root or settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    temp_context = tempfile.TemporaryDirectory(prefix="avbrief-")
    work_dir = Path(temp_context.name)

    try:
        print(f"Downloading source media: {source_url} ...")
        downloaded = download_youtube(source_url, work_dir)
        local_video = Path(downloaded["video_path"])
        thumbnail = Path(downloaded["thumbnail_path"]) if downloaded.get("thumbnail_path") else None
        title = str(downloaded.get("title") or "YouTube video")
        identifier = str(downloaded.get("id") or source_hash(source_url))
        metadata = {key: value for key, value in downloaded.items() if key not in {"video_path", "thumbnail_path"}}

        selected = {
            "start_seconds": 0.0,
            "end_seconds": min(15.0, float(metadata.get("duration") or 15.0)),
            "reason": "First fifteen seconds requested by user",
            "focal_x": 0.5,
            "focal_y": 0.5,
        }

        full_summary = f"{page_one_ar.strip()}\n\n{page_two_ar.strip()}"
        total_words = word_count(full_summary)

        folder_name = f"{slugify(title)}-{identifier}"
        item_dir = out_dir / folder_name
        item_dir.mkdir(parents=True, exist_ok=True)

        final_path = item_dir / "brief.mp4"
        transcript_path = item_dir / "transcript.json"
        summary_path = item_dir / "summary-ar.txt"
        post_title_path = item_dir / "post-title.txt"
        post_desc_path = item_dir / "post-description.txt"
        manifest_path = item_dir / "manifest.json"

        print(f"Rendering 20-second 9:16 vertical brief with Arabic typography ...")
        render_details = render_video(
            local_video, thumbnail, page_one_ar.strip(), page_two_ar.strip(), selected, final_path, settings, metadata=metadata, post_title=post_title
        )

        write_json(transcript_path, {"source_language": "en", "segments": []})
        summary_path.write_text(full_summary + "\n", encoding="utf-8")
        post_title_path.write_text(post_title.strip() + "\n", encoding="utf-8")
        post_desc_path.write_text(post_desc.strip() + "\n", encoding="utf-8")

        manifest = {
            "status": "success",
            "source": source_url,
            "metadata": metadata,
            "model": "antigravity-gemini-3.7-flash",
            "post_title": post_title,
            "post_description": post_desc,
            "summary_words": total_words,
            "pages_ar": [page_one_ar.strip(), page_two_ar.strip()],
            "clip_candidates": [],
            "selected_clip": selected,
            "render": render_details,
            "files": {
                "video": str(final_path),
                "transcript": str(transcript_path),
                "summary": str(summary_path),
                "post_title": str(post_title_path),
                "post_description": str(post_desc_path),
                "manifest": str(manifest_path),
            },
        }
        write_json(manifest_path, manifest)
        print(f"Render completed successfully: {final_path}")
        return manifest
    finally:
        temp_context.cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_single.py <config.json>")
        sys.exit(1)
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    res = process_video_brief(**config)
    print(json.dumps(res, ensure_ascii=False, indent=2))
