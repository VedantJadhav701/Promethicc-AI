"""Application configuration loaded from experts.yaml and environment variables."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_YAML_PATH = Path(__file__).parent / "experts.yaml"


class ExpertConfig(BaseModel):
    """Schema for a single expert definition.

    Attributes:
        label: Human-readable display name.
        risk_tier: 'standard' or 'high_stakes'.
        system_prompt: Full system prompt injected at inference time.
        rag_namespace: Supabase pgvector namespace for RAG retrieval.
    """

    label: str
    risk_tier: Literal["standard", "high_stakes"]
    system_prompt: str
    rag_namespace: str


class Settings(BaseSettings):
    """Environment-driven application settings.

    All values are read from a .env file or OS environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    MODEL_PATH: str = "./models/model.gguf"

    ONLINE_API_KEY: str = ""
    ONLINE_API_URL: str = "https://api.groq.com/openai/v1"
    ONLINE_MODEL: str = "llama-3.1-8b-instant"

    DAILY_OFFLINE_CAP: int = 50
    RATE_LIMIT_WINDOW_HOURS: int = 24
    MODEL_MAX_TOKENS: int = 512
    MODEL_CONTEXT_SIZE: int = 2048


def _load_experts(path: Path) -> dict[str, ExpertConfig]:
    """Parse experts.yaml into validated ExpertConfig instances.

    Args:
        path: Filesystem path to the YAML file.

    Returns:
        Mapping of expert slug to its configuration.
    """
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    loaded: dict[str, ExpertConfig] = {}
    for slug, data in raw.get("experts", {}).items():
        loaded[slug] = ExpertConfig(**data)

    logger.info("Loaded %d expert definitions from %s", len(loaded), path)
    return loaded


settings = Settings()
experts: dict[str, ExpertConfig] = _load_experts(_YAML_PATH)
