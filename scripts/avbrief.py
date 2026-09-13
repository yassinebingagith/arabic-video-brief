from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve()
    local_root = here.parents[1]
    configured = os.environ.get("ARABIC_VIDEO_BRIEF_PROJECT")
    project_root = Path(configured) if configured else local_root
    if not (project_root / "src" / "arabic_video_brief").exists():
        project_root = Path(r"D:\Automation\arabic-video-brief")

    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            return subprocess.call([str(venv_python), "-m", "arabic_video_brief", *sys.argv[1:]], cwd=project_root, env=env)
        except KeyboardInterrupt:
            print("\nProcess interrupted by user.")
            return 0



    sys.path.insert(0, str(project_root / "src"))
    from arabic_video_brief.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
