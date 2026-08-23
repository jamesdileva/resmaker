"""LLM polish endpoints (Sprint 30, feature-flagged).

The router is only registered when the LLM feature flag is enabled, per
the sprint plan; config management lives here too so the Settings page
can flip the flag without restarting the backend.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.exceptions import ValidationAppError
from app.core.llm_config import (
    LLMConfig,
    load_llm_config,
    save_llm_config,
)
from app.services.llm_service import LLMPolishError, LLMService

router = APIRouter(prefix="/llm", tags=["llm"])


class PolishRequest(BaseModel):
    """Payload for grammar/transition polish requests."""

    text: str = Field(min_length=1)
    mode: str = "grammar"


class KeywordRequest(BaseModel):
    """Payload for keyword expansion requests."""

    query: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=20)


class SuggestionOut(BaseModel):
    """One filtered polish suggestion (diff pair + explanation)."""

    original: str
    replacement: str
    type: str
    reason: str = ""


def _service() -> LLMService:
    return LLMService()


def _ensure_enabled() -> None:
    """403 while the feature flag is off (runtime-toggleable in Settings)."""
    if not load_llm_config().enabled:
        error = ValidationAppError(
            "LLM polish is disabled — enable it in Settings"
        )
        error.status_code = 403
        raise error


@router.get("/config", response_model=LLMConfig)
def get_llm_config() -> LLMConfig:
    """Return the effective LLM configuration."""
    return load_llm_config()


@router.put("/config", response_model=LLMConfig)
def update_llm_config(config: LLMConfig) -> LLMConfig:
    """Persist new LLM configuration (enable/disable, endpoint, model)."""
    save_llm_config(config)
    return load_llm_config()


@router.post("/grammar", response_model=list[SuggestionOut])
def polish_grammar(payload: PolishRequest) -> list[SuggestionOut]:
    """Grammar/punctuation suggestions for *payload.text*."""
    _ensure_enabled()
    return _polish(payload.text, "grammar")


@router.post("/transitions", response_model=list[SuggestionOut])
def polish_transitions(payload: PolishRequest) -> list[SuggestionOut]:
    """Transition-improvement suggestions for *payload.text*."""
    _ensure_enabled()
    return _polish(payload.text, "transitions")


@router.post("/keywords", response_model=list[str])
def expand_keywords(payload: KeywordRequest) -> list[str]:
    """Keyword synonyms/phrases related to *payload.query*."""
    _ensure_enabled()
    try:
        return _service().keyword_expansion(payload.query, payload.limit)
    except LLMPolishError as exc:
        raise ValidationAppError(str(exc)) from exc


def _polish(text: str, mode: str) -> list[SuggestionOut]:
    try:
        suggestions = _service().polish(text, mode=mode)
    except ValueError as exc:
        raise ValidationAppError(str(exc)) from exc
    except LLMPolishError as exc:
        raise ValidationAppError(str(exc)) from exc
    return [SuggestionOut(**s.__dict__) for s in suggestions]
