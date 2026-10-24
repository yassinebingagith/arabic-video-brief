from __future__ import annotations

import json
from pathlib import Path

import pytest

from arabic_video_brief.thumbnail import (
    FocalArchetype,
    ImageGeneratorClient,
    generate_thumbnail_package,
    process_folder_thumbnails,
    resolve_focal_archetype,
    resolve_visual_style,
)


def test_resolve_visual_style_10_styles() -> None:
    # 1. Noir Contrast
    style_dark = resolve_visual_style(title="Dark Manipulation Secrets and Power Dynamics")
    assert style_dark.name == "Noir / Dramatic High-Contrast & Shadow"

    # 2. Futuristic Cyberpunk
    style_sci = resolve_visual_style(title="Artificial Intelligence and Space Physics", description="Cosmos exploration")
    assert style_sci.name == "Futuristic / Cyberpunk & Cosmos"

    # 3. Minimalist Clean
    style_prod = resolve_visual_style(title="How to stop procrastination and build daily habits")
    assert style_prod.name == "Minimalist / Clean & Bold Contrast"

    # 4. Cinematic Documentary
    style_psych = resolve_visual_style(title="Jordan Peterson on Carl Jung and consciousness")
    assert style_psych.name == "Cinematic Documentary / Gritty Realism"

    # 5. Split-Screen Comparison
    style_split = resolve_visual_style(title="قبل وبعد: مقارنة حاسمة بين الحقيقة والوهم")
    assert style_split.name == "Split-Screen / Before & After (Dichotomy)"

    # 6. High-Energy
    style_energy = resolve_visual_style(title="كيف يجمع المليونير ثروة خيالية؟")
    assert style_energy.name == "High-Energy / Radiant Contrast & Glow"

    # 7. Retro Lo-Fi
    style_retro = resolve_visual_style(title="تاريخ سقوط الحضارات القديمة")
    assert style_retro.name == "Retro / Lo-Fi Vintage Aesthetic"

    # 8. Abstract Conceptual
    style_abs = resolve_visual_style(title="الوهم الأكبر في الوعي الباطن")
    assert style_abs.name == "Abstract / Conceptual & Mind-Bending Metaphor"

    # 9. Explicit override by alias or key
    assert resolve_visual_style(style_preference="animated_3d").name == "3D Stylized / Premium Dimensional Animation"
    assert resolve_visual_style(style_preference="hyper_realistic").name == "Hyper-Realistic Portrait & Metaphor"


def test_resolve_focal_archetype_dynamic_routing() -> None:
    # 1. Comparison
    arch_comp, _ = resolve_focal_archetype(title="الفرق بين الناجح والفاشل: مقارنة عملية")
    assert arch_comp == FocalArchetype.SPLIT_COMPARISON

    # 2. Symbolic Artifact
    arch_art, _ = resolve_focal_archetype(title="رمز الثروة والسيطرة: أيقونة النجاح")
    assert arch_art == FocalArchetype.SYMBOLIC_ARTIFACT

    # 3. Dramatic Scene
    arch_scene, _ = resolve_focal_archetype(title="معركة البقاء وسقوط أعظم إمبراطورية")
    assert arch_scene == FocalArchetype.DRAMATIC_SCENE

    # 4. Conceptual Metaphor
    arch_meta, _ = resolve_focal_archetype(title="حقيقة مصفوفة الوعي والوهم الإنساني")
    assert arch_meta == FocalArchetype.CONCEPTUAL_METAPHOR

    # 5. Emotive Portrait (with speaker)
    arch_port, _ = resolve_focal_archetype(
        title="لماذا تقرأ عيونهم أولاً؟",
        has_speaker=True,
    )
    assert arch_port == FocalArchetype.EMOTIVE_PORTRAIT


def test_generate_thumbnail_package_source_led_quality_and_safe_margins() -> None:
    title_ar = "تشتت عقلك إلى الأبد – دانيال بارادا"

    manifest_data = {
        "metadata": {
            "title": "Mind Distraction Guide",
            "uploader": "Daniel Barada",
            "description": "How modern distractions fracture focus.",
        }
    }

    package = generate_thumbnail_package(
        post_title_ar=title_ar,
        manifest_data=manifest_data,
        creative_plan={"thumbnail_hook_ar": "من يسرق انتباهك؟"},
    )

    # 4:5 Facebook checks
    assert "4:5 Aspect Ratio" in package.fb_master_prompt
    assert "تشتت عقلك إلى الأبد" in package.fb_master_prompt
    assert "natural pores" in package.fb_master_prompt
    assert "80px side margins" in package.fb_master_prompt
    assert "without misrepresenting the source" in package.fb_master_prompt

    # 9:16 Vertical cover checks (Cropping proofing)
    assert "9:16 Aspect Ratio" in package.vertical_master_prompt
    assert "title Y: 320px to 560px" in package.vertical_master_prompt
    assert "core subject Y: 580px to 1420px" in package.vertical_master_prompt
    assert "Bottom Y: 1450px to 1920px is strictly text-free" in package.vertical_master_prompt
    assert "No secondary conclusion" in package.vertical_master_prompt

    # Power word extraction check
    assert package.fb_text_specs["headline_arabic"] == "من يسرق انتباهك؟"
    assert package.video_title_ar == title_ar
    assert package.visual_style.id == "source_led"


def test_process_folder_thumbnails_creates_files_without_conclusion(tmp_path: Path) -> None:
    # Setup test folder
    (tmp_path / "post-title.txt").write_text("العادات الذرية وكيف تبني نظاماً ناجحاً", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "metadata": {
            "title": "Atomic Habits Guide",
            "uploader": "James Clear",
            "description": "Habits and productivity systems",
        }
    }), encoding="utf-8")

    fb_file, vert_file, guide_file = process_folder_thumbnails(tmp_path)

    assert fb_file.exists()
    assert vert_file.exists()
    assert guide_file.exists()

    fb_text = fb_file.read_text(encoding="utf-8")
    assert "العادات الذرية" in fb_text
    assert "MANUAL TEXT OVERLAY FALLBACK SPECS:" in fb_text
    assert "Bottom Badge: None" in fb_text

    vert_text = vert_file.read_text(encoding="utf-8")
    assert "Title Safe Zone: Y: 320px to 560px" in vert_text
    assert "Bottom Clearance Zone: Y: 1450px to 1920px text-free" in vert_text


def test_image_client_checks_existing_covers(tmp_path: Path) -> None:
    client = ImageGeneratorClient()
    covers = client.check_existing_covers(tmp_path)
    assert covers["facebook_4x5"] is None
    assert covers["vertical_9x16"] is None

    # Create dummy images
    (tmp_path / "cover_facebook_4x5.png").write_bytes(b"dummy_png")
    (tmp_path / "cover_vertical_9x16.jpg").write_bytes(b"dummy_jpg")

    covers = client.check_existing_covers(tmp_path)
    assert covers["facebook_4x5"] == tmp_path / "cover_facebook_4x5.png"
    assert covers["vertical_9x16"] == tmp_path / "cover_vertical_9x16.jpg"


def test_cli_thumbnail_command(tmp_path: Path) -> None:
    from arabic_video_brief.cli import main
    (tmp_path / "post-title.txt").write_text("قوة التركيز وكيف تحمي انتباهك", encoding="utf-8")

    # 1. When no deep_dive_summary.txt exists: Facebook 4:5 is skipped, saving tokens/credits
    exit_code_no_dd = main(["thumbnail", "--folder", str(tmp_path), "--style", "minimalist_clean", "--archetype", "artifact"])
    assert exit_code_no_dd == 0
    assert not (tmp_path / "thumbnail_prompt_facebook_4x5.txt").exists()
    assert (tmp_path / "thumbnail_prompt_vertical_9x16.txt").is_file()
    assert (tmp_path / "THUMBNAIL_GUIDE.md").is_file()

    # 2. When deep_dive_summary.txt exists: Facebook 4:5 IS generated
    (tmp_path / "deep_dive_summary.txt").write_text("ملخص معرفي شامل", encoding="utf-8")
    exit_code_dd = main(["thumbnail", "--folder", str(tmp_path), "--style", "minimalist_clean", "--archetype", "artifact"])
    assert exit_code_dd == 0
    assert (tmp_path / "thumbnail_prompt_facebook_4x5.txt").is_file()
    assert (tmp_path / "thumbnail_prompt_vertical_9x16.txt").is_file()

    fb_content = (tmp_path / "thumbnail_prompt_facebook_4x5.txt").read_text(encoding="utf-8")
    assert "Explicit requested composition: artifact" in fb_content


def test_format_dual_tone_title_ignores_numbers_and_particles() -> None:
    from arabic_video_brief.thumbnail.prompt_engine import format_dual_tone_title

    # 1. Title with leading number and English suffix
    _, power_word1, _ = format_dual_tone_title("6. القلق - (Anxiety)")
    assert power_word1 == "القلق"  # NOT "6"

    # 2. Digital brain title with particles
    _, power_word2, _ = format_dual_tone_title("كيف يؤثر العالم الرقمي على كيمياء الدماغ؟ | التفسير العلمي لغياب سعادتك")
    assert power_word2 in ["الدماغ", "العالم", "السعادة"]  # NOT "كيف" or "يؤثر"

    # 3. Boundaries title
    _, power_word3, _ = format_dual_tone_title("اليوم الذي تتوقف فيه عن منح الفرص الثانية – كارل يونغ")
    assert power_word3 in ["الفرص", "الثانية", "تتوقف"]  # NOT "اليوم" or "الذي"


def test_extract_curiosity_visual_hint_domains() -> None:
    from arabic_video_brief.thumbnail import extract_curiosity_visual_hint

    # 1. Digital Dopamine / Screens (Must not match sleep or potions!)
    hint_digital = extract_curiosity_visual_hint(
        title="كيف يؤثر العالم الرقمي على كيمياء الدماغ؟ | التفسير العلمي لغياب سعادتك",
        description="تأثير الشاشات وإدمان الهاتف على مستقبلات الدوبامين والشعور بالسعادة",
    )
    assert hint_digital.domain == "digital_dopamine_tech"
    assert "smartphone" in hint_digital.environmental_clue or "screen" in hint_digital.environmental_clue
    assert "amber" not in hint_digital.environmental_clue  # NO POTION BOTTLES
    assert "tea" not in hint_digital.environmental_clue

    # 2. Relationship Boundaries / Closure (Carl Jung)
    hint_rel = extract_curiosity_visual_hint(
        title="اليوم الذي تتوقف فيه عن منح الفرص الثانية – كارل يونغ",
        description="كارل يونغ والتوقف عن التسامح غير المشروط واستنزاف العلاقات",
        modality="illustrated_artistic",
    )
    assert hint_rel.domain == "relationship_boundaries"
    assert "watch" not in hint_rel.environmental_clue  # NO POCKET WATCHES
    assert "notebook" not in hint_rel.environmental_clue  # NO NOTEBOOKS

    # 3. Existential Anxiety
    hint_anxiety = extract_curiosity_visual_hint(
        title="6. القلق - (Anxiety)",
        description="القلق الوجودي ودوار الحرية وسارتر والاختيار الإنساني",
    )
    assert hint_anxiety.domain == "existential_anxiety"
    assert "chiaroscuro" in hint_anxiety.environmental_clue or "window" in hint_anxiety.environmental_clue


def test_prompt_cleanliness_zero_stickers() -> None:
    from arabic_video_brief.thumbnail import generate_thumbnail_package

    package = generate_thumbnail_package(
        post_title_ar="كيف يؤثر العالم الرقمي على كيمياء الدماغ؟",
        manifest_data={
            "metadata": {
                "title": "Digital World and Brain Chemistry",
                "uploader": "Abdelkader Elturkey",
                "description": "Smartphones, screens, and dopamine receptors.",
            }
        },
    )

    # Preserve quality without banning legitimate source art styles.
    assert "unsolicited badges" in package.fb_master_prompt
    assert "No secondary conclusion" in package.vertical_master_prompt
    assert "فخ التفكير؟" not in package.fb_master_prompt
    assert "قبل النوم فقط؟" not in package.fb_master_prompt

    # Verify natural environmental clue
    assert "Smartphones" in package.fb_master_prompt
    assert "amber apothecary" not in package.fb_master_prompt


def test_foreground_background_depth_layering() -> None:
    from arabic_video_brief.thumbnail import extract_curiosity_visual_hint, generate_thumbnail_package

    # Loneliness & Friendship recession
    hint = extract_curiosity_visual_hint(
        title="The Friendship Recession",
        description="The modern friendship recession explores loneliness, social isolation, and human connection.",
        modality="illustrated_artistic",
    )
    assert hint.domain == "social_isolation_loneliness"
    assert hint.foreground_clue
    assert hint.background_clue
    assert "water adorned with drifting wildflowers" not in hint.environmental_clue  # NO HARDCODED OPHELIA

    package = generate_thumbnail_package(
        post_title_ar="ركود الصداقة والعزلة الحديثة",
        manifest_data={
            "metadata": {
                "title": "The Friendship Recession",
                "uploader": "Queen",
                "description": "Loneliness and social connection in the modern era.",
            }
        },
    )
    assert "sculptural facial depth" in package.fb_master_prompt
    assert "Light direction, contact shadows and materials" in package.vertical_master_prompt
    assert "not as three mandatory props" in package.vertical_master_prompt
    assert "A face is optional" in package.fb_master_prompt


def test_active_pipeline_does_not_infer_source_medium_from_interview_keywords() -> None:
    from arabic_video_brief.thumbnail.prompt_engine import detect_source_modality, generate_thumbnail_package

    # 1. Jonathan Rauch Full Interview on Political Philosophy
    modality = detect_source_modality(
        reference_thumbnail_path=None,
        title="The political philosophy that changed the world - Jonathan Rauch Full Interview",
        description="Big Think interview with Jonathan Rauch discussing liberalism, enlightenment, and freedom.",
    )
    assert modality == "photographic"

    package = generate_thumbnail_package(
        post_title_ar="الليبرالية الحقيقية: الفلسفة التي غيرت العالم",
        manifest_data={
            "metadata": {
                "title": "The political philosophy that changed the world - Jonathan Rauch Full Interview",
                "uploader": "Big Think",
                "description": "Jonathan Rauch discusses liberalism and political philosophy.",
            }
        },
    )
    assert package.source_modality == "unverified_no_reference"
    assert "No original thumbnail is available" in package.vertical_master_prompt
    assert "classical Enlightenment" not in package.vertical_master_prompt
    assert "Bright backgrounds" in package.vertical_master_prompt
