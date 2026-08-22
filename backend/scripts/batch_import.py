"""Batch-import every real document into a fresh knowledge base.

Skips non-evidence files (postings, images) and "Copy of" duplicates
whose original is present. Uploads through the live API so the full
HTTP path is exercised.
"""

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent
FOLDERS = [ROOT / "resumes", ROOT / "soqs"]
API = "http://127.0.0.1:8000/api/v1"

SKIP_PATTERNS = ["duty statement", "typingtest"]


def normalize(name: str) -> str:
    """Normalize filenames for duplicate detection."""
    cleaned = name.lower().replace("copy of ", "").replace("_", " ")
    return " ".join(cleaned.split())


def collect_files() -> list[Path]:
    seen: dict[str, Path] = {}
    skipped: list[str] = []
    for folder in FOLDERS:
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            lowered = path.name.lower()
            if not lowered.endswith((".docx", ".pdf", ".txt")):
                skipped.append(f"{path.name} (not a document)")
                continue
            if any(pattern in lowered for pattern in SKIP_PATTERNS):
                skipped.append(f"{path.name} (posting/non-evidence)")
                continue
            key = normalize(path.stem)
            if key in seen:
                skipped.append(f"{path.name} (duplicate of {seen[key].name})")
                continue
            seen[key] = path
    return list(seen.values())


def main() -> int:
    files = collect_files()
    print(f"{len(files)} unique documents to import")

    created_total = 0
    failures: list[tuple[str, str]] = []
    empty_results: list[str] = []

    with httpx.Client(timeout=120) as client:
        health = client.get("http://127.0.0.1:8000/health")
        health.raise_for_status()

        for index, path in enumerate(files, start=1):
            try:
                response = client.post(
                    f"{API}/import/",
                    files={"file": (path.name, path.read_bytes(), "application/octet-stream")},
                )
                if response.status_code != 200:
                    failures.append((path.name, f"HTTP {response.status_code}: {response.text[:120]}"))
                    continue
                body = response.json()
                count = body.get("items_created", 0)
                created_total += count
                marker = "ok" if count else "EMPTY"
                print(f"[{index:>2}/{len(files)}] {marker:>5} {count:>3} items | {path.name}")
                if count == 0:
                    empty_results.append(path.name)
            except Exception as exc:  # noqa: BLE001
                failures.append((path.name, repr(exc)))

        stats = client.get(f"{API}/knowledge-items/?limit=1")
        total = stats.json()["total"]

    print()
    print(f"TOTAL items created: {created_total}")
    print(f"failures: {len(failures)}")
    for name, reason in failures:
        print(f"  FAIL {name}: {reason}")
    print(f"zero-item imports: {len(empty_results)}")
    for name in empty_results:
        print(f"  EMPTY {name}")
    print(f"knowledge base total: {total} items")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
