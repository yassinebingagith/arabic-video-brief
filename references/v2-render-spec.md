# V2 Render Specification (59.8-Second Format)

## Overview & Timeline Structure
- **Format:** 1080x1920 (9:16 vertical), 30 fps, H.264/AAC MP4.
- **Top Panel:** y=0 to y=760 (1080x760 px).
- **Lower Panel:** y=760 to y=1920 (1080x1160 px).
- **Total Duration:** 59.8 seconds (57.0s reading across 5 pages + 2.8s gamified outro).
- **Audio Mix:**
  - **Hook TTS Voiceover:** (`work/hook_tts.mp3`) starts at `t=0.0s` (`volume=1.3`).
  - **Selected V2 Background Music:** ducked to ~35% volume during hook narration (0-4.5s), then restores to standard volume (`volume=0.85`), playing continuously across all 5 reading slides and the final outro slide, with a gentle 0.5s fade-out at the very end (`st=59.3s`, `d=0.5s`).
  - **Outro Voiceover:** Completely removed. The background music carries through to the end of the video.

---

## Detailed Timeline Chronology

1. **0:00 - 0:13.8 (13.8s) - Page 1 (Everyday Dilemma / Relatable Trap):**
   - Top panel: 0:00-0:02.5 source card with kinetic Ken Burns push-in zoom and floating translucent metadata badge; 0:02.5-0:13.8 video playback begins with seamless bottom gradient blend and floating metadata badge.
   - Lower panel: Translated Arabic title header block + Category tag + 6-line summary paragraph.
   - Visual Motion: Entire pre-wrapped paragraph fades in all at once over 0.35s (opacity 0% to 100% with subtle 12px upward slide). Text remains 100% visible and static. Key phrase starts in white; at 1.5s, animates transition to yellow highlight (#FFD700) smoothly from right to left across words over 0.6s (finishing at 2.1s).
   - Bottom indicator: Continuous filling brain fills from 0% to 20%, slide timer bar fills 0-100%, page badge "1 / 5".

2. **0:13.8 - 0:24.6 (10.8s) - Page 2 (Dedicated Concrete Anchor):**
   - Top panel: Excerpt continues playing cleanly with subtle edge framing.
   - Lower panel: Dedicated Concrete Anchor (quote, personal anecdote, study with numbers, or paradox).
   - Visual Motion: Instant paragraph fade (0.35s, 12px slide). Highlighter sweep at 1.5s over 0.6s (finishing at 2.1s). Remainder of slide holds 100% static for natural reading.
   - Bottom indicator: Continuous filling brain fills from 20% to 40%, slide timer bar fills 0-100%, page badge "2 / 5".

3. **0:24.6 - 0:35.4 (10.8s) - Page 3 (Core Mechanism / Root Cause):**
   - Lower panel: Explanatory paragraph on underlying mechanism.
   - Visual Motion: Instant paragraph fade (0.35s, 12px slide). Highlighter sweep at 1.5s over 0.6s (finishing at 2.1s). 100% static hold until transition.
   - Bottom indicator: Continuous filling brain fills from 40% to 60%, slide timer bar fills 0-100%, page badge "3 / 5".

4. **0:35.4 - 0:46.2 (10.8s) - Page 4 (Deepening Insight / Framework / Hidden Cost):**
   - Lower panel: Deeper insight / framework / systemic impact.
   - Visual Motion: Instant paragraph fade (0.35s, 12px slide). Highlighter sweep at 1.5s over 0.6s (finishing at 2.1s). 100% static hold until transition.
   - Bottom indicator: Continuous filling brain fills from 60% to 80%, slide timer bar fills 0-100%, page badge "4 / 5".

5. **0:46.2 - 0:57.0 (10.8s) - Page 5 (Actionable Shift / Practical Takeaway):**
   - Lower panel: Concrete takeaway / actionable behavioral shift.
   - Visual Motion: Instant paragraph fade (0.35s, 12px slide). Highlighter sweep at 1.5s over 0.6s (finishing at 2.1s). 100% static hold until transition.
   - Bottom indicator: Continuous filling brain fills from 80% to 100%, slide timer bar fills 0-100%, page badge "5 / 5".

6. **0:57.0 - 0:59.8 (2.8s) - Gamified "100% Brain Overcharge" Screen:**
   - Top panel: Static source card / thumbnail with seamless gradient blend.
   - Lower panel:
     - Yellow conclusion question title at top with drop shadow.
     - 1.12x scaled 100% full gold brain with dual aura bloom (wide gold outer glow + intense white core bloom).
     - Gamified achievement badge text in crisp Arabic:
       - Header gold pill: `⚡ اكتمل شحن الفكرة 100%`
       - Dark card with gold outline:
         `تركيزك أعمق من 90% من المتصفحين!`
         `الشرح الكامل في الوصف 👇`
   - Audio: Background music continues playing smoothly with a gentle 0.5s fade-out at 59.3s-59.8s. No outro voiceover.

---

## Continuous "Filling Brain" Progress Indicator
- Position: Y=1680 (local y=920 in lower panel), centered horizontally.
- Brain Icon: 72x76 px silhouette in dark blue panel. Smoothly filled from bottom to top with `#FFD700` synced frame-by-frame:
  - Slide 1: 0% -> 20%
  - Slide 2: 20% -> 40%
  - Slide 3: 40% -> 60%
  - Slide 4: 60% -> 80%
  - Slide 5: 80% -> 100%
- Timer & Badge: Underneath brain, a 160px horizontal progress bar (current slide timer) and an Arabic badge ("1", "2", "3", "4", "5").
- Outro Screen Transition: Brain locks at 100%, scales 1.12x (82x86px), and activates dual aura bloom with the gamified achievement badge.
