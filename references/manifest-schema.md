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
- `render`: Details (width, height, duration=20.0, audio, music_track)
- `files`: Paths to video, summary, transcript, post_title, post_description, manifest

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
- `conclusion`:
  - `text`: Main conclusion
  - `highlights`: Highlighted words
  - `cta_save`: Save CTA
  - `cta_description`: Description CTA
- `render`: Details (width, height, duration=26.0, audio, music_track, tts_narration, timeline)
- `files`: Paths to `brief.mp4`, `summary-ar.txt`, `summary-pages.json`, `hook-ar.txt`, `hook-tts.txt`, `hook-voice.mp3`, `conclusion-ar.txt`, `cta-ar.txt`, `creative-plan.json`, `manifest.json`
