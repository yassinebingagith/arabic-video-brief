import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import fetch_video_details

s = get_settings()
details = fetch_video_details("V8XQCkBa6Tk", s.youtube_api_key)

CONDENSED_PROMPT = f"""Analyze this video to create an Arabic video brief and publication article.
Title: {details.get('title')}
Channel: {details.get('channel')}
Description: {details.get('description', '')[:250].replace(chr(10), ' ')}

Rules:
1. Simplified Modern Standard Arabic (فصحى سلسة).
2. Anti-meta ban: Never say "يناقش المقطع" or "يتناول الفيديو". Dive straight into facts/reality.
3. Concrete examples: Include real-world daily situations/tangible analogies.

Return ONLY a valid JSON object:
{{
  "source_language": "en",
  "post_title_ar": "Accurate Arabic translation of title without hashtags or emojis",
  "summary_ar": "Exactly two balanced Arabic paragraphs separated by newline (140-160 words total, 70-80 words each). P1: Addictive hook into the core reality. P2: Actionable rules, solutions, and core takeaway.",
  "post_description": "Addictive narrative article (1500-1700 chars): Line 1: Arabic title - Speaker/Channel. Hook paragraph (250 chars). 3 thematic sections starting with -عنوان المحور- with real examples. Final section: -خطوات عملية وخلاصة- with practical guidance. No bullets/timestamps."
}}"""

print(f"Prompt length: {len(CONDENSED_PROMPT)} characters")

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
        {"role": "user", "content": CONDENSED_PROMPT}
    ],
    "temperature": 0.3
}

req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        content = resp.read().decode("utf-8")
        res_json = json.loads(content)
        raw_text = res_json["choices"][0]["message"]["content"]
        with open("test_carl_jung_condensed.json", "w", encoding="utf-8") as f:
            f.write(raw_text)
        print("SUCCESS! Output length:", len(raw_text))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print("Err:", e)
