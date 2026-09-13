import json

with open("scratch_viral_2026.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("top_candidates_preview.txt", "w", encoding="utf-8") as out:
    for i, d in enumerate(data[:25], 1):
        out.write(f"{i}. [{d['topic']}] ({d['published_at']}, {d['duration_min']} mins)\n")
        out.write(f"   Title: {d['title']}\n")
        out.write(f"   Channel: {d['channel']}\n")
        out.write(f"   Views: {d['views']:,} | Likes: {d['likes']:,} | Comments: {d['comments']:,} | Engagement: {d['engagement_rate_pct']}%\n")
        out.write(f"   URL: https://www.youtube.com/watch?v={d['id']}\n")
        out.write(f"   Description: {d['description']}\n\n")

print("Done")
