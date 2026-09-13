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
