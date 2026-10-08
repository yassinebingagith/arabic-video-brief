import pytest
from pathlib import Path

from arabic_video_brief.publisher.formatter import load_post_data


def test_load_post_data_stages_capcut_filename_and_sanitizes_strikethrough(tmp_path: Path) -> None:
    # Setup mock brief folder
    brief_mp4 = tmp_path / "brief.mp4"
    brief_mp4.write_bytes(b"dummy video content for testing")

    title_file = tmp_path / "post-title.txt"
    title_file.write_text("لماذا تجعلك الحرية الزائدة تعيساً؟", encoding="utf-8")

    desc_file = tmp_path / "post-description.txt"
    desc_content = """لماذا تجعلك الحرية الزائدة تعيساً؟ – د. باري شوارتز
مقدمة شيقة عن مفارقة الاختيار في العصر الحديث.

-جوهر القضية والحقائق الواقعية-
شرح تفصيلي حول الضغط النفسي لكثرة البدائل.

-الخلاصة والخطوات العملية القادمة-
تحديد الخيارات بوعي يحميك من التشتت.

🔔 تابعنا ليصلك يومياً ملخص لأهم المقاطع!
#بودكاست #وعي #فكر"""
    desc_file.write_text(desc_content, encoding="utf-8")

    original_size = brief_mp4.stat().st_size

    # Load post data
    post = load_post_data(tmp_path)

    # 1. Video path must be strictly the single CapCut file
    assert post.video_path.name.startswith("CapCut_1080p_")
    assert post.video_path.name.endswith(".mp4")
    assert post.video_path.is_file()
    assert post.video_path.stat().st_size == original_size

    # 2. Redundant brief.mp4 must be completely removed so only ONE video exists
    assert not (tmp_path / "brief.mp4").exists()

    # 2. YouTube description must have diamond headers instead of hyphen headers
    assert "◈ جوهر القضية والحقائق الواقعية ◈" in post.youtube_description
    assert "◈ الخلاصة والخطوات العملية القادمة ◈" in post.youtube_description
    assert "-جوهر القضية-" not in post.youtube_description

    # 3. TikTok & Meta caption must also have clean headers without hyphens
    assert "◈ جوهر القضية والحقائق الواقعية ◈" in post.tiktok_caption
    assert "◈ الخلاصة والخطوات العملية القادمة ◈" in post.meta_caption


def test_deepdive_sanitizer_removes_markdown_artifacts(tmp_path: Path) -> None:
    from arabic_video_brief.deepdive import sanitize_deepdive_text

    raw_ai_text = """# عنوان الموضوع الشامل مع المتحدث (Author)

مقدمة افتتاحية عميقة تتناول المأزق الفكري والسلوكي.

---

## المحور الأول: تفكيك النماذج الذهنية

1. **المفهوم الأول والخطوة الأساسية:**
   - شرح تفصيلي للنقطة الأولى مع استشهاد دقيق.
2. **المفهوم الثاني:**
   - شرح إضافي.

---

## الخاتمة وسؤال التأمل

هذه هي الخلاصة الفلسفية الشاملة للدرس.

**سؤال التأمل:** ما هو القرار الذي ستتخذه اليوم؟"""

    cleaned = sanitize_deepdive_text(raw_ai_text)

    # 1. No markdown headers
    assert not any(line.startswith("#") for line in cleaned.splitlines())
    assert "عنوان الموضوع الشامل" in cleaned.splitlines()[0]

    # 2. No horizontal dividers
    assert "---" not in cleaned
    assert "___" not in cleaned

    # 3. No bold asterisks
    assert "**" not in cleaned

    # 4. Diamond sections
    assert "◈ تفكيك النماذج الذهنية" in cleaned
    assert "##" not in cleaned

    # 5. Narrative transitions instead of raw numbers/bullets
    assert "أولاً، " in cleaned
    assert "ثانياً، " in cleaned
    assert "   - " not in cleaned

    # 6. Clean ending without robotic headers/labels
    assert "الخاتمة وسؤال التأمل" not in cleaned
    assert "سؤال التأمل:" not in cleaned
    assert "ما هو القرار الذي ستتخذه اليوم؟" in cleaned
    assert "شاركنا تجربتك في التعليقات" in cleaned


def test_load_post_data_sanitizes_deepdive_caption(tmp_path: Path) -> None:
    brief_mp4 = tmp_path / "brief.mp4"
    brief_mp4.write_bytes(b"dummy")

    title_file = tmp_path / "post-title.txt"
    title_file.write_text("العنوان التجريبي", encoding="utf-8")

    desc_file = tmp_path / "post-description.txt"
    desc_file.write_text("الوصف التجريبي", encoding="utf-8")

    # Write a deepdive summary containing raw markdown artifacts
    dd_file = tmp_path / "deep_dive_summary.txt"
    dd_file.write_text("""# التحليل المعرفي العميق

مقدمة عن الموضوع.

---

## المحور الأول: الجوهر العملي

1. **الخطوة الأولى:** شرح.

## الخاتمة وسؤال التأمل
الخلاصة.
**سؤال التأمل:** كيف ترى مستقبلك؟
""", encoding="utf-8")

    post = load_post_data(tmp_path)
    assert post.deep_dive_caption is not None
    assert "#" not in post.deep_dive_caption
    assert "---" not in post.deep_dive_caption
    assert "**" not in post.deep_dive_caption
    assert "◈ الجوهر العملي" in post.deep_dive_caption


def test_dispatcher_auto_queues_facebook_photo_post_when_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    brief_mp4 = tmp_path / "brief.mp4"
    brief_mp4.write_bytes(b"dummy")

    title_file = tmp_path / "post-title.txt"
    title_file.write_text("العنوان التجريبي", encoding="utf-8")

    desc_file = tmp_path / "post-description.txt"
    desc_file.write_text("الوصف التجريبي", encoding="utf-8")

    dd_file = tmp_path / "deep_dive_summary.txt"
    dd_file.write_text("ملخص معرفي شامل ومطول", encoding="utf-8")

    fb_cover = tmp_path / "cover_facebook_4x5.png"
    fb_cover.write_bytes(b"dummy_fb_cover")

    vert_cover = tmp_path / "cover_vertical_9x16.png"
    vert_cover.write_bytes(b"dummy_vert_cover")

    from arabic_video_brief.publisher import dispatcher

    captured_tasks = []

    # Mock sync_playwright to prevent opening browser in test
    class DummyContext:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    class DummyPlaywright:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr(dispatcher, "sync_playwright", lambda: DummyPlaywright())
    monkeypatch.setattr(dispatcher, "persistent_browser_context", lambda *a, **kw: DummyContext())

    def mock_publish(context, post_data, **kwargs):
        captured_tasks.append((kwargs.get("mode"), kwargs.get("target")))
        return {"status": "success", "mode": "published"}

    monkeypatch.setattr(dispatcher, "publish_to_youtube", lambda *a, **kw: {"status": "success", "mode": "published"})
    monkeypatch.setattr(dispatcher, "publish_to_tiktok", lambda *a, **kw: {"status": "success", "mode": "published"})
    monkeypatch.setattr(dispatcher, "publish_to_meta", lambda ctx, post, **kw: mock_publish(ctx, post, **kw))
    monkeypatch.setattr(dispatcher.time, "sleep", lambda *a: None)

    res = dispatcher.publish_folder(tmp_path, platform="all")

    # Meta should have been called TWICE: once for video (Reel), once for photo (Facebook post)
    assert ("video", "meta") in captured_tasks
    assert ("photo", "facebook") in captured_tasks
    assert "meta_video" in res["results"]
    assert "meta_photo" in res["results"]


