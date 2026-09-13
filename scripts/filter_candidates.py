import json

with open("scripts/candidates.json", encoding="utf-8") as f:
    items = json.load(f)

with open("scripts/candidates_summary.txt", "w", encoding="utf-8") as out:
    for i, item in enumerate(items, 1):
        mins = item["duration_sec"] // 60
        title = item["title"]
        channel = item["channel"]
        pub = item["published_at"]
        views = item["views"]
        url = item["url"]
        desc = item["description"][:160]
        out.write(f"{i}. [{channel}] ({pub} | {mins} mins | {views:,} views)\n")
        out.write(f"   Title: {title}\n")
        out.write(f"   URL: {url}\n")
        out.write(f"   Desc: {desc}...\n")
        out.write("-" * 60 + "\n")
print("Written summary successfully")

