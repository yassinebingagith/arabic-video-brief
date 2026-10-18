# Manifest Schema Specification

## V1 Manifest (`manifest.json`)
Located in `outputs/<video-slug>/manifest.json`:
- `status`: `"success"`
- `source`: Source URL or path
- `output_dir`: Absolute path to output folder
- `created_at`: ISO timestamp
- `metadata`: Video details
- `model`: LLM model ID
- `post_title`: Translated title
- `post_description`: Narrative description (<2000 chars)
- `summary_words`: Word count of summary
- `pages_ar`: Array of 2 strings (Page 1 and Page 2)
- `ending_question_ar`: Main on-screen Arabic question
- `render`: Details (version=v1, width, height, duration=38.0, audio, music_track, ending_question_ar, timeline: page_1=[0,15], page_2=[15,30], ending=[30,38])
- `files`: Paths to video, summary, transcript, post_title, post_description, ending_question_ar, manifest

## V2 Manifest (`manifest.json`)
Located in `outputs/<video-slug>/v2/manifest.json`:
- `status`: `"success"`
- `version`: `"v2"`
- `source`: Source URL or path
- `output_dir`: Path to `.../v2/`
- `created_at`: ISO timestamp
- `metadata`: Video details
- `model`: LLM model ID
- `post_title`: Translated title
- `post_description`: Narrative description (<2000 chars)
- `hook`:
  - `display`: Text on screen
  - `highlight_phrase`: Text in gold
  - `category`: Category string
  - `tts_status`: `"success"` | `"fallback"` | `"skipped"`
  - `tts_duration`: Audio duration in seconds
- `pages`: Array of 4 page objects with `page`, `counter` (`١/٤`), `timing`, `words`, and `text`
- `ending_question_ar`: Main on-screen Arabic question
- `conclusion` (legacy field name retained for compatibility):
  - `text`: Main ending question
  - `highlights`: Highlighted words
  - `cta_save`: Save CTA
  - `cta_description`: Description CTA
- `render`: Details (width, height, duration=42.2, audio, music_track, tts_narration, timeline)
- `files`: Paths to the staged MP4, `summary-ar.txt`, `summary-pages.json`, `hook-ar.txt`, `hook-tts.txt`, `hook-voice.mp3`, `ending-question-ar.txt`, `conclusion-ar.txt`, `cta-ar.txt`, `creative-plan.json`, `manifest.json`

## V3 Manual Image Pack
V3 uses `generation-plan.json` rather than a video render manifest. Its ordered references, anchor dependencies, prompts, intended output paths and manual generation states are defined in [v3-carousel-pack.md](v3-carousel-pack.md).
