---
name: arabic-video-brief
description: Discover or process public YouTube videos into 20-second vertical 9:16 MP4 briefs with deep instrumental background music, readable Modern Standard Arabic summaries, bold source info cards, translated pure Arabic headline hooks, and universal narrative post descriptions (<2,000 characters).
---

# Arabic Video Brief

Create reviewable 9:16 Arabic video briefs through the local engine. Always process videos **sequentially one-by-one** with immediate per-item feedback.

## User Interaction & Entry Protocol

### Step 1: Communication Language Preference

When the user starts the skill, launches it, or greets (e.g., "Hey", "Play the skill", "Start"):

1. **Ask for Language:** Before presenting the workflow options, first ask the user which language they prefer for the chat conversation (e.g., English, العربية, Français, etc.).
2. **Chat Persistence:** Once the user specifies their preferred language (e.g., English), conduct **all subsequent conversation, prompts, explanations, status updates, and summary reports strictly in that chosen language**.
3. **Output Content Invariant:** Regardless of the selected chat language, **all produced brief files and video content (`brief.mp4`, `summary-ar.txt`, `post-title.txt`, `post-description.txt`) must strictly remain in pure Modern Standard Arabic** as specified in the Output Specifications.

### Step 2: Mode Selection

In the user's chosen chat language, prompt them to choose their preferred mode:

1. **Paste YouTube Link(s):** Provide a single YouTube link or multiple links to process into Arabic video briefs sequentially one by one.
2. **Start a Search:** Provide one or multiple search topics/themes to discover new high-value videos using the official **YouTube Data API v3** (`.env`).

### Step 2.5: Pipeline Version Selection

Prompt the user or accept `--version v1|v2`:

1. **(Recommended) V2 — Arabic Hook, 4 Summary Pages, Ending Card (26s):** Features a dedicated transcript hook with optional ElevenLabs TTS narration, 4 balanced sentence-aligned pages (35–40 words each), and a dedicated conclusion & CTA page. See [references/v2-render-spec.md](references/v2-render-spec.md).
2. **V1 — Legacy Format (25s):** The classic 2-page format with 5s static card + 15s video stream. See [references/v1-render-spec.md](references/v1-render-spec.md).

### Step 3: LLM Engine Selection

Before processing videos, prompt the user with `ask_question` to select how transcription extraction, translation, and Arabic summarization should be processed:

1. **(Recommended) Antigravity Brainstorm LLM:** Direct high-quality reasoning and synthesis with no external API cost.
2. **VyceAI API:** Uses credentials from `.env` (`VyceAI_API_KEY` / `VyceAI_Model`).
3. **Gemini API:** Uses `GEMINI_API_KEY` from `.env`.
4. **SeekAI API (`deepseek-v4-flash`):** Uses SeekAI endpoint from `.env`.

> [!IMPORTANT]
> **Default Fallback:** If the user skips this question or leaves it unspecified, **automatically use the Antigravity Brainstorm LLM** as the default engine.

### Step 3.2: Deep-Dive Educational Synthesis Decision Gate (ملخص معرفي مطوّل وشامل)

Prompt the user with `ask_question`:
> **"Generate exhaustive Deep-Dive Educational Synthesis (`deep_dive_summary.txt`) for this video/batch?"**
- **Option 1: No (Default/Normal):** Process video without deep-dive synthesis. No extra file is created.
- **Option 2: Yes:** A dedicated synthesis call executes the Senior Knowledge Architect & Content Strategist prompt on the full transcript, creating `deep_dive_summary.txt` in the folder without character limits. This text serves as the rich educational caption when posting Facebook Photo Posts (`--mode photo`).

### Step 3.5: Thumbnail Generation Protocol (Thumbnail Master 4.0 Engine)

Before processing or rendering assets, ask the user whether thumbnails are desired using a 2-tier question sequence:

#### Question A: "Generate thumbnails for this video/batch?"
- **Option 1: No (Default/Normal)**
  - Process video normally without thumbnails, without API calls, without KIE.ai, and **without creating any thumbnail prompt `.txt` files**.
- **Option 2: Yes**
  - Proceed to Question B.

#### Question B: "Thumbnail Generation Method:"
- **Option 1: Manual Generation (Prompts only)**
  - The engine generates high-CTR prompt files in the video folder:
    - `thumbnail_prompt_facebook_4x5.txt` (1080×1350 for Facebook photo posts)
    - `thumbnail_prompt_vertical_9x16.txt` (1080×1920 with 3:4/4:5 crop-proof safe margins)
    - `THUMBNAIL_GUIDE.md`
  - **4.0 Engine Capabilities**:
    - **Focal Archetypes**: Automatically routes between *Emotive Portrait*, *Split-Screen Comparison*, *Symbolic Artifact*, *Dramatic Scene*, or *Conceptual Metaphor* based on topic.
    - **Single Dominant Title**: Uses `post-title.txt` as the sole headline with dual-tone calligraphy (power-word highlighted in gold/crimson). No secondary conclusion text to clutter the image.
    - **Feed Crop Proofing**: Title placed in upper safe zone (Y: 320–560) and bottom 25% kept strictly text-free to clear platform UI overlays (`▷ 515`, duration, usernames).
    - **10 Visual Styles**: Full style menu with strict Anti-AI-Slop tactile texture enforcement.
  - In chat, the agent **must remind the user** to generate their images externally and save them in the video folder under the required names:
    - `cover_facebook_4x5.png` (or `.jpg`)
    - `cover_vertical_9x16.png` (or `.jpg`)
- **Option 2: KIE.ai API (Automated Image Generation & Sanitization)**
  - The pipeline automatically submits the full master prompts to KIE.ai API (`gpt-image-2-5-sunburst-image-to-image`, 1K quality).
  - Automatically downloads, scales, and crops to exact dimensions:
    - `cover_facebook_4x5.png` (1080×1350)
    - `cover_vertical_9x16.png` (1080×1920)
    - `cover_vertical_9x16_yt_opt.jpg` (YouTube-optimized under 2MB)
  - Automatically executes **Anti-AI Sanitization** (`sanitize_image(force=True)`) to strip C2PA provenance and AI metadata so Facebook/Instagram never flag the post as AI-generated.

### Step 4: Publishing Execution Protocol (Live Terminal vs. Background Service)

When the user asks to publish or upload a video (e.g., "publish this video", "upload to all platforms"):
**Always ask the user how they would like to run the publishing automation:**

1. **Option A (Watch Live on Screen - Recommended):** Provide the user the exact command to paste into their Antigravity IDE terminal (e.g., `python scripts/avbrief.py post --folder "outputs/Love and Trauma/<video_folder>" --platform all`). This executes in their desktop session, opening the real Chrome window live on their monitor so they can watch every step.
2. **Option B (Run in Background):** The agent triggers the command internally as an isolated background task.

## Required Behavior & Output Specifications

### 1. Sequential Execution

- Process batches **strictly sequentially one-by-one**.
- Deliver and report the completed brief, title, and description of each video before advancing to the next.

### 1b. Strict Literal-Equivalent Title Translation (MANDATORY)

- **Post Title & Voiceover Hook:** The Arabic title (`post-title.txt`, hook narration, and description header) must be a **100% direct, faithful, literal-equivalent translation** of the original YouTube video title into clear Modern Standard Arabic.
- **NEVER Paraphrase or Re-invent Titles:** Do NOT create a conceptual, abstract, or interpretive title from scratch based on the whole video theme.
  - *Example 1:* If original is *"Why More Freedom Is Making You Miserable"*, translate directly: `لماذا تجعلك الحرية الزائدة تعيساً؟` (NEVER rewrite into `فخ كثرة الخيارات: لماذا تسرق الحرية المطلقة سعادتنا`).
  - *Example 2:* If original is *"Give Me 47 Minutes If You Still Can't Move On From Your Ex"*, translate directly: `امنحني 47 دقيقة إذا كنت لا تزال عاجزاً عن تجاوز شريكك السابق` (NEVER rewrite into `لماذا تعجز عن تجاوز الانفصال والتعافي من علاقتك السابقة؟`).
- This direct translation must be the text saved in `post-title.txt`, displayed at the top of the narrative description, and spoken in the V2 hook voiceover.


### 2. Video Render Layout (28 Seconds - Version 1)

- **Top Panel (1080×760):**
  - **Motion:** 2.5s source card with kinetic Ken Burns push-in zoom + 17.5s video stream playback + 8s thumbnail card with kinetic Ken Burns zoom during CTA. Zero static freeze frames.
  - **Seamless Gradient Feather:** Alpha gradient fading from `y=490` to `y=760` into pure `#000000` black, eliminating all hard borders/letterboxing and avoiding Instagram's "video has a border" warning.
  - **Floating Glassmorphic Metadata Badge (1016×176px at y=556, r=26px):**
    - **RTL / BiDi Awareness:** For Arabic content, layout is strictly Right-to-Left (red YouTube play icon on the right, title right-aligned, metadata ordered `[Channel Name]` • `[View Count]` • `[Upload Date]`). For English content, layout is Left-to-Right.
    - **Multi-line Title:** Full video title wraps across 2–3 balanced lines without ellipsis (`...`) truncation.
    - **Metadata Row:** Channel name, view count, and upload date cleanly rendered with centered bullet separators.
- **Background Music:** Contemplative instrumental track (`assets/music/vangelis_la_petite_fille_de_la_mer.mp3`). Immediate hook at t=0s, steady volume, and a smooth 2.0-second fade-out between 18.0s and 20.0s.
- **Outro Voiceover (The Conversion Bridge):** Dedicated outro audio narration (`assets/music/last voicever.mp3`) plays during the final 8 seconds (20.0s - 28.0s) across the CTA page.
- **Left-Shift Safe Zone:** All Arabic text blocks on Page 1 & Page 2 are shifted 6% to the left (~65px) so that right-side platform action buttons never overlap with the Arabic text.
- **Page 1 (0–10s):** Direct translation of source YouTube title, center headline, dynamic category, and 70–80 word storytelling hook.
- **Page 2 (10–20s):** 70–80 word core value delivery, pro-tips or hidden game takeaway. Footer prompt: `اقرأ الوصف لمزيد من التفاصيل`. Total words 140–160.
- **CTA Page (20–28s):** Dedicated 8.0-second Call-to-Action ending page:
  - Top panel: Dynamic thumbnail card with subtle Ken Burns push-in zoom and floating metadata badge.
  - Bottom panel:
    - Middle action pill: `احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد` (34px, 15% platform safe margin).
    - Capsule Fikr circular logo and brand label.
    - Bottom gold badge: `السر الأهم والخطوات التطبيقية في الوصف بالأسفل` with downward chevron.
    - Outro narration bridge playing clearly.

### 2b. Video Render Layout (36.5 Seconds - Version 2 Extended Format)

- **Top Panel (1080×760):**
  - `0:00 - 0:02.5`: Source Card with kinetic Ken Burns push-in zoom and floating translucent metadata badge.
  - `0:02.5 - 0:28.5`: Highlighted Video Segment (26.0 seconds extracted from the source clip with seamless bottom gradient blend and floating metadata badge). Zero hard borders.
  - `0:28.5 - 0:36.5`: Dynamic thumbnail card with subtle Ken Burns push-in zoom during the final 8.0s conclusion & CTA page.
  - **Floating Glassmorphic Metadata Badge (1016×176px at y=556, r=26px):**
    - **RTL / BiDi Awareness:** For Arabic content, layout is strictly Right-to-Left (red YouTube icon on right, right-aligned title, RTL metadata order). For English content, layout is Left-to-Right.
    - **Multi-line Title:** Full video title wraps cleanly without truncation.
    - **Seamless Alpha Gradient:** Feathers from `y=490` to `y=760` into pure black `#000000`.
- **Bottom Panel (1080×1160) - 4 Text Pages + 1 Conclusion Screen:**
  - **Page 1 (0:00 - 0:09.0, 9.0s):** Main video title in Modern Standard Arabic + Category tag + Hook/Setup (30–44 words, ~20–25% gold-highlighted punch words).
  - **Page 2 (0:09.0 - 0:15.5, 6.5s):** Key insight 1 (30–44 words).
  - **Page 3 (0:15.5 - 0:22.0, 6.5s):** Key insight 2 (30–44 words).
  - **Page 4 (0:22.0 - 0:28.5, 6.5s):** Key insight 3 / practical advice (30–44 words).
  - **Conclusion & CTA Screen (0:28.5 - 0:36.5, 8.0s):**
    - **Conclusion Text:** Gold-highlighted memorable punchline (max 12 words).
    - **Secondary CTA:** Sleek dark pill with outline: `احفظ الفيديو لتستفيد منه لاحقاً`.
    - **Primary Description Badge:** Prominent, filled Gold Badge (`#F5C518`) with bold black text: `السر الأهم والخطوات التطبيقية بانتظارك في الوصف بالأسفل`.
    - **Indicator Arrow:** Sharp vector golden chevron/arrow pointing downwards directly at the platform's description box.
    - **Branding:** 130px circular Capsule Fikr logo with gold border ring and `كبسولة فكر` gold typography.
- **Audio Architecture:**
  - **Hook Narration:** ElevenLabs TTS Arabic voiceover at `t=0s` (`volume=1.3`, natural human cadence).
  - **Background Instrumental:** (`naruto_sadness_and_sorrow.mp3`) ducked to `0.12` during speech, swelling smoothly to `0.70` over 0.6s when narration ends.
  - **Music Outro Fade:** Background music fades out smoothly before the conclusion page (26.5s – 28.5s).
  - **Outro Voiceover:** (`assets/music/last voicever.mp3`) starts at `t=28.5s` (`volume=1.1`) and plays for 8.0 seconds during the Conclusion & CTA screen (28.5s – 36.5s).
  - **amix Parameters:** Configured with `normalize=0` to ensure vocals remain bold, clear, and unattenuated.

### 3. Post-Description File (`post-description.txt`)

- In-depth, continuous narrative article style with descriptive thematic section headings in simplified Modern Fusha:
  - **Line 1:** `عنوان الموضوع الشامل بالعربية – اسم المتحدث أو القناة`
  - **Opening paragraph:** Addictive, relatable hook (around 220–270 characters) drawing the reader into the topic immediately with zero meta-talk.
  - **Subsections:** 3 to 4 comprehensive thematic sections starting with elegant diamond bullet headings (`◈ عنوان المحور الوصفي ◈`) followed by detailed explanatory paragraphs. Strictly avoid surrounding headings with hyphens (`-عنوان-`) to prevent YouTube's native strikethrough formatting bug.
  - **Mandatory Real-World Examples:** Every section must pack concrete, tangible examples (mentioning specific professions, everyday scenarios, real numbers, or tangible analogies) rather than speaking in vague generalities or academic theory.
  - **Final Section:** Concrete actionable pro-tips / practical steps (or deep future implications if purely informative).
  - **No chapters, no timestamps, no bullet points, and no hooks.**
  - **Dynamic Subscription CTA:** Varied call-to-action rotated across posts (e.g. `🔔 تابعنا ليصلك يومياً ملخص لأهم المقاطع والبودكاست الفكرية والعلمية!`, `✨ تابع الصفحة يومياً لاكتشاف أعمق الأفكار والملخصات المعرفية المركزة!`).
  - **Dynamic Topic Hashtags:** 2–3 niche-specific hashtags matching the video's actual theme (e.g., `#علم_النفس`, `#فلسفة`, `#ذكاء_اصطناعي`, `#تاريخ`) combined with rotating broad hashtags (strictly no `#shorts` or platform names).
- **CRITICAL CHARACTER LIMIT:**
  - Absolute maximum: **2,000 characters INCLUDING spaces**.
  - Preferred target: **1,750–1,950 characters including spaces**.
  - NEVER exceed 2,000 characters (Count letters, spaces, punctuation, line breaks, numbers, hashtags, title).

### 3b. Deep-Dive Educational Synthesis (`deep_dive_summary.txt`)

- **Exhaustive, High-Prestige Long-Form Synthesis:** Designed for long-form consumption, executive takeaways, newsletter editions, and deep Facebook photo captions:
  - **Human Prose with Zero AI Markers:** Strictly NO markdown header symbols (`#`, `##`, `###`), NO dividers (`---`), and NO bold asterisks (`**`). All emphasis is driven through rhetorical rhythm and eloquent phrasing.
  - **Full Intellectual Depth & Concrete Data:** Preserves all exact percentages, statistics, numbers, timeframes, and specific case studies from the source transcript without superficial condensation.
  - **Conceptual Reliability with English Terms:** Key technical frameworks, models, and coined terms must include their original English phrasing in parentheses `(...)` next to their Arabic names (e.g. `(Jay Shetty)`, `(The Power of Silence)`, `(Highlight Reel Syndrome)`, `(The Comparison Trap)`, `(The Rule of 5)`, `(Social Detox)`, `(Compounding Skills & Wealth)`).
  - **Elegant Diamond Thematic Sections:** Uses clean line breaks and diamond symbols (`◈ [عنوان المحور الوصفي الجذاب]`) instead of robotic labels (`المحور الأول`, `النموذج النظري`, `التطبيق العملي`).
  - **Narrative Actionable Roadmap:** Broken into coherent paragraphs with narrative transition words (`أولاً، ...`, `ثانياً، ...`, `ثالثاً، ...`) instead of dashed lists.
  - **Organic Conclusion & Emotional Question:** Concludes with an uplifting philosophical summary flowing directly into a deep, introspective question (without any `سؤال التأمل:` label), followed by a warm, natural community call to action (commenting experiences, saving the summary for later, and sharing).

### 4. Output Files & Anti-Bot Stealth Architecture

- `CapCut_1080p_{YYYYMMDD}_{clean_slug}.mp4` (28s in V1 / 36.5s in V2 1080×1920 MP4)
  - **Strict Single-Video Anti-Bot Protocol:** Directly staged as `CapCut_1080p_{YYYYMMDD}_{clean_slug}.mp4`. Any intermediate or temporary `brief.mp4` is **immediately deleted upon creation** so platforms never detect bot script filenames on disk or in file pickers.
  - **Anti-Bot Container Spoofing:** Rendered with `-map_metadata -1`, `+bitexact`, `-metadata:s:v:0 encoder=CapCut`, `-metadata:s:a:0 encoder=CapCut`, `-metadata major_brand=mp42`, completely removing FFmpeg `Lavf`/`Lavc` traces.
  - **Acoustic De-duplication:** Subtle imperceptible audio micro-jitter (±0.5%–1.0%) to prevent Content ID and platform algorithms from clustering videos as repeated duplicate templates.
- `summary-ar.txt` (140–160 word Modern Standard Arabic abstract)
- `post-title.txt` (Faithful Arabic translation of the YouTube title, clean without `#shorts`)
- `post-description.txt` (In-depth narrative description under 2,000 chars, diamond headers `◈`, dynamic hashtags)
- `deep_dive_summary.txt` (Exhaustive, human-written deep-dive synthesis with English parenthetical concepts, zero markdown signs/annotations, and organic CTA)
- `transcript.json` (Transcript metadata)
- `manifest.json` (Full job manifest)

## Commands

```powershell
# Diagnostics & configuration check
python scripts/avbrief.py doctor

# Search candidate videos
python scripts/avbrief.py search --query "topic" --mode popular --region US --language ar --limit 5

# Generate Arabic briefs
python scripts/avbrief.py run --source "https://www.youtube.com/watch?v=..."
python scripts/avbrief.py run --job jobs/love_and_trauma.json

# Fast re-render of an existing brief folder without repeating analysis/LLM calls
python scripts/avbrief.py rerender --folder "outputs/<folder>"

# High-CTR Thumbnail & Photo Prompt Generation (Thumbnail Master 4.0)
# Auto-skips 4:5 Facebook thumbnail if deep_dive_summary.txt is not requested, saving API tokens & credits
python scripts/avbrief.py thumbnail --folder "outputs/<folder>"
python scripts/avbrief.py thumbnail --folder "outputs/<folder>" --kieai
# Optional flags: --facebook (force 4:5 FB generation) / --no-facebook (skip 4:5 FB generation)

# Exhaustive Deep-Dive Educational Synthesis (deep_dive_summary.txt)
python scripts/avbrief.py deepdive --folder "outputs/<folder>"
python scripts/avbrief.py deepdive --folder "outputs/<folder>" --provider vyceai

# Sanitize cover images: Eradicate C2PA provenance and AI metadata for untraceable organic posting
python scripts/avbrief.py sanitize --folder "outputs/<folder>"

# Social Media Publishing Automation (Playwright persistent profile)
# 1. One-time interactive login to your accounts:
python scripts/avbrief.py login [--platform all|youtube|tiktok|meta]

# 2. Publish a specific video folder on-demand:
# Video Reel publication (YouTube Shorts + TikTok + Meta [BOTH Facebook & Instagram simultaneously]):
python scripts/avbrief.py post --folder "outputs/<video_folder>" --platform all
python scripts/avbrief.py post --folder "outputs/<video_folder>" --platform youtube
python scripts/avbrief.py post --folder "outputs/<video_folder>" --platform tiktok
python scripts/avbrief.py post --folder "outputs/<video_folder>" --platform meta --mode video

# Platform destination targeting on Meta:
#   When user says "Meta" -> publishes to BOTH Facebook AND Instagram at the same time.
#   When user says "Instagram" -> use '--target instagram' (Instagram ONLY).
#   When user says "Facebook" (video) -> use '--target facebook' (Facebook ONLY).

# Facebook Photo Post publication (Facebook ONLY with 4:5 image + deep-dive caption):
python scripts/avbrief.py post --folder "outputs/<video_folder>" --platform meta --mode photo

# Optional publish flags:
#   --mode video|photo   Reel video (Facebook + Instagram) vs photo post (Facebook ONLY)
#   --target meta|instagram|facebook Explicit destination override on Meta (default: meta for video, facebook for photo)
#   --draft              Save as draft / unlisted instead of publishing now
#   --schedule "YYYY-MM-DD HH:MM"  Schedule publication natively
#   --force              Re-upload even if recorded as published
#   --headless           Run browser in background (default is visible headful)
```
