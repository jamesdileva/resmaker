"""Live check: the real CalCareers SOQ questions against the real corpus.

For each of the four numbered questions from the posting:
  suggest -> top 5 -> build (250 words) -> assert every item appears
  within budget. Exports question 1 as DOCX for eyeball review.
"""

import subprocess
import sys
import time
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parent.parent
PORT = 8021
BASE = f"http://127.0.0.1:{PORT}/api/v1"

QUESTIONS = [
    (
        "1",
        "Describe your relevant education, training, and experience "
        "researching information, preparing reports, and communicating "
        "effectively.",
    ),
    (
        "2",
        "Describe your experience prioritizing multiple high-level "
        "assignments and provide an example of how you were able to "
        "complete the assignments with conflicting deadlines.",
    ),
    (
        "3",
        "Describe your experience using Microsoft Office applications "
        "(Outlook, Word, Excel, Teams etc.) electronic systems to track "
        "and manage treatment information.",
    ),
    (
        "4",
        "Describe your experience supporting program operations and "
        "working with interdisciplinary treatment teams.",
    ),
]


def count_words(text: str) -> int:
    return len(text.split())


def main() -> int:
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
                if httpx.get(f"http://127.0.0.1:{PORT}/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(1)
        else:
            print("FAIL: backend did not come up")
            return 1

        failures = 0
        for number, question in QUESTIONS:
            suggestions = httpx.post(
                f"{BASE}/build/suggest", json={"query": question}, timeout=60
            ).json()
            top_ids = [s["knowledge_item"]["id"] for s in suggestions[:5]]
            built = httpx.post(
                f"{BASE}/build/soq",
                json={
                    "question": question,
                    "selected_item_ids": top_ids,
                    "max_words": 250,
                },
                timeout=60,
            ).json()
            response_lines = next(
                s["lines"] for s in built["sections"] if s["section_type"] == "soq_response"
            )
            total = sum(count_words(line) for line in response_lines)
            category = built.get("metadata", {}).get("category", "?")
            ok_items = len(response_lines) == min(5, len(suggestions))
            ok_budget = total <= 250
            status = "OK " if ok_items and ok_budget else "FAIL"
            if not (ok_items and ok_budget):
                failures += 1
            print(
                f"[{status}] Q{number}: category={category} items={len(response_lines)}/5 "
                f"words={total}/250 warnings={len(built['warnings'])}"
            )
            if number == "1":
                export = httpx.post(
                    f"http://127.0.0.1:{PORT}/api/v1/export/",
                    json={"document_id": built["document_id"], "format": "docx"},
                    timeout=60,
                ).json()
                target = Path.home() / "Desktop" / "calcareers_q1_sample.docx"
                blob = httpx.post(
                    f"http://127.0.0.1:{PORT}/api/v1/export/download",
                    json={"document_id": built["document_id"], "format": "docx"},
                    timeout=60,
                ).content
                target.write_bytes(blob)
                print(f"      exported sample: {target}")

        print()
        print("ALL QUESTIONS PASS" if failures == 0 else f"{failures} QUESTION(S) FAILED")
        return 0 if failures == 0 else 1
    finally:
        server.terminate()


if __name__ == "__main__":
    sys.exit(main())
