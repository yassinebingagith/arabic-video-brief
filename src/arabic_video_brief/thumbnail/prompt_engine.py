"""Thumbnail package compatibility types and explicit legacy presets.

Production generate_thumbnail_package delegates to source_led; the old keyword
helpers below remain import-compatible but do not choose the default treatment.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .styles import STYLE_REGISTRY, VisualStyle, resolve_visual_style


class FocalArchetype(str, Enum):
    EMOTIVE_PORTRAIT = "emotive_portrait"
    SPLIT_COMPARISON = "split_comparison"
    SYMBOLIC_ARTIFACT = "symbolic_artifact"
    DRAMATIC_SCENE = "dramatic_scene"
    CONCEPTUAL_METAPHOR = "conceptual_metaphor"


@dataclass
class CuriosityVisualHint:
    """Represents a context-derived tangible visual clue and open-loop narrative trigger."""
    domain: str
    environmental_clue: str
    subject_state: str
    open_loop_explanation: str
    tangible_object: str = ""
    subject_action: str = ""
    foreground_clue: str = ""
    background_clue: str = ""
    core_metaphor: str = ""
    power_word: str = ""
    focal_archetype_override: str = ""
    style_override: str = ""


@dataclass
class ThumbnailPackage:
    video_title_ar: str
    visual_style: VisualStyle
    focal_archetype: str
    reference_thumbnail_path: Path | None

    # 4:5 Facebook Photo Post
    fb_strategy_summary: str
    fb_master_prompt: str
    fb_text_specs: dict[str, Any]

    # 9:16 TikTok / Shorts Cover
    vertical_strategy_summary: str
    vertical_master_prompt: str
    vertical_text_specs: dict[str, Any]

    # Enhanced Curiosity & Visual Gap Metadata
    curiosity_hint: CuriosityVisualHint | None = None
    source_modality: str = "photographic"


def format_dual_tone_title(title_ar: str, power_word_override: str = "") -> tuple[str, str, str]:
    """Extracts headline words and designates a primary emotional power-word for dual-tone styling.
    
    Filters out episode tags (e.g. 'الحلقة 6:', 'Episode 6:', '#6 -') while strictly preserving
    high-converting listicle numbers (e.g. '20 عادة', '7 أسرار', '5 خطوات').
    
    Returns:
        (clean_full_title, power_word, styling_instruction)
    """
    clean_title = title_ar.replace("{", "").replace("}", "").strip()
    # Strip ONLY leading episode prefixes with punctuation or explicit labels; NEVER strip listicle quantities like "20 عادة"
    clean_title = re.sub(
        r"^(?:#\d+[\.\-:\s]+|\d+[\.\-:]+\s*|(?:الحلقة|حلقة|episode|ep)[\.\-:\s]*\d+[\.\-:\s]*)",
        "",
        clean_title,
        flags=re.IGNORECASE,
    ).strip()
    # Clean brackets or parentheses around subtitle words (e.g. "(Anxiety)" -> "Anxiety")
    clean_title = clean_title.replace("(", "").replace(")", "").strip()
    words = clean_title.split()
    if not words:
        return clean_title, "", "Uniform bold white calligraphy"

    # Common Arabic particles, prepositions, pronouns and stopwords to avoid as power words
    stopwords = {
        "في", "من", "عن", "مع", "إلى", "على", "هل", "كيف", "لماذا", "ما", "ماذا",
        "أو", "ثم", "بل", "لا", "لن", "لم", "أن", "إن", "هذا", "هذه", "ذلك", "تلك",
        "الذي", "التي", "الذين", "كل", "جميع", "بين", "حول", "عند", "قبل", "بعد",
        "يوم", "اليوم", "إذا", "حتى", "هو", "هي", "هم", "نحن", "أنا", "أنت"
    }

    # Low-value channel/media terms and generic nouns to avoid as highlighted power words
    ignored_words = {
        "فارماستان", "بودكاست", "قناة", "فيديو", "حلقة", "مقطع", "برنامج",
        "دكتور", "الدكتور", "كابتن", "أستاذ", "الأستاذ", "مهندس",
        "عادة", "عادات", "طريقة", "طرق", "خطوات", "أسباب", "أشياء", "شخص", "شخصاً", "أشخاص"
    }

    # Curated high-impact emotional, cognitive & conceptual power keywords
    power_keywords = [
        "التروما", "تروما", "الصدمة", "صدمة", "الذكاء", "ذكاء", "الجينات", "جينات",
        "القلق", "الخوف", "الدماغ", "الوعي", "الفرص", "العالم", "السعادة", "النوم",
        "الحقيقة", "الوهم", "السر", "الأسرار", "الكورتيزول", "الدوبامين", "المال",
        "الثروة", "النجاح", "كارثة", "تدمير", "قوة", "سحر", "أسرع", "خطأ", "عقلك",
        "نفسك", "تشتت", "وحيد", "أخطر", "التفكير", "القرارات", "العلاقات", "الانضباط",
        "التركيز", "التسويف", "التحول", "الإرادة", "الذاكرة", "الإدراك", "الهوية"
    ]

    power_word = ""

    # Priority 0: Explicit power_word_override if present in the title
    if power_word_override:
        clean_override = re.sub(r"[^\w\s]", "", power_word_override).strip()
        for raw_w in words:
            clean_w = re.sub(r"[^\w\s]", "", raw_w).strip()
            if clean_override and (clean_override == clean_w or clean_override in clean_w or clean_w in clean_override):
                power_word = clean_w
                break

    # 1. First pass: look for exact/substring match with curated power keywords (excluding numbers & ignored words)
    if not power_word:
        for raw_w in words:
            clean_w = re.sub(r"[^\w\s]", "", raw_w).strip()
            if not clean_w or clean_w.isdigit() or len(clean_w) < 3 or clean_w in ignored_words:
                continue
            if any(pk == clean_w or pk in clean_w for pk in power_keywords):
                power_word = clean_w
                break

    # 2. Second pass: pick first substantive noun (>= 4 chars, not a stopword, not in ignored_words, not digit)
    if not power_word:
        for raw_w in words:
            clean_w = re.sub(r"[^\w\s]", "", raw_w).strip()
            if clean_w.isdigit() or len(clean_w) < 4:
                continue
            if clean_w not in stopwords and clean_w not in ignored_words:
                power_word = clean_w
                break

    # 3. Fallback to last meaningful word
    if not power_word:
        for raw_w in reversed(words):
            clean_w = re.sub(r"[^\w\s]", "", raw_w).strip()
            if not clean_w.isdigit() and len(clean_w) >= 3 and clean_w not in stopwords:
                power_word = clean_w
                break

    if not power_word:
        power_word = re.sub(r"[^\w\s]", "", words[0])

    styling_instruction = (
        f'Pure white (#FFFFFF) for the primary headline text, with the key emotional power-word "{power_word}" '
        f'highlighted in vivid luminous gold (#F5C518) or intense crimson (#FF3B30), '
        f'backed by a subtle soft dark drop-shadow for 100% razor-sharp legibility.'
    )
    return clean_title, power_word, styling_instruction


def detect_source_modality(
    reference_thumbnail_path: Path | None,
    title: str = "",
    description: str = "",
) -> str:
    """Detects whether the source visual is photographic or an artistic illustration."""
    combined = f"{title} {description}".lower()

    # Real human / interview priority: If the content represents a real person, interview, podcast, or lecture, ALWAYS photographic
    real_speaker_keys = [
        "interview", "full interview", "podcast", "big think", "talk", "talks", "conversation",
        "discussion", "lecture", "speaker", "guest", "host", "jonathan rauch", "jay shetty",
        "andrew huberman", "jordan peterson", "tim ferriss", "lex fridman", "دانيال بارادا",
        "مقابلة", "حوار", "بودكاست", "لقاء", "محاضرة", "محادثة", "ضيف", "محاور"
    ]
    if any(k in combined for k in real_speaker_keys):
        return "photographic"

    # Keywords strongly associated with illustrative/artistic storytelling channels and classical philosophy art
    artistic_keywords = [
        "carl jung", "shadow work", "anime", "drawn", "sketch", "painting", "oil painting",
        "watercolor", "digital art", "bygone philosophy", "eternalised", "einzelgänger",
        "pursuit of wonder", "academy of ideas", "the school of life", "sisyphus 55",
        "stoic", "stoicism", "sun tzu", "epictetus", "seneca", "marcus aurelius", "nietzsche",
        "schopenhauer", "fine art", "museum art", "رسم", "كرتون", "لوحة فنية", "لوحة زيتية", "رواقية",
        "strategist", "the mind of a strategist", "art of war", "استراتيجية", "استراتيجي"
    ]
    if any(k in combined for k in artistic_keywords):
        return "illustrated_artistic"

    if reference_thumbnail_path and reference_thumbnail_path.is_file():
        try:
            from PIL import Image, ImageStat
            with Image.open(reference_thumbnail_path) as img:
                rgb = img.convert("RGB")
                stat = ImageStat.Stat(rgb)
                # Illustrations/paintings often feature higher saturation variance or distinct edge profiles
                ext = reference_thumbnail_path.suffix.lower()
        except Exception:
            pass

    return "photographic"


def generate_llm_curiosity_concept(
    title: str,
    description: str = "",
    creative_plan: dict[str, Any] | None = None,
    speaker_name: str = "",
    modality: str = "photographic",
    settings: Any | None = None,
) -> CuriosityVisualHint | None:
    """Invokes the configured LLM to synthesize an authentic, high-CTR, 1-of-1 visual scene concept.
    
    Eliminates stock podcast microphone cliches and passive phone-scrolling tropes by analyzing
    the actual editorial pages and identifying tangible physical narrative tension.
    """
    try:
        import os
        if "PYTEST_CURRENT_TEST" in os.environ and not (creative_plan and creative_plan.get("force_llm_test")):
            return None

        from ..config import get_settings
        from ..v2.editorial import call_llm

        s = settings or get_settings()
        if not (s.gemini_api_key or s.vyceai_api_key or s.seekai_api_key or s.apinex_api_key):
            return None

        creative_plan = creative_plan or {}
        pages = creative_plan.get("pages", [])
        pages_text = "\n".join([
            f"Page {p.get('page', i+1)}: {p.get('text', '')}"
            for i, p in enumerate(pages) if isinstance(p, dict)
        ])
        voiceover = creative_plan.get("voiceover", {})
        tts_text = voiceover.get("tts_text", "") if isinstance(voiceover, dict) else ""
        conclusion = creative_plan.get("conclusion", {})
        conclusion_text = conclusion.get("text", "") if isinstance(conclusion, dict) else ""

        # Avoid redundant calls if there is insufficient editorial context (e.g. bare title only)
        if not pages_text and not description and not tts_text:
            return None

        system_prompt = (
            "You are an elite YouTube & short-form video Thumbnail Creative Director and visual narrative strategist. "
            "You design 15%+ CTR visual scenes for high-intellect content that create immense cognitive tension and curiosity gaps. "
            "Return strictly valid JSON only."
        )

        prompt = f"""
Analyze this video content and design the single most compelling, high-CTR, 1-of-1 thumbnail scene concept.

Video Title: {title}
Speaker / Channel: {speaker_name}
Summary & Script Pages:
{pages_text}
Voiceover Hook: {tts_text}
Conclusion: {conclusion_text}
Narrative Context / Description: {description[:1200]}

CREATIVE DIRECTIVES:
1. STRICTLY NO BORING PODCAST CLICHÉS: Never specify broadcast microphones, studio soundboards, acoustic wall panels, or talking head setups unless the video is explicitly about audio podcasting.
2. STRICTLY NO GENERIC PHONE-SCROLLING: If digital distraction or phones are mentioned as an obstacle or bad habit, do NOT show someone passively looking at a phone! Show the active, tangible countermeasure (e.g. phone locked under a heavy vintage book, or focus entirely on journaling/writing systems/reading/deep-work).
3. SPECIFIC TANGIBLE HERO OBJECT & INTERACTION:
   - Identify the single most concrete, intriguing physical prop or clue directly from the script (e.g. an open leather gap-sheet journal, an October habit roadmap, an ancestral heirloom photograph or fading family shadows, a weathered case dossier, an ancient parchment, etc.).
   - The subject must be actively interacting with, observing, or reacting to this tangible clue with genuine emotional tension or deep cognitive focus.
4. DRAMATIC LIGHTING & CINEMATIC REALISM:
   - Chiaroscuro lighting, warm amber tungsten key light with soft shadow wrap, rich atmospheric depth.
   - Strictly NO flat white studio walls, NO sterile passport backdrops.
5. SELECT THE BEST POWER WORD: Choose the single most emotionally charged, high-converting Arabic word from the title to be highlighted in gold/crimson (e.g. "الذكاء", "التروما", "الانضباط"). NEVER choose the channel name or generic words like "عادة" or "طريقة".

Return strictly valid JSON with this exact schema:
{{
  "domain": "string (slug identifier)",
  "focal_archetype": "dramatic_scene | conceptual_metaphor | symbolic_artifact | emotive_portrait",
  "environmental_clue": "string (detailed cinematic environment & lighting)",
  "subject_state": "string (posture, facial expression, emotional tension)",
  "tangible_object": "string (the specific hero prop or mystery clue)",
  "subject_action": "string (what the subject is physically doing)",
  "foreground_clue": "string (what is sharply in focus in the foreground)",
  "background_clue": "string (what is atmospheric in the background)",
  "open_loop_explanation": "string (why the viewer cannot scroll past without clicking)",
  "core_metaphor": "string (symbolic meaning of the scene)",
  "power_word": "string (the Arabic power-word to highlight)",
  "style_override": "cinematic | noir | hyper_real | minimalist"
}}
""".strip()

        raw_json = call_llm(prompt, s, system_prompt=system_prompt, temperature=0.3)
        match = re.search(r"(\{.*\})", raw_json, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            if data.get("environmental_clue") and data.get("tangible_object"):
                return CuriosityVisualHint(
                    domain=str(data.get("domain", "llm_concept")),
                    environmental_clue=str(data.get("environmental_clue", "")),
                    subject_state=str(data.get("subject_state", "")),
                    open_loop_explanation=str(data.get("open_loop_explanation", "")),
                    tangible_object=str(data.get("tangible_object", "")),
                    subject_action=str(data.get("subject_action", "")),
                    foreground_clue=str(data.get("foreground_clue", "")),
                    background_clue=str(data.get("background_clue", "")),
                    core_metaphor=str(data.get("core_metaphor", "")),
                    power_word=str(data.get("power_word", "")),
                    focal_archetype_override=str(data.get("focal_archetype", "")),
                    style_override=str(data.get("style_override", "")),
                )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("LLM curiosity concept generation failed: %s; using heuristic fallback", exc)
    return None


def extract_curiosity_visual_hint(
    title: str = "",
    description: str = "",
    creative_plan: dict[str, Any] | None = None,
    speaker_name: str = "",
    modality: str = "photographic",
    settings: Any | None = None,
) -> CuriosityVisualHint:
    """Analyzes context to generate a subtle, natural, and script-faithful visual curiosity cue.
    
    Embeds clues naturally into environment, background, or lighting—never forcing unnatural props.
    """
    creative_plan = creative_plan or {}
    
    # Priority 0: Custom Dynamic Concept from Creative Plan or Manifest (LLM-driven 1-of-1 design)
    custom_concept = creative_plan.get("thumbnail_concept") or creative_plan.get("visual_concept")
    if custom_concept and isinstance(custom_concept, dict):
        return CuriosityVisualHint(
            domain=custom_concept.get("domain", "custom_concept"),
            environmental_clue=custom_concept.get("environmental_clue", ""),
            subject_state=custom_concept.get("subject_state", ""),
            open_loop_explanation=custom_concept.get("open_loop_explanation", ""),
            tangible_object=custom_concept.get("tangible_object", ""),
            subject_action=custom_concept.get("subject_action", ""),
            foreground_clue=custom_concept.get("foreground_clue", ""),
            background_clue=custom_concept.get("background_clue", ""),
            core_metaphor=custom_concept.get("core_metaphor", ""),
            power_word=custom_concept.get("power_word", ""),
            focal_archetype_override=custom_concept.get("focal_archetype", "") or custom_concept.get("focal_archetype_override", ""),
            style_override=custom_concept.get("style_override", ""),
        )

    # Priority 1: Automated 1-of-1 Dynamic Conceptual Generation via LLM Architect
    llm_hint = generate_llm_curiosity_concept(
        title=title,
        description=description,
        creative_plan=creative_plan,
        speaker_name=speaker_name,
        modality=modality,
        settings=settings,
    )
    if llm_hint:
        creative_plan["thumbnail_concept"] = {
            "domain": llm_hint.domain,
            "environmental_clue": llm_hint.environmental_clue,
            "subject_state": llm_hint.subject_state,
            "open_loop_explanation": llm_hint.open_loop_explanation,
            "tangible_object": llm_hint.tangible_object,
            "subject_action": llm_hint.subject_action,
            "foreground_clue": llm_hint.foreground_clue,
            "background_clue": llm_hint.background_clue,
            "core_metaphor": llm_hint.core_metaphor,
            "power_word": llm_hint.power_word,
            "focal_archetype": llm_hint.focal_archetype_override,
            "style_override": llm_hint.style_override,
        }
        return llm_hint

    pages = creative_plan.get("pages", [])
    pages_text = " ".join([p.get("text", "") for p in pages if isinstance(p, dict)])
    voiceover = creative_plan.get("voiceover", {})
    tts_text = voiceover.get("tts_text", "") if isinstance(voiceover, dict) else ""
    conclusion = creative_plan.get("conclusion", {})
    conclusion_text = conclusion.get("text", "") if isinstance(conclusion, dict) else ""

    full_context = f"{title} {description} {pages_text} {tts_text} {conclusion_text}".lower()
    title_lower = title.lower()

    # 0a-0. Generational Trauma, Epigenetics & Inherited Psychological Wounds
    generational_keys = [
        "تروما", "التروما", "جينات", "عابرة للأجيال", "صدمة وراثية", "صدمات", "وراثة نفسية",
        "مشاكلك النفسية مش انت السبب", "epigenetics", "generational trauma", "inherited trauma", "family trauma", "childhood wounds"
    ]
    if any(k in full_context for k in generational_keys):
        return CuriosityVisualHint(
            domain="generational_trauma_epigenetics",
            environmental_clue=(
                "a dramatic, atmospheric psychological interior bathed in intense Caravaggio chiaroscuro side-lighting, "
                "with deep textured obsidian shadows, warm amber rim highlights, and subtle, haunting layered ancestral silhouettes "
                "softly dissolving into the background gloom. Strictly zero podcast microphones, zero acoustic panels, zero flat white walls"
            ),
            subject_state=(
                "seated in deep psychological introspection, looking forward with haunting vulnerability, poignant solemnity, and profound realization"
            ),
            open_loop_explanation=(
                "Visualizes the invisible genetic and psychological thread binding ancestral wounds to modern struggles, "
                "sparking intense curiosity about what we unknowingly inherit."
            ),
            tangible_object="an aged, weathered ancestral photograph catching a sharp beam of directional golden light",
            subject_action="contemplating the ancestral relic or looking forward with intense psychological realization",
            foreground_clue="a weathered wooden desk edge with an aged, tactile ancestral photograph catching a crisp amber rim light in the immediate foreground",
            background_clue="deep cavernous chiaroscuro shadows with subtle, haunting ancestral silhouettes softly dissolving into the background haze",
            core_metaphor="breaking the invisible inherited chain of generational psychological trauma",
            power_word="التروما",
            focal_archetype_override="dramatic_scene",
            style_override="cinematic",
        )

    # 0a-1. Cognitive Habits, Intelligence-Maxxing, Deep Work & Radical Transformation
    habits_keys = [
        "تعظيم الذكاء", "عادات", "إنتاجية", "تسويف", "انضباط", "تطوير الذات", "غير معروف",
        "intelligence", "maxxing", "unrecognisable", "productivity", "procrastination", "deep work", "discipline"
    ]
    if any(k in full_context for k in habits_keys):
        return CuriosityVisualHint(
            domain="cognitive_habits_productivity",
            environmental_clue=(
                "a moody, aesthetic contemporary deep-work sanctuary bathed in directional warm 2700K tungsten lamp light "
                "cutting through atmospheric twilight shadows, with clean negative space, tactile desk textures, and zero digital clutter"
            ),
            subject_state=(
                "seated at a minimalist wooden desk, pausing in razor-sharp intellectual focus while writing, "
                "with an intense expression of cognitive clarity and disciplined determination"
            ),
            open_loop_explanation=(
                "Visualizes the tangible discipline of radical mental restructuring—writing your daily systems and physically locking distractions away—"
                "sparking intense curiosity about how small daily frictions make you unrecognizable."
            ),
            tangible_object="an open tactile leather-bound journal ('The Gap Sheet') with handwritten rules and an ink pen resting on it, beside a smartphone deliberately locked under a heavy vintage hardcover book",
            subject_action="pausing thoughtfully with a pen over the open journal while in deep intellectual flow, with the phone silenced under a heavy book nearby",
            foreground_clue="an open tactile leather journal with handwritten notes and a fountain pen sharply lit by warm directional desk light in the immediate foreground",
            background_clue="a minimalist aesthetic study wall with a subtle habit calendar marked with checked-off days softly receding into warm bokeh",
            core_metaphor="the deliberate friction and written systems that forge radical cognitive transformation",
            power_word="الذكاء",
            focal_archetype_override="dramatic_scene",
            style_override="cinematic",
        )

    # 0a. Grief, Mortality, Loss of Loved Ones & Life After Death
    grief_keys = [
        "حداد", "الراحلين", "الموت الرحيم", "الحياة بعد الموت",
        "bereavement", "afterlife", "psychic medium", "talking to the dead", "what the dead"
    ]
    if any(k in full_context for k in grief_keys):
        return CuriosityVisualHint(
            domain="grief_loss_mortality",
            environmental_clue=(
                "a high-prestige, intimate cinematic conversation atmosphere with dramatic warm chiaroscuro key lighting, "
                "subtle acoustic studio depth, and rich velvety dark charcoal backdrop, drenched in profound emotional gravity"
            ),
            subject_state=(
                "an authentic, deeply contemplative expression filled with emotional vulnerability, serious presence, and quiet empathy"
            ),
            open_loop_explanation=(
                "Captures the profound emotional weight of confronting mortality and loss, "
                "inviting deep curiosity about what truly matters after someone departs."
            ),
            tangible_object="an intimate studio broadcast microphone with warm directional rim lighting",
            subject_action="engaged in an earnest, unguarded existential conversation",
            foreground_clue="a professional broadcast studio microphone or a warm amber rim-lit desk edge in the immediate foreground",
            background_clue="deep textured charcoal studio acoustic wall panels bathed in subtle warm amber edge light",
            core_metaphor="the intimate dialogue between mortality, love, and what endures beyond physical absence",
        )

    # 0b. AI Disruption, Career Obsolescence, Layoffs & Job Market
    # Must be the explicit primary topic of the video (title or strong multi-term match), NEVER triggering on a casual mention of 'career' or 'job'
    job_explicit_keys = [
        "سوق الشغل", "سوق العمل", "وظائف المستقبل", "عصر البطالة", "تسريح الموظفين", "أزمة وظائف", "فقدان الوظيفة",
        "layoff", "layoffs", "unemployment", "job market crisis", "losing your job", "future of jobs"
    ]
    is_job_topic = any(k in title_lower for k in job_explicit_keys) or (
        any(k in title_lower for k in ["وظيفة", "وظائف", "مهنة", "job", "career"]) and 
        any(k in full_context for k in ["تسريح", "بطالة", "أتمتة", "layoff", "unemployment", "severance"])
    )
    if is_job_topic:
        return CuriosityVisualHint(
            domain="ai_tech_job_market",
            environmental_clue=(
                "a contemporary open-plan corporate office interior with cool architectural glass partitions, soft ambient lighting, "
                "and an authentic workplace atmosphere under dramatic cinematic key lighting"
            ),
            subject_state=(
                "an authentic contemplative expression while seated at a modern desk, packing personal workplace belongings, filled with poignant relatable vulnerability"
            ),
            open_loop_explanation=(
                "Captures the stark reality of sudden workplace disruption in changing modern industries, "
                "inviting deep curiosity about career adaptation."
            ),
            tangible_object="a neatly placed desk box and an employee access lanyard badge resting on a modern desk",
            subject_action="seated at an office desk looking contemplative with personal items on the desk",
            foreground_clue="a modern office desk edge with an employee access badge lanyard and a subtle desk box in the immediate foreground",
            background_clue="a contemporary corporate office floor with deep blue architectural glass partitions and soft ambient workstation bokeh",
            core_metaphor="navigating unexpected professional transformation and industry shifts",
        )

    # 0c. Political Philosophy, Enlightenment, Liberalism & Freedom
    philosophy_keys = [
        "ليبرالية", "الليبرالية", "فلسفة سياسية", "استبداد", "ديمقراطية", "جون لوك",
        "liberalism", "political philosophy", "enlightenment", "constitution of knowledge"
    ]
    if any(k in full_context for k in philosophy_keys):
        return CuriosityVisualHint(
            domain="political_philosophy_enlightenment",
            environmental_clue=(
                "a dark, atmospheric private study and classical library gallery with deep mahogany wood paneling and moody chiaroscuro lighting, "
                "where framed historical Enlightenment oil portraits (John Locke, Adam Smith, Voltaire) hang in soft focus behind him, "
                "illuminated by warm museum accent lights. Strictly zero flat white walls, zero sterile void rooms"
            ),
            subject_state=(
                "seated thoughtfully in an elegant vintage leather armchair, engaged in calm, piercing intellectual discourse with authentic gravitas"
            ),
            open_loop_explanation=(
                "Captures the enduring debate on liberalism and human freedom through the living legacy of the Enlightenment, "
                "sparking intense intellectual curiosity."
            ),
            tangible_object="an elegant vintage leather armchair and a dark polished mahogany desk edge catching subtle warm rim lighting",
            subject_action="seated in calm, authoritative philosophical reflection and intellectual dialogue",
            foreground_clue="a dark polished mahogany desk edge or library table with warm subtle chiaroscuro amber rim light in the immediate foreground",
            background_clue="a dramatic gallery wall of framed classical Enlightenment oil portraits softly out of focus in a dark, moody mahogany-paneled library or study with warm museum picture lights",
            core_metaphor="the dialogue between modern liberty and Enlightenment philosophy against authoritarian darkness",
        )

    # 0c-1. Crime, Legal Cases, Courtroom, Scandals & True-Crime Investigation (Netflix / HBO Documentary Style)
    crime_keys = [
        "قضية", "جريمة", "جرائم", "محكمة", "تحقيق", "اعتداء", "فضيحة", "بلاغ", "شرطة", "سجن", "جنائية", "اتهام",
        "crime", "criminal", "trial", "scandal", "court", "police", "investigation", "assault", "felony",
        "allegation", "indictment", "true crime", "case file"
    ]
    if any(k in full_context for k in crime_keys):
        return CuriosityVisualHint(
            domain="crime_legal_investigation",
            environmental_clue=(
                "a dark, cinematic true-crime documentary environment (David Fincher / Netflix True-Crime aesthetic) "
                "with deep chiaroscuro shadows, cold slate-blue atmospheric rain-slicked haze, and subtle crimson "
                "emergency vehicle rim reflections slicing through the ominous twilight"
            ),
            subject_state=(
                "evoking tense secrecy, forensic seriousness, and high-stakes investigative gravity, observing the evidence with solemn focus"
            ),
            open_loop_explanation=(
                "Captures the tension of an unfolding criminal scandal and forensic investigation, inviting intense curiosity about the hidden truth."
            ),
            tangible_object="a weathered confidential case folder with forensic stamps and a warm desk lamp slicing through the gloom",
            subject_action="examining an investigative file under focused directional light in an atmospheric room",
            foreground_clue="a weathered official case dossier or evidence folder edge sharply lit in the immediate foreground",
            background_clue="the imposing silhouette of the institutional building or courthouse shrouded in cold misty rain and distant emergency amber/red glow",
            core_metaphor="the razor-thin line between hidden transgressions and public exposure",
        )

    # 0c-2. Political News, Geopolitics, Elections & Broadcast Journalism (TV News Agency / Breaking News Style)
    politics_news_keys = [
        "سياسة", "سياسي", "انتخابات", "عاجل", "أخبار", "رئيس", "حكومة", "وزير", "برلمان", "معاهدة",
        "مفاوضات", "دبلوماسية", "قمة", "أزمة دولية", "geopolitics", "election", "breaking news", "president",
        "diplomacy", "treaty", "parliament", "foreign affairs", "summit", "geopolitical"
    ]
    if any(k in full_context for k in politics_news_keys):
        return CuriosityVisualHint(
            domain="political_news_journalism",
            environmental_clue=(
                "a high-stakes international broadcast journalism environment with dramatic newsroom chiaroscuro lighting, "
                "deep navy and graphite broadcast backdrops, and focused studio spotlighting with an urgent breaking-news gravitas"
            ),
            subject_state=(
                "sharp, authoritative journalistic presence delivering critical global developments with urgency and profound seriousness"
            ),
            open_loop_explanation=(
                "Captures the pulse of breaking geopolitical developments and institutional power shifts."
            ),
            tangible_object="a sleek broadcast anchor desk edge and high-profile press microphones catching crisp directional rim light",
            subject_action="delivering or analyzing breaking news developments with authoritative focus",
            foreground_clue="a sleek broadcast studio desk or press briefing podium catching crisp directional tungsten rim light",
            background_clue="a dynamic world geopolitical data map display and architectural newsroom depth softly out of focus",
            core_metaphor="the high-stakes chess match of global politics and breaking historical developments",
        )

    # 0c-3. Explanatory, Science, Informative Schematics & Visual Breakdown (Infographic / Explanatory Clarity)
    explanatory_keys = [
        "كيف يعمل", "شرح مبسط", "شرح", "انفوجرافيك", "نظرية", "دليل شامل", "خوارزمية", "تبسيط",
        "how it works", "explained", "breakdown", "science of", "visualized", "infographic", "schematic", "mechanism"
    ]
    if any(k in full_context for k in explanatory_keys):
        return CuriosityVisualHint(
            domain="explanatory_informative_diagram",
            environmental_clue=(
                "a sleek, intellectual explanatory studio featuring high-contrast holographic concept diagrams, "
                "clean floating schematics, and elegant blackboard or digital studio clarity under crisp soft-box lighting"
            ),
            subject_state=(
                "an engaging, brilliant communicator gesturing with absolute clarity, breaking down complex phenomena into intuitive visual steps"
            ),
            open_loop_explanation=(
                "Demystifies complex unseen mechanics through intuitive visual clarity, sparking profound intellectual curiosity."
            ),
            tangible_object="a crisp luminous concept diagram or blueprint schematic cleanly integrated into the space",
            subject_action="explaining a pivotal concept with clear, authoritative gesture toward the visual scheme",
            foreground_clue="a crisp, glowing explanatory diagram, flowchart arrow, or conceptual blueprint element seamlessly in frame",
            background_clue="a clean, modern studio or lecture amphitheater with deep charcoal contrast and focused soft-box key light",
            core_metaphor="demystifying complex unseen mechanics through elegant conceptual clarity",
        )

    # 0d. Social Isolation, Friendship Recession, Loneliness & Human Connection
    social_keys = [
        "صداقة", "عزلة", "وحدة", "أصدقاء", "فراغ اجتماعي", "عزلة اجتماعية", "تواصل", "انعزال", "وحيد",
        "friendship", "friends", "loneliness", "isolation", "solitude", "recession",
        "social connection", "belonging", "community"
    ]
    if any(k in full_context for k in social_keys):
        if modality == "illustrated_artistic":
            return CuriosityVisualHint(
                domain="social_isolation_loneliness",
                environmental_clue=(
                    "a vast, poetic fine-art landscape evoking a solitary introspective journey: rich warm amber dunes or coastal path "
                    "contrasting against a deep atmospheric teal and twilight expanse, drenched in poignant emotional stillness"
                ),
                subject_state=(
                    "a contemplative, solitary traveler walking with quiet grace and reflective dignity into the open horizon"
                ),
                open_loop_explanation=(
                    "Captures the profound emotional paradox of modern life: surrounded by millions yet walking an intensely solitary path, "
                    "inviting deep curiosity about the silent loss of authentic human connection."
                ),
                tangible_object="a solitary winding path or single footprints stretching toward an open horizon",
                subject_action="walking in quiet reflection along an expansive landscape",
                foreground_clue="single, deliberate footprints or a weathered path edge sharply textured in the immediate foreground",
                background_clue="an immense, evocative horizon where warm earth meets deep atmospheric ocean or twilight sky",
                core_metaphor="the solitary journey through a hyper-connected yet emotionally isolated world",
            )
        else:
            return CuriosityVisualHint(
                domain="social_isolation_loneliness",
                environmental_clue=(
                    "a moody, atmospheric urban terrace or quiet café at blue hour twilight, with warm interior amber glow "
                    "softly contrasting against cool exterior shadows, evoking the quiet space between solitude and belonging"
                ),
                subject_state=(
                    "a natural, grounded posture gazing into the distance with thoughtful, authentic emotional depth"
                ),
                open_loop_explanation=(
                    "Visualizes the silent modern epidemic of adult isolation and the search for authentic connection."
                ),
                tangible_object="a single warm coffee cup resting on an outdoor table under twilight sky",
                subject_action="seated or standing in quiet contemplation looking into the soft evening distance",
                foreground_clue="a textured wooden tabletop or terrace railing softly blurred in the immediate foreground",
                background_clue="subtle city twilight bokeh and gentle window lights glowing in the distance",
                core_metaphor="solitary reflection amid the bustling modern world",
            )

    # 1. Digital Dopamine, Screens, Smartphone Addiction & Screen Traps (High Priority)
    digital_keys = [
        "شاشات", "عالم رقمي", "رقمي", "هاتف", "دوبامين", "خوارزميات", "تطبيقات", "تصفح",
        "إنترنت", "إدمان الهاتف", "screen", "screens", "smartphone", "phone", "dopamine",
        "digital", "algorithm", "social media", "scroll", "internet"
    ]
    if any(k in full_context for k in digital_keys):
        return CuriosityVisualHint(
            domain="digital_dopamine_tech",
            environmental_clue=(
                "a dark, atmospheric contemporary interior where the cold, ethereal blue-white glow of a sleek smartphone screen "
                "illuminates the subject's contemplative face from below, with subtle notification light casting high-tech chiaroscuro contrast against deep shadows"
            ),
            subject_state=(
                "a natural, grounded posture—either looking slightly downward toward the glowing smartphone held naturally in hand, "
                "or looking up in profound reflection while the illuminated phone rests quietly on the desk beside them"
            ),
            open_loop_explanation=(
                "Visualizes the hidden biological tension between digital algorithms and neural exhaustion, "
                "provoking an immediate cognitive curiosity about how modern screens silently rob us of happiness."
            ),
            tangible_object="a sleek modern smartphone casting an intense ethereal blue-white screen glow in a dim room",
            subject_action="naturally observing the glowing smartphone screen in deep reflection",
            foreground_clue="a sleek modern smartphone resting on a dark wooden desk edge, casting a cold ethereal blue-white glow into the foreground",
            background_clue="a contemporary atmospheric interior with soft deep shadows and subtle warm ambient accent light in the distance",
            core_metaphor="the silent biological friction between algorithms and human peace",
        )

    # 1b. Strategy, Chess, Master Tacticians, Sun Tzu & Mind of a Strategist
    strategy_keys = [
        "شطرنج", "بيدق", "بيادق", "كش ملك", "رقعة", "فيليدور", "وزير الشطرنج", "استراتيجية", "استراتيجي", "تكتيك", "صن تزو", "فن الحرب",
        "chess", "pawn", "pawns", "chessboard", "checkmate", "endgame", "grandmaster", "gambit",
        "strategist", "strategy", "sun tzu", "art of war", "tactics", "grand strategy", "bygone philosophy"
    ]
    if any(k in full_context for k in strategy_keys):
        if modality in ("illustrated_artistic", "fine_art_oil"):
            return CuriosityVisualHint(
                domain="classical_strategy_fine_art",
                environmental_clue=(
                    "a moody, atmospheric 19th-century private study rendered in a masterwork classical oil painting style on textured canvas. "
                    "Dramatic Caravaggio chiaroscuro side-lighting casts deep umber and golden amber tones across a dark mahogany table, "
                    "with aged strategic maps, rolled manuscripts, and a weathered handcrafted wooden chessboard in deep concentration"
                ),
                subject_state=(
                    "a profound master strategist seated in contemplative quiet genius, head resting thoughtfully near the chessboard, "
                    "with deep expressive brushstrokes capturing profound intellectual depth and silent stoic mastery"
                ),
                open_loop_explanation=(
                    "Visualizes the supreme paradox of the true strategist: quiet observation and fluid patience reigning over brute force, "
                    "inviting deep curiosity about how master minds think five moves ahead."
                ),
                tangible_object="a masterfully carved wooden chess piece and aged parchment campaign map on a textured canvas",
                subject_action="seated over the chessboard in deep stoic calculation and silent strategic mastery",
                foreground_clue="a finely carved wooden chess piece in warm chiaroscuro rim lighting on the edge of the chessboard in the immediate foreground",
                background_clue="a dark, moody classical library study with textured oil paint glazes, dim candlelight, and faint parchment maps in the background",
                core_metaphor="the fluid mind of the master strategist anticipating unseen moves before the battle begins",
            )
        else:
            return CuriosityVisualHint(
                domain="chess_strategy",
                environmental_clue=(
                    "a dark, moody grandmaster chessboard surface with polished dark wood or reflective black obsidian marble squares, "
                    "bathed in dramatic chiaroscuro side-lighting and atmospheric haze, highlighting the silent tension between strategy and fate"
                ),
                subject_state=(
                    "focused strategic mastery, contemplating the chessboard with deep calculating intelligence and psychological resolve"
                ),
                open_loop_explanation=(
                    "Visualizes the profound paradox of the chessboard: how the humblest pawn holds the ultimate power of transformation and strategic victory."
                ),
                tangible_object="a masterfully carved, tactile chess pawn standing in the warm spotlight beside the looming shadow of the queen",
                subject_action="contemplating the pivotal chess piece on the board with absolute strategic clarity",
                foreground_clue="a masterfully carved tactile chess pawn standing prominently in the warm foreground spotlight",
                background_clue="an expansive grandmaster chessboard surface with the looming silhouette of the queen softly blurred in the background haze",
                core_metaphor="the unexpected power and transformation of the humblest piece on the board",
            )

    # 2. Relationship Boundaries, Emotional Closure, Second Chances & Letting Go (No hardcoded philosopher names)
    relationship_keys = [
        "فرص ثانية", "تسامح", "علاقات", "خذلان", "شريك", "انفصال", "تضحية عاطفية", "حدود شخصية", "حدود",
        "استنزاف", "second chance", "boundaries", "toxic", "letting go",
        "breakup", "relationship", "narcissist", "closure"
    ]
    if any(k in full_context for k in relationship_keys):
        if modality == "illustrated_artistic":
            return CuriosityVisualHint(
                domain="relationship_boundaries",
                environmental_clue=(
                    "a poetic, atmospheric architectural threshold where warm golden evening light meets cool slate shadows, "
                    "symbolizing firm personal boundaries, emotional clarity, and peaceful detachment"
                ),
                subject_state=(
                    "a calm, resolute figure standing with quiet dignity and unshakeable self-worth, gazing forward with serene closure"
                ),
                open_loop_explanation=(
                    "Captures the decisive emotional tipping point where self-respect replaces false hope, "
                    "posing the silent question of what happens when you finally stop saving others."
                ),
                tangible_object="a distinct architectural arch or doorway dividing warm light from cool shadow",
                subject_action="standing with calm emotional resolve at the threshold, facing forward",
                foreground_clue="a subtle stone threshold or architectural doorway frame in the foreground",
                background_clue="an open, tranquil golden-hour twilight horizon glowing in the background",
                core_metaphor="standing at the threshold between past tolerance and self-respect",
            )
        else:
            return CuriosityVisualHint(
                domain="relationship_boundaries",
                environmental_clue=(
                    "a quiet, moody room threshold where warm golden evening light meets cold slate shadow, "
                    "evoking a firm personal boundary and the calm dignity of walking away from toxic cycles"
                ),
                subject_state=(
                    "a calm, resolute posture with steady, unwavering eye contact that projects emotional maturity and unshakeable self-worth"
                ),
                open_loop_explanation=(
                    "Visualizes the decisive psychological line between healthy compassion and self-destructive tolerance."
                ),
                tangible_object="a stark doorway dividing warm evening light from cold shadow",
                subject_action="standing with quiet dignity at the threshold, looking forward with calm resolve",
                foreground_clue="a stark doorway edge dividing warm evening light from cold shadow",
                background_clue="a quiet, moody interior softly dissolving into twilight shadow",
                core_metaphor="the decisive psychological line between healthy compassion and self-destructive tolerance",
            )

    # 3. Existential Anxiety, Fear of Freedom & The Inner Abyss
    anxiety_keys = [
        "قلق", "وجودي", "سارتر", "كيركغارد", "حرية", "فراغ", "هاوية", "دوار الحرية", "خوف", "هلع", "توتر",
        "anxiety", "existential", "abyss", "dread", "freedom", "vertigo", "sartre", "kierkegaard", "panic"
    ]
    if any(k in full_context for k in anxiety_keys):
        return CuriosityVisualHint(
            domain="existential_anxiety",
            environmental_clue=(
                "a dramatic, moody cinematic space with intense chiaroscuro engulfed in deep obsidian shadows and atmospheric haze, "
                "with a single focused slash of high-contrast amber and tungsten side-light slicing through the darkness, "
                "evoking the silent, overwhelming weight of the racing mind against an endless psychological abyss. "
                "STRICTLY NO flat white studio walls, NO passport photo backdrops"
            ),
            subject_state=(
                "visceral introspective tension and raw psychological vulnerability—eyes wide with intense contemplation, "
                "partially shrouded in dramatic chiaroscuro shadows with zero artificial props"
            ),
            open_loop_explanation=(
                "Captures the profound vertigo of freedom and existential dread, confronting the viewer with the raw psychological reality of unmasked choice."
            ),
            tangible_object="a single high-contrast beam of light cutting through thick, moody atmospheric shadow",
            subject_action="caught in a moment of visceral contemplation within dramatic chiaroscuro shadow",
            foreground_clue="a dramatic architectural edge cutting through the immediate foreground, catching a razor-sharp slash of amber side-light",
            background_clue="cavernous cinematic space engulfed in velvety chiaroscuro shadows and atmospheric dust motes",
            core_metaphor="the dizzying vertigo of unconstrained freedom and choice",
        )

    # 4. Health, Deep Sleep, Night Metabolism & Bedtime Rituals (Specific Sleep Context Only)
    sleep_keys = [
        "نوم عميق", "قبل النوم", "حرق دهون", "كورتيزول ليلاً", "مغنيسيوم غلايسينات", "عشاء",
        "bedtime", "sleep", "belly fat", "overnight", "fat burn", "night ritual"
    ]
    if any(k in full_context for k in sleep_keys):
        return CuriosityVisualHint(
            domain="health_sleep_metabolism",
            environmental_clue=(
                "a serene, dimly lit evening bedroom sanctuary bathed in warm 2700K ambient lamplight, "
                "with a subtle bedside table resting in soft bokeh showing a minimalist evening clock set to late evening (10:45 PM)"
            ),
            subject_state=(
                "standing or sitting in quiet evening relaxation, looking toward the viewer with medical authority and calm certainty"
            ),
            open_loop_explanation=(
                "Visually signals a specific nighttime biological trigger that activates overnight metabolic recovery."
            ),
            tangible_object="a warm artisanal evening tea cup beside a subtle bedside clock set to 10:45 PM",
            subject_action="resting a hand near the evening nightstand with a look of calm scientific certainty",
            foreground_clue="an artisanal warm evening tea cup on a nightstand in soft foreground focus",
            background_clue="a calm bedroom sanctuary bathed in 2700K warm lamplight with a minimalist clock showing 10:45 PM",
            core_metaphor="unlocking nighttime metabolic restoration",
        )

    # 5. Psychology, Thinking Fast and Slow, Cognitive Bias & Decision Making
    psych_keys = [
        "تفكير سريع", "تفكير بطيء", "قرارات", "انحياز", "كانيمان", "عقل", "دماغ",
        "fast and slow", "bias", "kahneman", "decision", "cognitive", "mindset", "subconscious"
    ]
    if any(k in full_context for k in psych_keys):
        return CuriosityVisualHint(
            domain="psychology_decision",
            environmental_clue=(
                "a moody, atmospheric intellectual study with dramatic side chiaroscuro lighting, "
                "an uncluttered wooden desk with subtle optical reflection, visualizing dual cognitive systems"
            ),
            subject_state=(
                "deep analytical focus, looking forward with razor-sharp perceptual clarity and intense psychological discernment"
            ),
            open_loop_explanation=(
                "Materializes the invisible cognitive blind spot that silently dictates human choices."
            ),
            tangible_object="a pristine minimalist desk illuminated by a sharp beam of analytical side-light",
            subject_action="observing the viewer with piercing analytical focus",
            foreground_clue="an uncluttered desk surface with clean optical reflections catching a crisp beam of analytical light",
            background_clue="a rich intellectual study or archival bookshelves bathed in soft chiaroscuro rim lighting",
            core_metaphor="illuminating the hidden cognitive blind spots of human judgment",
        )

    # 6. Wealth, Investing, Money, Leverage & Business Strategy
    wealth_keys = [
        "مال", "ثروة", "استثمار", "أعمال", "شركة", "مشروع", "أموال", "غني", "فقر",
        "صفقة", "مفاوضات", "business", "money", "wealth", "invest", "millionaire", "capital", "leverage"
    ]
    if any(k in full_context for k in wealth_keys):
        return CuriosityVisualHint(
            domain="wealth_finance",
            environmental_clue=(
                "an executive boardroom or high-rise office at twilight, sleek dark mahogany surfaces, "
                "subtle architectural blueprint resting on the table, dramatic city skyline bokeh in the background"
            ),
            subject_state=(
                "calm commanding executive authority, leaning slightly forward with decisive intent"
            ),
            open_loop_explanation=(
                "Visualizes asymmetric competitive leverage and strategic clarity without giving away the exact trade."
            ),
            tangible_object="a dark mahogany desk with a subtle strategic document under warm directional lamp light",
            subject_action="leaning forward with calm, decisive executive authority",
            foreground_clue="a dark mahogany executive desk corner with a subtle strategic document in sharp focus",
            background_clue="a twilight high-rise skyline with dramatic architectural glass reflections in the distance",
            core_metaphor="asymmetric leverage and executive clarity",
        )

    # 7. History, Empires, Ancient Civilizations & Forgotten Turning Points
    history_keys = [
        "تاريخ", "حضارة", "سقوط", "معركة", "إمبراطورية", "ملك", "فيلسوف", "قديم", "أسرار",
        "روما", "يونان", "عصر", "history", "ancient", "civilization", "empire", "war", "collapse"
    ]
    if any(k in full_context for k in history_keys):
        return CuriosityVisualHint(
            domain="history_ancient",
            environmental_clue=(
                "weathered architectural stone textures, ancient parchment or relic illuminated under a focused warm beam of light"
            ),
            subject_state=(
                "scholarly gravitas and historical depth, examining historical truth with focused intensity"
            ),
            open_loop_explanation=(
                "Hints that a forgotten historical crisis holds the uncanny answer to a modern dilemma."
            ),
            tangible_object="an ancient weathered stone relic illuminated by a sharp beam of golden light",
            subject_action="observing the relic with deep scholarly gravitas",
            foreground_clue="weathered ancient stone carving or aged parchment relic with tactile surface cracks",
            background_clue="classical architectural arches and sunbeams piercing through dusty atmospheric air",
            core_metaphor="rediscovering timeless historical truth to solve modern dilemmas",
        )

    # 8. Universal / Personal Transformation (Grounded Fallback)
    return CuriosityVisualHint(
        domain="personal_transformation",
        environmental_clue=(
            "a textured, atmospheric architectural setting with cinematic directional lighting, rich negative space, and deep natural contrast"
        ),
        subject_state=(
            "steady, purposeful gaze with genuine emotional gravitas and completely natural body language"
        ),
        open_loop_explanation=(
            "Poses the fundamental question of personal breakthrough, timing, and direction."
        ),
        tangible_object="dramatic cinematic directional lighting creating bold atmospheric shadows",
        subject_action="looking directly forward with unwavering focus and emotional depth",
        foreground_clue="a textured architectural frame or tactile natural element in the immediate foreground adding cinematic depth",
        background_clue="an expansive, evocative horizon bathed in dramatic directional light and rich negative space",
        core_metaphor="the decisive moment of personal breakthrough",
    )


def resolve_focal_archetype(
    title: str = "",
    description: str = "",
    creative_plan: dict[str, Any] | None = None,
    has_speaker: bool = False,
    has_ref_image: bool = False,
    user_preference: str | None = None,
    hint: CuriosityVisualHint | None = None,
    speaker_name: str = "",
    modality: str = "photographic",
) -> tuple[FocalArchetype, str]:
    """Dynamically determines the most compelling visual focal archetype and generates a recipe."""
    if hint is None:
        hint = extract_curiosity_visual_hint(title, description, creative_plan, speaker_name, modality)

    if user_preference:
        pref = user_preference.strip().lower()
        for arch in FocalArchetype:
            if pref in arch.value or arch.value in pref:
                return arch, _get_archetype_recipe(arch, has_speaker, hint, speaker_name, modality)

    if hint and hint.focal_archetype_override:
        arch_ov = hint.focal_archetype_override.strip().lower()
        for arch in FocalArchetype:
            if arch_ov == arch.value or arch_ov in arch.value or arch.value in arch_ov:
                return arch, _get_archetype_recipe(arch, has_speaker, hint, speaker_name, modality)

    combined = f"{title} {description}".lower()
    title_lower = title.lower()
    creative_plan = creative_plan or {}
    visual_ideas = str(creative_plan.get("pages", "")) + " " + str(creative_plan.get("hook", ""))
    full_context = f"{combined} {visual_ideas}".lower()

    # 1. Split-Screen Comparison (ONLY when the title itself explicitly establishes a side-by-side dichotomy)
    split_explicit = [" vs ", " versus ", " vs. ", "قبل وبعد", "مقارنة بين", "الفرق بين", " before vs ", " before and after "]
    if any(k in title_lower for k in split_explicit):
        return FocalArchetype.SPLIT_COMPARISON, _get_archetype_recipe(FocalArchetype.SPLIT_COMPARISON, has_speaker, hint, speaker_name, modality)

    # 2. Fine Art Oil / Classical Philosophy / Strategy Scene
    if modality in ("illustrated_artistic", "fine_art_oil") or hint.domain in ("classical_strategy_fine_art", "political_philosophy_enlightenment"):
        return FocalArchetype.DRAMATIC_SCENE, _get_archetype_recipe(FocalArchetype.DRAMATIC_SCENE, has_speaker, hint, speaker_name, modality)

    # 2b. True-Crime Investigation, Courtroom Scandals & Political News Scenes (Netflix / HBO / Breaking News)
    if hint.domain in ("crime_legal_investigation", "political_news_journalism"):
        return FocalArchetype.DRAMATIC_SCENE, _get_archetype_recipe(FocalArchetype.DRAMATIC_SCENE, has_speaker, hint, speaker_name, modality)

    # 2c. Explanatory Schematics & Educational Breakdowns (Informative Diagrams)
    if hint.domain == "explanatory_informative_diagram":
        return FocalArchetype.CONCEPTUAL_METAPHOR, _get_archetype_recipe(FocalArchetype.CONCEPTUAL_METAPHOR, has_speaker, hint, speaker_name, modality)

    # 3. Symbolic Centerpiece (when the core concept is centered around an iconic object)
    if any(k in title_lower for k in ["شطرنج", "بيدق", "chess", "pawn", "gambit", "checkmate", "رمز", "تمثال", "أيقونة", "symbol", "monument", "sculpture"]):
        return FocalArchetype.SYMBOLIC_ARTIFACT, _get_archetype_recipe(FocalArchetype.SYMBOLIC_ARTIFACT, has_speaker, hint, speaker_name, modality)

    # 4. Dramatic Storytelling Scene
    if any(k in full_context for k in ["حضارة", "معركة", "سقوط", "مدينة", "تاريخ", "war", "collapse", "civilization", "empire", "journey"]):
        return FocalArchetype.DRAMATIC_SCENE, _get_archetype_recipe(FocalArchetype.DRAMATIC_SCENE, has_speaker, hint, speaker_name, modality)

    # 5. Mind-Bending Conceptual Metaphor
    if any(k in full_context for k in ["وهم", "مصفوفة", "حقيقة", "paradox", "matrix", "illusion", "existential"]):
        return FocalArchetype.CONCEPTUAL_METAPHOR, _get_archetype_recipe(FocalArchetype.CONCEPTUAL_METAPHOR, has_speaker, hint, speaker_name, modality)

    # 6. Default: Emotive Portrait (Most powerful CTR for human psychology, health & personal advice)
    return FocalArchetype.EMOTIVE_PORTRAIT, _get_archetype_recipe(FocalArchetype.EMOTIVE_PORTRAIT, has_speaker, hint, speaker_name, modality)


def _get_archetype_recipe(
    archetype: FocalArchetype,
    has_speaker: bool,
    hint: CuriosityVisualHint,
    speaker_name: str = "",
    modality: str = "photographic",
) -> str:
    """Returns detailed subject composition instructions embedding natural, unforced environmental cues."""
    is_object_centerpiece = (archetype == FocalArchetype.SYMBOLIC_ARTIFACT or hint.domain == "chess_strategy")
    speaker_tag = f"the central figure (modeled on the likeness and setting of {speaker_name})" if (has_speaker and speaker_name and not is_object_centerpiece) else "an intensely compelling, authentic focal subject"

    fg_line = f"- Foreground Contextual Depth: {hint.foreground_clue}.\n" if hint.foreground_clue else ""
    bg_line = f"- Background Environmental Horizon: {hint.background_clue}.\n" if hint.background_clue else ""

    if modality in ("illustrated_artistic", "fine_art_oil"):
        return (
            f"Classical Fine Art Masterpiece & Atmospheric Harmony (Oil Painting / Fine Art Modality):\n"
            f"A museum-grade classical oil painting composition faithfully mirroring the artistic spirit, impasto texture, and emotional gravitas of the reference image.\n"
            f"{fg_line}"
            f"- Classical Setting & Mood: {hint.environmental_clue}.\n"
            f"- Central Subject & Masterful Posture: {hint.subject_state}.\n"
            f"{bg_line}"
            f"- Visual Curiosity Gap & Open Loop: {hint.open_loop_explanation}.\n"
            f"Rendered as a masterwork oil-on-canvas with visible expressive brushstrokes, warm Caravaggio-style chiaroscuro, rich umber and antique amber glazes. "
            f"STRICTLY FORBIDDEN: Zero modern office clothing, zero corporate stock photo stiffness, zero plastic CGI gloss, and zero modern electronics."
        )

    if archetype == FocalArchetype.SPLIT_COMPARISON:
        return (
            f"Split-Screen Visual Dichotomy & Dynamic Contrast:\n"
            f"Divide the canvas into two distinctly contrasting states or perspectives separated by natural environmental atmosphere:\n"
            f"{fg_line}"
            f"- Side A (The Dilemma / Misconception): captures the constrained, anxious, or unexamined state, naturally reflecting the video's theme.\n"
            f"- Side B (The Resolution / Truth): captures clarity, mastery, and grounded perspective.\n"
            f"- The Central Focal Subject: {speaker_tag} stands as the thematic bridge, displaying {hint.subject_state}.\n"
            f"{bg_line}"
            f"Visual Curiosity Gap: {hint.open_loop_explanation}"
        )

    if archetype == FocalArchetype.SYMBOLIC_ARTIFACT:
        if hint.domain == "chess_strategy":
            return (
                f"Master Chessboard Artifact & Grandmaster Lighting:\n"
                f"{fg_line}"
                f"A cinematic, tangible centerpiece on the board: {hint.tangible_object}.\n"
                f"Atmosphere & Board Setting: {hint.environmental_clue}.\n"
                f"{bg_line}"
                f"Visual Curiosity Gap: {hint.open_loop_explanation}\n"
                f"Rendered with realistic physical textures, authentic wood or marble grain, volumetric rim lighting, and zero generic CGI gloss."
            )
        return (
            f"Grounded Environmental Centerpiece with Natural Presence:\n"
            f"{fg_line}"
            f"A hyper-detailed, tangible symbol naturally integrated into the environment: {hint.tangible_object}.\n"
            f"Setting & Atmosphere: {hint.environmental_clue}.\n"
            f"{bg_line}"
            f"Visual Curiosity Gap: {hint.open_loop_explanation}\n"
            f"Rendered with realistic physical textures, volumetric rim lighting, and zero generic CGI gloss."
        )

    if archetype == FocalArchetype.DRAMATIC_SCENE:
        return (
            f"Cinematic Storytelling Scene & Dramatic Environment:\n"
            f"{fg_line}"
            f"A high-stakes cinematic narrative tableau. {speaker_tag} is captured in a textured, atmospheric environment: {hint.environmental_clue}.\n"
            f"Natural Human Expression: {hint.subject_state}.\n"
            f"{bg_line}"
            f"Visual Curiosity Gap: {hint.open_loop_explanation}"
        )

    if archetype == FocalArchetype.CONCEPTUAL_METAPHOR:
        return (
            f"Grounded Conceptual Metaphor & Cognitive Tension:\n"
            f"{fg_line}"
            f"An enigmatic yet photorealistic physical manifestation of inner tension: {hint.environmental_clue}.\n"
            f"Subject Grounding: {speaker_tag} is captured with authentic introspection ({hint.subject_state}).\n"
            f"{bg_line}"
            f"Visual Curiosity Gap: {hint.open_loop_explanation}"
        )

    # Default EMOTIVE_PORTRAIT (Photographic Modality)
    return (
        f"Grounded Introspective Portrait & Environmental Clue (Photographic Modality):\n"
        f"A cinematic 35mm portrait of {speaker_tag}, captured with piercing, unwavering eye contact and authentic emotional gravitas.\n"
        f"{fg_line}"
        f"- Natural Subject Posture (Zero Forced Hand-Props): {hint.subject_state}.\n"
        f"- Environmental Visual Clue: {hint.environmental_clue}.\n"
        f"{bg_line}"
        f"- Visual Curiosity Gap & Open Loop: {hint.open_loop_explanation}.\n"
        f"Camera & Depth: Shot on 35mm master cinema prime at f/1.8 with creamy optical bokeh, Rembrandt side-lighting, "
        f"rendering authentic skin pores, natural hair strands, and real fabric textures in razor-sharp photorealistic clarity."
    )


def generate_thumbnail_package(
    post_title_ar: str,
    manifest_data: dict[str, Any] | None = None,
    creative_plan: dict[str, Any] | None = None,
    reference_thumbnail_path: Path | None = None,
    style_preference: str | None = None,
    archetype_preference: str | None = None,
) -> ThumbnailPackage:
    """Build source-led covers without the legacy keyword/style/prop presets."""
    from .source_led import build_source_led_package
    return build_source_led_package(
        post_title_ar, manifest_data, creative_plan, reference_thumbnail_path,
        style_preference, archetype_preference,
    )


def save_thumbnail_prompts(
    package: ThumbnailPackage,
    output_dir: Path,
    include_facebook: bool = True,
) -> tuple[Path | None, Path, Path]:
    """Saves prompt files and a comprehensive README/guide into the output folder."""
    output_dir.mkdir(parents=True, exist_ok=True)

    fb_file: Path | None = None
    if include_facebook:
        fb_file = output_dir / "thumbnail_prompt_facebook_4x5.txt"
    else:
        stale_fb = output_dir / "thumbnail_prompt_facebook_4x5.txt"
        if stale_fb.is_file():
            try:
                stale_fb.unlink()
            except Exception:
                pass

    vertical_file = output_dir / "thumbnail_prompt_vertical_9x16.txt"
    readme_file = output_dir / "THUMBNAIL_GUIDE.md"

    hint = package.curiosity_hint

    # 1. Facebook 4:5 Prompt File (only if include_facebook is True)
    if include_facebook and fb_file:
        fb_content = f"""================================================================================
SOURCE-LED HYBRID THUMBNAILS — FACEBOOK PHOTO POST (4:5 ASPECT RATIO)
================================================================================

[STRATEGY SUMMARY]
{package.fb_strategy_summary}

[VISUAL STYLE & ARCHETYPE]
Style: {package.visual_style.name}
Archetype: {package.focal_archetype.replace('_', ' ').title()}
Modality: {package.source_modality.replace('_', ' ').title()}
Curiosity Domain: {hint.domain if hint else 'universal'}
Environmental Clue: {hint.environmental_clue if hint else 'Contextual scene atmosphere'}

{package.fb_master_prompt}

================================================================================
MANUAL TEXT OVERLAY FALLBACK SPECS:
- Title (Top): {package.fb_text_specs['headline_arabic']}
- Highlighted Power-Word: {package.fb_text_specs['power_word_highlighted']}
- Font Recommendation: {package.fb_text_specs['font_recommendation']}
- Styling: {package.fb_text_specs['typography_styling']}
- Position: {package.fb_text_specs['header_position']}
- Bottom Badge: {package.fb_text_specs['footer_specs']}
================================================================================
"""
        fb_file.write_text(fb_content, encoding="utf-8")

    # 2. TikTok / Shorts 9:16 Prompt File
    vertical_content = f"""================================================================================
SOURCE-LED HYBRID THUMBNAILS — TIKTOK & SHORTS COVER (9:16 ASPECT RATIO)
================================================================================

[STRATEGY SUMMARY]
{package.vertical_strategy_summary}

[VISUAL STYLE & ARCHETYPE]
Style: {package.visual_style.name}
Archetype: {package.focal_archetype.replace('_', ' ').title()}
Modality: {package.source_modality.replace('_', ' ').title()}
Curiosity Domain: {hint.domain if hint else 'universal'}
Environmental Clue: {hint.environmental_clue if hint else 'Contextual scene atmosphere'}

{package.vertical_master_prompt}

================================================================================
MANUAL TEXT OVERLAY FALLBACK SPECS:
- Title (Top): {package.vertical_text_specs['headline_arabic']}
- Highlighted Power-Word: {package.vertical_text_specs['power_word_highlighted']}
- Font Recommendation: {package.vertical_text_specs['font_recommendation']}
- Styling: {package.vertical_text_specs['typography_styling']}
- Title Safe Zone: {package.vertical_text_specs['title_safe_zone']}
- Core Visual Safe Zone: {package.vertical_text_specs['core_visual_safe_zone']}
- Bottom Clearance Zone: {package.vertical_text_specs['bottom_clearance_zone']}
================================================================================
"""
    vertical_file.write_text(vertical_content, encoding="utf-8")

    # 3. Comprehensive Markdown Guide for the User
    ref_line = (
        f"3. **Original thumbnail / Style and identity reference**: [`{package.reference_thumbnail_path.name}`](file:///{package.reference_thumbnail_path.as_posix()})\n"
        if package.reference_thumbnail_path and package.reference_thumbnail_path.exists()
        else ""
    )

    hint_section = ""
    if hint:
        hint_section = f"""
---

## Curiosity Gap & Open Loop Strategy (High CTR):
- **Environmental Clue**: {hint.environmental_clue}
- **Natural Subject Posture**: {hint.subject_state}
- **Curiosity Open Loop**: {hint.open_loop_explanation}
- **Visual Medium / Modality**: {package.source_modality.replace('_', ' ').title()}
"""

    readme_content = f"""# Source-led Thumbnail Guide

These prompts preserve the source thumbnail's medium and visual language, with an episode-specific hybrid composition and short Arabic hook. Attach the original thumbnail; its pixels guide the image generator. Existing video titles and voiceovers are not rewritten.

## Configuration for This Video:
- **Visual Style**: {package.visual_style.name}
- **Focal Archetype**: {package.focal_archetype.replace('_', ' ').title()}
- **Full post title (unchanged)**: {package.video_title_ar}
- **Thumbnail hook**: {package.fb_text_specs['headline_arabic']}
- **Optional emphasis word**: {package.fb_text_specs['power_word_highlighted']}
{hint_section}
## Generated Prompt Files:
{f"1. **Facebook Photo Post Prompt (4:5)**: [`thumbnail_prompt_facebook_4x5.txt`](file:///{fb_file.as_posix()})\n" if fb_file else "1. **Facebook Photo Post Prompt (4:5)**: *Skipped (no deep-dive summary requested)*\n"}2. **TikTok / Shorts Cover Prompt (9:16)**: [`thumbnail_prompt_vertical_9x16.txt`](file:///{vertical_file.as_posix()})
{ref_line}
---

## Mobile Feed Safe-Zone Design (9:16):
- **Title Safe Zone (Y: 320 to 560px)**: Designed for centred 3:4 and 4:5 crops; check the actual platform preview. Square crops can trim the headline.
- **Visual Tension Center (Y: 580 to 1420px)**: Optimized for 1:1 square preview in direct message chat bubbles.
- **Bottom Clearance (Y: 1450 to 1920px)**: 100% text-free so platform play counts (`▷ 515`) and usernames never obscure content.

---

## How to Create the Images Manually:

### Step 1: Generate Visual
- Open your chosen image generator with image-reference support.
- Copy the master prompt from {f"[`thumbnail_prompt_facebook_4x5.txt`](file:///{fb_file.as_posix()}) or " if fb_file else ""}[`thumbnail_prompt_vertical_9x16.txt`](file:///{vertical_file.as_posix()}).
- Attach `{package.reference_thumbnail_path.name if package.reference_thumbnail_path else 'source_thumbnail.jpg'}` as Image 1 when present. A filename in the prompt does not attach the image. If missing, the prompt explicitly uses topic-only direction and cannot promise source-style continuity.

### Step 2: Save to Output Folder
Save your generated image directly in this folder:
{f"- **Facebook Photo Post**: `cover_facebook_4x5.png` (or `.jpg`)" if fb_file else ""}
- **TikTok / Shorts Cover**: `cover_vertical_9x16.png` (or `.jpg`)

### Step 3: Social Publishing
- To post as a high-engagement **Facebook Photo Post** with full narrative description:
  ```powershell
  python scripts/avbrief.py post --folder "{output_dir.as_posix()}" --platform meta --mode photo
  ```
- To post as standard video Reel:
  ```powershell
  python scripts/avbrief.py post --folder "{output_dir.as_posix()}" --platform meta --mode video
  ```
"""
    readme_file.write_text(readme_content, encoding="utf-8")

    return fb_file, vertical_file, readme_file
