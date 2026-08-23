"""Local LLM polish service (Sprint 30).

Optional, feature-flagged grammar/transition polishing against a local
Ollama instance. The LLM may ONLY refine language — every suggestion
passes :meth:`LLMService._filter_factual_changes` before leaving this
module, and every interaction (prompt, suggestions, filter decisions)
lands in ``logs/llm_audit.log``.

Anti-hallucination defense in depth:
1. System prompt forbids factual changes and demands JSON-only output.
2. Responses are parsed as structured suggestions; malformed payloads
   are rejected wholesale.
3. Heuristic filter rejects suggestions that tamper with numbers,
   invent proper nouns, balloon in length, or are not anchored to an
   exact substring of the input text.
4. The frontend presents surviving suggestions as diffs; nothing is
   applied until the user accepts.
"""

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from app.core.llm_config import LLMConfig, load_llm_config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CareerOS Grammar Assistant. You help improve the \
flow, grammar, and readability of career documents ONLY.

STRICT RULES:
1. You may ONLY suggest changes to: spelling, grammar, punctuation, \
sentence structure, and transitions between paragraphs.
2. You may NEVER add, remove, or alter factual information.
3. You may NEVER invent new content, experiences, or achievements.
4. If asked to create new facts, REFUSE immediately.

Return a JSON object exactly shaped like:
{"suggestions": [{"original": "...", "replacement": "...", "type": \
"grammar|transition", "reason": "..."}]}
Each "original" MUST be copied verbatim from the user's text."""

MODE_INSTRUCTIONS = {
    "grammar": (
        "Suggest spelling, grammar, punctuation, and sentence-structure "
        "improvements for the text below."
    ),
    "transitions": (
        "Suggest transition improvements between the paragraphs below. "
        "Only reword connecting language; keep every fact identical."
    ),
}

MAX_LENGTH_GROWTH_RATIO = 0.30

# Words that look like invented proper nouns: capitalized tokens not at
# sentence start that don't appear in the original text.
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")


@dataclass(frozen=True)
class LLMSuggestion:
    """One polished-language suggestion after safety filtering."""

    original: str
    replacement: str
    type: str  # "grammar" | "transition"
    reason: str = ""


@dataclass
class FilterResult:
    """Survivors plus what was dropped (and why) for audit purposes."""

    accepted: list[LLMSuggestion] = field(default_factory=list)
    rejected: list[tuple[LLMSuggestion, str]] = field(default_factory=list)


class LLMPolishError(Exception):
    """Raised when the LLM interaction fails or returns unusable output."""


class AuditLogger:
    """Append-only JSON-lines audit log for all LLM interactions."""

    def __init__(self, path: Path):
        self._path = path

    def record(self, payload: dict) -> None:
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **payload}
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
        except OSError:
            # Auditing must never break polishing; surface in server logs.
            logger.warning("Failed to write LLM audit entry", exc_info=True)


class LLMService:
    """Grammar/transition polish via a local Ollama endpoint."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        audit_path: Optional[Path] = None,
        client: Optional[httpx.Client] = None,
    ):
        self.config = config or load_llm_config()
        if audit_path is None:
            audit_path = (
                Path(__file__).resolve().parent.parent.parent
                / "logs"
                / "llm_audit.log"
            )
        self.audit = AuditLogger(audit_path)
        self._client = client

    # ------------------------------------------------------------ transport

    def _post_chat(self, user_prompt: str) -> str:
        """Call Ollama's chat API and return the assistant message text."""
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.config.model,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        url = f"{self.config.endpoint.rstrip('/')}/api/chat"
        try:
            if self._client is not None:
                response = self._client.post(
                    url, json=payload, headers=headers, timeout=120
                )
            else:
                response = httpx.post(url, json=payload, headers=headers, timeout=120)
        except httpx.HTTPError as exc:
            raise LLMPolishError(
                f"Ollama unreachable at {self.config.endpoint}: {exc}"
            ) from exc
        if response.status_code != 200:
            raise LLMPolishError(
                f"Ollama returned {response.status_code}: {response.text[:200]}"
            )
        try:
            return response.json()["message"]["content"]
        except (ValueError, KeyError) as exc:
            raise LLMPolishError(f"Unexpected Ollama response shape: {exc}") from exc

    def _parse_suggestions(self, content: str) -> list[dict]:
        """Parse the model's JSON payload; malformed output is rejected."""
        try:
            parsed = json.loads(content)
        except ValueError as exc:
            raise LLMPolishError(f"Model returned invalid JSON: {exc}") from exc
        suggestions = parsed.get("suggestions") if isinstance(parsed, dict) else None
        if not isinstance(suggestions, list):
            raise LLMPolishError("Model JSON lacks a 'suggestions' list")
        clean: list[dict] = []
        for entry in suggestions:
            if not isinstance(entry, dict):
                continue
            original = entry.get("original")
            replacement = entry.get("replacement")
            if not isinstance(original, str) or not isinstance(replacement, str):
                continue
            clean.append(entry)
        return clean

    # --------------------------------------------------------------- public

    def polish(self, text: str, mode: str = "grammar") -> list[LLMSuggestion]:
        """Request polish suggestions for *text* and filter them for facts.

        Returns only suggestions that survived the heuristic safety net;
        everything else is recorded in the audit log with its reason.
        """
        instruction = MODE_INSTRUCTIONS.get(mode)
        if instruction is None:
            raise ValueError(f"Unknown polish mode: {mode!r}")
        request_id = uuid.uuid4().hex[:12]
        raw_content = self._post_chat(
            f"{instruction}\n\nText:\n{text}\n\nReturn the JSON object now."
        )
        try:
            entries = self._parse_suggestions(raw_content)
        except LLMPolishError as exc:
            self.audit.record(
                {
                    "request_id": request_id,
                    "mode": mode,
                    "model": self.config.model,
                    "error": str(exc),
                    "raw_response": raw_content[:2000],
                }
            )
            raise
        candidates = [
            LLMSuggestion(
                original=str(entry["original"]),
                replacement=str(entry["replacement"]),
                type="transition" if mode == "transitions" else "grammar",
                reason=str(entry.get("reason", "")),
            )
            for entry in entries
        ]
        result = self.filter_factual_changes(text, candidates)
        self.audit.record(
            {
                "request_id": request_id,
                "mode": mode,
                "model": self.config.model,
                "original_length": len(text),
                "suggestions_count": len(candidates),
                "accepted_count": len(result.accepted),
                "rejected": [
                    {"replacement": s.replacement[:200], "reason": reason}
                    for s, reason in result.rejected
                ],
            }
        )
        return result.accepted

    def keyword_expansion(self, query: str, limit: int = 8) -> list[str]:
        """Suggest search keywords related to *query* (synonyms/phrases).

        Keyword suggestions never touch documents, so the factual-change
        filter does not apply — but the model is still bound to short,
        plain-string output.
        """
        request_id = uuid.uuid4().hex[:12]
        prompt = (
            "List search keywords closely related to the phrase below for "
            f"retrieving career experience. Return ONLY synonyms and short "
            f"related phrases, at most {limit}, no explanations.\n\n"
            f"Phrase: {query}\n\nJSON shape: {{\"keywords\": [\"...\"]}}"
        )
        raw = self._post_chat(prompt)
        try:
            parsed = json.loads(raw)
            keywords = parsed.get("keywords") if isinstance(parsed, dict) else None
            if not isinstance(keywords, list):
                raise ValueError("lacks 'keywords' list")
            clean = [str(k).strip() for k in keywords if str(k).strip()][:limit]
        except (ValueError, TypeError) as exc:
            self.audit.record(
                {
                    "request_id": request_id,
                    "mode": "keywords",
                    "model": self.config.model,
                    "error": f"invalid keyword payload: {exc}",
                    "raw_response": raw[:2000],
                }
            )
            raise LLMPolishError(f"Invalid keyword payload: {exc}") from exc
        self.audit.record(
            {
                "request_id": request_id,
                "mode": "keywords",
                "model": self.config.model,
                "query": query,
                "keyword_count": len(clean),
            }
        )
        return clean

    # --------------------------------------------------------------- filter

    def filter_factual_changes(
        self, source_text: str, suggestions: list[LLMSuggestion]
    ) -> FilterResult:
        """Heuristically reject any suggestion that alters factual content."""
        result = FilterResult()
        numbers = set(_NUMBER_RE.findall(source_text))
        lowered_source = source_text.lower()
        source_tokens = {token.lower() for token in _TOKEN_RE.findall(source_text)}
        for suggestion in suggestions:
            reason = self._rejection_reason(
                suggestion,
                source_text=source_text,
                lowered_source=lowered_source,
                source_numbers=numbers,
                source_tokens=source_tokens,
            )
            if reason is None:
                result.accepted.append(suggestion)
            else:
                result.rejected.append((suggestion, reason))
        return result

    def _rejection_reason(
        self,
        suggestion: LLMSuggestion,
        source_text: str,
        lowered_source: str,
        source_numbers: set[str],
        source_tokens: set[str],
    ) -> Optional[str]:
        """Return a rejection reason, or None when the suggestion is safe."""
        if not suggestion.original.strip():
            return "empty anchor"
        # Anchor rule: the claimed original must exist verbatim in the text.
        if suggestion.original not in source_text:
            return "anchor not found verbatim in text"
        # Number integrity: replacements may not introduce unseen figures.
        replacement_numbers = set(_NUMBER_RE.findall(suggestion.replacement))
        invented_numbers = replacement_numbers - source_numbers
        if invented_numbers:
            return f"introduces numbers absent from text: {sorted(invented_numbers)}"
        # Proper-noun guard: capitalized MID-SENTENCE tokens must pre-exist.
        # Sentence-initial capitals (e.g. a leading "Additionally,") are how
        # legitimate transitions read, so they are exempt.
        invented_names = {
            token
            for token in _mid_sentence_capitals(suggestion.replacement)
            if token.lower() not in source_tokens
        }
        if invented_names:
            return f"introduces unknown proper nouns: {sorted(invented_names)}"
        # Length explosion: >30% growth means content injection.
        growth = len(suggestion.replacement) / max(len(suggestion.original), 1) - 1
        if growth > MAX_LENGTH_GROWTH_RATIO:
            return f"length grows {growth:.0%} (> {MAX_LENGTH_GROWTH_RATIO:.0%})"
        return None


_SENTENCE_START_RE = re.compile(r"(?:^|[.!?\u2026][\"')\]]?\s+|\n\s*)([A-Z][A-Za-z'-]*)")


def _mid_sentence_capitals(text: str) -> set[str]:
    """Capitalized tokens in *text* that do NOT start a sentence/line."""
    starts = {match.group(1).lower() for match in _SENTENCE_START_RE.finditer(text)}
    return {
        match.group(0)
        for match in re.finditer(r"[A-Z][A-Za-z'-]*", text)
        if match.group(0).lower() not in starts
    }
