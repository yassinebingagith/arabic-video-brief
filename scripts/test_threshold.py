import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.vyceai import PROMPT

s = get_settings()
url = f"{s.vyceai_base_url}/chat/completions"
headers = {
    "Authorization": f"Bearer {s.vyceai_api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def test(label, model, text):
    payload = {"model": model, "messages": [{"role": "user", "content": text}], "temperature": 0.4}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read().decode("utf-8")
            print(f"[{label}] SUCCESS len={len(data)}")
    except urllib.error.HTTPError as e:
        print(f"[{label}] HTTP {e.code}: {e.read().decode('utf-8')[:100]}")
    except Exception as e:
        print(f"[{label}] Err: {e}")

# Check length threshold
for length in [500, 1000, 1500, 2000, 3000, 4000]:
    test(f"gpt-5.6-new len {length}", "gpt-5.6-new", PROMPT[:length])

for length in [500, 1000, 1500, 2000, 3000, 4000]:
    test(f"gpt-5.6-luna len {length}", "gpt-5.6-luna", PROMPT[:length])
