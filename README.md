# Arabic Video Brief Automation (موجز الفيديو العربي)

An automated production and multi-platform publishing engine for creating V1 (38-second) and V2 (42.2-second) vertical (9:16) video briefs with Modern Standard Arabic summaries, deep instrumental soundtrack, and automatic publishing to **YouTube Shorts**, **TikTok**, and **Meta / Instagram Reels**.

---

## 🌟 Key Features

- **Automated Video Synthesis:** Downloads source clips, generates concrete explanatory Modern Standard Arabic copy (140–160 words, split across two 15-second cards in V1), and compiles 1080×1920 60/30fps vertical MP4s.
- **Dynamic On-Screen Layout:**
  - 2.5-second source metadata card with title, channel, and category.
  - 27.5-second V1 / 31.7-second V2 live video segment with subtle darkening and audio ducking.
  - **Left-Shift Safe Zone (6% / ~65px):** Arabic text is offset to prevent right-side social platform buttons (Like, Comment, Share) from obscuring text.
  - Bottom 15% platform UI safe zone.
- **Multimodal LLM Support:**
  - **Antigravity Brainstorm:** Direct internal reasoning with zero external API cost.
  - **SeekAI API:** High-throughput `deepseek-v4-flash`.
  - **Google Gemini API:** Resilient multimodal `gemini-3.6-flash` / `gemini-3.5-flash`.
- **Multi-Platform Publishing Suite:**
  - Automated browser automation with persistent session support.
  - Native publishing for **YouTube Shorts** (with active 100% upload progress verification).
  - Native publishing for **TikTok**.
  - Native publishing for **Meta Business Suite** (cross-posted to Facebook Reels & Instagram Reels).
- **In-Depth Narrative Post Descriptions:** Generates rich, thematic long-form descriptions (< 2,000 characters) tailored for maximum engagement.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- FFmpeg (can be installed locally or placed in `bin/ffmpeg.exe`)
- Google Chrome (for automated publishing)

### 2. Clone & Install Dependencies
```powershell
git clone https://github.com/<your-username>/arabic-video-brief.git
cd arabic-video-brief

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install requirements
pip install -e .
playwright install chromium
```

### 3. Configure Environment Variables
Copy the `.env.example` template to `.env`:
```powershell
cp .env.example .env
```
Edit `.env` with your preferred API keys:
```env
GEMINI_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_data_api_v3_key
Seekai_api=your_seekai_key
SEEKAI_MODEL=deepseek-v4-flash
```

> [!CAUTION]
> **NEVER commit or upload `.env` to GitHub!** It contains your private API credentials and is strictly ignored in `.gitignore`.

---

## 🚀 Usage

### 1. System Diagnostics
Verify that your environment, FFmpeg, fonts, and API credentials are ready:
```powershell
python scripts/avbrief.py doctor
```

### 2. Discover Videos (Search Mode)
Search for trending or relevant long-form discussions using the YouTube Data API:
```powershell
python scripts/avbrief.py search --query "neuroscience habits" --mode popular --limit 5
```

### 3. Generate a Video Brief

Resolve the video version, analysis engine, deep-dive choice, and thumbnail choice with the user before starting, including when V3 is also requested. Non-interactive runs require explicit `--version`, `--deepdive` or `--no-deepdive`, and `--thumbnails none|manual|kieai`. Missing choices return `SETUP_REQUIRED`; default flags must not substitute for user answers. The examples below assume the user chose no deep dive and manual thumbnail prompts.

Support for both **V1 (two 15s pages + 8s question ending = 38s)** and **V2 (title hook + four pages + action/question ending = 42.2s)**:

#V1/V2 writing follows [the explanatory editorial guide](references/v1-v2-editorial-style.md). Video thumbnails preserve the original source medium and use episode-specific hybrid compositions with separate short Arabic hooks; full post titles and narration remain faithful translations. V3 is independent and unchanged.

### V2 Pipeline (42.2-second format):
Features the translated title hook with optional ElevenLabs TTS, 4 authored explanatory pages, and a dedicated full-page action/question ending with Capsule Fikr branding:
```powershell
python scripts/avbrief.py run --source "https://www.youtube.com/watch?v=..." --version v2 --provider vyceai --no-deepdive --thumbnails manual
```
Outputs are isolated under `outputs/<video-slug>/v2/`:
- `CapCut_1080p_*.mp4` (42.2-second 1080×1920 MP4)
- `summary-ar.txt` (Complete 140–160 word Arabic summary)
- `summary-pages.json` (Four rendered pages with sentence alignment and counters `١/٤` to `٤/٤`)
- `hook-ar.txt` & `hook-tts.txt` (Selected hook text & TTS normalized text)
- `hook-voice.mp3` (ElevenLabs voice narration, if configured)
- `ending-text-ar.txt` (V2 footer), `ending-question-ar.txt` / `conclusion-ar.txt` (compatibility aliases), and `cta-ar.txt`
- `creative-plan.json` (Internal candidate scoring and editorial plan)
- `post-title.txt` & `post-description.txt`
- `manifest.json`

#### V1 Pipeline (38-second format):
Two 15-second reading pages followed by an 8-second topic-specific question ending; existing music and visual design are retained:
```powershell
python scripts/avbrief.py run --source "https://www.youtube.com/watch?v=..." --version v1 --no-deepdive --thumbnails manual
```
Outputs are saved in `outputs/<video-slug>/`:
- `CapCut_1080p_*.mp4` (38-second 1080×1920 MP4)
- `post-title.txt` & `post-description.txt`
- `summary-ar.txt` (Two-page abstract)
- `ending-question-ar.txt` (Short Arabic discussion question)
- `manifest.json` & `transcript.json`

> [!TIP]
> Run `python scripts/avbrief.py doctor` to verify local ffmpeg, fonts, and API key statuses.

### V3: Carousel + Facebook Photo Packs

Use the same skill in chat:

- `$arabic-video-brief V3 — make a carousel and Facebook photo prompt pack from <URL>`
- `$arabic-video-brief V3 — use the existing transcript in <folder>`
- `$arabic-video-brief — make V1 and a V3 pack for <URL>`

If a video request has no version, the skill asks V1 or V2. If V3 sources are unspecified, it asks which links or existing videos need packs. V3 prepares one 4–6-slide Instagram carousel and one standalone Facebook photo concept per source, exact Arabic text, captions, standalone image prompts, and references. Art direction adapts to each source without a mandatory palette or logo. Slide 1 uses the original thumbnail; subsequent slides and the Facebook image use that thumbnail plus the accepted slide 1.

V3 uses **Western digits 0–9 in all Arabic audience-facing text and imagery** (for example `21–35` and `2–12`). Source thumbnail and original transcript are preserved as evidence. Run `python tools/v3_save_image.py check --folder "outputs/<video-slug>/v3"` to check authored copy; `normalize-digits` repairs a saved V3 pack's text/prompts/captions, without changing source material or already rendered images.

The pack includes a structured `generation-plan.json`. **After finishing the pack**, the agent asks whether to generate through a configured image API, through a persistent ChatGPT image-generation session (using connected MCP/computer-use where available), or stop for manual generation. Only the user's chosen method is used. In any method, generate slide 1 first, inspect/accept it, then use both actual attachments — source YouTube thumbnail (Image 1) and accepted slide 1 (Image 2) — for every later slide and the Facebook photo. Keep all ChatGPT image generation for one episode in one session.

After obtaining each actual image file, use `python tools/v3_save_image.py save --folder "outputs/<video-slug>/v3" --id ig-slide01 --source "path/to/image.png" --method chatgpt_mcp` to register it at `instagram/slide01.png` (and similarly for later images). Visually inspect slide 1, then call `python tools/v3_save_image.py accept --folder "outputs/<video-slug>/v3" --id ig-slide01 --reviewed` before the remaining images. This registration helper cannot generate or download images by itself. It preserves the received original in `generation-sources/`, creates a normalized 1080×1350 PNG, and updates `generation-plan.json`. If image bytes cannot be transferred from the generation chat to the local Windows project, request an actual download/attachment before claiming the file was saved.

After all images are saved and reviewed, double-click the pack’s `prepare-images.bat` or run `python scripts/avbrief.py prepare-v3-images --folder "outputs/<video-slug>/v3"`. Upload the copies listed in `posting-ready/export-report.json`; originals and reference images are preserved. This strips embedded metadata, with no guarantee about AI detection or labels. V3 is an agent workflow, not a `--version v3` CLI command. See [the V3 workflow](references/v3-carousel-pack.md).

### 4. Social Media Publishing

#### One-Time Interactive Login
Log into your creator accounts once in the persistent profile browser:
```powershell
python scripts/avbrief.py login --platform all
```

#### Upload & Publish
Publish to all platforms simultaneously:
```powershell
python scripts/avbrief.py post --folder "outputs/<video-slug>" --platform all
```
Or target an individual channel:
```powershell
python scripts/avbrief.py post --folder "outputs/<video-slug>" --platform youtube
python scripts/avbrief.py post --folder "outputs/<video-slug>" --platform tiktok
python scripts/avbrief.py post --folder "outputs/<video-slug>" --platform meta
```

### 5. AI Agent Skill Integration

This repository includes a ready-to-use AI Agent Skill for Antigravity IDE, Gemini CLI, Claude Code, and Codex.

- **Workspace Auto-Detection:** The skill is bundled in `.agents/skills/arabic-video-brief/` and automatically discovered when opening this folder in Antigravity IDE.
- **Global Installation:** To install the skill globally into your AI environment:
  ```powershell
  # For Antigravity / Gemini CLI:
  powershell -ExecutionPolicy Bypass -File scripts/install_skill.ps1 -Target gemini

  # For Codex:
  powershell -ExecutionPolicy Bypass -File scripts/install_skill.ps1 -Target codex
  ```
- **Interactive Conversation Flow:** Once invoked (e.g., `arabic-video-brief`), the agent asks for your preferred chat language (English, Arabic, French, etc.), lets you choose search or direct video processing mode, and outputs standardized briefs in pure Modern Standard Arabic.

---

## 🔒 Security Best Practices

When committing or publishing to GitHub:
- **Never upload `.env`:** Keep it strictly local.
- **Never upload `assets/browser_profile/`:** This contains your active browser cookies and login tokens.
- **Keep `outputs/` local:** Contains generated media files.

---

## 📄 License
MIT License

For the V3 browser/MCP sequence, download verification and interruption recovery, see [the execution procedure](references/v3-browser-execution.md). `python tools/v3_save_image.py next --folder "outputs/<source>/v3"` reports the next local action without generating anything. The agent operates the connected browser; there is no standalone unattended browser service or implemented image API adapter in this helper.

A confirmed successful live publication on any one platform automatically prefixes the episode folder with `Done-` after the upload queue closes. Publishing from its `v2/` child marks the parent episode. JSON paths inside the episode are updated; the returned report contains the new folder. Drafts, scheduled-only uploads and failures do not receive this prefix. `Done-` means at least one platform published; consult `publish_status.json` before posting to other platforms. Manual uploads outside this pipeline are not automatically detected.
