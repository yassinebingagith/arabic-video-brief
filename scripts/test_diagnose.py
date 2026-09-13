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

def try_req(name, model, messages):
    payload = {"model": model, "messages": messages, "temperature": 0.4}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read().decode("utf-8")
            print(f"[{name}] SUCCESS (len {len(data)})")
    except urllib.error.HTTPError as e:
        print(f"[{name}] HTTPError {e.code}: {e.read().decode('utf-8')[:120]}")
    except Exception as e:
        print(f"[{name}] Exception: {e}")

# Test 1: gpt-5.6-new without system message, only user message with PROMPT
try_req("1. gpt-5.6-new, no system msg, PROMPT only", "gpt-5.6-new", [{"role": "user", "content": PROMPT}])

# Test 2: gpt-5.6-luna with PROMPT
try_req("2. gpt-5.6-luna, PROMPT only", "gpt-5.6-luna", [{"role": "user", "content": PROMPT}])

# Test 3: gpt-5.6-new with shorter English prompt
try_req("3. gpt-5.6-new, short english", "gpt-5.6-new", [{"role": "user", "content": "Analyze Carl Jung's concept of the shadow and return JSON with summary_ar and post_title_ar."}])
