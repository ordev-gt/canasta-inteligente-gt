from ...domain.food import Food, FoodCatalog
from ...domain.nutrition import NutritionProfile
from ..matcher import FoodMatcher
from ..text import TextNormalizer
from .loader import Nutrition_INCAP
from rapidfuzz import fuzz, process
import pandas as pd


class INCAPNutritionEnricher:
    """Añade nutrición a un catálogo CBA ya unificado."""

    def __init__(self, loader: Nutrition_INCAP, min_probability: float = 0.50):
        self.loader = loader
        self.min_probability = min_probability

    def enrich(
        self,
        catalog: FoodCatalog,
        *,
        minimum_probability: float = 0.20,
        probability_step: float = 0.05,
        initial_energy_tolerance: float = 30,
        maximum_energy_tolerance: float = 75,
        energy_tolerance_step: float = 20,
        maximum_attempts: int = 7,
        top_n: int = 25,
    ) -> dict[str, int]:
        matched = 0
        unmatched = 0
        for food in catalog:
            food_candidates = self._search_with_fallback(
                food,
                energy_reference=self._energy_reference(food),
                minimum_probability=minimum_probability,
                probability_step=probability_step,
                initial_energy_tolerance=initial_energy_tolerance,
                maximum_energy_tolerance=maximum_energy_tolerance,
                energy_tolerance_step=energy_tolerance_step,
                maximum_attempts=maximum_attempts,
                top_n=top_n,
            )
            if food_candidates.empty:
                food.nutrition_candidates = food_candidates
                unmatched += 1
                continue

            selected = food_candidates.iloc[0]
            self._apply_match(
                food,
                selected,
                selected["match_probability"],
                selected["match_methods"],
            )
            food.nutrition_candidates = food_candidates.iloc[1:].reset_index(drop=True)
            matched += 1
        return {"matched": matched, "unmatched": unmatched}

    def _search_with_fallback(
        self,
        food: Food,
        *,
        energy_reference: float | None,
        minimum_probability: float,
        probability_step: float,
        initial_energy_tolerance: float,
        maximum_energy_tolerance: float,
        energy_tolerance_step: float,
        maximum_attempts: int,
        top_n: int,
    ) -> pd.DataFrame:
        last_result = pd.DataFrame()
        for attempt in range(maximum_attempts):
            min_probability = max(
                minimum_probability,
                self.min_probability - attempt * probability_step,
            )
            energy_tolerance = (
                min(
                    maximum_energy_tolerance,
                    initial_energy_tolerance + attempt * energy_tolerance_step,
                )
                if energy_reference is not None
                else None
            )
            results = []
            for query in {food.name, *food.aliases}:
                candidates = self.search_food_candidates(
                    category=None,
                    name=query,
                    min_probability=min_probability,
                    top_n=top_n,
                    energy_per_100g=energy_reference,
                    energy_tolerance=energy_tolerance,
                    require_match_methods=attempt < 2,
                )
                last_result = candidates
                if not candidates.empty:
                    candidates = candidates.copy()
                    candidates["search_query"] = query
                    results.append(candidates)

            if results:
                combined = pd.concat(results, ignore_index=True)
                combined = combined.sort_values(
                    "match_probability", ascending=False
                ).drop_duplicates("codigo", keep="first")
                if energy_reference is not None:
                    return combined.sort_values(
                        ["energy_difference_kcal", "match_probability"],
                        ascending=[True, False],
                    ).reset_index(drop=True)
                return combined.sort_values(
                    "match_probability", ascending=False
                ).reset_index(drop=True)
        return last_result

    @staticmethod
    def _energy_reference(food: Food) -> float | None:
        summaries = [
            summary
            for summary in food.avg_energy().values()
            if summary is not None and summary["count"] > 0
        ]
        observation_count = sum(summary["count"] for summary in summaries)
        if observation_count == 0:
            return None
        return sum(
            summary["avg"] * summary["count"] for summary in summaries
        ) / observation_count

    def enrich_food(
        self,
        category: str | int | None,
        name: str,
        min_probability: float,
        food: Food,
    ) -> Food:
        """Enriquece y devuelve una instancia individual de ``Food``.

        ``category`` puede ser el código o el nombre de una categoría INCAP.
        Si es ``None``, la búsqueda se realiza en todas las categorías. Si no
        se encuentra una coincidencia que alcance ``min_probability``, el
        alimento se devuelve sin modificar.
        """
        if not 0 <= min_probability <= 1:
            raise ValueError("min_probability debe estar entre 0 y 1")

        candidates = self._candidates_for_category(category)
        if candidates.empty:
            return food

        normalized_candidates = (
            candidates[self.loader.NORMALIZED_NAME_COL].fillna("").astype(str).tolist()
        )
        normalized_name = TextNormalizer.normalize(name)
        best = None
        for candidate, _, position in process.extract(
            normalized_name, normalized_candidates, scorer=fuzz.WRatio, limit=10
        ):
            score, methods, details = FoodMatcher.score(normalized_name, candidate)
            if score >= min_probability and methods and (best is None or score > best[1]):
                best = (candidates.iloc[position], score, methods, details)

        if best is not None:
            self._apply_match(food, *best[:3])
        return food

    def search_food_candidates(
        self,
        category: str | int | None,
        name: str,
        min_probability: float = 0.0,
        top_n: int | None = 10,
        energy_per_100g: float | None = None,
        energy_tolerance: float | None = None,
        require_match_methods: bool = True,
    ) -> pd.DataFrame:
        """Devuelve candidatos INCAP ordenados para una revisión manual.

        La salida conserva las columnas originales del INCAP y agrega
        ``match_probability`` y ``match_methods``. ``category`` acepta el
        código o nombre de categoría; con ``None`` busca en toda la tabla.
        """
        if not 0 <= min_probability <= 1:
            raise ValueError("min_probability debe estar entre 0 y 1")
        if top_n is not None and top_n <= 0:
            raise ValueError("top_n debe ser positivo o None")
        if energy_per_100g is not None and energy_per_100g < 0:
            raise ValueError("energy_per_100g no puede ser negativa")
        if energy_tolerance is not None:
            if energy_per_100g is None:
                raise ValueError("energy_tolerance requiere energy_per_100g")
            if energy_tolerance < 0:
                raise ValueError("energy_tolerance no puede ser negativa")

        candidates = self._candidates_for_category(category)
        normalized_name = TextNormalizer.normalize(name)
        matches = []
        for _, row in candidates.iterrows():
            candidate_name = str(row.get(self.loader.NORMALIZED_NAME_COL) or "")
            score, methods, _ = FoodMatcher.score(normalized_name, candidate_name)
            if score < min_probability or (require_match_methods and not methods):
                continue
            result = row.to_dict()
            result["match_probability"] = round(float(score), 4)
            result["match_methods"] = tuple(methods)
            if energy_per_100g is not None:
                candidate_energy = self._numeric(row.get("energia_kcal"))
                if not isinstance(candidate_energy, (int, float)) or pd.isna(candidate_energy):
                    continue
                energy_difference = abs(candidate_energy - energy_per_100g)
                if energy_tolerance is not None and energy_difference > energy_tolerance:
                    continue
                result["energy_difference_kcal"] = energy_difference
                result["energy_difference_pct"] = (
                    100 * energy_difference / energy_per_100g
                    if energy_per_100g != 0
                    else None
                )
            matches.append(result)

        if energy_per_100g is None:
            matches.sort(key=lambda result: result["match_probability"], reverse=True)
        else:
            matches.sort(
                key=lambda result: (
                    result["energy_difference_kcal"],
                    -result["match_probability"],
                )
            )
        if top_n is not None:
            matches = matches[:top_n]
        result_columns = list(candidates.columns) + [
            "match_probability",
            "match_methods",
        ]
        if energy_per_100g is not None:
            result_columns += [
                "energy_difference_kcal",
                "energy_difference_pct",
            ]
        return pd.DataFrame(matches, columns=result_columns)

    def _candidates_for_category(self, category: str | int | None):
        candidates = self.loader.data
        if category is None:
            return candidates

        category_text = TextNormalizer.normalize(category)
        try:
            category_code = int(str(category).strip())
        except ValueError:
            category_code = None

        def matches(code) -> bool:
            resolved_category = self._category_for(str(code))
            if category_code is not None:
                expected = self.loader.categories.get(category_code)
                return expected is not None and resolved_category == str(expected)
            return TextNormalizer.normalize(resolved_category or "") == category_text

        return candidates[candidates["codigo"].apply(matches)]

    def _apply_match(self, food: Food, row, score: float, methods) -> None:
        code = str(row.get("codigo")) if row.get("codigo") is not None else None
        category = self._category_for(code)
        excluded = {"codigo", "nombre", "nombre_normalizado"}
        values = {key: self._numeric(value) for key, value in row.items() if key not in excluded}
        food.nutrition = NutritionProfile(code, str(row["nombre"]), category, values)
        food.nutrition_match_score = round(float(score), 4)
        food.nutrition_match_methods = tuple(methods)

    def _category_for(self, code: str | None) -> str | None:
        if not code:
            return None
        try:
            category_code = int(str(code).strip()[:-3])
        except (TypeError, ValueError):
            return None
        category = self.loader.categories.get(category_code)
        return str(category) if category else None

    @staticmethod
    def _numeric(value):
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            return value
