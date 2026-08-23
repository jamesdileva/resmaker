"""TF-IDF vectorization service with SQLite-cached vectors.

Pure-Python implementation (no sklearn). Vectors are sparse dicts of
{term: tf-idf weight}; the fitted IDF vocabulary is cached in the
tfidf_vectors table under the special key __index_meta__ so queries can
be vectorized without re-fitting.
"""

import math
import re
from collections import Counter
from typing import Optional

from sqlmodel import Session, select

from app.db.models import KnowledgeItem, TfidfVector

META_KEY = "__index_meta__"
TOKEN_RE = re.compile(r"[a-z][a-z-]{2,}")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens (3+ chars, letters/hyphens only)."""
    return TOKEN_RE.findall(text.lower())


class TfidfVectorizer:
    """Fits an IDF vocabulary and transforms text into sparse vectors."""

    def __init__(self) -> None:
        self.idf: dict[str, float] = {}

    def fit(self, documents: list[str]) -> None:
        """Compute inverse document frequency over a corpus."""
        doc_token_sets = [set(tokenize(doc)) for doc in documents]
        total_docs = len(doc_token_sets)
        if total_docs == 0:
            self.idf = {}
            return
        document_frequency: Counter[str] = Counter()
        for tokens in doc_token_sets:
            document_frequency.update(tokens)
        self.idf = {
            term: math.log(total_docs / count)
            for term, count in document_frequency.items()
        }

    def transform(self, text: str) -> dict[str, float]:
        """Return the sparse TF-IDF vector for one document/query."""
        tokens = tokenize(text)
        if not tokens or not self.idf:
            return {}
        counts = Counter(tokens)
        total = len(tokens)
        return {
            term: (count / total) * self.idf[term]
            for term, count in counts.items()
            if term in self.idf and self.idf[term] > 0
        }

    @staticmethod
    def norm(vector: dict[str, float]) -> float:
        return math.sqrt(sum(weight * weight for weight in vector.values()))

    @staticmethod
    def cosine_similarity(
        vec_a: dict[str, float],
        vec_b: dict[str, float],
        norm_a: Optional[float] = None,
        norm_b: Optional[float] = None,
    ) -> float:
        """Cosine between two sparse vectors (norms optional precomputed)."""
        dot = sum(
            weight * vec_b.get(term, 0.0) for term, weight in vec_a.items()
        )
        na = norm_a if norm_a is not None else TfidfVectorizer.norm(vec_a)
        nb = norm_b if norm_b is not None else TfidfVectorizer.norm(vec_b)
        if na <= 0.0 or nb <= 0.0:
            return 0.0
        similarity = dot / (na * nb)
        # Guard against floating-point overshoot.
        return max(0.0, min(similarity, 1.0))


class TfidfService:
    """Builds, caches, and queries the TF-IDF index for knowledge items."""

    def __init__(self, session: Session, vectorizer: Optional[TfidfVectorizer] = None) -> None:
        self.session = session
        self.vectorizer = vectorizer or TfidfVectorizer()

    def build_index(self, items: Optional[list[KnowledgeItem]] = None) -> int:
        """Fit on all items and cache their vectors. Returns item count."""
        if items is None:
            items = list(self.session.exec(select(KnowledgeItem)).all())

        self.vectorizer.fit([item.content or "" for item in items])

        for row in self.session.exec(select(TfidfVector)).all():
            self.session.delete(row)

        for item in items:
            vector = self.vectorizer.transform(item.content or "")
            self.session.add(
                TfidfVector(
                    key=item.id,
                    vector_json=vector,
                    norm=TfidfVectorizer.norm(vector),
                )
            )
        self.session.add(
            TfidfVector(key=META_KEY, vector_json=self.vectorizer.idf, norm=0.0)
        )
        self.session.commit()
        return len(items)

    def _load_meta_idf(self) -> bool:
        """Load the cached IDF vocabulary; False when no index exists."""
        meta = self.session.get(TfidfVector, META_KEY)
        if meta is None:
            return False
        self.vectorizer.idf = meta.vector_json
        return True

    def vectorize_query(self, query: str) -> dict[str, float]:
        """Vectorize a query using the cached index vocabulary."""
        if not self._load_meta_idf():
            return {}
        return self.vectorizer.transform(query)

    def similarity(self, item_id: str, query_vec: dict[str, float]) -> float:
        """Cached cosine similarity between an item and a query vector."""
        if not query_vec:
            return 0.0
        row = self.session.get(TfidfVector, item_id)
        if row is None or not row.vector_json:
            return 0.0
        return TfidfVectorizer.cosine_similarity(
            query_vec, row.vector_json, norm_b=row.norm
        )

    def item_vectors(self, item_ids: list[str]) -> dict[str, tuple[dict, float]]:
        """Bulk-load (vector, norm) pairs for the given items."""
        rows = self.session.exec(
            select(TfidfVector).where(TfidfVector.key.in_(item_ids))  # type: ignore[attr-defined]
        ).all()
        return {
            row.key: (row.vector_json or {}, row.norm) for row in rows
        }

    @staticmethod
    def pairwise_similarity(
        vec_a: tuple[dict, float], vec_b: tuple[dict, float]
    ) -> float:
        """Cosine between two bulk-loaded (vector, norm) pairs."""
        return TfidfVectorizer.cosine_similarity(
            vec_a[0], vec_b[0], norm_a=vec_a[1], norm_b=vec_b[1]
        )

    def rebuild_if_needed(self) -> bool:
        """Rebuild the cached index when items changed. True if rebuilt."""
        from sqlalchemy import func

        item_count = self.session.execute(
            select(func.count()).select_from(KnowledgeItem)
        ).scalar_one()
        vector_rows = self.session.exec(select(TfidfVector)).all()
        vector_keys = {row.key for row in vector_rows} - {META_KEY}

        if len(vector_keys) != item_count:
            self.build_index()
            return True

        newest_update = self.session.execute(
            select(func.max(KnowledgeItem.updated_at))
        ).scalar_one()
        newest_build = max(
            (row.built_at for row in vector_rows), default=None
        )
        if newest_update is not None and newest_build is not None and (
            newest_update > newest_build
        ):
            self.build_index()
            return True

        return False
