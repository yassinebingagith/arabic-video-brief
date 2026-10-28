# Animated reading-page comparison

This preview tool builds the agreed HTML/SVG/GSAP reading-page treatment and renders it with the installed Hyperframes 0.8.30 runtime. It accepts a saved **V2** episode folder and creates a separate **50.2-second** comparison. Production V2 timing is 12.8/9.8/9.8/9.8 seconds plus the existing eight-second ending; production whiteboard integration remains separate.

The HTML contains native Arabic text with the existing Noto Sans Arabic variable font. Pillow supplies the established line breaks, font sizes and segment advances; `textLength` preserves those advances in the browser. Text stays editable. Only the existing background and brand-frame artwork are raster assets.

After user feedback, quick line fades were replaced by whiteboard writing. `strokes.py` derives invisible centerline guides from the existing font using NumPy/OpenCV thinning. GSAP draws those guides as SVG masks over complete shaped words. A final mask settle restores complete glyph edges. Following the two-second extension per page, writing lasts approximately 11.5 seconds on page 1 and 8.83 seconds on later pages, weighted by word length and punctuation. Gold markers follow the last written word of their phrase. No pen or hand is visible.

Run from `F:/Arabic Brief` with a fresh output folder:

```powershell
.venv/Scripts/python.exe tools/animated_reading/prepare.py --source '<existing-v2-folder>' --out 'work/animated-reading/<comparison>'
& 'C:/Users/Yassine/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' tools/animated_reading/inspect.mjs 'work/animated-reading/<comparison>/Project'
./tools/animated_reading/render.ps1 -Project 'work/animated-reading/<comparison>/Project'
.venv/Scripts/python.exe tools/animated_reading/compose.py --folder 'work/animated-reading/<comparison>'
.venv/Scripts/python.exe tools/animated_reading/verify.py --folder 'work/animated-reading/<comparison>'
```

`prepare.py --reference-video '<local-reference.mp4>'` can reuse an unchanged local copy of the supplied export to avoid copying it again across the network. Preparation refuses populated output folders. The composition stage refuses to overwrite an existing preview.

For a legacy 42.2-second reference, first run `.venv/Scripts/python.exe tools/animated_reading/extend_reference.py --episode '<existing-v2-folder>' --reference-video '<legacy-export.mp4>' --output '<new-reference.mp4>'`, then pass that new reference to preparation. This comparison helper preserves opening/ending playback speed, slows the middle top-video excerpt to fill the extra time, reuses the saved hook, extends the same selected music with the existing ducking/fade, and shifts the original eight-second outro. It writes a receipt describing those adjustments. New production episodes use a longer excerpt at normal speed.

Authoring sources are `template.html`, `motion.js`, `strokes.py` and `prepare.py`. Preparation embeds the motion and page data into the output `Project/index.html` to satisfy the Hyperframes composition scope. The output also includes readable `motion.js`, `page-data.json`, the original `summary-pages.json`, fonts, GSAP and artwork. Edit the generated `index.html` directly for an isolated project change, or edit these authoring sources and prepare a fresh comparison for repeatable changes. Editing the output motion/data copies alone does not update the embedded HTML.

The page component is 1080×1140, placed at y=780 during 0–42.2 seconds. The timing-matched reference supplies the top video, its AAC packets are copied, and its picture supplies the final eight seconds. The final encode is 1080×1920, 30 fps, H.264 CRF 20, all-intra. Pixel values in retained picture regions can differ slightly because the comparison is re-encoded. Duration and frame-count checks derive from the composition data.

Inspection checks fonts, paragraph visibility, text overflow, adjacent segment overlap, marker progression, exclusive page visibility and repeatable seeks. Verification checks the actual MP4, all six encoded text lines per page, original audio-packet equality and retained-picture error. Review the chronological PNG sheets for visual judgment. Some browser screenshots taken after large seeks can retain stale SVG paint; the encoded-frame sheets are the delivery review evidence.

Current extended preview: `F:/Arabic Brief/work/animated-reading/pollan-v2-whiteboard-plus2-r1/Preview.mp4`. The earlier 42.2-second whiteboard preview and quick-reveal comparison remain preserved. Inspection checks that writing progresses through the page and completes before the final hold. Encoded verification checks accumulating ink in the first word as well as final text visibility.
