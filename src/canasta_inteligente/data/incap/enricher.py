from ...domain.food import FoodCatalog
from ...domain.nutrition import NutritionProfile
from ..matcher import FoodMatcher
from ..text import TextNormalizer
from .loader import Nutrition_INCAP
from rapidfuzz import fuzz, process


class INCAPNutritionEnricher:
    """Añade nutrición a un catálogo CBA ya unificado."""

    def __init__(self, loader: Nutrition_INCAP, min_probability: float = 0.50):
        self.loader = loader
        self.min_probability = min_probability

    def enrich(self, catalog: FoodCatalog) -> dict[str, int]:
        matched = 0
        unmatched = 0
        candidates = self.loader.data[self.loader.NORMALIZED_NAME_COL].fillna("").astype(str).tolist()
        for food in catalog:
            best = None
            for query in {food.name, *food.aliases}:
                normalized_query = TextNormalizer.normalize(query)
                shortlist = process.extract(normalized_query, candidates, scorer=fuzz.WRatio, limit=10)
                for candidate, _, index in shortlist:
                    score, methods, details = FoodMatcher.score(normalized_query, candidate)
                    if score >= self.min_probability and methods and (best is None or score > best[1]):
                        best = (self.loader.data.iloc[index], score, methods, details)
            if best is None:
                unmatched += 1
                continue

            row, score, methods, _ = best
            code = str(row.get("codigo")) if row.get("codigo") is not None else None
            category = self._category_for(code)
            excluded = {"codigo", "nombre", "nombre_normalizado"}
            values = {key: self._numeric(value) for key, value in row.items() if key not in excluded}
            food.nutrition = NutritionProfile(code, str(row["nombre"]), category, values)
            food.nutrition_match_score = round(float(score), 4)
            food.nutrition_match_methods = tuple(methods)
            matched += 1
        return {"matched": matched, "unmatched": unmatched}

    def _category_for(self, code: str | None) -> str | None:
        if not code:
            return None
        for prefix_size in (2, 1):
            try:
                category = self.loader.categories.get(int(code[:prefix_size]))
            except (TypeError, ValueError):
                category = None
            if category:
                return str(category)
        return None

    @staticmethod
    def _numeric(value):
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            return value
