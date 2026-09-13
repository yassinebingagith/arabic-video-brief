import json
from pathlib import Path

data = json.loads(Path("scratch_september_2026.json").read_text(encoding="utf-8"))
print(f"Loaded {len(data)} videos from scratch_september_2026.json")

# Separate by Arabic vs English/US
arabic = [v for v in data if "Arabic" in v["topic_category"] or any(ord(c) > 0x600 and ord(c) < 0x6FF for c in v["title"])]
us_en = [v for v in data if v not in arabic]

print(f"Arabic count: {len(arabic)}")
print(f"US/English count: {len(us_en)}")

# Let's inspect top 15 Arabic and top 15 US
def clean_print(item, rank):
    print(f"Rank {rank}: [{item['channel']}]")
    print(f"  Title: {item['title']}")
    print(f"  Published: {item['published_at']} | Duration: {item['duration_minutes']} min")
    print(f"  Views: {item['views']:,} | Likes: {item['likes']:,} | Comments: {item['comments']:,}")
    print(f"  Like Rate: {item['like_rate_pct']}% | Eng Rate: {item['eng_rate_pct']}% | Conv Score: {item['conversion_score']:,}")
    print(f"  URL: {item['url']}")
    print(f"  Topic: {item['topic_category']}")
    print("-" * 60)

with open("analysis_output.txt", "w", encoding="utf-8") as out:
    def write_block(title, vlist):
        out.write(f"\n==================== {title} ====================\n\n")
        for i, item in enumerate(vlist[:15], 1):
            out.write(f"{i}. [{item['channel']}] {item['title']}\n")
            out.write(f"   Published: {item['published_at']} | Duration: {item['duration_minutes']} min\n")
            out.write(f"   Views: {item['views']:,} | Likes: {item['likes']:,} | Comments: {item['comments']:,}\n")
            out.write(f"   Like Rate: {item['like_rate_pct']}% | Eng Rate: {item['eng_rate_pct']}% | Score: {item['conversion_score']:,}\n")
            out.write(f"   Topic: {item['topic_category']} | URL: {item['url']}\n\n")

    write_block("TOP ARABIC VIDEOS (SEP 1 - 5, 2026)", sorted(arabic, key=lambda x: (x["views"], x["likes"]), reverse=True))
    write_block("TOP US / ENGLISH VIDEOS (SEP 1 - 5, 2026)", sorted(us_en, key=lambda x: (x["views"], x["likes"]), reverse=True))
    write_block("TOP HIGHEST ENGAGEMENT / CONVERSION (OVERALL)", sorted(data, key=lambda x: x["conversion_score"], reverse=True))

print("Wrote analysis_output.txt")
