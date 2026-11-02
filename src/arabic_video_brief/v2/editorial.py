from __future__ import annotations

import json
import logging
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import Settings
from ..utils import word_count
from ..editorial_style import REWRITE_STYLE

logger = logging.getLogger(__name__)


@dataclass
class HookCandidate:
    display_hook: str
    highlight_phrase: str
    tts_text: str
    category: str
    scores: dict[str, float]
    total_score: float
    explanation: str


@dataclass
class V2EditorialPackage:
    post_title_ar: str
    summary_ar: str
    pages: list[str]  # Exactly 5 pages
    hook: HookCandidate
    conclusion_ar: str
    conclusion_highlights: list[str]
    cta_ar: str
    cta_description: str
    creative_plan: dict[str, Any]


def call_llm(
    prompt: str,
    settings: Settings,
    system_prompt: str = "You are an expert Arabic video editor and copywriter. Return strictly valid JSON.",
    temperature: float = 0.4,
) -> str:
    """Universal LLM caller routing to the configured provider (vyceai, seekai, gemini)."""
    provider = settings.llm_provider
    if provider == "apinex":
        try:
            from ..apinex import _call_apinex_api, _clean_json_text
            raw = _call_apinex_api(
                settings.apinex_base_url,
                settings.apinex_api_key or "",
                settings.apinex_model,
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            return _clean_json_text(raw)
        except Exception as err:
            logger.warning("APInex call_llm failed (%s); falling back to Gemini.", err)
    elif provider == "vyceai":
        try:
            from ..vyceai import _call_vyceai_api, _clean_json_text
            raw = _call_vyceai_api(
                settings.vyceai_base_url,
                settings.vyceai_api_key or "",
                settings.vyceai_model,
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            return _clean_json_text(raw)
        except Exception as err:
            logger.warning("VyceAI call_llm failed (%s); falling back to Gemini.", err)
    elif provider == "seekai":
        try:
            from ..seekai import _call_seekai_api, _clean_json_text
            raw = _call_seekai_api(
                settings.seekai_base_url,
                settings.seekai_api_key or "",
                settings.seekai_model,
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            return _clean_json_text(raw)
        except Exception as err:
            logger.warning("SeekAI call_llm failed (%s); falling back to Gemini.", err)

    # Fallback to Gemini with retries and fallback models
    import time
    from urllib.error import HTTPError, URLError

    candidate_models = [settings.gemini_model]
    for fallback in ("gemini-3-flash-preview", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.8-flash"):
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error: Exception | None = None
    for model_name in candidate_models:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}],
            "generationConfig": {"temperature": temperature},
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except HTTPError as err:
                last_error = err
                if err.code in (429, 500, 502, 503, 504):
                    logger.warning("Gemini model %s returned HTTP %s on attempt %d; retrying...", model_name, err.code, attempt + 1)
                    time.sleep(2 * (attempt + 1))
                    continue
                break
            except (URLError, TimeoutError) as err:
                last_error = err
                logger.warning("Gemini model %s network error on attempt %d (%s); retrying...", model_name, attempt + 1, err)
                time.sleep(2 * (attempt + 1))
                continue
            except Exception as err:
                last_error = err
                break
    if last_error:
        raise last_error
    raise RuntimeError("All Gemini candidate models failed to produce content")


def split_half_into_two_pages(half_text: str, half_index: int, settings: Settings) -> list[str]:
    """
    Splits a ~70-80 word semantic half into two balanced pages (~35-40 words each)
    strictly respecting sentence boundaries (never splitting mid-sentence).
    """
    clean_text = half_text.strip()
    # Sentence splitting regex (Arabic/English full stops, exclamation marks, question marks, semicolons)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?؟؛])\s+", clean_text) if s.strip()]

    if len(sentences) >= 2:
        # Evaluate all possible split points
        best_split_idx = 1
        best_diff = 9999
        total_words = word_count(clean_text)
        target_per_page = total_words / 2.0

        for i in range(1, len(sentences)):
            p1 = " ".join(sentences[:i])
            p2 = " ".join(sentences[i:])
            w1 = word_count(p1)
            w2 = word_count(p2)
            diff = abs(w1 - target_per_page) + abs(w2 - target_per_page)
            if diff < best_diff:
                best_diff = diff
                best_split_idx = i

        page_a = " ".join(sentences[:best_split_idx]).strip()
        page_b = " ".join(sentences[best_split_idx:]).strip()

        # If both pages are between 20 and 50 words, sentence split is preserved verbatim!
        if 20 <= word_count(page_a) <= 50 and 20 <= word_count(page_b) <= 50:
            # Ensure sentence endings
            if not re.search(r"[.!?؟؛]$", page_a):
                page_a += "."
            if not re.search(r"[.!?؟؛]$", page_b):
                page_b += "."
            return [page_a, page_b]

    prompt = f"""
أعد تقسيم وصياغة الفقرة العربية التالية إلى صفحتين متوازنتين من حيث الطول والمعنى (بين 30 و 45 كلمة لكل صفحة).
القواعد الصارمة:
{REWRITE_STYLE}
1. الأمانة التامة للنص الأصلي: يمنع منعاً باتاً إضافة أي نصائح خارجية، أو اختراع روتين صباحي أو مسائي، أو ذكر عادات نوم أو أي معلومات غير موجودة في النص الأصلي. التزم بدقة بنقل نفس الأفكار والحقائق الواردة في النص دون زيادة أو نقصان.
2. يمنع قطع الجملة بين الصفحتين. كل صفحة يجب أن تبدأ بجملة مستقلة المعنى وتنتهي بنقطة تامة.
3. لا تستخدم نقاطاً نقطية أو عناوين.
4. قم بتمييز عبارتين أو ثلاث عبارات رئيسية في كل صفحة (كل عبارة تتكون من كلمتين إلى 3 كلمات) عبر إحاطتها بوسوم <hl>...</hl> (مثال: <hl>وكيمياء عصبية تختفي</hl>).
قاعدة حاسمة للغة العربية: أبقِ دائماً حروف العطف والجر المتصلة (و، ف، ب، ل، ك) داخل وسم <hl> (مثل <hl>وكيمياء عصبية</hl> وليس و<hl>كيمياء عصبية</hl>).

النص الأصلي:
{clean_text}

أعد الناتج بصيغة JSON فقط:
{{
  "page_a": "نص الصفحة الأولى (30-45 كلمة تنتهي بنقطة مع 2-3 عبارات داخل وسوم <hl>...</hl>)",
  "page_b": "نص الصفحة الثانية (30-45 كلمة تنتهي بنقطة مع 2-3 عبارات داخل وسوم <hl>...</hl>)"
}}
""".strip()

    try:
        res = call_llm(prompt, settings, temperature=0.2)
        match = re.search(r"(\{.*\})", res, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            pa = str(data.get("page_a", "")).strip()
            pb = str(data.get("page_b", "")).strip()
            if pa and pb and word_count(re.sub(r"</?hl>", "", pa)) >= 20 and word_count(re.sub(r"</?hl>", "", pb)) >= 20:
                if not re.search(r"[.!?؟؛]$", pa):
                    pa += "."
                if not re.search(r"[.!?؟؛]$", pb):
                    pb += "."
                return [pa, pb]
    except Exception as err:
        logger.warning("LLM page rebalancing fallback failed: %s; falling back to rough split", err)

    # Fallback to midpoint word split with period if LLM failed
    words = clean_text.split()
    mid = len(words) // 2
    pa = " ".join(words[:mid]).strip()
    pb = " ".join(words[mid:]).strip()
    if not re.search(r"[.!?؟؛]$", pa):
        pa += "."
    if not re.search(r"[.!?؟؛]$", pb):
        pb += "."
    return [pa, pb]


def split_text_into_five_pages(text: str, settings: Settings) -> list[str]:
    """
    Splits or formats text into 5 balanced pages (~30-40 words each)
    following the 5-beat arc. If LLM is available, uses LLM to rebalance.
    Otherwise, uses deterministic sentence grouping into 5 pages.
    """
    clean_text = text.strip()
    if not clean_text:
        return ["."] * 5

    paragraphs = [p.strip() for p in clean_text.split("\n") if p.strip()]
    if len(paragraphs) == 5:
        return paragraphs

    if settings.gemini_api_key or settings.vyceai_api_key or settings.seekai_api_key or settings.apinex_api_key:
        prompt = f"""
أعد صياغة وتقسيم النص العربي التالي إلى 5 صفحات متسلسلة ومتوازنة (بين 30 و 40 كلمة لكل صفحة، بإجمالي 160–180 كلمة).
القواعد الصارمة:
{REWRITE_STYLE}
1. البنية القصصية والتفسيرية المحددة للصفحات الخمس:
   - الصفحة 1 (المدخل والورطة): فخ يومي، معضلة مألوفة، أو مدخل بديهي يجذب المشاهد فوراً.
   - الصفحة 2 (الشاهد الحقيقي والركيزة الملموسة): اقتباس حقيقي مباشر، قصة/موقف شخصي من المتحدث، تجربة علمية محددة بأرقامها، أو مفارقة حادة من صلب النص. ممنوع الكلام النظري العام هنا.
   - الصفحة 3 (الآلية العميقة والتفسير): شرح كيف ولماذا تحدث الظاهرة بكلمات دقيقة وواضحة.
   - الصفحة 4 (الأثر والتعميق والتكلفة الخفية): توسيع أثر الفكرة أو ما يحدث عند تجاهلها أو إطار لفهمها.
   - الصفحة 5 (التحول العملي والحل): قاعدة سلوكية قابلة للتطبيق اليومي أو خطوة ملموسة في الحياة الواقعية.
2. الأمانة التامة للنص الأصلي: يُمنع منعاً باتاً اختراع دراسات أو قصص أو تفاصيل غير موجودة. استخرج الشاهد الملموس من صلب النص.
3. يمنع قطع الجملة بين الصفحات. كل صفحة يجب أن تبدأ بجملة مستقلة وتنتهي بنقطة تامة.
4. في كل صفحة، أحِط عبارتين إلى 3 عبارات رئيسية (كل منها 2 إلى 3 كلمات) بوسوم <hl>...</hl> لتمييزها بنمط قلم التظليل، مع إبقاء حروف العطف والجر المتصلة (و، ف، ب، ل، ك) داخل الوسم دائماً.
5. يُمنع منعاً باتاً أي توجيه لصندوق الوصف (مثل 'التفاصيل في الوصف').

النص الأصلي:
{clean_text}

أعد الناتج بصيغة JSON فقط:
{{
  "pages": [
    "نص الصفحة الأولى",
    "نص الصفحة الثانية",
    "نص الصفحة الثالثة",
    "نص الصفحة الرابعة",
    "نص الصفحة الخامسة"
  ]
}}
""".strip()
        try:
            res = call_llm(prompt, settings, temperature=0.2)
            match = re.search(r"(\{.*\})", res, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                candidate_pages = data.get("pages")
                if isinstance(candidate_pages, list) and len(candidate_pages) == 5:
                    cleaned_candidates = [str(p).strip() for p in candidate_pages]
                    if all(word_count(re.sub(r"</?hl>", "", p)) >= 15 for p in cleaned_candidates):
                        for idx, p in enumerate(cleaned_candidates):
                            if not re.search(r"[.!?؟؛]$", p):
                                cleaned_candidates[idx] = p + "."
                        return cleaned_candidates
        except Exception as err:
            logger.warning("LLM 5-page rebalancing failed: %s; using deterministic fallback", err)

    sentences = [s.strip() for s in re.split(r"(?<=[.!?؟؛])\s+", clean_text) if s.strip()]
    if len(sentences) >= 5:
        pages: list[list[str]] = [[] for _ in range(5)]
        total_words = word_count(clean_text)
        target = max(1, total_words / 5.0)
        curr_bucket = 0
        curr_words = 0
        for sent in sentences:
            sw = word_count(sent)
            if curr_bucket < 4 and len(pages[curr_bucket]) > 0 and (curr_words + sw > target * 1.15):
                curr_bucket += 1
                curr_words = 0
            pages[curr_bucket].append(sent)
            curr_words += sw

        result = [" ".join(p).strip() for p in pages]
        for i in range(5):
            if not result[i]:
                result[i] = "نقطة إضافية."
            if not re.search(r"[.!?؟؛]$", result[i]):
                result[i] += "."
        return result

    words = clean_text.split()
    n = len(words)
    chunk_size = max(1, n // 5)
    result = []
    for i in range(5):
        if i == 4:
            chunk = words[i * chunk_size:]
        else:
            chunk = words[i * chunk_size:(i + 1) * chunk_size]
        text_chunk = " ".join(chunk).strip() or "نقطة توضيحية."
        if not re.search(r"[.!?؟؛]$", text_chunk):
            text_chunk += "."
        result.append(text_chunk)
    return result


VOICEOVER_SUFFIX = "ملخص الفكرة في ثوانٍ، والتفاصيل الكاملة في صندوق الوصف"


def generate_v2_conclusion_and_cta(
    metadata: dict[str, Any],
    summary_ar: str,
    five_pages: list[str],
    settings: Settings,
) -> tuple[str, list[str], str, str]:
    """Compatibility entry point: the former conclusion is now a question."""
    from ..ending import resolve_ending_question
    question = resolve_ending_question({}, metadata, summary_ar or ' '.join(five_pages), settings)
    return question, [], "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد", "السر الأهم والخطوات التطبيقية في الوصف بالأسفل 👇"


def build_v2_editorial_package(
    base_analysis: dict[str, Any],
    metadata: dict[str, Any],
    settings: Settings,
) -> V2EditorialPackage:
    """
    Main entry point for V2 editorial production.
    Takes the base 140-160 word summary, splits into 5 complete-sentence pages,
    preserves the title + suffix voiceover, and resolves the ending question & CTA.
    """
    orig_title = str(metadata.get("original_title") or "").strip()
    raw_title = str(metadata.get("title") or "").strip()
    target_orig_ar = orig_title if re.search(r"[\u0600-\u06FF]", orig_title) else (raw_title if re.search(r"[\u0600-\u06FF]", raw_title) else "")

    # Rule: If the YouTube video is originally titled in Arabic, ALWAYS preserve it verbatim!
    if target_orig_ar:
        clean_ar = re.sub(r"#\b(?:shorts?|يوتيوب_عربي)\b", "", target_orig_ar, flags=re.IGNORECASE).strip()
        clean_ar = re.sub(r"^(?:(?:\d+|#\d+)[\.\-:\s]+|(?:الحلقة|حلقة|episode|ep)[\.\-:\s]*\d+[\.\-:\s]*)", "", clean_ar, flags=re.IGNORECASE).strip()
        post_title_ar = clean_ar
    elif base_analysis.get("post_title_ar"):
        post_title_ar = str(base_analysis["post_title_ar"]).strip()
    elif base_analysis.get("post_title"):
        post_title_ar = str(base_analysis["post_title"]).strip()
    elif base_analysis.get("title") and re.search(r"[\u0600-\u06FF]", str(base_analysis.get("title"))):
        post_title_ar = str(base_analysis["title"]).strip()
    else:
        post_title_ar = raw_title
    summary_ar = base_analysis.get("summary_ar", "").strip().replace("{", "").replace("}", "")

    # If pages are already pre-computed in base_analysis (e.g. Brainstorm mode or LLM analysis), use them directly
    if base_analysis.get("pages") and len(base_analysis["pages"]) == 5:
        raw_pages = list(base_analysis["pages"])
        five_pages = [
            str(p.get("text", "") if isinstance(p, dict) else p).strip().replace("{", "").replace("}", "")
            for p in raw_pages
        ]
        summary_ar = re.sub(r"</?hl>", "", "\n\n".join(five_pages))
    elif base_analysis.get("pages") and len(base_analysis["pages"]) == 4:
        raw_pages = [
            str(p.get("text", "") if isinstance(p, dict) else p).strip().replace("{", "").replace("}", "")
            for p in base_analysis["pages"]
        ]
        lens = [len(p.split()) for p in raw_pages]
        max_idx = lens.index(max(lens))
        longest = raw_pages[max_idx]
        sents = [s.strip() for s in re.split(r"(?<=[.!?؟؛])\s+", longest) if s.strip()]
        if len(sents) >= 2:
            mid = len(sents) // 2
            p_a = " ".join(sents[:mid]).strip()
            p_b = " ".join(sents[mid:]).strip()
        elif len(longest.split()) >= 2:
            words = longest.split()
            mid = len(words) // 2
            p_a = " ".join(words[:mid]).strip()
            p_b = " ".join(words[mid:]).strip()
        else:
            p_a = longest
            p_b = longest
        if not re.search(r"[.!?؟؛]$", p_a): p_a += "."
        if not re.search(r"[.!?؟؛]$", p_b): p_b += "."
        five_pages = raw_pages[:max_idx] + [p_a, p_b] + raw_pages[max_idx + 1:]
        summary_ar = re.sub(r"</?hl>", "", "\n\n".join(five_pages))
    else:
        five_pages = split_text_into_five_pages(summary_ar, settings)
        summary_ar = re.sub(r"</?hl>", "", "\n\n".join(five_pages))

    # Voiceover: translated title + description-directed suffix; visual content is unchanged.
    clean_title_for_tts = re.sub(r"[.!؟?\-_|]+$", "", post_title_ar).strip()
    voiceover_tts = f"{clean_title_for_tts}... {VOICEOVER_SUFFIX}."

    if base_analysis.get("hook") and isinstance(base_analysis["hook"], dict):
        hook_dict = base_analysis["hook"]
        hook = HookCandidate(
            display_hook=str(hook_dict.get("display") or clean_title_for_tts).strip(),
            highlight_phrase=str(hook_dict.get("highlight") or VOICEOVER_SUFFIX).strip(),
            tts_text=voiceover_tts,
            category=str(hook_dict.get("category") or "صوت افتتاحي").strip(),
            scores={"relevance": 10.0},
            total_score=100.0,
            explanation="Pre-computed custom hook",
        )
        voiceover_tts = hook.tts_text
        clean_title_for_tts = hook.display_hook
    else:
        hook = HookCandidate(
            display_hook=clean_title_for_tts,
            highlight_phrase=VOICEOVER_SUFFIX,
            tts_text=voiceover_tts,
            category="صوت افتتاحي",
            scores={"relevance": 10.0},
            total_score=100.0,
            explanation="Direct title + Option 3 voiceover hook",
        )

    from ..ending import resolve_v2_footer
    conclusion = resolve_v2_footer(base_analysis, metadata, ' '.join(five_pages), settings)
    conclusion_hl = [conclusion]
    legacy = base_analysis.get("conclusion")
    cta_fields = legacy if isinstance(legacy, dict) else base_analysis
    cta_save = str(cta_fields.get("cta_save") or "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد")
    cta_desc = str(cta_fields.get("cta_description") or "السر الأهم والخطوات التطبيقية في الوصف بالأسفل 👇")

    creative_plan = {
        "version": "v2",
        "ending_text_ar": conclusion,
        "ending_question_ar": conclusion,
        "thumbnail_hook_ar": base_analysis.get("thumbnail_hook_ar", ""),
        "voiceover": {
            "tts_text": voiceover_tts,
            "title_ar": clean_title_for_tts,
            "suffix": VOICEOVER_SUFFIX,
        },
        "pages": [
            {"page": i + 1, "words": word_count(re.sub(r"</?hl>", "", p)), "text": p}
            for i, p in enumerate(five_pages)
        ],
        "conclusion": {
            "text": conclusion,
            "highlights": conclusion_hl,
            "cta_save": cta_save,
            "cta_description": cta_desc,
        },
    }

    if base_analysis.get("thumbnail_concept") or base_analysis.get("visual_concept"):
        creative_plan["thumbnail_concept"] = base_analysis.get("thumbnail_concept") or base_analysis.get("visual_concept")

    return V2EditorialPackage(
        post_title_ar=post_title_ar,
        summary_ar=summary_ar,
        pages=five_pages,
        hook=hook,
        conclusion_ar=conclusion,
        conclusion_highlights=conclusion_hl,
        cta_ar=cta_save,
        cta_description=cta_desc,
        creative_plan=creative_plan,
    )
