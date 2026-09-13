from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import Settings
from .utils import word_count


PROMPT = """
Analyze this video as source material for an Arabic social-media video brief and a high-converting publication article.

Your audience consists of fast-scrolling Arab social media users (Instagram, TikTok, YouTube Shorts, Facebook) from diverse ages and backgrounds. They crave clear, addictive, real-world value and practical understanding, NOT dry academic book summaries or theoretical exposition.

CRITICAL WRITING RULES:
1. STRICT ANTI-META BAN: Absolutely NEVER use detached meta-phrases like "يناقش المقطع", "يستعرض الضيف", "يتناول الفيديو", "في هذه المقابلة", or "يقدم الطرح". Plunge directly into the living reality, facts, mechanisms, and ideas.
2. SIMPLIFIED MODERN FUSHA (فصحى بيضاء سلسة ومبسطة): Write in 100% correct Modern Standard Arabic using lucid, accessible everyday vocabulary. Avoid archaic classical vocabulary or dense textbook jargon.
3. CONCRETE REAL-WORLD EXAMPLES: Whenever explaining ideas, anchor them in tangible examples (naming specific professions, daily situations, real numbers, or tangible analogies) so the viewer immediately relates to the content.

Return only a valid JSON object with the following fields:
1. `source_language`: Spoken language of the source video (e.g., "en", "ar").
2. `transcript`: Meaningful timestamped segments in the spoken source language.
3. `post_title_ar`: A direct, faithful, and accurate translation of the source video's original title (from VIDEO CONTEXT) into 100% pure Modern Standard Arabic. Faithfully translate the core meaning and accurately transliterate any foreign guest or channel names phonetically into Arabic letters (e.g. "Your Lack of Personal Purpose Is Causing Your Romantic Obsession - Jett Franzen" -> "غياب هدفك الشخصي يسبب هوسك العاطفي – جيت فرانزن"). Strictly no English words, no emojis, and no hashtags.
4. `summary_ar`: Exactly one self-contained Modern Standard Arabic text of 140 to 160 words total, structured into exactly two balanced paragraphs (70 to 80 words each), separated by a single newline:
   - Paragraph 1 (Page 1, 0-10s, 70-80 words): Addictive storytelling hook plunging straight into the core reality, shocking facts, or daily struggle revealed in the video. Zero meta-language.
   - Paragraph 2 (Page 2, 10-20s, 70-80 words): The core value delivery. If the video is practical/self-dev/health/career: deliver concrete pro-tips, golden rules, and actionable solutions the viewer can apply. If the video is informative/news/political/philosophical: deliver the deep takeaway, the hidden game behind the scenes, and the real-world consequence affecting their future. No titles or headers in this field.
5. `post_description`: An in-depth, addictive narrative article in simplified Modern Fusha structured in this exact format:
   - Line 1: Specific Arabic topic title followed by an en-dash and speaker/channel name (e.g. `خمس وظائف فقط ستصمد أمام الذكاء الاصطناعي بحلول 2030 – د. رومان يامبولسكي`). Do NOT output literal placeholder text like "عنوان الموضوع".
   - Opening paragraph: Addictive, relatable hook (around 220-270 characters) drawing the reader into the topic immediately. No meta-talk.
   - 3 to 4 comprehensive thematic sections, each starting with `-عنوان المحور الوصفي-` followed by detailed explanatory paragraphs (each section around 350-450 characters).
   - Real examples requirement: In every section, include concrete real-world examples (mentioning specific professions, everyday scenarios, real mechanisms) rather than speaking in vague generalities.
   - Final section: Practical pro-tips / action steps (or deep future implications if purely informative).
   - Do NOT include chapters, timestamps, hooks, bullet points, or score labels.
   - Length constraint: The narrative body must be around 1,550 to 1,750 characters so that after adding the subscription CTA and hashtags at the end, the total character count is strictly between 1,750 and 1,950 characters (and never exceeds 2,000 characters).

IMPORTANT FORMATTING RULE: Ensure valid JSON syntax. For any quotes within text values, use single quotes or Arabic angle brackets « » to avoid breaking JSON string delimiters.
""".strip()


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    match_braces = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match_braces:
        return match_braces.group(1).strip()
    return cleaned


def _call_seekai_api(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str = "You are an expert video analyst producing Arabic social media video briefs. Return strictly valid JSON.",
    temperature: float = 0.5,
    timeout: int = 35,
) -> str:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
        choices = result.get("choices", [])
        if not choices:
            raise RuntimeError(f"SeekAI returned empty choices: {result}")
        return choices[0]["message"]["content"]


def _adjust_summary_seekai(
    base_url: str,
    api_key: str,
    candidate_models: list[str],
    current_summary: str,
    min_words: int,
    max_words: int,
) -> str:
    prompt = f"""
أعد صياغة النص العربي التالي بدقة بحيث يكون ملخصاً شاملاً ومتماسكاً باللغة العربية الفصحى يتكون من فقرتين متوازنتين، ويكون إجمالي عدد الكلمات بدقة بين {min_words} و {max_words} كلمة (حوالي 75 كلمة لكل فقرة). لا تضف أي عناوين أو مقدمات أو خاتمات، فقط النص العربي:

النص الأصلي:
{current_summary}
""".strip()
    for model in candidate_models:
        try:
            raw = _call_seekai_api(
                base_url,
                api_key,
                model,
                prompt,
                system_prompt="You are a professional Arabic language editor. Return ONLY the requested Arabic text without markdown or commentary.",
                temperature=0.3,
                timeout=25,
            )
            return raw.strip().strip('"').strip("'")
        except Exception:
            continue
    return current_summary


def analyze_video_seekai(
    source: str,
    local_path: Path,
    settings: Settings,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = settings.seekai_api_key
    if not api_key:
        raise RuntimeError("Seekai_api key is not configured in .env")

    video_context = ""
    if metadata:
        title = metadata.get("title", "")
        channel = metadata.get("channel", "")
        desc = metadata.get("description", "")
        transcript = metadata.get("transcript_text", "")
        video_context = f"""
VIDEO CONTEXT (GROUND TRUTH):
- Original Video Title: {title}
- Channel / Speaker: {channel}
- Video Description:
{desc[:1500]}

- Spoken Dialogue / Auto-Captions Transcript:
{transcript[:6000]}
"""
    prompt_text = f"{video_context}\n\n{PROMPT}" if video_context else PROMPT

    candidate_models = [settings.seekai_model]

    last_error: Exception | None = None
    payload: dict[str, Any] | None = None

    for model in candidate_models:
        try:
            content = _call_seekai_api(
                settings.seekai_base_url,
                api_key,
                model,
                prompt_text,
                temperature=0.4,
                timeout=35,
            )
            cleaned = _clean_json_text(content)
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "summary_ar" in parsed:
                payload = parsed
                break
        except Exception as error:
            last_error = error
            continue

    if payload is None:
        if last_error:
            raise RuntimeError(f"SeekAI video analysis failed: {last_error}")
        raise RuntimeError("SeekAI failed to return valid analysis JSON")

    # Validate and balance summary words
    summary = str(payload.get("summary_ar", "")).strip()
    count = word_count(summary)
    if not (settings.summary_min_words <= count <= settings.summary_max_words):
        for _ in range(2):
            try:
                summary = _adjust_summary_seekai(
                    settings.seekai_base_url,
                    api_key,
                    candidate_models,
                    summary,
                    settings.summary_min_words,
                    settings.summary_max_words,
                )
                count = word_count(summary)
                if settings.summary_min_words <= count <= settings.summary_max_words:
                    break
            except Exception:
                pass

    payload["summary_ar"] = summary
    return payload
