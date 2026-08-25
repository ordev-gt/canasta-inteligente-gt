from difflib import SequenceMatcher

import pandas as pd
from rapidfuzz import fuzz

from .text import TextNormalizer


class FoodMatcher:
    """Empareja nombres de productos sin encargarse de cargar sus fuentes."""

    @staticmethod
    def _ngrams(text: str, size: int = 3) -> set[str]:
        text = f" {text} "
        return {text[i:i + size] for i in range(max(0, len(text) - size + 1))}

    @classmethod
    def score(cls, query: str, candidate: str, ngram_size: int = 3) -> tuple[float, list[str], dict[str, float]]:
        if not query or not candidate:
            return 0.0, [], {}
        left, right = cls._ngrams(query, ngram_size), cls._ngrams(candidate, ngram_size)
        scores = {
            "exact": float(query == candidate),
            "contains": float(query in candidate or candidate in query),
            "sequence": SequenceMatcher(None, query, candidate).ratio(),
            "token_sort": fuzz.token_sort_ratio(query, candidate) / 100,
            "token_set": fuzz.token_set_ratio(query, candidate) / 100,
            "partial": fuzz.partial_ratio(query, candidate) / 100,
            "char_ngram_jaccard": len(left & right) / len(left | right) if left and right else 0.0,
        }
        return sum(scores.values()) / len(scores), [name for name, value in scores.items() if value >= 0.75], scores

    @classmethod
    def match(cls, query: str, candidates: pd.DataFrame, name_column: str = "nombre", top_n: int = 10, min_probability: float = 0.55):
        normalized_query = TextNormalizer.normalize(query)
        matches = []
        for _, row in candidates.iterrows():
            probability, methods, scores = cls.score(normalized_query, TextNormalizer.normalize(row.get(name_column)))
            if probability >= min_probability and methods:
                matches.append((row, round(probability, 4), methods, {key: round(value, 4) for key, value in scores.items()}))
        return sorted(matches, key=lambda item: item[1], reverse=True)[:top_n]
