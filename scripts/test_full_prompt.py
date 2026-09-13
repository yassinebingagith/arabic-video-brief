import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import fetch_video_details
from arabic_video_brief.vyceai import PROMPT

s = get_settings()
details = fetch_video_details("V8XQCkBa6Tk", s.youtube_api_key)
print("Details fetched:", details.get("title"))

ctx = f"""VIDEO CONTEXT (GROUND TRUTH):
- Original Video Title: {details.get('title')}
- Channel / Speaker: {details.get('channel')}
- Video Description:
{details.get('description', '')[:800]}
"""

full_prompt = f"{ctx}\n\n{PROMPT}"
print(f"Prompt length: {len(full_prompt)}")

url = f"{s.vyceai_base_url}/chat/completions"
headers = {
    "Authorization": f"Bearer {s.vyceai_api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

payload = {
    "model": "gpt-5.6-new",
    "messages": [
        {"role": "system", "content": "You are an expert video analyst producing Arabic social media video briefs. Return strictly valid JSON."},
        {"role": "user", "content": full_prompt}
    ],
    "temperature": 0.4
}

req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        content = resp.read().decode("utf-8")
        print("Success! Response length:", len(content))
        with open("test_resp.json", "w", encoding="utf-8") as f:
            f.write(content)
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Exception: {e}")
