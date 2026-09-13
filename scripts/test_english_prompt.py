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

def test_bytes(label, text):
    raw_bytes = json.dumps({"model": "gpt-5.6-new", "messages": [{"role": "user", "content": text}]}).encode("utf-8")
    print(f"[{label}] Raw byte length: {len(raw_bytes)}")
    req = urllib.request.Request(url, data=raw_bytes, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode("utf-8")
            print(f"[{label}] SUCCESS len={len(data)}")
    except urllib.error.HTTPError as e:
        print(f"[{label}] HTTP {e.code}: {e.read().decode('utf-8')[:100]}")
    except Exception as e:
        print(f"[{label}] Err: {e}")

# English prompt asking for Arabic output
test_bytes("English 400b", "Analyze this video about Carl Jung. Return JSON with post_title_ar, summary_ar (two paragraphs in Arabic), and post_description in Arabic.")
test_bytes("English 800b", "Analyze this video about Carl Jung. The title is 'Think About This Before You Go To Sleep And Your Life Will Change'. Speaker: Carl Jung. Description: A deep psychological guide into the subconscious mind and dream state. Return JSON with post_title_ar (translated to Arabic), summary_ar (140-150 words in Arabic split into two paragraphs), and post_description (comprehensive Arabic article).")
