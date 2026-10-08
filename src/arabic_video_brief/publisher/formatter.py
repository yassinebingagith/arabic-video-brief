from __future__ import annotations

import datetime
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..utils import slugify


@dataclass(frozen=True)
class FormattedPost:
    video_path: Path
    youtube_title: str
    youtube_description: str
    tiktok_caption: str
    meta_caption: str
    deep_dive_caption: str | None = None
    cover_facebook_4x5: Path | None = None
    cover_vertical_9x16: Path | None = None


def load_post_data(folder_path: Path | str) -> FormattedPost:
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Directory not found: {folder}")

    # Resolve target folder (check folder or folder/v2)
    if not (folder / "brief.mp4").is_file() and not any(folder.glob("CapCut_1080p_*.mp4")):
        if (folder / "v2").is_dir() and ((folder / "v2" / "brief.mp4").is_file() or any((folder / "v2").glob("CapCut_1080p_*.mp4"))):
            folder = folder / "v2"

    title_file = folder / "post-title.txt"
    desc_file = folder / "post-description.txt"

    raw_title = title_file.read_text(encoding="utf-8").strip() if title_file.exists() else folder.name
    raw_desc = desc_file.read_text(encoding="utf-8").strip() if desc_file.exists() else raw_title

    # --- Maintain Strictly ONE Authentic CapCut Video Filename for Social Upload ---
    # Social platforms inspect client filenames. Having 'brief.mp4' flags bot automation.
    # We consolidate strictly into ONE video file: CapCut_1080p_{YYYYMMDD}_{slug}.mp4
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    raw_slug = slugify(raw_title)
    if not raw_slug or len(raw_slug) < 3:
        raw_slug = slugify(folder.name)
    short_slug = raw_slug[:45].rstrip("-_")
    capcut_name = f"CapCut_1080p_{date_str}_{short_slug}.mp4"
    upload_video_path = folder / capcut_name

    existing_capcut = list(folder.glob("CapCut_1080p_*.mp4"))
    canonical_brief = folder / "brief.mp4"

    if existing_capcut:
        upload_video_path = existing_capcut[0]
        # Clean up redundant brief.mp4 if still present so only one video remains
        if canonical_brief.is_file():
            try:
                canonical_brief.unlink(missing_ok=True)
            except Exception:
                pass
    elif canonical_brief.is_file():
        # Rename brief.mp4 to CapCut export filename so only 1 clean file exists
        try:
            canonical_brief.rename(upload_video_path)
        except Exception:
            shutil.copyfile(str(canonical_brief), str(upload_video_path))
            canonical_brief.unlink(missing_ok=True)
    else:
        raise FileNotFoundError(f"No video brief found in: {folder}")

    # --- Defensive Strikethrough Sanitization ---
    # Convert any legacy or LLM hyphen headers like -عنوان المحور- to ◈ عنوان المحور ◈
    # to permanently eliminate YouTube's native Markdown strikethrough interpretation
    clean_lines = []
    for ln in raw_desc.splitlines():
        trimmed = ln.strip()
        if (
            (trimmed.startswith(("-", "–", "—")) and trimmed.endswith(("-", "–", "—")))
            and len(trimmed) > 2
            and not trimmed.startswith("---")
        ):
            inner = trimmed.strip("-–— ").strip()
            clean_lines.append(f"◈ {inner} ◈")
        else:
            clean_lines.append(ln)
    clean_desc = "\n".join(clean_lines)

    # --- YouTube Shorts Formatting ---
    yt_title_base = raw_title.strip()
    if not re.search(r"#shorts?\b", yt_title_base, flags=re.IGNORECASE):
        yt_candidate = f"{yt_title_base} #Shorts"
    else:
        yt_candidate = yt_title_base

    # YouTube max title is 100 chars
    if len(yt_candidate) > 100:
        max_len = 100 - len(" #Shorts")
        truncated = yt_title_base[:max_len].strip()
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0].rstrip(" ،,.-")
        yt_title = f"{truncated} #Shorts"
    else:
        yt_title = yt_candidate

    yt_description = clean_desc[:5000].strip()

    # --- TikTok & Meta Formatting ---
    # Combine title, narrative, and hashtags safely under 2,000 characters
    hashtags = re.findall(r"#[\w\u0600-\u06FF]+", clean_desc)
    hashtags_str = " ".join(hashtags) if hashtags else "#بودكاست #وعي #تطوير_الذات"

    # Clean description body without hashtags and CTA for compact caption
    body = clean_desc
    body = re.sub(r"#[\w\u0600-\u06FF]+", "", body).strip()
    body = re.sub(r"🔔.*$", "", body, flags=re.MULTILINE).strip()
    body = re.sub(r"✨.*$", "", body, flags=re.MULTILINE).strip()
    body = re.sub(r"💡.*$", "", body, flags=re.MULTILINE).strip()
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    if body.startswith(raw_title):
        body = body[len(raw_title):].strip()

    caption = f"{raw_title}\n\n{body}\n\n{hashtags_str}".strip()

    if len(caption) > 2000:
        allowed_body = 2000 - len(raw_title) - len(hashtags_str) - 20
        truncated_body = body[:allowed_body].rsplit(" ", 1)[0] + "..."
        caption = f"{raw_title}\n\n{truncated_body}\n\n{hashtags_str}".strip()

    fb_candidates = [
        folder / "cover_facebook_4x5.png",
        folder / "cover_facebook_4x5.jpg",
        folder / "cover_facebook_4x5.jpeg",
        folder / "cover_facebook_4x5.webp",
    ]
    vert_candidates = [
        folder / "cover_vertical_9x16.png",
        folder / "cover_vertical_9x16.jpg",
        folder / "cover_vertical_9x16.jpeg",
        folder / "cover_vertical_9x16.webp",
    ]
    cover_fb = next((p for p in fb_candidates if p.is_file()), None)
    cover_vert = next((p for p in vert_candidates if p.is_file()), None)

    # Check for exhaustive Deep-Dive Educational Synthesis
    deepdive_candidates = [
        folder / "deep_dive_summary.txt",
        folder.parent / "deep_dive_summary.txt" if folder.name == "v2" else folder / "deep_dive_summary.txt",
    ]
    deepdive_file = next((p for p in deepdive_candidates if p.is_file()), None)
    deep_dive_text = None
    if deepdive_file and deepdive_file.is_file():
        raw_dd = deepdive_file.read_text(encoding="utf-8").strip()
        try:
            from ..deepdive import sanitize_deepdive_text
            deep_dive_text = sanitize_deepdive_text(raw_dd)
        except Exception:
            deep_dive_text = raw_dd

    # Automatically eradicate C2PA provenance and AI metadata so Meta/TikTok never tag the post as AI
    try:
        from ..thumbnail.sanitizer import sanitize_image
        if cover_fb:
            sanitize_image(cover_fb)
        if cover_vert:
            sanitize_image(cover_vert)
    except Exception:
        pass

    return FormattedPost(
        video_path=upload_video_path,
        youtube_title=yt_title,
        youtube_description=yt_description,
        tiktok_caption=caption,
        meta_caption=caption,
        deep_dive_caption=deep_dive_text,
        cover_facebook_4x5=cover_fb,
        cover_vertical_9x16=cover_vert,
    )
