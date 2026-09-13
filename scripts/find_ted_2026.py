import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

settings = get_settings()
key = settings.youtube_api_key

# Query official TED channel: UCAuUUnT6oDeKwE6v1NGQxug
params = {
    "key": key,
    "part": "snippet",
    "type": "video",
    "channelId": "UCAuUUnT6oDeKwE6v1NGQxug",
    "order": "viewCount",
    "publishedAfter": "2026-01-01T00:00:00Z",
    "maxResults": 50,
}
res = _get_json("search", params)
vids = [it["id"]["videoId"] for it in res.get("items", []) if "videoId" in it.get("id", {})]

details_res = _get_json("videos", {
    "key": key,
    "part": "snippet,statistics,contentDetails",
    "id": ",".join(vids)
})

talks = []
for it in details_res.get("items", []):
    views = int(it.get("statistics", {}).get("viewCount", 0) or 0)
    dur = parse_iso_duration(it.get("contentDetails", {}).get("duration", ""))
    title = it["snippet"]["title"]
    pub = it["snippet"]["publishedAt"]
    vid = it["id"]
    # Real TED talks are standard talks, filter out very short teaser clips under 4 mins if any
    if dur >= 240:
        talks.append({
            "id": vid,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "title": title,
            "views": views,
            "duration_m": round(dur / 60, 1),
            "published_at": pub
        })

talks.sort(key=lambda x: x["views"], reverse=True)
print(f"Total TED talks on official channel in 2026 (>= 4 min): {len(talks)}\n")
for i, v in enumerate(talks[:10], 1):
    safe_title = v["title"].encode("ascii", errors="replace").decode("ascii")
    print(f"{i}. {safe_title}")
    print(f"   Views: {v['views']:,}")
    print(f"   Published: {v['published_at']}")
    print(f"   Duration: {v['duration_m']} mins")
    print(f"   Link: {v['url']}")
    print("-" * 60)

# Also dump JSON for reference
Path("outputs/top_ted_2026.json").write_text(json.dumps(talks[:5], indent=2), encoding="utf-8")
