import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.media import download_youtube

t = Path(tempfile.mkdtemp())
d = download_youtube("https://www.youtube.com/watch?v=MB_5DKSmOls", t, download_seconds=5)
print("thumbnail_path:", d.get("thumbnail_path"))
print("all files:", list(t.glob("*")))
