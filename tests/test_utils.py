from pathlib import Path

from arabic_video_brief.utils import (
    deduplicate_sources,
    redact,
    slugify,
    split_summary,
    word_count,
    youtube_video_id,
)


def test_youtube_video_id_common_shapes() -> None:
    assert youtube_video_id("https://www.youtube.com/watch?v=abcdefghijk") == "abcdefghijk"
    assert youtube_video_id("https://youtu.be/abcdefghijk?t=12") == "abcdefghijk"
    assert youtube_video_id("https://youtube.com/shorts/abcdefghijk") == "abcdefghijk"
    assert youtube_video_id("https://example.com/watch?v=abcdefghijk") is None


def test_batch_deduplicates_equivalent_youtube_urls(tmp_path: Path) -> None:
    local = tmp_path / "clip.mp4"
    local.touch()
    values = [
        "https://youtu.be/abcdefghijk",
        "https://www.youtube.com/watch?v=abcdefghijk",
        str(local),
        str(local),
    ]
    assert deduplicate_sources(values) == [values[0], str(local)]


def test_summary_split_prefers_sentence_boundary() -> None:
    text = "هذه جملة أولى قصيرة توضح الفكرة الأساسية بوضوح. وهذه جملة ثانية تضيف الدليل المهم ثم تقدم الخلاصة النهائية المفيدة للقارئ."
    first, second = split_summary(text)
    assert first.endswith(".")
    assert first and second
    assert word_count(first) + word_count(second) == word_count(text)


def test_summary_split_keeps_each_page_between_70_and_80_words() -> None:
    words = [f"كلمة{i}" for i in range(150)]
    words[74] += "."
    first, second = split_summary(" ".join(words))
    assert 70 <= word_count(first) <= 80
    assert 70 <= word_count(second) <= 80
    assert first.endswith(".")


def test_slug_and_secret_redaction() -> None:
    assert slugify("عنوان: فيديو / رائع") == "عنوان-فيديو-رائع"
    secret = "AIza-not-a-real-key"
    assert secret not in redact(f"request failed: {secret}", [secret])


def test_generate_post_title_and_description_universality() -> None:
    from arabic_video_brief.pipeline import generate_post_description, generate_post_title

    title = generate_post_title({"title": "How to manage stress?"}, title_hint="كيف تدير التوتر بنجاح؟ #shorts")
    assert "#shorts" not in title
    assert "#short" not in title
    assert title.endswith("؟")

    desc = generate_post_description(
        {"title": "إدارة التوتر", "channel": "قناة المعرفة", "tags": ["stress", "psychology", "shorts"]},
        "الفقرة الأولى تشرح أسباب التوتر وتأثيره على التفكير. والفقرة الثانية تقدم آليات عملية فعالة للتعامل مع الضغوط اليومية.",
    )
    assert "#shorts" not in desc
    assert "#short" not in desc
    assert "#يوتيوب_عربي" not in desc
    assert "🔔 تابعنا ليصلك يومياً ملخص لأهم المقاطع والبودكاست الفكرية والعلمية!" in desc
    assert "#بودكاست" in desc
    assert "#تطوير_الذات" in desc
    assert len(desc) <= 2000
