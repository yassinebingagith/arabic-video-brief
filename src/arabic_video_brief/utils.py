from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


def youtube_video_id(value: str) -> str | None:
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return None
    host = parsed.netloc.lower().split(":", 1)[0]
    if host not in YOUTUBE_HOSTS:
        return None
    if host.endswith("youtu.be"):
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif parsed.path == "/watch":
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
        candidate = parsed.path.strip("/").split("/", 1)[1].split("/", 1)[0]
    else:
        return None
    return candidate if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", candidate) else None


def canonical_source(value: str) -> str:
    video_id = youtube_video_id(value)
    if video_id:
        return f"youtube:{video_id}"
    path = Path(value).expanduser()
    if path.exists():
        return f"file:{path.resolve()}".lower()
    return value.strip()


def deduplicate_sources(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = canonical_source(value)
        if key not in seen:
            seen.add(key)
            output.append(value)
    return output


def slugify(value: str, fallback: str = "video") -> str:
    text = re.sub(r"[^\w\-\u0600-\u06FF]+", "-", value, flags=re.UNICODE).strip("-_")
    return (text[:80] or fallback).rstrip("-_")


def source_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text.strip()))


def split_summary(text: str, page_min_words: int = 70, page_max_words: int = 80) -> tuple[str, str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        raise ValueError("Arabic summary is empty")
    words = clean.split()
    midpoint = len(words) / 2
    lower = max(1, page_min_words, len(words) - page_max_words)
    upper = min(len(words) - 1, page_max_words, len(words) - page_min_words)
    allowed = range(lower, upper + 1) if lower <= upper else range(1, len(words))
    candidates: list[int] = []
    for index in allowed:
        word = words[index - 1]
        if re.search(r"[.!؟؛…]$", word):
            candidates.append(index)
    fallback = list(allowed)
    split_at = min(candidates or fallback, key=lambda i: abs(i - midpoint))
    split_at = max(1, min(len(words) - 1, split_at))
    return " ".join(words[:split_at]), " ".join(words[split_at:])


def redact(value: str, secrets: list[str | None]) -> str:
    result = value
    for secret in secrets:
        if secret and len(secret) >= 6:
            result = result.replace(secret, "[REDACTED]")
    return result


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
