"""Prepare lossless, metadata-free V3 posting copies without changing originals."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
from pathlib import Path

from PIL import Image, ImageCms, ImageOps


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def export_posting_image(source: Path, destination: Path) -> dict:
    """Apply orientation/color profile, then encode only decoded pixels as PNG.

    This strips embedded EXIF, XMP, C2PA and text chunks. It does not remove
    pixel-embedded watermarks, alter visual style or determine platform labels.
    """
    if source.resolve() == destination.resolve():
        raise ValueError("Posting copies must not overwrite the original image")
    original_bytes = source.read_bytes()
    with Image.open(io.BytesIO(original_bytes)) as image:
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("Animated images require an explicit frame selection")
        original_metadata_keys = sorted(image.info)
        image = ImageOps.exif_transpose(image)
        profile = image.info.get("icc_profile")
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        alpha = image.convert("RGBA").getchannel("A") if has_alpha else None
        if profile:
            color_source = image if image.mode in ("RGB", "CMYK", "LAB", "L") else image.convert("RGB")
            pixels = ImageCms.profileToProfile(
                color_source, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.createProfile("sRGB"), outputMode="RGB",
            )
        else:
            pixels = image.convert("RGB")
        if alpha is not None:
            pixels.putalpha(alpha)
        clean = Image.frombytes(pixels.mode, pixels.size, pixels.tobytes())

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        clean.save(temporary, "PNG", optimize=True)
        with Image.open(temporary) as verified:
            verified.load()
            if verified.info or verified.mode != clean.mode or verified.tobytes() != clean.tobytes():
                raise ValueError("PNG export verification failed")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "source": str(source), "output": str(destination),
        "width": clean.width, "height": clean.height, "mode": clean.mode,
        "source_metadata_keys": original_metadata_keys,
        "source_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "verified_metadata_free": True,
    }


def prepare_v3_images(folder: Path) -> dict:
    root = folder.resolve()
    if not (root / "generation-plan.json").is_file() and (root / "v3" / "generation-plan.json").is_file():
        root = root / "v3"
    if not (root / "generation-plan.json").is_file():
        raise ValueError("Choose a V3 pack folder containing generation-plan.json")
    export_root = root / "posting-ready"
    results, errors = [], []
    for platform in ("instagram", "facebook"):
        source_dir = root / platform
        if not source_dir.is_dir():
            continue
        for source in sorted(source_dir.iterdir()):
            if not source.is_file() or source.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            try:
                if not source.resolve().is_relative_to(root):
                    raise ValueError("Source image resolves outside this pack")
                name = source.name if source.suffix.lower() == ".png" else source.name + ".png"
                destination = export_root / platform / name
                if not destination.resolve().is_relative_to(root):
                    raise ValueError("Output resolves outside this pack")
                entry = export_posting_image(source, destination)
                entry["platform"] = platform
                results.append(entry)
            except Exception as error:
                errors.append({"source": str(source), "error": str(error)})
    report = {
        "status": "partial" if errors else ("success" if results else "no_images"),
        "folder": str(root), "export_folder": str(export_root),
        "exported": len(results), "failed": len(errors), "images": results, "errors": errors,
        "scope": "Embedded metadata removed; originals preserved; no Photoshop authorship tags added. Pixel watermarks and platform labels are not assessed.",
    }
    export_root.mkdir(parents=True, exist_ok=True)
    (export_root / "export-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
