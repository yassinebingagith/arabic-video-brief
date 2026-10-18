"""Register generated V3 images locally and verify authored Arabic number glyphs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arabic_video_brief.v3_assets import (  # noqa: E402
    accept_image,
    check_copy_digits,
    normalize_authored_copy,
    save_image,
    next_image_action,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("save", "accept", "check", "normalize-digits", "next"):
        p = sub.add_parser(command)
        p.add_argument("--folder", required=True, type=Path)
        if command in ("save", "accept"):
            p.add_argument("--id", required=True)
        if command == "save":
            p.add_argument("--source", required=True, type=Path)
            p.add_argument("--method", required=True, choices=["api", "chatgpt_mcp", "manual"])
        if command == "accept":
            p.add_argument("--reviewed", action="store_true", help="Confirm you visually inspected the output")
    args = parser.parse_args()
    try:
        if args.command == "save":
            report = save_image(args.folder, args.id, args.source, args.method)
        elif args.command == "accept":
            report = accept_image(args.folder, args.id, reviewed=args.reviewed)
        elif args.command == "check":
            report = check_copy_digits(args.folder)
        elif args.command == "next":
            report = next_image_action(args.folder)
        else:
            report = normalize_authored_copy(args.folder)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    # Keep the CLI functional on Windows shells whose stdout uses cp1252.
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report.get("status") != "fail" else 1


if __name__ == "__main__":
    sys.exit(main())
