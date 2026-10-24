import json

import pytest
from PIL import Image

from arabic_video_brief.config import Settings
from arabic_video_brief.ending import normalize_footer
from arabic_video_brief.thumbnail import generate_thumbnail_package, process_folder_thumbnails
from arabic_video_brief.utils import split_summary
from arabic_video_brief.v2.editorial import build_v2_editorial_package


QUESTION = "ما الدليل الذي قد يدفعك إلى مراجعة قناعة تتمسك بها؟"
ACTION = "اختر قناعة واحدة واكتب الدليل الذي يمكن أن يغيّرها."


def no_model(*args, **kwargs):
    raise AssertionError("Authored assets must not require an extra model call")


def test_source_reference_wins_over_philosophy_and_interview_keywords(tmp_path, monkeypatch):
    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", no_model)
    ref = tmp_path / "original.png"
    Image.new("RGB", (320, 180), "white").save(ref)
    package = generate_thumbnail_package(
        "لماذا نتمسك بأفكارنا؟",
        {"metadata": {"title": "Carl Jung Philosophy Full Interview", "uploader": "Interview Channel"}},
        {"thumbnail_hook_ar": "متى تصبح قناعتك فخاً؟"}, ref,
    )
    assert package.reference_thumbnail_path == ref
    assert package.source_modality == "source_reference"
    assert package.visual_style.id == "source_led"
    assert "If the original is surrealist, keep surrealism" in package.vertical_master_prompt
    assert "A real speaker or podcast title does not override" in package.vertical_master_prompt
    assert package.fb_text_specs["headline_arabic"] == "متى تصبح قناعتك فخاً؟"
    assert "classical museum oil-on-canvas" not in package.fb_master_prompt


def test_manual_folder_preserves_source_title_and_carries_hook_and_reading_copy(tmp_path, monkeypatch):
    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", no_model)
    monkeypatch.setattr("urllib.request.urlopen", no_model)
    title = "لماذا يصعب علينا التخلي عن القناعات القديمة عندما تتغير الأدلة؟"
    hook = "متى تصبح قناعتك فخاً؟"
    body = "نتمسك بالتفسير الأول ثم نتجاهل الدليل الذي يناقضه."
    (tmp_path / "post-title.txt").write_text(title, encoding="utf-8")
    (tmp_path / "summary-ar.txt").write_text(body, encoding="utf-8")
    Image.new("RGB", (320, 180), "white").save(tmp_path / "source_thumbnail.png")
    _, vertical, _ = process_folder_thumbnails(tmp_path, creative_plan={"thumbnail_hook_ar": hook})
    assert (tmp_path / "post-title.txt").read_text(encoding="utf-8") == title
    assert (tmp_path / "thumbnail-hook-ar.txt").read_text(encoding="utf-8").strip() == hook
    assert not (tmp_path / "source_thumbnail.jpg").exists()
    content = vertical.read_text(encoding="utf-8")
    assert body in content
    assert f'Render ONLY this exact Arabic headline: "{hook}"' in content
    # Standalone regeneration reuses the hook and reading copy without a text call.
    process_folder_thumbnails(tmp_path)
    assert f'Render ONLY this exact Arabic headline: "{hook}"' in vertical.read_text(encoding="utf-8")


def test_legacy_folder_without_hook_explicitly_delegates_short_copy():
    package = generate_thumbnail_package("عنوان قديم طويل لا ينبغي أن يتحول كله إلى نص صغير على الغلاف")
    assert package.fb_text_specs["headline_arabic"].startswith("Pending:")
    assert "Author and render ONE source-faithful Arabic hook" in package.fb_master_prompt


def test_freeform_explicit_style_does_not_fall_back_to_cinematic():
    package = generate_thumbnail_package("فخ القناعة القديمة", style_preference="surrealism")
    assert package.visual_style.name == "surrealism"
    assert "Explicit requested treatment: surrealism" in package.fb_master_prompt


def test_kie_missing_reference_fails_before_submitting_unrelated_image(tmp_path, monkeypatch):
    from arabic_video_brief.thumbnail.image_client import ImageGeneratorClient
    monkeypatch.setattr("urllib.request.urlopen", no_model)
    with pytest.raises(ValueError, match="No source thumbnail URL"):
        ImageGeneratorClient(api_key="test-key").generate_kieai_thumbnails(tmp_path, "fb", "vertical")


@pytest.mark.parametrize("footer", [QUESTION, ACTION])
def test_v2_authored_footer_and_four_beats_survive_without_extra_model_call(monkeypatch, footer):
    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", no_model)
    pages = ["مثال محدد يفتح الفكرة.", "شرح الآلية وراء المثال.", "مقارنة تضيف معنى جديداً.", "حدود الفكرة ونتائجها."]
    package = build_v2_editorial_package({
        "post_title_ar": "عنوان المصدر", "summary_ar": "ملخص مختلف قديم.",
        "pages": pages, "ending_text_ar": footer, "thumbnail_hook_ar": "متى تصبح قناعتك فخاً؟",
    }, {}, Settings())
    assert package.pages == pages
    assert package.summary_ar == "\n\n".join(pages)
    assert package.conclusion_ar == footer
    assert package.creative_plan["ending_text_ar"] == footer
    assert package.hook.tts_text.startswith("عنوان المصدر...")
    assert "متى تصبح" not in package.hook.tts_text


@pytest.mark.parametrize("text", ["قوة عقلك تقاس بقدرتك على تغيير قناعاتك.", "اسحب لمعرفة سر فخ اليقين", "ما رأيك في هذا الموضوع؟"])
def test_footer_rejects_conclusion_swipe_and_generic_question(text):
    assert not normalize_footer(text)


def test_v2_action_rerender_uses_canonical_footer(tmp_path, monkeypatch):
    from arabic_video_brief.rerender import rerender_folder
    (tmp_path / "manifest.json").write_text(json.dumps({"source": "https://www.youtube.com/watch?v=abcdefghijk", "render": {"version": "v2"}}), encoding="utf-8")
    (tmp_path / "ending-text-ar.txt").write_text(ACTION, encoding="utf-8")
    (tmp_path / "ending-question-ar.txt").write_text(QUESTION, encoding="utf-8")
    (tmp_path / "summary-pages.json").write_text(json.dumps([{"text": "مثال."}] * 4), encoding="utf-8")
    monkeypatch.setattr("arabic_video_brief.v2.editorial.call_llm", no_model)
    monkeypatch.setattr("arabic_video_brief.rerender.download_youtube", lambda *a, **kw: {"video_path": str(tmp_path / "source.mp4")})
    captured = {}
    def render(**kwargs):
        captured.update(kwargs)
        return {"version": "v2"}
    monkeypatch.setattr("arabic_video_brief.v2.renderer.render_v2_video", render)
    rerender_folder(tmp_path, Settings())
    assert captured["editorial"].conclusion_ar == ACTION
    assert (tmp_path / "conclusion-ar.txt").read_text(encoding="utf-8").strip() == ACTION
    saved = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert saved["ending_text_ar"] == ACTION


def test_v1_preserves_authored_paragraph_boundary_even_when_midpoint_differs():
    p1 = " ".join(["شرح"] * 69) + " تفصيل."
    p2 = " ".join(["مثال"] * 4) + " نقطة. " + " ".join(["تفسير"] * 74) + " نتيجة."
    assert len(p1.split()) == 70 and len(p2.split()) == 80
    assert split_summary(p1 + "\n" + p2) == (p1, p2)


def test_all_analysis_providers_request_explanatory_pages_and_distinct_cover_hook():
    from arabic_video_brief import gemini, vyceai, seekai, apinex
    for module in (gemini, vyceai, seekai, apinex):
        assert "Every page advances understanding" in module.PROMPT
        assert "`pages`: exactly four strings" in module.PROMPT
        assert "`thumbnail_hook_ar`" in module.PROMPT
        assert "`ending_text_ar`" in module.PROMPT
        assert "golden rules" not in module.PROMPT
    assert gemini.ANALYSIS_SCHEMA["properties"]["pages"]["maxItems"] == 4
