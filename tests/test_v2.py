from __future__ import annotations

import tempfile
from pathlib import Path
from arabic_video_brief.config import Settings, get_settings
from arabic_video_brief.media import probe_media, find_ffmpeg
from arabic_video_brief.v2.editorial import (
    HookCandidate,
    V2EditorialPackage,
    split_half_into_two_pages,
)
from arabic_video_brief.v2.renderer import (
    render_v2_hook_page,
    render_v2_summary_page,
    render_v2_conclusion_page,
    render_v2_video,
)
from arabic_video_brief.v2.tts import generate_hook_tts, normalize_hook_text_for_tts


def test_hook_normalization_for_tts():
    raw = "**هاتفك** بعد الغروب، لا يسرق نومك فقط"
    norm = normalize_hook_text_for_tts(raw)
    assert "**" not in norm
    assert "،" in norm
    assert norm.endswith(".")


def test_tts_graceful_fallback_when_no_key(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("Elevenlabs_api", raising=False)
    monkeypatch.delenv("ELEVENLABS_API", raising=False)
    settings = Settings()
    ffmpeg = find_ffmpeg()
    out = tmp_path / "test_hook.mp3"
    res = generate_hook_tts("هاتفك بعد الغروب لا يسرق نومك فقط", out, settings, ffmpeg)
    assert res["status"] == "fallback"
    assert not out.exists()


def test_v2_split_half_sentence_boundaries():
    settings = get_settings()
    half = (
        "قد تنهي يومك برسالة قصيرة على الهاتف، ثم تكتشف أن الساعة أصبحت الثانية صباحًا. "
        "المشكلة ليست في عدد ساعات النوم فقط؛ فالضوء الصناعي الساطع يرسل إلى دماغك إشارة مضللة بأن النهار لم ينتهِ، "
        "فتتأخر ساعة النوم وتستيقظ بطاقة أقل."
    )
    pages = split_half_into_two_pages(half, half_index=1, settings=settings)
    assert len(pages) == 2
    for p in pages:
        assert len(p.split()) >= 10
        assert p.endswith((".", "!", "؟", "؛"))


def test_v2_render_integration(tmp_path: Path):
    settings = get_settings()
    ffmpeg = find_ffmpeg()

    # Generate a dummy 2-second clip as local video source
    source_video = tmp_path / "dummy_source.mp4"
    import subprocess
    cmd = [
        ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=blue:s=1280x720:r=30:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source_video),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    dummy_thumb = tmp_path / "dummy_thumb.jpg"
    cmd_thumb = [
        ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=red:s=1280x720:d=1",
        "-frames:v", "1", str(dummy_thumb),
    ]
    subprocess.run(cmd_thumb, check=True, capture_output=True)

    hook = HookCandidate(
        display_hook="هاتفك بعد الغروب\nلا يسرق نومك فقط",
        highlight_phrase="لا يسرق نومك فقط",
        tts_text="هاتفُك بعد الغروب... لا يسرق نومَك فقط.",
        category="صحة ونوم",
        scores={"clarity": 9.0},
        total_score=54.0,
        explanation="test",
    )

    editorial = V2EditorialPackage(
        post_title_ar="روتين الدماغ والجسم",
        summary_ar="ملخص تجريبي متوازن.",
        pages=[
            "الصفحة الأولى تشرح المشكلة باختصار وإيجاز شديد.",
            "الصفحة الثانية توضح آلية الضوء وتأثيره على العين والدماغ.",
            "الصفحة الثالثة تقدم الفهم العميق لإفراز هرمون الميلاتونين ليلاً.",
            "الصفحة الرابعة تضع خطوات عملية للتحكم في الإضاءة والنوم.",
        ],
        hook=hook,
        conclusion_ar="ما الذي ستغيّره في إضاءة غرفتك هذا المساء؟",
        conclusion_highlights=["صباحك", "الليلة"],
        cta_ar="احفظها لتجربها الليلة",
        cta_description="اقرأ الوصف للتفاصيل والخطوات الكاملة",
        creative_plan={},
    )

    output_video = tmp_path / "v2_brief.mp4"
    render_details = render_v2_video(
        source=source_video,
        thumbnail=dummy_thumb,
        editorial=editorial,
        selected_clip={"start_seconds": 0.0, "end_seconds": 2.0},
        output=output_video,
        settings=settings,
        hook_audio_path=None,
        metadata={"title": "Test Video", "channel": "Test Channel"},
    )

    assert output_video.exists()
    assert render_details["version"] == "v2"
    info = probe_media(output_video)
    assert info.width == 1080
    assert info.height == 1920
    assert abs(info.duration - settings.duration_v2) < 0.2
    assert render_details["timeline"] == {
        "page_1": "0:00.0-0:12.8", "page_2": "0:12.8-0:22.6",
        "page_3": "0:22.6-0:32.4", "page_4": "0:32.4-0:42.2",
        "conclusion": "0:42.2-0:50.2",
    }

    # Both the retained short track and the new track must cover the longer reading section.
    import array
    audio = subprocess.run([ffmpeg, "-loglevel", "error", "-ss", "38", "-i", str(output_video),
                            "-t", "2", "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                           check=True, capture_output=True).stdout
    samples = array.array("f", audio)
    assert (sum(x*x for x in samples) / len(samples)) ** 0.5 > 0.001

    # Verify anti-bot CapCut metadata spoofing & absence of FFmpeg/Lavf markers
    import subprocess
    probe_proc = subprocess.run([ffmpeg, "-hide_banner", "-i", str(output_video)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    probe_output = probe_proc.stderr
    assert "major_brand     : mp42" in probe_output or "major_brand: mp42" in probe_output
    assert "CapCut" in probe_output
    assert "Lavf" not in probe_output
    assert "Lavc" not in probe_output


def test_v2_random_music_pool_keeps_both_tracks_and_excludes_v1(tmp_path, monkeypatch):
    from arabic_video_brief.v2.renderer import select_v2_music
    for name in ("naruto_sadness_and_sorrow.mp3", "godfather_0013.mp3", "andrea_vanzo_amelie_0030_0100.mp3"):
        (tmp_path / name).write_bytes(b"fixture")
    observed = []
    def choose(items):
        observed.extend(p.name for p in items)
        return items[-1]
    monkeypatch.setattr("random.choice", choose)
    assert select_v2_music(tmp_path).name == "godfather_0013.mp3"
    assert observed == ["naruto_sadness_and_sorrow.mp3", "godfather_0013.mp3"]


def test_v2_timing_and_voiceover_preserve_reading_content():
    import pytest
    from arabic_video_brief.v2.editorial import build_v2_editorial_package, VOICEOVER_SUFFIX
    settings = Settings()
    bounds = settings.v2_page_boundaries
    assert [bounds[i+1]-bounds[i] for i in range(4)] == pytest.approx([10.8+2, 7.8+2, 7.8+2, 7.8+2])
    assert bounds[-1] + settings.conclusion_duration == pytest.approx(50.2)
    pages = ["مثال عربي مع الرقم 21."] * 4
    result = build_v2_editorial_package({"post_title_ar": "عنوان الاختبار", "pages": pages,
        "ending_question_ar": "أي فكرة ستجرب تطبيقها في حياتك اليوم؟",
        "hook": {"tts": "النص القديم", "display": "العنوان المرئي"}}, {}, settings)
    assert result.pages == pages
    assert result.hook.display_hook == "العنوان المرئي"
    assert VOICEOVER_SUFFIX == "ملخص الفكرة في ثوانٍ، والتفاصيل الكاملة في صندوق الوصف"


def test_v2_summary_background_glow():
    from arabic_video_brief.v2.renderer import create_v2_summary_background
    bg = create_v2_summary_background(1080, 1920, 760)
    assert bg.size == (1080, 1920)
    # Check edge is pure midnight black #02060D
    corner_pixel = bg.getpixel((10, 10))
    assert corner_pixel[0] <= 5 and corner_pixel[1] <= 10 and corner_pixel[2] <= 18
    # Check center glow in lower canvas has royal/midnight blue tones
    center_pixel = bg.getpixel((540, 760 + int(1160 * 0.52)))
    assert center_pixel[2] > corner_pixel[2]  # Significantly more blue in glow center


def test_v2_highlight_wrapping_and_no_wrap():
    from PIL import ImageFont
    from arabic_video_brief.v2.renderer import wrap_v2_text_with_highlights
    settings = get_settings()
    font = ImageFont.truetype(str(settings.font_path), 46)
    try:
        font.set_variation_by_axes([700, 100])
    except Exception:
        pass

    text = "قد تظن أن الإرهاق مجرد <hl>تعب جسدي عابر</hl> يزول بالنوم، لكن الحقيقة هي <hl>وكيمياء عصبية تختفي</hl> تدريجياً."
    lines = wrap_v2_text_with_highlights(text, font, 815)

    # Verify no highlighted phrase was broken across lines
    hl_count = sum(line.count("<hl>") for line in lines)
    hl_close_count = sum(line.count("</hl>") for line in lines)
    assert hl_count == 2
    assert hl_close_count == 2
    for line in lines:
        if "<hl>" in line:
            assert "</hl>" in line  # Opening and closing must be on the SAME line (No-wrap rule)


def test_v2_tag_stripping_plain_text():
    import re
    from arabic_video_brief.v2.editorial import build_v2_editorial_package
    settings = get_settings()
    pages = [
        "هذه الصفحة تتضمن <hl>عبارة مميزة أولى</hl> و <hl>عبارة مميزة ثانية</hl> بالكامل.",
        "الصفحة الثانية فيها <hl>وكيمياء عصبية</hl> مهمة جداً للشرح.",
        "الصفحة الثالثة تشرح <hl>فكرة تطبيقية</hl> واضحة.",
        "الصفحة الرابعة تلخص <hl>النتيجة النهائية</hl> للموضوع.",
    ]
    pkg = build_v2_editorial_package({
        "post_title_ar": "عنوان تجريبي",
        "pages": pages,
        "ending_question_ar": "ما هو رأيك في التجربة؟",
    }, {}, settings)

    # editorial.pages retains <hl> tags for visual renderer
    assert "<hl>" in pkg.pages[0]
    # editorial.summary_ar has <hl> tags stripped for plain text logs/descriptions
    assert "<hl>" not in pkg.summary_ar
    assert "</hl>" not in pkg.summary_ar

