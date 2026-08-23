"""Sprint 30 live verification — real Ollama round-trip with fact guards.

Enables the LLM flag, starts a scratch-port backend, polishes a real
imported SOQ paragraph with gemma2, and programmatically proves that no
factual content changed:

1. every accepted suggestion is anchored verbatim in the source text;
2. accepted replacements introduce no numbers absent from the source;
3. applying all accepted suggestions keeps the number multiset intact.

Restores the disabled flag afterwards so the repo stays in its default
state. Requires: Ollama running on 127.0.0.1:11434 with gemma2 pulled.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent  # backend/ (script lives in backend/scripts)
BACKEND = ROOT
PORT = 8019
BASE = f"http://127.0.0.1:{PORT}"

sys.path.insert(0, str(BACKEND))

from app.core import llm_config  # noqa: E402

import re  # noqa: E402

NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")


def _soq_text() -> str:
    """First substantive paragraph from the committed sample SOQ fixture."""
    from docx import Document

    document = Document(str(BACKEND / "tests" / "fixtures" / "sample_soq.docx"))
    paragraphs = [
        p.text.strip()
        for p in document.paragraphs
        if len(p.text.strip().split()) >= 20
    ]
    if not paragraphs:
        raise SystemExit("sample_soq.docx yielded no substantial paragraph")
    return paragraphs[0]


def main() -> int:
    # 0. Ollama reachable + model present?
    try:
        tags = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5).json()
    except httpx.HTTPError as exc:
        print(f"FAIL: Ollama not reachable ({exc}) — start it and retry")
        return 1
    models = {m.get("name", "") for m in tags.get("models", [])}
    if not any(m.startswith("gemma2") for m in models):
        print(f"FAIL: gemma2 not pulled (have: {sorted(models)})")
        return 1
    print("[1] Ollama up; gemma2 available")

    # 1. enable the flag (runtime JSON config)
    llm_config.save_llm_config(
        llm_config.LLMConfig(enabled=True, model="gemma2")
    )
    print("[2] flag enabled via data/llm_config.json")

    server = subprocess.Popen(
        [
            str(BACKEND / ".venv" / "Scripts" / "python.exe"),
            "-m",
            "uvicorn",
            "app.main:app",
            "--port",
            str(PORT),
        ],
        cwd=str(BACKEND),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(30):
            try:
                if httpx.get(f"{BASE}/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(1)
        else:
            print("FAIL: backend did not come up")
            return 1
        print(f"[3] backend healthy on :{PORT}")

        text = _soq_text()
        # The fixture prose has no digits; add a figures-dense sentence so
        # the number-preservation assertions below are meaningful.
        text += (
            " In 2023 alone I processed over 50 confidential records "
            "weekly while maintaining a 98% accuracy rating."
        )
        numbers_before = sorted(NUMBER_RE.findall(text))
        print(f"[4] polishing real SOQ text ({len(text.split())} words)")
        print(f"    {text[:120]}...")

        response = httpx.post(
            f"{BASE}/api/v1/llm/grammar", json={"text": text}, timeout=180
        )
        if response.status_code != 200:
            print(f"FAIL: /llm/grammar -> {response.status_code}: {response.text[:200]}")
            return 1
        suggestions = response.json()
        print(f"[5] {len(suggestions)} suggestion(s) survived the safety filter")

        polished = text
        for suggestion in suggestions:
            assert (
                suggestion["original"] in polished
            ), f"unanchored suggestion leaked: {suggestion}"
            invented = set(NUMBER_RE.findall(suggestion["replacement"])) - set(
                NUMBER_RE.findall(polished)
            )
            assert not invented, f"invented numbers leaked: {invented}"
            polished = polished.replace(
                suggestion["original"], suggestion["replacement"], 1
            )

        numbers_after = sorted(NUMBER_RE.findall(polished))
        assert (
            numbers_after == numbers_before
        ), f"numbers changed! {numbers_before} -> {numbers_after}"

        transitions = httpx.post(
            f"{BASE}/api/v1/llm/transitions", json={"text": text}, timeout=180
        )
        assert transitions.status_code == 200, transitions.text[:200]
        print(f"[6] transitions mode OK ({len(transitions.json())} suggestion(s))")

        keywords = httpx.post(
            f"{BASE}/api/v1/llm/keywords",
            json={"query": "workers compensation claims", "limit": 6},
            timeout=120,
        )
        assert keywords.status_code == 200, keywords.text[:200]
        print(f"[7] keyword expansion OK: {keywords.json()}")

        audit = BACKEND / "logs" / "llm_audit.log"
        assert audit.exists(), "audit log missing"
        entries = [json.loads(line) for line in audit.read_text().splitlines()]
        assert any(e.get("mode") == "grammar" for e in entries)
        print(f"[8] audit log has {len(entries)} entries")

        print()
        print("LIVE SPRINT 30 VERIFICATION PASSED")
        print(f"  facts preserved: numbers {numbers_before} unchanged after polish")
        return 0
    finally:
        server.terminate()
        llm_config.config_path().unlink(missing_ok=True)  # restore disabled default


if __name__ == "__main__":
    sys.exit(main())
