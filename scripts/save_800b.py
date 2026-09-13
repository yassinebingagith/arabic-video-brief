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

prompt = (
    "Analyze this video about Carl Jung. The title is 'Think About This Before You Go To Sleep And Your Life Will Change'. "
    "Speaker: Carl Jung. Description: A deep psychological guide into the subconscious mind and dream state. "
    "Return JSON with post_title_ar (translated to Arabic), summary_ar (140-150 words in Arabic split into two paragraphs), "
    "and post_description (comprehensive Arabic article)."
)

payload = {
    "model": "gpt-5.6-new",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.4
}

req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        content = resp.read().decode("utf-8")
        with open("output_800b.json", "w", encoding="utf-8") as f:
            f.write(content)
        print("Success! Saved output_800b.json")
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print("Err:", e)
