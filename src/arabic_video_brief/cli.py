from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT, get_settings
from .media import find_ffmpeg
from .pipeline import run_batch
from .utils import redact
from .youtube import search_videos


if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


def _print_json(data: object) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))



def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="avbrief", description="Create Arabic vertical video briefs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Find YouTube candidates")
    search.add_argument("--query", default="")
    search.add_argument("--mode", choices=["trending", "recent", "popular", "classic", "rated", "relevant"], default="relevant")
    search.add_argument("--region", default="US")
    search.add_argument("--language", default="ar")
    search.add_argument("--duration", choices=["any", "short", "medium", "long"], default="any")
    search.add_argument("--limit", type=int, default=5)

    run = subparsers.add_parser("run", help="Process one or more sources sequentially")
    run.add_argument("--source", action="append", default=[])
    run.add_argument("--job", type=Path)
    run.add_argument("--output", type=Path)
    run.add_argument("--keep-work", action="store_true")
    run.add_argument("--provider", choices=["vyceai", "seekai", "gemini", "apinex", "brainstorm"], help="LLM provider for analysis")
    run.add_argument("--analysis", type=Path, help="Path to pre-computed analysis JSON file (Antigravity Brainstorm mode)")
    run.add_argument("--version", choices=["v1", "v2"], help="Video version (v1: 38s two-page, v2: 42.2s title hook + four pages; both end with a question). V3 manual packs are authored through the skill, not this video command.")
    run.add_argument("--model", type=str, help="LLM model name override (e.g. claude-sonnet-4-6, gpt-5.6-new)")
    run.add_argument("--no-tts", action="store_true", help="Render visual-only hook without ElevenLabs narration in V2")
    run.add_argument("--force", action="store_true", help="Force overwrite existing output folder")
    run.add_argument("--thumbnails", nargs="?", const="manual", default=None, choices=["none", "manual", "kieai"], help="Required choice in non-interactive runs: none, manual prompts, or KIE.ai generation")
    deepdive_choice = run.add_mutually_exclusive_group()
    deepdive_choice.add_argument("--deepdive", dest="deepdive", action="store_true", help="Generate deep_dive_summary.txt")
    deepdive_choice.add_argument("--no-deepdive", dest="deepdive", action="store_false", help="Explicitly decline the deep-dive summary")
    run.set_defaults(deepdive=None)

    subparsers.add_parser("doctor", help="Check local dependencies and configuration")

    login = subparsers.add_parser("login", help="Open visible browser to log into social platforms once")
    login.add_argument("--platform", choices=["all", "youtube", "tiktok", "meta"], default="all")

    post = subparsers.add_parser("post", help="Publish a generated video brief folder")
    post.add_argument("--folder", type=Path, required=True, help="Path to video folder (e.g. outputs/.../<folder>)")
    post.add_argument("--platform", default="all", help="Platform(s) to publish to: all, youtube, tiktok, meta, or comma-separated list (e.g. youtube,tiktok)")
    post.add_argument("--mode", choices=["video", "photo"], default="video", help="Post type for Meta: video Reel or photo post")
    post.add_argument("--target", choices=["instagram", "facebook", "both"], default=None, help="Explicit destination for Meta (defaults: instagram for reels, facebook for photo posts, both for Facebook+Instagram)")
    post.add_argument("--schedule", help="Optional schedule date/time, e.g. 'YYYY-MM-DD HH:MM'")
    post.add_argument("--draft", action="store_true", help="Save as unlisted/draft instead of publishing immediately")
    post.add_argument("--force", action="store_true", help="Re-post even if already recorded as published")
    post.add_argument("--headless", action="store_true", help="Run browser in background (default is visible/headful)")

    rerender = subparsers.add_parser("rerender", help="Re-render an existing video brief folder without repeating analysis")
    rerender.add_argument("--folder", type=Path, required=True, help="Path to video folder (e.g. outputs/.../<folder>)")

    thumb = subparsers.add_parser("thumbnail", help="Generate high-CTR thumbnail & photo prompts (4:5 FB and 9:16 vertical)")
    thumb.add_argument("--folder", type=Path, required=True, help="Path to video folder (e.g. outputs/.../<folder>)")
    thumb.add_argument("--style", type=str, help="Optional visual style override (cinematic, noir, futuristic, minimalist, split, abstract, high_energy, retro, 3d, hyper_real)")
    thumb.add_argument("--archetype", choices=["portrait", "comparison", "artifact", "scene", "metaphor"], help="Optional focal archetype override")
    thumb.add_argument("--kieai", action="store_true", help="Automatically generate images using KIE.ai API and sanitize")
    thumb.add_argument("--facebook", default=None, action="store_true", help="Explicitly generate Facebook 4:5 thumbnail")
    thumb.add_argument("--no-facebook", dest="facebook", action="store_false", help="Explicitly skip Facebook 4:5 thumbnail")

    sanitize = subparsers.add_parser("sanitize", help="Eradicate C2PA provenance and AI metadata from cover images")
    sanitize.add_argument("--folder", type=Path, required=True, help="Path to video folder (e.g. outputs/.../<folder>)")

    prepare_images = subparsers.add_parser("prepare-v3-images", help="Create metadata-free PNG posting copies of V3 images, preserving originals")
    prepare_images.add_argument("--folder", type=Path, required=True, help="V3 pack or its parent video folder")

    deepdive = subparsers.add_parser("deepdive", help="Generate or regenerate exhaustive Deep-Dive Educational Synthesis (deep_dive_summary.txt)")
    deepdive.add_argument("--folder", type=Path, required=True, help="Path to video folder (e.g. outputs/.../<folder>)")
    deepdive.add_argument("--provider", choices=["vyceai", "seekai", "gemini", "apinex", "brainstorm"], help="LLM provider for synthesis")
    deepdive.add_argument("--model", type=str, help="LLM model name override")

    return parser



def _load_job(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("Job JSON must contain a sources array")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = get_settings()
    try:
        if args.command == "prepare-v3-images":
            from .image_export import prepare_v3_images
            report = prepare_v3_images(args.folder)
            _print_json(report)
            return 0 if report["status"] == "success" else 1

        if args.command == "doctor":
            checks: dict[str, Any] = {
                "python": sys.version.split()[0],
                "project_root": str(PROJECT_ROOT),
                "apinex_api_key": "configured" if settings.apinex_api_key else "missing",
                "vyceai_api_key": "configured" if settings.vyceai_api_key else "missing",
                "seekai_api_key": "configured" if settings.seekai_api_key else "missing",
                "gemini_api_key": "configured" if settings.gemini_api_key else "missing",
                "elevenlabs_api_key": "configured" if settings.elevenlabs_api_key else "missing (visual hook will be used in v2)",
                "llm_provider": settings.llm_provider,
                "youtube_api_key": "configured" if settings.youtube_api_key else "missing (web fallback available in Codex)",
                "font": str(settings.font_path) if settings.font_path.exists() else "missing",
            }
            try:
                checks["ffmpeg"] = find_ffmpeg()
            except Exception as error:
                checks["ffmpeg"] = f"missing: {error}"
            checks["ready"] = bool((settings.apinex_api_key or settings.vyceai_api_key or settings.seekai_api_key or settings.gemini_api_key) and settings.font_path.exists() and not str(checks["ffmpeg"]).startswith("missing:"))
            _print_json(checks)
            return 0 if checks["ready"] else 2

        if args.command == "search":
            if not settings.youtube_api_key:
                _print_json({
                    "status": "fallback_required",
                    "reason": "YOUTUBE_API_KEY is not configured",
                    "query": args.query,
                    "mode": args.mode,
                    "region": args.region,
                    "language": args.language,
                    "limit": args.limit,
                })
                return 2
            results = search_videos(
                settings.youtube_api_key, args.query, args.mode, args.region, args.language, args.duration, args.limit
            )
            _print_json({"status": "selection_required", "candidates": results})
            return 0

        if args.command == "login":
            from .publisher.session import interactive_login
            try:
                interactive_login([args.platform])
            except KeyboardInterrupt:
                print("\nLogin session closed.")
            return 0


        if args.command == "post":
            from .publisher.dispatcher import publish_folder
            report = publish_folder(
                folder_path=args.folder,
                platform=args.platform,
                schedule=args.schedule,
                draft=args.draft,
                force=args.force,
                headless=args.headless,
                mode=getattr(args, "mode", "video"),
                target=getattr(args, "target", None),
            )
            _print_json(report)
            failed_count = sum(1 for v in report.get("results", {}).values() if v.get("status") == "failed")
            return 1 if failed_count > 0 else 0

        if args.command == "rerender":
            from .rerender import rerender_folder
            result = rerender_folder(folder_path=args.folder, settings=settings)
            _print_json(result)
            return 0

        if args.command == "thumbnail":
            from .thumbnail import process_folder_thumbnails
            folder = args.folder.resolve()
            has_dd = (
                (folder / "deep_dive_summary.txt").is_file()
                or (folder / "v2" / "deep_dive_summary.txt").is_file()
                or (folder.parent / "deep_dive_summary.txt").is_file()
            )
            inc_fb = getattr(args, "facebook", None)
            if inc_fb is None:
                inc_fb = has_dd

            fb_p, vert_p, guide_p = process_folder_thumbnails(
                folder,
                style_preference=getattr(args, "style", None),
                archetype_preference=getattr(args, "archetype", None),
                generate_kieai=getattr(args, "kieai", False),
                include_facebook=inc_fb,
            )
            _print_json({
                "status": "success",
                "folder": str(folder),
                "facebook_4x5_prompt": str(fb_p) if fb_p else None,
                "vertical_9x16_prompt": str(vert_p),
                "guide": str(guide_p),
            })
            return 0

        if args.command == "sanitize":
            from .thumbnail.sanitizer import sanitize_folder_images
            cleaned = sanitize_folder_images(args.folder)
            _print_json({
                "status": "success",
                "folder": str(args.folder),
                "sanitized_images": [p.name for p in cleaned],
                "ai_markers_removed": bool(cleaned),
            })
            return 0

        if args.command == "deepdive":
            from .deepdive import generate_deepdive_summary
            folder = args.folder.resolve()
            if not folder.is_dir():
                raise FileNotFoundError(f"Directory not found: {folder}")
            target_dir = folder / "v2" if (folder / "v2").is_dir() else folder
            t_file = target_dir / "transcript.json" if (target_dir / "transcript.json").is_file() else folder / "transcript.json"
            manifest_file = target_dir / "manifest.json" if (target_dir / "manifest.json").is_file() else folder / "manifest.json"
            meta = {}
            if manifest_file.is_file():
                try:
                    m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                    meta = m_data.get("metadata", {})
                except Exception:
                    pass
            out_p = generate_deepdive_summary(
                output_dir=target_dir,
                transcript_source=t_file,
                settings=settings,
                metadata=meta,
                provider=getattr(args, "provider", None),
                model=getattr(args, "model", None),
            )
            _print_json({
                "status": "success",
                "folder": str(target_dir),
                "deep_dive_summary": str(out_p),
            })
            return 0

        if getattr(args, "provider", None):
            os.environ["LLM_PROVIDER"] = args.provider

        if getattr(args, "model", None):
            prov = getattr(args, "provider", None)
            if prov == "vyceai" or prov is None:
                os.environ["VyceAI_Model"] = args.model
                os.environ["VYCEAI_MODEL"] = args.model
            elif prov == "gemini":
                os.environ["GEMINI_MODEL"] = args.model
            elif prov == "seekai":
                os.environ["SEEKAI_MODEL"] = args.model
            elif prov == "apinex":
                os.environ["APINEX_MODEL"] = args.model

        settings = get_settings()

        analysis_override = None
        if getattr(args, "analysis", None):
            analysis_override = json.loads(Path(args.analysis).read_text(encoding="utf-8"))

        sources = list(args.source)
        output = args.output or settings.output_dir
        keep_work = args.keep_work
        selected_version = getattr(args, "version", None)
        generate_deepdive = args.deepdive
        generate_thumbnails = args.thumbnails

        if args.job:
            job = _load_job(args.job)
            sources.extend(str(value) for value in job["sources"])
            if job.get("output_dir") and not args.output:
                output = Path(job["output_dir"])
            keep_work = bool(job.get("keep_work", keep_work))
            if not selected_version and job.get("version"):
                selected_version = str(job["version"]).lower()
            if generate_deepdive is None and "deepdive" in job:
                generate_deepdive = job["deepdive"]
            if generate_thumbnails is None and "thumbnails" in job:
                generate_thumbnails = job["thumbnails"]

        if not sources:
            raise ValueError("Provide at least one --source or a --job file")

        # Missing preferences must not silently become opt-outs in agent runs.
        if not sys.stdin.isatty():
            missing = []
            if selected_version is None:
                missing.append("V1/V2 (--version v1|v2)")
            if generate_deepdive is None:
                missing.append("deep dive (--deepdive or --no-deepdive)")
            if generate_thumbnails is None:
                missing.append("thumbnails (--thumbnails none|manual|kieai)")
            if missing:
                raise ValueError("SETUP_REQUIRED: Ask the user for the missing choices before processing: " + "; ".join(missing))

        if not selected_version:
            if sys.stdin.isatty():
                sys.stderr.write("\nSelect pipeline version:\n")
                sys.stderr.write("  1. V1 — 38-second, two-page format\n")
                sys.stderr.write("  2. V2 — 42.2-second, four-page format\n")
                try:
                    choice = input("Enter choice [1 or 2, default: 2]: ").strip()
                    if choice not in ("", "1", "2"):
                        raise ValueError("Choose 1 or 2")
                    selected_version = "v1" if choice == "1" else "v2"
                except (KeyboardInterrupt, EOFError):
                    raise ValueError("SETUP_REQUIRED: Version selection was not completed") from None
            else:
                raise ValueError("SETUP_REQUIRED: Select V1 or V2")

        # Step 2: Deep-Dive Educational Synthesis Decision Gate
        if generate_deepdive is None and sys.stdin.isatty():
            try:
                ans_dd = input("\nGenerate exhaustive Deep-Dive Educational Synthesis (deep_dive_summary.txt for Facebook photo posts)? [y/N]: ").strip().lower()
                if ans_dd not in ("", "n", "no", "y", "yes"):
                    raise ValueError("Answer yes or no for deep dive")
                generate_deepdive = ans_dd in ("y", "yes")
            except (KeyboardInterrupt, EOFError):
                raise ValueError("SETUP_REQUIRED: Deep-dive selection was not completed") from None

        # Step 3 & 4: Thumbnail Decision Gates
        if generate_thumbnails is None and sys.stdin.isatty():
            try:
                ans = input("\nGenerate high-CTR thumbnail & photo prompts (4:5 FB & 9:16 vertical)? [y/N]: ").strip().lower()
                if ans in ("y", "yes"):
                    method = input("  Choose generation method (1: Manual prompts, 2: Automatic KIE.ai): ").strip()
                    if method not in ("1", "2"):
                        raise ValueError("SETUP_REQUIRED: Explicitly choose manual or KIE.ai")
                    generate_thumbnails = "manual" if method == "1" else "kieai"
                else:
                    if ans not in ("", "n", "no"):
                        raise ValueError("Answer yes or no for thumbnails")
                    generate_thumbnails = "none"
            except (KeyboardInterrupt, EOFError):
                raise ValueError("SETUP_REQUIRED: Thumbnail selection was not completed") from None

        if selected_version not in ("v1", "v2") or type(generate_deepdive) is not bool or generate_thumbnails not in ("none", "manual", "kieai"):
            raise ValueError("Invalid setup choices: version v1/v2, deepdive boolean, thumbnails none/manual/kieai are required")

        if selected_version == "v2":
            from .v2.pipeline import run_batch_v2
            report = run_batch_v2(
                sources,
                output.resolve(),
                settings,
                keep_work=keep_work,
                force=getattr(args, "force", False),
                no_tts=getattr(args, "no_tts", False),
                analysis_override=analysis_override,
                generate_thumbnails=generate_thumbnails,
                generate_deepdive=generate_deepdive,
            )
        else:
            report = run_batch(
                sources,
                output.resolve(),
                settings,
                keep_work=keep_work,
                analysis_override=analysis_override,
                generate_thumbnails=generate_thumbnails,
                generate_deepdive=generate_deepdive,
            )

        _print_json(report)
        return 0 if report.get("failed", 0) == 0 else 1
    except Exception as error:
        safe = redact(str(error), [settings.gemini_api_key, settings.youtube_api_key, settings.seekai_api_key, settings.vyceai_api_key, settings.elevenlabs_api_key])
        _print_json({"status": "error", "error": safe})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
