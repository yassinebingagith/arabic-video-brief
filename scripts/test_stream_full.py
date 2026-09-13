import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import fetch_video_details
from arabic_video_brief.vyceai import PROMPT, _clean_json_text, _resilient_extract_json

s = get_settings()
details = fetch_video_details("V8XQCkBa6Tk", s.youtube_api_key)

v_ctx = f"""VIDEO CONTEXT (GROUND TRUTH):
- Original Video Title: {details.get('title')}
- Channel / Speaker: {details.get('channel')}
- Video Description:
{details.get('description', '')[:500]}
"""

full_prompt = f"{v_ctx}\n\n{PROMPT}"

url = f"{s.vyceai_base_url}/chat/completions"
headers = {
    "Authorization": f"Bearer {s.vyceai_api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/event-stream, application/json"
}

payload = {
    "model": "gpt-5.6-new",
    "messages": [
        {"role": "system", "content": "You are an expert video analyst producing Arabic social media video briefs. Return strictly valid JSON."},
        {"role": "user", "content": full_prompt}
    ],
    "temperature": 0.4,
    "stream": True
}

req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
print("Sending streamed request for full Carl Jung video brief...")
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        full_content = ""
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                data_part = line_str[6:]
                if data_part == "[DONE]":
                    break
                try:
                    delta = json.loads(data_part)["choices"][0]["delta"]
                    full_content += delta.get("content", "")
                except Exception:
                    pass
        print("Success! Total streamed characters:", len(full_content))
        with open("carl_jung_full_stream.json", "w", encoding="utf-8") as f:
            f.write(full_content)
        cleaned = _clean_json_text(full_content)
        parsed = _resilient_extract_json(cleaned)
        print("Keys in parsed JSON:", list(parsed.keys()))
        print("post_title_ar:", parsed.get("post_title_ar"))
        print("summary_ar words:", len(parsed.get("summary_ar", "").split()))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print("Err:", e)
