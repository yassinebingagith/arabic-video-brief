from unittest.mock import patch

from arabic_video_brief.youtube import parse_iso_duration, search_videos


def test_parse_iso_duration() -> None:
    assert parse_iso_duration("PT1H2M3S") == 3723
    assert parse_iso_duration("PT45S") == 45
    assert parse_iso_duration("invalid") == 0


def test_trending_search_returns_ranked_rows() -> None:
    payload = {
        "items": [
            {
                "id": "abcdefghijk",
                "snippet": {"title": "علم النفس اليوم", "description": "شرح", "channelTitle": "قناة", "publishedAt": "2026-01-01T00:00:00Z"},
                "statistics": {"viewCount": "1000", "likeCount": "100"},
                "contentDetails": {"duration": "PT10M"},
            }
        ]
    }
    with patch("arabic_video_brief.youtube._get_json", return_value=payload):
        rows = search_videos("fake-key", "علم النفس", mode="trending", region="MA", limit=5)
    assert rows[0]["url"].endswith("abcdefghijk")
    assert rows[0]["duration_seconds"] == 600
    assert "MA" in rows[0]["reason"]
