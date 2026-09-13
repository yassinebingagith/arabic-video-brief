# Arabic Video Brief Automation (موجز الفيديو العربي)

An automated production and multi-platform publishing engine for creating 20-second vertical (9:16) video briefs with Modern Standard Arabic summaries, deep instrumental soundtrack, and automatic publishing to **YouTube Shorts**, **TikTok**, and **Meta / Instagram Reels**.

---

## 🌟 Key Features

- **Automated Video Synthesis:** Downloads source clips, generates clean Modern Standard Arabic abstracts (140–160 words, split across two 10-second cards), and compiles 1080×1920 60/30fps vertical MP4s.
- **Dynamic On-Screen Layout:**
  - 5-second source metadata hook with title, channel, and category.
  - 15-second live video clip background with subtle darkening and audio ducking.
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

Support for both **V1 (Legacy 20s)** and **V2 (Hook + 4 Pages + Ending Card 26s)**:

#### V2 Pipeline (Recommended - 26-second format):
Features an independent conversational Arabic hook with optional ElevenLabs TTS, 4 balanced sentence-aligned summary pages, and a dedicated full-page conclusion with Capsule Fikr branding:
```powershell
python scripts/avbrief.py run --source "https://www.youtube.com/watch?v=..." --version v2 --provider vyceai
```
Outputs are isolated under `outputs/<video-slug>/v2/`:
- `brief.mp4` (26-second 1080×1920 MP4)
- `summary-ar.txt` (Complete 140–160 word Arabic summary)
- `summary-pages.json` (Four rendered pages with sentence alignment and counters `١/٤` to `٤/٤`)
- `hook-ar.txt` & `hook-tts.txt` (Selected hook text & TTS normalized text)
- `hook-voice.mp3` (ElevenLabs voice narration, if configured)
- `conclusion-ar.txt` & `cta-ar.txt` (Memorable conclusion & contextual save CTA)
- `creative-plan.json` (Internal candidate scoring and editorial plan)
- `post-title.txt` & `post-description.txt`
- `manifest.json`

#### V1 Pipeline (Legacy 20-second format):
The classic two-page format with 5s static thumbnail card + 15s video stream:
```powershell
python scripts/avbrief.py run --source "https://www.youtube.com/watch?v=..." --version v1
```
Outputs are saved in `outputs/<video-slug>/`:
- `brief.mp4` (20-second 1080×1920 MP4)
- `post-title.txt` & `post-description.txt`
- `summary-ar.txt` (Two-page abstract)
- `manifest.json` & `transcript.json`

> [!TIP]
> Run `python scripts/avbrief.py doctor` to verify local ffmpeg, fonts, and API key statuses.

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
