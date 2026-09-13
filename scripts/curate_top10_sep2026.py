import json
from pathlib import Path

data = json.loads(Path("scratch_september_2026.json").read_text(encoding="utf-8"))

# Filter out irrelevant gaming/sports if they slipped in
filtered = []
for d in data:
    t = d["title"].lower()
    c = d["channel"].lower()
    # exclude purely gaming/soccer match highlights
    if "gta 6" in t or "barcelona" in t or "الهلال" in t or "fifa" in t or "football" in t:
        continue
    # exclude french/non-english non-arabic
    if any(word in t for word in ["napoléon", "l'affaire", "documentaire"]):
        continue
    filtered.append(d)

print(f"Filtered pool size: {len(filtered)}")

# Separate Arabic vs US/English
arabic = [v for v in filtered if any(ord(c) > 0x600 and ord(c) < 0x6FF for c in v["title"]) or "Arabic" in v["topic_category"] or "ABtalks" in v["channel"] or "AJ+" in v["channel"]]
us_en = [v for v in filtered if v not in arabic]

print(f"Arabic pool: {len(arabic)}")
print(f"US pool: {len(us_en)}")

# Sort each by conversion_score and views
arabic_sorted = sorted(arabic, key=lambda x: (x["conversion_score"], x["views"]), reverse=True)
us_sorted = sorted(us_en, key=lambda x: (x["conversion_score"], x["views"]), reverse=True)

# Select top 5 Arabic and top 5 US representing all user themes
# Themes needed:
# - Podcasts
# - Informative / Documentaries
# - News / Economy
# - Psychology & Neuroscience
# - Health & Science
# - Love, Romance & Trauma

top_selection = []

# Top Arabic:
# 1. ABtalks (Haya Maraachli - Mother Trauma & Vulnerability) -> Love, Trauma & Psychology Podcast
# 2. Daheeh (Che Guevara: Art of Losing with Courage) -> Informative / Psychology of failure & resilience
# 3. Mokhbir Eqtisadi (China, US & Iran / Palantir) -> News, Economy & Geopolitics
# 4. ArabCast with Dr. Fawzia Al-Deraa (Psychology of Male Attraction & Marriage) -> Love, Romance & Relationships
# 5. Mikhtalif Podcast (Trauma Surgery / Life and Death Decisions) -> Health, Psychology & High Emotion

# Top US:
# 1. Raj Shamani x Andrew Huberman (Become Mentally Dangerous With Daily Habits) -> Science, Neuroscience & Psychology
# 2. The Diary Of A CEO x Andrew Huberman (Optimize Brain & Body Routine) -> Health, Science & Self-Optimization
# 3. Shawn Ryan Show (Navy SEAL / Shawn Ryan Personal Hell & Survival) -> Gripping Trauma, Mindset & Resilience Podcast
# 4. Annie Elise (Netflix, Mica Miller & Abuse / Relationship Breakdown) -> Love, Trauma, Crime & Relationship Investigation
# 5. Jay Shetty x Jillian Turecki (Dating Coach: #1 Sign He'll Stay / Avoid Heartbreak) -> Love, Romance & Dating Psychology

selected_ids = [
    # US
    "Y566_T-YlNQ",  # Huberman x Raj Shamani
    "MGxcosNuC8k",  # DOAC x Huberman
    "kUHsD5fWLs0",  # Annie Elise - Toxic Relationship & Trauma
    "2w-msuhTLd0",  # Shawn Ryan - Trauma / Near Death
    "P1OyIznd1aY",  # Jay Shetty x Jillian Turecki - Dating & Love

    # Arabic
    "Tny-11owWRw",  # ABtalks - Haya Maraachli (Mother trauma)
    "uDEwPkzOKSg",  # Daheeh - Guevara (Psychology of courage)
    "uL1Ie3Q7lRU",  # Mokhbir Eqtisadi - Geopolitics & Economy
    "p1oGxUhsyeg",  # ArabCast - Dr Fawzia Al-Deraa (Love & Romance)
    "LyxZez5Nixk",  # Mikhtalif - Trauma Surgery (Health & Life-or-death)
]

curated_map = {v["id"]: v for v in filtered}
final_10 = []
for vid in selected_ids:
    if vid in curated_map:
        final_10.append(curated_map[vid])

# If any missing, fallback to top scored
while len(final_10) < 10:
    for v in filtered:
        if v not in final_10:
            final_10.append(v)
            break

with open("top10_september_2026.json", "w", encoding="utf-8") as f:
    json.dump(final_10, f, ensure_ascii=False, indent=2)

print("Saved top 10 to top10_september_2026.json")
