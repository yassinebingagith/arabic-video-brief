from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_FILE = "publish_status.json"


def get_publish_status(folder: Path) -> dict[str, Any]:
    file_path = folder / STATUS_FILE
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def is_already_published(folder: Path, platform: str) -> bool:
    data = get_publish_status(folder)
    plat_data = data.get(platform, {})
    return plat_data.get("status") == "success"


def record_publish_result(
    folder: Path,
    platform: str,
    status: str,
    details: str = "",
    url: str = "",
) -> None:
    file_path = folder / STATUS_FILE
    data = get_publish_status(folder)
    data[platform] = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
        "url": url,
    }
    file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
