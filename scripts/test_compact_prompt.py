import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import fetch_video_details
from arabic_video_brief.utils import word_count

s = get_settings()
details = fetch_video_details("V8XQCkBa6Tk", s.youtube_api_key)
title = details.get("title", "Carl Jung")
channel = details.get("channel", "Motiversity")
desc = details.get("description", "")[:300].replace("\n", " ")

COMPACT_PROMPT = f"""حلل هذا الفيديو لإنتاج ملخص فيديو عربي احترافي ومقال للنشر.
العنوان: {title}
القناة: {channel}
الوصف: {desc}

المطلوب إرجاع كائن JSON صالح فقط بالحقول التالية دون أي نص خارجي:
1. "source_language": لغة المصدر ("en" أو "ar").
2. "post_title_ar": ترجمة عربية فصحى نقية ودقيقة لعنوان الفيديو بدون إيموجي أو هاشتاغ.
3. "summary_ar": ملخص فصيح ومؤثر من فقرتين متوازنتين (إجمالي 140 إلى 150 كلمة):
- الفقرة الأولى (70-75 كلمة): مقدمة مشوقة واقعية تغوص في الفكرة فوراً بدون أي عبارات وصفية مثل 'يناقش المقطع'.
- الفقرة الثانية (70-75 كلمة): الخلاصة العملية والحلول والنصائح الذهبية.
4. "post_description": مقال سردي جذاب بالفصحى المبسطة (بين 1400 و1600 حرف):
السطر الأول: عنوان الموضوع متبوعاً بشرطة واسم المتحدث أو القناة.
فقرة افتتاحية مشوقة (250 حرف).
3 محاور رئيسية، كل محور يبدأ بـ -عنوان المحور- متبوعاً بشرح واقعي وأمثلة ملموسة.
محور ختامي: -خطوات عملية وخلاصة- يقدم توجيهات تطبيقية. لا تضع أي هاشتاغات هنا.
"""

print(f"Total prompt length: {len(COMPACT_PROMPT)} characters")

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
        {"role": "user", "content": COMPACT_PROMPT}
    ],
    "temperature": 0.4
}

req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        content = resp.read().decode("utf-8")
        res_json = json.loads(content)
        text = res_json["choices"][0]["message"]["content"]
        print("Success! Got response:")
        # Save response
        with open("carl_jung_result.json", "w", encoding="utf-8") as f:
            f.write(text)
        print("Length of content:", len(text))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print("Exception:", e)
