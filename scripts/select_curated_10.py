import json

with open("all_2026_candidates.json", "r", encoding="utf-8") as f:
    vids = json.load(f)

# Let's curate 10 diverse, top-performing videos across both Arab and Western podcast spheres
# matching: Economy, Love/Relationships, Psychology/Trauma/Behavior, and Monologue/Interview formats.

# Selection criteria:
# - Verified 2026 release date
# - High shareability signals (massive view count, exceptional like count, thousands of comments)
# - Representation of Economy, Love/Relationships, and Psychology

selected_ids = [
    # 1. Economy & Global Crisis (US)
    "PUO51DoSEqk", # Diary of A CEO - Financial Crash Expert: The 90-Day Collapse Timeline They Are Desperately Hiding (8.5M views, 230K likes, 32K comments)
    # 2. Psychology, Self-Worth & Trauma (Global/Arab crossover - #ABtalks x The Wizard Liz)
    "X82zMaQYAwc", # #ABtalks with The Wizard Liz - 19 Years of Abuse, Betrayal, & Rebuilding Her Life (7.0M views, 185K likes, 11K comments)
    # 3. Monologue / Emotional Vulnerability (Arabic - Kadim Al Sahir on #ABtalks)
    "qKgRo3pTRCg", # #ABtalks with Kadim Al Sahir - خُلقت من المأساة (6.0M views, 184K likes, 24K comments)
    # 4. Economy, AI & Wealth Dynamics (US)
    "Bu0xNDLNORU", # Diary of A CEO - Ray Dalio: I Predicted The 2008 CRASH, I Know What Comes Next! (5.7M views, 112K likes, 7.9K comments)
    # 5. Psychology, Habits & Financial Behavior (US)
    "uysZfSEmeRE", # Mel Robbins - 5 Money Rules That Will Change Your Life & Create Financial Freedom (4.1M views, 96K likes, 4.4K comments)
    # 6. Psychology of Influence & Human Behavior (US)
    "9uSXOr-AdAU", # Diary of A CEO - Chase Hughes: The 3 "Dark Psychology" Tricks To Read Anyone's Mind! (3.5M views, 77K likes, 4.2K comments)
    # 7. Love, Relationships & Femininity Dynamics (Arabic)
    "3QN0F5E-DUw", # Glow Up Podcast - كيف تكون الأنثى أنثى؟ (3.4M views, 84K likes, 3.4K comments)
    # 8. Love & Modern Relationship Journey (Arabic)
    "rnGQrsEZdGg", # #ABtalks with Layla & Hesham - قصة حب بدأت في المسلسل واكتملت في الواقع (3.3M views, 40K likes, 10.8K comments)
    # 9. Geopolitical Economy & Sanctions (Arabic)
    "hmtuZdWVNwA", # Al Mokhber Al Eqtisadi (AJ+ Kibreet) - لماذا تساعد روسيا إيران على الصمود وتوريط أمريكا؟ (2.2M views, 33K likes, 1.2K comments)
    # 10. Clinical Psychology & Rewiring Thought Patterns (US)
    "9G2MRFs4vac", # Andrew Huberman & Dr. K (Healthy Gamer) - Unlearn Negative Thoughts & Behaviors Patterns (2.0M views, 43K likes, 2.7K comments)
]

top10 = []
for target_id in selected_ids:
    for v in vids:
        if v["id"] == target_id:
            top10.append(v)
            break

with open("top10_curated.json", "w", encoding="utf-8") as f:
    json.dump(top10, f, indent=2, ensure_ascii=False)

print(f"Successfully curated {len(top10)} videos.")
