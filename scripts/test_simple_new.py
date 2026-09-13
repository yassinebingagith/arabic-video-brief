import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings

s = get_settings()
url = f"{s.vyceai_base_url}/chat/completions"
headers = {
    "Authorization": f"Bearer {s.vyceai_api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Let's test streaming with gpt-5.6-new
payload = {
    "model": "gpt-5.6-new",
    "messages": [
        {"role": "user", "content": "Write a 1-sentence summary of Carl Jung in Arabic."}
    ],
    "stream": False
}

req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
try:
    print("Testing gpt-5.6-new 1 sentence...")
    with urllib.request.urlopen(req, timeout=60) as resp:
        print("Success:", resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print("Exception:", e)
