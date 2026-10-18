# V3 — Arabic carousel and standalone Facebook photo pack

This is an agent-authored image production mode, not a third MP4 renderer. Invoke with `$arabic-video-brief V3`, `carousel pack`, `launch carousel`, or `carousels and Facebook photo`. Do not send `--version v3` to the video CLI. The existing V1/V2 video and thumbnail engines are independent.

For mixed V1/V2 + V3 requests, complete the main skill’s video setup questions first. The post-pack image-method question is additional; it never replaces the earlier deep-dive and video-thumbnail questions. Read [v3-browser-execution.md](v3-browser-execution.md) before any chosen browser/MCP generation or resuming an interrupted episode.

## Selection and source reuse

- If no sources are specified, ask which YouTube links or existing processed-video folders to use. For a selection from existing work, inspect the relevant output folders and show a short list of titles; do not process every historical video automatically.
- Accept a link, several selected links, an existing source folder, or a supplied transcript. Ask for source identity/thumbnail when the transcript has neither; do not invent a video ID or borrow another video's reference.
- For video plus pack, ask V1 or V2 only if unspecified, and ask which videos need a pack if the subset is unclear. An explicit “both for all these links” answers that question. Process sources one at a time; each source may produce both deliverables.
- Reuse the same video's complete original transcript when available: supplied original transcript, saved source captions, or the matching manifest's `metadata.transcript_text`. Check source ID, language and coverage. A model-generated compact `transcript.json`, summary, or deep-dive essay is not automatically a full transcript. If only partial evidence exists, retrieve the source captions/video evidence using the available source-analysis tools or disclose the coverage and request the missing material. Do not fabricate a whole-video pack from its title.
- Store source provenance and relevant passage timestamps where available. Do not invent timestamps for a supplied untimed transcript. Verify consequential numbers and changing factual claims when needed, and distinguish source opinion, evidence and your illustrative examples.
- Retrieve and inspect the original YouTube thumbnail using the source ID or reuse its verified local file. It guides visual direction and recognizable subjects; the transcript governs factual content. Keep the original reference as a file for manual attachment.

## Editorial product

Default: one Instagram carousel of 4–6 slides and one separate Facebook photo post, both 1080×1350 (4:5). These are chosen canvases, not platform limits. All visible copy and both captions use accessible Modern Standard Arabic, correct shaping and RTL. Visual instructions may be English.

**Numeric typography invariant:** in every authored V3 Arabic headline, body, label, caption, number on a diagram/calendar, prompt's exact-text block, and finished image, use Western/ASCII numerals `0 1 2 3 4 5 6 7 8 9`, even in RTL text. For example `21–35 يوماً`, `2–12`, `18–19`, never `٢١–٣٥` or `۲۱–۳۵`. Apply this to `script.json`, both captions, and all prompt files *before* generation; check any actual printed numerals by visually inspecting each generated image. Preserve unaltered source screenshots, titles and transcripts for factual fidelity. `python tools/v3_save_image.py check --folder "outputs/<source>/v3"` checks written script/caption/prompt fields for non-Western digit glyphs.

Use the fewest slides that deliver the selected idea. Give a useful reveal by slide 2. Each slide adds an explanation, example, comparison, consequence or story beat; avoid repeating the same headline-and-paragraph layout mechanically. Summarize the chosen angle faithfully rather than cramming an entire interview into six slides.

Choose the structure for the subject; these are examples, not required slots:

| Subject | Possible progression |
|---|---|
| Psychology / practical | Hook → concrete problem → model → example/protocol → useful nuance → takeaway and question |
| Science / information | Surprise → phenomenon → mechanism/evidence → implications → limits → question |
| Current affairs | Development → context → competing explanations → evidence → consequences → question |
| History / biography | Intriguing moment → setting → turning point → consequences → interpretation → question |

Do not force statistics, protocols, health recommendations, conflict or practical tips into a source that does not support them. Entertainment or a compelling historical explanation can be the whole payoff. Maintain the user's broad topic scope; do not restrict the skill to a niche.

The ending fulfills the opening promise, with a brief takeaway where helpful and one topic-specific question or sharing invitation. Prefer a concrete experience, meaningful choice or reasoned comparison. Avoid generic “what do you think,” stacked like/save/share requests or a provocative political claim unsupported by the source. A question can invite dialogue between people who disagree without inventing a conflict.

The standalone Facebook image needs its own hook, readable explanation and complete payoff/question when viewed without its caption. It is not merely the carousel cover. Approximately 35–65 visible words is a starting design guide, not a quota. Keep the original deep-dive/video photo outputs intact; this is a separate V3 composition.

## Open art direction and reference continuity

Inspect the thumbnail and interpret the content before choosing the style. There is no permanent palette, logo, mascot, watermark, fixed layout, style menu or requirement to use cinematic imagery. A faithful stylistic adaptation, a hybrid or a new treatment may all fit. Existing video thumbnail style rules do not constrain V3.

For each episode, describe concrete rendering, materials, lighting, typography, composition and emotional rhythm. Establish intentional continuity within that episode, not a compulsory brand system across episodes. No Capsule Fikr logo is required on V3 images.

Reference order:

1. **Slide 1:** Image 1 = original YouTube thumbnail. Create one finished cover that establishes the carousel's treatment.
2. **Slides 2–6:** Image 1 = the same original thumbnail; Image 2 = the same accepted slide 1. Never replace slide 1 with only the preceding slide.
3. **Facebook photo:** original thumbnail + accepted slide 1, with an independent complete composition.

The thumbnail anchors source identity; slide 1 anchors the selected visual treatment. Do not inherit thumbnail text or previous slide text implicitly. Each prompt specifies its own exact Arabic copy. Preserve meaningful character/object identity while varying framing, pose, diagram, scene and emphasis as the storyboard requires. Extra authentic references may be included when necessary for factual depictions, with explicit roles and order.

Prepare the full pack before slide 1 exists. Mark its path as an expected output and the later images `pending_anchor`; do not claim to have inspected an image that is still pending. When the user supplies slide 1, inspect it and either accept it or describe the needed repair, then confirm/update the dependent prompts for its actual traits. References are actual attachments, not filenames mentioned in a prompt.

**Required session pattern:** use the actual YouTube thumbnail to generate the first image, inspect/accept slide 1, and use *both that identical original thumbnail (Image 1)* and *that identical accepted slide 1 (Image 2)* for **every** later slide and the Facebook standalone image. Keep all image generations for an episode in one persistent ChatGPT image-generation chat/session when that route is selected; reuse existing tab/session for every image. No separate chat per slide. Each request is a separate complete prompt, with actual image attachments in the correct order. New slide layout/story must vary without losing the accepted slide 1's style. Do not treat the most recent slide as the style anchor.

## Pack location and deliverables

New source: `outputs/<source-slug-and-id>/v3/`. Existing V1 folder: its `v3/` child. Existing `v2/` folder: sibling `v3/` under the source folder. Preserve previous final images and accepted anchors; revisions use new revision paths rather than overwriting accepted work.

Produce:

- `production-pack.md`: reader question, selected angle, evidence/coverage, complete Arabic script by image ID, storyboard, concrete art direction, reference roles, allowed changes, source notes and unresolved items.
- `references/source-thumbnail.<ext>` and `source-transcript.json`: verified source reference and transcript with identity, origin, coverage and original segments/text. The pack remains Arabic; the original transcript may retain its source language.
- `instagram/slide01 (YouTube thumbnail).prompt.txt`; later `slide02 (YouTube thumbnail + slide01 anchor).prompt.txt`, etc.
- `facebook/photo01 (YouTube thumbnail + slide01 anchor).prompt.txt`.
- `instagram/caption.txt` and `facebook/caption.txt`: separately written Arabic captions; source/creator credit, topic-appropriate question or sharing reason, relevant hashtags without a compulsory number. Put source URLs and evidence notes in the production pack; do not invent URLs.
- `script.json`: authored content by image ID, with exact headline, body, labels, takeaway/question, and purpose/storyboard. Keep it identical to the TXT prompts.
- `generation-plan.json`: executor-neutral contract below.
- `prepare-images.bat`: copy the project's `tools/prepare_v3_images.bat` into the pack under this name. It prepares posting copies after the user saves the generated images.

Each TXT must be a complete copy-paste prompt, not instructions to combine master fragments. Include canvas, purpose, concrete art direction, scene, composition, continuity constraints, intentional changes, exact Arabic text and placement, numbered input descriptions, and a request for **one finished image**. Attachment cues belong in filenames; copied prompt text refers to “Image 1: original YouTube thumbnail” and “Image 2: accepted first slide,” not local paths or invented API parameters.

## Generation plan for all methods

Write concrete values for the current pack using this contract. Paths are relative to the pack root and remain inside it. This JSON describes intended work; it does not execute an API, browser action or publication. Initially `execution` is null until the user chooses a method (unless already explicitly selected); record the chosen route before execution. Do not confuse an unanswered question with manual mode. Do not mark `generated` or `accepted` based solely on a prompt or an image preview.

```json
{
  "schema_version": 1,
  "mode": "v3",
  "execution": null,
  "source": {
    "video_id": null,
    "url": null,
    "transcript_path": "source-transcript.json",
    "thumbnail_path": "references/source-thumbnail.jpg",
    "coverage": "full"
  },
  "language": "ar",
  "canvas": {"width": 1080, "height": 1350},
  "anchor_id": "ig-slide01",
  "postprocess": {
    "command": "prepare-v3-images",
    "after": "generated images saved and inspected",
    "report_path": "posting-ready/export-report.json"
  },
  "images": [
    {
      "id": "ig-slide01",
      "platform": "instagram",
      "prompt_path": "instagram/slide01 (YouTube thumbnail).prompt.txt",
      "output_path": "instagram/slide01.png",
      "inputs": [{"order": 1, "role": "source_thumbnail", "path": "references/source-thumbnail.jpg"}],
      "depends_on": [],
      "status": "prompt_ready"
    },
    {
      "id": "ig-slide02",
      "platform": "instagram",
      "prompt_path": "instagram/slide02 (YouTube thumbnail + slide01 anchor).prompt.txt",
      "output_path": "instagram/slide02.png",
      "inputs": [
        {"order": 1, "role": "source_thumbnail", "path": "references/source-thumbnail.jpg"},
        {"order": 2, "role": "style_anchor", "path": "instagram/slide01.png", "image_id": "ig-slide01"}
      ],
      "depends_on": ["ig-slide01"],
      "status": "pending_anchor"
    }
  ]
}
```

Populate all 4–6 Instagram image records and `fb-photo01`, not just the two illustrative records above. Use the actual thumbnail extension. Unknown source identity stays null with an explanation; coverage can be `full`, `partial` or `unknown`, and must match the evidence. Status lifecycle: `pending_source`, `prompt_ready`, `pending_anchor`, `generated`, `needs_revision`, `accepted`. Only mark generated/accepted after inspecting actual supplied files. Keep retries/versioned output records with the affected image rather than regenerating the whole set.

A chosen MCP/computer-use/API executor consumes the same ordered inputs and standalone prompts, generates slide 1 first, inspects it, and generates dependent images sequentially. Skip accepted images, preserve revisions, record actual file paths, errors and progress, and stop on unresolved source/anchor problems. Use a real available tool and its established input/image-transfer capabilities: a file name in the prompt does not attach an image, and a ChatGPT output in another chat does not automatically materialize on the local Windows machine.

## Required end-of-pack image-generation checkpoint

**After completing and checking the entire V3 pack, ask exactly once** (unless the user already explicitly selected a method for this episode):

> The V3 pack is ready. How do you want to generate and save its images?
> 1. **Image API (future integration / available only with a verified image adapter)** — a saved API key alone does not implement image generation. Use only an explicitly selected, working image adapter with both-reference support, local saving, and authorized cost. Otherwise explain that this route is not implemented. Never silently switch from ChatGPT/MCP to a paid API.
> 2. **ChatGPT images through the current session / MCP / computer use** — generate images one by one in the SAME persistent generation chat/session, using original thumbnail → accepted slide 1 → remaining slides and Facebook. If the current session lacks image-generation or local-save ability, use a connected browser/computer-use tool only when available, reuse or create one browser generation chat within the chosen route when supported, and explain any manual transfer step before claiming files are saved.
> 3. **Stop here / manual** — leave the prompts, thumbnail, scripts and captions ready; the user creates and saves images themselves.

The question is the only post-pack generation-method gate; the earlier video setup gates still apply to mixed requests. Do not ask for style approval or API access while the text pack is being prepared. Keep the user's explicit choice for resuming the same episode, but ask again for a fresh episode unless they requested an ongoing default. Record the selection in `generation-plan.json` (`execution`: `api`, `chatgpt_mcp` or `manual`; optionally `provider` and `generation_session`). Do not read or disclose API secret values. Publishing requires its own separate request.

### Chosen generation paths

**API:** Only use a verified configured provider that can upload both image references and preserve 4:5 output. Run slide 1 and visually inspect it. For slide 2 onward and Facebook, send original thumbnail first and accepted slide 1 second, plus that image's full prompt. Save response files locally, record metadata/status in the plan and inspect Arabic, including Western numerals. If an API cannot accept both attachments, pause and explain rather than pretending visual continuity is maintained.

**ChatGPT/MCP/computer use:** Follow the full [sequential execution and resume procedure](v3-browser-execution.md). Prefer the current persistent image-generation chat if it supports image generation and the image bytes can be saved to the selected local folder. Otherwise use the available connected desktop browser/MCP in one maintained chat/tab for the whole episode. Upload both actual references on *every* subsequent request, send the matching full prompt, wait for the result, inspect/download/save it and register its output before advancing. When chat images are only present as attachments in a different runtime, transfer or download the actual image bytes into the local project first; never invent a source filesystem path or claim the image was saved merely because it appeared in the conversation. Avoid opening a new chat for every slide. If no capable generation or transfer tool is available, stop at the ready pack, retain the selected method and tell the user what needs connecting.

**Manual:** No image generation and no API usage. The user creates images by following the same attachment order and saves them to the planned locations. Later resume using already accepted files without regenerating them.

On resume, run `python tools/v3_save_image.py next --folder "outputs/<source>/v3"` first. Follow its action before submitting anything: saved images need inspection; active jobs need recovery; missing images need generation. `next` is a local read-only coordinator, not an image generator.

For any path, image outputs are saved in the V3 episode folder as `instagram/slide01.png` through the final carousel slide and `facebook/photo01.png`; source thumbnail remains `references/source-thumbnail.<ext>`. A local file transfer can be registered with:

```powershell
python tools/v3_save_image.py save --folder "outputs/<source>/v3" --id ig-slide01 --source "C:\path\to\downloaded_slide1.png" --method chatgpt_mcp
python tools/v3_save_image.py accept --folder "outputs/<source>/v3" --id ig-slide01 --reviewed
# Only after slide01 is inspected and accepted:
python tools/v3_save_image.py save --folder "outputs/<source>/v3" --id ig-slide02 --source "C:\path\to\downloaded_slide2.png" --method chatgpt_mcp
```

`save` validates the source image, stores the original source file under `generation-sources/`, writes the normalized 1080×1350 PNG to the planned output path, and sets its status to `generated`. The `accept` step requires a real inspection, updates its plan status to `accepted`, and unlocks the dependent prompts for slide 2 onward. An existing output is preserved; do not overwrite accepted work during a retry. The helper works with any supported method (`api`, `chatgpt_mcp`, `manual`), but it does not itself invoke an image model or operate a browser.

## Posting-image export

After generated images are saved in `instagram/` and `facebook/`, run:

```powershell
python scripts/avbrief.py prepare-v3-images --folder "outputs/<source>/v3"
```

The user can also double-click `prepare-images.bat` inside the pack. The command works with a source folder or its V3 child, and processes actual PNG/JPEG/WebP files directly inside the two platform folders, including manually named files such as `facebook/photo.png`.

It creates separate, lossless PNG copies under `posting-ready/instagram/` and `posting-ready/facebook/`. It applies EXIF orientation and converts an embedded color profile to sRGB before removing metadata. It preserves image dimensions and transparency and verifies the saved pixels; no resizing, noise, blurring, or layout changes are applied. Originals, references, and the accepted style anchor remain intact. Upload the exported files listed in the current `posting-ready/export-report.json`; inspect the report for failures. Rerun after replacing or revising an original. Do not post stale copies left over from earlier selections.

This removes embedded EXIF/XMP/C2PA/text metadata through a fresh pixel-buffer export. It cannot promise removal of invisible pixel watermarks or exemption from AI labels, and it does not turn AI imagery into Photoshop-authored work. Do not add a false Photoshop software/author tag or claim a changed file hash defeats visual detection. Visual design quality still comes from the art direction and actual image review.

The chosen generation executor should call this same local export command after image QA and use the report's verified output paths. Do not overwrite reference inputs or mark an image accepted merely because export succeeds.

## Finish

Check script/prompts/captions agree, all expected image records exist, all later images reference the original thumbnail plus slide 1, the Facebook image delivers a complete idea, and the Arabic copy and Western digits are readable on a phone. When no method has been selected, say **pack ready; images pending method selection** and ask the generation checkpoint. If the user already selected the route for this episode, proceed within that authorization without asking again. After a chosen route, report actual created and inspected local files and their real statuses. Never say “carousel generated” until images have actually been created. No new approval gate for choosing a style or drafting prompts.
