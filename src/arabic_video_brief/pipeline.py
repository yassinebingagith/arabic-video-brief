from __future__ import annotations

import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from .config import Settings
from .gemini import analyze_video
from .seekai import analyze_video_seekai
from .vyceai import analyze_video_vyceai
from .media import download_youtube, infer_category, render_video
from .utils import deduplicate_sources, redact, slugify, source_hash, split_summary, write_json, youtube_video_id
from .youtube import fetch_video_details


def generate_post_title(metadata: dict[str, Any], title_hint: str = "") -> str:
    raw_title = str(metadata.get("title") or "").strip()
    orig_title = str(metadata.get("original_title") or "").strip()

    def _strip_shorts(s: str) -> str:
        s = re.sub(r"#\b(?:shorts?|يوتيوب_عربي)\b", "", s, flags=re.IGNORECASE).strip()
        return re.sub(r"\s+", " ", s).strip()

    # Rule: If the video was originally titled in Arabic, KEEP IT directly!
    # Strip any trailing/leading #shorts or platform tags, but preserve the exact Arabic title.
    target_orig_ar = orig_title if re.search(r"[\u0600-\u06FF]", orig_title) else (raw_title if re.search(r"[\u0600-\u06FF]", raw_title) else "")
    if target_orig_ar:
        clean = _strip_shorts(target_orig_ar)
        return clean

    is_original_question = raw_title.endswith("?") or "?" in raw_title

    # If title_hint contains Arabic, prioritize using it
    if title_hint and re.search(r"[\u0600-\u06FF]", title_hint):
        clean = _strip_shorts(title_hint)
        is_hint_question = bool(re.search(r"[?؟]\s*$", clean)) or clean.startswith(
            ("هل ", "كيف ", "لماذا ", "ما هو ", "ما هي ", "ماذا ", "من هو ", "أين ", "متى ")
        )
        clean = re.sub(r"[.!؟?\-_|]+$", "", clean).strip()
        if is_original_question or is_hint_question:
            clean = f"{clean}؟"
        return clean

    fallback = _strip_shorts(raw_title) or "مقطع مميز"
    return fallback


def generate_post_description(
    metadata: dict[str, Any],
    summary_text: str,
    narrative_desc: str = "",
) -> str:
    category = infer_category(metadata, summary_text)
    tags = metadata.get("tags") or []
    hashtags_list = ["#بودكاست", "#تطوير_الذات", "#فكر", "#ثقافة", "#معرفة", "#وعي"]
    for t in tags[:4]:
        clean_t = re.sub(r"[^\w\u0600-\u06FF]+", "", str(t))
        clean_t_lower = clean_t.lower()
        if clean_t and clean_t_lower not in ("shorts", "short", "يوتيوب_عربي", "youtube") and f"#{clean_t}" not in hashtags_list:
            hashtags_list.append(f"#{clean_t}")
    hashtags_str = " ".join(hashtags_list[:8])
    cta_str = "🔔 تابعنا ليصلك يومياً ملخص لأهم المقاطع والبودكاست الفكرية والعلمية!"

    channel = str(metadata.get("channel") or metadata.get("uploader") or "يوتيوب").strip()

    if narrative_desc and len(narrative_desc.strip()) >= 600:
        desc = narrative_desc.strip()
        # Remove any unwanted bullet lists or old headers if present
        desc = re.sub(r"^فيديوهات وجب مشاهدتها.*?\n+", "", desc, flags=re.MULTILINE)
        desc = re.sub(r"📌 محاور وفصول الحلقة:.*?(?=\n\n|\Z)", "", desc, flags=re.DOTALL)
        desc = re.sub(r"💡 أهم الأفكار والنقاط الجوهرية:.*?(?=\n\n|\Z)", "", desc, flags=re.DOTALL)
        desc = re.sub(r"🛠️ خطوات وتوصيات عملية للتطبيق:.*?(?=\n\n|\Z)", "", desc, flags=re.DOTALL)
        desc = re.sub(r"🔗 لمشاهدة الحلقة الكاملة:.*?(?=\n\n|\Z)", "", desc, flags=re.DOTALL)
        # Robust line-by-line removal of any channel subscription or bell prompts
        filtered_lines = [
            ln for ln in desc.splitlines()
            if not any(marker in ln for marker in ("اشترك في القناة", "اشتركوا في القناة", "اشتركوا", "للاشتراك", "زر الجرس", "جرس التنبيهات", "لا تنس الاشتراك", "إذا كان هذا المحتوى", "تابعنا", "🔔"))
        ]
        desc = "\n".join(filtered_lines).strip()
        desc = re.sub(r"(?:\s*#[\w\u0600-\u06FF]+)+$", "", desc).strip()
        desc = re.sub(r"\n{3,}", "\n\n", desc).strip()

        # Sanitize any literal placeholder in line 1
        lines = desc.splitlines()
        if lines and ("عنوان الموضوع" in lines[0] or "عنوان المحور" in lines[0]):
            clean_title = metadata.get("post_title_ar") or generate_post_title(metadata)
            speaker_suffix = ""
            if "–" in lines[0]:
                speaker_suffix = lines[0].split("–", 1)[1].strip()
            elif "-" in lines[0]:
                speaker_suffix = lines[0].split("-", 1)[1].strip()
            if not speaker_suffix:
                speaker_suffix = channel
            lines[0] = f"{clean_title} – {speaker_suffix}"
            desc = "\n".join(lines).strip()
    else:
        # Construct narrative article summary with sections -عنوان المحور-
        paragraphs = [p.strip() for p in summary_text.strip().split("\n") if p.strip()]
        p1 = paragraphs[0] if paragraphs else summary_text
        p2 = paragraphs[1] if len(paragraphs) > 1 else ""

        title = str(metadata.get("title") or "الموضوع").strip()
        clean_title = metadata.get("post_title_ar") or generate_post_title(metadata)
        desc = f"""{clean_title} – {channel}
في عالم يتغير بسرعة مذهلة، يغفل الكثيرون عن الأسباب الحقيقية وراء التحديات اليومية التي تواجهنا، سواء في العمل أو الحياة الشخصية. الفهم الحقيقي للواقع يبدأ بالنظر إلى ما وراء الأفكار الشائعة، واكتشاف الآليات الفعلية التي تؤثر في قراراتنا اليومية ومستقبلنا العملي.

-جوهر القضية والحقائق الواقعية-
{p1}

-التأثير المباشر على حياتنا اليومية-
{p2 if p2 else 'التعامل مع هذه التغيرات يتطلب نظرة واقعية؛ فمحاولة الاستمرار بنفس الأساليب القديمة لم تعد مجدية. من الضروري إدراك الفارق بين الأوهام المريحة والخطوات الحقيقية التي تصنع فارقاً ملموساً في الاستقرار والتطور.'}

-الخلاصة والخطوات العملية القادمة-
النجاح والاستقرار اليوم لا يتحققان عبر التمنيات أو الحلول السريعة السطحية، بل من خلال تطوير وعي ذاتي مستمر والتركيز على المهارات التي لا يمكن تعويضها. اجعل من هذه المعرفة نقطة انطلاق لإعادة تقييم خياراتك اليومية، وحماية طاقتك، وتوجيه جهودك نحو ما يبني مستقبلاً آمناً ومتوازناً.""".strip()

    # If description is below preferred target (1,750 chars), add integrative synthesis subsection
    if len(f"{desc}\n\n{cta_str}\n\n{hashtags_str}".strip()) < 1750:
        extra_takeaways = (
            "\n\n-الاستثمار في الوعي وبناء القيمة المستدامة-\n"
            "تؤكد هذه الحقائق أن حماية مستقبلك وتحقيق التوازن الحقيقي لا يعتمدان على الصدفة أو الحلول المؤقتة، "
            "بل على فهم دقيق للواقع والالتزام بتطوير مهارات عملية واعية تتوافق مع التحديات المعاصرة. إن الاستثمار المستمر "
            "في بناء قدراتك الإنسانية والمهنية هو الضمان الحقيقي للحفاظ على تميزك وصناعة أثر إيجابي طويل الأمد."
        )
        if len(f"{desc}{extra_takeaways}\n\n{cta_str}\n\n{hashtags_str}".strip()) <= 1980:
            desc = f"{desc}{extra_takeaways}"

    # Compose full text with CTA and hashtags
    full_text = f"{desc}\n\n{cta_str}\n\n{hashtags_str}".strip()

    # Enforce strictly: Target 1,750 - 1,950 characters, NEVER exceed 2,000 characters
    if len(full_text) > 2000:
        budget = 2000 - len(cta_str) - len(hashtags_str) - 20
        trimmed_desc = desc[:budget].rstrip()
        last_break = max(trimmed_desc.rfind("."), trimmed_desc.rfind("\n"))
        if last_break > budget // 2:
            trimmed_desc = trimmed_desc[:last_break].rstrip()
        full_text = f"{trimmed_desc}\n\n{cta_str}\n\n{hashtags_str}".strip()

    return full_text


TRANSIENT_MARKERS = ("timeout", "temporarily", "rate limit", "429", "500", "502", "503", "504", "bad gateway", "internal server error", "connection reset", "words; expected")


def _retry_delay(error_text: str, attempt: int) -> float:
    """Honor provider retry hints while keeping retries bounded."""
    matches = (
        re.search(r"retry in\s+([0-9.]+)s", error_text, flags=re.IGNORECASE),
        re.search(r"retryDelay['\"\s:]+([0-9.]+)s", error_text, flags=re.IGNORECASE),
    )
    for match in matches:
        if match:
            return min(float(match.group(1)) + 1.0, 90.0)
    return float(2 ** attempt)


def _with_retries(function: Any, attempts: int = 3) -> Any:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return function()
        except Exception as error:
            last_error = error
            text = str(error).lower()
            if attempt >= attempts - 1 or not any(marker in text for marker in TRANSIENT_MARKERS):
                raise
            time.sleep(_retry_delay(str(error), attempt))
    raise RuntimeError("Retry loop ended unexpectedly") from last_error


def process_source(
    source: str,
    output_root: Path,
    settings: Settings,
    keep_work: bool = False,
    analysis_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    temp_context: tempfile.TemporaryDirectory[str] | None = None
    if keep_work:
        work_parent = output_root / "work"
        work_parent.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(prefix="avbrief-", dir=work_parent))
    else:
        temp_context = tempfile.TemporaryDirectory(prefix="avbrief-")
        work_dir = Path(temp_context.name)
    try:
        video_id = youtube_video_id(source)
        if video_id:
            downloaded = _with_retries(lambda: download_youtube(source, work_dir))
            local_video = Path(downloaded["video_path"])
            thumbnail = Path(downloaded["thumbnail_path"]) if downloaded.get("thumbnail_path") else None
            title = str(downloaded.get("title") or "YouTube video")
            identifier = str(downloaded.get("id") or video_id)
            metadata = {key: value for key, value in downloaded.items() if key not in {"video_path", "thumbnail_path"}}

            if settings.youtube_api_key:
                details = fetch_video_details(video_id, settings.youtube_api_key)
                if details and details.get("title"):
                    metadata["title"] = details["title"]
                    metadata["original_title"] = details.get("original_title")
                    title = details["title"]
                    if details.get("channel"):
                        metadata["channel"] = details["channel"]
                    if details.get("description"):
                        metadata["description"] = details["description"]
        else:
            local_video = Path(source).expanduser().resolve()
            if not local_video.is_file():
                raise ValueError("Source must be a public YouTube URL or an existing local video file")
            title = local_video.stem
            identifier = source_hash(str(local_video))
            thumbnail = next((path for path in (local_video.with_suffix(".jpg"), local_video.with_suffix(".png"), local_video.with_suffix(".webp")) if path.exists()), None)
            metadata = {"title": title, "id": identifier, "local_path": str(local_video)}

        analysis = analysis_override
        actual_model = (
            settings.apinex_model
            if settings.llm_provider == "apinex"
            else (settings.vyceai_model if settings.llm_provider == "vyceai" else ("antigravity-brainstorm" if analysis_override else settings.gemini_model))
        )
        if analysis is None and settings.llm_provider == "apinex":
            from .apinex import analyze_video_apinex
            try:
                analysis = _with_retries(lambda: analyze_video_apinex(source, local_video, settings, metadata=metadata), attempts=2)
                actual_model = settings.apinex_model
            except Exception as apx_err:
                print(f"[Warning] APInex provider error ({apx_err}); falling back to Gemini.", flush=True)
                analysis = None

        if analysis is None and settings.llm_provider == "vyceai":
            try:
                analysis = _with_retries(lambda: analyze_video_vyceai(source, local_video, settings, metadata=metadata), attempts=2)
                actual_model = settings.vyceai_model
            except Exception as vyce_err:
                print(f"[Warning] VyceAI provider error ({vyce_err}); falling back to Gemini.", flush=True)
                analysis = None

        if analysis is None and settings.llm_provider == "seekai":
            try:
                analysis = _with_retries(lambda: analyze_video_seekai(source, local_video, settings, metadata=metadata), attempts=1)
                actual_model = settings.seekai_model
            except Exception as seek_err:
                print(f"[Warning] SeekAI provider error ({seek_err}); falling back to Gemini.", flush=True)
                analysis = None

        if analysis is None:
            analysis = _with_retries(lambda: analyze_video(source, local_video, settings, metadata=metadata))
            actual_model = settings.gemini_model

        page_one, page_two = split_summary(
            analysis["summary_ar"], settings.page_min_words, settings.page_max_words
        )
        selected = {
            "start_seconds": 0.0,
            "end_seconds": min(15.0, float(metadata.get("duration") or 15.0)),
            "reason": "First fifteen seconds requested by user",
            "focal_x": 0.5,
            "focal_y": 0.5,
        }
        item_dir = output_root / f"{slugify(title)}-{identifier}"
        item_dir.mkdir(parents=True, exist_ok=True)
        final_path = item_dir / "brief.mp4"
        transcript_path = item_dir / "transcript.json"
        summary_path = item_dir / "summary-ar.txt"
        manifest_path = item_dir / "manifest.json"
        write_json(transcript_path, {"source_language": analysis.get("source_language"), "segments": analysis.get("transcript", [])})
        summary_path.write_text(analysis["summary_ar"].strip() + "\n", encoding="utf-8")
        post_title = generate_post_title(metadata, analysis.get("post_title_ar") or analysis.get("summary_ar", ""))
        render_details = render_video(
            local_video, thumbnail, page_one, page_two, selected, final_path, settings, metadata=metadata, post_title=post_title
        )
        post_description = generate_post_description(metadata, analysis["summary_ar"], analysis.get("post_description", ""))
        post_title_path = item_dir / "post-title.txt"
        post_desc_path = item_dir / "post-description.txt"

        post_title_path.write_text(post_title.strip() + "\n", encoding="utf-8")
        post_desc_path.write_text(post_description.strip() + "\n", encoding="utf-8")

        manifest = {
            "status": "success",
            "source": source,
            "metadata": metadata,
            "model": actual_model,
            "post_title": post_title,
            "post_description": post_description,
            "summary_words": len(analysis["summary_ar"].split()),
            "pages_ar": [page_one, page_two],
            "clip_candidates": [],
            "selected_clip": selected,
            "render": render_details,
            "files": {
                "video": str(final_path),
                "transcript": str(transcript_path),
                "summary": str(summary_path),
                "post_title": str(post_title_path),
                "post_description": str(post_desc_path),
                "manifest": str(manifest_path),
            },
        }
        write_json(manifest_path, manifest)
        return manifest
    finally:
        if temp_context is not None:
            temp_context.cleanup()


def run_batch(
    sources: list[str],
    output_root: Path,
    settings: Settings,
    keep_work: bool = False,
    analysis_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    unique_sources = deduplicate_sources(sources)
    results: list[dict[str, Any]] = []
    for source in unique_sources:
        try:
            results.append(process_source(source, output_root, settings, keep_work=keep_work, analysis_override=analysis_override))
        except Exception as error:
            results.append({
                "status": "failed",
                "source": source,
                "error": redact(str(error), [settings.gemini_api_key, settings.youtube_api_key, settings.seekai_api_key]),
            })
    report = {
        "status": "complete",
        "requested": len(sources),
        "unique": len(unique_sources),
        "succeeded": sum(item["status"] == "success" for item in results),
        "failed": sum(item["status"] == "failed" for item in results),
        "results": results,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    write_json(output_root / "job-report.json", report)
    return report
