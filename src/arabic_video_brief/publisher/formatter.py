from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FormattedPost:
    video_path: Path
    youtube_title: str
    youtube_description: str
    tiktok_caption: str
    meta_caption: str


def load_post_data(folder_path: Path | str) -> FormattedPost:
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Directory not found: {folder}")

    video_path = folder / "brief.mp4"
    if not video_path.is_file() and (folder / "v2" / "brief.mp4").is_file():
        folder = folder / "v2"
        video_path = folder / "brief.mp4"
    elif not video_path.is_file():
        raise FileNotFoundError(f"Video file 'brief.mp4' not found in: {folder}")

    title_file = folder / "post-title.txt"
    desc_file = folder / "post-description.txt"

    raw_title = title_file.read_text(encoding="utf-8").strip() if title_file.exists() else folder.name
    raw_desc = desc_file.read_text(encoding="utf-8").strip() if desc_file.exists() else raw_title

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

    yt_description = raw_desc[:5000].strip()

    # --- TikTok & Meta Formatting ---
    # Combine title, narrative, and hashtags safely under 2,000 characters
    # Extract hashtags
    hashtags = re.findall(r"#[\w\u0600-\u06FF]+", raw_desc)
    hashtags_str = " ".join(hashtags) if hashtags else "#بودكاست #وعي #تطوير_الذات"

    # Clean description body without hashtags and CTA for compact caption
    body = raw_desc
    body = re.sub(r"#[\w\u0600-\u06FF]+", "", body).strip()
    body = re.sub(r"🔔.*$", "", body, flags=re.MULTILINE).strip()
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    caption = f"{raw_title}\n\n{body}\n\n{hashtags_str}".strip()

    if len(caption) > 2000:
        allowed_body = 2000 - len(raw_title) - len(hashtags_str) - 20
        truncated_body = body[:allowed_body].rsplit(" ", 1)[0] + "..."
        caption = f"{raw_title}\n\n{truncated_body}\n\n{hashtags_str}".strip()

    return FormattedPost(
        video_path=video_path,
        youtube_title=yt_title,
        youtube_description=yt_description,
        tiktok_caption=caption,
        meta_caption=caption,
    )
