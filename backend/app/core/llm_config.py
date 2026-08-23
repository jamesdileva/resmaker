"""LLM feature configuration (Sprint 30).

Runtime-toggleable config stored in ``data/llm_config.json`` so the
Settings page can flip the flag without a backend restart. Environment
variables provide defaults for a fresh install; the JSON file, when
present, wins over env so the user's saved choices persist.
"""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

CONFIG_FILENAME = "llm_config.json"
ENABLED_ENV_VAR = "CAREER_OS_LLM_ENABLED"
ENDPOINT_ENV_VAR = "CAREER_OS_LLM_ENDPOINT"
MODEL_ENV_VAR = "CAREER_OS_LLM_MODEL"


class LLMConfig(BaseModel):
    """Local LLM integration settings (feature-flagged, off by default)."""

    enabled: bool = False
    endpoint: str = Field(default="http://127.0.0.1:11434")
    model: str = "gemma2"
    max_tokens: int = Field(default=500, ge=1)
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)


def config_path() -> Path:
    """Location of the runtime config file (backend/data/llm_config.json)."""
    return (
        Path(__file__).resolve().parent.parent.parent / "data" / CONFIG_FILENAME
    )


def _env_defaults() -> LLMConfig:
    """Build the base config from environment variables."""
    enabled_raw = os.environ.get(ENABLED_ENV_VAR, "").strip().lower()
    enabled = enabled_raw in ("1", "true", "yes", "on")
    return LLMConfig(
        enabled=enabled,
        endpoint=os.environ.get(ENDPOINT_ENV_VAR, LLMConfig().endpoint),
        model=os.environ.get(MODEL_ENV_VAR, LLMConfig().model),
    )


def load_llm_config() -> LLMConfig:
    """Load the effective config: env defaults overridden by the JSON file.

    A missing, unreadable, or invalid file falls back to env defaults —
    a corrupt config file must never crash the backend.
    """
    config = _env_defaults()
    path = config_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        config = LLMConfig(**{**config.model_dump(), **raw})
    except (OSError, ValueError):
        pass
    return config


def save_llm_config(config: LLMConfig) -> None:
    """Persist the config to the runtime JSON file."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(config.model_dump(), indent=2) + "\n", encoding="utf-8"
    )


def llm_enabled() -> bool:
    """Convenience check used by the router registration gate."""
    return load_llm_config().enabled


def ollama_unreachable_detail(exc: Exception) -> str:
    """Human-readable detail for connection failures (used by the API)."""
    return f"Ollama unreachable at {load_llm_config().endpoint}: {exc}"
