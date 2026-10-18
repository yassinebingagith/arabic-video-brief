from __future__ import annotations

import random
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

from .formatter import load_post_data
from .meta import publish_to_meta
from .session import persistent_browser_context
from .tiktok import publish_to_tiktok
from .tracker import get_publish_status, is_already_published, record_publish_result
from .completion import mark_episode_done
from .youtube import publish_to_youtube


def publish_folder(
    folder_path: Path | str,
    platform: str = "all",
    schedule: str | None = None,
    draft: bool = False,
    force: bool = False,
    headless: bool = False,
    mode: str = "video",
    target: str | None = None,
) -> dict[str, Any]:
    folder = Path(folder_path).resolve()
    if not (folder / "brief.mp4").is_file() and not any(folder.glob("CapCut_1080p_*.mp4")):
        if (folder / "v2").is_dir() and ((folder / "v2" / "brief.mp4").is_file() or any((folder / "v2").glob("CapCut_1080p_*.mp4"))):
            folder = folder / "v2"
    print(f"\n=======================================================")
    print(f"  PUBLISHING AUTOMATION: {folder.name}")
    print(f"=======================================================")

    post_data = load_post_data(folder)
    print(f"Video file: {post_data.video_path}")
    print(f"Title: {post_data.youtube_title}")

    requested_platforms = []
    platform_lower = platform.lower()
    if platform_lower == "all":
        requested_platforms = ["youtube", "tiktok", "meta"]
    elif "," in platform_lower:
        parts = [p.strip() for p in platform_lower.split(",") if p.strip()]
        for p in parts:
            if p in ("youtube", "tiktok", "meta"):
                requested_platforms.append(p)
            else:
                raise ValueError(f"Unknown platform: '{p}'. Choose from: all, youtube, tiktok, meta")
    elif platform_lower in ("youtube", "tiktok", "meta"):
        requested_platforms = [platform_lower]
    else:
        raise ValueError(f"Unknown platform: '{platform}'. Choose from: all, youtube, tiktok, meta, or comma-separated list (e.g. youtube,tiktok)")

    # Build queue of publishing tasks: (platform, mode, target)
    tasks: list[dict[str, Any]] = []
    for plat in requested_platforms:
        if plat == "meta":
            meta_tgt = target if target else ("meta" if mode == "video" else "facebook")
            tasks.append({"platform": "meta", "mode": mode, "target": meta_tgt})
        else:
            tasks.append({"platform": plat, "mode": mode, "target": None})

    # Automatic Facebook Photo Post Rule:
    # When publishing across 'all' (or when 'meta' is included in video mode), and the folder contains
    # an exhaustive Deep-Dive Educational Synthesis + 4:5 Facebook cover, automatically queue the Facebook Photo Post!
    if (
        (platform_lower == "all" or "meta" in requested_platforms)
        and mode == "video"
        and post_data.deep_dive_caption
        and post_data.cover_facebook_4x5
        and post_data.cover_facebook_4x5.is_file()
    ):
        print(
            f"[Workflow Auto-Queue] Exhaustive deep-dive summary and 4:5 Facebook cover detected. "
            f"Automatically appending Facebook Photo Post to publishing queue."
        )
        tasks.append({"platform": "meta", "mode": "photo", "target": "facebook"})

    results: dict[str, Any] = {}
    confirmed_publication = False

    with sync_playwright() as p:
        with persistent_browser_context(p, headless=headless) as context:
            for idx, task in enumerate(tasks):
                plat = task["platform"]
                task_mode = task["mode"]
                task_target = task["target"]
                track_key = f"meta_{task_mode}" if plat == "meta" else plat

                if not force and is_already_published(folder, track_key):
                    print(f"[{plat.upper()} ({task_mode})] Already recorded as published. Skipping (use --force to re-post).")
                    results[track_key] = {"status": "skipped", "reason": "already_published"}
                    prior = get_publish_status(folder).get(track_key, {})
                    confirmed_publication |= prior.get("publication_state") == "published"
                    continue

                if idx > 0:
                    pause = random.randint(15, 30)
                    print(f"\n[Cooldown] Waiting {pause}s between platform uploads for safety...")
                    time.sleep(pause)

                print(f"\n>>> Starting upload to: {plat.upper()} (mode={task_mode}, target={task_target})")
                try:
                    if plat == "youtube":
                        res = publish_to_youtube(context, post_data, schedule=schedule, draft=draft)
                    elif plat == "tiktok":
                        res = publish_to_tiktok(context, post_data, schedule=schedule, draft=draft)
                    elif plat == "meta":
                        res = publish_to_meta(context, post_data, schedule=schedule, draft=draft, mode=task_mode, target=task_target)
                    else:
                        continue

                    if res.get("status") != "success":
                        raise RuntimeError(f"Publication was not confirmed: {res}")
                    publication_state = "draft" if draft or res.get("mode") == "draft" else (
                        "scheduled" if schedule or res.get("mode") == "scheduled" else "published"
                    )
                    confirmed_publication |= publication_state == "published"

                    record_publish_result(
                        folder=folder,
                        platform=track_key,
                        status="success",
                        details=res.get("mode", "published"),
                        url=res.get("url", ""),
                        publication_state=publication_state,
                    )
                    results[track_key] = {"status": "success", **res, "publication_state": publication_state}
                except Exception as exc:
                    record_publish_result(
                        folder=folder,
                        platform=track_key,
                        status="failed",
                        details=str(exc),
                    )
                    results[track_key] = {"status": "failed", "error": str(exc)}
                    print(f"[{plat.upper()}] FAILED: {exc}")

    completion = None
    if confirmed_publication:
        # Wait until all uploads and browser handles are closed before renaming.
        try:
            completion = mark_episode_done(folder)
            folder = Path(completion["folder"])
        except (OSError, ValueError) as error:
            completion = {"status": "rename_failed", "error": str(error)}
            print(f"[Folder marker] Publication succeeded, but folder rename failed: {error}")

    print("\n=======================================================")
    print("  PUBLISHING RUN COMPLETE")
    print(f"=======================================================")
    for p_name, r_data in results.items():
        print(f"  • {p_name.upper()}: {r_data.get('status')}")
    print("=======================================================\n")

    return {
        "folder": str(folder),
        "results": results,
        "completion": completion,
    }
