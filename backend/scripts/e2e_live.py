"""Live end-to-end run against the real knowledge base and packaged app.

Exercises: stats -> search -> suggest -> build (SOQ from real corpus)
-> validate -> export DOCX. Run with the backend on :8000.
"""

import io
import sys

import httpx

API = "http://127.0.0.1:8000/api/v1"


def section(title: str) -> None:
    print(f"\n=== {title}")


def main() -> int:
    failures: list[str] = []
    with httpx.Client(timeout=120) as client:
        health = client.get("http://127.0.0.1:8000/health")
        print(f"health: {health.json()['status']}")

        # 1. Corpus stats by type.
        section("corpus")
        stats: dict[str, int] = {}
        for item_type in (
            "resume_bullet",
            "soq_paragraph",
            "skill",
        ):
            response = client.get(
                f"{API}/knowledge-items/", params={"type": item_type, "limit": 1}
            )
            stats[item_type] = response.json()["total"]
        total_response = client.get(f"{API}/knowledge-items/?limit=1")
        grand_total = total_response.json()["total"]
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print(f"  TOTAL: {grand_total}")
        if grand_total < 100:
            failures.append(f"corpus smaller than expected: {grand_total}")

        # 2. Explorer-style search on real data.
        section("search 'confidential records'")
        results = client.post(
            f"{API}/search/",
            json={"query": "confidential records", "limit": 5},
        ).json()
        print(f"  {results['total']} hits; top score "
              f"{results['items'][0]['score']:.3f} "
              f"({results['items'][0]['star_rating']} stars)")
        print(f"  top: {results['items'][0]['knowledge_item']['content'][:80]}...")
        if results["total"] == 0:
            failures.append("search returned nothing")

        # 3. Suggestions for a real SOQ-style question.
        section("suggest")
        suggestions = client.post(
            f"{API}/build/suggest",
            json={
                "query": "Describe your experience handling confidential information",
                "item_types": ["soq_paragraph"],
                "top_k": 5,
            },
        ).json()
        print(f"  {len(suggestions)} suggestions")
        if suggestions:
            print(f"  top: {suggestions[0]['knowledge_item']['content'][:80]}...")

        # 4. Build a real SOQ response from corpus items.
        section("build SOQ")
        soq_items = client.get(
            f"{API}/knowledge-items/", params={"type": "soq_paragraph", "limit": 30}
        ).json()["items"]
        bullets = client.get(
            f"{API}/knowledge-items/", params={"type": "resume_bullet", "limit": 60}
        ).json()["items"]
        confidential_bullet = next(
            (b for b in bullets if "confidential" in b["content"].lower()), None
        )
        selection = [i["id"] for i in soq_items[:4]]
        if confidential_bullet:
            selection.append(confidential_bullet["id"])

        question = (
            "Describe your experience handling confidential and sensitive "
            "information in accordance with privacy requirements."
        )
        built = client.post(
            f"{API}/build/soq",
            json={
                "question": question,
                "selected_item_ids": selection,
                "max_words": 250,
            },
        )
        if built.status_code != 200:
            failures.append(f"SOQ build failed: HTTP {built.status_code}")
            print(f"  FAIL: {built.text[:200]}")
        else:
            document = built.json()
            answer = " ".join(
                document["sections"][1]["lines"]
            )
            words = len(answer.split())
            print(f"  document {document['document_id'][:8]}...")
            print(f"  category: {document['metadata'].get('category')}")
            print(f"  {words} words from {len(document['sections'][1]['lines'])} blocks")
            print(f"  traceability entries: {len(document['traceability'])}")

            # 5. Validate the built document.
            section("validate")
            validation = client.post(
                f"{API}/validate/",
                json={
                    "document_id": document["document_id"],
                    "doc_type": "soq",
                    "keywords": ["confidential", "privacy"],
                },
            ).json()
            print(f"  valid: {validation['valid']}  score: {validation['score']}")
            print(f"  errors: {len(validation['errors'])}  warnings: {len(validation['warnings'])}")
            for issue in validation["warnings"][:2]:
                print(f"    warn: {issue['message'][:90]}")

            # 6. Export DOCX.
            section("export DOCX")
            exported = client.post(
                f"{API}/export/download",
                json={"document_id": document["document_id"], "format": "docx"},
            )
            size = len(exported.content)
            print(f"  {size} bytes, content-type "
                  f"{exported.headers.get('content-type', '?')[:50]}")
            if size < 5000 or not exported.headers.get("content-disposition"):
                failures.append("export suspiciously small or missing headers")
            else:
                path = r"C:\Users\j\AppData\Local\Temp\career-os-live-e2e.docx"
                with open(path, "wb") as handle:
                    handle.write(exported.content)
                from docx import Document as DocxDocument

                parsed = DocxDocument(io.BytesIO(exported.content))
                texts = [p.text for p in parsed.paragraphs if p.text.strip()]
                print(f"  parsed back: {len(texts)} non-empty paragraphs")
                print(f"  saved sample -> {path}")

    print("\n================ RESULT ================")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("LIVE E2E PASSED — all stages OK against real corpus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
