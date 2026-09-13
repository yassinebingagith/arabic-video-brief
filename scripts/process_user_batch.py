import sys
import time
from pathlib import Path

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from arabic_video_brief.config import get_settings
from arabic_video_brief.pipeline import process_source
from arabic_video_brief.v2.pipeline import process_source_v2

settings = get_settings()
output_root = settings.output_dir

print(f"Using Provider: {settings.llm_provider}")
print(f"Using Gemini Model: {settings.gemini_model}")

# 1. q2cg1gEYWJQ with V2
print("\n=======================================================")
print(">>> [1/4] Processing 'q2cg1gEYWJQ' with V2...")
print("=======================================================")
slug_candidates = list(output_root.glob("*q2cg1gEYWJQ*/v2/brief.mp4"))
if slug_candidates and slug_candidates[0].exists():
    print(f"Skipping [1/4]: Already completed at {slug_candidates[0]}")
else:
    t0 = time.time()
    res1 = process_source_v2(
        "https://www.youtube.com/watch?v=q2cg1gEYWJQ",
        output_root,
        settings,
        force=True,
    )
    print(f"Done [1/4] in {time.time() - t0:.1f}s")

# 2. 4Vz6L8B73i4 with V1
print("\n=======================================================")
print(">>> [2/4] Processing '4Vz6L8B73i4' with V1...")
print("=======================================================")
slug_candidates_2 = [p for p in output_root.glob("*4Vz6L8B73i4*/brief.mp4") if "v2" not in str(p.parent.name)]
if slug_candidates_2 and slug_candidates_2[0].exists():
    print(f"Skipping [2/4]: Already completed at {slug_candidates_2[0]}")
else:
    t0 = time.time()
    res2 = process_source(
        "https://www.youtube.com/watch?v=4Vz6L8B73i4",
        output_root,
        settings,
    )
    print(f"Done [2/4] in {time.time() - t0:.1f}s")

# 3. ywd-Ve8a8Tc with V1
print("\n=======================================================")
print(">>> [3/4] Processing 'ywd-Ve8a8Tc' with V1...")
print("=======================================================")
t0 = time.time()
res3 = process_source(
    "https://www.youtube.com/watch?v=ywd-Ve8a8Tc",
    output_root,
    settings,
)
print(f"Done [3/4] in {time.time() - t0:.1f}s")

# 4. ywd-Ve8a8Tc with V2
print("\n=======================================================")
print(">>> [4/4] Processing 'ywd-Ve8a8Tc' with V2...")
print("=======================================================")
t0 = time.time()
res4 = process_source_v2(
    "https://www.youtube.com/watch?v=ywd-Ve8a8Tc",
    output_root,
    settings,
    force=True,
)
print(f"Done [4/4] in {time.time() - t0:.1f}s")

print("\n=======================================================")
print(">>> ALL 4 TASKS COMPLETED SUCCESSFULLY!")
print("=======================================================")
