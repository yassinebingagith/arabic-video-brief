# V1 Render Specification (28-Second Format)

## Overview
- **Total Duration:** 28.0 seconds.
- **Resolution & Aspect Ratio:** 1080×1920 (9:16 vertical MP4).
- **Background Music:** Contemplative instrumental (`vangelis_la_petite_fille_de_la_mer.mp3`) at 0.85 volume with 2.0s smooth fade-out between 18.0s and 20.0s.
- **Outro Voiceover:** Dedicated outro narration (`assets/music/last voicever.mp3`) playing across 20.0s – 28.0s (8.0 seconds) during the final CTA page.
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
- **0:00 – 0:02.5 (2.5s):** Top panel shows source card with kinetic Ken Burns push-in zoom and floating translucent metadata badge. Bottom panel shows Page 1.
- **0:02.5 – 0:10 (7.5s):** Top panel plays video stream at `selected_clip["start_seconds"]` with seamless bottom gradient blend and floating metadata badge. Bottom panel continues showing Page 1.
- **0:10 – 0:20 (10.0s):** Top panel continues video playback (total 17.5s video stream). Bottom panel displays Page 2 with footer: `اقرأ الوصف لمزيد من التفاصيل`. Music fades out between 18.0s and 20.0s.
- **0:20 – 0:28 (8.0s):** Top panel displays thumbnail card with kinetic Ken Burns zoom and floating badge. Bottom panel shows CTA page (action pill, logo, description badge) accompanied by the outro voiceover.

## Text & Typography
- **Total Words:** 140–160 Modern Standard Arabic words split into two 70–80 word panels.
- **Safe Zone:** 6% left-shift (~65px) to clear platform right-side interaction icons (TikTok/Reels/Shorts).

