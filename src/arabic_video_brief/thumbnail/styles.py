from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class VisualStyle:
    id: str
    name: str
    description: str
    camera_and_lighting: str
    color_palette: str
    texture_and_atmosphere: str


STYLE_REGISTRY: dict[str, VisualStyle] = {
    # 1. Hyper-realistic / Cinematic Focus
    "hyper_realistic": VisualStyle(
        id="hyper_realistic",
        name="Hyper-Realistic Portrait & Metaphor",
        description="Emotionally intense, expressive human portrait fused with a clever physical metaphor.",
        camera_and_lighting="Shot on 85mm portrait prime telephoto lens at f/1.4, creamy optical bokeh, Rembrandt beauty-dish key light with soft wrap, razor-sharp catchlights in the pupils, subtle cinematic rim separation light.",
        color_palette="Rich lifelike skin tones, deep cinematic charcoal/obsidian background with warm amber (#E5A93C) and cool slate rim highlights.",
        texture_and_atmosphere="100% authentic micro-textures, individual visible hair strands, micro-pores and natural skin creases. Strictly zero beauty-filter smoothing, zero wax surfaces, and zero generic CGI gloss.",
    ),
    # 2. 3D Pixar-Style / Animated & Stylized
    "animated_3d": VisualStyle(
        id="animated_3d",
        name="3D Stylized / Premium Dimensional Animation",
        description="Vibrant, high-charm 3D stylized character art with expressive features and Pixar-quality subsurface scattering.",
        camera_and_lighting="Studio volumetric lighting, warm soft key light, gentle purple-cyan fill lights, soft depth of field focusing on exaggerated expressive eyes and facial gestures.",
        color_palette="Vibrant, rich saturation: electric cobalt blue, radiant gold, warm peach, deep indigo shadow tones.",
        texture_and_atmosphere="Tactile clay-like or smooth stylized resin textures, ray-traced subsurface scattering on skin, clean atmospheric dust motes with soft depth, highly polished yet non-slop aesthetic.",
    ),
    # 3. Split-Screen / Before & After (Contrast & Dichotomy)
    "split_screen": VisualStyle(
        id="split_screen",
        name="Split-Screen / Before & After (Dichotomy)",
        description="High-tension direct visual comparison dividing the frame into two starkly opposing realities, mental states, or outcomes.",
        camera_and_lighting="Dual-temperature lighting: left side in bleak, desaturated cold fluorescent blue/grey tones with harsh downward shadows; right side in radiant, golden-hour amber sunlight with upward victorious rim light.",
        color_palette="Stark split dichotomy: cold concrete grey and muted slate vs. triumphant golden sunbeam (#F5C518) and vibrant sky cyan (#00D2FF).",
        texture_and_atmosphere="Left side weathered, fatigued, chained, and strained textures; right side clean, energetic, buoyant, liberated atmosphere with subtle lens glow. Clear diagonal or vertical visual split.",
    ),
    # 4. Cinematic Documentary / Gritty News-Style
    "cinematic_documentary": VisualStyle(
        id="cinematic_documentary",
        name="Cinematic Documentary / Gritty Realism",
        description="Moody, authentic, high-prestige editorial aesthetic matching serious intellectual, psychological, and historical discourse.",
        camera_and_lighting="Shot on 35mm master cinema prime at f/1.8, shallow depth of field, dramatic chiaroscuro with deep directional rim highlights and rich, velvety shadows.",
        color_palette="Moody documentary grade: deep charcoal black (#0C0D10), warm tungsten key light, subtle cyan or gold accent edge lights.",
        texture_and_atmosphere="Authentic tactile skin pores, natural lived-experience imperfections, cinematic atmospheric haze, subtle 35mm film grain. Strictly zero plastic CGI or airbrushed smoothing.",
    ),
    # 5. Minimalist / Clean & Bright
    "minimalist_clean": VisualStyle(
        id="minimalist_clean",
        name="Minimalist / Clean & Bold Contrast",
        description="Ultra-clean, uncluttered, and punchy. Maximizes 0.1-second comprehension for productivity, habits, health, and decision-making.",
        camera_and_lighting="Crisp studio lighting, high-key with razor-sharp contrast, isolated central subject against a massive clean geometric backdrop, zero visual clutter.",
        color_palette="Stark matte dark background (#111111) paired with punchy warm gold (#F5C518) and pure clinical white (#FFFFFF).",
        texture_and_atmosphere="Matte smooth industrial textures, razor-sharp silhouettes, expansive negative space engineered for immediate typography absorption.",
    ),
    # 6. Abstract / Conceptual & Mind-Bending
    "abstract_conceptual": VisualStyle(
        id="abstract_conceptual",
        name="Abstract / Conceptual & Mind-Bending Metaphor",
        description="Surrealistic physical manifestations of psychological dilemmas, mental illusions, and deep philosophical paradigms.",
        camera_and_lighting="Dream-logic cinematic lighting, surreal overhead spotlights piercing through dark atmospheric fog, impossible architectural shadows and refractive caustic light rays.",
        color_palette="Deep twilight indigo, smoky obsidian, with incandescent glowing gold thread, shattered mirror reflections, or bioluminescent highlights.",
        texture_and_atmosphere="Crumbling marble statues, unraveling golden threads, floating geometric prisms, shattered hourglass sand frozen in mid-air. Profound sense of cognitive revelation.",
    ),
    # 7. High-Energy / "MrBeast" Glow & Velocity
    "high_energy": VisualStyle(
        id="high_energy",
        name="High-Energy / Radiant Contrast & Glow",
        description="Extreme visual stop power, vibrant saturated colors, intense kinetic expressions, and glowing rim accents that command mobile feeds.",
        camera_and_lighting="Ultra-wide 20mm dynamic angle with exaggerated perspective, high-intensity three-point lighting, saturated neon rim lighting wrapping around subjects.",
        color_palette="Hyper-saturated contrasts: electric neon yellow (#FFE600), vivid magenta, radiant electric cyan, and deep punchy midnight blue.",
        texture_and_atmosphere="Dynamic motion blur streaks on peripheral elements, glowing energy auras, crisp high-contrast foreground objects with zero visual lag.",
    ),
    # 8. Retro / Lo-Fi Vintage Aesthetic
    "retro_lofi": VisualStyle(
        id="retro_lofi",
        name="Retro / Lo-Fi Vintage Aesthetic",
        description="Nostalgic, warm, analog film aesthetic evoking 1970s-1990s archival journalism, retro psychology, and vintage case studies.",
        camera_and_lighting="Vintage 16mm/35mm analog camera optics with characteristic optical halation around highlights, warm tungsten practical lamps, soft shadow rolloff.",
        color_palette="Warm nostalgic sepia, faded kodachrome tones, olive green, muted mustard gold, and warm burgundy shadows.",
        texture_and_atmosphere="Tactile film grain, subtle analog chromatic aberration, dust and gate scratches on archival polaroids or vintage monitors, rich nostalgic patina.",
    ),
    # 9. Futuristic / Cyberpunk & Deep Cosmos
    "futuristic_cyber": VisualStyle(
        id="futuristic_cyber",
        name="Futuristic / Cyberpunk & Cosmos",
        description="Awe-inspiring, cosmic, and cerebral. Tailored for AI, astrophysics, deep science, synthetic minds, and future civilization.",
        camera_and_lighting="Anamorphic cinema lens with horizontal optical flare streaks, volumetric blue/magenta backlighting, glowing holographic interfaces and neural grids.",
        color_palette="Deep space violet, obsidian, electric cyan (#00D2FF), glowing neural gold (#FFB800), and laser-etched white.",
        texture_and_atmosphere="Hyper-detailed circuit weaves, translucent holographic projections, cosmic nebula dust, crystalline optical surfaces, infinite depth of scale.",
    ),
    # 10. Noir / Dramatic High-Contrast & Shadow
    "noir_contrast": VisualStyle(
        id="noir_contrast",
        name="Noir / Dramatic High-Contrast & Shadow",
        description="High tension, secrecy, psychological manipulation, and hidden power dynamics.",
        camera_and_lighting="Low-key cinematic noir lighting, razor-sharp hard venetian blind shadows cutting across faces and walls, solitary harsh side-light, wide Dutch-angle tension.",
        color_palette="High-contrast monochromatic charcoal and obsidian with a piercing single saturated accent color (crimson red #E63946, toxic amber, or emerald).",
        texture_and_atmosphere="Smoky atmospheric haze, rain-slicked reflective surfaces, silhouette outlines, intense psychological tension in negative space.",
    ),
    # 11. Classical Fine Art & Oil Painting Masterpiece
    "fine_art_oil": VisualStyle(
        id="fine_art_oil",
        name="Classical Fine Art & Oil Painting Masterpiece",
        description="Rich, painterly, museum-grade classical fine art aesthetic matching deep philosophy, timeless strategy, and historical wisdom.",
        camera_and_lighting="Classical chiaroscuro Caravaggio/Rembrandt lighting, directional warm amber candlelight or lantern glow illuminating the central subject against deep raw umber and burnt sienna shadows.",
        color_palette="Warm earthy museum palette: burnt umber, raw sienna, deep crimson, antique gold, and aged parchment tones with rich painterly depth.",
        texture_and_atmosphere="Authentic oil-on-canvas impasto textures, subtle craquelure, visible expressive brushstrokes, and timeless poetic dignity. Strictly zero modern corporate stock photography, zero flat vector art, and zero plastic 3D CGI.",
    ),
}

# Aliases for flexible matching
STYLE_ALIASES: dict[str, str] = {
    "cinematic": "cinematic_documentary",
    "documentary": "cinematic_documentary",
    "gritty_documentary": "cinematic_documentary",
    "noir": "noir_contrast",
    "futuristic": "futuristic_cyber",
    "cyberpunk": "futuristic_cyber",
    "cosmos": "futuristic_cyber",
    "minimalist": "minimalist_clean",
    "clean": "minimalist_clean",
    "split": "split_screen",
    "comparison": "split_screen",
    "before_after": "split_screen",
    "hyper_real": "hyper_realistic",
    "portrait": "hyper_realistic",
    "abstract": "abstract_conceptual",
    "conceptual": "abstract_conceptual",
    "high_energy": "high_energy",
    "glow": "high_energy",
    "mrbeast": "high_energy",
    "retro": "retro_lofi",
    "vintage": "retro_lofi",
    "lofi": "retro_lofi",
    "3d": "animated_3d",
    "pixar": "animated_3d",
    "animated": "animated_3d",
    "fine_art": "fine_art_oil",
    "oil_painting": "fine_art_oil",
    "painting": "fine_art_oil",
    "art": "fine_art_oil",
    "classical": "fine_art_oil",
}


def resolve_visual_style(
    title: str = "",
    description: str = "",
    categories_or_tags: list[str] | None = None,
    style_preference: str | None = None,
) -> VisualStyle:
    """Dynamically route to the best visual style among the 11 Thumbnail 4.0 archetypes."""
    # 1. Direct or alias preference
    if style_preference:
        pref_key = style_preference.strip().lower().replace("-", "_").replace(" ", "_")
        if pref_key in STYLE_REGISTRY:
            return STYLE_REGISTRY[pref_key]
        if pref_key in STYLE_ALIASES:
            return STYLE_REGISTRY[STYLE_ALIASES[pref_key]]

    combined_text = f"{title} {description} {' '.join(categories_or_tags or [])}".lower()
    title_lower = title.lower()

    # Split screen / comparison (ONLY when title explicitly indicates a dichotomy or direct comparison)
    if any(k in title_lower for k in [" vs ", " versus ", " vs. ", "قبل وبعد", "مقارنة بين", "الفرق بين", " before vs ", " before and after "]):
        return STYLE_REGISTRY["split_screen"]

    # Classical Fine Art, Philosophy, Stoicism & Ancient Strategy (e.g. Bygone Philosophy, Sun Tzu, Stoicism, Chess, Classical Thought)
    if any(k in combined_text for k in [
        "bygone philosophy", "eternalised", "einzelgänger", "pursuit of wonder", "academy of ideas",
        "stoic", "stoicism", "sun tzu", "epictetus", "seneca", "marcus aurelius", "nietzsche", "schopenhauer",
        "رواقية", "صن تزو", "إبكتيتوس", "ماركوس أوريليوس", "لوحة زيتية", "فلسفة قديمة", "شطرنج",
        "art of war", "bygone", "strategist", "the mind of a strategist", "oil painting"
    ]):
        return STYLE_REGISTRY["fine_art_oil"]

    # Social isolation, loneliness, friendship recession, solitude, human connection
    if any(k in combined_text for k in [
        "friendship", "loneliness", "isolation", "recession", "solitude", "third place",
        "صداقة", "عزلة", "وحدة", "تواصل", "انعزال", "وحيد"
    ]):
        return STYLE_REGISTRY["cinematic_documentary"]

    # Dark psychology, criminal mind, manipulation, psychopathy, toxic deception (Specific, high-intent terms only—no generic 'قوة' or 'سر')
    if any(k in combined_text for k in [
        "dark psychology", "dark triad", "psychopath", "sociopath", "gaslighting", "blackmail", "manipulation",
        "خداع نفسي", "تلاعب نفسي", "سيكوباتية", "ميكافيلية", "علم النفس المظلم", "نرجسي خبيث", "ابتزاز عاطفي"
    ]):
        return STYLE_REGISTRY["noir_contrast"]

    # Futuristic, AI, space, cosmos, tech, physics
    if re.search(r"\b(artificial intelligence|solar system|physics|quantum mechanics|cyberpunk|deep cosmos)\b", combined_text) or any(k in combined_text for k in ["ذكاء اصطناعي", "فضاء كوني", "فيزياء كمية"]):
        return STYLE_REGISTRY["futuristic_cyber"]

    # Productivity, habits, time management, health, fat loss, routine
    if any(k in combined_text for k in ["procrastination", "fat loss", "habits", "daily routine", "تسويف", "عادات يومية", "نظام غذائي", "انتاجية"]):
        return STYLE_REGISTRY["minimalist_clean"]

    # High energy, challenge, money, billionaire, wealth, extreme
    if any(k in combined_text for k in ["millionaire", "billionaire", "extreme challenge", "أثرياء العالم", "مليونير", "تحدي خطير"]):
        return STYLE_REGISTRY["high_energy"]

    # Retro, history, archival, ancient, cold war, 70s, 80s
    if any(k in combined_text for k in [
        "ancient history", "cold war", "1970s", "1980s", "archival", "حضارة قديمة", "تاريخ قديم",
        "الحضارات القديمة", "سقوط الحضارات", "تاريخ"
    ]):
        return STYLE_REGISTRY["retro_lofi"]

    # Abstract, mind, illusion, consciousness, existentialism, soul
    if any(k in combined_text for k in [
        "existential paradox", "matrix simulation", "وهم وجودي", "الوعي المطلق",
        "الوهم الأكبر", "الوعي الباطن", "الوهم", "matrix", "simulation"
    ]):
        return STYLE_REGISTRY["abstract_conceptual"]

    # Philosophy, psychoanalysis, Jung, Peterson, De Botton, Aristotle, interviews
    if any(k in combined_text for k in [
        "jung", "peterson", "greene", "williamson", "aristotle", "epicurus", "kant", "montaigne",
        "فلسفة", "علم نفس", "بيترسون", "كارل يونغ"
    ]):
        return STYLE_REGISTRY["cinematic_documentary"]

    # Animated, playful, storytelling, cartoons
    if any(k in combined_text for k in ["animation", "cartoon", "story for kids", "قصة كرتون"]):
        return STYLE_REGISTRY["animated_3d"]

    # Default to hyper-realistic cinematic portrait & metaphor
    return STYLE_REGISTRY["hyper_realistic"]
