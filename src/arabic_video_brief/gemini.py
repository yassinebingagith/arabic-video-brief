from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .config import Settings
from .utils import word_count


ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "source_language": {"type": "string"},
        "transcript": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start_seconds": {"type": "number"},
                    "end_seconds": {"type": "number"},
                    "text": {"type": "string"},
                    "language": {"type": "string"},
                },
                "required": ["start_seconds", "end_seconds", "text", "language"],
            },
        },
        "post_title_ar": {"type": "string"},
        "summary_ar": {"type": "string"},
        "post_description": {"type": "string"},
    },
    "required": ["source_language", "transcript", "post_title_ar", "summary_ar", "post_description"],
}


PROMPT = """
Analyze this video as source material for an Arabic social-media video brief and a high-converting publication article.

Your audience consists of fast-scrolling Arab social media users (Instagram, TikTok, YouTube Shorts, Facebook) from diverse ages and backgrounds. They crave clear, addictive, real-world value and practical understanding, NOT dry academic book summaries or theoretical exposition.

CRITICAL WRITING RULES:
1. STRICT ANTI-META BAN: Absolutely NEVER use detached meta-phrases like "يناقش المقطع", "يستعرض الضيف", "يتناول الفيديو", "في هذه المقابلة", or "يقدم الطرح". Plunge directly into the living reality, facts, mechanisms, and ideas.
2. SIMPLIFIED MODERN FUSHA (فصحى بيضاء سلسة ومبسطة): Write in 100% correct Modern Standard Arabic using lucid, accessible everyday vocabulary. Avoid archaic classical vocabulary or dense textbook jargon.
3. CONCRETE REAL-WORLD EXAMPLES: Whenever explaining ideas, anchor them in tangible examples (naming specific professions, daily situations, real numbers, or tangible analogies) so the viewer immediately relates to the content.

Return only the requested structured JSON object with the following fields:
1. `source_language`: Spoken language of the source video (e.g., "en", "ar").
2. `transcript`: Compact meaningful timestamped segments in the spoken source language.
3. `post_title_ar`: A direct, faithful, and accurate translation of the source video's original title (from VIDEO CONTEXT) into 100% pure Modern Standard Arabic. Faithfully translate the core meaning and accurately transliterate any foreign guest or channel names phonetically into Arabic letters (e.g. "Female Psychopath Explains How She Manipulates Men - Kanika Batra" -> "سيكوباتية توضح كيف تتلاعب بالرجال – كانيكا باترا"). Do NOT invent a new topic hook or arbitrary question; translate the original title directly. Strictly no English words, no emojis, and no hashtags.
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
""".strip()


def _extract_text(response: Any) -> str:
    for attribute in ("output_text", "text"):
        value = getattr(response, attribute, None)
        if value:
            return value
    if isinstance(response, dict):
        for key in ("output_text", "text"):
            if response.get(key):
                return str(response[key])
    raise RuntimeError("Gemini returned no text output")


def _adjust_summary(client: Any, model: str, current_summary: str, min_words: int, max_words: int) -> str:
    prompt = f"""
أعد صياغة النص العربي التالي بدقة بحيث يكون ملخصاً شاملاً ومتماسكاً باللغة العربية الفصحى يتكون من فقرتين متوازنتين، ويكون إجمالي عدد الكلمات بدقة بين {min_words} و {max_words} كلمة (حوالي 75 كلمة لكل فقرة). لا تضف أي عناوين أو مقدمات أو خاتمات، فقط النص العربي:

النص الأصلي:
{current_summary}
""".strip()
    candidate_models = [model]
    for fallback in ("gemini-3-flash-preview", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.8-flash"):
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error: Exception | None = None
    for candidate in candidate_models:
        try:
            response = client.models.generate_content(
                model=candidate,
                contents=prompt,
            )
            return _extract_text(response).strip()
        except Exception as error:
            last_error = error
            err_str = str(error)
            if any(token in err_str for token in ("429", "503", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "quota")):
                continue
            raise
    if last_error:
        raise last_error
    return ""


def _validate(payload: dict[str, Any], settings: Settings, client: Any = None) -> dict[str, Any]:
    summary = str(payload.get("summary_ar", "")).strip()
    count = word_count(summary)
    if not (settings.summary_min_words <= count <= settings.summary_max_words) and client is not None:
        for _ in range(3):
            try:
                summary = _adjust_summary(client, settings.gemini_model, summary, settings.summary_min_words, settings.summary_max_words)
                count = word_count(summary)
                if settings.summary_min_words <= count <= settings.summary_max_words:
                    break
            except Exception:
                pass
    if not settings.summary_min_words <= count <= settings.summary_max_words:
        raise ValueError(f"Gemini summary has {count} words; expected {settings.summary_min_words}-{settings.summary_max_words}")
    payload["summary_ar"] = summary
    return payload


def _generate_content(client: Any, model: str, prompt_text: str, video_uri: str | None = None, mime_type: str | None = None) -> Any:
    from google.genai import types

    parts = []
    if video_uri:
        parts.append(types.Part(file_data=types.FileData(file_uri=video_uri, mime_type=mime_type)))
    parts.append(types.Part(text=prompt_text))

    candidate_models = [model]
    for fallback in ("gemini-3-flash-preview", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.8-flash"):
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error: Exception | None = None
    for candidate in candidate_models:
        try:
            return client.models.generate_content(
                model=candidate,
                contents=types.Content(parts=parts),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=ANALYSIS_SCHEMA,
                    thinking_config=types.ThinkingConfig(thinking_level="LOW"),
                    media_resolution="MEDIA_RESOLUTION_LOW",
                ),
            )
        except Exception as error:
            last_error = error
            err_str = str(error)
            if any(token in err_str for token in ("429", "503", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "quota")):
                continue
            raise
    if last_error:
        raise last_error


def analyze_video(source: str, local_path: Path, settings: Settings, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    try:
        from google import genai
    except ImportError as error:
        raise RuntimeError("google-genai is not installed; run scripts/setup.ps1") from error

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
{desc[:3000]}

- Spoken Dialogue / Auto-Captions Transcript:
{transcript[:15000]}
"""
    prompt_text = f"{video_context}\n\n{PROMPT}" if video_context else PROMPT

    client = genai.Client(api_key=settings.gemini_api_key, http_options={"timeout": 300_000})
    response = None
    direct_error: Exception | None = None
    if source.startswith(("https://www.youtube.com/", "https://youtu.be/")):
        try:
            response = _generate_content(client, settings.gemini_model, prompt_text, video_uri=source)
        except Exception as error:
            direct_error = error

    if response is None and video_context:
        try:
            response = _generate_content(client, settings.gemini_model, prompt_text)
        except Exception as text_err:
            direct_error = text_err

    if response is None:
        try:
            uploaded = client.files.upload(file=str(local_path))
            deadline = time.monotonic() + 600
            while getattr(getattr(uploaded, "state", None), "name", "ACTIVE") not in {"ACTIVE", "FAILED"}:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Gemini file processing exceeded 10 minutes")
                time.sleep(2)
                uploaded = client.files.get(name=uploaded.name)
            if getattr(getattr(uploaded, "state", None), "name", "ACTIVE") == "FAILED":
                raise RuntimeError("Gemini failed to process the uploaded video") from direct_error
            response = _generate_content(
                client, settings.gemini_model, prompt_text, video_uri=uploaded.uri, mime_type=getattr(uploaded, "mime_type", "video/mp4")
            )
        except Exception:
            response = _generate_content(client, settings.gemini_model, prompt_text)

    raw = _extract_text(response)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("Gemini returned invalid structured JSON") from error
    return _validate(payload, settings, client=client)

