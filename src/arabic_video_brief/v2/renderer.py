from __future__ import annotations

import logging
import math
import re
import shutil
import subprocess
import tempfile
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
    find_ffmpeg,
    infer_category,
    render_metadata_bar,
    render_source_card,
    render_top_overlay,
    select_background_music,
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
) -> None:
    """
    Renders one of the 4 summary pages (1080x1920) for the lower panel.
    - NO page counter numbers (completely removed per user instruction).
    - Page 1 headlines are centered horizontally.
    - Generous typography (48-52px) filling the lower panel without a huge black void.
    - Respects bottom 15% safe margin.
    """
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (settings.width, settings.height), "#000000")
    draw = ImageDraw.Draw(image)

    panel_top = settings.top_height
    safe_bottom = settings.height - int(settings.height * 0.15)
    side_margin = 100
    # Safe text width respecting the 6% left-shift to clear right-side platform action buttons
    offset_x = int(settings.width * settings.text_offset_ratio)  # ~65px
    max_text_width = settings.width - (side_margin * 2) - offset_x  # ~815px
    content_right = settings.width - side_margin - offset_x

    cur_y = panel_top + 20

    # Page 1: Centered Headline Block
    if page_index == 1:
        if main_title:
            title_font = ImageFont.truetype(str(settings.font_path), 38)
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
                sub_font.set_variation_by_name("Medium")
            except (AttributeError, OSError, ValueError):
                pass
            s_vis = _display_text(f"النوع: {category}")
            s_box = draw.textbbox((0, 0), s_vis, font=sub_font)
            s_w = s_box[2] - s_box[0]
            draw.text(((settings.width - s_w) // 2, cur_y), s_vis, font=sub_font, fill="#A0A0A0")  # Centered!
            cur_y += (s_box[3] - s_box[1]) + 26

    # Body Typography: Large and filling the available panel comfortably
    # Page 1 has header block so 48px; Pages 2, 3, 4 have full space so 52px
    body_font_size = 48 if page_index == 1 else 52
    body_font = ImageFont.truetype(str(settings.font_path), body_font_size)
    try:
        body_font.set_variation_by_name("SemiBold")
    except (AttributeError, OSError, ValueError):
        pass

    lines = _wrap_rtl(text, body_font, max_text_width)
    line_h = math.ceil(body_font_size * 1.55)
    total_text_h = len(lines) * line_h

    # Vertically balance the body text within the remaining panel height
    remaining_h = safe_bottom - cur_y
    if remaining_h > total_text_h and page_index > 1:
        # Vertically center in the lower panel
        cur_y = panel_top + (safe_bottom - panel_top - total_text_h) // 2
    elif remaining_h > total_text_h:
        # Add slight breathing room below header
        cur_y += max(16, (remaining_h - total_text_h) // 3)

    for line in lines:
        vis = _display_text(line)
        box = draw.textbbox((0, 0), vis, font=body_font)
        lw = box[2] - box[0]
        x = content_right - lw
        draw.text((x, cur_y), vis, font=body_font, fill="#FFFFFF")
        cur_y += line_h

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
    Renders the dedicated full-page conclusion & CTA (1080x1920) for 0:22.5-0:26.
    The top 760px retains the static source card (matching user instruction).
    The lower panel displays the memorable conclusion (Gold words), contextual save CTA,
    description CTA, and a larger Capsule Fikr logo at the bottom.
    """
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (settings.width, settings.height), "#000000")

    # Paste the static source card in the top panel (1080x760)
    if source_card_path.exists():
        with Image.open(source_card_path) as card_img:
            image.paste(card_img.convert("RGB"), (0, 0))

    draw = ImageDraw.Draw(image)

    panel_top = settings.top_height
    # Strict platform safe margins (15% left & right margin = 162px each -> max content width = 756px)
    # This completely prevents any overlap with TikTok / Reels / Shorts action buttons.
    side_safe_margin = int(settings.width * 0.15)  # 162px
    max_safe_width = settings.width - (2 * side_safe_margin)  # 756px

    # 1. Main Conclusion (Max 12 words) - Kept prominent and centered
    conc_font = ImageFont.truetype(str(settings.font_path), 46)
    try:
        conc_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    conc_lines = _balance_wrap(conclusion_text, conc_font, max_safe_width)
    conc_line_h = math.ceil(46 * 1.45)
    conc_y = panel_top + 45

    for line in conc_lines:
        vis = _display_text(line)
        box = draw.textbbox((0, 0), vis, font=conc_font)
        tw = box[2] - box[0]
        tx = (settings.width - tw) // 2

        is_hl = any(h.strip() in line for h in conclusion_highlights if h.strip())
        col = "#F5C518" if is_hl else "#FFFFFF"

        draw.text((tx + 2, conc_y + 2), vis, font=conc_font, fill="#000000")
        draw.text((tx, conc_y), vis, font=conc_font, fill=col)
        conc_y += conc_line_h

    # 2. Action Pill Box (Save / Share / Follow): Clean, high contrast, enlarged font, NO repetitive description
    # Clean text to strictly avoid any description duplication
    clean_save_cta = save_cta.strip()
    # Remove any stray description phrases if ever passed
    clean_save_cta = re.sub(r"(?:السر الأهم|الخطوات التطبيقية|في الوصف|بالأسفل|👇).*", "", clean_save_cta).strip()
    if not clean_save_cta or len(clean_save_cta) < 10:
        clean_save_cta = "احفظها وشاركها مع أصدقائك، وتابع الصفحة للمزيد"

    cur_save_size = 34
    save_font = ImageFont.truetype(str(settings.font_path), cur_save_size)
    try:
        save_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    save_vis = _display_text(clean_save_cta)
    s_box = draw.textbbox((0, 0), save_vis, font=save_font)
    sw = s_box[2] - s_box[0]

    # Auto-scale font down to minimum 24px so it stays strictly within the 15% safe margin (max_safe_width - 40)
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
    save_pill_h = 66
    save_pill_x = (settings.width - save_pill_w) // 2
    save_pill_y = conc_y + 32

    # High-contrast outline pill
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

    # 3. Capsule Fikr Logo & Brand Label
    logo_size = 145
    logo_x = (settings.width - logo_size) // 2
    logo_y = save_pill_y + save_pill_h + 30

    if avatar_path and avatar_path.exists():
        try:
            av_img = Image.open(avatar_path).convert("RGBA")
            av_img = av_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, logo_size, logo_size), fill=255)
            image.paste(av_img, (logo_x, logo_y), mask)
            # Bold Gold outline ring around the logo
            draw.ellipse((logo_x, logo_y, logo_x + logo_size, logo_y + logo_size), outline="#F5C518", width=4)
        except Exception as err:
            logger.warning("Failed to render avatar logo: %s", err)

    # Brand text label under logo
    brand_font = ImageFont.truetype(str(settings.font_path), 30)
    try:
        brand_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass
    brand_vis = _display_text("كبسولة فكر")
    b_box = draw.textbbox((0, 0), brand_vis, font=brand_font)
    bw = b_box[2] - b_box[0]
    brand_y = logo_y + logo_size + 10
    draw.text(((settings.width - bw) // 2, brand_y), brand_vis, font=brand_font, fill="#F5C518")

    # 4. Primary Description CTA: Filled Glowing Gold Badge within 15% safe margin
    clean_desc_cta = desc_cta.replace("👇", "").strip()
    if not clean_desc_cta:
        clean_desc_cta = "السر الأهم والخطوات التطبيقية في الوصف بالأسفل"

    cur_desc_size = 36
    desc_font = ImageFont.truetype(str(settings.font_path), cur_desc_size)
    try:
        desc_font.set_variation_by_name("Bold")
    except (AttributeError, OSError, ValueError):
        pass

    d_vis = _display_text(clean_desc_cta)
    d_box = draw.textbbox((0, 0), d_vis, font=desc_font)
    dw = d_box[2] - d_box[0]

    # Auto-scale font so the entire gold badge fits comfortably inside the 15% safe margin
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
    desc_pill_y = max(brand_y + 42, 1340)

    # Subtle outer glow shadow for high contrast
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
    # Bold Black text on Gold badge
    draw.text(
        (desc_pill_x + (desc_pill_w - dw) // 2, desc_pill_y + (desc_pill_h - (d_box[3] - d_box[1])) // 2 - d_box[1]),
        d_vis,
        font=desc_font,
        fill="#000000",
    )

    # 5. Prominent Downward pointing indicator chevron/arrow
    arrow_x = settings.width // 2
    arrow_y = desc_pill_y + desc_pill_h + 14
    draw.line([(arrow_x, arrow_y), (arrow_x, arrow_y + 18)], fill="#F5C518", width=6)
    draw.polygon([
        (arrow_x - 16, arrow_y + 14),
        (arrow_x + 16, arrow_y + 14),
        (arrow_x, arrow_y + 32),
    ], fill="#F5C518")

    image.save(output_path, format="PNG")



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
    """
    Renders the complete 26-second V2 vertical MP4:
    - 0:00-0:02.5: Hook (top source card + bottom hook with Gold highlight & badge + ElevenLabs narration)
    - 0:02.5-0:05.0: Page 1 with static source card
    - 0:05.0-0:07.5: Page 1 with muted source video playback
    - 0:07.5-0:12.5: Page 2 with muted video playback
    - 0:12.5-0:17.5: Page 3 with muted video playback
    - 0:17.5-0:22.5: Page 4 with muted video playback
    - 0:22.5-0:26.0: Conclusion & CTA with top source card and larger Capsule Fikr logo
    - Background Music: Naruto Sadness and Sorrow (or configured music)
    """
    ffmpeg = find_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)

    total_duration = settings.duration_v2  # 26.0s
    start_time = float(selected_clip.get("start_seconds", 0.0))

    with tempfile.TemporaryDirectory(prefix="avbrief-v2-render-", dir=output.parent) as temp_dir_str:
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

        # 3. Render Top Panel MP4 (Exact 36.5s duration)
        # 0:00 to 0:02.5 (2.5s): Kinetic Ken Burns zoom on source_card + floating overlay
        # 0:02.5 to 0:28.5 (26.0s): Full 1080x760 video stream with floating overlay & seamless gradient blend
        # 0:28.5 to 0:36.5 (8.0s): Kinetic Ken Burns zoom on CTA card + floating overlay
        top_path = temp / "top_v2.mp4"
        open_dur = 2.5
        v_stream_dur = 26.0
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

        page_pngs: list[Path] = []
        for i, page_text in enumerate(editorial.pages):
            p_png = temp / f"page_{i + 1}.png"
            render_v2_summary_page(
                page_text,
                page_index=i + 1,
                output_path=p_png,
                settings=settings,
                main_title=clean_title if i == 0 else None,
                category=category if i == 0 else None,
            )
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

        # 5. Background music selection: Naruto Sadness and Sorrow as default V2 music
        v2_music_file = settings.music_dir / "naruto_sadness_and_sorrow.mp3"
        if v2_music_file.exists():
            music_track = v2_music_file
        else:
            music_track = select_background_music(settings.music_dir)

        # 6. Compose Video Filtergraph across the timeline
        # Top panel is at (0, 0) continuously across all total_duration
        # Bottom panel transitions:
        # page_1.png: 0 to 9.0s (9.0s total - ample reading time + voiceover)
        # page_2.png: 9.0 to 15.5s (6.5s)
        # page_3.png: 15.5 to 22.0s (6.5s)
        # page_4.png: 22.0 to 28.5s (6.5s)
        # conclusion.png: 28.5 to total_duration (8.0s)

        filter_parts: list[str] = [
            f"color=c=black:s={settings.width}x{settings.height}:r={settings.fps}:d={total_duration}[base]",
            f"[1:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[p1]",
            f"[2:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[p2]",
            f"[3:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[p3]",
            f"[4:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[p4]",
            f"[5:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[conc]",
            "[base][p1]overlay=0:0:enable='lt(t,9.0)'[c1]",
            "[c1][p2]overlay=0:0:enable='between(t,9.0,15.5)'[c2]",
            "[c2][p3]overlay=0:0:enable='between(t,15.5,22.0)'[c3]",
            "[c3][p4]overlay=0:0:enable='between(t,22.0,28.5)'[c4]",
            "[c4][conc]overlay=0:0:enable='gte(t,28.5)'[c5]",
        ]

        final_cmd = [
            ffmpeg, "-hide_banner", "-loglevel", "error",
            "-i", str(top_path),
            "-i", str(page_pngs[0]),
            "-i", str(page_pngs[1]),
            "-i", str(page_pngs[2]),
            "-i", str(page_pngs[3]),
            "-i", str(conc_png),
        ]

        next_input_idx = 6

        # Check if Prussian Airbrush Frame asset is present
        has_frame = bool(settings.brand_frame_path and settings.brand_frame_path.exists())
        if has_frame:
            frame_idx = next_input_idx
            final_cmd.extend(["-i", str(settings.brand_frame_path)])
            next_input_idx += 1
            filter_parts.extend([
                "[c5][0:v]overlay=0:0[inner_full]",
                f"color=c=black:s={settings.width}x{settings.height}:r={settings.fps}:d={total_duration}[canvas_base]",
                "[inner_full]scale=972:1728:flags=lanczos[scaled_inner]",
                "[canvas_base][scaled_inner]overlay=54:96[padded_video]",
                f"[{frame_idx}:v]loop=loop=-1:size=1:start=0,fps={settings.fps},setpts=N/({settings.fps}*TB)[frame_v]",
                "[padded_video][frame_v]overlay=0:0[vout]",
            ])
        else:
            filter_parts.append("[c5][0:v]overlay=0:0[vout]")

        # Audio configuration:
        # Hook voiceover starts at t=0.
        # Music track plays with ducking during hook narration, then fades out before 28.5s.
        # Outro voiceover starts at t=28.5s during the 8.0s conclusion/CTA page.
        has_hook_audio = bool(hook_audio_path and hook_audio_path.exists())
        outro_voice = settings.outro_voiceover_path
        has_outro = bool(outro_voice and outro_voice.exists())

        fade_dur = 2.0
        fade_st = 26.5

        mix_inputs: list[str] = []

        if music_track:
            final_cmd.extend(["-i", str(music_track)])
            music_idx = next_input_idx
            next_input_idx += 1
            if has_hook_audio:
                voice_dur = 4.5
                try:
                    vinfo = probe_media(hook_audio_path, ffmpeg)
                    voice_dur = max(2.0, min(10.5, float(vinfo.duration)))
                except Exception:
                    voice_dur = 4.5
                filter_parts.append(
                    f"[{music_idx}:a]volume='if(lt(t,{voice_dur:.2f}), 0.12, min(0.70, 0.12 + (0.70-0.12)*(t-{voice_dur:.2f})/0.6))':eval=frame,"
                    f"afade=t=out:st={fade_st:.2f}:d={fade_dur:.2f},apad=whole_dur={total_duration}[ducked_music]"
                )
                mix_inputs.append("[ducked_music]")
            else:
                filter_parts.append(
                    f"[{music_idx}:a]volume={settings.music_volume},"
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

        if has_outro:
            final_cmd.extend(["-i", str(outro_voice)])
            outro_idx = next_input_idx
            next_input_idx += 1
            filter_parts.append(
                f"[{outro_idx}:a]atempo=1.084,volume=1.1,adelay=28500|28500,apad=whole_dur={total_duration}[outro_audio]"
            )
            mix_inputs.append("[outro_audio]")

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

        final_cmd.extend([
            "-t", f"{total_duration}",
            "-frames:v", str(round(total_duration * settings.fps)),
            "-r", str(settings.fps),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "1",
            "-pix_fmt", "yuv420p",
        ])

        if music_track or has_hook_audio or has_outro:
            final_cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        final_cmd.extend(["-movflags", "+faststart", "-y", str(output)])

        _run(final_cmd, timeout=900)

        return {
            "version": "v2",
            "width": settings.width,
            "height": settings.height,
            "duration": total_duration,
            "audio": bool(music_track or has_hook_audio or has_outro),
            "music_track": str(music_track.name) if music_track else None,
            "tts_narration": has_hook_audio,
            "outro_voiceover": has_outro,
            "timeline": {
                "page_1": "0:00-0:09.0",
                "page_2": "0:09.0-0:15.5",
                "page_3": "0:15.5-0:22.0",
                "page_4": "0:22.0-0:28.5",
                "conclusion": f"0:28.5-0:{total_duration:.1f}",
            },
        }
