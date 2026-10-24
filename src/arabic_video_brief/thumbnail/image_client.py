from __future__ import annotations

import json
import logging
import os
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image

from .sanitizer import sanitize_image

logger = logging.getLogger(__name__)


def get_kieai_api_key() -> str | None:
    api_key = os.getenv("KIEAI_API_KEY")
    if not api_key:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("KIEAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return api_key


class ImageGeneratorClient:
    """Client for automated image generation via KIE.ai API (GPT Image 2.5 Sunburst)."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_kieai_api_key()

    @property
    def is_api_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def check_existing_covers(self, folder: Path) -> dict[str, Path | None]:
        """Checks if manual or generated cover images exist in the folder."""
        fb_candidates = [
            folder / "cover_facebook_4x5.png",
            folder / "cover_facebook_4x5.jpg",
            folder / "cover_facebook_4x5.jpeg",
            folder / "cover_facebook_4x5.webp",
        ]
        vert_candidates = [
            folder / "cover_vertical_9x16.png",
            folder / "cover_vertical_9x16.jpg",
            folder / "cover_vertical_9x16.jpeg",
            folder / "cover_vertical_9x16.webp",
        ]

        fb_cover = next((p for p in fb_candidates if p.is_file()), None)
        vert_cover = next((p for p in vert_candidates if p.is_file()), None)

        return {
            "facebook_4x5": fb_cover,
            "vertical_9x16": vert_cover,
        }

    def generate_kieai_thumbnails(
        self,
        folder: Path,
        fb_prompt: str,
        vert_prompt: str,
        reference_image_url: str | None = None,
        timeout_seconds: int = 500,
    ) -> dict[str, Path]:
        """
        Submits full master prompts for 4:5 FB and 9:16 Vertical covers to KIE.ai API,
        polls until completion (~360s), downloads, crops/resizes, and sanitizes AI metadata.
        """
        if not self.is_api_configured:
            raise RuntimeError(
                "KIEAI_API_KEY not configured in .env! "
                "Add KIEAI_API_KEY=<your_key> to .env or generate thumbnails manually."
            )

        # Resolve public YouTube reference URL if not provided
        if not reference_image_url:
            manifest_file = folder / "manifest.json"
            if not manifest_file.exists() and folder.name == "v2" and folder.parent.exists():
                manifest_file = folder.parent / "manifest.json"

            vid_id = None
            if manifest_file.exists():
                try:
                    data = json.loads(manifest_file.read_text(encoding="utf-8"))
                    vid_id = data.get("metadata", {}).get("id") or data.get("metadata", {}).get("video_id")
                    if not vid_id and data.get("source"):
                        from ..utils import youtube_video_id
                        vid_id = youtube_video_id(data["source"])
                except Exception:
                    pass

            if vid_id:
                # Prefer maxresdefault, verify or fallback to hqdefault
                maxres_url = f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg"
                hq_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                try:
                    req_test = urllib.request.Request(maxres_url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
                    with urllib.request.urlopen(req_test, timeout=5) as resp:
                        reference_image_url = maxres_url if resp.status == 200 else hq_url
                except Exception:
                    reference_image_url = hq_url
            else:
                raise ValueError(
                    "No source thumbnail URL is available. Supply this episode's original reference "
                    "or use the saved manual prompts with its local image; unrelated fallback images are not allowed."
                )

        create_url = "https://api.kie.ai/api/v1/jobs/createTask"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Submit tasks
        tasks = {}

        def _submit(payload: dict[str, Any]) -> str:
            req = urllib.request.Request(
                create_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("code") == 200 and res.get("data", {}).get("taskId"):
                    return res["data"]["taskId"]
                raise RuntimeError(f"KIE.ai submission failed: {res}")

        # 1. Submit Facebook (3:4 -> 4:5) task ONLY if fb_prompt is provided
        if fb_prompt and str(fb_prompt).strip():
            payload_fb = {
                "model": "gpt-image-2-5-sunburst-image-to-image",
                "input": {
                    "prompt": fb_prompt,
                    "input_urls": [reference_image_url],
                    "aspect_ratio": "3:4",
                    "resolution": "1K",
                    "background": "opaque",
                },
            }
            logger.info("[KIE.ai] Submitting Facebook 4:5 thumbnail task...")
            fb_task_id = _submit(payload_fb)
            tasks["facebook"] = fb_task_id
            logger.info("[KIE.ai] Facebook task submitted: %s", fb_task_id)
        else:
            logger.info("[KIE.ai] Facebook 4:5 thumbnail skipped (no deep-dive summary requested, saving credits).")

        # 2. Submit Vertical (9:16) task
        payload_vert = {
            "model": "gpt-image-2-5-sunburst-image-to-image",
            "input": {
                "prompt": vert_prompt,
                "input_urls": [reference_image_url],
                "aspect_ratio": "9:16",
                "resolution": "1K",
                "background": "opaque",
            },
        }
        logger.info("[KIE.ai] Submitting Vertical 9:16 thumbnail task...")
        vert_task_id = _submit(payload_vert)
        tasks["vertical"] = vert_task_id
        logger.info("[KIE.ai] Vertical task submitted: %s", vert_task_id)

        # Poll until active tasks complete
        results_urls: dict[str, str] = {}
        start_time = time.time()

        while len(results_urls) < len(tasks):
            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"KIE.ai generation timed out after {timeout_seconds} seconds")

            for name, tid in tasks.items():
                if name in results_urls:
                    continue
                info_url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}"
                req = urllib.request.Request(info_url, headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        d = json.loads(resp.read().decode("utf-8")).get("data", {})
                except Exception as err:
                    logger.debug("[KIE.ai] Poll check warning: %s", err)
                    continue

                state = d.get("state")
                if state == "success":
                    urls = []
                    if d.get("resultJson"):
                        try:
                            urls = json.loads(d["resultJson"]).get("resultUrls", [])
                        except Exception:
                            pass
                    elif d.get("response", {}).get("resultUrls"):
                        urls = d["response"]["resultUrls"]
                    if urls:
                        results_urls[name] = urls[0]
                        logger.info("[KIE.ai] Task %s (%s) finished successfully!", name, tid)
                elif state in ("fail", "failed", "error"):
                    fail_msg = d.get("failMsg") or d.get("errMsg") or "Unknown error"
                    raise RuntimeError(f"KIE.ai task {tid} ({name}) failed: {fail_msg}")

            if len(results_urls) < len(tasks):
                time.sleep(12)

        output_dict: dict[str, Path] = {}

        # Download, format, and sanitize Facebook 4:5 if requested
        if "facebook" in results_urls:
            dest_fb = folder / "cover_facebook_4x5.png"
            raw_fb_p = folder / "raw_kie_facebook_3x4.png"
            req_fb = urllib.request.Request(results_urls["facebook"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_fb, timeout=60) as resp:
                raw_fb_p.write_bytes(resp.read())
            im_fb = Image.open(raw_fb_p)
            scaled_fb = im_fb.resize((1080, 1440), Image.Resampling.LANCZOS)
            cropped_fb = scaled_fb.crop((0, 45, 1080, 1440 - 45))
            cropped_fb.save(dest_fb, "PNG")
            sanitize_image(dest_fb, force=True)
            output_dict["facebook_4x5"] = dest_fb
            if folder.name == "v2" and folder.parent.exists():
                shutil.copyfile(str(dest_fb), str(folder.parent / dest_fb.name))

        # Download, format, and sanitize Vertical 9:16
        if "vertical" in results_urls:
            dest_vert = folder / "cover_vertical_9x16.png"
            dest_yt = folder / "cover_vertical_9x16_yt_opt.jpg"
            raw_vert_p = folder / "raw_kie_vertical_9x16.png"
            req_vert = urllib.request.Request(results_urls["vertical"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_vert, timeout=60) as resp:
                raw_vert_p.write_bytes(resp.read())
            im_vert = Image.open(raw_vert_p)
            im_vert_resized = im_vert.resize((1080, 1920), Image.Resampling.LANCZOS)
            im_vert_resized.save(dest_vert, "PNG")
            im_vert_resized.convert("RGB").save(dest_yt, "JPEG", quality=90, optimize=True)
            sanitize_image(dest_vert, force=True)
            sanitize_image(dest_yt, force=True)
            output_dict["vertical_9x16"] = dest_vert
            output_dict["youtube_opt"] = dest_yt
            if folder.name == "v2" and folder.parent.exists():
                shutil.copyfile(str(dest_vert), str(folder.parent / dest_vert.name))
                shutil.copyfile(str(dest_yt), str(folder.parent / dest_yt.name))

        logger.info("[KIE.ai] Thumbnails formatted and sanitized successfully: %s", list(output_dict.keys()))
        return output_dict
