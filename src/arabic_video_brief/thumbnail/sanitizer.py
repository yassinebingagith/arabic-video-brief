from __future__ import annotations

import os
from pathlib import Path
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
]


def has_ai_metadata(image_path: Path) -> bool:
    """Check if the image file contains C2PA or AI provenance metadata markers."""
    if not image_path.is_file():
        return False
    try:
        raw_bytes = image_path.read_bytes()
        return any(marker in raw_bytes for marker in AI_MARKERS)
    except Exception:
        return False


def sanitize_image(image_path: Path, force: bool = False) -> bool:
    """
    Strips all C2PA manifest boxes (caBX), IPTC digitalSourceType tags, EXIF, and AI generator signatures
    by rebuilding the image strictly from its raw decoded pixel buffer.
    This removes embedded metadata only; it does not guarantee platform labels or remove pixel watermarks.
    """
    if not image_path.is_file():
        return False

    needs_sanitize = force or has_ai_metadata(image_path)
    if not needs_sanitize:
        return False

    try:
        with Image.open(image_path) as im:
            mode = im.mode
            size = im.size
            raw_pixels = im.tobytes()
            clean_im = Image.frombytes(mode, size, raw_pixels)

            temp_path = image_path.parent / f"{image_path.stem}_clean{image_path.suffix}"
            ext = image_path.suffix.lower()

            if ext in (".jpg", ".jpeg"):
                clean_im = clean_im.convert("RGB")
                clean_im.save(temp_path, "JPEG", quality=95, optimize=True)
            elif ext == ".webp":
                clean_im.save(temp_path, "WEBP", quality=95, method=6)
            else:  # PNG or default
                clean_im.save(temp_path, "PNG", optimize=True)

        # Replace original with sanitized file
        temp_path.replace(image_path)
        return True
    except Exception as exc:
        print(f"[Sanitizer] Warning: Failed to sanitize {image_path.name}: {exc}")
        return False


def sanitize_folder_images(folder: Path) -> list[Path]:
    """Finds and sanitizes all cover images in the specified folder."""
    sanitized: list[Path] = []
    candidates = [
        folder / "cover_facebook_4x5.png",
        folder / "cover_facebook_4x5.jpg",
        folder / "cover_facebook_4x5.jpeg",
        folder / "cover_facebook_4x5.webp",
        folder / "cover_vertical_9x16.png",
        folder / "cover_vertical_9x16.jpg",
        folder / "cover_vertical_9x16.jpeg",
        folder / "cover_vertical_9x16.webp",
    ]
    for p in candidates:
        if p.is_file() and sanitize_image(p):
            sanitized.append(p)
    return sanitized
