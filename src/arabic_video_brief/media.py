from __future__ import annotations

import json
import math
import os
import random
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings


@dataclass(frozen=True)
class MediaInfo:
    width: int
    height: int
    duration: float
    has_audio: bool = False


def find_ffmpeg() -> str:
    override = os.environ.get("FFMPEG_BINARY")
    if override and Path(override).exists():
        return override
    bundled = Path(__file__).resolve().parents[2] / "bin" / "ffmpeg.exe"
    if bundled.exists():
        return str(bundled)
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as error:
        raise RuntimeError("FFmpeg is unavailable; run scripts/setup.ps1") from error


def _run(command: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(command, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    if process.returncode != 0:
        tail = (process.stderr or process.stdout)[-2500:]
        raise RuntimeError(f"Media command failed: {tail}")
    return process


def probe_media(path: Path, ffmpeg: str | None = None) -> MediaInfo:
    executable = ffmpeg or find_ffmpeg()
    process = subprocess.run([executable, "-hide_banner", "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = process.stderr
    duration_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if not duration_match:
        raise RuntimeError(f"Could not read media metadata for {path}")
    hours, minutes, seconds = duration_match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    video_match = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", output)
    width = int(video_match.group(1)) if video_match else 0
    height = int(video_match.group(2)) if video_match else 0
    has_audio = bool(re.search(r"Audio:\s*", output))
    return MediaInfo(width, height, duration, has_audio)


def _extract_captions(auto_subs: dict[str, Any] | None) -> str:
    if not auto_subs:
        return ""
    import json
    from urllib.request import Request, urlopen
    for lang in ("en", "en-US", "en-GB", "ar"):
        formats = auto_subs.get(lang) or []
        json3 = next((s for s in formats if s.get("ext") == "json3"), None)
        if json3 and json3.get("url"):
            try:
                req = Request(json3["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    words: list[str] = []
                    for ev in data.get("events", []):
                        for seg in ev.get("segs", []):
                            w = seg.get("utf8", "").strip()
                            if w:
                                words.append(w)
                    if words:
                        return " ".join(words)
            except Exception:
                pass
    return ""


def download_youtube(url: str, work_dir: Path, download_seconds: float = 40.0) -> dict[str, Any]:
    try:
        import yt_dlp
        from yt_dlp.utils import download_range_func
    except ImportError as error:
        raise RuntimeError("yt-dlp is not installed; run scripts/setup.ps1") from error
    ffmpeg = find_ffmpeg()
    options = {
        "format": "bestvideo[ext=mp4][height<=720]/bestvideo[height<=720]",
        "download_ranges": download_range_func(None, [(0, int(download_seconds))]),
        "force_keyframes_at_cuts": True,
        "outtmpl": str(work_dir / "source.%(ext)s"),
        "writethumbnail": True,
        "writeinfojson": False,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "ffmpeg_location": str(Path(ffmpeg).parent),
        "http_headers": {"Accept-Language": "en-US,en;q=0.9"},
        "retries": 2,
        "fragment_retries": 2,
    }
    original_path = os.environ.get("PATH", "")
    os.environ["PATH"] = str(Path(ffmpeg).parent) + os.pathsep + original_path
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
    finally:
        os.environ["PATH"] = original_path
    videos = [path for path in work_dir.glob("source.*") if path.suffix.lower() in {".mp4", ".webm", ".mkv", ".mov"}]
    if not videos:
        raise RuntimeError("YouTube download completed without a usable video file")
    thumbnails = [path for path in work_dir.glob("source.*") if path not in videos and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    auto_subs = info.get("automatic_captions") or info.get("subtitles") or {}
    transcript_text = _extract_captions(auto_subs)
    return {
        "title": info.get("title") or "YouTube video",
        "id": info.get("id"),
        "uploader": info.get("uploader"),
        "channel": info.get("channel") or info.get("uploader"),
        "view_count": info.get("view_count"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "description": info.get("description") or "",
        "transcript_text": transcript_text,
        "video_path": videos[0],
        "thumbnail_path": thumbnails[0] if thumbnails else None,
        "webpage_url": info.get("webpage_url") or url,
    }


def _extract_frame(video: Path, timestamp: float, output: Path, ffmpeg: str) -> None:
    _run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, timestamp):.3f}", "-i", str(video),
        "-frames:v", "1", "-q:v", "2", "-y", str(output),
    ], timeout=120)


def _frame_score(paths: list[Path]) -> tuple[float, tuple[float, float]]:
    from PIL import Image, ImageChops, ImageStat

    images = [Image.open(path).convert("RGB") for path in paths]
    luminances: list[float] = []
    contrasts: list[float] = []
    for image in images:
        stat = ImageStat.Stat(image.convert("L"))
        luminances.append(stat.mean[0])
        contrasts.append(stat.stddev[0])
    valid_light = sum(1 for value in luminances if 20 <= value <= 235) / len(images)
    contrast = min(1.0, sum(contrasts) / len(contrasts) / 64.0)
    motion = 0.0
    if len(images) > 1:
        differences = [ImageStat.Stat(ImageChops.difference(a, b).convert("L")).mean[0] for a, b in zip(images, images[1:])]
        motion = min(1.0, sum(differences) / len(differences) / 35.0)
    face_bonus = 0.0
    centers: list[tuple[float, float]] = []
    try:
        import cv2
        import numpy as np

        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(str(cascade_path))
        for image in images:
            array = np.array(image)
            gray = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
            faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
            if len(faces):
                x, y, width, height = max(faces, key=lambda rect: rect[2] * rect[3])
                centers.append(((x + width / 2) / image.width, (y + height / 2) / image.height))
        face_bonus = min(0.2, len(centers) / len(images) * 0.2)
    except (ImportError, AttributeError):
        pass
    focal = (
        sum(center[0] for center in centers) / len(centers),
        sum(center[1] for center in centers) / len(centers),
    ) if centers else (0.5, 0.5)
    return valid_light * 0.35 + contrast * 0.2 + motion * 0.25 + face_bonus, focal


def select_clip(video: Path, candidates: list[dict[str, Any]], ffmpeg: str | None = None) -> dict[str, Any]:
    executable = ffmpeg or find_ffmpeg()
    info = probe_media(video, executable)
    clip_length = min(10.0, info.duration)
    normalized: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates[:3]):
        requested = float(candidate.get("start_seconds", 0) or 0)
        start = max(0.0, min(requested, max(0.0, info.duration - clip_length)))
        with tempfile.TemporaryDirectory(prefix="avbrief-score-") as temp_name:
            temp = Path(temp_name)
            frame_paths: list[Path] = []
            for frame_index, ratio in enumerate((0.1, 0.3, 0.5, 0.7, 0.9)):
                path = temp / f"frame-{frame_index}.jpg"
                _extract_frame(video, start + clip_length * ratio, path, executable)
                if path.exists():
                    frame_paths.append(path)
            visual_score, focal = _frame_score(frame_paths) if frame_paths else (0.0, (0.5, 0.5))
        semantic = max(0.0, min(1.0, float(candidate.get("semantic_score", 0.5) or 0.5)))
        normalized.append({
            **candidate,
            "start_seconds": start,
            "end_seconds": start + clip_length,
            "semantic_score": semantic,
            "visual_score": visual_score,
            "combined_score": semantic * 0.65 + visual_score * 0.35,
            "focal_x": focal[0],
            "focal_y": focal[1],
            "candidate_index": index,
        })
    if not normalized:
        normalized.append({
            "start_seconds": 0.0,
            "end_seconds": clip_length,
            "reason": "Fallback to the earliest available segment",
            "semantic_score": 0.0,
            "visual_score": 0.0,
            "combined_score": 0.0,
            "focal_x": 0.5,
            "focal_y": 0.5,
            "candidate_index": 0,
        })
    return max(normalized, key=lambda item: item["combined_score"])


def _crop_filter(info: MediaInfo, target_width: int, target_height: int, focal_x: float, focal_y: float) -> str:
    target_aspect = target_width / target_height
    source_aspect = info.width / info.height
    if source_aspect > target_aspect:
        crop_height = info.height
        crop_width = max(2, int(crop_height * target_aspect) // 2 * 2)
        x = int(focal_x * info.width - crop_width / 2)
        x = max(0, min(info.width - crop_width, x))
        y = 0
    else:
        crop_width = info.width
        crop_height = max(2, int(crop_width / target_aspect) // 2 * 2)
        x = 0
        y = int(focal_y * info.height - crop_height / 2)
        y = max(0, min(info.height - crop_height, y))
    return f"crop={crop_width}:{crop_height}:{x}:{y},scale={target_width}:{target_height}:flags=lanczos,setsar=1"


def _contain_filter(target_width: int, target_height: int) -> str:
    return (
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )


def _shape_line(text: str) -> str:
    import arabic_reshaper
    from bidi.algorithm import get_display

    return get_display(arabic_reshaper.reshape(text), base_dir="R")


def _wrap_rtl(text: str, font: Any, max_width: int) -> list[str]:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines: list[str] = []
    current: list[str] = []
    for word in text.split():
        candidate = " ".join([*current, word])
        width = draw.textbbox((0, 0), _shape_line(candidate), font=font)[2]
        if current and width > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _compact_count(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return ""
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if number >= threshold:
            compact = number / threshold
            return f"{compact:.1f}".rstrip("0").rstrip(".") + suffix
    return str(number)


def _metadata_line(metadata: dict[str, Any]) -> str:
    channel = str(metadata.get("channel") or metadata.get("uploader") or "YouTube")
    fields = [channel]
    views = _compact_count(metadata.get("view_count"))
    if views:
        fields.append(f"{views} views")
    upload_date = str(metadata.get("upload_date") or "")
    if len(upload_date) == 8 and upload_date.isdigit():
        fields.append(f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}")
    return " · ".join(fields)


def sanitize_display_text(text: str) -> str:
    if not text:
        return ""
    # Strip emojis and unrenderable unicode symbols that cause empty square boxes in Noto Sans Arabic
    emoji_pattern = re.compile(
        "["
        "\U00010000-\U0010ffff"  # Supplementary planes / emojis
        "\u2190-\u21ff"          # Arrows (including ↓, →, etc.)
        "\u2300-\u23ff"          # Misc technical
        "\u2460-\u24ff"          # Enclosed alphanumerics
        "\u25a0-\u25ff"          # Geometric shapes
        "\u2600-\u27bf"          # Misc symbols & Dingbats
        "\u2b00-\u2bff"          # Misc symbols and arrows
        "\ufe00-\ufe0f"          # Variation selectors
        "]+",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _display_text(text: str) -> str:
    clean = sanitize_display_text(text)
    return _shape_line(clean) if re.search(r"[\u0600-\u06FF]", clean) else clean


def _wrap_display_text(text: str, font: Any, max_width: int) -> list[str]:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines: list[str] = []
    current: list[str] = []
    for word in text.split():
        candidate = " ".join([*current, word])
        if current and draw.textbbox((0, 0), _display_text(candidate), font=font)[2] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _balance_wrap(text: str, font: Any, max_width: int) -> list[str]:
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    clean_text = text.strip()
    if draw.textbbox((0, 0), _display_text(clean_text), font=font)[2] <= max_width:
        return [clean_text]
    words = clean_text.split()
    best_split: list[str] | None = None
    min_diff = float("inf")
    for i in range(1, len(words)):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:])
        w1 = draw.textbbox((0, 0), _display_text(l1), font=font)[2]
        w2 = draw.textbbox((0, 0), _display_text(l2), font=font)[2]
        if w1 <= max_width and w2 <= max_width:
            diff = abs(w1 - w2)
            if diff < min_diff:
                min_diff = diff
                best_split = [l1, l2]
    if best_split:
        return best_split
    return _wrap_display_text(clean_text, font, max_width)


def render_metadata_bar(metadata: dict[str, Any], output: Path, settings: Settings, metadata_height: int = 152) -> None:
    from PIL import Image, ImageDraw, ImageFont

    canvas = Image.new("RGB", (settings.width, metadata_height), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)

    avatar_size = 90
    avatar_x = 32
    avatar_y = (metadata_height - avatar_size) // 2
    draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size), fill="#1A1A1A")
    avatar_font = ImageFont.truetype(str(settings.font_path), 42)
    try:
        avatar_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass
    channel = str(metadata.get("channel") or metadata.get("uploader") or "Y")
    initial = next((char for char in channel.strip() if not char.isspace()), "Y")
    initial_visual = _display_text(initial)
    box = draw.textbbox((0, 0), initial_visual, font=avatar_font)
    draw.text(
        (avatar_x + (avatar_size - (box[2] - box[0])) / 2, avatar_y + (avatar_size - (box[3] - box[1])) / 2 - box[1]),
        initial_visual,
        font=avatar_font,
        fill="#FFFFFF",
    )

    text_x = avatar_x + avatar_size + 24
    text_right = settings.width - 32
    text_width = max(80, text_right - text_x)
    title = str(metadata.get("title") or "Video")

    title_font = ImageFont.truetype(str(settings.font_path), 34)
    try:
        title_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    title_lines = _balance_wrap(title, title_font, text_width)
    if len(title_lines) > 2:
        title_font = ImageFont.truetype(str(settings.font_path), 28)
        try:
            title_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        title_lines = _balance_wrap(title, title_font, text_width)

    ty = 16 if len(title_lines) >= 2 else 34
    for line in title_lines[:2]:
        visual = _display_text(line)
        draw.text((text_x, ty), visual, font=title_font, fill="#0A0A0A")
        ty += title_font.size + 8

    detail = _metadata_line(metadata)
    detail_font = ImageFont.truetype(str(settings.font_path), 24)
    try:
        detail_font.set_variation_by_name("SemiBold")
    except (AttributeError, OSError, ValueError):
        pass
    detail_visual = _display_text(detail)
    draw.text((text_x, metadata_height - 38), detail_visual, font=detail_font, fill="#525252")
    canvas.save(output, format="PNG")


def render_source_card(thumbnail: Path, metadata: dict[str, Any], output: Path, settings: Settings) -> None:
    from PIL import Image, ImageOps

    canvas = Image.new("RGB", (settings.width, settings.top_height), "#000000")
    with Image.open(thumbnail) as source_image:
        fitted = ImageOps.fit(source_image.convert("RGB"), (settings.width, settings.top_height), Image.Resampling.LANCZOS)
    canvas.paste(fitted, (0, 0))
    canvas.save(output, format="PNG")


def render_top_overlay(metadata: dict[str, Any], output: Path, settings: Settings) -> None:
    """
    Renders an RGBA overlay for the 1080x760 top video panel:
    1. A smooth alpha gradient at the bottom (y=490 to 760) fading the video into #000000,
       eliminating all hard borders and letterbox edges.
    2. An organized, spacious translucent glassmorphic badge (y=556, h=176, w=1016)
       displaying the full video title (multi-line without truncation), red YouTube play
       icon, channel name, views count, and upload date clearly with generous breathing room.
       Fully respects RTL (right-to-left) alignment and element order for Arabic content.
    """
    import re
    from PIL import Image, ImageDraw, ImageFont

    width = settings.width
    height = settings.top_height
    fade_start = 490

    # Fast smooth alpha gradient layer
    alpha_strip = Image.new("L", (1, height), 0)
    for y in range(fade_start, height):
        ratio = (y - fade_start) / (height - fade_start)
        alpha = int(255 * (ratio ** 1.6))
        alpha_strip.putpixel((0, y), min(255, alpha))
    alpha_mask = alpha_strip.resize((width, height), Image.Resampling.NEAREST)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    overlay.putalpha(alpha_mask)

    draw = ImageDraw.Draw(overlay)

    # Organized multi-line glassmorphic badge
    pill_w = 1016
    pill_h = 176
    pill_x = (width - pill_w) // 2
    pill_y = 556

    # Sleek dark translucent glassmorphic card
    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=26,
        fill=(14, 16, 24, 230),
        outline=(255, 255, 255, 55),
        width=2,
    )

    title = str(metadata.get("title") or "Video").strip()
    channel_name = str(metadata.get("channel") or metadata.get("uploader") or "YouTube").strip()
    is_rtl = bool(re.search(r"[\u0600-\u06FF]", title + channel_name))

    avatar_size = 68
    avatar_y = pill_y + (pill_h - avatar_size) // 2

    if is_rtl:
        avatar_x = (pill_x + pill_w) - 24 - avatar_size
        text_right = avatar_x - 24
        text_left = pill_x + 24
        text_max_w = text_right - text_left
    else:
        avatar_x = pill_x + 24
        text_left = avatar_x + avatar_size + 24
        text_right = (pill_x + pill_w) - 24
        text_max_w = text_right - text_left

    # Red circular YouTube play icon
    draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size), fill=(225, 29, 72, 255))
    tcx = avatar_x + avatar_size // 2 + 1
    tcy = avatar_y + avatar_size // 2
    draw.polygon([(tcx - 8, tcy - 12), (tcx - 8, tcy + 12), (tcx + 13, tcy)], fill=(255, 255, 255, 255))

    font_title = ImageFont.truetype(str(settings.font_path), 26)
    try:
        font_title.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    lines = _balance_wrap(title, font_title, text_max_w)
    if len(lines) > 2:
        font_title = ImageFont.truetype(str(settings.font_path), 23)
        try:
            font_title.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        lines = _balance_wrap(title, font_title, text_max_w)

    line_h = font_title.size + 10
    if len(lines) == 1:
        ty = pill_y + 34
    elif len(lines) == 2:
        ty = pill_y + 18
    else:
        ty = pill_y + 12

    for line in lines[:3]:
        vis = _display_text(line)
        box = draw.textbbox((0, 0), vis, font=font_title)
        line_w = box[2] - box[0]
        tx = text_right - line_w if is_rtl else text_left
        draw.text((tx, ty), vis, font=font_title, fill=(255, 255, 255, 255))
        ty += line_h

    # Metadata row: Channel • Views • Date
    font_channel = ImageFont.truetype(str(settings.font_path), 22)
    try:
        font_channel.set_variation_by_name("SemiBold")
    except (AttributeError, OSError, ValueError):
        pass

    font_sub = ImageFont.truetype(str(settings.font_path), 21)

    channel_vis = _display_text(channel_name)
    views_cnt = metadata.get("view_count")
    views_str = f"{_compact_count(views_cnt)} views" if views_cnt else ""

    raw_date = str(metadata.get("upload_date") or "").strip()
    date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}" if len(raw_date) == 8 and raw_date.isdigit() else raw_date

    my = pill_y + pill_h - 58

    if is_rtl:
        cur_r = text_right
        # 1. Channel
        ch_box = draw.textbbox((0, 0), channel_vis, font=font_channel)
        ch_w = ch_box[2] - ch_box[0]
        draw.text((cur_r - ch_w, my), channel_vis, font=font_channel, fill=(243, 244, 246, 255))
        cur_r -= ch_w + 12

        # 2. Bullet + Views
        if views_str:
            b_box = draw.textbbox((0, 0), "•", font=font_sub)
            b_w = b_box[2] - b_box[0]
            draw.text((cur_r - b_w, my), "•", font=font_sub, fill=(156, 163, 175, 220))
            cur_r -= b_w + 12

            v_box = draw.textbbox((0, 0), views_str, font=font_sub)
            v_w = v_box[2] - v_box[0]
            draw.text((cur_r - v_w, my), views_str, font=font_sub, fill=(209, 213, 219, 230))
            cur_r -= v_w + 12

        # 3. Bullet + Date
        if date_str:
            b_box = draw.textbbox((0, 0), "•", font=font_sub)
            b_w = b_box[2] - b_box[0]
            draw.text((cur_r - b_w, my), "•", font=font_sub, fill=(156, 163, 175, 220))
            cur_r -= b_w + 12

            d_box = draw.textbbox((0, 0), date_str, font=font_sub)
            d_w = d_box[2] - d_box[0]
            draw.text((cur_r - d_w, my), date_str, font=font_sub, fill=(209, 213, 219, 230))
    else:
        cur_x = text_left
        draw.text((cur_x, my), channel_vis, font=font_channel, fill=(243, 244, 246, 255))
        ch_box = draw.textbbox((cur_x, my), channel_vis, font=font_channel)
        cur_x = ch_box[2] + 12

        if views_str:
            draw.text((cur_x, my), "•", font=font_sub, fill=(156, 163, 175, 220))
            b_box = draw.textbbox((cur_x, my), "•", font=font_sub)
            cur_x = b_box[2] + 12

            draw.text((cur_x, my), views_str, font=font_sub, fill=(209, 213, 219, 230))
            v_box = draw.textbbox((cur_x, my), views_str, font=font_sub)
            cur_x = v_box[2] + 12

        if date_str:
            draw.text((cur_x, my), "•", font=font_sub, fill=(156, 163, 175, 220))
            b_box = draw.textbbox((cur_x, my), "•", font=font_sub)
            cur_x = b_box[2] + 12

            draw.text((cur_x, my), date_str, font=font_sub, fill=(209, 213, 219, 230))

    overlay.save(output, format="PNG")


def infer_category(metadata: dict[str, Any] | None = None, summary_text: str = "") -> str:
    if not metadata:
        metadata = {}
    combined = (
        str(metadata.get("title") or "")
        + " "
        + str(metadata.get("description") or "")
        + " "
        + " ".join(metadata.get("tags") or [])
        + " "
        + " ".join(metadata.get("categories") or [])
        + " "
        + summary_text
    ).lower()

    if any(k in combined for k in ["نفس", "psychology", "سلوك", "علاقات", "مشاعر", "love", "تواصل", "questions"]):
        return "علم نفس / تنمية وتواصل"
    elif any(k in combined for k in ["اقتصاد", "مال", "استثمار", "economy", "finance", "money", "تضخم", "أسواق"]):
        return "اقتصاد وأعمال"
    elif any(k in combined for k in ["سياسة", "politics", "حرب", "دولة", "حكومة", "نظام", "انتخابات"]):
        return "سياسة وشؤون دولية"
    elif any(k in combined for k in ["تاريخ", "تراث", "فلسفة", "دين", "تيه", "المن", "سرديات", "قديمة", "أساطير"]):
        return "تاريخ وفكر نقدي"
    elif any(k in combined for k in ["تكنولوجيا", "ذكاء اصطناعي", "برمجة", "تقنية", "ai", "tech"]):
        return "تكنولوجيا وعلوم"
    elif any(k in combined for k in ["صحة", "طب", "تغذية", "حمية", "طبي", "لقاحات"]):
        return "صحة وطب ونقد علمي"
    return "ثقافة وفكر عام"


def render_text_page(
    text: str,
    output: Path,
    settings: Settings,
    main_title: str | None = None,
    header: str | None = None,
    sub_header: str | None = None,
    footer: str | None = None,
) -> int:
    from PIL import Image, ImageDraw, ImageFont

    if not settings.font_path.exists():
        raise RuntimeError(f"Bundled Arabic font is missing: {settings.font_path}")
    image = Image.new("RGB", (settings.width, settings.height), "#000000")
    draw = ImageDraw.Draw(image)
    panel_top = settings.top_height
    has_frame = bool(settings.brand_frame_path and settings.brand_frame_path.exists())
    if has_frame:
        # Platform-safe bounding box ensuring zero collision with TikTok/Reels/Shorts UI overlays
        # Left edge: 110px (inset from left border to avoid hugging the edge)
        # Right edge: 850px (leaving 230px safety clearance from Like/Comment/Share icons at x >= 975)
        # Top edge: 800px (20px below top video panel)
        # Bottom edge: 1520px (leaving 400px / 20.8% margin from screen bottom for timeline scroller & channel handle)
        safe_left = 110
        safe_right = 850
        max_width = safe_right - safe_left  # 740px
        safe_top = 800
        safe_bottom = 1520
        available_height = safe_bottom - safe_top  # 720px
        zone_mid = (safe_left + safe_right) // 2
    else:
        bottom_safe_margin = int(settings.height * 0.15)
        side_margin = 100
        max_width = settings.width - (side_margin * 2)
        safe_top = panel_top + 24
        safe_bottom = settings.height - bottom_safe_margin - 24
        available_height = safe_bottom - safe_top
        zone_mid = settings.width // 2

    main_font = None
    header_font = None
    sub_font = None
    footer_font = None
    m_lines: list[str] = []
    h_vis = None
    s_vis = None
    f_vis = None
    header_block_height = 0
    footer_block_height = 0

    if main_title:
        title_sz = 34 if has_frame else 36
        main_font = ImageFont.truetype(str(settings.font_path), title_sz)
        try:
            main_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        m_lines = _balance_wrap(main_title, main_font, max_width)
        main_line_h = math.ceil(title_sz * 1.35)
        header_block_height += len(m_lines) * main_line_h + (8 if has_frame else 14)

    if header:
        h_sz = 26 if has_frame else 28
        header_font = ImageFont.truetype(str(settings.font_path), h_sz)
        try:
            header_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        h_vis = _display_text(header)
        h_box = draw.textbbox((0, 0), h_vis, font=header_font)
        header_block_height += (h_box[3] - h_box[1]) + (6 if has_frame else 10)

    if sub_header:
        s_sz = 22 if has_frame else 22
        sub_font = ImageFont.truetype(str(settings.font_path), s_sz)
        try:
            sub_font.set_variation_by_name("Medium")
        except (AttributeError, OSError, ValueError):
            pass
        s_vis = _display_text(sub_header)
        s_box = draw.textbbox((0, 0), s_vis, font=sub_font)
        header_block_height += (s_box[3] - s_box[1]) + (12 if has_frame else 20)

    if footer:
        f_sz = 28 if has_frame else 28
        footer_font = ImageFont.truetype(str(settings.font_path), f_sz)
        try:
            footer_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        f_vis = _display_text(footer)
        f_box = draw.textbbox((0, 0), f_vis, font=footer_font)
        footer_block_height += (f_box[3] - f_box[1]) + (14 if has_frame else 24)

    chosen: tuple[Any, list[str], int] | None = None
    search_max = 38 if has_frame else settings.font_size
    search_min = 24 if has_frame else settings.min_font_size
    for size in range(search_max, search_min - 1, -1):
        font = ImageFont.truetype(str(settings.font_path), size)
        try:
            font.set_variation_by_name("SemiBold")
        except (AttributeError, OSError, ValueError):
            pass
        lines = _wrap_rtl(text, font, max_width)
        line_height = math.ceil(size * (1.45 if has_frame else 1.55))
        if (header_block_height + footer_block_height + len(lines) * line_height) <= available_height:
            chosen = (font, lines, line_height)
            break
    if chosen is None:
        font = ImageFont.truetype(str(settings.font_path), search_min)
        try:
            font.set_variation_by_name("SemiBold")
        except (AttributeError, OSError, ValueError):
            pass
        lines = _wrap_rtl(text, font, max_width)
        line_height = math.ceil(search_min * (1.45 if has_frame else 1.55))
        chosen = (font, lines, line_height)

    font, lines, line_height = chosen
    total_content_height = header_block_height + footer_block_height + len(lines) * line_height
    cur_y = safe_top + (available_height - total_content_height) // 2
    x_offset = 0 if has_frame else int(settings.width * settings.text_offset_ratio)

    if main_title and m_lines and main_font:
        main_line_h = math.ceil((34 if has_frame else 36) * 1.35)
        for m_line in m_lines:
            m_vis = _display_text(m_line)
            m_box = draw.textbbox((0, 0), m_vis, font=main_font)
            m_w = m_box[2] - m_box[0]
            x_pos = (zone_mid - m_w // 2) if has_frame else ((settings.width - m_w) // 2 - x_offset)
            draw.text((x_pos, cur_y), m_vis, font=main_font, fill="#FFFFFF")
            cur_y += main_line_h
        cur_y += 8 if has_frame else 14

    if header and h_vis and header_font:
        h_box = draw.textbbox((0, 0), h_vis, font=header_font)
        h_w = h_box[2] - h_box[0]
        x_pos = (zone_mid - h_w // 2) if has_frame else ((settings.width - h_w) // 2 - x_offset)
        draw.text((x_pos, cur_y), h_vis, font=header_font, fill="#FFD700")
        cur_y += (h_box[3] - h_box[1]) + (6 if has_frame else 10)

    if sub_header and s_vis and sub_font:
        s_box = draw.textbbox((0, 0), s_vis, font=sub_font)
        s_w = s_box[2] - s_box[0]
        x_pos = (zone_mid - s_w // 2) if has_frame else ((settings.width - s_w) // 2 - x_offset)
        draw.text((x_pos, cur_y), s_vis, font=sub_font, fill="#A3A3A3")
        cur_y += (s_box[3] - s_box[1]) + (12 if has_frame else 20)

    for logical_line in lines:
        visual_line = _shape_line(logical_line)
        bounds = draw.textbbox((0, 0), visual_line, font=font)
        width = bounds[2] - bounds[0]
        x_pos = (zone_mid - width // 2) if has_frame else ((settings.width - width) // 2 - x_offset)
        draw.text((x_pos, cur_y), visual_line, font=font, fill="#F0F0F0")
        cur_y += line_height

    if footer and f_vis and footer_font:
        cur_y += 10 if has_frame else 16
        f_box = draw.textbbox((0, 0), f_vis, font=footer_font)
        f_w = f_box[2] - f_box[0]
        x_pos = (zone_mid - f_w // 2) if has_frame else ((settings.width - f_w) // 2 - x_offset)
        draw.text((x_pos, cur_y), f_vis, font=footer_font, fill="#38BDF8")
    image.save(output, format="PNG")
    return font.size


def render_v1_cta_page(
    output_path: Path,
    settings: Settings,
    avatar_path: Path | None = None,
) -> None:
    """
    Renders the dedicated 5-second Call-To-Action ending page (1080x1920) for V1 (20s - 25s):
    - Top panel (1080x760): Fixed static YouTube source card.
    - Bottom panel (1080x1160):
      - No conclusion text.
      - Action Pill Box: "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد" (enlarged, 15% safe margin).
      - Capsule Fikr Logo & Brand label.
      - Primary Description Gold Badge: "السر الأهم والخطوات التطبيقية في الوصف بالأسفل" with downward chevron.
    """
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (settings.width, settings.height), "#000000")
    draw = ImageDraw.Draw(image)

    panel_top = settings.top_height
    side_safe_margin = int(settings.width * 0.15)  # 162px (15% platform safe margin)
    max_safe_width = settings.width - (2 * side_safe_margin)  # 756px

    # 1. Action Pill Box (Save / Share / Follow): Enlarged, high contrast, clean
    action_text = "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد"
    cur_save_size = 34
    save_font = ImageFont.truetype(str(settings.font_path), cur_save_size)
    try:
        save_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    save_vis = _display_text(action_text)
    s_box = draw.textbbox((0, 0), save_vis, font=save_font)
    sw = s_box[2] - s_box[0]

    target_pill_text_max = max_safe_width - 48
    while sw > target_pill_text_max and cur_save_size > 24:
        cur_save_size -= 1
        save_font = ImageFont.truetype(str(settings.font_path), cur_save_size)
        try:
            save_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        s_box = draw.textbbox((0, 0), save_vis, font=save_font)
        sw = s_box[2] - s_box[0]

    save_pill_w = min(sw + 56, max_safe_width)
    save_pill_h = 68
    save_pill_x = (settings.width - save_pill_w) // 2
    save_pill_y = panel_top + 100

    draw.rounded_rectangle(
        (save_pill_x, save_pill_y, save_pill_x + save_pill_w, save_pill_y + save_pill_h),
        radius=save_pill_h // 2,
        fill="#141418",
        outline="#F5C518",
        width=2,
    )
    draw.text(
        (save_pill_x + (save_pill_w - sw) // 2, save_pill_y + (save_pill_h - (s_box[3] - s_box[1])) // 2 - s_box[1]),
        save_vis,
        font=save_font,
        fill="#FFFFFF",
    )

    # 2. Capsule Fikr Logo & Brand Label
    logo_size = 150
    logo_x = (settings.width - logo_size) // 2
    logo_y = save_pill_y + save_pill_h + 40

    target_avatar = avatar_path or settings.brand_avatar_path
    if target_avatar and target_avatar.exists():
        try:
            av_img = Image.open(target_avatar).convert("RGBA")
            av_img = av_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, logo_size, logo_size), fill=255)
            image.paste(av_img, (logo_x, logo_y), mask)
            draw.ellipse((logo_x, logo_y, logo_x + logo_size, logo_y + logo_size), outline="#F5C518", width=4)
        except Exception as err:
            logger.warning("Failed to render avatar logo in V1 CTA page: %s", err)

    brand_font = ImageFont.truetype(str(settings.font_path), 32)
    try:
        brand_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass
    brand_vis = _display_text("كبسولة فكر")
    b_box = draw.textbbox((0, 0), brand_vis, font=brand_font)
    bw = b_box[2] - b_box[0]
    brand_y = logo_y + logo_size + 14
    draw.text(((settings.width - bw) // 2, brand_y), brand_vis, font=brand_font, fill="#F5C518")

    # 3. Primary Description CTA: Filled Glowing Gold Badge within 15% safe margin
    desc_cta_text = "السر الأهم والخطوات التطبيقية في الوصف بالأسفل"
    cur_desc_size = 36
    desc_font = ImageFont.truetype(str(settings.font_path), cur_desc_size)
    try:
        desc_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    d_vis = _display_text(desc_cta_text)
    d_box = draw.textbbox((0, 0), d_vis, font=desc_font)
    dw = d_box[2] - d_box[0]

    target_badge_text_max = max_safe_width - 64
    while dw > target_badge_text_max and cur_desc_size > 26:
        cur_desc_size -= 1
        desc_font = ImageFont.truetype(str(settings.font_path), cur_desc_size)
        try:
            desc_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        d_box = draw.textbbox((0, 0), d_vis, font=desc_font)
        dw = d_box[2] - d_box[0]

    desc_pill_w = min(dw + 64, max_safe_width)
    desc_pill_h = 88
    desc_pill_x = (settings.width - desc_pill_w) // 2
    desc_pill_y = max(brand_y + 50, 1340)

    # Subtle outer glow shadow
    draw.rounded_rectangle(
        (desc_pill_x - 3, desc_pill_y - 3, desc_pill_x + desc_pill_w + 3, desc_pill_y + desc_pill_h + 3),
        radius=desc_pill_h // 2,
        fill="#5A4700",
    )
    # Main filled Gold badge
    draw.rounded_rectangle(
        (desc_pill_x, desc_pill_y, desc_pill_x + desc_pill_w, desc_pill_y + desc_pill_h),
        radius=desc_pill_h // 2,
        fill="#F5C518",
        outline="#FFE066",
        width=3,
    )
    draw.text(
        (desc_pill_x + (desc_pill_w - dw) // 2, desc_pill_y + (desc_pill_h - (d_box[3] - d_box[1])) // 2 - d_box[1]),
        d_vis,
        font=desc_font,
        fill="#000000",
    )

    # Downward pointing indicator chevron
    arrow_x = settings.width // 2
    arrow_y = desc_pill_y + desc_pill_h + 14
    draw.line([(arrow_x, arrow_y), (arrow_x, arrow_y + 18)], fill="#F5C518", width=6)
    draw.polygon([
        (arrow_x - 16, arrow_y + 14),
        (arrow_x + 16, arrow_y + 14),
        (arrow_x, arrow_y + 32),
    ], fill="#F5C518")

    image.save(output_path, format="PNG")


def render_video(
    source: Path,
    thumbnail: Path | None,
    page_one: str,
    page_two: str,
    selected_clip: dict[str, Any],
    output: Path,
    settings: Settings,
    metadata: dict[str, Any] | None = None,
    post_title: str | None = None,
) -> dict[str, Any]:
    ffmpeg = find_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="avbrief-render-", dir=output.parent) as temp_name:
        temp = Path(temp_name)
        if thumbnail is None or not thumbnail.exists():
            thumbnail = temp / "fallback-thumbnail.jpg"
            sample_time = max(float(selected_clip["start_seconds"]) + 1.5, 1.5)
            _extract_frame(source, sample_time, thumbnail, ffmpeg)

        source_card = temp / "source-card.png"
        render_source_card(thumbnail, metadata or {}, source_card, settings)

        top_overlay = temp / "top-overlay.png"
        render_top_overlay(metadata or {}, top_overlay, settings)

        category = infer_category(metadata or {}, page_one + " " + page_two)
        page_one_png = temp / "page-one.png"
        page_two_png = temp / "page-two.png"
        cta_page_png = temp / "cta-page.png"

        # Determine top headline: use post_title or fallback to metadata title
        display_headline = post_title
        if display_headline and ("#shorts" in display_headline.lower()):
            display_headline = re.sub(r"#shorts\s*", "", display_headline, flags=re.IGNORECASE).strip()
        if display_headline:
            display_headline = sanitize_display_text(display_headline)

        font_one = render_text_page(
            page_one,
            page_one_png,
            settings,
            main_title=display_headline,
            header="فيديوهات وجب مشاهدتها على اليوتيوب",
            sub_header=f"النوع: {category}",
        )
        font_two = render_text_page(
            page_two,
            page_two_png,
            settings,
            footer="اقرأ الوصف لمزيد من التفاصيل",
        )
        render_v1_cta_page(
            cta_page_png,
            settings,
            avatar_path=settings.brand_avatar_path,
        )

        # 28.0s Timeline setup:
        # Top Panel:
        # 0:00 to 0:02.5 (2.5s): Kinetic Ken Burns zoom on source_card + floating overlay
        # 0:02.5 to 0:20.0 (17.5s): Video stream with floating overlay & seamless gradient blend
        # 0:20.0 to 0:28.0 (8.0s): Kinetic Ken Burns zoom on CTA card + floating overlay
        start = float(selected_clip["start_seconds"])
        top_path = temp / "top.mp4"
        open_dur = 2.5
        v_stream_dur = 17.5
        cta_dur = float(settings.cta_duration)
        fps = settings.fps
        d_open = int(open_dur * fps)
        d_cta = int(cta_dur * fps)

        command_top = [
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-t", f"{open_dur:.1f}", "-i", str(source_card),
            "-ss", f"{start:.3f}", "-i", str(source),
            "-loop", "1", "-t", f"{settings.duration:.1f}", "-i", str(top_overlay),
            "-loop", "1", "-t", f"{cta_dur:.1f}", "-i", str(source_card),
            "-filter_complex",
            f"[0:v]scale={settings.width}:{settings.top_height}:force_original_aspect_ratio=increase,crop={settings.width}:{settings.top_height},"
            f"zoompan=z='min(zoom+0.0008,1.06)':d={d_open}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={settings.width}x{settings.top_height}:fps={fps}[c1_zoom];"
            f"[c1_zoom][2:v]overlay=0:0:format=auto,fps={fps},trim=duration={open_dur:.1f},setpts=PTS-STARTPTS,setsar=1[card1];"
            f"[1:v]scale={settings.width}:{settings.top_height}:force_original_aspect_ratio=increase,crop={settings.width}:{settings.top_height},setsar=1[vclip];"
            f"[vclip][2:v]overlay=0:0:format=auto,fps={fps},trim=duration={v_stream_dur:.1f},setpts=PTS-STARTPTS,setsar=1[vstream];"
            f"[3:v]scale={settings.width}:{settings.top_height}:force_original_aspect_ratio=increase,crop={settings.width}:{settings.top_height},"
            f"zoompan=z='min(zoom+0.00025,1.06)':d={d_cta}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={settings.width}x{settings.top_height}:fps={fps}[c2_zoom];"
            f"[c2_zoom][2:v]overlay=0:0:format=auto,fps={fps},trim=duration={cta_dur:.1f},setpts=PTS-STARTPTS,setsar=1[card2];"
            "[card1][vstream][card2]concat=n=3:v=1:a=0[top]",
            "-map", "[top]", "-t", f"{settings.duration}", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", str(top_path),
        ]
        _run(command_top, timeout=900)

        # Select background music track: V1 strictly uses Vangelis La Petite Fille De La Mer
        v1_music = settings.music_dir / "vangelis_la_petite_fille_de_la_mer.mp3"
        if v1_music.exists():
            music_track = v1_music
        else:
            music_track = select_background_music(settings.music_dir)

        # Overlay text pages across the 28s timeline:
        # Page 1: 0 to 10.0s
        # Page 2: 10.0s to 20.0s
        # CTA Page: 20.0s to 28.0s
        filter_str = (
            f"[1:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[page1];"
            f"[2:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[page2];"
            f"[3:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[page_cta];"
            f"color=c=black:s={settings.width}x{settings.height}:r={settings.fps}:d={settings.duration}[base];"
            f"[base][page1]overlay=0:0:enable='lt(t,10.0)'[p1];"
            f"[p1][page2]overlay=0:0:enable='between(t,10.0,20.0)'[p2];"
            f"[p2][page_cta]overlay=0:0:enable='gte(t,20.0)'[bg];"
        )
        command_final = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(top_path),
            "-i", str(page_one_png), "-i", str(page_two_png), "-i", str(cta_page_png),
        ]

        next_input_idx = 4
        has_frame = bool(settings.brand_frame_path and settings.brand_frame_path.exists())
        if has_frame:
            frame_idx = next_input_idx
            command_final.extend(["-i", str(settings.brand_frame_path)])
            next_input_idx += 1
            filter_str += (
                f"[0:v]scale=972:684:flags=lanczos[top_scaled];"
                f"[bg][top_scaled]overlay=54:96[inner];"
                f"[{frame_idx}:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[frame_v];"
                f"[inner][frame_v]overlay=0:0[out]"
            )
        else:
            filter_str += "[bg][0:v]overlay=0:0:eof_action=repeat,format=yuv420p[out]"

        outro_voice = settings.outro_voiceover_path
        has_outro = bool(outro_voice and outro_voice.exists())

        if music_track and has_outro:
            music_idx = next_input_idx
            next_input_idx += 1
            outro_idx = next_input_idx
            next_input_idx += 1
            filter_str += (
                f";[{music_idx}:a]atrim=duration=20.0,volume={settings.music_volume},"
                f"afade=t=out:st=18.0:d=2.0,"
                f"apad=whole_dur={settings.duration}[bg_music];"
                f"[{outro_idx}:a]atempo=1.084,volume=1.0,adelay=20000|20000,apad=whole_dur={settings.duration}[outro_voice];"
                f"[bg_music][outro_voice]amix=inputs=2:duration=first:dropout_transition=0,"
                f"aformat=channel_layouts=stereo:sample_rates=44100[aout]"
            )
            command_final.extend(["-i", str(music_track), "-i", str(outro_voice)])
            command_final.extend([
                "-filter_complex", filter_str,
                "-map", "[out]", "-map", "[aout]",
                "-t", f"{settings.duration}",
                "-frames:v", str(round(settings.duration * settings.fps)), "-r", str(settings.fps),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-y", str(output),
            ])
        elif music_track:
            music_idx = next_input_idx
            next_input_idx += 1
            filter_str += (
                f";[{music_idx}:a]atrim=duration=20.0,volume={settings.music_volume},"
                f"afade=t=out:st=18.0:d=2.0,"
                f"apad=whole_dur={settings.duration},"
                f"aformat=channel_layouts=stereo:sample_rates=44100[aout]"
            )
            command_final.extend(["-i", str(music_track)])
            command_final.extend([
                "-filter_complex", filter_str,
                "-map", "[out]", "-map", "[aout]",
                "-t", f"{settings.duration}",
                "-frames:v", str(round(settings.duration * settings.fps)), "-r", str(settings.fps),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-y", str(output),
            ])
        elif has_outro:
            outro_idx = next_input_idx
            next_input_idx += 1
            filter_str += (
                f";[{outro_idx}:a]atempo=1.084,volume=1.0,adelay=20000|20000,apad=whole_dur={settings.duration},"
                f"aformat=channel_layouts=stereo:sample_rates=44100[aout]"
            )
            command_final.extend(["-i", str(outro_voice)])
            command_final.extend([
                "-filter_complex", filter_str,
                "-map", "[out]", "-map", "[aout]",
                "-t", f"{settings.duration}",
                "-frames:v", str(round(settings.duration * settings.fps)), "-r", str(settings.fps),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-y", str(output),
            ])
        else:
            command_final.extend([
                "-filter_complex", filter_str,
                "-map", "[out]",
                "-t", f"{settings.duration}",
                "-frames:v", str(round(settings.duration * settings.fps)), "-r", str(settings.fps), "-an",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", "-y", str(output),
            ])

        _run(command_final, timeout=900)

    final_info = probe_media(output, ffmpeg)
    return {
        "width": final_info.width,
        "height": final_info.height,
        "duration": final_info.duration,
        "font_sizes": [font_one, font_two],
        "audio": final_info.has_audio,
        "music_track": music_track.name if music_track else None,
    }



def select_background_music(music_dir: Path) -> Path | None:
    if not music_dir or not music_dir.exists() or not music_dir.is_dir():
        return None
    valid_extensions = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
    tracks = sorted([p for p in music_dir.iterdir() if p.is_file() and p.suffix.lower() in valid_extensions])
    if not tracks:
        return None
    return random.choice(tracks)


def probe_image(path: Path) -> MediaInfo:
    from PIL import Image

    with Image.open(path) as image:
        return MediaInfo(image.width, image.height, 0.0)
