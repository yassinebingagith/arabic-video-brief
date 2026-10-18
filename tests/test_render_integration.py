from pathlib import Path

import pytest

from arabic_video_brief.config import Settings
from arabic_video_brief.media import find_ffmpeg, probe_media, render_video


def test_render_v1_38_seconds_with_question_and_audio(tmp_path: Path) -> None:
    settings = Settings()
    if not settings.font_path.exists():
        pytest.skip("Bundled font has not been downloaded")
    try:
        ffmpeg = find_ffmpeg()
    except RuntimeError:
        pytest.skip("FFmpeg is unavailable")
    source = tmp_path / "source.mp4"
    fixture_command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
        "-t", "12", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", str(source),
    ]
    import subprocess

    subprocess.run(fixture_command, check=True, timeout=120)
    output = tmp_path / "brief.mp4"
    selected = {"start_seconds": 1.0, "focal_x": 0.5, "focal_y": 0.5}
    details = render_video(
        source,
        None,
        "تقدم الصفحة الأولى ملخصًا واضحًا ومباشرًا للفكرة الأساسية مع الحفاظ على الدقة وسهولة القراءة.",
        "وتكمل الصفحة الثانية النتيجة المهمة بأسلوب عربي فصيح يناسب مقاطع الفيديو القصيرة على الهاتف.",
        selected,
        output,
        settings,
        ending_question="ما المهارة التي تؤجل التدرب على أصعب جزء فيها؟",
    )
    info = probe_media(output, ffmpeg)
    assert (info.width, info.height) == (1080, 1920)
    assert 37.8 <= info.duration <= 38.2
    assert info.has_audio is True
    assert details["timeline"] == {"page_1": [0, 15], "page_2": [15, 30], "ending": [30, 38]}
    # The old 20s asset left page two silent: check actual decoded late-page audio.
    import array
    audio = subprocess.run([
        ffmpeg, "-loglevel", "error", "-ss", "24", "-i", str(output),
        "-t", "3", "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "-",
    ], check=True, capture_output=True).stdout
    samples = array.array("f", audio)
    rms = (sum(value * value for value in samples) / len(samples)) ** 0.5
    assert rms > 0.001, "Background music must continue after 20 seconds"
