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

def call_clean(text):
    payload = {"model": "gpt-5.6-new", "messages": [{"role": "user", "content": text}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            print("SUCCESS! Resp:", resp.read().decode("utf-8")[:100])
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")

clean_prompt = """Analyze this video to create an Arabic video brief and article.
Title: Think About This Before You Go To Sleep And Your Life Will Change - Carl Jung
Channel: Motiversity
Rules:
1. Pure Modern Standard Arabic.
2. Anti-meta ban: Never say 'in this video'.
Return ONLY valid JSON:
{
  "source_language": "en",
  "post_title_ar": "فكر في هذا قبل النوم وستتغير حياتك - كارل يونغ",
  "summary_ar": "فقرتان بالعربية الفصحى (140 كلمة).",
  "post_description": "مقال سردي كامل بالعربية (1500 حرف) مع محاور."
}"""

print("Testing clean prompt without special chars...")
call_clean(clean_prompt)
