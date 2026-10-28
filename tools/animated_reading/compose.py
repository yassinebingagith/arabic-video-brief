"""Replace the page region in the reference; copy its already mixed audio."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from arabic_video_brief.render_runtime import load_render_runtime

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--folder", type=Path, required=True)
args = ap.parse_args()
folder = args.folder.resolve()
data = json.loads((folder / "Project/page-data.json").read_text(encoding="utf-8"))
runtime = load_render_runtime()
duration = data.get("total_duration", data["duration"] + 8)
probe = json.loads(subprocess.check_output([runtime["FFPROBE_BIN"], "-v", "error", "-show_entries", "format=duration", "-of", "json", str(folder / "Source/reference.mp4")]))
if abs(float(probe["format"]["duration"])-duration)>.05:
    raise ValueError("Reference timing differs from the page composition. Use extend_reference.py to prepare a matching reference first.")
target = folder / "Preview.mp4"
if target.exists():
    raise ValueError("Preserve existing preview; use a fresh output directory.")
subprocess.run([
    runtime["FFMPEG_BIN"], "-hide_banner", "-loglevel", "warning",
    "-i", str(folder / "Source/reference.mp4"), "-i", str(folder / "reading-pages.mp4"),
    "-filter_complex", f"[0:v][1:v]overlay=0:780:enable='lt(t,{data['duration']})':eof_action=pass:repeatlast=0,format=yuv420p[v]",
    "-map", "[v]", "-map", "0:a:0", "-c:v", "libx264", "-preset", "veryfast",
    "-crf", "20", "-g", "1", "-r", str(data["fps"]), "-frames:v", str(round(duration*data["fps"])), "-t", str(duration),
    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(target)
], check=True)
print(target)
