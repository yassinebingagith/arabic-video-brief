"""Short, source-specific Arabic discussion questions shared by video modes."""
from __future__ import annotations

import json
import re
from typing import Any

from .config import Settings


def normalize_question(value: Any) -> str:
    text = " ".join(str(value or "").replace("{", "").replace("}", "").split())
    if not text.endswith(("؟", "?")):
        return ""
    text = text[:-1].strip() + "؟"
    if not re.search(r"[\u0600-\u06ff]", text) or re.search(r"[A-Za-z]", text):
        return ""
    if "؟" in text[:-1] or "?" in text[:-1] or not 4 <= len(text.split()) <= 18 or len(text) > 140:
        return ""
    if text in {"ما رأيك في هذا الموضوع؟", "ما رأيك في هذا الفيديو؟"}:
        return ""
    return text


def resolve_ending_question(analysis: dict[str, Any], metadata: dict[str, Any], summary: str, settings: Settings) -> str:
    """Reuse authored questions; generate only when missing/legacy declarative."""
    legacy = analysis.get("conclusion")
    candidates = [analysis.get("ending_question_ar"), analysis.get("question_ar"),
                  legacy.get("text") if isinstance(legacy, dict) else legacy]
    for candidate in candidates:
        question = normalize_question(candidate)
        if question:
            return question

    # Lazy import keeps media rendering independent of the LLM/editorial modules.
    from .v2.editorial import call_llm
    prompt = f"""اكتب سؤالاً واحداً بالعربية الفصحى المبسطة لنهاية فيديو، مرتبطاً بفكرة محددة في الملخص.
العنوان: {metadata.get('title', '')}
الملخص: {summary}
السؤال قابل للإجابة بتجربة أو اختيار مع تعليل أو مقارنة وجهتي نظر؛ لا تطلب إفشاء معلومات حساسة.
اكتب بروح تذييل شريحة تفسيرية: اربط السؤال بتفصيل أو آلية أو مثال محدد شُرح في الملخص، واجعل القارئ يطبقه أو يفحصه في موقف واضح.
لا تكرر عنوان الفيديو بصيغة سؤال، ولا تسأل عن «فكرة ستطبقها اليوم» دون تسميتها، ولا تستخدم خاتمة تحفيزية أو طلب السحب إلى شريحة أخرى.
من 4 إلى 18 كلمة وبحد أقصى 140 حرفاً، وينتهي بعلامة استفهام عربية.
لا تكتب خلاصة تقريرية ولا سؤال «ما رأيك؟» العام ولا تجمع طلبات الحفظ والمشاركة والمتابعة.
لا تفترض نصيحة عملية لكل موضوع؛ طابق السؤال مع العلم أو التاريخ أو الخبر أو النفس حسب المصدر.
أعد JSON فقط: {{"ending_question_ar": "السؤال"}}"""
    for attempt in range(2):
        raw = call_llm(prompt, settings, temperature=0.3)
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group(0) if match else raw)
            question = normalize_question(data.get("ending_question_ar"))
            if question:
                return question
        except (ValueError, AttributeError):
            pass
        prompt += "\nالناتج السابق غير صالح؛ أعد سؤالاً واحداً قصيراً بالشكل المطلوب فقط."
    raise ValueError("Could not produce a valid Arabic ending question; supply ending_question_ar in the analysis JSON.")


def normalize_footer(value: Any) -> str:
    """V2 permits one question or a concrete action; old statements are not actions."""
    question = normalize_question(value)
    if question:
        return question
    text = " ".join(str(value or "").replace("{", "").replace("}", "").split())
    if not 4 <= len(text.split()) <= 18 or len(text) > 140:
        return ""
    if not re.search(r"[\u0600-\u06ff]", text) or re.search(r"[A-Za-z؟?]", text):
        return ""
    if not re.match(r"^(?:جرّب|جرب|اختبر|قارن|لاحظ|راجع|اختر|اكتب|حدد|حدّد|اسأل|فكّر|فكر|تأمل|تأمّل|تتبّع|تتبع|ابحث|ناقش|طبّق|طبق|تحقق|تحقّق)\s", text):
        return ""
    if any(word in text for word in ("اسحب", "تابع الصفحة", "اضغط إعجاب", "شارك الفيديو")):
        return ""
    return text


def resolve_v2_footer(analysis: dict[str, Any], metadata: dict[str, Any], summary: str, settings: Settings) -> str:
    """Prefer the authored carousel-like footer; retain valid legacy questions."""
    footer = normalize_footer(analysis.get("ending_text_ar"))
    if footer:
        return footer
    # Do not reinterpret an old declarative conclusion as a user action.
    return resolve_ending_question(analysis, metadata, summary, settings)
