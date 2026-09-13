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
from .tracker import is_already_published, record_publish_result
from .youtube import publish_to_youtube


def publish_folder(
    folder_path: Path | str,
    platform: str = "all",
    schedule: str | None = None,
    draft: bool = False,
    force: bool = False,
    headless: bool = False,
) -> dict[str, Any]:
    folder = Path(folder_path).resolve()
    if not (folder / "brief.mp4").is_file() and (folder / "v2" / "brief.mp4").is_file():
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
    elif platform_lower in ("youtube", "tiktok", "meta"):
        requested_platforms = [platform_lower]
    else:
        raise ValueError(f"Unknown platform: '{platform}'. Choose from: all, youtube, tiktok, meta")

    results: dict[str, Any] = {}

    with sync_playwright() as p:
        with persistent_browser_context(p, headless=headless) as context:
            for idx, plat in enumerate(requested_platforms):
                if not force and is_already_published(folder, plat):
                    print(f"[{plat.upper()}] Video is already recorded as published. Skipping (use --force to re-post).")
                    results[plat] = {"status": "skipped", "reason": "already_published"}
                    continue

                if idx > 0:
                    pause = random.randint(15, 30)
                    print(f"\n[Cooldown] Waiting {pause}s between platform uploads for safety...")
                    time.sleep(pause)

                print(f"\n>>> Starting upload to: {plat.upper()}")
                try:
                    if plat == "youtube":
                        res = publish_to_youtube(context, post_data, schedule=schedule, draft=draft)
                    elif plat == "tiktok":
                        res = publish_to_tiktok(context, post_data, schedule=schedule, draft=draft)
                    elif plat == "meta":
                        res = publish_to_meta(context, post_data, schedule=schedule, draft=draft)
                    else:
                        continue

                    record_publish_result(
                        folder=folder,
                        platform=plat,
                        status="success",
                        details=res.get("mode", "published"),
                        url=res.get("url", ""),
                    )
                    results[plat] = {"status": "success", **res}
                except Exception as exc:
                    record_publish_result(
                        folder=folder,
                        platform=plat,
                        status="failed",
                        details=str(exc),
                    )
                    results[plat] = {"status": "failed", "error": str(exc)}
                    print(f"[{plat.upper()}] FAILED: {exc}")

    print("\n=======================================================")
    print("  PUBLISHING RUN COMPLETE")
    print(f"=======================================================")
    for p_name, r_data in results.items():
        print(f"  • {p_name.upper()}: {r_data.get('status')}")
    print("=======================================================\n")

    return {
        "folder": str(folder),
        "results": results,
    }
