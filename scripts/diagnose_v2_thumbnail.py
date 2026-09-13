import tempfile
from pathlib import Path
import sys
from PIL import Image

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.media import download_youtube, render_source_card, find_ffmpeg, _extract_frame

settings = get_settings()
temp = Path(tempfile.mkdtemp())
downloaded = download_youtube("https://www.youtube.com/watch?v=MB_5DKSmOls", temp, download_seconds=5)

print("Downloaded keys:", list(downloaded.keys()))
thumbnail_path = Path(downloaded["thumbnail_path"]) if downloaded.get("thumbnail_path") else None
print("Thumbnail path:", thumbnail_path)
print("Thumbnail exists:", thumbnail_path.exists() if thumbnail_path else False)

if thumbnail_path and thumbnail_path.exists():
    im = Image.open(thumbnail_path)
    print("Thumbnail format:", im.format, "size:", im.size, "mode:", im.mode)
    
    card_path = temp / "source-card.png"
    render_source_card(thumbnail_path, downloaded, card_path, settings)
    print("Card exists:", card_path.exists())
    card_im = Image.open(card_path)
    print("Card format:", card_im.format, "size:", card_im.size, "bbox:", card_im.getbbox())
    # Sample center pixel
    print("Card pixel center:", card_im.getpixel((540, 380)))
