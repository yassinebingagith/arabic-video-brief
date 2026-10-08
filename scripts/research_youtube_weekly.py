import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Set stdout to UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path.cwd() / "src"))
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

settings = get_settings()
api_key = settings.youtube_api_key

if not api_key:
    print("Error: YOUTUBE_API_KEY not found in .env")
    sys.exit(1)

# Time window: Last 7 days
# Current date: 2026-09-16
now = datetime.now(timezone.utc)
published_after = (now - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
published_before = now.strftime("%Y-%m-%dT23:59:59Z")

print(f"=== YouTube Research: Last Week ({published_after} to {published_before}) ===")

# Definition of search queries
searches = [
    # ================= ARAB WORLD =================
    # Top Arabic Podcasts
    {"q": "بودكاست فنجان", "region": "SA", "lang": "ar", "topic": "Arabic Podcast - Finjan (ثمانية)", "scope": "Arab World"},
    {"q": "بودكاست ABtalks أنس بوخش", "region": "AE", "lang": "ar", "topic": "Arabic Podcast - ABtalks (أنس بوخش)", "scope": "Arab World"},
    {"q": "بودكاست وعي", "region": "EG", "lang": "ar", "topic": "Arabic Podcast - Waei (وعي)", "scope": "Arab World"},
    {"q": "بودكاست بدون ورق", "region": "KW", "lang": "ar", "topic": "Arabic Podcast - Bedoon Waraq", "scope": "Arab World"},
    {"q": "بودكاست سكون", "region": "SA", "lang": "ar", "topic": "Arabic Podcast - Sokoun", "scope": "Arab World"},
    {"q": "بودكاست علاقات وتطوير الذات", "region": "SA", "lang": "ar", "topic": "Arabic Podcast - Relationships & Self-Growth", "scope": "Arab World"},
    {"q": "بودكاست صحة وتغذية وعقل", "region": "EG", "lang": "ar", "topic": "Arabic Podcast - Health & Neuroscience", "scope": "Arab World"},
    {"q": "بودكاست بزنس وريادة أعمال", "region": "SA", "lang": "ar", "topic": "Arabic Podcast - Business & Entrepreneurship", "scope": "Arab World"},

    # Arabic Informative & Educational & Documentary
    {"q": "الدحيح", "region": "EG", "lang": "ar", "topic": "Arabic Informative - Daheeh (Science/History)", "scope": "Arab World"},
    {"q": "المخبر الاقتصادي", "region": "EG", "lang": "ar", "topic": "Arabic Informative - Economic Informant", "scope": "Arab World"},
    {"q": "ياسر الحزيمي", "region": "SA", "lang": "ar", "topic": "Arabic Informative - Yasser Al-Hazimi (Psychology)", "scope": "Arab World"},
    {"q": "علي محمد علي تلخيص كتب أفكار", "region": "EG", "lang": "ar", "topic": "Arabic Informative - Book Summaries & Ideas", "scope": "Arab World"},
    {"q": "وثائقي علم نفس وتاريخ", "region": "EG", "lang": "ar", "topic": "Arabic Documentary - Psychology & History", "scope": "Arab World"},
    {"q": "الجزيرة الوثائقية", "region": "QA", "lang": "ar", "topic": "Arabic Documentary - Al Jazeera Documentary", "scope": "Arab World"},

    # ================= WORLDWIDE =================
    # Top Worldwide Podcasts
    {"q": "The Diary Of A CEO podcast Steven Bartlett", "region": "US", "lang": "en", "topic": "Global Podcast - The Diary Of A CEO", "scope": "Worldwide"},
    {"q": "Lex Fridman Podcast", "region": "US", "lang": "en", "topic": "Global Podcast - Lex Fridman (AI & Science)", "scope": "Worldwide"},
    {"q": "Andrew Huberman Lab podcast health", "region": "US", "lang": "en", "topic": "Global Podcast - Huberman Lab (Neuroscience)", "scope": "Worldwide"},
    {"q": "Chris Williamson Modern Wisdom podcast", "region": "US", "lang": "en", "topic": "Global Podcast - Modern Wisdom (Psychology/Culture)", "scope": "Worldwide"},
    {"q": "Mel Robbins podcast", "region": "US", "lang": "en", "topic": "Global Podcast - Mel Robbins (Trauma & Mindset)", "scope": "Worldwide"},
    {"q": "Shawn Ryan Show podcast", "region": "US", "lang": "en", "topic": "Global Podcast - Shawn Ryan Show (Stories & Intel)", "scope": "Worldwide"},
    {"q": "Joe Rogan Experience podcast", "region": "US", "lang": "en", "topic": "Global Podcast - JRE", "scope": "Worldwide"},
    {"q": "Jay Shetty Purpose podcast love healing", "region": "US", "lang": "en", "topic": "Global Podcast - Jay Shetty (Relationships)", "scope": "Worldwide"},
    {"q": "podcast psychology neuroscience human behavior", "region": "US", "lang": "en", "topic": "Global Podcast - Psychology & Behavior", "scope": "Worldwide"},

    # Worldwide Informative & Educational & Documentary
    {"q": "Veritasium science", "region": "US", "lang": "en", "topic": "Global Informative - Veritasium (Physics/Science)", "scope": "Worldwide"},
    {"q": "Kurzgesagt In a Nutshell", "region": "US", "lang": "en", "topic": "Global Informative - Kurzgesagt (Science/Future)", "scope": "Worldwide"},
    {"q": "ColdFusion technology documentary", "region": "US", "lang": "en", "topic": "Global Informative - ColdFusion (Tech History)", "scope": "Worldwide"},
    {"q": "Cleo Abram huge if true science tech", "region": "US", "lang": "en", "topic": "Global Informative - Cleo Abram (Optimistic Tech)", "scope": "Worldwide"},
    {"q": "Johnny Harris documentary investigation", "region": "US", "lang": "en", "topic": "Global Informative - Johnny Harris (Visual Journalism)", "scope": "Worldwide"},
    {"q": "TED talk ideas worth spreading", "region": "US", "lang": "en", "topic": "Global Informative - TED Talks", "scope": "Worldwide"},
    {"q": "deep dive documentary history economy", "region": "US", "lang": "en", "topic": "Global Informative - Deep Dive Documentaries", "scope": "Worldwide"},
    {"q": "AI breakthrough technology documentary 2026", "region": "US", "lang": "en", "topic": "Global Informative - AI & Tech Analysis", "scope": "Worldwide"},
]

seen_ids = set()
candidate_pool = []

# 1. Fetch search queries
print(f"\n1. Executing targeted searches across {len(searches)} specific topic clusters...")
for idx, s in enumerate(searches, 1):
    for order in ["viewCount", "relevance"]:
        try:
            params = {
                "key": api_key,
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
                    candidate_pool.append({
                        "id": vid,
                        "topic": s["topic"],
                        "scope": s["scope"],
                        "source_query": s["q"],
                    })
        except Exception as e:
            print(f"  Error searching '{s['q']}' ({order}): {e}")

print(f"Total unique candidates after targeted searches: {len(candidate_pool)}")

# 2. Fetch Most Popular / Trending charts for informative categories
print("\n2. Querying YouTube Trending / Most Popular charts across key regions...")
trending_regions = [
    {"region": "US", "scope": "Worldwide"},
    {"region": "GB", "scope": "Worldwide"},
    {"region": "SA", "scope": "Arab World"},
    {"region": "EG", "scope": "Arab World"},
    {"region": "AE", "scope": "Arab World"},
]

categories = [None, "27", "28", "25"]  # None = Overall, 27 = Education, 28 = Science & Tech, 25 = News

for tr in trending_regions:
    reg = tr["region"]
    scope = tr["scope"]
    for cat in categories:
        try:
            params = {
                "key": api_key,
                "part": "snippet",
                "chart": "mostPopular",
                "regionCode": reg,
                "maxResults": 25,
            }
            if cat:
                params["videoCategoryId"] = cat
            res = _get_json("videos", params)
            items = res.get("items", [])
            for item in items:
                vid = item.get("id")
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    candidate_pool.append({
                        "id": vid,
                        "topic": f"Trending Chart ({reg}) - Cat {cat or 'Overall'}",
                        "scope": scope,
                        "source_query": f"chart:mostPopular:{reg}",
                    })
        except Exception as e:
            pass

print(f"Total unique candidates in pool: {len(candidate_pool)}")

# 3. Batch retrieve statistics and content details
print(f"\n3. Fetching full video statistics and metadata for {len(candidate_pool)} candidates...")
ids = [c["id"] for c in candidate_pool]
id_to_meta = {c["id"]: c for c in candidate_pool}

video_details = []
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    try:
        res = _get_json("videos", {
            "key": api_key,
            "part": "snippet,statistics,contentDetails,topicDetails",
            "id": ",".join(batch)
        })
        video_details.extend(res.get("items", []))
    except Exception as e:
        print(f"  Error fetching details batch {i}: {e}")

print(f"Retrieved details for {len(video_details)} videos.")

# 4. Filter, score, and rank
processed_videos = []

for v in video_details:
    vid = v.get("id")
    snippet = v.get("snippet", {})
    stats = v.get("statistics", {})
    cd = v.get("contentDetails", {})
    meta = id_to_meta.get(vid, {})

    pub = snippet.get("publishedAt", "")
    # Check published in past 7 days (published_after to published_before)
    if not (pub >= published_after and pub <= published_before):
        continue

    duration_sec = parse_iso_duration(cd.get("duration", ""))
    # Filter: substantive content (>= 180 seconds to filter shorts/clips)
    if duration_sec < 180:
        continue

    views = int(stats.get("viewCount", 0) or 0)
    likes = int(stats.get("likeCount", 0) or 0)
    comments = int(stats.get("commentCount", 0) or 0)

    # Filter out videos with trivial views
    if views < 5000:
        continue

    # Engagement metrics
    like_rate = round((likes / views * 100), 2) if views > 0 else 0
    comment_rate = round((comments / views * 100), 3) if views > 0 else 0
    total_eng_rate = round(((likes + comments) / views * 100), 2) if views > 0 else 0

    # Discussion Intensity: ratio of comments to likes
    disc_intensity = round((comments / likes * 100), 2) if likes > 0 else 0

    # Composite Engagement / Virality Score:
    # (views^0.5) * (likes + comments * 3.0)
    virality_score = round((views ** 0.5) * (likes + comments * 3.0))

    title = snippet.get("title", "")
    channel = snippet.get("channelTitle", "")
    description = snippet.get("description", "")
    tags = snippet.get("tags", [])
    category_id = snippet.get("categoryId", "")

    # Exclude music, gaming streams, cartoons
    title_lower = title.lower()
    ch_lower = channel.lower()
    if any(skip in title_lower for skip in ["official music video", "official video", "lyric video", "minecraft gameplay", "roblox", "live stream replay", "fortnite"]):
        continue

    # Determine primary content format
    if any(w in title_lower or w in ch_lower for w in ["podcast", "بودكاست", "interview", "حوار", "لقاء", "diary of a ceo", "huberman", "fridman", "modern wisdom", "rogan", "talks"]):
        format_type = "Podcast"
    elif any(w in title_lower or w in ch_lower for w in ["documentary", "وثائقي", "الدحيح", "المخبر الاقتصادي", "science", "explained", "deep dive", "analysis", "history", "ted"]):
        format_type = "Informative / Analysis"
    elif duration_sec > 1800:
        format_type = "Long-form Discussion"
    else:
        format_type = "Informative Video"

    processed_videos.append({
        "id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": title,
        "channel": channel,
        "scope": meta.get("scope", "Worldwide"),
        "format_type": format_type,
        "topic_cluster": meta.get("topic", "General"),
        "published_at": pub,
        "duration_seconds": duration_sec,
        "duration_minutes": round(duration_sec / 60, 1),
        "views": views,
        "likes": likes,
        "comments": comments,
        "like_rate_pct": like_rate,
        "comment_rate_pct": comment_rate,
        "total_eng_rate_pct": total_eng_rate,
        "disc_intensity_pct": disc_intensity,
        "virality_score": virality_score,
        "description_snippet": description[:250].replace("\n", " ") if description else ""
    })

print(f"\nTotal qualified substantive videos in last week: {len(processed_videos)}")

# Separate Arab World and Worldwide
arab_videos = [v for v in processed_videos if v["scope"] == "Arab World"]
worldwide_videos = [v for v in processed_videos if v["scope"] == "Worldwide"]

# Sort each by likes, comments, and virality score
arab_by_likes = sorted(arab_videos, key=lambda x: x["likes"], reverse=True)
arab_by_comments = sorted(arab_videos, key=lambda x: x["comments"], reverse=True)
arab_by_score = sorted(arab_videos, key=lambda x: x["virality_score"], reverse=True)

world_by_likes = sorted(worldwide_videos, key=lambda x: x["likes"], reverse=True)
world_by_comments = sorted(worldwide_videos, key=lambda x: x["comments"], reverse=True)
world_by_score = sorted(worldwide_videos, key=lambda x: x["virality_score"], reverse=True)

output_data = {
    "generated_at": now.isoformat(),
    "window_start": published_after,
    "window_end": published_before,
    "total_qualified": len(processed_videos),
    "arab_world_total": len(arab_videos),
    "worldwide_total": len(worldwide_videos),
    "arab_world_top_by_likes": arab_by_likes[:25],
    "arab_world_top_by_comments": arab_by_comments[:25],
    "arab_world_top_by_virality_score": arab_by_score[:25],
    "worldwide_top_by_likes": world_by_likes[:25],
    "worldwide_top_by_comments": world_by_comments[:25],
    "worldwide_top_by_virality_score": world_by_score[:25],
    "all_arab_videos": arab_by_score,
    "all_worldwide_videos": world_by_score
}

output_path = Path("scratch/weekly_research_september_2026.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Saved full research output to {output_path}")

# Print Top Summaries
print("\n" + "="*80)
print("TOP 10 ARAB WORLD (By Virality / Value Score)")
print("="*80)
for i, v in enumerate(arab_by_score[:10], 1):
    print(f"{i}. [{v['channel']}] {v['title'][:65]}...")
    print(f"   Views: {v['views']:,} | Likes: {v['likes']:,} ({v['like_rate_pct']}%) | Comments: {v['comments']:,} | Duration: {v['duration_minutes']}m | Type: {v['format_type']}")
    print(f"   URL: {v['url']}")

print("\n" + "="*80)
print("TOP 10 WORLDWIDE (By Virality / Value Score)")
print("="*80)
for i, v in enumerate(world_by_score[:10], 1):
    print(f"{i}. [{v['channel']}] {v['title'][:65]}...")
    print(f"   Views: {v['views']:,} | Likes: {v['likes']:,} ({v['like_rate_pct']}%) | Comments: {v['comments']:,} | Duration: {v['duration_minutes']}m | Type: {v['format_type']}")
    print(f"   URL: {v['url']}")
