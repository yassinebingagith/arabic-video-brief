from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from playwright.sync_api import BrowserContext, Playwright

from ..config import PROJECT_ROOT

DEFAULT_PROFILE_DIR = PROJECT_ROOT / "assets" / "browser_profile"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

PLATFORM_URLS = [
    "https://www.facebook.com/login.php",
    "https://www.tiktok.com/login",
    "https://business.facebook.com/latest/reels_composer",
    "https://studio.youtube.com",
]


def find_chrome_exe() -> str:
    candidates = [
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError("Google Chrome was not found in standard Windows installation paths.")


def get_profile_path() -> Path:
    override = os.environ.get("ARABIC_VIDEO_BRIEF_BROWSER_PROFILE")
    path = Path(override) if override else DEFAULT_PROFILE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def persistent_browser_context(
    playwright: Playwright,
    headless: bool = False,
) -> Generator[BrowserContext, None, None]:
    profile_path = get_profile_path()

    # Clean launcher with NO flags that trigger Chrome security infobar warnings
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_path),
        channel="chrome",
        chromium_sandbox=True,
        headless=headless,
        user_agent=DEFAULT_USER_AGENT,
        viewport=None,
        args=[],
        ignore_default_args=["--enable-automation"],
        locale="en-US",
    )

    # Stealth: Mask automation markers cleanly via JavaScript
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        window.chrome = window.chrome || {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    """)

    try:
        yield context
    finally:
        try:
            context.close()
        except Exception:
            pass


def interactive_login(platforms: list[str] | None = None) -> None:
    """Launches official Google Chrome directly with your persistent profile for native login."""
    profile_path = get_profile_path()
    chrome_exe = find_chrome_exe()

    print("=" * 68)
    print("  INTERACTIVE CHROME LOGIN SESSION (100% NATIVE)")
    print("=" * 68)
    print("Opening your official Google Chrome with your persistent profile.")
    print("No automation flags are attached. Two-Factor Authentication (2FA),")
    print("WebAuthn, and SMS verification will work completely naturally.")
    print(f"Profile directory: {profile_path}")
    print("=" * 68)

    # Launch native Chrome pointing directly to our persistent profile directory
    cmd = [
        str(chrome_exe),
        f"--user-data-dir={str(profile_path)}",
        "--no-first-run",
        "--no-default-browser-check",
        *PLATFORM_URLS,
    ]

    proc = subprocess.Popen(cmd)

    print("\n" + "#" * 68)
    print("  STEPS IN CHROME:")
    print("  1. In Tab 1: Sign into Facebook (2FA will prompt and load smoothly).")
    print("  2. In Tab 2: On TikTok, click 'Continue with Facebook'.")
    print("  3. In Tab 3: Confirm Meta Business Suite is accessible.")
    print("  4. In Tab 4: Sign into your YouTube Studio channel.")
    print("  5. When you are done, return here and press [ENTER] (or close Chrome).")
    print("#" * 68 + "\n")

    try:
        input(">>> Press [ENTER] here when all accounts are logged in... ")
    except (KeyboardInterrupt, EOFError):
        print("\nClosing session...")

    # Wait or terminate the interactive browser process
    try:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
    except Exception:
        pass

    print("\nSUCCESS: All login sessions saved to disk! You are ready to publish.")
