from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env.local"
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "bookings.db"

load_dotenv(ENV_FILE)


class MissingConfigError(RuntimeError):
    pass


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise MissingConfigError(
            f"Missing required environment variable '{key}'. Add it to {ENV_FILE}."
        )
    return value


@dataclass(frozen=True)
class Settings:
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    deepgram_api_key: str
    groq_api_key: str
    stt_model: str
    tts_model: str
    llm_model: str
    business_name: str
    timezone: str

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            livekit_url=_require("LIVEKIT_URL"),
            livekit_api_key=_require("LIVEKIT_API_KEY"),
            livekit_api_secret=_require("LIVEKIT_API_SECRET"),
            deepgram_api_key=_require("DEEPGRAM_API_KEY"),
            groq_api_key=_require("GROQ_API_KEY"),
            stt_model=os.getenv("STT_MODEL", "nova-3"),
            tts_model=os.getenv("TTS_MODEL", "aura-2-andromeda-en"),
            llm_model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
            business_name=os.getenv("BUSINESS_NAME", "Bright Smile Dental"),
            timezone=os.getenv("BUSINESS_TIMEZONE", "America/New_York"),
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def __getattr__(name: str) -> Settings:
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
