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
    pages: list[str]  # Exactly 4 pages
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
1. الأمانة التامة للنص الأصلي: يمنع منعاً باتاً إضافة أي نصائح خارجية، أو اختراع روتين صباحي أو مسائي، أو ذكر عادات نوم أو أي معلومات غير موجودة في النص الأصلي. التزم بدقة بنقل نفس الأفكار والحقائق الواردة في النص دون زيادة أو نقصان.
2. يمنع قطع الجملة بين الصفحتين. كل صفحة يجب أن تبدأ بجملة مستقلة المعنى وتنتهي بنقطة تامة.
3. لا تستخدم نقاطاً نقطية أو عناوين.

النص الأصلي:
{clean_text}

أعد الناتج بصيغة JSON فقط:
{{
  "page_a": "نص الصفحة الأولى (30-45 كلمة تنتهي بنقطة)",
  "page_b": "نص الصفحة الثانية (30-45 كلمة تنتهي بنقطة)"
}}
""".strip()

    try:
        res = call_llm(prompt, settings, temperature=0.2)
        match = re.search(r"(\{.*\})", res, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            pa = str(data.get("page_a", "")).strip()
            pb = str(data.get("page_b", "")).strip()
            if pa and pb and word_count(pa) >= 20 and word_count(pb) >= 20:
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


VOICEOVER_SUFFIX = "خلاصة الحوار وأبرز أسراره في ثوانٍ"


def generate_v2_conclusion_and_cta(
    metadata: dict[str, Any],
    summary_ar: str,
    four_pages: list[str],
    settings: Settings,
) -> tuple[str, list[str], str, str]:
    """
    Generates a concise conclusion and save CTA (< 100 tokens total) with zero hook token overhead.
    """
    prompt = f"""
أنت خبير محتوى عربي لفيديوهات السوشيال ميديا القصيرة.
المطلوب صياغة خاتمة رنانة ودعوة للحفظ والمتابعة (CTA) لنهاية الفيديو بناءً على ملخص الصفحات:
{' '.join(four_pages)}

المطلوب بدقة واختصار:
1. `conclusion`: جملة خاتمة عميقة ومحكمة لا تتجاوز 12 كلمة تلخص الجوهر المعرفي للفيديو وتترك أثراً قوياً.
2. `conclusion_highlights`: قائمة بكلمة أو كلمتين مفتاحيتين من جملة الخاتمة ليتم تلوينهما بالذهبي.
3. `cta_save`: احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد
4. `cta_description`: السر الأهم والخطوات التطبيقية في الوصف بالأسفل 👇

القاعدة الصارمة: يمنع منعاً باتاً دمج أو تكرار عبارة الوصف داخل `cta_save`. حقل `cta_save` مخصص فقط للحفظ والمشاركة ومتابعة الصفحة.

أعد الناتج بصيغة JSON فقط:
{{
  "conclusion": "جملة الخاتمة",
  "conclusion_highlights": ["كلمة1", "كلمة2"],
  "cta_save": "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد",
  "cta_description": "السر الأهم والخطوات التطبيقية في الوصف بالأسفل 👇"
}}
""".strip()

    raw_json = call_llm(prompt, settings, temperature=0.3)
    data: dict[str, Any] = {}
    try:
        match = re.search(r"(\{.*\})", raw_json, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
    except Exception as err:
        logger.warning("Failed to parse LLM conclusion JSON: %s", err)

    conclusion = str(data.get("conclusion") or "حين يكتمل الوعي بالواقع، تبدأ الخطوات الحقيقية للتغيير").strip()
    conclusion_hl = data.get("conclusion_highlights") or ["الوعي", "التغيير"]
    cta_save = "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد"
    cta_desc = "السر الأهم والخطوات التطبيقية في الوصف بالأسفل 👇"
    return conclusion, conclusion_hl, cta_save, cta_desc


def build_v2_editorial_package(
    base_analysis: dict[str, Any],
    metadata: dict[str, Any],
    settings: Settings,
) -> V2EditorialPackage:
    """
    Main entry point for V2 editorial production.
    Takes the base 140-160 word summary, splits into 4 complete-sentence pages,
    creates Option 3 voiceover text (Title + Suffix), and generates the conclusion & CTA.
    """
    raw_title = str(metadata.get("title") or "").strip()
    orig_title = str(metadata.get("original_title") or "").strip()
    if re.search(r"[\u0600-\u06FF]", orig_title):
        post_title_ar = re.sub(r"#\b(?:shorts?|يوتيوب_عربي)\b", "", orig_title, flags=re.IGNORECASE).strip()
    elif re.search(r"[\u0600-\u06FF]", raw_title):
        post_title_ar = re.sub(r"#\b(?:shorts?|يوتيوب_عربي)\b", "", raw_title, flags=re.IGNORECASE).strip()
    else:
        post_title_ar = base_analysis.get("post_title_ar") or raw_title
    summary_ar = base_analysis.get("summary_ar", "").strip()

    # If pages are already pre-computed in base_analysis (e.g. Brainstorm mode), use them directly
    if base_analysis.get("pages") and len(base_analysis["pages"]) == 4:
        four_pages = list(base_analysis["pages"])
    else:
        # Base summary must have two semantic halves
        paragraphs = [p.strip() for p in summary_ar.split("\n") if p.strip()]
        if len(paragraphs) >= 2:
            half_one = paragraphs[0]
            half_two = paragraphs[1]
        else:
            # Split roughly at sentence midpoint
            sents = [s.strip() for s in re.split(r"(?<=[.!?؟؛])\s+", summary_ar) if s.strip()]
            mid = len(sents) // 2
            half_one = " ".join(sents[:mid])
            half_two = " ".join(sents[mid:])

        # Split Half 1 into Page 1 and Page 2 (35-40 words each)
        p1, p2 = split_half_into_two_pages(half_one, half_index=1, settings=settings)

        # Split Half 2 into Page 3 and Page 4 (35-40 words each)
        p3, p4 = split_half_into_two_pages(half_two, half_index=2, settings=settings)

        four_pages = [p1, p2, p3, p4]

    # Voiceover: post_title_ar + Option 3 suffix ("... خلاصة الحوار وأبرز أسراره في ثوانٍ.")
    clean_title_for_tts = re.sub(r"[.!؟?\-_|]+$", "", post_title_ar).strip()
    voiceover_tts = f"{clean_title_for_tts}... {VOICEOVER_SUFFIX}."

    hook = HookCandidate(
        display_hook=clean_title_for_tts,
        highlight_phrase=VOICEOVER_SUFFIX,
        tts_text=voiceover_tts,
        category="صوت افتتاحي",
        scores={"relevance": 10.0},
        total_score=100.0,
        explanation="Direct title + Option 3 voiceover hook",
    )

    if base_analysis.get("conclusion"):
        conclusion = str(base_analysis["conclusion"]).strip()
        conclusion_hl = list(base_analysis.get("conclusion_highlights") or ["الوعي", "التغيير"])
        cta_save = str(base_analysis.get("cta_save") or "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد")
        cta_desc = str(base_analysis.get("cta_description") or "السر الأهم والخطوات التطبيقية في الوصف بالأسفل 👇")
    else:
        conclusion, conclusion_hl, cta_save, cta_desc = generate_v2_conclusion_and_cta(
            metadata, summary_ar, four_pages, settings
        )

    creative_plan = {
        "version": "v2",
        "voiceover": {
            "tts_text": voiceover_tts,
            "title_ar": clean_title_for_tts,
            "suffix": VOICEOVER_SUFFIX,
        },
        "pages": [
            {"page": i + 1, "words": word_count(p), "text": p}
            for i, p in enumerate(four_pages)
        ],
        "conclusion": {
            "text": conclusion,
            "highlights": conclusion_hl,
            "cta_save": cta_save,
            "cta_description": cta_desc,
        },
    }

    return V2EditorialPackage(
        post_title_ar=post_title_ar,
        summary_ar=summary_ar,
        pages=four_pages,
        hook=hook,
        conclusion_ar=conclusion,
        conclusion_highlights=conclusion_hl,
        cta_ar=cta_save,
        cta_description=cta_desc,
        creative_plan=creative_plan,
    )
