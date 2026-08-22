"""Category keyword patterns for SOQ question classification."""

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_soq_categories() -> dict[str, list[str]]:
    """Load the SOQ category → keyword-pattern mapping."""
    with open(DATA_DIR / "soq_categories.json", encoding="utf-8") as handle:
        return json.load(handle)


class SOQAnalyzer:
    """Classifies SOQ questions and extracts domain keywords."""

    DEFAULT_CATEGORY = "General"

    def __init__(self) -> None:
        self._categories = load_soq_categories()

    def classify_question(self, question: str) -> str:
        """Return the best-matching category for a question."""
        lowered = question.lower()
        best_category = self.DEFAULT_CATEGORY
        best_score = 0
        for category, patterns in self._categories.items():
            score = sum(lowered.count(pattern.lower()) for pattern in patterns)
            if score > best_score:
                best_category = category
                best_score = score
        return best_category

    def extract_keywords(self, question: str) -> list[str]:
        """Extract domain-relevant keywords from a question.

        Combines cleaned tokens with any category keyword patterns that
        appear verbatim in the question.
        """
        lowered = question.lower()
        keywords: list[str] = []

        matched_patterns = [
            pattern.lower()
            for patterns in self._categories.values()
            for pattern in patterns
            if pattern.lower() in lowered
        ]
        # Longest phrases first so multi-word terms are not shadowed.
        matched_patterns.sort(key=len, reverse=True)

        token_set = set(self._tokenize(question))
        for phrase in matched_patterns:
            if phrase not in keywords:
                keywords.append(phrase)
            for word in phrase.split():
                token_set.discard(word)

        keywords.extend(sorted(token_set))
        return keywords

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re

        STOPWORDS = frozenset(
            """a an and are as at be by describe do does for from has have
            how i in is it of on or please tell that the their them they
            this to us was were what when where which you your""".split()
        )
        return [
            token
            for token in re.findall(r"[a-z][a-z-]+", text.lower())
            if token not in STOPWORDS and len(token) >= 3
        ]

    def analyze(self, question: str):
        """Return category and keywords together."""
        from app.models.soq import SOQAnalysis

        return SOQAnalysis(
            category=self.classify_question(question),
            keywords=self.extract_keywords(question),
        )
