import os
import sys
from pathlib import Path

# Add src
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import search_videos

settings = get_settings()
key = settings.youtube_api_key

candidates_queries = [
    ("The Diary Of A CEO", "long"),
    ("Lex Fridman Podcast", "long"),
    ("Chris Williamson Modern Wisdom", "long"),
    ("Mel Robbins Podcast", "long"),
    ("Lewis Howes School of Greatness", "long"),
    ("Veritasium", "any"),
    ("Andrew Huberman", "long"),
]

all_videos = []
seen_ids = set()

for q, dur in candidates_queries:
    res = search_videos(api_key=key, query=q, mode="recent", duration=dur, limit=5)
    for v in res:
        if v["id"] not in seen_ids:
            seen_ids.add(v["id"])
            all_videos.append(v)

# Filter last 48 hours (published >= 2026-08-26)
filtered = [v for v in all_videos if v.get("published_at", "") >= "2026-08-26"]
# Filter out short clips/reuploads with < 500s or non-official channels if possible, or sort by views
filtered.sort(key=lambda x: x.get("views", 0), reverse=True)

print(f"Total videos found in last 48h: {len(filtered)}\n")
for i, v in enumerate(filtered[:10], 1):
    print(f"{i}. Title: {v['title']}")
    print(f"   Channel: {v['channel']}")
    print(f"   Views: {v.get('views', 0):,}")
    print(f"   Published: {v.get('published_at')}")
    print(f"   Duration: {v.get('duration_seconds', 0)//60} mins")
    print(f"   Link: https://www.youtube.com/watch?v={v['id']}")
    print("-" * 60)
