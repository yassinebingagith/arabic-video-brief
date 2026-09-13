# V2 Render Specification (36.5-Second Format)

## Overview
- **Total Duration:** 36.5 seconds.
- **Resolution & Aspect Ratio:** 1080×1920 (9:16 vertical MP4).
- **Audio Architecture:**
  - **Hook Narration:** ElevenLabs TTS Arabic voiceover at `t=0s` (`volume=1.3`, full cadence preserved).
  - **Background Instrumental:** (`naruto_sadness_and_sorrow.mp3`) ducked to `0.12` during speech, smoothly swelling to `0.70` over 0.6s when narration ends.
  - **Music Outro Fade:** Background music fades out smoothly before the conclusion page (26.5s – 28.5s).
  - **Outro Voiceover:** (`assets/music/last voicever.mp3`) starts at `t=28.5s` (`volume=1.1`) and plays for 8.0 seconds during the Conclusion & CTA screen (28.5s – 36.5s).
  - **amix Parameters:** Configured with `normalize=0` so vocal clarity and amplitude are never attenuated.
- **Source Audio:** 100% muted throughout.

## Top Panel & Metadata Overlay (1080×760)
- **Seamless Alpha Gradient:** Bottom video edge feathers from `y=490` to `y=760` into pure `#000000` black, eliminating hard horizontal cuts and avoiding Instagram's "video has a border" penalty.
- **Floating Glassmorphic Badge (1016×176px at y=556, r=26px):**
  - **RTL / BiDi Awareness:**
    - **Arabic Content (RTL):** YouTube red play icon anchored on the right (`x = 924`), multi-line title right-aligned, and metadata elements ordered Right-to-Left: `[Channel Name]` • `[View Count]` • `[Upload Date]`.
    - **English Content (LTR):** YouTube red play icon on the left (`x = 56`), title left-aligned, and metadata elements ordered Left-to-Right.
  - **Full Multi-line Title:** Dynamically wrapped across 2–3 balanced lines (26px/23px Bold) with zero ellipsis (`...`) truncation.
  - **Channel, Views & Date:** Clearly rendered in 22px/21px semi-bold typography with centered bullet separators.

## Timeline
1. **0:00 – 0:09.0 (9.0s) — Page 1:**
   - Top panel: 0:00–0:02.5 source card with kinetic Ken Burns push-in zoom and floating translucent metadata badge; 0:02.5–0:09.0 video playback begins with seamless bottom gradient blend and floating metadata badge.
   - Bottom panel: Page 1 Arabic summary (30–44 words), category tag, and main title in Fusha.
   - Hook audio narration starts at t=0s.
2. **0:09.0 – 0:15.5 (6.5s) — Page 2:**
   - Top panel: Video stream continues (seamless gradient blend & floating badge).
   - Bottom panel: Page 2 Arabic summary (30–44 words), counter `٢/٤`.
3. **0:15.5 – 0:22.0 (6.5s) — Page 3:**
   - Top panel: Video stream continues (seamless gradient blend & floating badge).
   - Bottom panel: Page 3 Arabic summary (30–44 words), counter `٣/٤`.
4. **0:22.0 – 0:28.5 (6.5s) — Page 4:**
   - Top panel: Video stream continues (seamless gradient blend & floating badge; total 26.0s video stream).
   - Bottom panel: Page 4 Arabic summary (30–44 words), counter `٤/٤`. Music fades out between 26.5s and 28.5s.
5. **0:28.5 – 0:36.5 (8.0s) — Conclusion & CTA Screen:**
   - Top panel: Thumbnail card with kinetic Ken Burns push-in zoom and floating metadata badge.
   - Bottom panel: Full-page conclusion screen:
     - Gold-highlighted punchline.
     - Secondary CTA pill: `احفظ الفيديو لتستفيد منه لاحقاً`.
     - Prominent Gold Badge (`#F5C518`) with down arrow: `السر الأهم والخطوات التطبيقية بانتظارك في الوصف بالأسفل`.
     - 130px circular Capsule Fikr brand logo.
     - Dedicated outro voiceover (`last voicever.mp3`) plays throughout the entire 8.0s CTA page.

