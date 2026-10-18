"""V3 generated-image registration and Western-digit copy checks.

Image generation itself belongs to the selected API or connected ChatGPT/MCP
session. This module only validates local files and records their status.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps


NON_WESTERN_DIGITS = "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹"
WESTERN_DIGITS = "0123456789" * 2
DIGIT_TABLE = str.maketrans(NON_WESTERN_DIGITS, WESTERN_DIGITS)
SOURCE_FORMATS = {".png", ".jpg", ".jpeg", ".webp"}
METHODS = {"api", "chatgpt_mcp", "manual"}
COPY_FILES = ("script.json", "production-pack.md", "instagram/caption.txt", "facebook/caption.txt")


def normalize_digits(text: str) -> str:
    """Convert Arabic-Indic and Persian digits to 0-9 without changing letters."""
    return text.translate(DIGIT_TABLE)


def _root(folder: Path) -> Path:
    root = folder.resolve()
    if not (root / "generation-plan.json").is_file() and (root / "v3" / "generation-plan.json").is_file():
        root = root / "v3"
    if not (root / "generation-plan.json").is_file():
        raise ValueError("Expected a V3 folder containing generation-plan.json")
    return root


def _safe_local(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("V3 output/reference paths must be relative and inside the pack")
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise ValueError("V3 path points outside the pack")
    return target


def _plan(root: Path) -> dict:
    plan = json.loads((root / "generation-plan.json").read_text(encoding="utf-8"))
    if plan.get("mode") != "v3" or not isinstance(plan.get("images"), list):
        raise ValueError("Invalid V3 generation-plan.json")
    return plan


def _row(plan: dict, image_id: str) -> dict:
    matches = [item for item in plan["images"] if item.get("id") == image_id]
    if len(matches) != 1:
        raise ValueError(f"Image ID is missing or ambiguous: {image_id}")
    return matches[0]


def _write_plan(root: Path, plan: dict) -> None:
    location = root / "generation-plan.json"
    temp = root / "generation-plan.pending.json"
    temp.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(location)


def _copy_paths(root: Path, plan: dict) -> list[Path]:
    paths = [_safe_local(root, p) for p in COPY_FILES]
    for row in plan["images"]:
        paths.append(_safe_local(root, row["prompt_path"]))
    return paths


def check_copy_digits(folder: Path) -> dict:
    root = _root(folder)
    files = _copy_paths(root, _plan(root))
    violations = []
    missing = []
    for file in files:
        if not file.is_file():
            missing.append(str(file.relative_to(root)))
            continue
        text = file.read_text(encoding="utf-8")
        wrong = sorted(set(text).intersection(NON_WESTERN_DIGITS))
        if wrong:
            violations.append({"path": str(file.relative_to(root)), "digits": "".join(wrong)})
    return {"status": "pass" if not violations and not missing else "fail", "violations": violations, "missing": missing}


def normalize_authored_copy(folder: Path) -> dict:
    """Repair only V3 authored text. Never rewrite transcript or images."""
    root = _root(folder)
    changed = []
    for path in _copy_paths(root, _plan(root)):
        if not path.is_file():
            raise FileNotFoundError(path)
        before = path.read_text(encoding="utf-8")
        after = normalize_digits(before)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changed.append(str(path.relative_to(root)))
    return {"changed": changed, **check_copy_digits(root)}


def _image_qa(path: Path) -> tuple[int, int]:
    if not path.is_file() or path.suffix.lower() not in SOURCE_FORMATS:
        raise ValueError("An existing PNG/JPEG/WebP file is required")
    with Image.open(path) as img:
        if getattr(img, "n_frames", 1) != 1:
            raise ValueError("Animated images are not supported")
        width, height = ImageOps.exif_transpose(img).size
    if width < 768 or height < 960:
        raise ValueError("Image resolution is too low for the 1080x1350 V3 deliverable")
    if abs(width / height - 4 / 5) > 0.015:
        raise ValueError(f"Expected a 4:5 portrait image; received {width}x{height}")
    return width, height


def save_image(folder: Path, image_id: str, source: Path, method: str) -> dict:
    if method not in METHODS:
        raise ValueError(f"Method must be one of: {', '.join(sorted(METHODS))}")
    root = _root(folder)
    plan = _plan(root)
    copy_report = check_copy_digits(root)
    if copy_report["status"] != "pass":
        raise ValueError("V3 authored copy has missing files or non-Western digits; run check / normalize-digits first")
    row = _row(plan, image_id)
    expected_thumbnail = plan.get("source", {}).get("thumbnail_path")
    declared_inputs = row.get("inputs", [])
    if not expected_thumbnail or not declared_inputs or declared_inputs[0].get("path") != expected_thumbnail:
        raise ValueError("The V3 source thumbnail must be the first reference")
    if not _safe_local(root, expected_thumbnail).is_file():
        raise ValueError("The original YouTube source thumbnail is missing")
    if row.get("depends_on"):
        if len(declared_inputs) < 2 or declared_inputs[1].get("role") != "style_anchor":
            raise ValueError("Later images require the accepted slide 1 as the second reference")
        anchor = _row(plan, plan.get("anchor_id", "ig-slide01"))
        if declared_inputs[1].get("path") != anchor["output_path"]:
            raise ValueError("The second reference must always be the original accepted slide 1")
    elif len(declared_inputs) != 1:
        raise ValueError("Slide 1 uses only the original YouTube thumbnail")
    if row["status"] in {"generated", "accepted"}:
        raise ValueError(f"{image_id} already exists. Preserve it and create a separate revision.")
    for dependency in row.get("depends_on", []):
        anchor = _row(plan, dependency)
        if anchor.get("status") != "accepted" or not _safe_local(root, anchor["output_path"]).is_file():
            raise ValueError(f"Accept and save {dependency} before generating {image_id}")
    original = source.resolve(strict=True)
    width, height = _image_qa(original)
    destination = _safe_local(root, row["output_path"])
    if destination.suffix.lower() != ".png":
        raise ValueError("Canonical V3 output paths must use PNG")
    if destination.exists():
        raise ValueError(f"Destination already exists: {destination}")
    preserved = _safe_local(root, f"generation-sources/{image_id}{original.suffix.lower()}")
    if preserved.exists() or original == destination or original == preserved:
        raise ValueError("The source or preserved original already occupies this output location")

    destination.parent.mkdir(parents=True, exist_ok=True)
    preserved.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the exact received file, including any metadata, for reproducibility.
    shutil.copy2(original, preserved)
    try:
        with Image.open(original) as im:
            im = ImageOps.exif_transpose(im)
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
            # Minor 4:5 drift is cropped rather than stretching the artwork.
            image = ImageOps.fit(im, (1080, 1350), Image.Resampling.LANCZOS)
            image.save(destination, format="PNG")
        _image_qa(destination)
        row["status"] = "generated"
        row["source_image_path"] = str(preserved.relative_to(root)).replace("\\", "/")
        row["generation_method"] = method
        row["width"], row["height"] = (1080, 1350)
        row["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
        row["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
        if isinstance(row.get("generation_job"), dict):
            row["generation_job"]["state"] = "saved"
            row["generation_job"]["saved_path"] = row["output_path"]
        plan["execution"] = method
        _write_plan(root, plan)
    except Exception:
        destination.unlink(missing_ok=True)
        preserved.unlink(missing_ok=True)
        raise
    return {"id": image_id, "status": "generated", "path": str(destination), "source_resolution": [width, height]}


def accept_image(folder: Path, image_id: str, *, reviewed: bool = False) -> dict:
    if not reviewed:
        raise ValueError("Visual review is required before accepting an image; pass --reviewed after inspecting it")
    root = _root(folder)
    plan = _plan(root)
    row = _row(plan, image_id)
    if row["status"] != "generated":
        raise ValueError(f"{image_id} must be generated before acceptance")
    target = _safe_local(root, row["output_path"])
    _image_qa(target)
    row["status"] = "accepted"
    row["accepted_at_utc"] = datetime.now(timezone.utc).isoformat()
    if image_id == plan.get("anchor_id", "ig-slide01"):
        for dependent in plan["images"]:
            if image_id in dependent.get("depends_on", []) and dependent["status"] == "pending_anchor":
                dependent["status"] = "prompt_ready"
    _write_plan(root, plan)
    return {"id": image_id, "status": "accepted", "path": str(target)}


def next_image_action(folder: Path) -> dict:
    """Read-only resume guidance; never submits, downloads or accepts an image."""
    root = _root(folder)
    plan = _plan(root)
    copy_report = check_copy_digits(root)
    if copy_report["status"] != "pass":
        return {"action": "repair_pack", "copy_check": copy_report}
    if plan.get("execution") not in METHODS:
        return {"action": "select_method", "reason": "The image-generation method has not been selected"}
    anchor_id = plan.get("anchor_id", "ig-slide01")
    anchor = _row(plan, anchor_id)
    rows = [anchor] + [row for row in plan["images"] if row["id"] != anchor_id]
    for row in rows:
        image_id = row["id"]
        target = _safe_local(root, row["output_path"])
        status = row.get("status")
        base = {"id": image_id, "path": str(target), "status": status}
        if status in {"generated", "accepted"}:
            try:
                _image_qa(target)
            except (ValueError, OSError) as error:
                return {**base, "action": "reconcile", "reason": str(error)}
            if row.get("sha256") and hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256"]:
                return {**base, "action": "reconcile", "reason": "Saved image changed after registration"}
            if status == "generated":
                return {**base, "action": "review", "reason": "Inspect this saved image before proceeding"}
            continue
        if target.exists():
            return {**base, "action": "reconcile", "reason": "Unregistered file already exists; do not regenerate or overwrite it"}
        job = row.get("generation_job") or {}
        if job.get("state") in {"submitted", "generating", "download_pending", "downloaded"}:
            return {**base, "action": "resume_job", "job": job,
                    "generation_session": plan.get("generation_session"),
                    "reason": "Resolve the existing request or download before submitting another"}
        if status == "needs_revision":
            return {**base, "action": "revise", "reason": "Preserve the existing attempt and repair its specific QA issue"}
        expected_thumbnail = plan.get("source", {}).get("thumbnail_path")
        inputs = row.get("inputs", [])
        if not expected_thumbnail or not inputs or inputs[0].get("path") != expected_thumbnail:
            return {**base, "action": "repair_pack", "reason": "Original thumbnail must be reference 1"}
        if image_id != anchor_id:
            if (anchor_id not in row.get("depends_on", []) or len(inputs) < 2
                    or inputs[1].get("path") != anchor["output_path"]
                    or inputs[1].get("role") != "style_anchor"):
                return {**base, "action": "repair_pack", "reason": "Every later image requires the same slide 1 anchor as reference 2"}
        for item in inputs:
            if not _safe_local(root, item["path"]).is_file():
                return {**base, "action": "repair_pack", "reason": f"Missing reference: {item['path']}"}
        return {**base, "action": "await_manual" if plan["execution"] == "manual" else "generate",
                "prompt": str(_safe_local(root, row["prompt_path"])), "inputs": inputs,
                "generation_session": plan.get("generation_session")}
    return {"action": "export", "reason": "All planned images are saved and accepted; prepare and verify posting copies"}
