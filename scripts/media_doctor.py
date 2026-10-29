"""Install/check portable media binaries without an API key or browser."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from arabic_video_brief.media_tools import check_media_tools

if __name__=="__main__":
    print(json.dumps(check_media_tools(),indent=2))
