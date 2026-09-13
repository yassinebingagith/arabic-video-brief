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
    parser = argparse.ArgumentParser(prog="avbrief", description="Create silent Arabic vertical video briefs")
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
    run.add_argument("--version", choices=["v1", "v2"], help="Pipeline version (v1: 20s legacy two-page, v2: 26s hook + four pages + conclusion)")
    run.add_argument("--model", type=str, help="LLM model name override (e.g. claude-sonnet-4-6, gpt-5.6-new)")
    run.add_argument("--no-tts", action="store_true", help="Render visual-only hook without ElevenLabs narration in V2")
    run.add_argument("--force", action="store_true", help="Force overwrite existing output folder")

    subparsers.add_parser("doctor", help="Check local dependencies and configuration")

    login = subparsers.add_parser("login", help="Open visible browser to log into social platforms once")
    login.add_argument("--platform", choices=["all", "youtube", "tiktok", "meta"], default="all")

    post = subparsers.add_parser("post", help="Publish a generated video brief folder")
    post.add_argument("--folder", type=Path, required=True, help="Path to video folder (e.g. outputs/.../<folder>)")
    post.add_argument("--platform", choices=["all", "youtube", "tiktok", "meta"], default="all")
    post.add_argument("--schedule", help="Optional schedule date/time, e.g. 'YYYY-MM-DD HH:MM'")
    post.add_argument("--draft", action="store_true", help="Save as unlisted/draft instead of publishing immediately")
    post.add_argument("--force", action="store_true", help="Re-post even if already recorded as published")
    post.add_argument("--headless", action="store_true", help="Run browser in background (default is visible/headful)")

    rerender = subparsers.add_parser("rerender", help="Re-render an existing video brief folder without repeating analysis")
    rerender.add_argument("--folder", type=Path, required=True, help="Path to video folder (e.g. outputs/.../<folder>)")

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
            )
            _print_json(report)
            failed_count = sum(1 for v in report.get("results", {}).values() if v.get("status") == "failed")
            return 1 if failed_count > 0 else 0

        if args.command == "rerender":
            from .rerender import rerender_folder
            result = rerender_folder(folder_path=args.folder, settings=settings)
            _print_json(result)
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

        if args.job:
            job = _load_job(args.job)
            sources.extend(str(value) for value in job["sources"])
            if job.get("output_dir") and not args.output:
                output = Path(job["output_dir"])
            keep_work = bool(job.get("keep_work", keep_work))
            if not selected_version and job.get("version"):
                selected_version = str(job["version"]).lower()

        if not sources:
            raise ValueError("Provide at least one --source or a --job file")

        if not selected_version:
            if sys.stdin.isatty():
                sys.stderr.write("\nSelect pipeline version:\n")
                sys.stderr.write("  1. V1 — Legacy 20-second, two-page format\n")
                sys.stderr.write("  2. V2 — Arabic hook, four summary pages, conclusion (Recommended)\n")
                try:
                    choice = input("Enter choice [1 or 2, default: 2]: ").strip()
                    selected_version = "v1" if choice == "1" else "v2"
                except (KeyboardInterrupt, EOFError):
                    selected_version = "v1"
            else:
                selected_version = "v1"

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
            )
        else:
            report = run_batch(sources, output.resolve(), settings, keep_work=keep_work, analysis_override=analysis_override)

        _print_json(report)
        return 0 if report.get("failed", 0) == 0 else 1
    except Exception as error:
        safe = redact(str(error), [settings.gemini_api_key, settings.youtube_api_key, settings.seekai_api_key, settings.vyceai_api_key, settings.elevenlabs_api_key])
        _print_json({"status": "error", "error": safe})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
