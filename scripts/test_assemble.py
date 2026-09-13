import subprocess
from pathlib import Path
import tempfile
import sys
from PIL import Image

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.v2.renderer import render_v2_summary_page, render_v2_conclusion_page
from arabic_video_brief.media import render_top_overlay

settings = get_settings()
temp = Path(tempfile.mkdtemp())

# Check how V2 brief.mp4 currently in outputs/ was built
# Let's inspect brief.mp4 by probing streams and duration
v2_brief = Path("outputs/The-Hidden-Psychology-Of-Highly-Sensitive-People---Dr-Sasha-Hamdani-MB_5DKSmOls/v2/brief.mp4")
res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(v2_brief)], capture_output=True, text=True)
print("v2_brief duration:", res.stdout.strip())

# Extract 5 frames across the first 3 seconds: 0.1s, 0.5s, 1.0s, 2.0s, 2.4s, 2.6s, 3.0s
for sec in (0.1, 0.5, 1.0, 2.0, 2.4, 2.6, 3.0):
    f_path = temp / f"frame_{sec}.png"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{sec}", "-i", str(v2_brief), "-vframes", "1", str(f_path)], capture_output=True)
    if f_path.exists():
        im = Image.open(f_path)
        # Check pixel at (540, 200) - in the top panel above the badge
        pix = im.getpixel((540, 200))
        print(f"Time {sec}s pixel (540, 200):", pix)
