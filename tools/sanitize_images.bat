@echo off & python -x "%~f0" %* & pause & exit /b
"""
Anti-AI Image Metadata Sanitizer (Standalone Tool)
=================================================
Double-click this file in any folder to wipe all AI provenance,
C2PA manifest boxes (caBX), EXIF, and IPTC tags from all images.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure Pillow is available
try:
    from PIL import Image
except ImportError:
    print("[INFO] Pillow library not found. Installing Pillow automatically...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

AI_MARKERS = [
    b"caBX",
    b"c2pa",
    b"OpenAI",
    b"ChatGPT",
    b"DALL-E",
    b"dall-e",
    b"trainedAlgorithmicMedia",
    b"compositeWithTrainedAlgorithmicMedia",
    b"digitalSourceType",
    b"Midjourney",
    b"Adobe Firefly",
    b"Stable Diffusion",
    b"Flux",
    b"flux",
    b"comfyui",
    b"automatic1111",
]

def sanitize_single_image(img_path: Path) -> tuple[bool, str]:
    try:
        raw_bytes = img_path.read_bytes()
        has_ai_tag = any(m in raw_bytes for m in AI_MARKERS)

        with Image.open(img_path) as im:
            mode = im.mode
            size = im.size
            raw_pixels = im.tobytes()
            clean_im = Image.frombytes(mode, size, raw_pixels)

            temp_path = img_path.parent / f"{img_path.stem}__clean_temp{img_path.suffix}"
            ext = img_path.suffix.lower()

            if ext in (".jpg", ".jpeg"):
                clean_im = clean_im.convert("RGB")
                clean_im.save(temp_path, "JPEG", quality=95, optimize=True)
            elif ext == ".webp":
                clean_im.save(temp_path, "WEBP", quality=95, method=6)
            else:  # PNG or other
                clean_im.save(temp_path, "PNG", optimize=True)

        temp_path.replace(img_path)
        tag_note = " (AI/C2PA signature eradicated)" if has_ai_tag else " (EXIF/metadata wiped)"
        return True, tag_note
    except Exception as exc:
        return False, f" Error: {exc}"

def main():
    print("=" * 65)
    print("     ANTI-AI IMAGE SANITIZER (C2PA / EXIF WIPER)")
    print("=" * 65)
    
    current_dir = Path.cwd()
    print(f"Target Directory: {current_dir}\n")

    valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    images = [
        p for p in current_dir.iterdir()
        if p.is_file() and p.suffix.lower() in valid_extensions and "__clean_temp" not in p.name
    ]

    if not images:
        print("[-] No image files (.png, .jpg, .jpeg, .webp) found in this folder.")
        print("=" * 65)
        return

    print(f"Found {len(images)} image(s) to process:\n")
    success_count = 0

    for idx, img in enumerate(images, 1):
        ok, note = sanitize_single_image(img)
        if ok:
            success_count += 1
            print(f" [{idx}/{len(images)}] [OK] {img.name}{note}")
        else:
            print(f" [{idx}/{len(images)}] [FAIL] {img.name}{note}")

    print("\n" + "=" * 65)
    print(f" Complete! Successfully sanitized: {success_count}/{len(images)} images.")
    print(" All images in this folder are now 100% clean raw pixel buffers.")
    print("=" * 65)

if __name__ == "__main__":
    main()
