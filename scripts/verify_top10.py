import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json
from arabic_video_brief.config import get_settings
from arabic_video_brief.youtube import _get_json, parse_iso_duration

api_key = get_settings().youtube_api_key
ids = [
    "Nqvi_35FVrE",  # pearlieee
    "3ZPnAntJUkA",  # Bailey Schildbach
    "WmieVoaWDwM",  # natalie etched
    "G1kpCs2nC3k",  # Dr Tom Bellamy
    "68UcnUdt6xA",  # Sisyphus 55
    "rhbejide-4c",  # slit
    "5RuccW8ZwV8",  # EVITA PK
    "YDarVXsMnmE",  # Crappy Childhood Fairy
    "m-u13XRBC2M",  # Tim Fletcher
    "V3VvFPhMejs",  # DoctorRamani
]

res = _get_json("videos", {
    "key": api_key,
    "part": "snippet,statistics,contentDetails",
    "id": ",".join(ids)
})

out = []
for it in res.get("items", []):
    s = it["snippet"]
    st = it["statistics"]
    cd = it["contentDetails"]
    total_sec = parse_iso_duration(cd["duration"])
    out.append({
        "id": it["id"],
        "title": s["title"],
        "channel": s["channelTitle"],
        "publishedAt": s["publishedAt"][:10],
        "duration": f"{total_sec // 60}m {total_sec % 60}s",
        "views": int(st.get("viewCount", 0)),
        "likes": int(st.get("likeCount", 0)),
        "url": f"https://www.youtube.com/watch?v={it['id']}"
    })

with open("scripts/top10_verified.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("Saved 10 verified items.")
