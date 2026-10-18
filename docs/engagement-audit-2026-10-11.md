# Capsule Fikr — engagement and production audit

Audit date: 11 October 2026. Prepared from the public channels, the local repository and three bounded video analyses. Production code, settings and live posts were not changed.

## Assessment

The strongest working diagnosis is a mismatch between the way the information is packaged and the effort a scrolling viewer will spend consuming it. The workflow produces substantial summaries, but the video often behaves like a timed reading exercise. Narration introduces the topic and promotes the channel; it does not carry the explanation. Large source metadata, dense text, moving source footage and decorative framing compete for attention.

The research and automation are useful assets. The next investment should be in evidence quality, editorial selection, comprehensible storytelling and measurement. More thumbnail detail or concealment of the editing software is unlikely to resolve these problems.

This is an evidence-based content and pipeline audit, not a confirmed causal diagnosis of distribution. Private impressions, audience retention, account recommendation status, shares, saves and post-attributed follows were unavailable. Public view counts cannot establish a shadowban, audience satisfaction or the reason a particular post performed better.

## Public evidence

| Channel | Observed public state | Interpretation limits |
|---|---|---|
| [YouTube](https://www.youtube.com/@capsulefikr/shorts) | 85 subscribers, 132 videos; About panel showed 36,892 views | Lifetime public totals, not a three-week cohort or unique viewers |
| [Instagram](https://www.instagram.com/capsulefikr/reels/) | 47 followers, 130 posts; first 12 visible Reels ranged from 16 to 545 views | Different post ages; not the whole account or a reach report |
| [Facebook](https://www.facebook.com/profile.php?id=61593697093901) | 30 followers; recent Reels and separate long text/image briefs were visible | Reach, readership, saves and recommendation eligibility unavailable |

YouTube’s About panel says Joined Aug 29, 2026; this is account creation and need not be the date consistent publishing began. Its description still promises 20-second capsules, while inspected videos run approximately 28 or 36–37 seconds. Correct that promise when the format changes.

The latest visible YouTube list included 75 views for «لتحقيق العظمة», 333 for «لماذا تفكر كل الأجيال اللاحقة لنا بشكل أقل؟», 884 for the 1984 discussion, and rounded 1K labels for several posts. The Popular list placed «لماذا يفسر مضيق هرمز سبب بقائك أعزباً؟» first with a rounded 1K label. This establishes that content has been seen, not that it received a particular number of recommendation impressions. It does not prove a 1,000-view ceiling or identify a winning niche.

The newest Facebook Reel was only about three hours old at inspection. Comparing its accumulated views with an older popular video would be misleading.

## Video inspection

The watch skill used the configured Gemini video engine on 00:00–00:45 of each Short; this covers the reported duration of each. The audio/timeline findings below are Gemini observations. I separately inspected the public channel grids and the live opening frame of the first Short, and checked the renderer. Exact word estimates from video analysis are approximate.

| Sample | Observed structure | What to test |
|---|---|---|
| [لتحقيق العظمة](https://www.youtube.com/shorts/58ZT8nHEM24) | Approximately 28s. Text and music during the first 20s; spoken promotion in the final 8s. The opening frame visibly combines a source card, metadata, title/category, a long Arabic paragraph and a blue surround. | Whether replacing timed paragraphs with a narrated single idea improves retention and understanding |
| [لماذا تفكر كل الأجيال اللاحقة لنا بشكل أقل؟](https://www.youtube.com/shorts/2YgTql6XKpw) | Approximately 36–37s. Opening narration around 0–8s reads the title plus «خلاصة الحوار وأبرز أسراره في ثوانٍ». Body around 8–28s is music and text, without explanatory narration. Outro about 28–36s. | Drop at the narration-to-reading transition; benefit of continuous explanatory narration |
| [لماذا يفسر مضيق هرمز سبب بقائك أعزباً؟](https://www.youtube.com/shorts/QtrLNAgtu0k) | Approximately 36s. Spoken introduction, then text-heavy body with music, then spoken promotion. Same basic reading format despite its higher public ranking. | Whether the unexpected, specific premise attracts attention; not evidence that the whole format retains well |

The high-ranked example is a useful counterexample to “this format never works.” A strong topic can get some response within it. We cannot determine which part caused that response without analytics.

## Prioritized findings and fixes

### 1. The video demands too much reading, too quickly — high confidence in the design problem

V1 asks for 70–80 words per 10-second page: 420–480 words per minute, excluding headings, source information and visual interpretation. V2 specifies 30–44 words in 6.5-second pages: approximately 277–406 words per minute. These are arithmetic demands, not asserted Arabic reading-speed norms. Some viewers can pause; a discovery format should not depend on that.

The V2 page splitter can also accept 20–50 words, so the configured 30–44 range is not a reliable final guarantee. A 50-word page in 6.5s demands approximately 462 words per minute.

**Change:** Explain one useful idea per video. Start with roughly 60–85 spoken Arabic words for a 30–40s prototype, then set timing from the actual recording. Use short, synchronized caption phrases of approximately 3–7 words, normally no more than two lines. These are starting design constraints to test, not ranking rules. Keep the full synthesis in the reading product.

Files: [config.py](</F:/Arabic Brief/src/arabic_video_brief/config.py:62>), [editorial.py](</F:/Arabic Brief/src/arabic_video_brief/v2/editorial.py:167>), [renderer.py](</F:/Arabic Brief/src/arabic_video_brief/v2/renderer.py:580>).

### 2. Speech is spent on announcements instead of explanation — high confidence

The opening suffix describes the service rather than delivering insight. The fixed 8-second ending takes 28.6% of a 28-second video or 21.9% of a 36.5-second video. Multiple simultaneous requests—save, share, follow, read and comment—make the next step diffuse.

**Change:** Begin with a specific situation or tension, explain it immediately, and finish with one useful action. If a CTA is needed, use one contextual sentence occupying roughly the final 1–2 seconds, or overlay it while the explanation concludes. Keep the main payoff inside the video. The caption should offer additional depth rather than the answer withheld from the video.

Do not assume silence is inherently bad. A quiet reading format may suit existing readers; test it as a deliberate compact format or carousel, rather than expecting it to serve every discovery viewer.

Files: [editorial.py](</F:/Arabic Brief/src/arabic_video_brief/v2/editorial.py:221>), [renderer.py](</F:/Arabic Brief/src/arabic_video_brief/v2/renderer.py:674>).

### 3. The title rule preserves source marketing instead of adapting the viewer promise — high confidence

The skill requires a literal-equivalent translation of the original title, also used for narration. This confuses faithful attribution with effective packaging. A source title optimized for an established English-language audience, or a long interview, need not work for a short Arabic explanation. The published «امنحني 47 دقيقة…» is an obvious duration mismatch for a capsule.

**Change:** Separate `source_title_original`, `source_title_ar`, `publication_title_ar` and `hook_ar`. Preserve the original title and link in attribution. Allow a concise, accurate Arabic hook for the particular idea covered. No invented claims, exaggerated certainty or fabricated quotes. A good rewrite narrows the promise to what the Short actually delivers.

Example based on the greatness topic: replace a generic «لتحقيق العظمة» discovery hook with «تتدرّب كثيراً ولا تتحسّن؟» only when the chosen passage actually supports the deliberate-practice idea. Cover text could be «لماذا لا تتحسّن؟» rather than the entire source title.

The publisher also truncates long YouTube titles to reserve space for `#Shorts`. A visible AI-related title ends at «احتمال الانقراض», losing the remainder of the promise. Generate a complete short title before formatting, instead of slicing prose at the limit.

Files: [skill](</F:/Arabic Brief/.agents/skills/arabic-video-brief/SKILL.md>), [editorial.py](</F:/Arabic Brief/src/arabic_video_brief/v2/editorial.py:285>), [formatter.py](</F:/Arabic Brief/src/arabic_video_brief/publisher/formatter.py:97>).

### 4. Covers look more dramatic than the reading experience they lead into — observed mismatch; impact is a hypothesis

The visible covers include cinematic figures, large expressive faces and dramatic environments. The actual opening often changes to a much smaller source clip above a paragraph. A viewer attracted by a visual story receives a text card instead.

Calling an image “high CTR” in its generation prompt does not establish its click-through rate. And a thumbnail click is not the same decision as staying on an autoplaying Short. YouTube documents chose-to-view, view duration and percentage viewed as Shorts performance signals. [YouTube Shorts discovery guidance](https://support.google.com/youtube/answer/11914225?co=YOUTUBE._YTVideoType%3Dshorts&hl=en).

**Change:** Match the cover’s promise with the opening spoken line and first visual. Reduce cover copy to one readable phrase. Put the explanatory example or visual demonstration in the main area. Use a small source credit; move full source title, upload date and source view count into the caption. Retain readable branding without giving it the same visual weight as the lesson.

### 5. The blue frame still reduces the content area — confirmed implementation

When the frame asset exists, the renderer scales the composition to 972×1728 and places it at (54,96) inside 1080×1920. This is 90% of the linear dimensions and 81% of the canvas area before the decorative overlay. The blur has not made the content full-screen; it surrounds a smaller composition.

**Change:** Remove the decorative inset in the experimental format and use the canvas for the explanation. Keep platform-safe caption placement and validate it on a real phone. Cosmetic blending does not demonstrate originality or guarantee recommendation eligibility.

File: [renderer.py](</F:/Arabic Brief/src/arabic_video_brief/v2/renderer.py:608>).

### 6. Original contribution needs to be visible in the video — material risk, not a confirmed penalty

Arabic synthesis adds value, but a repeating template over third-party clips can still look like an aggregation account. The viewer should recognize Capsule Fikr’s interpretation, example, comparison or demonstration as the main product.

Facebook’s current guidance distinguishes meaningful original analysis from minor changes such as borders and captions, and says low-value reuse may be deprioritized. That does **not** prove your accounts have been restricted. [Meta’s originality guidance](https://about.fb.com/news/2026/03/rewarding-original-creators-on-facebook/).

**Change:** Make the video an original Arabic explanation, supported by selective source evidence. Use your own recorded demonstration, original diagrams or explicitly illustrative scenes. If comfortable, test your own on-camera explanation; it is an option, not a requirement or guarantee. For a faceless format, make the analysis and illustrative visuals yours rather than continuously displaying another person talking silently.

### 7. Broad topics weaken the reason to follow — working hypothesis

The visible catalogue jumps among relationships, philosophy, religion, economics, AI, literature, motivation and psychology. There is no automatic penalty for breadth. The human problem is that enjoying one item may not tell someone what useful experience they will get next.

“All” is a reasonable set of business goals—reach, followers and deeper reading—but is too broad as a starting audience definition.

**Change:** For the experiment, choose one recurring audience need. A plausible starting hypothesis is Arabic-speaking students and early-career adults seeking practical help with attention, habits and decisions. Validate this against actual audience data. Publish adjacent episodes that reward following: distraction → starting difficult work → choosing priorities → noticing a bad decision.

Suggested promise: «فكرة واضحة تساعدك على فهم نفسك واتخاذ قرار أفضل. شرح قصير، ومصدر، وخطوة عملية.» Keep psychology claims qualified and avoid diagnosis-by-personality-title content.

Pin an introduction to this promise, a representative explanation and a useful reading resource. Organize series around the viewer’s problem rather than only the source celebrity.

### 8. Source fidelity has concrete failure paths — fix before scaling

These are code findings, not proof that particular published briefs are inaccurate. The actual effect depends on the provider, available captions and any manually supplied analysis.

| Finding | Evidence | Required correction |
|---|---|---|
| VyceAI receives only the first 300 transcript characters; its next fallback drops the transcript entirely | [vyceai.py](</F:/Arabic Brief/src/arabic_video_brief/vyceai.py:220>) | Ingest the source transcript in timestamped chunks; synthesize from complete coverage rather than a title/description or prefix |
| Gemini can fall back from video access to a text context that exists even when captions are missing | [gemini.py](</F:/Arabic Brief/src/arabic_video_brief/gemini.py:197>) | Refuse to label a result a full-video summary without verified coverage; explicitly mark partial evidence |
| Downloaded visual material starts at zero, and V2’s selected clip also starts at zero | [media.py](</F:/Arabic Brief/src/arabic_video_brief/media.py:101>), [v2/pipeline.py](</F:/Arabic Brief/src/arabic_video_brief/v2/pipeline.py:179>) | Select evidence-bearing moments from actual timestamps; do not assume an opening montage illustrates a later takeaway |
| V2 writes `metadata.get("transcript") or []`, while the downloader supplies `transcript_text` | [v2/pipeline.py](</F:/Arabic Brief/src/arabic_video_brief/v2/pipeline.py:262>) | Store the original transcript, timestamps, language and source identity consistently |
| Deep-dive generation can receive the model-generated `analysis.transcript`, which the base prompt requests as compact segments | [v2/pipeline.py](</F:/Arabic Brief/src/arabic_video_brief/v2/pipeline.py:300>) | Feed the original complete transcript into the deep-dive stage; distinguish extracted captions from model summaries |
| A fallback selects the first `*transcript*.txt` found in parent directories, without matching source identity | [deepdive.py](</F:/Arabic Brief/src/arabic_video_brief/deepdive.py:361>) | Require an exact source/video-ID match; fail rather than risk borrowing another item’s transcript |
| Both custom and default hooks receive a fixed score of 100 | [editorial.py](</F:/Arabic Brief/src/arabic_video_brief/v2/editorial.py:342>) | Remove the misleading score or label it unevaluated; distinguish an editorial rubric from measured audience results |

Store source passage/time for each substantial claim. Label speaker opinion, supporting study and creator illustration separately. A famous speaker or polished English term is not independent evidence. Titles attributing broad contemporary advice to Carl Jung require a verifiable primary passage or honest wording such as an interpretation of his ideas; attribution in the source title alone is insufficient.

### 9. The deep brief has a difficult entrance — directly inspected

The [Facebook post on thinking and later generations](https://www.facebook.com/permalink.php?story_fbid=pfbid02KQBHQ1r8giXHaRfCCFBKNXsXt1pr1MAsRcDZ7qx84bQGwJjmLUCEELSyG9qh7gcYl&id=61593697093901) opens with a long bilingual title, then two abstract introductory paragraphs before its first thematic heading. It repeatedly adds English phrases in parentheses and speaks with broad certainty about cognition, intelligence and technology. The visible post showed one share at inspection; its readership is unknown.

This follows a prompt that demands an authoritative, exhaustive essay with a long introduction. Length is not itself a defect; requiring every brief to use this register delays the practical value. Some scientific-sounding claims require more qualification and evidence than the post displays. I did not independently fact-check the full source video, so I am not labeling individual statements false.

**Change:** Start with the reader’s specific problem and the useful distinction in the first two lines. Then provide a short “what you will get” summary, clear thematic sections, concrete examples and one realistic experiment. Keep necessary technical terms; remove decorative translations. Provide the original source link, relevant time, and a short boundary on what the source does and does not establish. Allow lists when they make steps easier to use.

Suggested editorial opening, not a verified scientific claim: «تقرأ كثيراً، لكن هل تستطيع شرح ما قرأت بكلماتك؟ يطرح هذا المقطع سؤالاً عن الفرق بين استهلاك المعلومات والعمل عليها. إليك الفكرة، وحدودها، وتجربة صغيرة لتختبرها بنفسك.»

Preserve an optional full essay for interested readers, but create a concise companion post or carousel rather than forcing everyone into the exhaustive version. Generic questions about one’s entire life demand more effort than a specific question such as «ما آخر فكرة غيّرت رأيك فيها؟».

### 10. Detection workarounds are distracting from measurable improvements

The repository claims that `brief.mp4` filenames flag automation, labels FFmpeg output as CapCut, varies audio tempo to randomize its fingerprint, and describes automated account warmup as guaranteeing trust. I found no substantiation for those growth guarantees. They are not a substitute for audience response or platform eligibility checks.

**Change:** Use honest, predictable export metadata and filenames. Stop treating randomized tempo, cosmetic blur or account browsing as growth levers. The observed YouTube sound attribution identified Vangelis in the latest sample, so acoustic changes should not be assumed to make a soundtrack unrecognizable.

Inspect actual restrictions in Studio and the relevant account dashboards. A music credit on a public video is not proof of a copyright claim, restriction or reduced reach. The pipeline uses named commercial recordings; verify the rights for each destination or use an appropriate licensed track. YouTube distinguishes music added through its own Shorts tools from externally embedded music, which may receive standard claims. [YouTube music guidance](https://support.google.com/youtube/answer/13053317?hl=en).

Files: [formatter.py](</F:/Arabic Brief/src/arabic_video_brief/publisher/formatter.py:41>), [renderer.py](</F:/Arabic Brief/src/arabic_video_brief/v2/renderer.py:643>), [brand roadmap](</F:/Arabic Brief/docs/brand_and_channels_roadmap.md>).

## Proposed V3 using the existing tools

Build an experimental mode; keep existing exports available for comparison. No new paid visual tool is required to test the main hypothesis.

1. **Evidence:** existing caption extraction or video analysis, with complete coverage, timestamp preservation and explicit failure when evidence is insufficient.
2. **Editorial selection:** choose one audience problem and one defensible takeaway. Generate a few faithful hooks; human-select one. Store a concrete example, takeaway and source passage.
3. **Script:** roughly 60–85 Arabic words as a starting budget, including the hook. Deliver a complete explanation before an optional single CTA.
4. **Narration:** extend existing ElevenLabs support to the entire explanation. Use one tested Arabic voice consistently during the experiment; the current implementation randomly chooses from a voice pool. Time the output rather than estimating audio duration from word count alone.
5. **Captions:** export an SRT/ASS or equivalent cue file from the actual narration. Existing FFmpeg plus the project’s Arabic text rendering can compose synchronized phrases. Add forced alignment only if manual/segment timing becomes a bottleneck; verify that any selected tool handles Arabic accurately before adopting it.
6. **Visuals:** existing Pillow/FFmpeg for simple original diagrams, examples and emphasis. Use the current image tool only where a custom illustration explains the idea. Avoid adding generic AI footage merely to increase motion.
7. **Audio:** keep music below speech, judge intelligibility on a phone, and check clipping/true peaks. Use measured loudness, not fixed volume multipliers as proof of a balanced mix.
8. **Packaging:** separate cover headline, publication title, source title, short caption and optional deep brief. Write destination-specific next steps instead of a universal “look below” arrow.
9. **Measurement:** keep a local experiment log from native analytics exports or manual entry. Add authenticated analytics APIs only if repeated manual collection becomes expensive. No new connector is needed for the first test.

Suggested manifest fields: `source_video_id`, `transcript_origin`, `coverage`, `claim_evidence`, `audience_problem`, `series`, `format_version`, `experiment_id`, `hook_variant`, `script_ar`, `narration_duration`, `caption_cues`, `visual_plan`, `source_credit`, `cta`, `published_url`.

Quality gates: comprehension without opening the caption; captions work muted; speech alone conveys the core idea; no cropped Arabic glyphs; actual timing matches speech; no unverified study/quotation; source passage supports the takeaway; one clear next action; no unexplained switch of voice; phone-size review before publishing.

### Concrete 30–35-second prototype

This is a proposed editorial adaptation of the practice idea present in your published greatness caption. Verify it against the original source before production. The scenario is an illustrative example, not a claimed quotation or study result.

| Approximate time | Narration | Visual/caption focus |
|---|---|---|
| 0–3s | «تتدرّب كثيراً ولا تتحسّن؟ انظر إلى ما تتجنّبه.» | One task with its difficult part marked; caption «ما الذي تتجنّبه؟» |
| 3–11s | «قد تكرّر الجزء الذي تتقنه لأنه يمنحك شعوراً بالإنجاز، بينما تترك الجزء الصعب كما هو.» | Same easy section repeated; then highlight the untouched difficult section |
| 11–21s | «مثلاً، تعيد عزف المقطع السهل، وتؤجّل الانتقال الذي تخطئ فيه كل مرة. هنا تصبح الممارسة إعادةً لما تعرفه.» | Simple original sequence: easy bars → difficult transition |
| 21–30s | «في تدريبك المقبل، اختر خطأً واحداً، وأبطئ الحركة، واطلب ملاحظة محدّدة، ثم أعد المحاولة. قارن أداءك في هذا الجزء قبل التدريب وبعده.» | One error → slow attempt → feedback → retry |
| 30–33s | «ما الجزء الذي ستتدرّب عليه؟» | Final practical question and small source credit |

Measure the actual recording and adjust duration naturally. Do not speed up the voice just to fit this sketch. If using a save CTA instead of the question, use only that CTA. Suggested cover: «لماذا لا تتحسّن؟». The caption can explain limits, give another example and link the source.

## Platform-specific role

| Platform | Discovery product | Deeper product | Main measurement |
|---|---|---|---|
| YouTube | A complete narrated Short, clear opening and source in description | Organized series/playlists; fuller explanation later if demand supports it | Stayed to watch, engaged views, average view duration/percentage, retention and attributed subscribers |
| Instagram | A readable, self-contained Reel with consistent editorial voice | Companion carousel for the strongest useful frameworks | Reach, watch time where available, shares and saves per reach, attributed follows/profile activity |
| Facebook | Original explanatory Reel with a specific practical takeaway | Standalone readable text/image brief, with the useful idea in its opening lines | Reach/watch behavior for Reels; meaningful responses/shares and available post activity for text |

Keep metric definitions distinct. YouTube’s average percentage viewed and average view duration for Shorts concern those who stayed to watch; they do not replace the swipe-away measure. [Official metric definitions](https://support.google.com/youtube/answer/12220281?hl=en).

Do not interpret saves as confirmed reading. If caption opens or read time are unavailable, say readership is unmeasured. A later optional web archive could measure actual visits and reading proxies, but building one is unnecessary before validating the content.

Instagram Trial Reels can be useful if the option is available on this account; they expose experiments to non-followers first. They are not a controlled randomized A/B test or a promised reach boost. [Meta Trial Reels explanation](https://about.fb.com/news/2024/12/trial-reels-try-content-non-followers-first-see-what-perfoms-best/).

## Two-week experiment

**Before the run:** obtain the last 20 comparable posts’ analytics, with post dates, duration and format version. Check actual recommendation/restriction notices once. Repair the evidence paths before generating more “full” summaries. Choose one audience problem and one narrator, music bed and visual system. Preserve existing posts; do not mass-delete or repost identical clips.

**Cadence:** one considered discovery post per day is a sustainable test schedule, not an algorithm requirement. Daily uploading is not a guarantee of growth; YouTube explicitly says there is no minimum posting cadence required for performance. [YouTube guidance](https://support.google.com/youtube/answer/11914225?co=YOUTUBE._YTVideoType%3Dshorts&hl=en).

**Design:** use seven matched topic pairs, with one topic-specific post per day. Within each pair, randomly assign one to a compact reading format (A) and one to the continuously narrated version (B). Both should have the same one-idea scope, similar length, clear hook, short captions, source quality and single brief CTA. Keep covers, posting window and editorial standard comparable. Do not compare dense V1 to completely redesigned V3 and claim the voice alone caused the difference.

Topics should be adjacent, not duplicate uploads: practicing a weak point / getting useful feedback; starting a task / reducing an unnecessary step; choosing a priority / saying no to a competing task. Every claim still needs source support. This is a directional matched-topic experiment, not laboratory causal evidence: topic strength, exposure and changing viewers remain confounders.

**Record at the same age:** 24 hours, 72 hours and 7 days after each post. Final seven-day comparison therefore occurs after the two-week publishing run. Do not force daily winners from the latest raw view count.

**Primary question:** does explanatory narration improve viewing of the main idea? On YouTube, inspect stayed-to-watch and average view duration/percentage together, then the actual retention curve if available. On Meta, use available hold/watch metrics. Compare seconds watched as well as percentages when durations differ.

**Secondary question:** is the explanation worth returning to or sharing? Compare shares and saves per 1,000 reached accounts on Meta, and subscribers gained per 1,000 engaged views on YouTube. Record denominators and do not substitute unavailable metrics with zero. Use follows per reach on Meta when attributed follows are available. Do not combine different platform denominators into one engagement score.

**Decision:** look for a repeatable improvement across most matched pairs and the per-format median, without a decline in useful-action rates. A provisional “wins in at least five of seven pairs” rule can organize the decision, but it is a practical heuristic, not a significance test. A handful of shares or tiny exposure makes the result inconclusive; extend the test rather than declare failure. Inspect examples as well as numbers.

After the format test, change one question at a time: audience/series, then hook, then length or CTA. Do not add several new tools, styles and voices during the same comparison.

## How to interpret the missing analytics

| Observed private pattern | Leading explanation to test | Next action |
|---|---|---|
| Very little exposure | Eligibility, audience demand, competition or immature distribution | Check actual notices and traffic sources; do not presume a shadowban |
| Exposure but viewers swipe immediately | Opening relevance or unclear visual/voice promise | Rewrite the first line and simplify the first frame |
| Viewers stay initially but leave when narration stops | Reading burden or broken delivery expectation | Narrate the explanation; simplify text |
| Strong middle, sharp decline at CTA | Ending is too long or adds no value | Remove the 8-second promotional block |
| Good watch behavior, few shares/saves | Idea is interesting but not practically or socially useful | Add a concrete example, decision rule or reference-worthy explanation |
| Good engagement, few follows | Unclear recurring promise or profile mismatch | Build coherent series and align bio/pinned posts |
| Video response but no evidence of deep reading | Too much friction or no measurement | Make the next step specific; give the brief a clear independent opening |

Consistency has already built a substantial publishing sample and reusable tooling. It has not yet produced a clean learning loop. The useful next step is a smaller, more comprehensible product and a disciplined test, rather than another cosmetic layer or a promise that more posting will eventually work.
