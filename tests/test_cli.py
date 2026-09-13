import json

from arabic_video_brief.cli import main


def test_search_requests_web_fallback_without_key(monkeypatch, capsys) -> None:
    monkeypatch.setenv("YOUTUBE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    result = main(["search", "--query", "psychology", "--mode", "popular"])
    payload = json.loads(capsys.readouterr().out)
    assert result == 2
    assert payload["status"] == "fallback_required"
    assert "AIza" not in json.dumps(payload)
