from __future__ import annotations

import argparse
import json
from pathlib import Path

from arabic_video_brief.config import get_settings
from arabic_video_brief.media import render_video
from arabic_video_brief.utils import slugify, split_summary, write_json


def parse_json3(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    segments: list[dict[str, object]] = []
    for event in payload.get("events", []):
        text = "".join(part.get("utf8", "") for part in event.get("segs", [])).replace("\n", " ").strip()
        if not text:
            continue
        start = float(event.get("tStartMs", 0)) / 1000
        duration = float(event.get("dDurationMs", 0)) / 1000
        segments.append({
            "start_seconds": start,
            "end_seconds": start + duration,
            "text": text,
            "language": "ar",
        })
    return segments


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an Arabic brief from public caption analysis")
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--item-dir", type=Path)
    args = parser.parse_args()

    work = args.work_dir.resolve()
    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    info = json.loads((work / "source.info.json").read_text(encoding="utf-8"))
    source = work / "source.mp4"
    thumbnail = work / "source.webp"
    captions = work / "source.ar-orig.json3"
    summary = str(analysis["summary_ar"]).strip()
    settings = get_settings()
    page_one, page_two = split_summary(summary, settings.page_min_words, settings.page_max_words)
    selected = {
        "start_seconds": 0.0,
        "end_seconds": min(10.0, float(info.get("duration") or 10.0)),
        "reason": "First ten seconds requested by user",
        "focal_x": 0.5,
        "focal_y": 0.5,
    }

    output_slug = slugify(str(analysis.get("output_slug") or info.get("title") or "video"))
    item_dir = args.item_dir.resolve() if args.item_dir else args.output_root.resolve() / f"{output_slug}-{info.get('id', 'unknown')}"
    item_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = item_dir / "transcript.json"
    summary_path = item_dir / "summary-ar.txt"
    final_path = item_dir / "brief.mp4"
    manifest_path = item_dir / "manifest.json"
    if captions.exists():
        transcript = {"source_language": "ar", "segments": parse_json3(captions)}
    else:
        transcript = json.loads(Path(analysis["transcript_path"]).read_text(encoding="utf-8"))
    write_json(transcript_path, transcript)
    summary_path.write_text(summary + "\n", encoding="utf-8")
    metadata = {
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "view_count": info.get("view_count"),
        "upload_date": info.get("upload_date"),
    }
    render = render_video(source, thumbnail, page_one, page_two, selected, final_path, settings, metadata=metadata)
    manifest = {
        "status": "success",
        "source": analysis["source"],
        "metadata": metadata,
        "model": "caption-fallback (Gemini quota exhausted)",
        "summary_words": len(summary.split()),
        "pages_ar": [page_one, page_two],
        "clip_candidates": [],
        "selected_clip": selected,
        "render": render,
        "files": {"video": str(final_path), "transcript": str(transcript_path), "summary": str(summary_path), "manifest": str(manifest_path)},
    }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
