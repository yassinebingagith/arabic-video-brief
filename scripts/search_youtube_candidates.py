import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

settings = get_settings()
api_key = settings.youtube_api_key

search_terms = [
    "romantic obsession monologue",
    "limerence lack of purpose love trauma",
    "why you obsess over people monologue psychology",
    "narcissistic trauma romance deep talk podcast",
    "emotional detachment romantic obsession healing",
    "unrequited love personal purpose monologue"
]

all_items = {}

for term in search_terms:
    data = _get_json("search", {
        "key": api_key,
        "part": "snippet",
        "type": "video",
        "q": term,
        "order": "relevance",
        "publishedAfter": "2025-01-01T00:00:00Z",
        "videoDuration": "medium",  # 4 - 20 mins or long
        "maxResults": 15,
    })
    for item in data.get("items", []):
        vid = item.get("id", {}).get("videoId")
        if vid and vid not in all_items:
            all_items[vid] = item

print(f"Total candidate videos collected: {len(all_items)}")

# Fetch video details in batches of 50
ids = list(all_items.keys())
details_list = []
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    res = _get_json("videos", {
        "key": api_key,
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(batch)
    })
    details_list.extend(res.get("items", []))

curated = []
for d in details_list:
    snippet = d.get("snippet", {})
    stats = d.get("statistics", {})
    cd = d.get("contentDetails", {})
    channel = snippet.get("channelTitle", "")
    title = snippet.get("title", "")
    
    # Exclude Jett Franzen as requested
    if "jett" in channel.lower() or "franzen" in channel.lower():
        continue
    
    duration = parse_iso_duration(cd.get("duration", ""))
    views = int(stats.get("viewCount", 0) or 0)
    
    # Check if duration is at least 4 minutes (deep talk/monologue style, not shorts)
    if duration < 240:
        continue
        
    curated.append({
        "id": d.get("id"),
        "title": title,
        "channel": channel,
        "published_at": snippet.get("publishedAt", "")[:10],
        "duration_sec": duration,
        "views": views,
        "likes": int(stats.get("likeCount", 0) or 0),
        "description": snippet.get("description", "")[:250].replace("\n", " "),
        "url": f"https://www.youtube.com/watch?v={d.get('id')}"
    })

# Sort by relevance / views
curated.sort(key=lambda x: x["views"], reverse=True)

with open("scripts/candidates.json", "w", encoding="utf-8") as f:
    json.dump(curated, f, indent=2, ensure_ascii=False)
print("Saved", len(curated), "candidates to scripts/candidates.json")

