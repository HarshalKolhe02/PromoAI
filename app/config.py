"""
Application configuration for PromoFinder AI.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
DEMO_DIR = DATA_DIR / "demo"
RAW_AI_DIR = DATA_DIR / "raw_ai_responses"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure runtime directories exist
for path in [DATA_DIR, UPLOAD_DIR, OUTPUT_DIR, DEMO_DIR, RAW_AI_DIR, REPORTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env", override=True)


class Config:
    """Central configuration container for PromoFinder AI."""

    # AI Provider & Model
    AI_PROVIDER = os.getenv("AI_PROVIDER", "mock").lower()
    AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")
    
    # API Keys & Endpoints
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Model Generation Parameters
    AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))
    AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "120"))

    # Processing & Chunking
    MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "12000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "500"))

    # App Environment & Logging
    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Hard Duration Constraints for Promos (seconds)
    MIN_PROMO_DURATION = 20.0
    MAX_PROMO_DURATION = 60.0

    # Default Deterministic Scoring Weights (out of 100)
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "hook": 25.0,          # 2.5 multiplier
        "cliffhanger": 25.0,   # 2.5 multiplier
        "standalone": 20.0,    # 2.0 multiplier
        "emotional": 15.0,     # 1.5 multiplier
        "curiosity": 10.0,     # 1.0 multiplier
        "coherence": 5.0,      # 0.5 multiplier
    }

    @classmethod
    def get_api_key_for_provider(cls, provider: str) -> str:
        provider = provider.lower()
        if provider == "gemini":
            return cls.GEMINI_API_KEY
        elif provider == "openai":
            return cls.OPENAI_API_KEY
        elif provider == "anthropic":
            return cls.ANTHROPIC_API_KEY
        return ""
