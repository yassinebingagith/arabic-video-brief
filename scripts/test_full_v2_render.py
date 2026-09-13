import subprocess
from pathlib import Path
import tempfile
import sys
import json
from PIL import Image

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.media import download_youtube
from arabic_video_brief.v2.renderer import render_v2_video
from arabic_video_brief.v2.editorial import V2EditorialPackage, HookCandidate

settings = get_settings()
folder = Path("outputs/The-Hidden-Psychology-Of-Highly-Sensitive-People---Dr-Sasha-Hamdani-MB_5DKSmOls/v2")
manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
source = manifest["source"]

temp = Path(tempfile.mkdtemp())
print("Downloading source...")
downloaded = download_youtube(source, temp, download_seconds=40.0)

local_video = Path(downloaded["video_path"])
thumbnail = Path(downloaded["thumbnail_path"]) if downloaded.get("thumbnail_path") else None
print("Thumbnail path:", thumbnail, "exists:", thumbnail.exists() if thumbnail else False)

pages_data = json.loads((folder / "summary-pages.json").read_text(encoding="utf-8"))
pages = [p["text"] for p in pages_data]

hook_ar = (folder / "hook-ar.txt").read_text(encoding="utf-8").strip()
conclusion_ar = (folder / "conclusion-ar.txt").read_text(encoding="utf-8").strip()
cta_ar = (folder / "cta-ar.txt").read_text(encoding="utf-8").strip()
summary_ar = (folder / "summary-ar.txt").read_text(encoding="utf-8").strip()
post_title = (folder / "post-title.txt").read_text(encoding="utf-8").strip()

editorial = V2EditorialPackage(
    post_title_ar=post_title,
    summary_ar=summary_ar,
    pages=pages,
    hook=HookCandidate(display_hook=hook_ar, highlight_phrase="", tts_text="", category="", scores={}, total_score=1.0, explanation=""),
    conclusion_ar=conclusion_ar,
    conclusion_highlights=[],
    cta_ar=cta_ar,
    cta_description="",
    creative_plan={},
)

out_test = Path("scratch/test_v2_render.mp4")
render_v2_video(
    source=local_video,
    thumbnail=thumbnail,
    editorial=editorial,
    selected_clip={"start_seconds": 0.0, "end_seconds": 28.5},
    output=out_test,
    settings=settings,
    hook_audio_path=folder / "hook-voice.mp3",
    metadata=manifest.get("metadata", {}),
)

print("Render complete! Checking frame at 1.0s...")
f1 = Path("scratch/test_v2_render_1s.png")
subprocess.run(["ffmpeg", "-y", "-ss", "00:00:01.0", "-i", str(out_test), "-vframes", "1", str(f1)], capture_output=True)
im = Image.open(f1)
print("Pixel at (540, 200):", im.getpixel((540, 200)))
