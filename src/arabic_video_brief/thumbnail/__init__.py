from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .image_client import ImageGeneratorClient
from .prompt_engine import (
    CuriosityVisualHint,
    FocalArchetype,
    ThumbnailPackage,
    extract_curiosity_visual_hint,
    generate_thumbnail_package,
    resolve_focal_archetype,
    save_thumbnail_prompts,
)
from .sanitizer import has_ai_metadata, sanitize_folder_images, sanitize_image
from .styles import STYLE_REGISTRY, VisualStyle, resolve_visual_style


def process_folder_thumbnails(
    folder: Path,
    manifest_data: dict[str, Any] | None = None,
    style_preference: str | None = None,
    archetype_preference: str | None = None,
    generate_kieai: bool = False,
    include_facebook: bool = True,
    **kwargs: Any,
) -> tuple[Path | None, Path, Path]:
    """Processes an existing or newly rendered video folder and creates 4:5 and 9:16 thumbnail prompt assets."""
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    # Handle argument shifts if manifest_data was omitted positionally
    if isinstance(manifest_data, str) and style_preference is None:
        style_preference = manifest_data
        manifest_data = None
    elif isinstance(manifest_data, bool) and not generate_kieai:
        generate_kieai = manifest_data
        manifest_data = None

    if "generate_kieai" in kwargs:
        generate_kieai = bool(kwargs["generate_kieai"])

    if "include_facebook" in kwargs:
        include_facebook = bool(kwargs["include_facebook"])

    # Check title
    title_path = folder / "post-title.txt"
    manifest_path = folder / "manifest.json"
    creative_path = folder / "creative-plan.json"
    if not creative_path.exists():
        creative_path = folder / "creative_plan.json"

    merged_manifest: dict[str, Any] = dict(manifest_data or {})
    if manifest_path.exists():
        try:
            loaded_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded_data, dict):
                merged_manifest = {**loaded_data, **merged_manifest}
        except Exception:
            pass
    manifest_data = merged_manifest

    creative_plan: dict[str, Any] = {}
    if creative_path.exists():
        try:
            creative_plan = json.loads(creative_path.read_text(encoding="utf-8"))
        except Exception:
            creative_plan = {}

    # V1 passes its current analysis before manifest.json is written. Standalone
    # thumbnail runs reuse saved copy; neither route needs another paid text call.
    if isinstance(kwargs.get("creative_plan"), dict):
        creative_plan.update(kwargs["creative_plan"])
    summary_path = folder / "summary-ar.txt"
    if summary_path.is_file() and not creative_plan.get("summary_ar"):
        creative_plan["summary_ar"] = summary_path.read_text(encoding="utf-8").strip()
    hook_path = folder / "thumbnail-hook-ar.txt"
    if hook_path.is_file():
        creative_plan["thumbnail_hook_ar"] = hook_path.read_text(encoding="utf-8").strip()
    from .source_led import clean_thumbnail_hook
    hook = clean_thumbnail_hook(creative_plan.get("thumbnail_hook_ar") or merged_manifest.get("thumbnail_hook_ar"))
    if hook:
        creative_plan["thumbnail_hook_ar"] = hook
        hook_path.write_text(hook + "\n", encoding="utf-8")

    # Extract Arabic title
    if title_path.exists():
        post_title_ar = title_path.read_text(encoding="utf-8").strip()
    elif creative_plan.get("voiceover", {}).get("title_ar"):
        post_title_ar = creative_plan["voiceover"]["title_ar"].strip()
    elif manifest_data.get("metadata", {}).get("title"):
        post_title_ar = manifest_data["metadata"]["title"].strip()
    else:
        post_title_ar = folder.name

    # Identify source thumbnail reference
    ref_candidates = [
        folder / "source_thumbnail.jpg",
        folder / "source_thumbnail.png",
        folder / "source_thumbnail.webp",
        folder / "source.jpg",
        folder / "source.webp",
        folder / "source.png",
    ]
    # Also check parent directory if in v2 subfolder
    if folder.name == "v2" and folder.parent.exists():
        ref_candidates.extend([
            folder.parent / "source_thumbnail.jpg",
            folder.parent / "source_thumbnail.png",
            folder.parent / "source_thumbnail.webp",
            folder.parent / "source.jpg",
            folder.parent / "source.webp",
            folder.parent / "source.png",
        ])

    ref_thumbnail = next((p for p in ref_candidates if p.is_file()), None)

    target_ref = folder / "source_thumbnail.jpg"
    # Preserve the real reference format instead of relabelling PNG/WebP as JPEG.

    # If reference thumbnail is not found, automatically retrieve it
    if not ref_thumbnail or not ref_thumbnail.exists():
        vid_id = manifest_data.get("metadata", {}).get("id") or manifest_data.get("metadata", {}).get("video_id")
        if not vid_id:
            src = manifest_data.get("source", "")
            from ..utils import youtube_video_id
            vid_id = youtube_video_id(src) if src else None

        if vid_id:
            import urllib.request
            for thumb_url in [
                f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg",
                f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg",
                f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg",
            ]:
                try:
                    req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status == 200:
                            content = resp.read()
                            # YouTube returns a tiny placeholder if maxres is missing
                            if len(content) > 2000:
                                target_ref.write_bytes(content)
                                ref_thumbnail = target_ref
                                break
                except Exception:
                    pass

        # Fallback: extract clear video frame from existing MP4 if still missing
        if not ref_thumbnail or not ref_thumbnail.exists():
            videos = list(folder.glob("*.mp4"))
            if not videos and folder.name == "v2" and folder.parent.exists():
                videos = list(folder.parent.glob("*.mp4"))
            if videos:
                import subprocess
                from ..media import find_ffmpeg
                try:
                    ffmpeg = find_ffmpeg()
                    cmd = [
                        str(ffmpeg), "-y",
                        "-ss", "00:00:02.000",
                        "-i", str(videos[0]),
                        "-frames:v", "1",
                        "-q:v", "2",
                        str(target_ref),
                    ]
                    subprocess.run(cmd, capture_output=True, check=True)
                    if target_ref.is_file():
                        ref_thumbnail = target_ref
                except Exception:
                    pass

    package = generate_thumbnail_package(
        post_title_ar=post_title_ar,
        manifest_data=manifest_data,
        creative_plan=creative_plan,
        reference_thumbnail_path=ref_thumbnail,
        style_preference=style_preference,
        archetype_preference=archetype_preference or kwargs.get("archetype_preference"),
    )

    saved_prompts = save_thumbnail_prompts(package, folder, include_facebook=include_facebook)

    if generate_kieai:
        client = ImageGeneratorClient()
        if client.is_api_configured:
            try:
                ref_image_url = None
                vid_id = (manifest_data or {}).get("metadata", {}).get("id") or (manifest_data or {}).get("metadata", {}).get("video_id")
                if not vid_id and (manifest_data or {}).get("source"):
                    from ..utils import youtube_video_id
                    vid_id = youtube_video_id(manifest_data["source"])
                if vid_id:
                    import urllib.request
                    for img_name in ("maxresdefault.jpg", "hqdefault.jpg"):
                        candidate = f"https://i.ytimg.com/vi/{vid_id}/{img_name}"
                        try:
                            req = urllib.request.Request(candidate, method="HEAD")
                            with urllib.request.urlopen(req, timeout=5) as r:
                                if r.status == 200:
                                    ref_image_url = candidate
                                    break
                        except Exception:
                            continue
                    if not ref_image_url:
                        ref_image_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                client.generate_kieai_thumbnails(
                    folder=folder,
                    fb_prompt=package.fb_master_prompt if include_facebook else None,
                    vert_prompt=package.vertical_master_prompt,
                    reference_image_url=ref_image_url,
                )
            except Exception as exc:
                raise RuntimeError(f"Thumbnail prompts saved, but KIE.ai image generation failed: {exc}") from exc
        else:
            raise RuntimeError("Thumbnail prompts saved, but KIE.ai image generation needs a configured API key.")

    return saved_prompts


__all__ = [
    "CuriosityVisualHint",
    "FocalArchetype",
    "ImageGeneratorClient",
    "STYLE_REGISTRY",
    "ThumbnailPackage",
    "VisualStyle",
    "extract_curiosity_visual_hint",
    "generate_thumbnail_package",
    "process_folder_thumbnails",
    "resolve_focal_archetype",
    "resolve_visual_style",
    "save_thumbnail_prompts",
]
