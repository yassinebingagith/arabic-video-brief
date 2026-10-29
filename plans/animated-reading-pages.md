# Python/FFmpeg whiteboard rendering

V1 and V2 use the same native Python page engine in their normal production renderers. There is no browser, JavaScript runtime or separate animation framework in this rendering path.

## Setup

Run `python scripts/setup.py` once (Python 3.11+). Pillow, NumPy and OpenCV are base dependencies. FFmpeg and FFprobe are discovered on PATH or installed by the Python media bootstrap; explicit FFMPEG_BINARY/FFMPEG_BIN and FFPROBE_BINARY/FFPROBE_BIN overrides are supported. `python scripts/media_doctor.py` verifies them. Optional publishing browser dependencies are separate from rendering.

## Production contract

Use the existing `avbrief run ... --version v1|v2` and `avbrief rerender <episode-folder>` commands with the normal required editorial choices. Both production functions call WhiteboardProject directly. V1 is 38 seconds (15/15/8); V2 is 50.2 seconds (12.8/9.8/9.8/9.8/8). Keep full copy and two or three gold phrases per page; whole highlighted phrases and attached Arabic prefixes stay together on a line. Text is shaped for Arabic before deriving glyph masks and stroke paths. Strokes are revealed across the page's reading interval with brief punctuation pauses; completed words remain visible. Markers sweep right to left after their phrases are written. The source video and existing audio/export composition remain in their original renderers.

## Complete editable delivery

Each episode folder contains the final MP4, its normal Arabic editorial files and manifest, plus `render-project/`:

- `project.json`: editable Arabic texts, title, ending, motion controls, timing/settings and relative asset paths.
- `assets/`: retained source footage, thumbnail, font/license, branding, selected music, hook/outro and intermediate source panel when present.
- `pages/page-N/`: settled layout PNG, base/background PNGs, per-word masks and `motion.json` stroke/marker timing data.
- `pages/page-N.mkv`: lossless animated reading-region intermediates and encode logs.
- `engine/`, `requirements.txt`, `render.py`: bundled Python source and local rerender entry point.
- `export.json`: the final FFmpeg composition arguments with portable asset paths and unchanged audio/metadata parameters.

Copy the whole episode folder to another computer. Inside render-project, run `python -m pip install -r requirements.txt`, edit project.json as needed, then `python render.py --output ../CapCut_1080p_whiteboard_rerender.mp4`. Existing output paths require `--overwrite`. This rebuilds the complete video from retained media without API calls or another project's files. Fonts/audio and full source media increase package size intentionally. No API keys or browser sessions are included.

The automatic page schedule uses available page time; it does not guarantee comfortable reading for every text length. Inspect the preview, preserve full text, and extend page durations if the user requests slower reading. Keep requested timing unchanged otherwise.

## Verification

Run `python scripts/python_whiteboard_smoke.py` for synthetic V1/V2 exports without API keys. Tests verify stroke progression, retained words, marker direction, output duration, package assets and existing CapCut/mp42 metadata. Full integration tests exercise 38-second V1 and 50.2-second V2 outputs. These metadata settings do not establish how a platform classifies content.
