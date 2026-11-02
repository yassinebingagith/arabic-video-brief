from __future__ import annotations

import logging
import math
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from ..config import Settings
from ..media import (
    _balance_wrap,
    _display_text,
    _extract_frame,
    _metadata_line,
    _run,
    _wrap_rtl,
    create_v2_summary_background,
    find_ffmpeg,
    infer_category,
    render_metadata_bar,
    render_source_card,
    render_top_overlay,
    select_background_music,
    wrap_v2_text_with_highlights,
)
from .editorial import HookCandidate, V2EditorialPackage

logger = logging.getLogger(__name__)


def render_v2_hook_page(
    source_card_path: Path,
    hook: HookCandidate,
    output_path: Path,
    settings: Settings,
) -> None:
    """
    Renders the dedicated hook page (1080x1920) for 0:00-0:02.5.
    The top 760px contains the exact YouTube source card (continuity with Page 1).
    The bottom panel contains the large centered Arabic hook with gold highlight,
    and a subtitle badge below it preparing the viewer.
    """
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (settings.width, settings.height), "#000000")

    # Paste the static source card in the top panel (1080x760)
    if source_card_path.exists():
        with Image.open(source_card_path) as card_img:
            image.paste(card_img.convert("RGB"), (0, 0))

    draw = ImageDraw.Draw(image)

    # Lower panel: y=760 to y=1920
    panel_top = settings.top_height
    safe_bottom = settings.height - int(settings.height * 0.15)
    available_h = safe_bottom - panel_top

    # Hook typography: 62px Bold
    font_size = 62
    hook_font = ImageFont.truetype(str(settings.font_path), font_size)
    try:
        hook_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    lines = [ln.strip() for ln in hook.display_hook.split("\n") if ln.strip()]
    if len(lines) == 1:
        lines = _balance_wrap(lines[0], hook_font, settings.width - 240)

    line_h = math.ceil(font_size * 1.45)
    total_hook_h = len(lines) * line_h

    # Subtitle badge under the hook: "أبرز ما جاء في هذا الحوار" (Bigger, prominent pill badge)
    sub_text = "أبرز ما جاء في هذا الحوار"
    sub_font = ImageFont.truetype(str(settings.font_path), 36)
    try:
        sub_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass
    sub_vis = _display_text(sub_text)
    sub_box = draw.textbbox((0, 0), sub_vis, font=sub_font)
    sub_w = sub_box[2] - sub_box[0]
    sub_h = sub_box[3] - sub_box[1]

    # Center hook block vertically in available lower panel
    block_total_h = total_hook_h + 46 + sub_h + 28
    start_y = panel_top + (available_h - block_total_h) // 2

    highlight_clean = hook.highlight_phrase.strip()
    cur_y = start_y

    for line in lines[:2]:
        is_highlighted = bool(highlight_clean and (highlight_clean in line or line in highlight_clean))
        color = "#F5C518" if is_highlighted else "#FFFFFF"

        vis = _display_text(line)
        box = draw.textbbox((0, 0), vis, font=hook_font)
        tw = box[2] - box[0]
        tx = (settings.width - tw) // 2

        # Draw text with subtle punch shadow
        draw.text((tx + 3, cur_y + 3), vis, font=hook_font, fill="#000000")
        draw.text((tx, cur_y), vis, font=hook_font, fill=color)
        cur_y += line_h

    # Draw prominent subtitle badge under the hook
    cur_y += 36
    badge_pad_x = 36
    badge_pad_y = 14
    badge_w = sub_w + (badge_pad_x * 2)
    badge_h = sub_h + (badge_pad_y * 2)
    badge_x = (settings.width - badge_w) // 2

    draw.rounded_rectangle(
        (badge_x, cur_y, badge_x + badge_w, cur_y + badge_h),
        radius=badge_h // 2,
        fill="#1A1A24",
        outline="#F5C518",
        width=2,
    )
    draw.text(
        (badge_x + badge_pad_x, cur_y + badge_pad_y - sub_box[1]),
        sub_vis,
        font=sub_font,
        fill="#FFFFFF",
    )

    image.save(output_path, format="PNG")


def render_v2_summary_page(
    text: str,
    page_index: int,
    output_path: Path,
    settings: Settings,
    main_title: str | None = None,
    category: str | None = None,
    _layout: dict[str, Any] | None = None,
) -> None:
    """
    Renders one of the 4 summary pages (1080x1920) for the lower panel (00:00-00:33).
    - Background: Deep black-and-navy radial glow with soft Gaussian blur effect (#102A45 / #071322 over #02060D).
    - Page 1 retains the translated title block header (centered).
    - Pages 2, 3, 4 render ONLY the 6-line Arabic paragraph (NO card kickers, NO numbers, NO footer dots).
    - Base Arabic text: Bold (700) Crisp White (#F8FAFC), line height 1.85.
    - Highlighted phrases (<hl>...</hl>): Warm Gold (#FFD700) Bold (750-800) with translucent warm gold rounded pill
      box (background: rgba(255, 215, 0, 0.14); border-radius: 10px; padding: 2px 10px 4px 10px;), no-wrap,
      clean descenders without underlines.
    """
    from PIL import Image, ImageDraw, ImageFont
    import arabic_reshaper
    from bidi.algorithm import get_display

    image = create_v2_summary_background(settings.width, settings.height, settings.top_height)
    draw = ImageDraw.Draw(image)

    panel_top = settings.top_height
    safe_bottom = settings.height - int(settings.height * 0.15)
    side_margin = 100
    # Safe text width respecting the 6% left-shift to clear right-side platform action buttons
    offset_x = int(settings.width * settings.text_offset_ratio)  # ~65px
    max_text_width = settings.width - (side_margin * 2) - offset_x  # ~815px
    content_right = settings.width - side_margin - offset_x

    cur_y = panel_top + 20

    # Page 1: Centered Headline Block (Preserved verbatim per user instruction)
    if page_index == 1:
        if main_title:
            title_font = ImageFont.truetype(str(settings.font_path), 38)
            try:
                title_font.set_variation_by_axes([700, 100])
            except (AttributeError, OSError, ValueError):
                try:
                    title_font.set_variation_by_name("Bold")
                except (AttributeError, OSError, ValueError):
                    pass
            m_lines = _balance_wrap(main_title, title_font, max_text_width)
            title_line_h = math.ceil(38 * 1.35)
            for ml in m_lines:
                vis = _display_text(ml)
                box = draw.textbbox((0, 0), vis, font=title_font)
                tw = box[2] - box[0]
                tx = (settings.width - tw) // 2  # Centered!
                draw.text((tx, cur_y), vis, font=title_font, fill="#F5C518")
                cur_y += title_line_h
            cur_y += 10

        header_font = ImageFont.truetype(str(settings.font_path), 28)
        try:
            header_font.set_variation_by_axes([700, 100])
        except (AttributeError, OSError, ValueError):
            try:
                header_font.set_variation_by_name("Bold")
            except (AttributeError, OSError, ValueError):
                pass
        h_vis = _display_text("فيديوهات وجب مشاهدتها على اليوتيوب")
        h_box = draw.textbbox((0, 0), h_vis, font=header_font)
        h_w = h_box[2] - h_box[0]
        draw.text(((settings.width - h_w) // 2, cur_y), h_vis, font=header_font, fill="#FFFFFF")  # Centered!
        cur_y += (h_box[3] - h_box[1]) + 10

        if category:
            sub_font = ImageFont.truetype(str(settings.font_path), 22)
            try:
                sub_font.set_variation_by_axes([500, 100])
            except (AttributeError, OSError, ValueError):
                try:
                    sub_font.set_variation_by_name("Medium")
                except (AttributeError, OSError, ValueError):
                    pass
            s_vis = _display_text(f"النوع: {category}")
            s_box = draw.textbbox((0, 0), s_vis, font=sub_font)
            s_w = s_box[2] - s_box[0]
            draw.text(((settings.width - s_w) // 2, cur_y), s_vis, font=sub_font, fill="#A0A0A0")  # Centered!
            cur_y += (s_box[3] - s_box[1]) + 26

    # Clean text braces while preserving <hl> tags
    clean_text = text.replace("{", "").replace("}", "")

    # Base typography: Bold (700) across entire paragraph so text never looks thin
    # Line height: 1.85 for clean vertical breathing room
    font_size = 42 if page_index == 1 else 46
    body_font = ImageFont.truetype(str(settings.font_path), font_size)
    try:
        body_font.set_variation_by_axes([700, 100])
    except (AttributeError, OSError, ValueError):
        try:
            body_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass

    lines = wrap_v2_text_with_highlights(clean_text, body_font, max_text_width)

    # Adaptive font scaling to ensure it fits ~6 lines comfortably within safe height
    min_size = 34
    while len(lines) > 6 and font_size > min_size:
        font_size -= 2
        body_font = ImageFont.truetype(str(settings.font_path), font_size)
        try:
            body_font.set_variation_by_axes([700, 100])
        except (AttributeError, OSError, ValueError):
            try:
                body_font.set_variation_by_name("Bold")
            except (AttributeError, OSError, ValueError):
                pass
        lines = wrap_v2_text_with_highlights(clean_text, body_font, max_text_width)

    # Highlight font (Bold 750-800)
    hl_font = ImageFont.truetype(str(settings.font_path), font_size)
    try:
        hl_font.set_variation_by_axes([750, 100])
    except (AttributeError, OSError, ValueError):
        try:
            hl_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass

    line_h = math.ceil(font_size * 1.85)
    total_text_h = len(lines) * line_h

    # Vertically balance the body text within the remaining panel height
    remaining_h = safe_bottom - cur_y
    if page_index > 1:
        # Vertically center in the lower panel
        cur_y = panel_top + (safe_bottom - panel_top - total_text_h) // 2
    elif remaining_h > total_text_h:
        # Add slight breathing room below header on page 1
        cur_y += max(16, (remaining_h - total_text_h) // 3)

    if _layout is not None:
        _layout.update(base=image.copy(), font_size=font_size)
    # Render highlight pills on an overlay layer
    overlay = Image.new("RGBA", (settings.width, settings.height), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    dummy = ImageDraw.Draw(Image.new("L", (1, 1)))

    rendered_lines: list[list[dict[str, Any]]] = []
    line_y = cur_y

    for line in lines:
        pattern = re.compile(r"(<hl>.*?</hl>)")
        raw_segments = pattern.split(line)
        segments: list[tuple[str, bool]] = []
        for seg in raw_segments:
            if not seg:
                continue
            if seg.startswith("<hl>") and seg.endswith("</hl>"):
                segments.append((seg[4:-5], True))
            else:
                segments.append((seg, False))

        processed_segments: list[dict[str, Any]] = []
        for seg_text, is_hl in segments:
            f = hl_font if is_hl else body_font
            reshaped = arabic_reshaper.reshape(seg_text)
            vis = get_display(reshaped, base_dir="R")
            w = dummy.textlength(vis, font=f)
            processed_segments.append({
                "text": seg_text,
                "vis": vis,
                "is_hl": is_hl,
                "font": f,
                "width": w,
            })

        # In RTL Arabic, segment 0 is far right (content_right)
        cur_right = content_right
        for s in processed_segments:
            w = s["width"]
            x = cur_right - w
            s["x"] = x
            s["y"] = line_y
            if s["is_hl"]:
                bbox = dummy.textbbox((x, line_y), s["vis"], font=s["font"])
                # Highlight pill box: rgba(255, 215, 0, 0.14), radius=10px, padding: 2px 10px 4px 10px
                pad_top = 2
                pad_bottom = 4
                pad_x = 10
                pill_box = (
                    bbox[0] - pad_x,
                    bbox[1] - pad_top,
                    bbox[2] + pad_x,
                    bbox[3] + pad_bottom,
                )
                draw_overlay.rounded_rectangle(
                    pill_box,
                    radius=10,
                    fill=(255, 215, 0, int(255 * 0.14)),
                )
            cur_right = x

        rendered_lines.append(processed_segments)
        line_y += line_h

    # Composite translucent highlight pills over background
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Draw text: Crisp White (#F8FAFC) for base, Warm Gold (#FFD700) for highlights
    for line_segs in rendered_lines:
        for s in line_segs:
            color = "#FFD700" if s["is_hl"] else "#F8FAFC"
            draw.text((s["x"], s["y"]), s["vis"], font=s["font"], fill=color)

    if _layout is not None:
        _layout["lines"] = rendered_lines
    image.save(output_path, format="PNG")


def render_v2_conclusion_page(
    source_card_path: Path,
    conclusion_text: str,
    conclusion_highlights: list[str],
    save_cta: str,
    desc_cta: str,
    avatar_path: Path | None,
    output_path: Path,
    settings: Settings,
) -> None:
    """
    Renders the gamified '100% Brain Overcharge' outro ending (1080x1920) for 0:57.0-0:59.8 (2.8s).
    The top 760px retains the static source card / thumbnail with seamless background.
    The lower panel displays:
      1. Yellow conclusion question title at top
      2. 1.12x scaled 100% full gold brain with dual aura/bloom effect
      3. Gamified achievement badge text in crisp Arabic:
         "⚡ اكتمل شحن الفكرة 100% — تركيزك أعمق من 90% من المتصفحين! الشرح الكامل في الوصف 👇"
    """
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    from ..media import create_v2_summary_background, _display_text, _balance_wrap
    from ..whiteboard import get_brain_mask

    image = create_v2_summary_background(settings.width, settings.height, settings.top_height)

    # Paste the static source card in the top panel (1080x760)
    if source_card_path and source_card_path.exists():
        with Image.open(source_card_path) as card_img:
            image.paste(card_img.convert("RGB"), (0, 0))

    draw = ImageDraw.Draw(image)

    panel_top = settings.top_height
    side_safe_margin = int(settings.width * 0.15)  # 162px
    max_safe_width = settings.width - (2 * side_safe_margin)  # 756px

    # 1. Main ending question title in yellow (#FFD700) with subtle drop shadow
    conc_size = 46
    conc_font = ImageFont.truetype(str(settings.font_path), conc_size)
    try:
        conc_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    clean_conc = conclusion_text.replace("{", "").replace("}", "").strip()
    conc_lines = _balance_wrap(clean_conc, conc_font, max_safe_width)
    while len(conc_lines) > 3 and conc_size > 32:
        conc_size -= 2
        conc_font = ImageFont.truetype(str(settings.font_path), conc_size)
        try:
            conc_font.set_variation_by_name("Bold")
        except (AttributeError, OSError, ValueError):
            pass
        conc_lines = _balance_wrap(clean_conc, conc_font, max_safe_width)
    conc_line_h = math.ceil(conc_size * 1.45)
    conc_y = panel_top + 45

    for line in conc_lines:
        vis = _display_text(line)
        box = draw.textbbox((0, 0), vis, font=conc_font)
        tw = box[2] - box[0]
        tx = (settings.width - tw) // 2

        draw.text((tx + 2, conc_y + 2), vis, font=conc_font, fill="#000000")
        draw.text((tx, conc_y), vis, font=conc_font, fill="#FFD700")
        conc_y += conc_line_h

    # 2. 100% Brain Overcharge Icon (scaled 1.12x, locked at 100% gold, with bright aura bloom)
    bw, bh = 82, 86
    brain_mask = get_brain_mask((bw, bh))

    pad = 60
    aura_size = (bw + pad * 2, bh + pad * 2)
    aura_layer = Image.new("RGBA", aura_size, (0, 0, 0, 0))
    big_glow_mask = Image.new("L", aura_size, 0)
    big_glow_mask.paste(brain_mask, (pad, pad))

    # Outer warm gold bloom
    big_glow = big_glow_mask.filter(ImageFilter.GaussianBlur(24))
    gold_fill = Image.new("RGBA", aura_size, (255, 215, 0, 160))
    aura_layer.paste(gold_fill, (0, 0), big_glow)

    # Core intense white-gold bloom
    core_glow = big_glow_mask.filter(ImageFilter.GaussianBlur(10))
    white_fill = Image.new("RGBA", aura_size, (255, 255, 230, 220))
    aura_layer.paste(white_fill, (0, 0), core_glow)

    cx = settings.width // 2
    brain_y = conc_y + 70
    bx = cx - bw // 2
    by = brain_y

    image.paste(aura_layer, (cx - aura_size[0] // 2, by + bh // 2 - aura_size[1] // 2), aura_layer)
    gold_brain = Image.new("RGBA", (bw, bh), (255, 215, 0, 255))
    image.paste(gold_brain, (bx, by), brain_mask)

    outline = brain_mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.8))
    outline_img = Image.new("RGBA", (bw, bh), (255, 255, 255, 240))
    image.paste(outline_img, (bx, by), outline)

    # 3. Achievement Badge text
    # "⚡ اكتمل شحن الفكرة 100% — تركيزك أعمق من 90% من المتصفحين! الشرح الكامل في الوصف 👇"
    badge_y = by + bh + 45

    # Header gold pill: "⚡ اكتمل شحن الفكرة 100%"
    h_font = ImageFont.truetype(str(settings.font_path), 34)
    try:
        h_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass
    h_text = "⚡ اكتمل شحن الفكرة 100%"
    h_vis = _display_text(h_text)
    h_box = draw.textbbox((0, 0), h_vis, font=h_font)
    hw, hh = h_box[2] - h_box[0], h_box[3] - h_box[1]

    h_pill_w = hw + 56
    h_pill_h = hh + 24
    h_pill_x = (settings.width - h_pill_w) // 2

    draw.rounded_rectangle(
        (h_pill_x - 2, badge_y - 2, h_pill_x + h_pill_w + 2, badge_y + h_pill_h + 2),
        radius=h_pill_h // 2,
        fill="#5A4700",
    )
    draw.rounded_rectangle(
        (h_pill_x, badge_y, h_pill_x + h_pill_w, badge_y + h_pill_h),
        radius=h_pill_h // 2,
        fill="#F5C518",
        outline="#FFF3B0",
        width=2,
    )
    draw.text(
        (h_pill_x + (h_pill_w - hw) // 2, badge_y + (h_pill_h - hh) // 2 - h_box[1]),
        h_vis,
        font=h_font,
        fill="#000000",
    )

    # Sub-card:
    # "تركيزك أعمق من 90% من المتصفحين!"
    # "الشرح الكامل في الوصف 👇"
    sub_y = badge_y + h_pill_h + 26
    sub_font = ImageFont.truetype(str(settings.font_path), 30)
    try:
        sub_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    sub_line1 = "تركيزك أعمق من 90% من المتصفحين!"
    sub_line2 = "الشرح الكامل في الوصف 👇"

    s1_vis = _display_text(sub_line1)
    s2_vis = _display_text(sub_line2)

    s1_box = draw.textbbox((0, 0), s1_vis, font=sub_font)
    s2_box = draw.textbbox((0, 0), s2_vis, font=sub_font)

    s1_w, s1_h = s1_box[2] - s1_box[0], s1_box[3] - s1_box[1]
    s2_w, s2_h = s2_box[2] - s2_box[0], s2_box[3] - s2_box[1]

    card_w = min(max(s1_w, s2_w) + 64, max_safe_width)
    card_h = s1_h + s2_h + 46
    card_x = (settings.width - card_w) // 2

    draw.rounded_rectangle(
        (card_x, sub_y, card_x + card_w, sub_y + card_h),
        radius=20,
        fill="#0d1726",
        outline="#FFD700",
        width=2,
    )

    draw.text(
        (card_x + (card_w - s1_w) // 2, sub_y + 16 - s1_box[1]),
        s1_vis,
        font=sub_font,
        fill="#FFFFFF",
    )
    draw.text(
        (card_x + (card_w - s2_w) // 2, sub_y + 20 + s1_h + 10 - s2_box[1]),
        s2_vis,
        font=sub_font,
        fill="#FFD700",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")



def select_v2_music(music_dir: Path) -> Path | None:
    import random
    names = ("naruto_sadness_and_sorrow.mp3", "godfather_0013.mp3")
    available = [music_dir / name for name in names if (music_dir / name).is_file()]
    return random.choice(available) if available else None


def render_v2_video(
    source: Path,
    thumbnail: Path | None,
    editorial: V2EditorialPackage,
    selected_clip: dict[str, Any],
    output: Path,
    settings: Settings,
    hook_audio_path: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Render V2 with five reading pages (57.0s total) and a 2.8s gamified 100% brain overcharge ending (59.8s total)."""
    ffmpeg = find_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)

    bounds = settings.v2_page_boundaries
    reading_end = bounds[-1]
    total_duration = round(reading_end + settings.conclusion_duration, 1)
    start_time = float(selected_clip.get("start_seconds", 0.0))

    with tempfile.TemporaryDirectory(prefix="avbrief-v2-render-", dir=output.parent, ignore_cleanup_errors=True) as temp_dir_str:
        temp = Path(temp_dir_str)

        if thumbnail is None or not thumbnail.exists():
            thumbnail = temp / "fallback-thumbnail.jpg"
            sample_time = max(start_time + 1.5, 1.5)
            _extract_frame(source, sample_time, thumbnail, ffmpeg)

        # 1. Source card (1080x760)
        source_card = temp / "source-card.png"
        render_source_card(thumbnail, metadata or {}, source_card, settings)

        # 2. Top overlay with seamless gradient & floating badge (1080x760)
        top_overlay = temp / "top-overlay.png"
        render_top_overlay(metadata or {}, top_overlay, settings)

        # 3. Render Top Panel MP4 (Exact 50.2s duration)
        # 0:00 to 0:02.5 (2.5s): Kinetic Ken Burns zoom on source_card + floating overlay
        # 0:02.5 to 0:42.2 (39.7s): Full 1080x760 video stream with floating overlay & seamless gradient blend
        # 0:42.2 to 0:50.2 (8.0s): Kinetic Ken Burns zoom on CTA card + floating overlay
        top_path = temp / "top_v2.mp4"
        open_dur = settings.hook_duration
        v_stream_dur = reading_end - open_dur
        cta_dur = float(settings.conclusion_duration)
        fps = settings.fps
        d_open = int(open_dur * fps)
        d_cta = int(cta_dur * fps)

        command_top = [
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-t", f"{open_dur:.1f}", "-i", str(source_card),
            "-ss", f"{start_time:.3f}", "-i", str(source),
            "-loop", "1", "-t", f"{total_duration:.1f}", "-i", str(top_overlay),
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
            "-map", "[top]", "-t", f"{total_duration}", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", str(top_path),
        ]
        _run(command_top, timeout=900)

        # 4. Render Visual PNG Pages (Page 1 directly at t=0s, NO hook page)
        category = infer_category(metadata or {}, " ".join(editorial.pages))

        clean_title = editorial.post_title_ar
        if clean_title and "#shorts" in clean_title.lower():
            clean_title = re.sub(r"#shorts\s*", "", clean_title, flags=re.IGNORECASE).strip()

        from ..whiteboard import WhiteboardProject
        project = WhiteboardProject(output,settings,"v2",source,thumbnail,editorial.pages,metadata=metadata,selected_clip=selected_clip,
            title=clean_title,ending=editorial.conclusion_ar,hook=hook_audio_path,
            editorial={"conclusion_highlights":editorial.conclusion_highlights,"cta_ar":editorial.cta_ar,"cta_description":editorial.cta_description})
        project.ffmpeg = ffmpeg
        page_pngs: list[Path] = []
        for i, page_text in enumerate(editorial.pages):
            p_png = project.page(i+1,page_text,bounds[i],bounds[i+1],title=clean_title if i==0 else None,category=category if i==0 else None)
            page_pngs.append(p_png)

        conc_png = temp / "conclusion.png"
        render_v2_conclusion_page(
            source_card,
            editorial.conclusion_ar,
            editorial.conclusion_highlights,
            editorial.cta_ar,
            editorial.cta_description,
            settings.brand_avatar_path,
            conc_png,
            settings,
        )

        # Select independently for each render; keep the pool specific to V2.
        music_track = select_v2_music(settings.music_dir)

        conc_input_idx = len(page_pngs) + 1
        final_cmd = [
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-i", str(top_path),
        ]
        for p_png in page_pngs:
            final_cmd.extend(["-i", str(p_png)])
        final_cmd.extend(["-i", str(conc_png)])

        next_input_idx = conc_input_idx + 1

        filter_parts: list[str] = [
            f"color=c=black:s={settings.width}x{settings.height}:r={settings.fps}:d={total_duration}[base]",
        ]
        for i in range(len(page_pngs)):
            input_idx = i + 1
            pts_offset = f"+{bounds[i]}/TB" if bounds[i] > 0 else ""
            filter_parts.append(
                f"[{input_idx}:v]pad={settings.width}:{settings.height}:0:{settings.top_height}:color=black,fps={settings.fps},setpts=PTS-STARTPTS{pts_offset}[p{i + 1}]"
            )
        filter_parts.append(
            f"[{conc_input_idx}:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[conc]"
        )

        prev_stream = "[base]"
        for i in range(len(page_pngs)):
            curr_stream = f"[c{i + 1}]"
            start_t = bounds[i]
            end_t = bounds[i + 1]
            if i == 0:
                enable_expr = f"lt(t,{end_t:.1f})"
            else:
                enable_expr = f"gte(t,{start_t:.1f})*lt(t,{end_t:.1f})"
            filter_parts.append(
                f"{prev_stream}[p{i + 1}]overlay=0:0:enable='{enable_expr}'{curr_stream}"
            )
            prev_stream = curr_stream

        conc_stream = f"[c{len(page_pngs) + 1}]"
        filter_parts.append(
            f"{prev_stream}[conc]overlay=0:0:enable='gte(t,{reading_end:.1f})'{conc_stream}"
        )

        # Check if Prussian Airbrush Frame asset is present
        has_frame = bool(settings.brand_frame_path and settings.brand_frame_path.exists())
        if has_frame:
            frame_idx = next_input_idx
            final_cmd.extend(["-i", str(settings.brand_frame_path)])
            next_input_idx += 1
            filter_parts.extend([
                f"{conc_stream}[0:v]overlay=0:0[inner_full]",
                f"color=c=black:s={settings.width}x{settings.height}:r={settings.fps}:d={total_duration}[canvas_base]",
                "[inner_full]scale=972:1728:flags=lanczos[scaled_inner]",
                "[canvas_base][scaled_inner]overlay=54:96[padded_video]",
                f"[{frame_idx}:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[frame_v]",
                "[padded_video][frame_v]overlay=0:0[vout]",
            ])
        else:
            filter_parts.append(f"{conc_stream}[0:v]overlay=0:0[vout]")

        # Audio configuration:
        # Hook voiceover starts at t=0.
        # Music track plays with ducking during hook narration, and continues smoothly until total_duration with a gentle 0.5s fade-out.
        # Outro voiceover is completely removed on the 2.8s overcharge conclusion page.
        has_hook_audio = bool(hook_audio_path and hook_audio_path.exists())
        has_outro = False
        outro_voice = None

        fade_dur = 0.5
        fade_st = total_duration - fade_dur

        mix_inputs: list[str] = []

        if music_track:
            final_cmd.extend(["-stream_loop", "-1", "-i", str(music_track)])
            music_idx = next_input_idx
            next_input_idx += 1
            if has_hook_audio:
                voice_dur = 4.5
                try:
                    vinfo = probe_media(hook_audio_path, ffmpeg)
                    voice_dur = max(2.0, min(10.5, float(vinfo.duration)))
                except Exception:
                    voice_dur = 4.5

                # Subtle deterministic micro-jitter (0.995-1.005) to randomize acoustic fingerprint
                seed_val = sum(ord(c) for c in str((metadata or {}).get("id") or (metadata or {}).get("title") or "v2"))
                tempo_jitter = 0.995 + ((seed_val % 11) * 0.001)

                filter_parts.append(
                    f"[{music_idx}:a]atempo={tempo_jitter:.4f},atrim=duration={total_duration:.1f},"
                    f"volume='if(lt(t,{voice_dur:.2f}), 0.12, min(0.70, 0.12 + (0.70-0.12)*(t-{voice_dur:.2f})/0.6))':eval=frame,"
                    f"afade=t=out:st={fade_st:.2f}:d={fade_dur:.2f},apad=whole_dur={total_duration}[ducked_music]"
                )
                mix_inputs.append("[ducked_music]")
            else:
                seed_val = sum(ord(c) for c in str((metadata or {}).get("id") or (metadata or {}).get("title") or "v2"))
                tempo_jitter = 0.995 + ((seed_val % 11) * 0.001)
                filter_parts.append(
                    f"[{music_idx}:a]atempo={tempo_jitter:.4f},atrim=duration={total_duration:.1f},volume={settings.music_volume},"
                    f"afade=t=out:st={fade_st:.2f}:d={fade_dur:.2f},apad=whole_dur={total_duration}[bg_music]"
                )
                mix_inputs.append("[bg_music]")

        if has_hook_audio:
            final_cmd.extend(["-i", str(hook_audio_path)])
            hook_idx = next_input_idx
            next_input_idx += 1
            filter_parts.append(
                f"[{hook_idx}:a]volume=1.3,apad=whole_dur={total_duration}[hook_audio]"
            )
            mix_inputs.append("[hook_audio]")

        if len(mix_inputs) > 1:
            filter_parts.append(
                f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0:normalize=0,"
                f"aformat=channel_layouts=stereo:sample_rates=44100[aout]"
            )
            final_cmd.extend([
                "-filter_complex", ";".join(filter_parts),
                "-map", "[vout]", "-map", "[aout]",
            ])
        elif len(mix_inputs) == 1:
            filter_parts.append(
                f"{mix_inputs[0]}aformat=channel_layouts=stereo:sample_rates=44100[aout]"
            )
            final_cmd.extend([
                "-filter_complex", ";".join(filter_parts),
                "-map", "[vout]", "-map", "[aout]",
            ])
        else:
            final_cmd.extend([
                "-filter_complex", ";".join(filter_parts),
                "-map", "[vout]", "-an",
            ])

        import datetime
        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z")

        has_audio = bool(music_track or has_hook_audio or has_outro)
        final_cmd.extend([
            "-t", f"{total_duration}",
            "-frames:v", str(round(total_duration * settings.fps)),
            "-r", str(settings.fps),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1",
            "-pix_fmt", "yuv420p",
            # Strip FFmpeg / Lavf automation traces
            "-map_metadata", "-1",
            "-fflags", "+bitexact",
            "-flags:v", "+bitexact",
            "-flags:a", "+bitexact",
            "-metadata:s:v:0", "encoder=CapCut",
            "-metadata", "encoder=CapCut",
            "-metadata", "comment=CapCut",
            "-metadata", f"creation_time={now_iso}",
            "-brand", "mp42",
        ])

        if has_audio:
            final_cmd.extend([
                "-c:a", "aac", "-b:a", "192k",
                "-metadata:s:a:0", "encoder=CapCut",
            ])

        final_cmd.extend(["-movflags", "+faststart", "-y", str(output)])

        project.finish(final_cmd,output,top_path,conc_png,music_track,outro_voice)
        _run(final_cmd, timeout=900)
        time.sleep(0.5)

        return {
            "version": "v2",
            **project.details(),
            "width": settings.width,
            "height": settings.height,
            "duration": total_duration,
            "audio": bool(music_track or has_hook_audio or has_outro),
            "music_track": str(music_track.name) if music_track else None,
            "tts_narration": has_hook_audio,
            "outro_voiceover": has_outro,
            "timeline": {
                **{f"page_{i + 1}": f"{int(bounds[i] // 60)}:{bounds[i] % 60:04.1f}-{int(bounds[i + 1] // 60)}:{bounds[i + 1] % 60:04.1f}" for i in range(len(editorial.pages))},
                "conclusion": f"{int(reading_end // 60)}:{reading_end % 60:04.1f}-{int(total_duration // 60)}:{total_duration % 60:04.1f}",
            },
        }
