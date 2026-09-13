import json

with open("scratch_viral_2026.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total candidates in 2026: {len(data)}")

# Sort by different metrics to inspect
# 1. Total views
# 2. Total likes
# 3. Shareability / engagement rate

print("=" * 70)
print("TOP BY VIEWS & ENGAGEMENT (2026):")
print("=" * 70)

for i, d in enumerate(data[:35], 1):
    t = d['title'].encode('ascii', 'replace').decode('ascii')
    ch = d['channel'].encode('ascii', 'replace').decode('ascii')
    topic = d['topic']
    v = d['views']
    l = d['likes']
    c = d['comments']
    eng = d['engagement_rate_pct']
    dur = d['duration_min']
    date = d['published_at']
    vid = d['id']
    print(f"{i}. [{topic}] ({date}, {dur}m)")
    print(f"   Views: {v:,} | Likes: {l:,} | Comments: {c:,} | Eng: {eng}%")
    print(f"   Channel: {ch}")
    print(f"   Title: {t}")
    print(f"   URL: https://www.youtube.com/watch?v={vid}")
    print()
