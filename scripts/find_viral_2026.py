import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

settings = get_settings()
key = settings.youtube_api_key

searches = [
    # Arabic - Psychology, Relationships, Economy, Monologues & Podcasts
    {"q": "فنجان ثمانية علاقات حب نفس 2026", "region": "SA", "lang": "ar", "topic": "Psychology & Relationships (Arabic)"},
    {"q": "بودكاست فنجان اقتصاد 2026", "region": "SA", "lang": "ar", "topic": "Economy (Arabic)"},
    {"q": "ABtalks Anas Bukhash 2026", "region": "AE", "lang": "ar", "topic": "Psychology & Vulnerability (Arabic)"},
    {"q": "المخبر الاقتصادي 2026", "region": "EG", "lang": "ar", "topic": "Economy (Arabic)"},
    {"q": "بودكاست وعي 2026 علاقات نفسي", "region": "EG", "lang": "ar", "topic": "Psychology & Life (Arabic)"},
    {"q": "ياسر الحزيمي 2026", "region": "SA", "lang": "ar", "topic": "Psychology & Self-Worth (Arabic)"},
    {"q": "بودكاست ساندوتش ورقي 2026", "region": "SA", "lang": "ar", "topic": "Mindset & Psychology (Arabic)"},

    # US / Global - Psychology, Love, Economy, Life Monologues
    {"q": "The Diary Of A CEO relationship psychology 2026", "region": "US", "lang": "en", "topic": "Psychology & Relationships (US)"},
    {"q": "The Diary Of A CEO economy money future 2026", "region": "US", "lang": "en", "topic": "Economy & Career (US)"},
    {"q": "Andrew Huberman psychology mental health 2026", "region": "US", "lang": "en", "topic": "Neuroscience & Psychology (US)"},
    {"q": "Chris Williamson Modern Wisdom dating love psychology 2026", "region": "US", "lang": "en", "topic": "Love & Modern Dating (US)"},
    {"q": "Mel Robbins podcast trauma habits love 2026", "region": "US", "lang": "en", "topic": "Psychology & Self-Help (US)"},
    {"q": "Lex Fridman economy society psychology 2026", "region": "US", "lang": "en", "topic": "Economics & Tech (US)"},
]

seen_ids = set()
raw_candidates = []

for s in searches:
    try:
        res = _get_json("search", {
            "key": key,
            "part": "snippet",
            "q": s["q"],
            "type": "video",
            "publishedAfter": "2026-01-01T00:00:00Z",
            "videoDuration": "long",
            "order": "viewCount",
            "maxResults": 10
        })
        for item in res.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                raw_candidates.append({
                    "id": vid,
                    "topic_category": s["topic"],
                    "search_q": s["q"]
                })
    except Exception as e:
        print(f"Error searching {s['q']}: {e}")

print(f"Collected {len(raw_candidates)} unique candidate video IDs from 2026.")

# Fetch details in batches
details_list = []
ids = [c["id"] for c in raw_candidates]
id_to_topic = {c["id"]: c["topic_category"] for c in raw_candidates}

for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    res = _get_json("videos", {
        "key": key,
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(batch)
    })
    details_list.extend(res.get("items", []))

processed = []
for d in details_list:
    snippet = d.get("snippet", {})
    stats = d.get("statistics", {})
    cd = d.get("contentDetails", {})
    
    pub = snippet.get("publishedAt", "")
    # strict filter for 2026
    if not pub.startswith("2026"):
        continue
        
    duration = parse_iso_duration(cd.get("duration", ""))
    # filter out shorts / clips shorter than 5 minutes
    if duration < 300:
        continue
        
    views = int(stats.get("viewCount", 0) or 0)
    likes = int(stats.get("likeCount", 0) or 0)
    comments = int(stats.get("commentCount", 0) or 0)
    
    if views < 50000:  # must have significant viral volume
        continue
        
    # Engagement rates
    eng_rate = ((likes + comments) / views * 100) if views > 0 else 0
    like_rate = (likes / views * 100) if views > 0 else 0
    comment_rate = (comments / views * 1000) if views > 0 else 0 # comments per 1k views
    
    # Shareability composite score (virality signal): views weight + high engagement
    # High like rate + comment rate strongly correlates with click/share behaviour on YouTube
    shareability_score = (views / 100000) * 0.5 + (eng_rate * 2.0)
    
    title = snippet.get("title", "")
    # Unescape HTML entities
    title = title.replace("&quot;", "\"").replace("&#39;", "'").replace("&amp;", "&")
    
    processed.append({
        "id": d.get("id"),
        "title": title,
        "channel": snippet.get("channelTitle", ""),
        "published_at": pub[:10],
        "duration_min": round(duration / 60, 1),
        "views": views,
        "likes": likes,
        "comments": comments,
        "engagement_rate_pct": round(eng_rate, 2),
        "comments_per_1k": round(comment_rate, 2),
        "shareability_score": round(shareability_score, 2),
        "topic": id_to_topic.get(d.get("id"), "General"),
        "url": f"https://www.youtube.com/watch?v={d.get('id')}",
        "description": snippet.get("description", "")[:300].replace("\n", " ")
    })

print(f"Qualified videos in 2026: {len(processed)}")
processed.sort(key=lambda x: x["views"], reverse=True)

with open("scratch_viral_2026.json", "w", encoding="utf-8") as f:
    json.dump(processed, f, indent=2, ensure_ascii=False)

print("Top 15 preview:")
for i, v in enumerate(processed[:15], 1):
    print(f"{i}. [{v['views']:,} views | {v['likes']:,} likes | {v['engagement_rate_pct']}% eng] {v['channel']}: {v['title']}")
