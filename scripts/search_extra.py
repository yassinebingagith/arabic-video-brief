import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

key = get_settings().youtube_api_key

extra_searches = [
    {"q": "ثمانية فنجان 2026", "cat": "Arabic Culture & Society"},
    {"q": "Chris Williamson Modern Wisdom 2026", "cat": "Modern Wisdom / Dating & Mind"},
    {"q": "Jordan Peterson podcast 2026 love psychology", "cat": "Psychology & Meaning"},
    {"q": "Ali Abdaal deep dive 2026 economy career", "cat": "Productivity & Economy"},
]

results = []
for s in extra_searches:
    res = _get_json("search", {
        "key": key,
        "part": "snippet",
        "q": s["q"],
        "type": "video",
        "publishedAfter": "2026-01-01T00:00:00Z",
        "order": "viewCount",
        "maxResults": 6
    })
    ids = [item["id"]["videoId"] for item in res.get("items", []) if "videoId" in item.get("id", {})]
    if ids:
        vids = _get_json("videos", {"key": key, "part": "snippet,statistics,contentDetails", "id": ",".join(ids)})
        for v in vids.get("items", []):
            sn = v["snippet"]
            st = v["statistics"]
            cd = v["contentDetails"]
            dur = parse_iso_duration(cd.get("duration", ""))
            pub = sn.get("publishedAt", "")
            if pub.startswith("2026") and dur >= 600:
                views = int(st.get("viewCount", 0) or 0)
                likes = int(st.get("likeCount", 0) or 0)
                comments = int(st.get("commentCount", 0) or 0)
                eng = round(((likes + comments) / views * 100), 2) if views > 0 else 0
                results.append({
                    "id": v["id"],
                    "title": sn["title"],
                    "channel": sn["channelTitle"],
                    "published_at": pub[:10],
                    "duration_min": round(dur / 60, 1),
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "engagement_rate_pct": eng,
                    "category": s["cat"],
                    "description": sn.get("description", "")[:250].replace("\n", " "),
                    "url": f"https://www.youtube.com/watch?v={v['id']}"
                })

with open("scratch_extra.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Extra fetched: {len(results)}")
