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

    # Rule: If the video was originally titled in Arabic, KEEP IT directly (unless it contains English words and a pure Arabic hint is supplied)!
    # Strip any trailing/leading #shorts or platform tags, but preserve the exact Arabic title.
    target_orig_ar = orig_title if re.search(r"[\u0600-\u06FF]", orig_title) else (raw_title if re.search(r"[\u0600-\u06FF]", raw_title) else "")
    if target_orig_ar and not (re.search(r"[a-zA-Z]{2,}", target_orig_ar) and title_hint and re.search(r"[\u0600-\u06FF]", title_hint)):
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

    # 1. Dynamic Niche-Specific Hashtags
    niche_map = {
        "علم النفس": ["#علم_النفس", "#الصحة_النفسية", "#سلوك_إنساني"],
        "فلسفة وفكر": ["#فلسفة", "#فكر_معاصر", "#تأملات"],
        "تكنولوجيا وذكاء اصطناعي": ["#ذكاء_اصطناعي", "#تكنولوجيا", "#تقنية"],
        "تاريخ وحضارة": ["#تاريخ", "#حضارة", "#قصص_تاريخية"],
        "علاقات وتواصل": ["#علاقات", "#ذكاء_عاطفي", "#تواصل"],
        "تطوير الذات وإنتاجية": ["#تطوير_الذات", "#إنتاجية", "#تحفيز"],
        "أعمال ومال": ["#ريادة_أعمال", "#اقتصاد", "#مال_وأعمال"],
        "علوم وفيزياء": ["#علوم", "#فيزياء", "#معرفة_علمية"],
    }
    niche_tags = list(niche_map.get(category, ["#فكر", "#معرفة", "#وعي"]))

    # Incorporate clean Arabic tags from YouTube metadata if relevant
    for t in tags[:5]:
        clean_t = re.sub(r"[^\w\u0600-\u06FF]+", "", str(t))
        clean_t_lower = clean_t.lower()
        if clean_t and clean_t_lower not in ("shorts", "short", "يوتيوب_عربي", "youtube", "podcast", "video") and f"#{clean_t}" not in niche_tags:
            niche_tags.append(f"#{clean_t}")

    # Rotating pool of broad Arabic hashtags
    core_pool = [
        ["#بودكاست", "#وعي", "#فكر"],
        ["#معرفة", "#ثقافة", "#إلهام"],
        ["#بودكاست", "#تطوير_الذات", "#معرفة"],
        ["#فكر", "#ثقافة", "#وعي"],
    ]

    seed_key = str(metadata.get("title") or metadata.get("id") or "seed")
    rotation_idx = sum(ord(c) for c in seed_key) % len(core_pool)
    selected_core = core_pool[rotation_idx]

    combined_hashtags = []
    for h in niche_tags[:4] + selected_core:
        if h not in combined_hashtags:
            combined_hashtags.append(h)
    hashtags_str = " ".join(combined_hashtags[:7])

    # Rotating subscription CTA pool
    cta_pool = [
        "🔔 تابعنا ليصلك يومياً ملخص لأهم المقاطع والبودكاست الفكرية والعلمية!",
        "✨ تابع الصفحة يومياً لاكتشاف أعمق الأفكار والملخصات المعرفية المركزة!",
        "💡 للمزيد من الرؤى الفكرية والملخصات اليومية الملهمة، انضم إلى مجتمعنا وتابع الصفحة!",
    ]
    cta_str = cta_pool[rotation_idx % len(cta_pool)]

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

        # Sanitize hyphen headers like -عنوان المحور- to eliminate YouTube strikethrough glitch
        clean_lines = []
        for ln in desc.splitlines():
            trimmed = ln.strip()
            if (
                (trimmed.startswith(("-", "–", "—")) and trimmed.endswith(("-", "–", "—")))
                and len(trimmed) > 2
                and not trimmed.startswith("---")
            ):
                inner = trimmed.strip("-–— ").strip()
                clean_lines.append(f"◈ {inner} ◈")
            else:
                clean_lines.append(ln)
        desc = "\n".join(clean_lines).strip()
    else:
        # Construct narrative article summary with diamond bullet sections ◈ عنوان المحور ◈
        paragraphs = [p.strip() for p in summary_text.strip().split("\n") if p.strip()]
        p1 = paragraphs[0] if paragraphs else summary_text
        p2 = paragraphs[1] if len(paragraphs) > 1 else ""

        title = str(metadata.get("title") or "الموضوع").strip()
        clean_title = metadata.get("post_title_ar") or generate_post_title(metadata)
        desc = f"""{clean_title} – {channel}
في عالم يتغير بسرعة مذهلة، يغفل الكثيرون عن الأسباب الحقيقية وراء التحديات اليومية التي تواجهنا، سواء في العمل أو الحياة الشخصية. الفهم الحقيقي للواقع يبدأ بالنظر إلى ما وراء الأفكار الشائعة، واكتشاف الآليات الفعلية التي تؤثر في قراراتنا اليومية ومستقبلنا العملي.

◈ جوهر القضية والحقائق الواقعية ◈
{p1}

◈ التأثير المباشر على حياتنا اليومية ◈
{p2 if p2 else 'التعامل مع هذه التغيرات يتطلب نظرة واقعية؛ فمحاولة الاستمرار بنفس الأساليب القديمة لم تعد مجدية. من الضروري إدراك الفارق بين الأوهام المريحة والخطوات الحقيقية التي تصنع فارقاً ملموساً في الاستقرار والتطور.'}

◈ الخلاصة والخطوات العملية القادمة ◈
النجاح والاستقرار اليوم لا يتحققان عبر التمنيات أو الحلول السريعة السطحية، بل من خلال تطوير وعي ذاتي مستمر والتركيز على المهارات التي لا يمكن تعويضها. اجعل من هذه المعرفة نقطة انطلاق لإعادة تقييم خياراتك اليومية، وحماية طاقتك، وتوجيه جهودك نحو ما يبني مستقبلاً آمناً ومتوازناً.""".strip()

    # If description is below preferred target (1,750 chars), add integrative synthesis subsection
    if len(f"{desc}\n\n{cta_str}\n\n{hashtags_str}".strip()) < 1750:
        extra_takeaways = (
            "\n\n◈ الاستثمار في الوعي وبناء القيمة المستدامة ◈\n"
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


TRANSIENT_MARKERS = ("timeout", "temporarily", "rate limit", "429", "500", "502", "503", "504", "bad gateway", "internal server error", "connection reset", "words; expected", "ffmpeg", "exit code", "download")


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
    generate_thumbnails: bool | str = "none",
    generate_deepdive: bool = False,
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

        analysis["summary_ar"] = str(analysis.get("summary_ar", "")).replace("{", "").replace("}", "")
        page_one, page_two = split_summary(
            analysis["summary_ar"], settings.page_min_words, settings.page_max_words
        )
        selected = {
            "start_seconds": 0.0,
            "end_seconds": min(27.5, float(metadata.get("duration") or 27.5)),
            "reason": "Opening source footage for the 30-second reading section",
            "focal_x": 0.5,
            "focal_y": 0.5,
        }
        item_dir = output_root / f"{slugify(title)}-{identifier}"
        item_dir.mkdir(parents=True, exist_ok=True)
        temp_render_path = item_dir / "brief.mp4"
        transcript_path = item_dir / "transcript.json"
        summary_path = item_dir / "summary-ar.txt"
        manifest_path = item_dir / "manifest.json"
        write_json(transcript_path, {"source_language": analysis.get("source_language"), "segments": analysis.get("transcript", [])})
        plain_summary = re.sub(r"</?hl>", "", analysis["summary_ar"]).strip()
        summary_path.write_text(plain_summary + "\n", encoding="utf-8")
        post_title = generate_post_title(metadata, analysis.get("post_title_ar") or plain_summary)
        from .ending import resolve_ending_question
        ending_question = resolve_ending_question(analysis, metadata, plain_summary, settings)
        (item_dir / "ending-question-ar.txt").write_text(ending_question + "\n", encoding="utf-8")
        render_details = render_video(
            local_video, thumbnail, page_one, page_two, selected, temp_render_path, settings, metadata=metadata, post_title=post_title, ending_question=ending_question
        )

        # Anti-Bot Authentic CapCut Filename Staging:
        import datetime
        import shutil
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        raw_slug = slugify(post_title)
        if not raw_slug or len(raw_slug) < 3:
            raw_slug = slugify(title)
        short_slug = raw_slug[:45].rstrip("-_")
        capcut_name = f"CapCut_1080p_{date_str}_{short_slug}.mp4"
        staged_video_path = item_dir / capcut_name

        if temp_render_path.is_file():
            try:
                temp_render_path.rename(staged_video_path)
            except Exception:
                shutil.copyfile(str(temp_render_path), str(staged_video_path))
                temp_render_path.unlink(missing_ok=True)
            if temp_render_path.is_file():
                temp_render_path.unlink(missing_ok=True)
        final_path = staged_video_path
        post_description = generate_post_description(metadata, plain_summary, analysis.get("post_description", ""))
        post_title_path = item_dir / "post-title.txt"
        post_desc_path = item_dir / "post-description.txt"

        post_title_path.write_text(post_title.strip() + "\n", encoding="utf-8")
        post_desc_path.write_text(post_description.strip() + "\n", encoding="utf-8")

        # Preserve source thumbnail in output directory
        source_thumb_dest = None
        if thumbnail and thumbnail.is_file():
            source_thumb_dest = item_dir / f"source_thumbnail{thumbnail.suffix.lower()}"
            if not source_thumb_dest.exists() or source_thumb_dest.resolve() != thumbnail.resolve():
                try:
                    shutil.copyfile(str(thumbnail), str(source_thumb_dest))
                except Exception:
                    pass

        # Optional high-CTR thumbnail & photo prompts generation
        fb_prompt_p: str | None = None
        vert_prompt_p: str | None = None
        is_thumb_enabled = generate_thumbnails and str(generate_thumbnails).lower() not in ("none", "false", "0")
        if is_thumb_enabled:
            try:
                from .thumbnail import process_folder_thumbnails
                use_kieai = str(generate_thumbnails).lower() == "kieai"
                fb_p, vert_p, _ = process_folder_thumbnails(
                    item_dir,
                    manifest_data={"metadata": metadata, "source": source},
                    creative_plan=analysis,
                    generate_kieai=use_kieai,
                    include_facebook=generate_deepdive,
                )
                fb_prompt_p = str(fb_p) if fb_p else None
                vert_prompt_p = str(vert_p)
            except Exception as exc:
                print(f"[Warning] Failed to generate thumbnails: {exc}", flush=True)

        # Optional exhaustive Deep-Dive Educational Synthesis (ملخص معرفي مطوّل وشامل)
        deepdive_p: str | None = None
        if generate_deepdive:
            try:
                from .deepdive import generate_deepdive_summary
                dd_file = generate_deepdive_summary(
                    output_dir=item_dir,
                    transcript_source=analysis.get("transcript") or transcript_path,
                    settings=settings,
                    metadata=metadata,
                    override_text=analysis_override.get("deep_dive_summary") if analysis_override else None,
                )
                deepdive_p = str(dd_file)
            except Exception as exc:
                print(f"[Warning] Failed to generate deep-dive synthesis: {exc}", flush=True)

        manifest = {
            "status": "success",
            "source": source,
            "metadata": metadata,
            "model": actual_model,
            "post_title": post_title,
            "post_description": post_description,
            "summary_words": len(analysis["summary_ar"].split()),
            "pages_ar": [page_one, page_two],
            "thumbnail_hook_ar": analysis.get("thumbnail_hook_ar", ""),
            "ending_question_ar": ending_question,
            "clip_candidates": [],
            "selected_clip": selected,
            "render": render_details,
            "files": {
                "ending_question_ar": str(item_dir / "ending-question-ar.txt"),
                "video": str(final_path),
                "transcript": str(transcript_path),
                "summary": str(summary_path),
                "post_title": str(post_title_path),
                "post_description": str(post_desc_path),
                "deep_dive_summary": deepdive_p,
                "thumbnail_prompt_fb": fb_prompt_p,
                "thumbnail_prompt_vertical": vert_prompt_p,
                "source_thumbnail": str(source_thumb_dest) if source_thumb_dest and source_thumb_dest.exists() else None,
                "manifest": str(manifest_path),
            },
        }
        from .whiteboard import finalize_package
        finalize_package(final_path)
        manifest["files"]["render_project"] = str(item_dir / "render-project")
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
    generate_thumbnails: bool | str = "none",
    generate_deepdive: bool = False,
) -> dict[str, Any]:
    unique_sources = deduplicate_sources(sources)
    results: list[dict[str, Any]] = []
    for source in unique_sources:
        try:
            results.append(
                process_source(
                    source,
                    output_root,
                    settings,
                    keep_work=keep_work,
                    analysis_override=analysis_override,
                    generate_thumbnails=generate_thumbnails,
                    generate_deepdive=generate_deepdive,
                )
            )
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
