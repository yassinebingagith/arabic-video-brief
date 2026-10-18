import json
from contextlib import nullcontext
from pathlib import Path

import pytest

from arabic_video_brief.publisher.completion import mark_episode_done
from arabic_video_brief.publisher import dispatcher


def test_v2_publication_marks_parent_and_rebases_local_paths(tmp_path):
    episode = tmp_path / "episode"
    v2 = episode / "v2"
    v2.mkdir(parents=True)
    (episode / "v3").mkdir()
    (v2 / "manifest.json").write_text(json.dumps({"files": {"video": str(v2 / "video.mp4")},
                                               "source": "https://example.com/source"}))
    (v2 / "video.mp4").write_bytes(b"unchanged-video")
    (episode / "v3/generation-plan.json").write_text(json.dumps({"output_path": "instagram/slide01.png"}))
    result = mark_episode_done(v2)
    moved = tmp_path / "Done-episode"
    assert Path(result["folder"]) == moved / "v2"
    assert (moved / "v2/video.mp4").read_bytes() == b"unchanged-video"
    manifest = json.loads((moved / "v2/manifest.json").read_text())
    assert manifest["files"]["video"] == str(moved / "v2/video.mp4")
    assert manifest["source"] == "https://example.com/source"
    assert json.loads((moved / "v3/generation-plan.json").read_text())["output_path"] == "instagram/slide01.png"
    assert mark_episode_done(moved / "v2")["status"] == "already_marked"


def test_done_collision_does_not_overwrite(tmp_path):
    (tmp_path / "episode").mkdir()
    (tmp_path / "Done-episode").mkdir()
    with pytest.raises(FileExistsError):
        mark_episode_done(tmp_path / "episode")
    assert (tmp_path / "episode").is_dir()


def test_draft_does_not_prevent_later_real_publication(tmp_path):
    from arabic_video_brief.publisher.tracker import record_publish_result, is_already_published
    record_publish_result(tmp_path, "tiktok", "success", publication_state="draft")
    assert not is_already_published(tmp_path, "tiktok")
    record_publish_result(tmp_path, "tiktok", "success", publication_state="published")
    assert is_already_published(tmp_path, "tiktok")


@pytest.mark.parametrize("draft,schedule,status,marked", [
    (False, None, "success", True), (True, None, "success", False),
    (False, "2027-01-01 10:00", "success", False), (False, None, "failed", False),
])
def test_tiktok_only_marks_after_confirmed_live_success(tmp_path, monkeypatch, draft, schedule, status, marked):
    episode = tmp_path / "episode"
    episode.mkdir()
    (episode / "brief.mp4").write_bytes(b"video")
    (episode / "post-title.txt").write_text("عنوان", encoding="utf-8")
    (episode / "post-description.txt").write_text("وصف", encoding="utf-8")
    monkeypatch.setattr(dispatcher, "sync_playwright", lambda: nullcontext(None))
    monkeypatch.setattr(dispatcher, "persistent_browser_context", lambda *a, **kw: nullcontext(None))
    monkeypatch.setattr(dispatcher, "publish_to_tiktok", lambda *a, **kw: {"status": status})
    result = dispatcher.publish_folder(episode, platform="tiktok", draft=draft, schedule=schedule)
    assert (tmp_path / "Done-episode").exists() is marked
    assert Path(result["folder"]).exists()
    if marked:
        receipt = json.loads((Path(result["folder"]) / "publish_status.json").read_text())
        assert receipt["tiktok"]["publication_state"] == "published"
