import subprocess
from pathlib import Path
import tempfile
from PIL import Image

temp = Path(tempfile.mkdtemp())
img = Image.new("RGB", (1080, 760), color=(255, 0, 0)) # bright red
img.save(temp / "test_card.png")

cmd = [
    "ffmpeg", "-hide_banner",
    "-loop", "1", "-t", "2.5", "-i", str(temp / "test_card.png"),
    "-filter_complex",
    "[0:v]scale=1080:760:force_original_aspect_ratio=increase,crop=1080:760,"
    "zoompan=z='min(zoom+0.0008,1.06)':d=75:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x760:fps=30[c1_zoom]",
    "-map", "[c1_zoom]", "-t", "2.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", str(temp / "out.mp4")
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Returncode:", res.returncode)
print("Stderr:", res.stderr[-500:] if res.stderr else "")

# Extract frame from out.mp4
subprocess.run(["ffmpeg", "-y", "-ss", "00:00:01.0", "-i", str(temp / "out.mp4"), "-vframes", "1", str(temp / "frame1.png")], capture_output=True)
if (temp / "frame1.png").exists():
    im = Image.open(temp / "frame1.png")
    print("Frame 1 color:", im.getpixel((100, 100)))
