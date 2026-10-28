"""Replace the page region in the reference; copy its already mixed audio."""
import argparse
import json
import subprocess
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--folder", type=Path, required=True)
args = ap.parse_args()
folder = args.folder.resolve()
data = json.loads((folder / "Project/page-data.json").read_text(encoding="utf-8"))
runtime = json.loads(Path("F:/hyperframes-v3/config/local-runtime.json").read_text())
target = folder / "Preview.mp4"
if target.exists():
    raise ValueError("Preserve existing preview; use a fresh output directory.")
subprocess.run([
    runtime["FFMPEG_BIN"], "-hide_banner", "-loglevel", "warning",
    "-i", str(folder / "Source/reference.mp4"), "-i", str(folder / "reading-pages.mp4"),
    "-filter_complex", f"[0:v][1:v]overlay=0:780:enable='lt(t,{data['duration']})':eof_action=pass:repeatlast=0,format=yuv420p[v]",
    "-map", "[v]", "-map", "0:a:0", "-c:v", "libx264", "-preset", "veryfast",
    "-crf", "20", "-g", "1", "-r", "30", "-frames:v", "1266", "-t", "42.2",
    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(target)
], check=True)
print(target)
