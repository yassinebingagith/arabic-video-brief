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
        conclusion_ar="صباحك الأفضل يبدأ من الضوء الذي تخفّضه الليلة",
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
