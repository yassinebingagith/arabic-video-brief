# Animated reading-page comparison

This preview tool builds the agreed HTML/SVG/GSAP reading-page treatment and renders it with the installed Hyperframes 0.8.30 runtime. It currently accepts a saved **V2** episode folder and creates a separate 42.2-second comparison. Production V1/V2 renderers are not switched by this tool.

The HTML contains native Arabic text with the existing Noto Sans Arabic variable font. Pillow supplies the established line breaks, font sizes and segment advances; `textLength` preserves those advances in the browser. Text stays editable. Only the existing background and brand-frame artwork are raster assets.

After user feedback, quick line fades were replaced by whiteboard writing. `strokes.py` derives invisible centerline guides from the existing font using NumPy/OpenCV thinning. GSAP draws those guides as SVG masks over complete shaped words. A final mask settle restores complete glyph edges. Writing lasts approximately 9.5 seconds on page 1 and 6.84 seconds on later pages, weighted by word length and punctuation. Gold markers follow the last written word of their phrase. No pen or hand is visible.

Run from `F:/Arabic Brief` with a fresh output folder:

```powershell
.venv/Scripts/python.exe tools/animated_reading/prepare.py --source '<existing-v2-folder>' --out 'work/animated-reading/<comparison>'
& 'C:/Users/Yassine/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' tools/animated_reading/inspect.mjs 'work/animated-reading/<comparison>/Project'
./tools/animated_reading/render.ps1 -Project 'work/animated-reading/<comparison>/Project'
.venv/Scripts/python.exe tools/animated_reading/compose.py --folder 'work/animated-reading/<comparison>'
.venv/Scripts/python.exe tools/animated_reading/verify.py --folder 'work/animated-reading/<comparison>'
```

`prepare.py --reference-video '<local-reference.mp4>'` can reuse an unchanged local copy of the supplied export to avoid copying it again across the network. Preparation refuses populated output folders. The composition stage refuses to overwrite an existing preview.

Authoring sources are `template.html`, `motion.js`, `strokes.py` and `prepare.py`. Preparation embeds the motion and page data into the output `Project/index.html` to satisfy the Hyperframes composition scope. The output also includes readable `motion.js`, `page-data.json`, the original `summary-pages.json`, fonts, GSAP and artwork. Edit the generated `index.html` directly for an isolated project change, or edit these authoring sources and prepare a fresh comparison for repeatable changes. Editing the output motion/data copies alone does not update the embedded HTML.

The page component is 1080×1140, placed at y=780 during 0–34.2 seconds. The original top video is retained, the existing AAC packets are copied, and the original picture supplies the final eight seconds. The final encode is 1080×1920, 30 fps, H.264 CRF 20, all-intra, with the original AAC audio. Pixel values in retained picture regions can differ slightly because the comparison is re-encoded.

Inspection checks fonts, paragraph visibility, text overflow, adjacent segment overlap, marker progression, exclusive page visibility and repeatable seeks. Verification checks the actual MP4, all six encoded text lines per page, original audio-packet equality and retained-picture error. Review the chronological PNG sheets for visual judgment. Some browser screenshots taken after large seeks can retain stale SVG paint; the encoded-frame sheets are the delivery review evidence.

Current reviewed preview: `F:/Arabic Brief/work/animated-reading/pollan-v2-whiteboard-r3/Preview.mp4`. The original quick-reveal comparison remains preserved at `pollan-v2-r4`. Inspection now checks that writing progresses through the page and completes before the final hold. Encoded verification checks accumulating ink in the first word as well as final text visibility.
