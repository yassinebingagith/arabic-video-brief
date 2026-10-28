"""Shared V1/V2 writing direction; V3 has its own independent workflow."""

CORE_EXPLANATORY_STYLE = """
Write like a compelling explanatory carousel, in accessible Modern Standard Arabic.
Choose a specific angle from this source. Start with its strongest concrete event,
observation, experiment, example or puzzle, and explain why it matters immediately.
Connect what happened to how/why it happened: name the mechanism in ordinary words,
then deepen it with a distinct example, comparison, consequence or useful limitation.
Every page advances understanding; do not repeat the hook, paraphrase the previous
page or finish with a generic motivational lesson. Vary the progression with the
source: a story, scientific mechanism, historical turning point and practical
explanation need different structures. Do not impose a shocking hook, hidden secret,
three tips, self-improvement advice or philosophical punchline on every episode.
Prefer concrete nouns and active verbs to abstract claims about awareness, success,
transformation and the importance of change. No 'يناقش الفيديو', 'في عالمنا اليوم',
'في النهاية', 'يكمن السر', or interchangeable 'ليس X بل Y' rhetorical templates.
Keep the source's meaningful names, numbers, causal details and qualifications.
Never invent a statistic, study, anecdote, motive, outcome or factual certainty to
make the story stronger. Distinguish an illustrative analogy from source evidence.
Use event -> explanation -> insight when it fits; do not force that order or reuse
the same metaphor across unrelated topics.
Before returning, remove any sentence that could fit an unrelated episode unchanged.
""".strip()

SUMMARY_SPEC = """
4. `summary_ar`: 140–160 Arabic words in exactly two paragraphs of 70–80 words,
   separated by a single newline. Each paragraph is a V1 reading page. Apply the
   CORE EXPLANATORY STYLE below. Deliver an explanation on page 1, not just a teaser;
   page 2 develops the idea rather than repeating it. No headings or bullet lists.
   CRITICAL HIGHLIGHT RULE (V1 & V2): In each paragraph of summary_ar (for V1) and on each
   of the 4 pages (for V2), wrap 2 to 3 key phrases (each 2–3 words long) inside <hl>...</hl> tags
   (book highlighter style, e.g. <hl>وكيمياء عصبية تختفي</hl>).
   Always keep attached single-letter Arabic prefixes (و, ف, ب, ل, ك) INSIDE the <hl> tag
   (e.g., <hl>وكيمياء عصبية تختفي</hl>, never و<hl>كيمياء عصبية تختفي</hl>).
   STRICT NO-CTA RULE IN SUMMARY: Absolutely NEVER conclude summary_ar or page 2 with meta-CTAs or
   phrases pointing to the description (such as 'المزيد من التفاصيل في صندوق الوصف' or 'اقرأ الوصف');
   the final 8-second video ending screen already handles all calls to action.
   Think in four linked explanatory beats within these two paragraphs so V2 can
   give each beat its own page. End sentences at meaningful beat boundaries.
   Also return `pages`: exactly four strings of 30–44 words each for V2. Write each
   as a complete explanatory beat with its own new information, using the same
   source-grounded angle as summary_ar. Total 140–160 words. These are authored
   pages, not arbitrary equal-sized cuts; no repeated introductions or conclusions.
   Return `thumbnail_hook_ar`: one engaging Arabic thumbnail headline, preferably
   3–8 words, maximum 10 words / 70 characters. Choose a specific unresolved question,
   surprising contrast or consequence supported by the source, without exaggeration.
   It is separate from the faithful translated post_title_ar and spoken title.
   Return `ending_text_ar` for V2's final 8-second screen: one topic-specific question
   or useful action, 4–18 words / at most 140 characters, inspired by a carousel footer.
   Tie it to a concrete detail explained on the pages. No declarative conclusion,
   generic 'ما رأيك؟', swipe instruction, or stacked like/save/share/follow requests.
   A question is usually appropriate; use an action only when the source supports it.
   Keep `ending_question_ar` as a question for V1; V2 may reuse it when appropriate.
""".strip()

REWRITE_STYLE = """
حافظ على أسلوب الشرح المباشر: واقعة أو مثال محدد، ثم تفسير الآلية وما يضيفه كل جزء.
لا تستبدل التفاصيل بتعميمات أو حكم تحفيزية، ولا تكرر الفكرة بين الصفحات.
حافظ على الأسماء والأرقام والتحفظات والمعنى، ولا تضف حقائق أو أمثلة جديدة لسد عدد الكلمات.
في كل فقرة (لـ V1) أو صفحة (لـ V2)، أحِط عبارتين إلى 3 عبارات رئيسية (كل منها 2 إلى 3 كلمات) بوسوم <hl>...</hl> لتمييزها بنمط قلم التظليل، مع إبقاء حروف العطف والجر المتصلة (و، ف، ب، ل، ك) داخل الوسم دائماً.
يُمنع منعاً باتاً إنهاء الملخص بعبارات توجيهية لصندوق الوصف مثل «المزيد من التفاصيل في صندوق الوصف» أو «اقرأ الوصف».
""".strip()
