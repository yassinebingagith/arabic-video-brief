# V2 Render Specification (42.2-Second Format)

## Overview
- **Total Duration:** 42.2 seconds.
- **Resolution & Aspect Ratio:** 1080×1920 (9:16 vertical MP4).
- **Audio Architecture:**
  - **Hook Narration:** ElevenLabs TTS Arabic voiceover at `t=0s` (`volume=1.3`, full cadence preserved).
  - **Background Instrumental:** (randomly choose `naruto_sadness_and_sorrow.mp3` or `godfather_0013.mp3` per render) ducked to `0.12` during speech, smoothly swelling to `0.70` over 0.6s when narration ends.
  - **Music Outro Fade:** Background music fades out smoothly before the conclusion page (32.2s – 34.2s).
  - **Outro Voiceover:** (`assets/music/last voicever.mp3`) starts at `t=34.2s` (`volume=1.1`) and plays for 8.0 seconds during the Conclusion & CTA screen (34.2s – 42.2s).
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
1. **0:00 – 0:10.8 (10.8s) — Page 1:**
   - Top panel: 0:00–0:02.5 source card with kinetic Ken Burns push-in zoom and floating translucent metadata badge; 0:02.5–0:10.8 video playback begins with seamless bottom gradient blend and floating metadata badge.
   - Bottom panel: Page 1 Arabic summary (30–44 words), category tag, and main title in Fusha.
   - Hook audio narration starts at t=0s.
2. **0:10.8 – 0:18.6 (7.8s) — Page 2:**
   - Top panel: Video stream continues (seamless gradient blend & floating badge).
   - Bottom panel: Page 2 Arabic summary (30–44 words), counter `٢/٤`.
3. **0:18.6 – 0:26.4 (7.8s) — Page 3:**
   - Top panel: Video stream continues (seamless gradient blend & floating badge).
   - Bottom panel: Page 3 Arabic summary (30–44 words), counter `٣/٤`.
4. **0:26.4 – 0:34.2 (7.8s) — Page 4:**
   - Top panel: Video stream continues (seamless gradient blend & floating badge; total 31.7s video stream).
   - Bottom panel: Page 4 Arabic summary (30–44 words), counter `٤/٤`. Music fades out between 32.2s and 34.2s.
5. **0:34.2 – 0:42.2 (8.0s) — Conclusion & CTA Screen:**
   - Top panel: Thumbnail card with kinetic Ken Burns push-in zoom and floating metadata badge.
   - Bottom panel: Full-page conclusion screen:
     - Gold-highlighted source-specific Footer Action / Question replacing the punchline: 4–18 words, at most 140 characters. Tie it to a concrete explanation on the pages. Avoid generic “ما رأيك؟”, declarative conclusions and swipe instructions.
     - Secondary CTA pill: `احفظ الفيديو لتستفيد منه لاحقاً`.
     - Prominent Gold Badge (`#F5C518`) with down arrow: `السر الأهم والخطوات التطبيقية بانتظارك في الوصف بالأسفل`.
     - 130px circular Capsule Fikr brand logo.
     - Dedicated outro voiceover (`last voicever.mp3`) plays throughout the entire 8.0s CTA page.


The opening narration remains the translated source title plus the description-directed suffix specified below; do not add full-summary or ending-question narration. Save canonical `ending-text-ar.txt`, with the same footer in `ending-question-ar.txt` and `conclusion-ar.txt` for compatibility. Page styling, word counts, number formatting, the blue frame, and the recorded 8-second outro remain unchanged. Thumbnail direction follows the editorial reference. Reading durations increase by exactly 20%: 9→10.8s and 6.5→7.8s for each remaining page.

## Opening narration and music selection
Narrate the translated title, then `ملخص الفكرة في ثوانٍ، والتفاصيل الكاملة في صندوق الوصف.` This changes only the ElevenLabs script, not the displayed page copy. The configured music pool contains the original Sadness and Sorrow track and `godfather_0013.mp3`, sourced from https://www.youtube.com/watch?v=AJgE_dLWsuQ beginning at 0:13. Choose independently with equal probability on each render; repeats are allowed. Preserve current ducking and fade music over 32.2–34.2s. Loop the chosen input when needed so neither track ends early. Record the chosen filename in the render manifest.

## Reading-copy direction
Follow [v1-v2-editorial-style.md](v1-v2-editorial-style.md) for source-specific explanatory writing and hybrid thumbnail direction. Preserve the timeline and rendering geometry above.
