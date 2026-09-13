from __future__ import annotations

import json
import re
import time
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
   - Do NOT include chapters, timestamps, bullet points, or score labels.
   - Length constraint: The narrative body must be around 1,550 to 1,750 characters so that after adding the subscription CTA and hashtags at the end, the total character count is strictly between 1,750 and 1,950 characters (and never exceeds 2,000 characters).

IMPORTANT FORMATTING RULE: Ensure valid JSON syntax. For any quotes within text values, use single quotes or Arabic angle brackets « » to avoid breaking JSON string delimiters.
""".strip()


def _normalize_model_id(model_name: str) -> str:
    cleaned = model_name.strip().lower()
    if "new" in cleaned and ("5.6" in cleaned or "luna" in cleaned):
        return "gpt-5.6-new"
    if "luna-testing" in cleaned:
        return "gpt-5.6-luna-testing"
    if "luna" in cleaned or "5.6" in cleaned:
        return "gpt-5.6-luna"
    if "claude" in cleaned and ("4.6" in cleaned or "4-6" in cleaned or "4_6" in cleaned or "sonnet" in cleaned):
        return "claude-sonnet-4-6"
    if "deepseek" in cleaned and "flash" in cleaned:
        return "deepseek-flash"
    if "deepseek" in cleaned:
        return "deepseek"
    slug = re.sub(r"[^\w\.-]+", "-", cleaned).strip("-")
    return slug


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    match_braces = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match_braces:
        return match_braces.group(1).strip()
    return cleaned


def _resilient_extract_json(raw: str) -> dict[str, Any]:
    """Fallback extractor when JSON contains unescaped quotes in values."""
    data: dict[str, Any] = {}
    m_lang = re.search(r'"source_language"\s*:\s*"([^"]+)"', raw)
    if m_lang:
        data["source_language"] = m_lang.group(1)

    m_tr = re.search(r'"transcript"\s*:\s*(\[.*?\])(?=\s*,\s*"post_title_ar")', raw, re.DOTALL)
    if m_tr:
        try:
            data["transcript"] = json.loads(m_tr.group(1))
        except Exception:
            data["transcript"] = []

    m_title = re.search(r'"post_title_ar"\s*:\s*"(.*?)"(?=\s*,\s*"summary_ar")', raw, re.DOTALL)
    if m_title:
        data["post_title_ar"] = m_title.group(1)

    m_sum = re.search(r'"summary_ar"\s*:\s*"(.*?)"(?=\s*,\s*"post_description")', raw, re.DOTALL)
    if m_sum:
        raw_s = m_sum.group(1)
        data["summary_ar"] = raw_s.replace("\\n", "\n")

    m_desc = re.search(r'"post_description"\s*:\s*"(.*)"\s*\}\s*$', raw, re.DOTALL)
    if m_desc:
        raw_d = m_desc.group(1)
        data["post_description"] = raw_d.replace("\\n", "\n")

    return data


def _call_vyceai_api(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str = "You are an expert video analyst producing Arabic social media video briefs. Return strictly valid JSON.",
    temperature: float = 0.4,
    timeout: int = 90,
) -> str:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    normalized_model = _normalize_model_id(model)
    payload = {
        "model": normalized_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": 2500,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        },
    )
    last_err: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                choices = result.get("choices", [])
                if not choices:
                    raise RuntimeError(f"VyceAI returned empty choices: {result}")
                return choices[0]["message"]["content"]
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="ignore")
            last_err = RuntimeError(f"VyceAI API HTTP {err.code} Error ({err.reason}): {body}")
            if err.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(5.0 * (attempt + 1))
                continue
            raise last_err from err
        except Exception as err:
            last_err = RuntimeError(f"VyceAI API connection failed: {err}")
            if attempt < 4:
                time.sleep(4.0 * (attempt + 1))
                continue
            raise last_err from err
    if last_err:
        raise last_err
    raise RuntimeError("VyceAI API failed after retries")


def _adjust_summary_vyceai(
    base_url: str,
    api_key: str,
    model: str,
    current_summary: str,
    min_words: int,
    max_words: int,
) -> str:
    prompt = f"""
أعد صياغة النص العربي التالي بدقة بحيث يكون ملخصاً شاملاً ومتماسكاً باللغة العربية الفصحى يتكون من فقرتين متوازنتين، ويكون إجمالي عدد الكلمات بدقة بين {min_words} و {max_words} كلمة (حوالي 75 كلمة لكل فقرة). لا تضف أي عناوين أو مقدمات أو خاتمات، فقط النص العربي:

النص الأصلي:
{current_summary}
""".strip()
    try:
        raw = _call_vyceai_api(
            base_url,
            api_key,
            model,
            prompt,
            system_prompt="You are a professional Arabic language editor. Return ONLY the requested Arabic text without markdown or commentary.",
            temperature=0.3,
            timeout=45,
        )
        return raw.strip().strip('"').strip("'")
    except Exception:
        return current_summary


def analyze_video_vyceai(
    source: str,
    local_path: Path,
    settings: Settings,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = settings.vyceai_api_key
    if not api_key:
        raise RuntimeError("VyceAI_api key is not configured in .env")

    model = settings.vyceai_model or "gpt-5.6-luna"

    # Build progressive context (focused to avoid proxy HTTP 500 error on large inputs)
    contexts_to_try: list[str] = []
    if metadata:
        title = metadata.get("title", "")
        channel = metadata.get("channel", "")
        desc = metadata.get("description", "")
        transcript = metadata.get("transcript_text", "")

        # Optimal size that succeeds consistently on VyceAI proxy
        contexts_to_try.append(f"""VIDEO CONTEXT (GROUND TRUTH):
- Original Video Title: {title}
- Channel / Speaker: {channel}
- Video Description:
{desc[:800]}

- Spoken Dialogue / Auto-Captions Transcript:
{transcript[:300]}
""")
        # Compact fallback if first attempts encounter proxy limits
        contexts_to_try.append(f"""VIDEO CONTEXT (GROUND TRUTH):
- Original Video Title: {title}
- Channel / Speaker: {channel}
- Video Description:
{desc[:400]}
""")
    else:
        contexts_to_try.append("")

    last_error: Exception | None = None
    content: str | None = None

    for i, v_ctx in enumerate(contexts_to_try):
        prompt_text = f"{v_ctx}\n\n{PROMPT}" if v_ctx else PROMPT
        try:
            if i > 0:
                time.sleep(4)  # Brief pause between retries to satisfy proxy rate limiter
            content = _call_vyceai_api(
                settings.vyceai_base_url,
                api_key,
                model,
                prompt_text,
                temperature=0.4,
                timeout=90,
            )
            if content:
                break
        except Exception as err:
            last_error = err
            continue

    if not content:
        if last_error:
            raise last_error
        raise RuntimeError("VyceAI failed to return a response from GPT 5.6 Luna")

    cleaned = _clean_json_text(content)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        payload = _resilient_extract_json(cleaned)

    if not isinstance(payload, dict) or "summary_ar" not in payload:
        raise RuntimeError(f"VyceAI JSON missing required fields. Output was:\n{content[:500]}")

    # Validate and balance summary words if needed
    summary = str(payload.get("summary_ar", "")).strip()
    count = word_count(summary)
    if not (settings.summary_min_words <= count <= settings.summary_max_words):
        try:
            time.sleep(2)
            adjusted = _adjust_summary_vyceai(
                settings.vyceai_base_url,
                api_key,
                model,
                summary,
                settings.summary_min_words,
                settings.summary_max_words,
            )
            adj_count = word_count(adjusted)
            if settings.summary_min_words <= adj_count <= settings.summary_max_words:
                summary = adjusted
        except Exception:
            pass

    payload["summary_ar"] = summary
    return payload
