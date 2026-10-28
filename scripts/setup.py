"""Install this checkout on Windows, macOS or Linux (Python 3.11+, Node.js 22+)."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def run(command):
    subprocess.run([str(part) for part in command], check=True, cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv-dir", type=Path, default=ROOT / ".venv")
    parser.add_argument("--with-publisher", action="store_true")
    parser.add_argument("--with-tests", action="store_true")
    parser.add_argument("--skip-renderer", action="store_true", help="Install Python tools only.")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or later is required.")
    npm = None
    if not args.skip_renderer:
        node = shutil.which("node")
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if not node or not npm:
            parser.error("Install Node.js 22+ (including npm), then rerun setup.")
        version = subprocess.check_output([node, "--version"], text=True).strip()
        if int(version.lstrip("v").split(".")[0]) < 22:
            parser.error("Node.js 22 or later is required.")
    environment = args.venv_dir.resolve()
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        print(f"Creating Python environment: {environment}", flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    extras = ["whiteboard"]
    if args.with_publisher:
        extras.append("publisher")
    if args.with_tests:
        extras.append("test")
    run([python, "-m", "pip", "install", "-e", f"{ROOT}[{','.join(extras)}]"])
    if npm:
        run([npm, "ci", "--no-audit", "--no-fund"])
        run([npm, "run", "doctor:renderer"])
    if args.with_publisher:
        run([python, "-m", "playwright", "install", "chromium"])
    if not (ROOT / ".env").exists():
        shutil.copy2(ROOT / ".env.example", ROOT / ".env")
    print("Setup complete. Configure your own API keys in .env for source analysis; local whiteboard rendering needs no API key.")
    print(f"Python environment: {python}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)
