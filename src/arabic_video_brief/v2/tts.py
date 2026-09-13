from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ..config import Settings

logger = logging.getLogger(__name__)

# Default pre-made multilingual voice (George / Conversational)
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"


def normalize_hook_text_for_tts(text: str) -> str:
    """
    Prepare Arabic hook text for natural, human-like cadence and delivery.
    Preserves micro-pauses (em-dashes, commas, ellipses) without robotic monotone pacing.
    """
    cleaned = text.strip()
    # Remove markdown asterisks, backticks, hashes, etc.
    cleaned = re.sub(r"[*_#`~]+", "", cleaned)
    # Remove hashtags and leading bullet dashes
    cleaned = re.sub(r"#\S+", "", cleaned)
    cleaned = re.sub(r"^[-–—•\s]+", "", cleaned)
    # Convert standard commas to natural pause commas/ellipses for punchy micro-pauses
    cleaned = re.sub(r"\s*([،,])\s*", "، ", cleaned)
    cleaned = re.sub(r"\s*[-–—]\s*", " — ", cleaned)
    cleaned = re.sub(r"\s*\.\.\.\s*", "... ", cleaned)
    # Clean up double spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Ensure natural terminal punctuation
    if not re.search(r"[.!?؟…]$", cleaned):
        cleaned = f"{cleaned}."
    return cleaned.strip()


def generate_hook_tts(
    hook_text: str,
    output_path: Path,
    settings: Settings,
    ffmpeg_bin: str,
) -> dict[str, Any]:
    """
    Synthesizes the Arabic hook via ElevenLabs TTS per Elevenlabs.md specifications:
    - Target voice: Dey7SsJGQxe5rLi7TlDb (or ELEVENLABS_VOICE_ID from .env)
    - Payload settings:
        model_id: "eleven_multilingual_v2"
        voice_settings:
          stability: 0.38
          similarity_boost: 0.80
          style: 0.28
          use_speaker_boost: true
    - Dynamic duration: preserves authentic cadence without artificial speed compression.
    - Graceful fallback: retries with pre-made voice if library voice encounters plan restrictions (402).
    """
    api_key = settings.elevenlabs_api_key
    if not api_key:
        return {
            "status": "fallback",
            "reason": "ELEVENLABS_API_KEY is not configured",
            "audio_path": None,
            "duration": 0.0,
        }

    import random

    pool = settings.elevenlabs_voice_pool
    if pool and len(pool) > 1:
        voice_id = random.choice(pool)
    else:
        voice_id = settings.elevenlabs_voice_id or DEFAULT_VOICE_ID

    model_id = settings.elevenlabs_model_id
    language_code = settings.elevenlabs_language_code
    logger.info("Selected ElevenLabs voice for V2 voiceover: %s (from pool of %d)", voice_id, len(pool) if pool else 1)

    tts_prompt = normalize_hook_text_for_tts(hook_text)

    # Voice settings precisely matching Elevenlabs.md
    voice_settings = {
        "stability": 0.38,
        "similarity_boost": 0.80,
        "style": 0.28,
        "use_speaker_boost": True,
    }

    payload = {
        "text": tts_prompt,
        "model_id": model_id,
        "language_code": language_code,
        "voice_settings": voice_settings,
    }

    def _call_elevenlabs(vid: str) -> bytes:
        endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
                "User-Agent": "ArabicVideoBrief/2.0",
            },
        )
        with urllib.request.urlopen(req, timeout=35) as resp:
            return resp.read()

    active_voice_id = voice_id
    audio_bytes: bytes | None = None
    try:
        active_voice_id = voice_id
        audio_bytes = _call_elevenlabs(active_voice_id)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="ignore")[:300]
        logger.warning("ElevenLabs request for voice %s failed (HTTP %s: %s)", active_voice_id, err.code, body)
        if active_voice_id != DEFAULT_VOICE_ID:
            logger.info("Retrying ElevenLabs TTS with default pre-made voice %s...", DEFAULT_VOICE_ID)
            try:
                active_voice_id = DEFAULT_VOICE_ID
                audio_bytes = _call_elevenlabs(active_voice_id)
            except Exception as retry_err:
                safe_msg = f"ElevenLabs retry error: {retry_err}"
                logger.warning(safe_msg)
                return {
                    "status": "fallback",
                    "reason": safe_msg,
                    "audio_path": None,
                    "duration": 0.0,
                }
        else:
            return {
                "status": "fallback",
                "reason": f"ElevenLabs HTTP {err.code}: {body}",
                "audio_path": None,
                "duration": 0.0,
            }
    except Exception as err:
        logger.warning("ElevenLabs connection error: %s; falling back to visual hook", err)
        return {
            "status": "fallback",
            "reason": f"Connection error: {err}",
            "audio_path": None,
            "duration": 0.0,
        }

    if not audio_bytes:
        return {
            "status": "fallback",
            "reason": "No audio bytes received from ElevenLabs",
            "audio_path": None,
            "duration": 0.0,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as raw_file:
        raw_path = Path(raw_file.name)
        raw_path.write_bytes(audio_bytes)

    try:
        # Probe raw audio duration
        probe_cmd = [
            ffmpeg_bin, "-hide_banner", "-i", str(raw_path),
        ]
        proc = subprocess.run(probe_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
        raw_duration = 0.0
        if m:
            raw_duration = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

        # Dynamic Cadence: trim leading/trailing dead silence and normalize loudness.
        # Do NOT artificially compress into <2.4s. Keep natural duration (2.0s - 8.0s) per Elevenlabs.md
        filter_chain: list[str] = [
            "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-40dB:detection=peak",
            "areverse",
            "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-40dB:detection=peak",
            "areverse",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
        ]

        process_cmd = [
            ffmpeg_bin, "-hide_banner", "-loglevel", "error",
            "-i", str(raw_path),
            "-filter_complex", ",".join(filter_chain),
            "-c:a", "libmp3lame", "-b:a", "192k",
            "-y", str(output_path),
        ]
        subprocess.run(process_cmd, check=True, capture_output=True, timeout=30)

        # Probe final duration
        proc_final = subprocess.run([ffmpeg_bin, "-hide_banner", "-i", str(output_path)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        mf = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc_final.stderr)
        final_duration = 0.0
        if mf:
            final_duration = int(mf.group(1)) * 3600 + int(mf.group(2)) * 60 + float(mf.group(3))

        return {
            "status": "success",
            "audio_path": str(output_path),
            "raw_duration": raw_duration,
            "duration": final_duration,
            "voice_id": active_voice_id,
            "model_id": model_id,
        }
    except Exception as err:
        logger.warning("FFmpeg audio post-processing failed for TTS: %s; falling back to visual hook", err)
        return {
            "status": "fallback",
            "reason": f"Post-processing failed: {err}",
            "audio_path": None,
            "duration": 0.0,
        }
    finally:
        try:
            if raw_path.exists():
                raw_path.unlink()
        except OSError:
            pass
