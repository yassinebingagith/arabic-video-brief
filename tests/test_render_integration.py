from pathlib import Path

import pytest

from arabic_video_brief.config import Settings
from arabic_video_brief.media import find_ffmpeg, probe_media, render_video


def test_render_exact_vertical_silent_video(tmp_path: Path) -> None:
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
    render_video(
        source,
        None,
        "تقدم الصفحة الأولى ملخصًا واضحًا ومباشرًا للفكرة الأساسية مع الحفاظ على الدقة وسهولة القراءة.",
        "وتكمل الصفحة الثانية النتيجة المهمة بأسلوب عربي فصيح يناسب مقاطع الفيديو القصيرة على الهاتف.",
        selected,
        output,
        settings,
    )
    info = probe_media(output, ffmpeg)
    assert (info.width, info.height) == (1080, 1920)
    assert 27.8 <= info.duration <= 28.2
    assert info.has_audio is True
