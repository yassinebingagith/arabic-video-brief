# Multi-Platform Video Publishing Automation (YouTube Shorts, TikTok, Instagram & Facebook Reels)

Build a dedicated, on-demand publishing engine (`avbrief post` and `avbrief login`) for `arabic-video-brief` using a persistent Playwright browser profile. This automates uploading vertical video briefs (`brief.mp4`) with faithful Arabic titles (`post-title.txt`) and formatted descriptions (`post-description.txt`) directly to YouTube Shorts, TikTok Web, and Meta Business Suite (simultaneously cross-posting to Facebook Page and Instagram Reels) in a visible (headful) browser window.

---

## 1. Key Architectural Decisions (From User Alignment)

- **Execution Engine:** Local Browser Session via Playwright with a persistent user data directory (`assets/browser_profile/`). 100% free, no third-party SaaS fees, and no developer app review bottlenecks.
- **Platforms Covered (4 Platforms):**
  1. **YouTube Shorts** (via `studio.youtube.com`)
  2. **TikTok Web** (via `tiktok.com/creator-center/upload`)
  3. **Meta Business Suite** (via `business.facebook.com`), creating a unified Reel that cross-posts to both **Facebook Page** and **Instagram Reels**.
- **Browser Mode:** Headful (visible browser window) so the user can observe the bot in real time and easily resolve any unexpected 2FA or CAPTCHA prompts.
- **Authentication:** One-time interactive login command (`python scripts/avbrief.py login`). No passwords stored in `.env`. Cookies and sessions are preserved permanently on disk.
- **Triggering:** **Strictly manual / on-demand**. Never runs automatically. The user specifies the video folder and the target platform:
  ```bash
  python scripts/avbrief.py post --folder "outputs/Love and Trauma/<video_folder>" --platform all
  ```
- **Publishing Mode:** Default is **Publish Now**, with optional `--schedule "YYYY-MM-DD HH:MM"` and `--draft` flags.
- **Safety & Tracking:** Saves a `publish_status.json` inside each video's folder recording timestamps, target platforms, and statuses to prevent accidental duplicate uploads.

---

## 2. Directory & Module Architecture

```text
src/arabic_video_brief/publisher/
├── __init__.py
├── session.py        # Manages persistent browser context (assets/browser_profile) & headful launching
├── formatter.py      # Extracts & formats titles, captions, hashtags, and enforces char limits
├── youtube.py        # YouTube Studio automation (upload, title, description, not-for-kids, publish/schedule)
├── tiktok.py         # TikTok Web automation (upload, caption with hashtags, post now/schedule)
├── meta.py           # Meta Business Suite automation (upload Reel, select FB Page + IG, post/schedule)
├── tracker.py        # Reads & updates publish_status.json per video directory
└── dispatcher.py     # Coordinates sequential posting with humanized randomized pauses (15–45s)
```

---

## 3. Platform Specifications & Formatting

### A. YouTube Shorts (`youtube.py`)
- **Portal:** `studio.youtube.com`
- **File:** `brief.mp4`
- **Title:** `post-title.txt` + ` #Shorts` (Strictly under 100 characters).
- **Description:** Full content of `post-description.txt` (including structured article points, hashtags, and CTA).
- **Audience:** Explicitly selects `"No, it's not made for kids"`.
- **Visibility:** Default `"Public"` (Publish Now) or `"Schedule"`.

### B. TikTok Web (`tiktok.py`)
- **Portal:** `tiktok.com/creator-center/upload`
- **File:** `brief.mp4`
- **Caption:** Headline + concise excerpt + hashtags, capped under 2,000 characters (TikTok limit: 2,200).
- **Visibility:** Default `"Post"` (Now) or native schedule if requested.

### C. Meta Business Suite (`meta.py`)
- **Portal:** `business.facebook.com` (Reels Composer)
- **File:** `brief.mp4`
- **Targeting:** Dual-selection: Check both **Facebook Page** and **Instagram Account**.
- **Caption:** Formatted Arabic text with hashtags (capped under 2,000 characters).
- **Visibility:** Default `"Publish"` (Now) or `"Schedule"`.

---

## 4. CLI Subcommands

### 1. `avbrief login`
Opens a visible browser with tabs for YouTube Studio, TikTok, and Meta Business Suite:
```bash
python scripts/avbrief.py login [--platform all|youtube|tiktok|meta]
```
The user logs in once manually. When finished, pressing `Enter` in the terminal safely saves and closes the session.

### 2. `avbrief post`
Publishes a selected video folder:
```bash
# Post to all 4 platforms (YouTube, TikTok, Instagram & Facebook):
python scripts/avbrief.py post --folder "outputs/Love and Trauma/Begging-For-Love-rhbejide-4c" --platform all

# Post to YouTube Shorts only:
python scripts/avbrief.py post --folder "outputs/Love and Trauma/Begging-For-Love-rhbejide-4c" --platform youtube

# Post with schedule:
python scripts/avbrief.py post --folder "outputs/Love and Trauma/Begging-For-Love-rhbejide-4c" --platform all --schedule "2026-09-03 18:00"
```

---

## 5. Implementation Steps

1. **Install Playwright**:
   - Add `playwright>=1.40.0` to virtual environment dependencies and run `playwright install chromium`.
2. **Build `session.py`**:
   - Create persistent browser launcher pointing to `assets/browser_profile` with stealth arguments (disabling `navigator.webdriver` flags, setting realistic viewport).
3. **Build `formatter.py` & `tracker.py`**:
   - Handle text extraction, character limits, hashtag parsing, and duplicate prevention via `publish_status.json`.
4. **Implement Platform Automations**:
   - `youtube.py`: YouTube Studio upload flow.
   - `tiktok.py`: TikTok Creator Center upload flow.
   - `meta.py`: Meta Business Suite unified Reel flow.
5. **Implement `dispatcher.py` & CLI integration**:
   - Connect subcommands to `src/arabic_video_brief/cli.py` and `scripts/avbrief.py`.
6. **Interactive Dry Run**:
   - Run `avbrief login` to establish the sessions.
   - Perform a live single-video test with one of the newly generated briefs from `outputs/Love and Trauma/`.
