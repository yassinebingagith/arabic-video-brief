# Animated reading pages — V1 and V2

Interview decisions recorded 2026-10-28. Separate V2 whiteboard comparisons have been implemented and rendered. Production V2 timing has been extended; production whiteboard integration and the V1 renderer remain separate.

## Latest timing decision — two more seconds per V2 reading page

The user chose to preserve the full text and extend each of the four reading pages and its writing animation by two seconds. The current V2 schedule is page 1: 0–12.8; page 2: 12.8–22.6; page 3: 22.6–32.4; page 4: 32.4–42.2; ending: 42.2–50.2 seconds. Writing lasts approximately 11.5 seconds on page 1 and 8.83 seconds on later pages. The measured animation extension is within one frame of two seconds per page, with text unchanged.

V2 configuration, CLI labels, renderer timing expectations and mirrored skill specifications now use the 50.2-second schedule. V1 is unchanged. Production whiteboard integration remains separate from this page-preview builder.

Extended preview: `F:/Arabic Brief/work/animated-reading/pollan-v2-whiteboard-plus2-r1/Preview.mp4`. Its reference remixes the same music and saved hook to the new reading window, shifts the original eight-second outro, and slightly slows the example's middle top-video footage. New production episodes can extract longer source footage at normal speed. Earlier previews remain preserved; subsequent sections record their historical timing.

## Current revision — supersedes the initial line-reveal treatment below

The user rejected the 1.2-second line entrance as too fast and requested whiteboard-style writing without a pen or hand, following the reader. The current composition therefore draws native shaped Arabic words through invisible font-derived stroke masks. Written words remain in place. The gold marker follows the final written word of each highlighted phrase. Lines do not move or fade in as whole units.

Page 1 writes from 0.45 to 9.96 seconds; later pages write across approximately 6.84 seconds each. Word slots follow word length and punctuation, leaving a final hold before the existing outgoing fade. With about 40 words per 7.8-second page, slower pacing beyond this revision requires shorter copy or longer page windows; neither change has been made.

Current preview: `F:/Arabic Brief/work/animated-reading/pollan-v2-whiteboard-r3/Preview.mp4`.
Editable project: `F:/Arabic Brief/work/animated-reading/pollan-v2-whiteboard-r3/Project/index.html`.
Verification and chronological visual sheets are in that preview folder. Verified 42.2 seconds, 1080×1920, 30 fps, original AAC packets unchanged, and all text present at the final reading holds. Encoded close-ups show accumulating letter strokes; page sheets show successive words and phrase highlights. The earlier preview remains preserved. Production integration and V1 support are still pending review of the treatment.

The remaining sections record the original interview and first comparison; their quick-reveal tuning is historical.

## Objective

Replace static reading-page images with HTML/CSS/JavaScript pages rendered through Hyperframes, then composed with the existing source-video and audio pipeline through FFmpeg. Give viewers a guided reading experience while preserving the existing Arabic editorial style. Platform ranking improvements are an untested hypothesis, not an acceptance criterion or promise.

## Confirmed user decisions

- Short sequential line reveals; all revealed lines remain visible together.
- Right-to-left gold marker strokes behind 2–3 key phrases per page. Strokes stay visible after being drawn and are staggered through the reading hold, approximately following the reader.
- Preserve bold white Arabic typography and the black/deep-navy radial glow.
- Preserve the actual current top-video geometry, thumbnail-to-source-video sequence, metadata badge, blue outer frame and overall canvas. Do not resize the top video to a new percentage.
- Brief fade-out followed by the next page's line reveal.
- Keep the final 8-second screen entirely unchanged, including its existing motion, wording, artwork and audio.
- Preserve current V1/V2 editorial writing, page durations, music choices, narration, audio mixing and export settings.
- Keep highlighted phrases on one line with attached Arabic prefixes inside the highlighted unit.

## Reference

User-supplied folder:
`\\192.168.0.86\d\Yesine\Done-Can-a-Plant-a-Chatbot-or-Your-Gut-Be-Conscious-With-Michael-Pollan-B9DWJl3UQEI\v2`

Inspected saved page JSON and sampled actual export frames at 1, 5, 12, 21, 29 and 36 seconds. Export is 1080×1920, 42.2 seconds. Four reading pages contain 40, 40, 41 and 38 words. Samples show six-line paragraphs, gold text over translucent gold backgrounds, source metadata and a blue outer frame. Use the actual export and its manifest to establish geometry before implementation; do not substitute approximate coordinates from older documentation. These samples establish appearance, not a complete frame-by-frame motion audit. Source copy is reference material, not independently verified factual evidence.

## Fixed timeline

| Version | Reading-page windows | Existing ending |
| --- | --- | --- |
| V1 | 0–15, 15–30 seconds | 30–38 seconds |
| V2 | 0–10.8, 10.8–18.6, 18.6–26.4, 26.4–34.2 seconds | 34.2–42.2 seconds |

All transitions occur inside these windows; no added duration or shifted audio cues.

## Proposed first-preview tuning

These are engineering starting values, not separately user-approved timings.

- Complete the paragraph's sequential entrance in approximately 1–1.3 seconds, using a short opacity fade and very small upward movement per line.
- Reserve every line's final position from the start so later lines never reflow earlier text.
- Preserve Arabic shaping by animating complete line wrappers rather than individual letters.
- Schedule each marker from its phrase's position in the paragraph, after that line is fully visible. Use estimated reading progression, not claimed eye tracking or narration alignment.
- Draw each rounded translucent marker right-to-left over roughly 0.35–0.5 seconds, then retain it. Keep the established gold lettering and final highlight appearance.
- Finish the final highlight comfortably before the outgoing fade.
- Use approximately 0.15–0.2 seconds at the end of a reading-page window for its fade-out. Start the next reveal at the exact existing boundary. Transition to the unchanged ending at its exact start time.
- Keep paragraph text stationary after entrance. The staggered marker strokes provide the later activity.

## Implementation workflow

1. Read saved page text and `<hl>` spans without rewriting the editorial content. Reuse existing source, thumbnail, audio and metadata assets.
2. Measure the reference composition and inspect the current renderer to identify page-only replacement boundaries, fonts, safe areas and scaling. Preserve the source panel and outer frame through the existing compositor.
3. Build a reusable RTL HTML/CSS page template. Wrap highlighted phrases as nonbreaking units, preserving attached prefixes. Load the exact existing fonts before layout and capture.
4. Resolve stable rendered lines while keeping highlight units intact; animate their wrappers without changing line geometry. Validate overflow against both V1's longer pages and V2's shorter pages.
5. Drive entrance, marker and fade states using a deterministic seekable JavaScript/GSAP timeline compatible with the installed Hyperframes runtime. Do not depend on wall-clock timers or uncontrolled CSS animation playback.
6. Render only the reading-page component through Hyperframes. Choose an intermediate with a verified alpha/compositing contract or an exact opaque page-region replacement; avoid covering the preserved source panel or frame.
7. Have FFmpeg composite the animated pages into the existing V1/V2 output timeline and retain the current audio assembly and final-screen path.
8. Deliver an editable project and separate comparison preview before replacing any production default. Preserve the supplied published export and other completed videos.

## Review criteria

- Exact total duration and unchanged page boundaries, top geometry, source sequence, audio and ending.
- Matching settled appearance, safe areas and typography.
- Natural RTL reading order; intact Arabic joins, punctuation and attached prefixes.
- No split highlights, clipping, blank-frame flashes, line reflow or overlapping page states.
- Lines visible early enough for the original reading duration; later marker strokes clearly visible without obscuring text.
- Inspect moving sequences as well as frames at entrances, marker midpoints, page boundaries and the ending handoff.
- Verify actual encoded output dimensions, frame rate, duration and audio against the existing export settings.

## Next deliverable

A separate V2 comparison preview using this supplied example's saved page text, with the settled direction above. Use it to judge reveal and marker pacing before integrating the shared page renderer for both V1 and V2. The preview is a visual engineering comparison; it is not a new factual endorsement or publishing action.

## Delivered comparison

- Preview: `F:/Arabic Brief/work/animated-reading/pollan-v2-r4/Preview.mp4`.
- Editable composition: `F:/Arabic Brief/work/animated-reading/pollan-v2-r4/Project/index.html`.
- Reusable preview builder and documentation: `F:/Arabic Brief/tools/animated_reading/`.
- Actual-output verification: `F:/Arabic Brief/work/animated-reading/pollan-v2-r4/verification.json`.
- Visual review: `F:/Arabic Brief/work/animated-reading/pollan-v2-r4/Review/`.
- Verified 1080×1920, 30 fps, 1266 frames, 42.2 seconds. Original AAC packets match exactly; sampled top-panel and ending pictures match within re-encoding tolerance. All six text lines are present after each entrance. Output decodes without errors.
- Reviewed encoded chronological sheets for line entrances, right-to-left marker growth, the first page transition, four settled reading pages and the ending. Text remains legible, highlighted units remain intact, adjacent segment spacing is preserved, and the navy/blue frame continues across the retained top panel and replacement page area.
- The standalone builder currently supports V2 comparisons. V1 layout support and production integration follow review of this treatment; neither is claimed as complete.
