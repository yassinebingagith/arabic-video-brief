# Rendering Modes (V1 & V2)

The engine renders 1080x1920 (9:16 vertical MP4) high-definition video briefs in two distinct versions:

## Core Visual Standard (Common to V1 & V2)
- **Top Panel (1080x760):**
  - **Seamless Alpha Gradient:** Bottom video edge feathers smoothly from `y=490` to `y=760` into pure `#000000` black, eliminating hard horizontal lines and avoiding platform border warnings.
  - **Floating Glassmorphic Metadata Badge (1016x176px at y=556, radius=26px):**
    - **RTL / BiDi Awareness:**
      - **Arabic Content (RTL):** YouTube red play icon anchored on the right (`x = 924`), multi-line title right-aligned, and metadata elements ordered Right-to-Left: `[Channel Name]` • `[View Count]` • `[Upload Date]`.
      - **English Content (LTR):** YouTube red play icon on the left (`x = 56`), title left-aligned, and metadata elements ordered Left-to-Right.
    - **Full Multi-line Title:** Dynamically wrapped across 2–3 balanced lines (26px/23px Bold) with zero ellipsis (`...`) truncation.
    - **Metadata Row:** Channel, view count, and relative upload date clearly rendered in 22px/21px semi-bold with centered bullets.

## Pipeline Versions
1. **Version 1 (28.0 Seconds):**
   - 2.5s source card (kinetic Ken Burns zoom) + 17.5s video stream + 8.0s CTA page.
   - Background instrumental music (`vangelis_la_petite_fille_de_la_mer.mp3`) at 0.85 volume with 2.0s smooth fade-out (18s-20s).
   - Dedicated outro voiceover (`last voicever.mp3`) during 20s-28s CTA page.
   - See detailed spec: [references/v1-render-spec.md](v1-render-spec.md).

2. **Version 2 Extended Format (36.5 Seconds - Recommended):**
   - 2.5s source card + 26.0s video stream (across 4 summary pages, 30-44 words each) + 8.0s CTA screen.
   - ElevenLabs TTS Arabic voiceover at `t=0s` (`volume=1.3`).
   - Background music (`naruto_sadness_and_sorrow.mp3`) ducked to `0.12` during speech, swelling to `0.70`, fading at 26.5s-28.5s.
   - Dedicated outro voiceover (`last voicever.mp3`) at `t=28.5s` (`volume=1.1`).
   - `normalize=0` on FFmpeg `amix` to ensure crystal-clear vocal volume.
   - See detailed spec: [references/v2-render-spec.md](v2-render-spec.md).

## Post-Description & Publishing Standard
- In-depth, continuous narrative article style with descriptive thematic section headings (`-عنوان المحور-`) in simplified Modern Fusha.
- Concrete, real-world examples in every section.
- Universal subscription CTA and platform-agnostic hashtags.
- Total character count strictly under 2,000 characters (typically 1,600–1,900 chars).
- No chapters, no timestamps, no bullet points, and no emojis in headings.

