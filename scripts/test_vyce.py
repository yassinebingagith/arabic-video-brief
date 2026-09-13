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

def call(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

print("1. Testing user message only:")
code, res = call({"model": "gpt-5.6-new", "messages": [{"role": "user", "content": "Hi"}]})
print(f"Code: {code}, Res: {res[:100]}")

print("2. Testing system + user message:")
code, res = call({"model": "gpt-5.6-new", "messages": [{"role": "system", "content": "You are an assistant"}, {"role": "user", "content": "Hi"}]})
print(f"Code: {code}, Res: {res[:100]}")

print("3. Testing with temperature & max_tokens:")
code, res = call({"model": "gpt-5.6-new", "messages": [{"role": "user", "content": "Say test in Arabic"}], "temperature": 0.4, "max_tokens": 500})
print(f"Code: {code}, Res: {res[:100]}")

print("4. Testing gpt-5.6-luna:")
code, res = call({"model": "gpt-5.6-luna", "messages": [{"role": "user", "content": "Hi"}]})
print(f"Code: {code}, Res: {res[:100]}")
