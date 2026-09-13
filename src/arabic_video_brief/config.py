from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(('"', "'")):
            quote_char = value[0]
            closing_idx = value.find(quote_char, 1)
            if closing_idx != -1:
                value = value[1:closing_idx]
            else:
                value = value.strip(quote_char)
        else:
            for sep in (" #", "\t#"):
                if sep in value:
                    value = value.split(sep, 1)[0].strip()
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    width: int = 1080
    height: int = 1920
    top_height: int = 760
    fps: int = 30
    duration: float = 28.0
    thumbnail_duration: float = 5.0
    page_duration: float = 10.0
    cta_duration: float = 8.0
    summary_min_words: int = 140
    summary_max_words: int = 160
    page_min_words: int = 70
    page_max_words: int = 80
    font_size: int = 46
    min_font_size: int = 32
    text_offset_ratio: float = 0.06  # 6% (~65px) left shift to clear right-side social icons
    gemini_model: str = "gemini-3.8-flash"
    seekai_model: str = "deepseek-v4-flash"
    vyceai_model: str = "gpt-5.6-luna"
    apinex_model: str = "free/gemini-3.8-flash"
    music_volume: float = 0.85
    music_fade_out: float = 2.0

    # V2 Configuration (36.5-second timeline: hook 2.5s + 4 pages [9s + 3*6.5s] + conclusion 8.0s)
    duration_v2: float = 36.5
    hook_duration: float = 2.5
    page_duration_v2: float = 6.5
    conclusion_duration: float = 8.0
    page_v2_min_words: int = 30
    page_v2_max_words: int = 44
    music_duck_volume: float = 0.35  # ~6-8 dB ducking during hook narration

    @property
    def gemini_api_key(self) -> str | None:
        return os.environ.get("GEMINI_API_KEY") or None

    @property
    def seekai_api_key(self) -> str | None:
        return os.environ.get("Seekai_api") or os.environ.get("SEEKAI_API_KEY") or None

    @property
    def seekai_base_url(self) -> str:
        return os.environ.get("SEEKAI_BASE_URL", "https://seekai.cc/v1")

    @property
    def vyceai_api_key(self) -> str | None:
        return os.environ.get("VyceAI_api") or os.environ.get("VYCEAI_API_KEY") or None

    @property
    def vyceai_base_url(self) -> str:
        return os.environ.get("VYCEAI_BASE_URL", "https://vyceai.com/v1")

    @property
    def apinex_api_key(self) -> str | None:
        return os.environ.get("APINEX_API_KEY") or os.environ.get("Apinex_api") or None

    @property
    def apinex_base_url(self) -> str:
        return os.environ.get("APINEX_BASE_URL", "https://api.apinex.bond/v1")

    @property
    def llm_provider(self) -> str:
        explicit = os.environ.get("LLM_PROVIDER")
        if explicit:
            return explicit.lower()
        if self.gemini_api_key:
            return "gemini"
        if self.vyceai_api_key:
            return "vyceai"
        if self.apinex_api_key:
            return "apinex"
        return "gemini"

    @property
    def youtube_api_key(self) -> str | None:
        return os.environ.get("YOUTUBE_API_KEY") or None

    @property
    def font_path(self) -> Path:
        override = os.environ.get("ARABIC_VIDEO_BRIEF_FONT")
        if override:
            return Path(override)
        return PROJECT_ROOT / "assets" / "NotoSansArabic-SemiBold.ttf"

    @property
    def music_dir(self) -> Path:
        override = os.environ.get("ARABIC_VIDEO_BRIEF_MUSIC_DIR")
        if override:
            return Path(override)
        return PROJECT_ROOT / "assets" / "music"

    @property
    def elevenlabs_api_key(self) -> str | None:
        return os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("Elevenlabs_api") or os.environ.get("ELEVENLABS_API") or None

    @property
    def elevenlabs_voice_id(self) -> str:
        return os.environ.get("ELEVENLABS_VOICE_ID") or "ErXwobaYiN019PkySvjV"

    @property
    def elevenlabs_voice_pool(self) -> list[str]:
        raw = os.environ.get("ELEVENLABS_VOICE_POOL")
        if raw:
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            if parts:
                return parts
        return ["ErXwobaYiN019PkySvjV", "TX3LPaxmHKxFdv7VOQHJ", "JBFqnCBsd6RMkjVDRZzb"]

    @property
    def elevenlabs_model_id(self) -> str:
        return os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

    @property
    def elevenlabs_language_code(self) -> str:
        return os.environ.get("ELEVENLABS_LANGUAGE_CODE", "ar")

    @property
    def brand_avatar_path(self) -> Path:
        return PROJECT_ROOT / "assets" / "brand" / "profile_avatar.jpg"

    @property
    def brand_frame_path(self) -> Path:
        return PROJECT_ROOT / "assets" / "brand" / "prussian_airbrush_frame.png"

    @property
    def outro_voiceover_path(self) -> Path:
        override = os.environ.get("ARABIC_VIDEO_BRIEF_OUTRO_VOICEOVER")
        if override:
            return Path(override)
        return PROJECT_ROOT / "assets" / "music" / "last voicever.mp3"

    @property
    def output_dir(self) -> Path:
        return PROJECT_ROOT / "outputs"


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
        seekai_model=os.environ.get("SEEKAI_MODEL", "deepseek-v4-flash"),
        vyceai_model=os.environ.get("VyceAI_Model") or os.environ.get("VYCEAI_MODEL", "gpt-5.6-luna"),
        apinex_model=os.environ.get("APINEX_MODEL", "free/gemini-3.8-flash"),
    )

