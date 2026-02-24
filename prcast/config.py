"""PRCast configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM Provider: "openai", "gemini", or "anthropic"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")

    # Provider API Keys (only the active provider's key is required)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))

    # TTS
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "edge")  # "edge" or "elevenlabs"
    HOST_A_VOICE: str = os.getenv("HOST_A_VOICE", "en-US-AndrewMultilingualNeural")
    HOST_A_NAME: str = os.getenv("HOST_A_NAME", "Alex")

    # Kept for future two-host support
    HOST_B_VOICE: str = os.getenv("HOST_B_VOICE", "en-US-JennyNeural")
    HOST_B_NAME: str = os.getenv("HOST_B_NAME", "Sam")

    # Output
    AUDIO_DIR: Path = Path(os.getenv("AUDIO_DIR", "./audio"))
    FEEDS_DIR: Path = Path(os.getenv("FEEDS_DIR", "./feeds"))
    BASE_URL: str = os.getenv("BASE_URL", "https://fraga.github.io/prcast")

    # Podcast metadata
    PODCAST_TITLE: str = os.getenv("PODCAST_TITLE", "PRCast")
    PODCAST_DESCRIPTION: str = os.getenv(
        "PODCAST_DESCRIPTION",
        "AI-generated podcast episodes from Pull Requests"
    )
    PODCAST_AUTHOR: str = os.getenv("PODCAST_AUTHOR", "PRCast")
    PODCAST_EMAIL: str = os.getenv("PODCAST_EMAIL", "")
    PODCAST_LANGUAGE: str = os.getenv("PODCAST_LANGUAGE", "en")
    PODCAST_CATEGORY: str = os.getenv("PODCAST_CATEGORY", "Technology")
    PODCAST_IMAGE: str = os.getenv("PODCAST_IMAGE", "")

    def __init__(self):
        self.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        self.FEEDS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
