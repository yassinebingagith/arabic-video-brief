import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

settings = get_settings()
api_key = settings.youtube_api_key

targeted_queries = [
    "lack of purpose romantic obsession",
    "why you obsess over a person purpose",
    "limerence emptiness purpose",
    "stop obsessing over them find purpose monologue",
    "trauma bond narcissist monologue",
    "unrequited love monologue intimate"
]

more_items = {}
for q in targeted_queries:
    data = _get_json("search", {
        "key": api_key,
        "part": "snippet",
        "type": "video",
        "q": q,
        "order": "relevance",
        "publishedAfter": "2025-01-01T00:00:00Z",
        "videoDuration": "medium",
        "maxResults": 15,
    })
    for item in data.get("items", []):
        vid = item.get("id", {}).get("videoId")
        if vid:
            more_items[vid] = item

ids = list(more_items.keys())
details = []
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    res = _get_json("videos", {
        "key": api_key,
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(batch)
    })
    details.extend(res.get("items", []))

results = []
for d in details:
    snippet = d.get("snippet", {})
    stats = d.get("statistics", {})
    cd = d.get("contentDetails", {})
    channel = snippet.get("channelTitle", "")
    title = snippet.get("title", "")
    
    if "jett" in channel.lower() or "franzen" in channel.lower():
        continue
    duration = parse_iso_duration(cd.get("duration", ""))
    if duration < 240:
        continue
    
    results.append({
        "id": d.get("id"),
        "title": title,
        "channel": channel,
        "published_at": snippet.get("publishedAt", "")[:10],
        "duration_sec": duration,
        "views": int(stats.get("viewCount", 0) or 0),
        "likes": int(stats.get("likeCount", 0) or 0),
        "description": snippet.get("description", "")[:200].replace("\n", " "),
        "url": f"https://www.youtube.com/watch?v={d.get('id')}"
    })

results.sort(key=lambda x: x["views"], reverse=True)

with open("scripts/targeted_summary.txt", "w", encoding="utf-8") as out:
    for i, item in enumerate(results, 1):
        mins = item["duration_sec"] // 60
        out.write(f"{i}. [{item['channel']}] ({item['published_at']} | {mins}m | {item['views']:,} views)\n")
        out.write(f"   Title: {item['title']}\n")
        out.write(f"   URL: {item['url']}\n")
        out.write(f"   Desc: {item['description']}\n")
        out.write("-" * 60 + "\n")

print(f"Written {len(results)} targeted results to scripts/targeted_summary.txt")
