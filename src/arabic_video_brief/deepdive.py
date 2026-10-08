from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import Settings

logger = logging.getLogger(__name__)

DEEPDIVE_SYSTEM_PROMPT = """You are a Senior Knowledge Architect, Elite Essayist, and Executive Content Strategist. Your task is to transform the provided video/audio transcript into an exhaustive, highly engaging, deep-dive educational synthesis (ملخص معرفي مطوّل وشامل).

### Target Audience & Tone:
- Language: Polished, professional, and captivating Modern Standard Arabic (فصحى رصينة، سلسة، وإنسانية).
- Tone: Authoritative, intellectually stimulating, reflective, and practically actionable. Must read like a masterwork written by an experienced human thinker, NOT like a bulleted AI summary or robotic lecture notes.
- Audience: High-performing professionals, thinkers, lifelong learners, and decision-makers.

### Critical Processing Rules:
1. Preserve Concrete Data & Full Depth:
   - Do NOT abbreviate or generalize specific evidence.
   - Retain all exact statistics, percentages, years, numbers, survey findings, and named case studies cited in the transcript.
   - Explain the full underlying logic, the "why," and the "how" behind every concept. Depth and substance take priority over brevity.
2. Conceptual & Technical Precision with English Terms:
   - Keep the speaker’s exact frameworks, models, and coined concepts intact.
   - You MUST write the original English term in parentheses next to the Arabic translation upon its mention (e.g. (Jay Shetty)، قوة الصمت (The Power of Silence)، متلازمة شريط الإنجازات الزائف (Highlight Reel Syndrome)، فخ المقارنات (The Comparison Trap)، قانون الخمسة المقربين (The Rule of 5)، تنقية البيئة (Social Detox)، الاستثمار التراكمي (Compounding Skills & Wealth)). This gives the summary immense authority, credibility, and practical value.
3. Natural Human Prose — STRICT BAN ON AI MARKDOWN & ANNOTATIONS:
   - Strictly NO markdown header symbols (#, ##, ###).
   - Strictly NO horizontal dividers (---, ___).
   - Strictly NO bold asterisks (**text** or *text*). Emphasis must be conveyed through eloquent phrasing and rhetorical rhythm.
   - Strictly NO robotic bullet lists, numbered dashes (e.g. "1. **...**:", "   - ..."). Break points into elegant natural paragraphs starting with narrative transition words (أولاً، ... / ثانياً، ... / ثالثاً، ...).
   - Strictly NO artificial mechanical section titles like "المحور الأول", "المحور الثاني", "النموذج النظري", "التطبيق العملي", or "الخاتمة وسؤال التأمل".
   - Use ONLY clean double line breaks and the elegant diamond symbol (◈) for major thematic section titles.
4. Seamless Ending & Direct Engagement:
   - Do NOT create a section named "الخاتمة" or "سؤال التأمل".
   - Conclude the narrative organically by synthesizing the overarching philosophy into a powerful, inspiring crescendo.
   - Transition directly from the philosophical conclusion into a profound, soul-searching reflective question that challenges the reader's current life habits.
   - Follow immediately with a warm, natural human call to action to boost engagement (inviting the reader to share their personal experience in the comments, save the summary for later reflection, and share it with others).

### Required Structural Architecture:

[Line 1]: عنوان الموضوع الشامل بالعربية مع اسم المتحدث أو القناة واسمه بالإنجليزية بين قوسين (بدون أي علامات #)

[مقدمة افتتاحية عميقة ومطولة من فقرتين]:
- افتتاح بسياق التحدي المعاصر والمأزق النفسي أو السلوكي أو المهني الذي يعالجه المحتوى.
- نقد المقاربات التقليدية وكيف تختلف رؤية المتحدث وخلفيته وتجاربه الواقعية.
- طرح الأطروحة المركزية بوضوح وبلاغة دون استخدام مصطلحات تقنية جافة.

◈ [عنوان المحور الموضوعي الأول وصفي وجذاب] (English Concept)
- تفكيك المفهوم بشرح وافٍ وتفاصيل دقيقة، مع ربط السلوك الإنساني بالواقع اليومي.
- إدراج المفاهيم الإنجليزية المقابلة بين قوسين.

◈ [عنوان المحور الثاني وصفي وجذاب] (English Concept)
- استعراض النماذج الذهنية والمفارقات، وكشف الأوهام الشائعة، وربطها بالدراسات أو الأمثلة الواقعية الواردة في المقطع.

◈ [عنوان المحور الثالث: خريطة الطريق العملية وعادات الانضباط]
- تفكيك الخطوات التطبيقية، الممارسات اليومية، وقواعد السلوك إلى فقرات سردية متماسكة تبدأ بـ (أولاً، ثانياً، ثالثاً، رابعاً...) مع شرح دقيق للأرقام، المدد الزمنية، والتمارين السلوكية، وإدراج المصطلحات الإنجليزية لكل خطوة.

◈ [مفارقات النضج والرؤى العميقة] (English Concept)
- استخلاص المفارقات الحياتية والدروس المستفادة، ومقارنة تكلفة الانضباط مقابل تكلفة الندم والتهاون.

[الخاتمة الفلسفية والسؤال الوجداني التفاعلي]:
- فقرة ختامية متدفقة تلخص جوهر الرسالة وقيمة الوقت والانضباط.
- سؤال تأملي وجداني عميق يبدأ مباشرة (مثل: إذا نظرت بصدق وتجرد إلى مسار حياتك الآن: ما هي...؟) دون كتابة "سؤال التأمل:".
- دعوة إنسانية ذكية للتفاعل (المشاركة في التعليقات، حفظ الملخص للمراجعة، والمشاركة مع الأصدقاء).

Important: Output pure, pristine Arabic text without any code fences, markdown hashes, divider lines, or asterisks.
""".strip()



def extract_transcript_text(transcript_source: Any) -> str:
    """Extract and reconstruct clean continuous transcript text from multiple source types."""
    if isinstance(transcript_source, Path):
        if transcript_source.is_file():
            try:
                data = json.loads(transcript_source.read_text(encoding="utf-8"))
                return extract_transcript_text(data)
            except Exception:
                return transcript_source.read_text(encoding="utf-8").strip()
        return ""

    if isinstance(transcript_source, str):
        if transcript_source.strip().startswith("{") or transcript_source.strip().startswith("["):
            try:
                data = json.loads(transcript_source)
                return extract_transcript_text(data)
            except Exception:
                pass
        return transcript_source.strip()

    if isinstance(transcript_source, dict):
        segments = transcript_source.get("segments") or transcript_source.get("transcript") or []
        if isinstance(segments, list) and segments:
            lines = [seg.get("text", "").strip() for seg in segments if isinstance(seg, dict) and seg.get("text")]
            return " ".join(lines).strip()
        if "text" in transcript_source:
            return str(transcript_source["text"]).strip()

    if isinstance(transcript_source, list):
        lines: list[str] = []
        for item in transcript_source:
            if isinstance(item, dict) and "text" in item:
                lines.append(str(item["text"]).strip())
            elif isinstance(item, str):
                lines.append(item.strip())
        return " ".join(lines).strip()

    return ""


def _call_openai_compatible_api(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: int = 180,
    max_tokens: int = 8000,
) -> str:
    """Generic caller for OpenAI-compatible chat completion endpoints."""
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ArabicVideoBrief/DeepDive",
            "Accept": "application/json",
        },
    )
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                choices = result.get("choices", [])
                if not choices:
                    raise RuntimeError(f"API returned empty choices: {result}")
                return choices[0]["message"]["content"]
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="ignore")
            last_err = RuntimeError(f"HTTP {err.code} Error ({err.reason}): {body}")
            if err.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(4.0 * (attempt + 1))
                continue
            raise last_err from err
        except Exception as err:
            last_err = RuntimeError(f"API connection failed: {err}")
            if attempt < 3:
                time.sleep(3.0 * (attempt + 1))
                continue
            raise last_err from err
    if last_err:
        raise last_err
    raise RuntimeError("API failed after retries")


def _call_gemini_api(
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Call Google GenAI SDK for deepdive generation."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed; run scripts/setup.ps1") from exc

    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

    candidate_models = [model]
    for fallback in ("gemini-2.5-pro", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest", "gemini-3-flash-preview"):
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error: Exception | None = None
    for candidate in candidate_models:
        try:
            res = client.models.generate_content(
                model=candidate,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.35,
                    max_output_tokens=8192,
                ),
            )
            text = getattr(res, "text", "") or ""
            if text.strip():
                return text.strip()
        except Exception as err:
            last_error = err
            err_str = str(err)
            if any(token in err_str for token in ("429", "503", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "quota")):
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("Gemini API returned empty response for deep-dive synthesis")


def sanitize_deepdive_text(text: str) -> str:
    """
    Sanitize and transform any deep dive summary text into pure human essay prose
    strictly adhering to the Arabic Video Brief DeepDive specification:
    - Strips all markdown code fences (```).
    - Ensures Line 1 is a clean, prestigious title without #, ◈, or markdown markers.
    - Strips all horizontal dividers (---, ___, ***).
    - Strips all bold / italic asterisks (**word** -> word, *word* -> word).
    - Converts robotic section headings (## المحور الأول: X, ## التطبيق العملي, etc.) into elegant diamond sections: ◈ X.
    - Strips robotic ending headings (## الخاتمة وسؤال التأمل, ## الخاتمة, etc.).
    - Converts numbered dashed list items (1. **X**:, - الخطوة 1:) into smooth narrative transitions (أولاً، ... / ثانياً، ... / ثالثاً، ...).
    - Strips dash bullets (- ) and dots (• ).
    - Removes robotic prompt labels like 'سؤال التأمل:'.
    - Appends a warm, organic human community call to action if not present.
    """
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:markdown|text)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    # Strip horizontal dividers
    cleaned = re.sub(r"^[ \t]*[-*_]{3,}[ \t]*$", "", cleaned, flags=re.MULTILINE)
    # Strip bold / italics asterisks
    cleaned = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", cleaned)

    num_map = {
        "1": "أولاً، ",
        "2": "ثانياً، ",
        "3": "ثالثاً، ",
        "4": "رابعاً، ",
        "5": "خامساً، ",
        "6": "سادساً، ",
        "7": "سابعاً، ",
    }

    lines = cleaned.splitlines()
    processed_lines: list[str] = []
    is_title = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            processed_lines.append("")
            continue

        # First non-empty line is Title
        if is_title:
            title = re.sub(r"^[#◈\s\-]+", "", stripped).strip()
            title = re.sub(r"[\s#]+$", "", title).strip()
            processed_lines.append(title)
            is_title = False
            continue

        # Drop robotic ending section headers
        if re.match(r"^(?:#{1,6}\s*)?(?:الخاتمة\s*وسؤال\s*التأمل|الخاتمة|سؤال\s*التأمل)\s*[:\-]*\s*$", stripped):
            continue

        # Strip bullet points dashes or dots FIRST: '- ', '• '
        stripped = re.sub(r"^[ \t]*[-•]\s*", "", stripped)

        # Strip robotic label 'سؤال التأمل:'
        stripped = re.sub(r"^(?:سؤال\s*التأمل)\s*[:\-]*\s*", "", stripped)

        # Check if line is a section header (starts with # or matches known section patterns)
        header_match = re.match(r"^#{1,6}\s*(.*)$", stripped)
        if header_match:
            header_content = header_match.group(1).strip()
            # Clean robotic numeric prefixes like 'المحور الأول:', 'المحور الثاني:'
            header_content = re.sub(r"^المحور\s*(?:الأول|الثاني|الثالث|الرابع|الخامس|السادس)\s*[:\-]*\s*", "", header_content)
            # Avoid repeating diamond
            header_content = header_content.replace("◈", "").strip()
            processed_lines.append(f"◈ {header_content}")
            continue

        # Transform numbered steps/points (e.g. '1. ', '2. ', 'الخطوة 1: ')
        num_step_match = re.match(r"^(?:الخطوة\s*)?([1-7])[\.\-:\)]\s*(.*)$", stripped)
        if num_step_match:
            idx = num_step_match.group(1)
            rest = num_step_match.group(2).strip()
            prefix = num_map.get(idx, "")
            processed_lines.append(f"{prefix}{rest}")
            continue

        processed_lines.append(stripped)

    result = "\n".join(processed_lines)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()

    # Check if CTA is present, if not append warm community engagement CTA
    tail = result[-300:] if len(result) > 300 else result
    if "شارك" not in tail and "احفظ" not in tail:
        cta_text = "\n\nشاركنا تجربتك في التعليقات: كيف غيرت مواجهتك لمخاوفك نظرتك للحياة ومسؤوليتك؟ احفظ هذا الملخص ليكون بوصلة لك عند الشعور بالتردد، وشاركه مع من يحتاج إلى استعادة شجاعته الوجودية."
        result += cta_text

    return result


def generate_deepdive_summary(
    output_dir: Path,
    transcript_source: Any,
    settings: Settings,
    metadata: dict[str, Any] | None = None,
    provider: str | None = None,
    model: str | None = None,
    override_text: str | None = None,
) -> Path:
    """Generate exhaustive deep-dive educational synthesis and save to deep_dive_summary.txt."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_file = output_dir / "deep_dive_summary.txt"

    # If pre-computed override is provided (e.g. Brainstorm mode), sanitize it strictly
    if override_text and override_text.strip():
        cleaned_override = sanitize_deepdive_text(override_text)
        dest_file.write_text(cleaned_override + "\n", encoding="utf-8")
        print(f"[DeepDive] Saved sanitized pre-computed synthesis to: {dest_file.name}", flush=True)
        return dest_file

    transcript_text = extract_transcript_text(transcript_source)
    if not transcript_text:
        # Check transcript.json in output_dir and parent
        for cand in [output_dir / "transcript.json", output_dir.parent / "transcript.json"]:
            if cand.is_file():
                t = extract_transcript_text(cand)
                if t:
                    transcript_text = t
                    break

    if not transcript_text:
        # Check manifest.json in output_dir or parent for metadata.transcript_text
        for cand in [output_dir / "manifest.json", output_dir.parent / "manifest.json"]:
            if cand.is_file():
                try:
                    m_data = json.loads(cand.read_text(encoding="utf-8"))
                    t = m_data.get("metadata", {}).get("transcript_text")
                    if t and str(t).strip():
                        transcript_text = str(t).strip()
                        break
                except Exception:
                    pass

    if not transcript_text:
        # Check for any *transcript*.txt in output_dir, parent, or outputs root
        for search_dir in [output_dir, output_dir.parent, output_dir.parent.parent]:
            if search_dir.is_dir():
                txt_cands = list(search_dir.glob("*transcript*.txt"))
                if txt_cands and txt_cands[0].is_file():
                    transcript_text = txt_cands[0].read_text(encoding="utf-8").strip()
                    if transcript_text:
                        break

    if not transcript_text:
        raise ValueError(f"Cannot generate deep-dive synthesis: No transcript found for {output_dir}")

    meta = metadata or {}
    title = meta.get("title") or meta.get("original_title") or output_dir.name
    channel = meta.get("channel") or meta.get("uploader") or ""
    video_desc = meta.get("description") or ""

    user_prompt = f"""
VIDEO GROUND TRUTH CONTEXT:
- Original Title: {title}
- Channel / Speaker: {channel}
- Source Description: {video_desc[:1200]}

FULL VIDEO TRANSCRIPT:
{transcript_text}

Transform this complete transcript into the required exhaustive deep-dive educational synthesis (ملخص معرفي مطوّل وشامل) in Modern Standard Arabic following all critical processing rules and required structural sections.
""".strip()

    active_provider = (provider or settings.llm_provider or "gemini").lower()
    print(f"[DeepDive] Generating Deep-Dive Educational Synthesis using provider: {active_provider}...", flush=True)

    result_text = ""

    if active_provider == "vyceai" and settings.vyceai_api_key:
        active_model = model or settings.vyceai_model or "claude-sonnet-4-6"
        result_text = _call_openai_compatible_api(
            settings.vyceai_base_url,
            settings.vyceai_api_key,
            active_model,
            DEEPDIVE_SYSTEM_PROMPT,
            user_prompt,
        )
    elif active_provider == "seekai" and settings.seekai_api_key:
        active_model = model or settings.seekai_model or "deepseek-v4-flash"
        result_text = _call_openai_compatible_api(
            settings.seekai_base_url,
            settings.seekai_api_key,
            active_model,
            DEEPDIVE_SYSTEM_PROMPT,
            user_prompt,
        )
    elif active_provider == "apinex" and settings.apinex_api_key:
        active_model = model or settings.apinex_model or "gpt-5.6-luna"
        result_text = _call_openai_compatible_api(
            settings.apinex_base_url,
            settings.apinex_api_key,
            active_model,
            DEEPDIVE_SYSTEM_PROMPT,
            user_prompt,
        )
    elif settings.gemini_api_key:
        active_model = model or settings.gemini_model or "gemini-3.5-flash"
        result_text = _call_gemini_api(
            settings.gemini_api_key,
            active_model,
            DEEPDIVE_SYSTEM_PROMPT,
            user_prompt,
        )
    elif settings.vyceai_api_key:
        active_model = model or settings.vyceai_model or "claude-sonnet-4-6"
        result_text = _call_openai_compatible_api(
            settings.vyceai_base_url,
            settings.vyceai_api_key,
            active_model,
            DEEPDIVE_SYSTEM_PROMPT,
            user_prompt,
        )
    else:
        raise RuntimeError("No configured API key found for Deep-Dive Synthesis (configure GEMINI_API_KEY or VyceAI in .env)")

    # Post-process cleanup and formatting via sanitize_deepdive_text
    cleaned = sanitize_deepdive_text(result_text)

    dest_file.write_text(cleaned + "\n", encoding="utf-8")
    print(f"[DeepDive] Successfully created: {dest_file.name} ({len(cleaned.split())} words, {len(cleaned)} characters)", flush=True)
    return dest_file
