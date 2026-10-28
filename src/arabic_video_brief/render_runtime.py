"""Read this checkout's generated renderer configuration, never another project."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .config import PROJECT_ROOT


def load_render_runtime(root: Path | None = None) -> dict[str, str]:
    root = (root or PROJECT_ROOT).resolve()
    config = root / ".runtime" / "render-runtime.json"
    if not config.is_file():
        raise RuntimeError("Renderer dependencies are not installed. Run python scripts/setup.py (or npm ci).")
    runtime = json.loads(config.read_text(encoding="utf-8"))
    if Path(runtime.get("PROJECT_ROOT", "")).resolve() != root:
        raise RuntimeError("This checkout moved. Run npm run setup:renderer to refresh its local paths.")
    for key in ("NODE_BIN", "CHROME_BIN", "FFMPEG_BIN", "FFPROBE_BIN", "HYPERFRAMES_CLI", "GSAP_JS"):
        if not Path(runtime.get(key, "")).is_file():
            raise RuntimeError(f"Renderer dependency {key} is missing. Run npm ci.")
    # Explicit overrides are useful for managed installations; no personal paths are assumed.
    for key in ("CHROME_BIN", "FFMPEG_BIN", "FFPROBE_BIN"):
        if os.environ.get(key):
            candidate = Path(os.environ[key]).expanduser().resolve()
            if not candidate.is_file():
                raise RuntimeError(f"Configured {key} does not exist: {candidate}")
            runtime[key] = str(candidate)
    return runtime
