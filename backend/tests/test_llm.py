"""Sprint 30 — LLM polish service, safety filter, and API tests.

All model interaction is faked via an injectable httpx-compatible client;
no live Ollama is needed for the suite (live verification lives in
scripts/verify_sprint30.py). Config and audit paths are redirected into
tmp so tests never touch backend/data or backend/logs.
"""

import json
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.v1.llm as llm_api
from app.core import llm_config
from app.services.llm_service import (
    LLMPolishError,
    LLMSuggestion,
    LLMService,
)


# ----------------------------------------------------------------- helpers


class _FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeOllama:
    """httpx.Client stand-in returning canned assistant content."""

    def __init__(self, content: str | list[str]):
        self.contents = content if isinstance(content, list) else [content]
        self.calls: list[dict] = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "payload": json})
        content = self.contents[min(len(self.calls) - 1, len(self.contents) - 1)]
        return _FakeResponse({"message": {"role": "assistant", "content": content}})


def _suggestions_payload(*suggestions):
    return json.dumps({"suggestions": list(suggestions)})


@pytest.fixture()
def llm_env(tmp_path, monkeypatch):
    """Redirect config + audit paths into tmp; default config disabled."""
    monkeypatch.setattr(llm_config, "config_path", lambda: tmp_path / "llm_config.json")
    monkeypatch.delenv(llm_config.ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(llm_config.ENDPOINT_ENV_VAR, raising=False)
    monkeypatch.delenv(llm_config.MODEL_ENV_VAR, raising=False)
    audit_path = tmp_path / "logs" / "llm_audit.log"
    yield {"audit_path": audit_path, "tmp_path": tmp_path}


def _service(env, client=None) -> LLMService:
    return LLMService(audit_path=Path(env["audit_path"]), client=client)


def _read_audit(env) -> list[dict]:
    path = Path(env["audit_path"])
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


# ------------------------------------------------------------------ config


def test_config_defaults_disabled(llm_env):
    config = llm_config.load_llm_config()
    assert config.enabled is False
    assert config.endpoint == "http://127.0.0.1:11434"
    assert config.model == "gemma2"


def test_config_env_overrides(llm_env, monkeypatch):
    monkeypatch.setenv(llm_config.ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(llm_config.ENDPOINT_ENV_VAR, "http://localhost:9999")
    monkeypatch.setenv(llm_config.MODEL_ENV_VAR, "llama3.1")
    config = llm_config.load_llm_config()
    assert config.enabled is True
    assert config.endpoint == "http://localhost:9999"
    assert config.model == "llama3.1"


def test_config_file_round_trip_and_corrupt_fallback(llm_env):
    saved = llm_config.LLMConfig(enabled=True, model="gemma2", temperature=0.2)
    llm_config.save_llm_config(saved)
    loaded = llm_config.load_llm_config()
    assert loaded.enabled is True
    assert loaded.temperature == 0.2

    llm_config.config_path().write_text("{not json", encoding="utf-8")
    fallback = llm_config.load_llm_config()
    assert fallback.enabled is False  # env defaults win when file is corrupt


# ------------------------------------------------------------------ filter


SOURCE = (
    "Processed over 50 confidential records weekly while resolving "
    "customer complaints at Acme Corp."
)


def _svc(llm_env, client=None) -> LLMService:
    return _service(llm_env, client)


def test_filter_accepts_pure_grammar_fix(llm_env):
    result = _svc(llm_env).filter_factual_changes(
        SOURCE,
        [
            LLMSuggestion(
                original="Processed over 50 confidential records weekly while",
                replacement=(
                    "Processed more than 50 confidential records per week while"
                ),
                type="grammar",
                reason="wording",
            )
        ],
    )
    assert len(result.accepted) == 1
    assert not result.rejected


def test_filter_rejects_invented_numbers(llm_env):
    result = _svc(llm_env).filter_factual_changes(
        SOURCE,
        [
            LLMSuggestion(
                original="Processed over 50 confidential records",
                replacement="Processed over 500 confidential records",
                type="grammar",
            )
        ],
    )
    assert not result.accepted
    assert "numbers" in result.rejected[0][1]


def test_filter_rejects_mid_sentence_proper_nouns(llm_env):
    result = _svc(llm_env).filter_factual_changes(
        SOURCE,
        [
            LLMSuggestion(
                original="resolving customer complaints",
                replacement="resolving customer complaints at Globex Industries",
                type="grammar",
            )
        ],
    )
    assert not result.accepted
    assert "proper nouns" in result.rejected[0][1]


def test_filter_allows_sentence_initial_transition_words(llm_env):
    result = _svc(llm_env).filter_factual_changes(
        SOURCE,
        [
            LLMSuggestion(
                original=("Processed over 50 confidential records weekly while resolving customer complaints"),
                replacement=(
                    "Additionally, processed over 50 confidential records weekly while resolving complaints"
                ),
                type="transition",
            )
        ],
    )
    assert len(result.accepted) == 1


def test_filter_rejects_length_explosion(llm_env):
    filler = " and demonstrated exceptional dedication every single day"
    result = _svc(llm_env).filter_factual_changes(
        SOURCE,
        [
            LLMSuggestion(
                original="resolving customer complaints",
                replacement="resolving customer complaints" + filler * 3,
                type="grammar",
            )
        ],
    )
    assert not result.accepted
    assert "length grows" in result.rejected[0][1]


def test_filter_rejects_unanchored_original(llm_env):
    result = _svc(llm_env).filter_factual_changes(
        SOURCE,
        [
            LLMSuggestion(
                original="Led a team of twelve engineers",
                replacement="Led a team of engineers",
                type="grammar",
            )
        ],
    )
    assert not result.accepted
    assert "anchor not found" in result.rejected[0][1]


# ------------------------------------------------------- service round-trip


GOOD_PAYLOAD = _suggestions_payload(
    {
        "original": "resolving customer complaints",
        "replacement": "resolving customer escalations",
        "type": "grammar",
        "reason": "stronger verb phrase",
    },
    {
        # filtered: invented number
        "original": "over 50 confidential records",
        "replacement": "over 150 confidential records",
        "type": "grammar",
        "reason": "more impressive",
    },
)


def test_polish_returns_only_filtered_suggestions_and_audits(llm_env):
    ollama = FakeOllama(GOOD_PAYLOAD)
    suggestions = _svc(llm_env, client=ollama).polish(SOURCE, mode="grammar")
    assert [s.replacement for s in suggestions] == ["resolving customer escalations"]
    # system prompt + strict rules travel with every request
    sent = ollama.calls[0]["payload"]
    system_message = sent["messages"][0]["content"]
    assert "NEVER add, remove, or alter factual information" in system_message
    assert sent["format"] == "json"
    entries = _read_audit(llm_env)
    assert entries and entries[0]["accepted_count"] == 1
    assert entries[0]["rejected"][0]["reason"].startswith("introduces numbers")


def test_polish_rejects_malformed_model_json(llm_env):
    ollama = FakeOllama("Here are my thoughts: definitely, sure, sounds good!")
    with pytest.raises(LLMPolishError, match="invalid JSON"):
        _svc(llm_env, client=ollama).polish(SOURCE)
    errors = _read_audit(llm_env)
    assert errors and "invalid JSON" in errors[0]["error"]


def test_polish_surfaces_unreachable_endpoint(llm_env):
    class DownClient:
        def post(self, *a, **k):
            raise httpx.ConnectError("connection refused")

    with pytest.raises(LLMPolishError, match="Ollama unreachable"):
        _svc(llm_env, client=DownClient()).polish(SOURCE)


def test_polish_rejects_unknown_mode(llm_env):
    with pytest.raises(ValueError, match="mode"):
        _svc(llm_env).polish(SOURCE, mode="vibes")


def test_keyword_expansion_parses_and_caps(llm_env):
    ollama = FakeOllama(json.dumps({"keywords": ["claims", "disputes", "", "fraud"]}))
    keywords = _svc(llm_env, client=ollama).keyword_expansion(
        "workers compensation claims", limit=5
    )
    assert keywords == ["claims", "disputes", "fraud"]


# ---------------------------------------------------------------------- api


@pytest.fixture()
def llm_app(llm_env, monkeypatch):
    """Standalone FastAPI app mounting only the LLM router (flag on)."""
    from fastapi.responses import JSONResponse

    from app.core.exceptions import AppError

    llm_config.save_llm_config(llm_config.LLMConfig(enabled=True))
    application = FastAPI()
    application.include_router(llm_api.router, prefix="/api/v1")

    @application.exception_handler(AppError)
    async def app_error_handler(request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message})

    return TestClient(application)


def test_api_default_install_gates_llm_surface(client, monkeypatch, tmp_path):
    """Routes are always mounted (runtime toggle), but polish endpoints
    answer 403 while the flag is off — unusable without explicit opt-in."""
    monkeypatch.setattr(
        llm_config, "config_path", lambda: tmp_path / "llm_config.json"
    )
    from app.main import app as real_app

    assert any("/api/v1/llm" in path for path in real_app.openapi()["paths"])
    response = client.post("/api/v1/llm/grammar", json={"text": SOURCE})
    if llm_config.llm_enabled():
        assert response.status_code != 403
    else:
        assert response.status_code == 403


def test_api_grammar_endpoint_filters(llm_app, llm_env, monkeypatch):
    ollama = FakeOllama(GOOD_PAYLOAD)

    def fake_service():
        return LLMService(audit_path=Path(llm_env["audit_path"]), client=ollama)

    monkeypatch.setattr(llm_api, "_service", fake_service)
    response = llm_app.post("/api/v1/llm/grammar", json={"text": SOURCE})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["replacement"] == "resolving customer escalations"


def test_api_grammar_error_maps_to_400(llm_app, llm_env, monkeypatch):
    def down_service():
        return LLMService(
            audit_path=Path(llm_env["audit_path"]),
            client=_DownClient(),
        )

    class _DownClient:
        def post(self, *a, **k):
            raise httpx.ConnectError("refused")

    monkeypatch.setattr(llm_api, "_service", down_service)
    response = llm_app.post("/api/v1/llm/grammar", json={"text": SOURCE})
    assert response.status_code == 400
    assert "Ollama unreachable" in response.json()["error"]


ANCHOR_TEXT = (
    "Processed confidential records weekly for the claims department "
    "and resolved customer disputes."
)


def test_api_transitions_endpoint(llm_app, llm_env, monkeypatch):
    payload = _suggestions_payload(
        {
            "original": ANCHOR_TEXT,
            "replacement": (
                "Additionally, processed confidential records weekly for the "
                "claims department and resolved disputes"
            ),
            "type": "transition",
            "reason": "smoother opening",
        }
    )

    def fake_service():
        return LLMService(
            audit_path=Path(llm_env["audit_path"]), client=FakeOllama(payload)
        )

    monkeypatch.setattr(llm_api, "_service", fake_service)
    response = llm_app.post(
        "/api/v1/llm/transitions",
        json={"text": ANCHOR_TEXT, "mode": "transitions"},
    )
    assert response.status_code == 200
    assert response.json()[0]["type"] == "transition"


def test_api_keywords_endpoint(llm_app, llm_env, monkeypatch):
    def fake_service():
        return LLMService(
            audit_path=Path(llm_env["audit_path"]),
            client=FakeOllama(json.dumps({"keywords": ["claims", "disputes"]})),
        )

    monkeypatch.setattr(llm_api, "_service", fake_service)
    response = llm_app.post(
        "/api/v1/llm/keywords", json={"query": "claims", "limit": 5}
    )
    assert response.status_code == 200
    assert response.json() == ["claims", "disputes"]


def test_api_config_round_trip(llm_app, llm_env):
    response = llm_app.put(
        "/api/v1/llm/config",
        json={
            "enabled": True,
            "endpoint": "http://127.0.0.1:11434",
            "model": "gemma2",
            "max_tokens": 500,
            "temperature": 0.3,
        },
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is True
    fetched = llm_app.get("/api/v1/llm/config")
    assert fetched.json()["enabled"] is True
