import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

settings = get_settings()
key = settings.youtube_api_key

searches = [
    # --- ARABIC ---
    # Podcasts / Relationships / Love / Trauma
    {"q": "بودكاست علاقات حب صدمات", "region": "SA", "lang": "ar", "topic": "Arabic - Love & Trauma / Relationships"},
    {"q": "فنجان ثمانية", "region": "SA", "lang": "ar", "topic": "Arabic - Culture & Psychology (Finjan)"},
    {"q": "ABtalks أنس بوخش", "region": "AE", "lang": "ar", "topic": "Arabic - Psychology & Vulnerability (ABtalks)"},
    {"q": "بودكاست وعي", "region": "EG", "lang": "ar", "topic": "Arabic - Self-Help & Psychology (Waei)"},
    {"q": "الدحيح", "region": "EG", "lang": "ar", "topic": "Arabic - Science & Informative (Daheeh)"},
    {"q": "المخبر الاقتصادي", "region": "EG", "lang": "ar", "topic": "Arabic - News & Economy"},
    {"q": "ياسر الحزيمي علاقات حب ذات", "region": "SA", "lang": "ar", "topic": "Arabic - Relationships & Self-Worth"},
    {"q": "وثائقي علم نفس صحة", "region": "EG", "lang": "ar", "topic": "Arabic - Science & Health"},
    {"q": "بودكاست صحة تغذية عقل", "region": "SA", "lang": "ar", "topic": "Arabic - Health & Science"},

    # --- AMERICAN / ENGLISH ---
    # Podcasts / Love / Romance / Trauma / Psychology
    {"q": "podcast love trauma relationships psychology", "region": "US", "lang": "en", "topic": "US - Love, Romance & Trauma"},
    {"q": "The Diary Of A CEO podcast", "region": "US", "lang": "en", "topic": "US - Psychology & Deep Talk (DOAC)"},
    {"q": "Andrew Huberman health science psychology", "region": "US", "lang": "en", "topic": "US - Science & Neuroscience"},
    {"q": "Chris Williamson Modern Wisdom psychology", "region": "US", "lang": "en", "topic": "US - Modern Psychology & Dating"},
    {"q": "Mel Robbins trauma healing habits", "region": "US", "lang": "en", "topic": "US - Trauma & Mindset"},
    {"q": "Jay Shetty podcast love relationship heal", "region": "US", "lang": "en", "topic": "US - Love & Healing"},
    {"q": "science health documentary informative", "region": "US", "lang": "en", "topic": "US - Science & Informative"},
    {"q": "news deep dive documentary analysis", "region": "US", "lang": "en", "topic": "US - News & Analysis"},
    {"q": "Lex Fridman podcast", "region": "US", "lang": "en", "topic": "US - Deep Conversations & Science"},
    {"q": "Shawn Ryan Show podcast", "region": "US", "lang": "en", "topic": "US - Gripping Stories & News/Trauma"},
]

published_after = "2026-09-01T00:00:00Z"
published_before = "2026-09-06T00:00:00Z"

seen_ids = set()
raw_candidates = []

print(f"Executing search queries across YouTube API (window: {published_after} to {published_before})...")

for s in searches:
    for order in ["viewCount", "relevance"]:
        try:
            params = {
                "key": key,
                "part": "snippet",
                "q": s["q"],
                "type": "video",
                "publishedAfter": published_after,
                "publishedBefore": published_before,
                "maxResults": 15
            }
            if s.get("region"):
                params["regionCode"] = s["region"]
            if s.get("lang"):
                params["relevanceLanguage"] = s["lang"]
            if order:
                params["order"] = order

            res = _get_json("search", params)
            items = res.get("items", [])
            for item in items:
                vid = item.get("id", {}).get("videoId")
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    raw_candidates.append({
                        "id": vid,
                        "topic_category": s["topic"],
                        "search_q": s["q"]
                    })
        except Exception as e:
            print(f"Error searching {s['q']} ({order}): {e}")

print(f"Found {len(raw_candidates)} candidate videos. Now fetching detailed metrics...")

ids = [c["id"] for c in raw_candidates]
id_to_topic = {c["id"]: c["topic_category"] for c in raw_candidates}

details_list = []
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    try:
        res = _get_json("videos", {
            "key": key,
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch)
        })
        details_list.extend(res.get("items", []))
    except Exception as e:
        print(f"Error fetching batch {i}: {e}")

processed = []
for d in details_list:
    snippet = d.get("snippet", {})
    stats = d.get("statistics", {})
    cd = d.get("contentDetails", {})
    vid = d.get("id")

    pub = snippet.get("publishedAt", "")
    # Check date is in September 2026
    if not (pub >= published_after and pub <= published_before):
        continue

    duration = parse_iso_duration(cd.get("duration", ""))
    # Filter out short clips / vertical shorts under 3 minutes (180s)
    if duration < 180:
        continue

    views = int(stats.get("viewCount", 0) or 0)
    likes = int(stats.get("likeCount", 0) or 0)
    comments = int(stats.get("commentCount", 0) or 0)

    # Conversion / Engagement rate
    eng_rate = round(((likes + comments) / views * 100), 2) if views > 0 else 0
    like_rate = round((likes / views * 100), 2) if views > 0 else 0

    # High conversion score combines view volume and engagement density
    # Conversion score = views^0.6 * (likes + comments)
    conversion_score = round((views ** 0.5) * (likes + 1.5 * comments))

    title = snippet.get("title", "")
    channel = snippet.get("channelTitle", "")
    description = snippet.get("description", "")
    tags = snippet.get("tags", [])

    duration_min = round(duration / 60, 1)

    processed.append({
        "id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": title,
        "channel": channel,
        "published_at": pub,
        "duration_minutes": duration_min,
        "views": views,
        "likes": likes,
        "comments": comments,
        "like_rate_pct": like_rate,
        "eng_rate_pct": eng_rate,
        "conversion_score": conversion_score,
        "topic_category": id_to_topic.get(vid, "General"),
        "description_snippet": description[:200].replace("\n", " ") if description else ""
    })

# Sort by views and engagement
processed.sort(key=lambda x: (x["views"], x["likes"]), reverse=True)

with open("scratch_september_2026.json", "w", encoding="utf-8") as f:
    json.dump(processed, f, ensure_ascii=False, indent=2)

print(f"Total qualified long-form videos published Sep 1 - Sep 5, 2026: {len(processed)}")
for i, p in enumerate(processed[:20], 1):
    print(f"{i}. [{p['channel']}] {p['title'][:60]} | Views: {p['views']:,} | Likes: {p['likes']:,} | {p['topic_category']}")
