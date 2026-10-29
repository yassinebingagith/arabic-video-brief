import pytest

from arabic_video_brief.config import Settings
from arabic_video_brief.ending import normalize_question, resolve_ending_question
from arabic_video_brief.v2.editorial import build_v2_editorial_package


QUESTION = "ما المهارة التي تؤجل التدرب على أصعب جزء فيها؟"


def test_authored_question_needs_no_extra_model_call(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("Authored question must not invoke a model")
    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", unexpected)
    assert resolve_ending_question({"ending_question_ar": QUESTION}, {}, "", Settings()) == QUESTION
    package = build_v2_editorial_package({"post_title_ar": "التدريب", "pages": ["مثال."] * 4,
                                         "ending_question_ar": QUESTION}, {}, Settings())
    assert package.conclusion_ar == QUESTION


def test_legacy_statement_is_replaced_and_invalid_generation_retried(monkeypatch):
    outputs = iter(['{"ending_question_ar":"التدريب يحسن الأداء."}', '{"ending_question_ar":"' + QUESTION + '"}'])
    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", lambda *a, **k: next(outputs))
    assert resolve_ending_question({"conclusion": "التدريب يحسن الأداء."}, {}, "التدريب", Settings()) == QUESTION


@pytest.mark.parametrize("text", ["خلاصة لا تتضمن سؤالاً", "ما رأيك في هذا الموضوع؟", "What do you think?", "هل تقرأ؟ ولماذا تفعل ذلك؟"])
def test_invalid_ending_is_not_accepted(text):
    assert normalize_question(text) == ""


def test_invalid_generated_question_fails_instead_of_silently_using_a_conclusion(monkeypatch):
    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", lambda *a, **k: '{}')
    with pytest.raises(ValueError, match="ending_question_ar"):
        resolve_ending_question({}, {}, "ملخص", Settings())


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_rerender_reuses_saved_question_and_updates_manifest(tmp_path, monkeypatch, version):
    import json
    from arabic_video_brief.rerender import rerender_folder

    (tmp_path / "manifest.json").write_text(json.dumps({
        "source": "https://www.youtube.com/watch?v=abcdefghijk",
        "render": {"version": version}, "pages_ar": ["نص أول.", "نص ثان."],
        "conclusion": {"text": "الخلاصة القديمة"},
    }), encoding="utf-8")
    (tmp_path / "ending-question-ar.txt").write_text(QUESTION, encoding="utf-8")
    if version == "v2":
        (tmp_path / "summary-pages.json").write_text(json.dumps([
            {"text": "مثال."} for _ in range(4)
        ]), encoding="utf-8")

    def unexpected(*args, **kwargs):
        raise AssertionError("Saved question must not invoke a model")

    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", unexpected)
    monkeypatch.setattr("arabic_video_brief.rerender.download_youtube",
                        lambda *a, **k: {"video_path": str(tmp_path / "source.mp4")})
    captured = {}

    def fake_render(**kwargs):
        captured.update(kwargs)
        project = tmp_path / "render-project"
        project.mkdir(exist_ok=True)
        (project / "project.json").write_text(json.dumps({"renderer": "python-whiteboard"}), encoding="utf-8")
        return {"version": version}

    target = ("arabic_video_brief.rerender.render_video" if version == "v1"
              else "arabic_video_brief.v2.renderer.render_v2_video")
    monkeypatch.setattr(target, fake_render)
    result = rerender_folder(tmp_path, Settings())
    assert result["status"] == "success"
    actual = captured["ending_question"] if version == "v1" else captured["editorial"].conclusion_ar
    assert actual == QUESTION
    saved = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert saved["ending_question_ar"] == QUESTION
    assert saved["files"]["render_project"] == str(tmp_path / "render-project")
    if version == "v2":
        assert (tmp_path / "conclusion-ar.txt").read_text(encoding="utf-8").strip() == QUESTION
        assert saved["conclusion"]["text"] == QUESTION
