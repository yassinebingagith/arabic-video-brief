from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://www.googleapis.com/youtube/v3"


def _get_json(endpoint: str, params: dict[str, str | int], timeout: int = 30) -> dict[str, Any]:
    url = f"{API_ROOT}/{endpoint}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "arabic-video-brief/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_iso_duration(value: str) -> int:
    match = re.fullmatch(r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?", value)
    if not match:
        return 0
    parts = {key: int(number or 0) for key, number in match.groupdict().items()}
    return parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]


def _video_row(item: dict[str, Any], reason: str) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})
    views = int(stats.get("viewCount", 0) or 0)
    likes = int(stats.get("likeCount", 0) or 0)
    comments = int(stats.get("commentCount", 0) or 0)
    return {
        "id": item.get("id"),
        "url": f"https://www.youtube.com/watch?v={item.get('id')}",
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "duration_seconds": parse_iso_duration(details.get("duration", "")),
        "views": views,
        "likes": likes,
        "comments": comments,
        "reason": reason,
    }


def search_videos(
    api_key: str,
    query: str,
    mode: str = "relevant",
    region: str = "US",
    language: str = "ar",
    duration: str = "any",
    limit: int = 5,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 10))
    region = region.upper()
    mode = mode.lower()
    if mode == "trending":
        payload = _get_json("videos", {
            "key": api_key,
            "part": "snippet,statistics,contentDetails,status",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": min(50, max(10, limit * 3)),
        })
        items = payload.get("items", [])
        if query:
            terms = [term.casefold() for term in re.findall(r"\w+", query)]
            items.sort(key=lambda item: sum(term in (item.get("snippet", {}).get("title", "") + " " + item.get("snippet", {}).get("description", "")).casefold() for term in terms), reverse=True)
        return [_video_row(item, f"Popular chart for {region}") for item in items[:limit]]

    order = {
        "recent": "date",
        "popular": "viewCount",
        "classic": "viewCount",
        "rated": "rating",
        "relevant": "relevance",
    }.get(mode, "relevance")
    params: dict[str, str | int] = {
        "key": api_key,
        "part": "snippet",
        "type": "video",
        "q": query,
        "order": order,
        "regionCode": region,
        "relevanceLanguage": language,
        "safeSearch": "moderate",
        "videoEmbeddable": "true",
        "maxResults": min(50, max(15, limit * 4)),
    }
    if duration in {"short", "medium", "long"}:
        params["videoDuration"] = duration
    if mode == "classic":
        cutoff = datetime.now(timezone.utc) - timedelta(days=365 * 5)
        params["publishedBefore"] = cutoff.isoformat().replace("+00:00", "Z")
    search_payload = _get_json("search", params)
    ids = [item.get("id", {}).get("videoId") for item in search_payload.get("items", [])]
    ids = [video_id for video_id in ids if video_id]
    if not ids:
        return []
    details = _get_json("videos", {
        "key": api_key,
        "part": "snippet,statistics,contentDetails,status",
        "id": ",".join(ids[:50]),
    })
    rows = [_video_row(item, f"{mode.title()} match for '{query}'") for item in details.get("items", [])]
    if mode == "classic":
        rows.sort(key=lambda row: math.log10(row["views"] + 1) + math.log10(row["likes"] + 1) * 0.3, reverse=True)
    return rows[:limit]


def fetch_video_details(video_id: str, api_key: str | None) -> dict[str, Any] | None:
    """Fetch official metadata and prioritize English localizations for multi-language videos."""
    if not api_key:
        return None
    try:
        data = _get_json("videos", {
            "key": api_key,
            "part": "snippet,localizations",
            "id": video_id,
        })
        items = data.get("items", [])
        if not items:
            return None
        item = items[0]
        snippet = item.get("snippet", {})
        localizations = item.get("localizations", {})

        raw_title = snippet.get("title") or ""
        is_arabic_title = bool(re.search(r"[\u0600-\u06FF]", raw_title))

        # If English localization is available, prioritize it ONLY for non-Arabic titles
        # so international titles get clean English versions, while original Arabic titles are strictly kept intact.
        en_loc = (
            localizations.get("en-US")
            or localizations.get("en")
            or localizations.get("en-GB")
        )
        en_title = en_loc.get("title") if en_loc else None
        en_desc = en_loc.get("description") if en_loc else None

        if is_arabic_title:
            title = raw_title
            desc = snippet.get("description") or ""
        else:
            title = en_title or raw_title
            desc = en_desc or snippet.get("description") or ""

        return {
            "title": title,
            "original_title": raw_title,
            "is_arabic_title": is_arabic_title,
            "channel": snippet.get("channelTitle") or "",
            "tags": snippet.get("tags") or [],
            "published_at": snippet.get("publishedAt") or "",
            "default_language": snippet.get("defaultLanguage") or snippet.get("defaultAudioLanguage") or "",
            "has_english_localization": bool(en_title),
            "description": desc,
        }
    except Exception:
        return None
