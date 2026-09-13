import sys
import time
from pathlib import Path

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from arabic_video_brief.publisher.dispatcher import publish_folder

folder_root = Path("outputs/World-Order-Is-a-Lie-The-Next-50-Years-Will-Change-Everything-Prof-Jiang-FO547-R-ywd-Ve8a8Tc").resolve()
folder_v2 = folder_root / "v2"

print("\n=======================================================")
print("  MULTI-PLATFORM TARGETED PUBLISHING")
print("  • Meta (Instagram + Facebook): Version 1 Video")
print("  • YouTube + TikTok: Version 2 Video")
print("=======================================================\n")

# 1. Meta (Instagram & Facebook) using V1
print(">>> [1/3] Publishing V1 video to META (Instagram & Facebook)...")
res_meta = publish_folder(folder_root, platform="meta", headless=False)
print(f"Meta Status: {res_meta.get('results', {}).get('meta', {}).get('status')}")

print("\n[Cooldown] Waiting 20s before next upload for account safety...")
time.sleep(20)

# 2. YouTube using V2
print(">>> [2/3] Publishing V2 video to YOUTUBE SHORTS...")
res_yt = publish_folder(folder_v2, platform="youtube", headless=False)
print(f"YouTube Status: {res_yt.get('results', {}).get('youtube', {}).get('status')}")

print("\n[Cooldown] Waiting 20s before next upload for account safety...")
time.sleep(20)

# 3. TikTok using V2
print(">>> [3/3] Publishing V2 video to TIKTOK...")
res_tt = publish_folder(folder_v2, platform="tiktok", headless=False)
print(f"TikTok Status: {res_tt.get('results', {}).get('tiktok', {}).get('status')}")

print("\n=======================================================")
print("  ALL TARGETED PUBLISHING TASKS COMPLETED!")
print("  • Meta (V1):", res_meta.get("results", {}).get("meta", {}).get("status"))
print("  • YouTube (V2):", res_yt.get("results", {}).get("youtube", {}).get("status"))
print("  • TikTok (V2):", res_tt.get("results", {}).get("tiktok", {}).get("status"))
print("=======================================================\n")
