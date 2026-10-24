---
name: arabic-video-brief
description: Process or discover YouTube sources for Arabic content. V1 creates a 38-second two-page video brief; V2 creates a 42.2-second four-page brief. V3 prepares Instagram carousel and Facebook photo packs with source-thumbnail references, Arabic copy, captions, and a choice of API, ChatGPT/MCP, or manual image generation. Supports new links, existing transcripts, and combined video plus image packs.
---

# Arabic Video Brief

Create reviewable 9:16 Arabic video briefs through the local engine, or V3 image prompt packs through the workflow in [references/v3-carousel-pack.md](references/v3-carousel-pack.md). Always process sources **sequentially one-by-one** with immediate per-item feedback.

Preserve the user's current video design: title-only opening narration (with the V2 suffix `ملخص الفكرة في ثوانٍ، والتفاصيل الكاملة في صندوق الوصف`), existing outro recording, V1/V2 music choices, blue blurred frame, and export settings. Do not introduce full-summary narration, require a paid voice plan, or narrow the topic range. V3 has independent, source-led art direction without a compulsory palette, logo, or mascot.

For V1/V2 writing and video thumbnails, read [references/v1-v2-editorial-style.md](references/v1-v2-editorial-style.md). Use concrete explanatory copy and source-led hybrid covers. Keep V3 unchanged.

## User Interaction & Entry Protocol

### Required setup before any V1/V2 production

For **V1, V2, V1 + V3, or V2 + V3**, resolve every missing video setup choice before analysis, rendering, or thumbnail production. Selecting V1 + V3 specifies formats only: it does **not** answer the deep-dive or thumbnail questions. V3-only is the sole exception to these video questions.

1. V1 or V2 (already answered when the user names it).
2. Analysis engine (Step 3).
3. Deep-dive summary: yes or no (Step 3.2).
4. Video thumbnail prompts/images: yes or no; if yes, manual prompts or KIE.ai (Step 3.5).

Use the available user-question tool, or a plain chat question if that tool is unavailable; `ask_question` below means the host's supported question mechanism, not an invented tool name. Bundle missing independent questions to reduce interruptions. Reuse explicit current-batch answers or an explicit ongoing user preference. An absent answer, a preselected UI option, an API key's presence, “be quick,” or the desire to “get to the point” is not a choice. Defaults in the menus are suggestions, not permission to omit questions. If a required answer is pending, wait before dependent production. Do not infer “no” from silence.

Record the actual answers and their scope in the job notes or `run-options.json`; never invent an answer to satisfy a check. Read-only source/folder inspection is allowed while waiting. For agent/CLI execution, pass the answers explicitly: `--version v1|v2`, `--deepdive` **or** `--no-deepdive`, and `--thumbnails none|manual|kieai`. JSON jobs may specify `version`, boolean `deepdive`, and `thumbnails` with those exact values. Missing choices in a non-interactive `run` now produce `SETUP_REQUIRED` before production. Do not work around that by using guessed flags or direct pipeline calls.

Video thumbnails and V3 images are separate deliverables. A V3 carousel cover never substitutes for the video thumbnail prompt files. If the user selects video thumbnails, check the requested prompt files/guide actually exist before reporting completion. If a requested optional stage failed while the video succeeded, report that partial outcome rather than claiming the whole request is complete.

### Step 1: Communication Language Preference

When the user starts the skill, launches it, or greets (e.g., "Hey", "Play the skill", "Start"):

1. **Ask for Language Only If Unknown:** Honor an explicit or already established chat language; otherwise ask which language they prefer (e.g., English, العربية, Français).
2. **Chat Persistence:** Once the user specifies their preferred language (e.g., English), conduct **all subsequent conversation, prompts, explanations, status updates, and summary reports strictly in that chosen language**.
3. **Output Content Invariant:** Regardless of the selected chat language, **all produced brief files and video content (`brief.mp4`, `summary-ar.txt`, `post-title.txt`, `post-description.txt`) must strictly remain in pure Modern Standard Arabic** as specified in the Output Specifications.

### Step 2: Mode Selection

Honor links, source folders, and mode choices already supplied. If the intended task is unclear, offer:

1. **Paste YouTube Link(s):** Provide a single YouTube link or multiple links to process into Arabic video briefs sequentially one by one.
2. **Start a Search:** Provide one or multiple search topics/themes to discover new high-value videos using the official **YouTube Data API v3** (`.env`).
3. **V3 Carousel + Photo Pack:** Use new YouTube links or selected existing transcripts to prepare manual image prompts and references.

### Step 2.5: Pipeline Version Selection

Use the same skill name, `$arabic-video-brief`, with the requested mode:

1. **V1 — Two-Page Video (38s):** Two 15-second reading pages, then an 8-second question ending. See [references/v1-render-spec.md](references/v1-render-spec.md).
2. **V2 — Four-Page Video (42.2s):** Existing title hook and four-page pacing, then an 8-second question ending. See [references/v2-render-spec.md](references/v2-render-spec.md).
3. **V3 — Instagram Carousel + Facebook Photo Pack:** One 4–6-slide Instagram carousel and one separate Facebook photo concept per source, with standalone prompts, reference instructions, Arabic captions, and a generation plan. After preparing the entire pack, ask whether to generate via a configured image API, in one persistent ChatGPT/MCP generation session, or to stop for manual generation. Follow [references/v3-carousel-pack.md](references/v3-carousel-pack.md).

**Routing rules:**
- For an ambiguous video request such as “Process this video,” ask **“V1 (38s) or V2 (42.2s)?”** before running the video pipeline. Never silently choose the CLI default. An explicit version or an established choice for this batch satisfies the gate.
- “V3”, “do carousel”, “launch carousel”, or “carousel and photo pack” selects V3. If sources are unspecified, ask **“Which YouTube links or existing video folders should I use for the carousel and Facebook photo packs?”** List identifiable existing candidates when useful; do not process every old video automatically.
- If the user requests video plus V3, ask V1/V2 only if unknown. If the V3 subset is unclear, ask which selected videos also need packs. Reuse the matching source transcript; do not transcribe again unnecessarily.
- V3 alone bypasses the video-only engine, deep-dive, and thumbnail gates below. Its prompts and references are always included. Do not call the existing thumbnail generator or renderer for V3.
- V3 is an agent-authored workflow, **not** `--version v3` in the CLI. Do not invent a CLI command for it.
- For V3, finish all source references, standalone prompts, captions, scripts and the generation plan **before** the single generation-method question. Never select an image provider, use an API key, launch browser automation, or generate images without the user's choice. Selecting a method authorizes that episode's sequential generation and saving to its V3 output folder; publishing remains separate.
- **V3 visible-number rule:** use Western/ASCII digits `0 1 2 3 4 5 6 7 8 9` in *all* Arabic viewer-facing scripts, headlines, body, captions, charts, visual prompts and generated images. Do not use Eastern Arabic-Indic `٠١٢٣٤٥٦٧٨٩` or Persian `۰۱۲۳۴۵۶۷۸۹` glyphs. Example: `21–35 يوماً`, `2–12`, `18–19`. Preserve the original reference image and transcript as source evidence even if they contain other glyphs. Check the final images visually as well as the written pack.

Examples:
- `$arabic-video-brief V1 — process this video: <URL>`
- `$arabic-video-brief V3 — make a carousel and Facebook photo prompt pack from: <URL>`
- `$arabic-video-brief V3 — use the existing transcript in <folder>`
- `$arabic-video-brief — make V2 and a V3 pack for this link: <URL>`

### Step 3: LLM Engine Selection

Before processing videos, prompt the user with `ask_question` to select how transcription extraction, translation, and Arabic summarization should be processed:

1. **(Recommended) Antigravity Brainstorm LLM:** Direct high-quality reasoning and synthesis with no external API cost.
2. **VyceAI API:** Uses credentials from `.env` (`VyceAI_API_KEY` / `VyceAI_Model`).
3. **Gemini API:** Uses `GEMINI_API_KEY` from `.env`.
4. **SeekAI API (`deepseek-v4-flash`):** Uses SeekAI endpoint from `.env`.

> [!IMPORTANT]
> **Suggested engine:** Antigravity Brainstorm LLM. Use it when the user chooses it or explicitly asks you to choose the engine; do not treat an unanswered setup question as consent. In Brainstorm mode, author the complete analysis JSON (including `ending_question_ar`, V2 `pages` and `ending_text_ar`, and `thumbnail_hook_ar` when covers are requested) and pass `--provider brainstorm --analysis <file>`; do not silently make paid analysis calls.

### Step 3.2: Deep-Dive Educational Synthesis Decision Gate (ملخص معرفي مطوّل وشامل)

Prompt the user with `ask_question`:
> **"Generate exhaustive Deep-Dive Educational Synthesis (`deep_dive_summary.txt`) for this video/batch?"**
- **Option 1: No (Default/Normal):** Process video without deep-dive synthesis. No extra file is created.
- **Option 2: Yes:** A dedicated synthesis call executes the Senior Knowledge Architect & Content Strategist prompt on the full transcript, creating `deep_dive_summary.txt` in the folder without character limits. This text serves as the rich educational caption when posting Facebook Photo Posts (`--mode photo`).

### Step 3.5: Thumbnail Generation Protocol (Source-led Hybrid Engine)

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
  - **Source-led hybrid direction**: Inspect the original thumbnail. Preserve its actual medium and style (including surrealism), adapted to this episode's topic. Consider face-led, scene/object-led and hybrid compositions; choose the clearest curiosity gap. No automatic dark/gold palette, portrait, desk, manuscript or cinematic treatment.
  - **Short thumbnail hook**: Prefer 3–8 Arabic words, maximum 10 words / 70 characters. Save as `thumbnail-hook-ar.txt` when authored; keep the full translated post title and narration unchanged. Older folders may delegate hook authoring to the image generator, explicitly marked pending in the guide.
  - **Quality invariants**: Dimensional faces when present, source identity, purposeful lighting and natural or intentionally artistic textures; no waxy skin, generic CGI gloss or distorted Arabic.
  - **Feed framing**: Retain vertical title Y 320–560, central subject Y 580–1420 and text-free bottom Y 1450–1920. Verify the actual preview; square crops can trim the headline.
  - In chat, the agent **must remind the user** to generate their images externally and save them in the video folder under the required names:
    - `cover_facebook_4x5.png` (or `.jpg`)
    - `cover_vertical_9x16.png` (or `.jpg`)
- **Option 2: KIE.ai API (Automated Image Generation & Sanitization)**
  - The pipeline automatically submits the full master prompts to KIE.ai API (`gpt-image-2-5-sunburst-image-to-image`, 1K quality).
  - Automatically downloads, scales, and crops to exact dimensions:
    - `cover_facebook_4x5.png` (1080×1350)
    - `cover_vertical_9x16.png` (1080×1920)
    - `cover_vertical_9x16_yt_opt.jpg` (YouTube-optimized under 2MB)
  - Automatically executes **Anti-AI Sanitization** (`sanitize_image(force=True)`) to strip C2PA provenance and AI metadata from the exported file; this does not guarantee platform AI-label behavior.

### Step 4: Publishing Execution Protocol (Live Terminal vs. Background Service)

When the user asks to publish or upload a video (e.g., "publish this video", "upload to all platforms"):
**Always ask the user how they would like to run the publishing automation:**

1. **Option A (Watch Live on Screen - Recommended):** Provide the user the exact command to paste into their Antigravity IDE terminal (e.g., `python scripts/avbrief.py post --folder "outputs/Love and Trauma/<video_folder>" --platform all`). This executes in their desktop session, opening the real Chrome window live on their monitor so they can watch every step.
2. **Option B (Run in Background):** The agent triggers the command internally as an isolated background task.

### Published episode folder marker

After the publisher confirms at least one successful live post on any platform (including TikTok only), it renames the episode folder to `Done-<original-name>`. A publication from `episode/v2/` marks the parent episode so the prefix is visible in `outputs/`. Wait until the upload queue and browser file handles close before renaming. `Done-` means at least one platform published, not all platforms; consult `publish_status.json` for platform-specific results.

Drafts, scheduled uploads that are not live yet, failed attempts, prompt generation and metadata export do not count as publication. Preserve existing `Done-` prefixes, never overwrite a colliding destination, update absolute paths in episode JSON files, and report a rename failure separately from upload success. This automatic marker applies to the local publishing pipeline; an upload performed manually outside it needs explicit confirmation before marking. Never infer publication merely from files existing. Existing outputs are not retroactively renamed by a skill update.

## Required Behavior & Output Specifications

### 1. Sequential Execution

- Process batches **strictly sequentially one-by-one**.
- Deliver and report the completed brief, title, and description of each video before advancing to the next.

### 1b. Strict Literal-Equivalent Video Title Translation (V1/V2)

- **Post Title & Voiceover Hook:** The Arabic title (`post-title.txt`, hook narration, and description header) must be a **100% direct, faithful, literal-equivalent translation** of the original YouTube video title into clear Modern Standard Arabic.
- **NEVER Paraphrase or Re-invent Titles:** Do NOT create a conceptual, abstract, or interpretive title from scratch based on the whole video theme.
  - *Example 1:* If original is *"Why More Freedom Is Making You Miserable"*, translate directly: `لماذا تجعلك الحرية الزائدة تعيساً؟` (NEVER rewrite into `فخ كثرة الخيارات: لماذا تسرق الحرية المطلقة سعادتنا`).
  - *Example 2:* If original is *"Give Me 47 Minutes If You Still Can't Move On From Your Ex"*, translate directly: `امنحني 47 دقيقة إذا كنت لا تزال عاجزاً عن تجاوز شريكك السابق` (NEVER rewrite into `لماذا تعجز عن تجاوز الانفصال والتعافي من علاقتك السابقة؟`).
- This direct translation must be the text saved in `post-title.txt`, displayed at the top of the narrative description, and spoken in the V2 hook voiceover.


### 2. Video Render Layout (38 Seconds - Version 1)

- **Top Panel (1080×760):**
  - **Motion:** 2.5s source card with kinetic Ken Burns push-in zoom + 27.5s video stream playback + 8s thumbnail card with kinetic Ken Burns zoom during CTA. Zero static freeze frames.
  - **Seamless Gradient Feather:** Alpha gradient fading from `y=490` to `y=760` into pure `#000000` black, eliminating all hard borders/letterboxing and avoiding Instagram's "video has a border" warning.
  - **Floating Glassmorphic Metadata Badge (1016×176px at y=556, r=26px):**
    - **RTL / BiDi Awareness:** For Arabic content, layout is strictly Right-to-Left (red YouTube play icon on the right, title right-aligned, metadata ordered `[Channel Name]` • `[View Count]` • `[Upload Date]`). For English content, layout is Left-to-Right.
    - **Multi-line Title:** Full video title wraps across 2–3 balanced lines without ellipsis (`...`) truncation.
    - **Metadata Row:** Channel name, view count, and upload date cleanly rendered with centered bullet separators.
- **Background Music:** Contemplative instrumental track (`assets/music/andrea_vanzo_amelie_0030_0100.mp3`). The requested YouTube excerpt from 0:30–1:00, a 1-second fade-in at t=0s, steady volume, and a smooth 2.0-second fade-out between 28.0s and 30.0s.
- **Outro Voiceover (The Conversion Bridge):** Dedicated outro audio narration (`assets/music/last voicever.mp3`) plays during the final 8 seconds (30.0s - 38.0s) across the CTA page.
- **Left-Shift Safe Zone:** All Arabic text blocks on Page 1 & Page 2 are shifted 6% to the left (~65px) so that right-side platform action buttons never overlap with the Arabic text.
- **Page 1 (0–15s):** Direct translation of source YouTube title, center headline, dynamic category, and 70–80 words opening with a source-specific example, event or puzzle and beginning its explanation.
- **Page 2 (15–30s):** 70–80 words developing the explanation through a distinct example, consequence, comparison or nuance; no repeated hook or compulsory tips. Footer prompt: `اقرأ الوصف لمزيد من التفاصيل`. Total words 140–160.
- **Question & CTA Page (30–38s):** Dedicated 8.0-second ending page:
  - Top panel: Dynamic thumbnail card with subtle Ken Burns push-in zoom and floating metadata badge.
  - Bottom panel:
    - Main gold text: one topic-specific Arabic question, following the shared ending rules below.
    - Middle action pill: `احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد` (34px, 15% platform safe margin).
    - Capsule Fikr circular logo and brand label.
    - Bottom gold badge: `السر الأهم والخطوات التطبيقية في الوصف بالأسفل` with downward chevron.
    - Outro narration bridge playing clearly.

### 2b. Video Render Layout (42.2 Seconds - Version 2 Extended Format)

- **Top Panel (1080×760):**
  - `0:00 - 0:02.5`: Source Card with kinetic Ken Burns push-in zoom and floating translucent metadata badge.
  - `0:02.5 - 0:34.2`: Highlighted Video Segment (31.7 seconds extracted from the source clip with seamless bottom gradient blend and floating metadata badge). Zero hard borders.
  - `0:34.2 - 0:42.2`: Dynamic thumbnail card with subtle Ken Burns push-in zoom during the final 8.0s conclusion & CTA page.
  - **Floating Glassmorphic Metadata Badge (1016×176px at y=556, r=26px):**
    - **RTL / BiDi Awareness:** For Arabic content, layout is strictly Right-to-Left (red YouTube icon on right, right-aligned title, RTL metadata order). For English content, layout is Left-to-Right.
    - **Multi-line Title:** Full video title wraps cleanly without truncation.
    - **Seamless Alpha Gradient:** Feathers from `y=490` to `y=760` into pure black `#000000`.
- **Bottom Panel (1080×1160) - 4 Text Pages + 1 Conclusion Screen:**
  - **Page 1 (0:00 - 0:10.8, 10.8s):** Main video title in Modern Standard Arabic + Category tag + first explanatory beat with a concrete entry point and useful reveal (30–44 words, existing gold highlighting).
  - **Page 2 (0:10.8 - 0:18.6, 7.8s):** next explanatory beat adding mechanism, evidence or context (30–44 words).
  - **Page 3 (0:18.6 - 0:26.4, 7.8s):** a distinct example, comparison, development or consequence (30–44 words).
  - **Page 4 (0:26.4 - 0:34.2, 7.8s):** the source-appropriate payoff or nuance (30–44 words), without a generic conclusion or forced advice.
  - **Conclusion & CTA Screen (0:34.2 - 0:42.2, 8.0s):**
    - **Main Ending Text:** Gold-highlighted V3-style Footer Action / Question (4–18 words, maximum 140 characters), replacing the declarative punchline on this existing screen. Tie it to a concrete detail in the reading pages; no swipe instructions.
    - **Secondary CTA:** Sleek dark pill with outline: `احفظ الفيديو لتستفيد منه لاحقاً`.
    - **Primary Description Badge:** Prominent, filled Gold Badge (`#F5C518`) with bold black text: `السر الأهم والخطوات التطبيقية بانتظارك في الوصف بالأسفل`.
    - **Indicator Arrow:** Sharp vector golden chevron/arrow pointing downwards directly at the platform's description box.
    - **Branding:** 130px circular Capsule Fikr logo with gold border ring and `كبسولة فكر` gold typography.
- **Audio Architecture:**
  - **Hook Script:** Translated title followed by `ملخص الفكرة في ثوانٍ، والتفاصيل الكاملة في صندوق الوصف.` Change only the TTS script; preserve on-screen wording.
  - **Hook Narration:** ElevenLabs TTS Arabic voiceover at `t=0s` (`volume=1.3`, natural human cadence).
  - **Background Instrumental:** (randomly choose `naruto_sadness_and_sorrow.mp3` or `godfather_0013.mp3` per render) ducked to `0.12` during speech, swelling smoothly to `0.70` over 0.6s when narration ends.
  - **Music Outro Fade:** Background music fades out smoothly before the conclusion page (32.2s – 34.2s).
  - **Outro Voiceover:** (`assets/music/last voicever.mp3`) starts at `t=34.2s` (`volume=1.1`) and plays for 8.0 seconds during the Conclusion & CTA screen (34.2s – 42.2s).
  - **amix Parameters:** Configured with `normalize=0` to ensure vocals remain bold, clear, and unattenuated.

### 2c. Source-specific Endings (Both Video Versions)

- Author `ending_question_ar` for V1. For V2, author `ending_text_ar` as one source-specific Footer Action / Question on the existing final 8-second screen. Reuse valid authored text without an extra model call. See the editorial style reference for details.
- V1 uses one concise, source-grounded Arabic question, 4–18 words and at most 140 characters, ending in `؟`. V2 questions follow the same rules; its alternative action footer follows the editorial style reference. Invite a concrete experience, choice with a reason, or thoughtful comparison, in the spirit of the deep-dive post's final question.
- Match the source: psychology can invite reflection; science can ask about an implication; history or geopolitics can compare explanations. Do not force practical advice, polarizing allegiance, sensitive disclosure, or unsupported claims.
- Avoid generic “ما رأيك في هذا الموضوع؟” and multiple stacked questions. Examples: `ما المهارة التي تؤجل التدرب على أصعب جزء فيها؟` / `أي نتيجة في هذه الدراسة غيّرت تفسيرك للمشكلة؟`
- Keep the existing save/description badges and recorded outro. The question is displayed on screen; do not synthesize additional narration.
- Save `ending-question-ar.txt` in V1. V2 saves canonical `ending-text-ar.txt`, with `ending-question-ar.txt` and `conclusion-ar.txt` as compatibility aliases containing the same footer, whether question or action.
- Existing exports remain untouched until rerendered. Rerender reuses the saved V1 question or V2 footer. Legacy folders need valid authored ending copy or a question-generation call; rerender does not rewrite summary pages.

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

- `CapCut_1080p_{YYYYMMDD}_{clean_slug}.mp4` (38s in V1 / 42.2s in V2 1080×1920 MP4)
  - **Strict Single-Video Anti-Bot Protocol:** Directly staged as `CapCut_1080p_{YYYYMMDD}_{clean_slug}.mp4`. Any intermediate or temporary `brief.mp4` is **immediately deleted upon creation** so platforms never detect bot script filenames on disk or in file pickers.
  - **Anti-Bot Container Spoofing:** Rendered with `-map_metadata -1`, `+bitexact`, `-metadata:s:v:0 encoder=CapCut`, `-metadata:s:a:0 encoder=CapCut`, `-metadata major_brand=mp42`, completely removing FFmpeg `Lavf`/`Lavc` traces.
  - **Acoustic De-duplication:** Subtle imperceptible audio micro-jitter (±0.5%–1.0%) to prevent Content ID and platform algorithms from clustering videos as repeated duplicate templates.
- `summary-ar.txt` (140–160 words of concrete explanatory Modern Standard Arabic copy)
- `ending-question-ar.txt` (V1 question; V2 compatibility alias). V2 writes canonical `ending-text-ar.txt` and alias `conclusion-ar.txt`.
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

# Example AFTER the user chooses V1, no deep dive, and manual thumbnail prompts
python scripts/avbrief.py run --source "https://www.youtube.com/watch?v=..." --version v1 --no-deepdive --thumbnails manual --provider brainstorm --analysis "<analysis.json>"
# Jobs must contain the user's explicit version/deepdive/thumbnails choices, or pass them as flags
python scripts/avbrief.py run --job "<answered-job.json>"

# Re-render using saved text; legacy folders without a question may need a text LLM call
python scripts/avbrief.py rerender --folder "outputs/<folder>"

# Source-led Hybrid Thumbnail & Photo Prompt Generation
# Auto-skips 4:5 Facebook thumbnail if deep_dive_summary.txt is not requested, saving API tokens & credits
python scripts/avbrief.py thumbnail --folder "outputs/<folder>"
python scripts/avbrief.py thumbnail --folder "outputs/<folder>" --kieai
# Optional flags: --facebook (force 4:5 FB generation) / --no-facebook (skip 4:5 FB generation)

# Exhaustive Deep-Dive Educational Synthesis (deep_dive_summary.txt)
python scripts/avbrief.py deepdive --folder "outputs/<folder>"
python scripts/avbrief.py deepdive --folder "outputs/<folder>" --provider vyceai

# Prepare metadata-free V3 posting copies, preserving original images
python scripts/avbrief.py prepare-v3-images --folder "outputs/<video_folder>/v3"

# Remove embedded metadata from existing cover images
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
