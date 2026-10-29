# V1 Render Specification (38-Second Format)

Production reading pages use the mandatory [Python/FFmpeg whiteboard engine](python-whiteboard.md), with a complete editable render-project inside each episode folder. The specifications below describe the preserved composition and settled page appearance; reading text is progressively written rather than shown as a static slide.

## Overview
- **Total Duration:** 38.0 seconds: 15 + 15 + 8.
- **Resolution & Aspect Ratio:** 1080×1920 (9:16 vertical MP4).
- **Background Music:** Contemplative instrumental (`andrea_vanzo_amelie_0030_0100.mp3`) at 0.85 volume, with a 1.0s fade-in and 2.0s smooth fade-out between 28.0s and 30.0s.
- **Outro Voiceover:** Dedicated outro narration (`assets/music/last voicever.mp3`) playing across 30.0s – 38.0s (8.0 seconds) during the final CTA page.
- **Source Audio:** 100% muted throughout.

## Top Panel & Metadata Overlay (1080×760)
- **Seamless Alpha Gradient:** Bottom video edge feathers from `y=490` to `y=760` into pure `#000000` black, eliminating hard horizontal lines and avoiding Instagram's "video has a border" penalty.
- **Floating Glassmorphic Badge (1016×176px at y=556, r=26px):**
  - **RTL / BiDi Awareness:**
    - **Arabic Content (RTL):** YouTube red play icon anchored on the right (`x = 924`), multi-line title right-aligned, and metadata elements ordered Right-to-Left: `[Channel Name]` • `[View Count]` • `[Upload Date]`.
    - **English Content (LTR):** YouTube red play icon on the left (`x = 56`), title left-aligned, and metadata elements ordered Left-to-Right.
  - **Full Multi-line Title:** Dynamically wrapped across 2–3 balanced lines (26px/23px Bold) with zero ellipsis (`...`) truncation.
  - **Channel, Views & Date:** Clearly rendered in 22px/21px semi-bold typography with centered bullet separators.

## Timeline
- **0:00 – 0:02.5 (2.5s):** Top panel shows source card with kinetic Ken Burns push-in zoom and floating translucent metadata badge. Bottom panel shows Page 1 on deep black-and-navy radial glow canvas.
- **0:02.5 – 0:15 (12.5s):** Top panel plays video stream at `selected_clip["start_seconds"]` with seamless bottom gradient blend and floating metadata badge. Bottom panel continues showing Page 1 with centered gold title header and book-highlighted text.
- **0:15 – 0:30 (15.0s):** Top panel continues video playback (total 27.5s video stream). Bottom panel displays Page 2 (vertically centered, 2–3 gold highlighted phrases, strictly NO duplicate description CTA footer or repetitive callout text). Music fades out between 28.0s and 30.0s.
- **0:30 – 0:38 (8.0s):** Top panel displays thumbnail card with kinetic Ken Burns zoom and floating badge. Bottom panel shows a topic-specific gold Arabic question on the navy radial glow canvas above the action pill, logo, and description badge accompanied by the outro voiceover.

## Text & Typography
- **Total Words:** 140–160 Modern Standard Arabic words split into two 70–80 word panels.
- **Background Style:** Deep royal/midnight blue radial glow (`#102A45`) softly blurred (`sigma=120`) through dark navy (`#071322`) to pure midnight black (`#02060D`) via `create_v2_summary_background`.
- **Base Typography:** Bold 700 Crisp White (`#F8FAFC`) with generous line height (~1.75–1.80) for clean vertical breathing room.
- **Book-Highlighter Styling:** 2–3 key phrases per page enclosed in `<hl>...</hl>` tags, rendered in Warm Gold (`#FFD700`) Bold (750–800) with a translucent warm gold rounded pill box (`rgba(255, 215, 0, 0.14)`, radius 10px, padding 2px 10px 4px 10px). Non-breaking spaces (`\u00A0`) prevent phrases from wrapping mid-highlight. Attached single-letter prefixes (`و`, `ف`, `ب`, `ل`, `ك`) stay inside `<hl>`. Clean descenders without underlines.
- **No Duplicate CTA Footer:** Page 2 does NOT include a blue footer or trailing description callout; all calls to action are cleanly reserved for the 8-second ending screen.
- **Safe Zone:** 6% left-shift (~65px) to clear platform right-side interaction icons (TikTok/Reels/Shorts).


- **Ending:** One source-grounded question, 4–18 words and at most 140 characters; save as `ending-question-ar.txt`. Invite a concrete experience, reasoned choice, or comparison; no generic “ما رأيك؟”. Display the question on screen without additional narration.

## Music source and coverage
Use the 30-second excerpt from [Andrea Vanzo’s Amélie performance](https://www.youtube.com/watch?v=e6Po2lDHD1I), source time 0:30–1:00. Provenance is saved in `assets/music/v1-music-source.json`. The renderer loops the music input defensively, trims it to the 30-second reading section, fades in at 0–1s and out at 28–30s, then leaves the existing outro for 30–38s. The old 19.99-second V1 asset is no longer selected. V2 music is unchanged.

## Reading-copy direction
Follow [v1-v2-editorial-style.md](v1-v2-editorial-style.md) for source-specific explanatory writing and hybrid thumbnail direction. Preserve the timeline and rendering geometry above.
