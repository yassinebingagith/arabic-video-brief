import subprocess
from pathlib import Path
import tempfile
import sys
from PIL import Image

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.media import download_youtube, render_source_card, render_top_overlay

settings = get_settings()
temp = Path(tempfile.mkdtemp())
downloaded = download_youtube("https://www.youtube.com/watch?v=MB_5DKSmOls", temp, download_seconds=5)

source_card = temp / "source-card.png"
render_source_card(Path(downloaded["thumbnail_path"]), downloaded, source_card, settings)

top_overlay = temp / "top-overlay.png"
render_top_overlay(downloaded, top_overlay, settings)

top_path = temp / "top_v2.mp4"
open_dur = 2.5
v_stream_dur = 2.0
cta_dur = 2.0
fps = 30
d_open = int(open_dur * fps)
d_cta = int(cta_dur * fps)

cmd = [
    "ffmpeg", "-hide_banner",
    "-loop", "1", "-t", f"{open_dur:.1f}", "-i", str(source_card),
    "-ss", "0.000", "-i", str(downloaded["video_path"]),
    "-loop", "1", "-t", "6.5", "-i", str(top_overlay),
    "-loop", "1", "-t", f"{cta_dur:.1f}", "-i", str(source_card),
    "-filter_complex",
    f"[0:v]scale={settings.width}:{settings.top_height}:force_original_aspect_ratio=increase,crop={settings.width}:{settings.top_height},"
    f"zoompan=z='min(zoom+0.0008,1.06)':d={d_open}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={settings.width}x{settings.top_height}:fps={fps}[c1_zoom];"
    f"[c1_zoom][2:v]overlay=0:0:format=auto,fps={fps},trim=duration={open_dur:.1f},setpts=PTS-STARTPTS,setsar=1[card1];"
    f"[1:v]scale={settings.width}:{settings.top_height}:force_original_aspect_ratio=increase,crop={settings.width}:{settings.top_height},setsar=1[vclip];"
    f"[vclip][2:v]overlay=0:0:format=auto,fps={fps},trim=duration={v_stream_dur:.1f},setpts=PTS-STARTPTS,setsar=1[vstream];"
    f"[3:v]scale={settings.width}:{settings.top_height}:force_original_aspect_ratio=increase,crop={settings.width}:{settings.top_height},"
    f"zoompan=z='min(zoom+0.00025,1.06)':d={d_cta}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={settings.width}x{settings.top_height}:fps={fps}[c2_zoom];"
    f"[c2_zoom][2:v]overlay=0:0:format=auto,fps={fps},trim=duration={cta_dur:.1f},setpts=PTS-STARTPTS,setsar=1[card2];"
    "[card1][vstream][card2]concat=n=3:v=1:a=0[top]",
    "-map", "[top]", "-t", "6.5", "-an", "-c:v", "libx264", "-preset", "veryfast",
    "-crf", "20", "-pix_fmt", "yuv420p", "-y", str(top_path),
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg returncode:", res.returncode)
if res.returncode != 0:
    print("FFmpeg error:", res.stderr)

# Extract frame at 1.0s (during card1)
subprocess.run(["ffmpeg", "-y", "-ss", "00:00:01.0", "-i", str(top_path), "-vframes", "1", str(temp / "frame_top_1s.png")], capture_output=True)
im = Image.open(temp / "frame_top_1s.png")
print("Top frame at 1s color (540, 200):", im.getpixel((540, 200)))
print("Top frame at 1s color (540, 600):", im.getpixel((540, 600)))
im.save("scratch/test_top_1s.png")
