import json

with open("scratch_viral_2026.json", "r", encoding="utf-8") as f:
    v1 = json.load(f)

with open("scratch_extra.json", "r", encoding="utf-8") as f:
    v2 = json.load(f)

combined = {v["id"]: v for v in (v1 + v2)}
all_vids = list(combined.values())

# Sort by views & engagement
all_vids.sort(key=lambda x: x["views"], reverse=True)

with open("all_2026_candidates.json", "w", encoding="utf-8") as f:
    json.dump(all_vids, f, indent=2, ensure_ascii=False)

print(f"Total unique videos: {len(all_vids)}")
for i, v in enumerate(all_vids[:20], 1):
    print(f"{i}. [{v.get('published_at')}] {v['channel']}: {v['title'][:60]}... | {v['views']:,} views | {v['likes']:,} likes | {v['comments']:,} comments | {v['engagement_rate_pct']}% eng")
