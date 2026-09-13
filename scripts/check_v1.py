import subprocess
from pathlib import Path
import sys

outputs = Path("outputs")
v1_files = []
for p in outputs.rglob("brief.mp4"):
    if "uNWl-hpVTa0" in str(p):
        v1_files.append(p)

print("Found V1 files:", len(v1_files))
if v1_files:
    v1_path = v1_files[0]
    print("V1 path:", v1_path.parent.name.encode("ascii", "replace").decode("ascii"))
    
    # Extract frames at 1s, 5s, 22s
    f1 = Path("scratch/v1_1s.png")
    f5 = Path("scratch/v1_5s.png")
    f22 = Path("scratch/v1_22s.png")
    
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:01.0", "-i", str(v1_path), "-vframes", "1", str(f1)], capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:05.0", "-i", str(v1_path), "-vframes", "1", str(f5)], capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:22.0", "-i", str(v1_path), "-vframes", "1", str(f22)], capture_output=True)
    
    print("Extracted frames: 1s exists:", f1.exists(), "5s exists:", f5.exists(), "22s exists:", f22.exists())
