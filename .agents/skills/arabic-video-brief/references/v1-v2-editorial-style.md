# V1/V2 explanatory writing and source-led thumbnails

Read this for V1/V2 authoring, including Brainstorm JSON and video thumbnail prompts.
V3 keeps its existing independent instructions and outputs.

## Reading copy

Use the Core Explanatory Body approach from the user's Think Again carousel reference:
a specific event, observation or example draws the reader in; the copy explains the
mechanism behind it; the next beat adds evidence, comparison, consequence or nuance.
The source determines which progression fits. The reference illustrates writing style;
its historical claims and statistics must not be reused as verified source evidence.

Write accessible Modern Standard Arabic with concrete nouns and active verbs. Give the
reader an explanation on the first page, not a long teaser. Preserve important source
names, numbers, causal links and qualifications. Avoid formal synopsis language,
generic statements about awareness or success, repeated hooks, obligatory tips,
manufactured secrets, motivational conclusions and identical rhetorical patterns.
Do not invent anecdotes or advice to fill the word budget. Each page must add information
that the previous page did not provide. Before delivery, remove sentences that could
fit unrelated episodes unchanged. Vary the narrative structure to suit the content.

- V1: two authored paragraphs/pages, each 70–80 words, 140–160 total. Page 1 begins
  explaining; page 2 develops the idea. Keep 15s + 15s + existing 8s ending.
- V2: four authored complete explanatory beats, each 30–44 words, 140–160 total.
  Plan the transitions deliberately rather than cutting a V1 paragraph at arbitrary
  word counts. Keep 10.8s + 7.8s + 7.8s + 7.8s + existing 8s ending.
- Neither format requires a fixed hook/problem/tips/conclusion sequence. Render design,
  page count, audio, spoken title and timing remain unchanged.

## Final screen

V2's main text on the existing 8-second screen is a carousel-style Footer Action /
Question: one concrete question or useful action tied to a detail the pages explained.
Prefer an answerable question about evidence, a decision, a mechanism or an experience.
Use an action only when the source supports it. Keep 4–18 words and at most 140 characters.
No declarative punchline, generic “ما رأيك؟”, swipe instruction, or stacked engagement asks.
The footer is displayed, not narrated. Preserve the existing recorded outro and badges.

Example for a rethinking episode: `ما الدليل الذي قد يدفعك إلى مراجعة قناعة تتمسك بها؟`
An action alternative: `اختر قناعة واحدة واكتب الدليل الذي يمكن أن يغيّرها.`
These illustrate specificity, not reusable endings for unrelated videos.

Save V2's canonical footer as `ending-text-ar.txt`. Keep `conclusion-ar.txt` and
`ending-question-ar.txt` as compatibility aliases, even when the footer is an action.
V1 still uses `ending_question_ar` / `ending-question-ar.txt` as a question.
Rerender reuses saved copy; it does not rewrite old summaries automatically.

## Thumbnail direction

Inspect the original thumbnail and understand the topic before choosing an episode's
treatment. Preserve its actual medium and visual language: surrealism stays surrealism,
illustration stays illustration, collage stays collage, and source hybrids stay hybrid.
A real speaker's name does not force photography; a philosophy keyword does not force
oil painting. No automatic palette, historical props, desk composition, amber lighting,
or style menu. The old keyword presets are not the default production path.

Consider face-led, scene/object-led and hybrid concepts. Pick the composition that
communicates the strongest source-grounded curiosity gap at grid size. A recognizable
face is useful when it contributes; it is not mandatory. Preserve dimensional faces,
likeness, natural textures and purposeful lighting within the source's artistic medium.
Vary framing, palette, viewpoint, scale, background and typography with the source.
Bright treatments and clean cutouts are valid. Avoid waxy skin, generic CGI gloss,
unmotivated props, visual clutter and distorted Arabic. No promised engagement metric.

Author a separate `thumbnail_hook_ar`: preferably 3–8 Arabic words, maximum 10 words /
70 characters, grounded in the source's specific question, contrast or consequence.
Keep `post-title.txt` and the spoken title as faithful translations. The short hook is
for the cover only. Save `thumbnail-hook-ar.txt` when available. For older folders
without one, the image prompt explicitly asks the image generator to author the short
hook from saved content; the guide marks the text as pending rather than pretending
an exact headline has already been chosen.

Manual prompts use the actual original thumbnail as Image 1. A path in prompt text is
not an attachment. The image generator inspects this reference; text-only code must
not claim to have visually classified it. KIE.ai uses the verified source thumbnail URL;
if unavailable, retain prompts and explain the failure instead of borrowing another
episode's image. Without any reference, label direction as topic-only.

Keep existing 4:5/9:16 outputs and vertical safe areas (title Y 320–560, central subject
Y 580–1420, text-free bottom Y 1450–1920). Check actual feed previews; square cropping
can trim the headline. V3 images never substitute for these video covers.

## Brainstorm / supplied analysis

Author `summary_ar`, `post_title_ar`, `post_description`, `ending_question_ar` and source
transcript fields as before. For V2, supply `pages` as four strings (or four objects
with `text`) and `ending_text_ar`. Include `thumbnail_hook_ar` when covers are requested.
Optional `thumbnail_concept` can contain the episode-specific visual idea and observed
source treatment, but it must not impose the old cinematic defaults. Supply the
complete authored package to avoid unnecessary text API calls. Existing authored pages
remain reusable explicitly; new V2 runs do not silently inherit an old V1 summary.
