import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

settings = get_settings()
key = settings.youtube_api_key

more_searches = [
    {"q": "بودكاست علاقات عاطفية حب زواج", "region": "EG", "lang": "ar", "topic": "Arabic - Love & Marriage"},
    {"q": "بودكاست صدمات الطفولة تعافي نفسي", "region": "EG", "lang": "ar", "topic": "Arabic - Trauma & Healing"},
    {"q": "Mel Robbins Podcast relationship love trauma", "region": "US", "lang": "en", "topic": "US - Trauma & Relationships"},
    {"q": "Chris Williamson Modern Wisdom dating trauma", "region": "US", "lang": "en", "topic": "US - Modern Wisdom Dating"},
    {"q": "Huberman Lab relationship attachment psychology", "region": "US", "lang": "en", "topic": "US - Neuroscience Attachment"},
    {"q": "School of Greatness Lewis Howes trauma relationship", "region": "US", "lang": "en", "topic": "US - Greatness Love & Trauma"},
    {"q": "دكتور عماد رشاد بودكاست علاقات صدمات", "region": "EG", "lang": "ar", "topic": "Arabic - Deep Psychology & Healing"}
]

published_after = "2026-09-01T00:00:00Z"
published_before = "2026-09-06T00:00:00Z"

seen_ids = set()
with open("scratch_september_2026.json", "r", encoding="utf-8") as f:
    existing = json.load(f)
for item in existing:
    seen_ids.add(item["id"])

new_raw = []
for s in more_searches:
    for order in ["viewCount", "relevance"]:
        try:
            params = {
                "key": key,
                "part": "snippet",
                "q": s["q"],
                "type": "video",
                "publishedAfter": published_after,
                "publishedBefore": published_before,
                "maxResults": 10
            }
            if s.get("region"):
                params["regionCode"] = s["region"]
            if s.get("lang"):
                params["relevanceLanguage"] = s["lang"]
            if order:
                params["order"] = order

            res = _get_json("search", params)
            for item in res.get("items", []):
                vid = item.get("id", {}).get("videoId")
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    new_raw.append({"id": vid, "topic": s["topic"]})
        except Exception as e:
            print(f"Error: {e}")

if new_raw:
    ids = [c["id"] for c in new_raw]
    id_to_topic = {c["id"]: c["topic"] for c in new_raw}
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        res = _get_json("videos", {
            "key": key,
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch)
        })
        for d in res.get("items", []):
            snippet = d.get("snippet", {})
            stats = d.get("statistics", {})
            cd = d.get("contentDetails", {})
            vid = d.get("id")
            pub = snippet.get("publishedAt", "")
            if not (pub >= published_after and pub <= published_before):
                continue
            duration = parse_iso_duration(cd.get("duration", ""))
            if duration < 180:
                continue
            views = int(stats.get("viewCount", 0) or 0)
            likes = int(stats.get("likeCount", 0) or 0)
            comments = int(stats.get("commentCount", 0) or 0)
            eng_rate = round(((likes + comments) / views * 100), 2) if views > 0 else 0
            like_rate = round((likes / views * 100), 2) if views > 0 else 0
            conversion_score = round((views ** 0.5) * (likes + 1.5 * comments))

            existing.append({
                "id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "published_at": pub,
                "duration_minutes": round(duration / 60, 1),
                "views": views,
                "likes": likes,
                "comments": comments,
                "like_rate_pct": like_rate,
                "eng_rate_pct": eng_rate,
                "conversion_score": conversion_score,
                "topic_category": id_to_topic.get(vid, "General"),
                "description_snippet": snippet.get("description", "")[:200].replace("\n", " ")
            })

existing.sort(key=lambda x: (x["views"], x["likes"]), reverse=True)
with open("scratch_september_2026.json", "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"Total videos now: {len(existing)}")
