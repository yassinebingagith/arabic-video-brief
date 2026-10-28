from pathlib import Path

import pytest

from arabic_video_brief.config import Settings
from arabic_video_brief.media import render_source_card, render_text_page


def test_rtl_page_renders_inside_full_canvas(tmp_path: Path) -> None:
    settings = Settings()
    if not settings.font_path.exists():
        pytest.skip("Bundled font has not been downloaded")
    output = tmp_path / "page.png"
    text = "يشرح الفيديو كيف تساعد الأسئلة المتابعة على بناء حوار أعمق وأكثر صدقًا، لأن الاهتمام الحقيقي يظهر في الإنصات للتفاصيل وفهم مشاعر الطرف الآخر بدل الاكتفاء بإجابة سطحية سريعة."
    size = render_text_page(text, output, settings)
    from PIL import Image

    with Image.open(output) as image:
        assert image.size == (1080, 1920)
        assert image.getpixel((10, 10)) == (0, 0, 0)
    assert settings.min_font_size <= size <= settings.font_size


def test_source_card_contains_full_thumbnail_and_metadata(tmp_path: Path) -> None:
    from PIL import Image

    settings = Settings()
    thumbnail = tmp_path / "thumb.png"
    Image.new("RGB", (1280, 720), "#CC3311").save(thumbnail)
    output = tmp_path / "card.png"
    render_source_card(
        thumbnail,
        {
            "title": "عنوان فيديو كامل للاختبار",
            "channel": "قناة الاختبار",
            "view_count": 2_600_000,
            "upload_date": "20250801",
        },
        output,
        settings,
    )
    with Image.open(output) as image:
        assert image.size == (settings.width, settings.top_height)
        assert image.getpixel((540, 100)) == (204, 51, 17)


def test_render_text_page_with_highlights(tmp_path: Path) -> None:
    from PIL import Image
    settings = Settings()
    if not settings.font_path.exists():
        pytest.skip("Bundled font has not been downloaded")
    output = tmp_path / "page_hl.png"
    text = "عندما يسألك شخص عن هواياتك في الكِبر، قد تتلعثم طويلاً. لا يستطيع الإنسان رعاية أكثر من <hl>ثلاثة جوانب رئيسية</hl> بالتوازي وإلا أصابه <hl>الإنهاك العصبي الحاد</hl>."
    size = render_text_page(text, output, settings)
    assert size >= 24
    with Image.open(output) as image:
        assert image.size == (1080, 1920)
        # Verify lower panel glow exists (more blue than corner)
        corner = image.getpixel((10, 10))
        center_glow = image.getpixel((540, 760 + int(1160 * 0.52)))
        assert center_glow[2] > corner[2]


def test_sanitize_v1_summary_text_removes_description_callout() -> None:
    from arabic_video_brief.media import sanitize_v1_summary_text

    text_with_cta1 = "هذه الفكرة تغير نظرتك للعالم تماماً. المزيد من التفاصيل في صندوق الوصف."
    assert sanitize_v1_summary_text(text_with_cta1) == "هذه الفكرة تغير نظرتك للعالم تماماً."

    text_with_cta2 = "هذه الفكرة تغير نظرتك للعالم تماماً. اقرأ الوصف لمزيد من التفاصيل."
    assert sanitize_v1_summary_text(text_with_cta2) == "هذه الفكرة تغير نظرتك للعالم تماماً."

    text_with_cta3 = "هذه الفكرة تغير نظرتك للعالم تماماً. التفاصيل الكاملة في صندوق الوصف"
    assert sanitize_v1_summary_text(text_with_cta3) == "هذه الفكرة تغير نظرتك للعالم تماماً."

    text_clean = "هذه الفكرة تغير نظرتك للعالم تماماً. استمر في السعي وراء أهدافك."
    assert sanitize_v1_summary_text(text_clean) == "هذه الفكرة تغير نظرتك للعالم تماماً. استمر في السعي وراء أهدافك."


def test_v1_cta_page_uses_glow_background(tmp_path: Path) -> None:
    from PIL import Image
    from arabic_video_brief.media import render_v1_cta_page
    settings = Settings()
    if not settings.font_path.exists():
        pytest.skip("Bundled font has not been downloaded")
    output = tmp_path / "v1_cta.png"
    render_v1_cta_page(output, settings, ending_question="ما الهواية التي تنتظر بهدوء لتعود إليها؟")
    with Image.open(output) as image:
        assert image.size == (1080, 1920)
        center_glow = image.getpixel((540, 760 + int(1160 * 0.52)))
        # Radial glow in lower panel has royal blue component
        assert center_glow[2] >= 15
