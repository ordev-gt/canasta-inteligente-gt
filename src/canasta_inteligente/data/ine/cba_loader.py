import csv
import re
import unicodedata
from pathlib import Path

import pandas as pd

from ...domain.food import Food, FoodCatalog
from ...domain.prices import GENERAL, RURAL, URBAN, PricePoint
from ..matcher import FoodMatcher
from ..text import TextNormalizer


MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

LEGACY_COLUMNS = [
    "number", "category", "product", "base_unit", "daily_grams",
    "base_unit_price", "daily_cost",
]


def canonical_id(name: str) -> str:
    normalized = identity_text(name)
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_") or "alimento"


def identity_text(name: str) -> str:
    text = str(name).lower().strip()
    text = "".join(char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text)).strip()


def _number(value) -> float | None:
    if pd.isna(value) or value == "":
        return None
    return float(str(value).replace(",", ""))


class CBADataLoader:
    """Unifica las CBA antes de cualquier emparejamiento nutricional.
    Legacy corresponde a los datos de octubre 2017 a 2023
    """

    def __init__(self, history_dir: str | Path, fuzzy_threshold: float = 0.72):
        self.history_dir = Path(history_dir)
        self.fuzzy_threshold = fuzzy_threshold

    def load(self) -> FoodCatalog:
        catalog = FoodCatalog()
        self._load_legacy(catalog)
        self._load_regional_workbook(catalog, self._rural_workbook(), RURAL)
        self._load_regional_workbook(catalog, self._urban_workbook(), URBAN)
        self.add_general_regional_means(catalog)
        return catalog

    def _rural_workbook(self) -> Path:
        matches = sorted(self.history_dir.glob("Historico-por-grupo-alimenticio-y-por-producto-CBAR*.xlsx"))
        if not matches:
            raise FileNotFoundError("No se encontró el histórico rural CBAR")
        return matches[0]

    def _urban_workbook(self) -> Path:
        matches = sorted(self.history_dir.glob("Historico-por-grupo-alimenticio-y-por-producto-CBAU*.xlsx"))
        if not matches:
            raise FileNotFoundError("No se encontró el histórico urbano CBAU")
        return matches[0]

    def _load_legacy(self, catalog: FoodCatalog) -> None:
        """De 2017 a 2023. Globales. Sin separacion por region."""
        pattern = re.compile(r"cba_(\d{4})_(\d{2})[a-z]+_tabla\.csv$", re.IGNORECASE)
        for path in sorted(self.history_dir.glob("cba_*_tabla.csv")):
            match = pattern.match(path.name)
            if not match:
                continue
            year, month = map(int, match.groups())

            for row in self._read_legacy_csv(path).to_dict("records"):
                name = str(row["product"]).strip()
                price_per_100g = self._legacy_price_per_100g(
                    name, _number(row["base_unit_price"]), str(row["base_unit"])
                )
                point = PricePoint(
                    year=year,
                    month=month,
                    region=GENERAL,
                    original_name=name,
                    source=path.name,
                    cost_per_gram=(price_per_100g / 100) if price_per_100g is not None else None,
                    price_per_100g=price_per_100g,
                    daily_grams=_number(row["daily_grams"])/4.77,
                    daily_cost=_number(row["daily_cost"])/4.77,
                    base_unit=str(row["base_unit"]),
                    base_unit_price=_number(row["base_unit_price"]),
                )
                food = self._resolve_food(
                    catalog, name, point,
                    category=str(row["category"]).strip(),
                    allow_fuzzy=False,
                )
                food.add_price_point(point)

    @staticmethod
    def _read_legacy_csv(path: Path) -> pd.DataFrame:
        rows = []
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            
            for line_number, row in enumerate(reader, start=2):
                if not row or all(not cell.strip() for cell in row):
                    continue
                if len(row) > 7:
                    row = [row[0], row[1], ",".join(row[2:-4]).strip(), *row[-4:]]
                if len(row) != 7:
                    raise ValueError(f"Fila inválida en {path.name}:{line_number}")
                rows.append(row)
        return pd.DataFrame(rows, columns=LEGACY_COLUMNS)

    @staticmethod
    def _legacy_price_per_100g(product: str, price: float | None, unit_text: str) -> float | None:
        if price is None:
            return None
        match = re.match(r"\s*([\d,.]+)\s*([^\s]+)", unit_text.lower())
        if not match:
            return None
        quantity = float(match.group(1).replace(",", ""))
        unit = match.group(2)
        if unit in {"g", "gm", "gms", "gramo", "gramos"}:
            grams = quantity
        elif unit in {"ml", "mililitro", "mililitros"}:
            density = 1.030 if "leche" in TextNormalizer.normalize(product) else None
            if density is None:
                return None
            grams = quantity * density
        else:
            return None
        return price / grams * 100

    def _load_regional_workbook(self, catalog: FoodCatalog, path: Path, region: str) -> None:
        workbook = pd.ExcelFile(path)
        sheet = next((name for name in workbook.sheet_names if "producto" in TextNormalizer.normalize(name)), None)
        if sheet is None:
            raise ValueError(f"{path.name} no contiene una hoja de productos")
        frame = pd.read_excel(path, sheet_name=sheet)
        columns = {TextNormalizer.normalize(column): column for column in frame.columns}

        def column(*names: str):
            for name in names:
                if name in columns:
                    return columns[name]
            raise KeyError(f"No se encontró ninguna columna {names} en {path.name}")

        year_col = column("ano")
        month_col = column("mes")
        product_col = column("producto")
        daily_kcal_col = column("kilocalorias diarias")
        monthly_kcal_col = column("kilocalorias mensuales")
        daily_grams_col = column("cantidad gramos diarios")
        monthly_grams_col = column("cantidad gramos mensuales")
        daily_cost_col = column("costo diario")
        monthly_cost_col = column("costo mensual")
        base_quantity_col = column("cantidad base")
        base_unit_col = column("unidad medida base", "unidad de medida base")
        base_price_col = column("precio segun unidad medida base", "precio segun unidad de medida base")

        for _, row in frame.dropna(subset=[year_col, month_col, product_col]).iterrows():
            name = str(row[product_col]).strip()
            month_name = TextNormalizer.normalize(row[month_col])
            if month_name not in MONTHS:
                raise ValueError(f"Mes no reconocido: {row[month_col]}")
            daily_grams = _number(row[daily_grams_col])
            daily_cost = _number(row[daily_cost_col])
            cost_per_gram = daily_cost / daily_grams if daily_cost is not None and daily_grams else None
            point = PricePoint(
                year=int(row[year_col]), month=MONTHS[month_name], region=region,
                original_name=name, source=path.name,
                cost_per_gram=cost_per_gram,
                price_per_100g=(cost_per_gram * 100) if cost_per_gram is not None else None,
                daily_grams=daily_grams, monthly_grams=_number(row[monthly_grams_col]),
                daily_cost=daily_cost, monthly_cost=_number(row[monthly_cost_col]),
                daily_kcal=_number(row[daily_kcal_col]), monthly_kcal=_number(row[monthly_kcal_col]),
                base_quantity=_number(row[base_quantity_col]), base_unit=str(row[base_unit_col]),
                base_unit_price=_number(row[base_price_col]),
            )
            food = self._resolve_food(catalog, name, point)
            food.add_price_point(point)

    def _resolve_food(
        self, catalog: FoodCatalog, name: str, point: PricePoint,
        *, category: str | None = None, allow_fuzzy: bool = True,
    ) -> Food:
        normalized = identity_text(name)
        exact = catalog.find_by_normalized_alias(normalized)
        if exact is not None:
            if exact.category is None and category:
                exact.category = category
            return exact

        best_food, best_score = None, 0.0
        if allow_fuzzy:
            for food in catalog:
                query = TextNormalizer.normalize(name)
                candidates = {TextNormalizer.normalize(food.name), *(TextNormalizer.normalize(alias) for alias in food.aliases)}
                score = max((FoodMatcher.score(query, candidate)[0] for candidate in candidates), default=0.0)
                if score > best_score:
                    best_food, best_score = food, score

        key = (point.year, point.month)
        existing_timeline = best_food.price_timelines.get(point.region) if best_food is not None else None
        collision = existing_timeline is not None and key in existing_timeline
        if best_food is not None and best_score >= self.fuzzy_threshold and not collision:
            catalog.register_alias(best_food, name, normalized)
            if best_food.category is None and category:
                best_food.category = category
            return best_food

        food_id = canonical_id(name)
        suffix = 2
        while any(food.id == food_id for food in catalog):
            food_id = f"{canonical_id(name)}_{suffix}"
            suffix += 1
        return catalog.add(Food(food_id, name, category=category), {normalized})

    @staticmethod
    def add_general_regional_means(catalog: FoodCatalog) -> int:
        numeric_fields = (
            "cost_per_gram", "price_per_100g", "daily_grams", "monthly_grams",
            "daily_cost", "monthly_cost", "daily_kcal", "monthly_kcal",
            "base_quantity", "base_unit_price",
        )
        created = 0
        for food in catalog:
            rural = food.price_timelines.get(RURAL)
            urban = food.price_timelines.get(URBAN)
            if rural is None or urban is None:
                continue
            for year, month in sorted(rural.keys() & urban.keys()):
                if food.price_timelines.get(GENERAL) and (year, month) in food.price_timelines[GENERAL]:
                    continue
                left, right = rural.get(year, month), urban.get(year, month)
                values = {}
                for name in numeric_fields:
                    a, b = getattr(left, name), getattr(right, name)
                    values[name] = (a + b) / 2 if a is not None and b is not None else None
                point = PricePoint(
                    year=year, month=month, region=GENERAL,
                    original_name=food.name, source=f"mean:{left.source}+{right.source}",
                    base_unit=left.base_unit if left.base_unit == right.base_unit else None,
                    derived=True, **values,
                )
                food.add_price_point(point)
                created += 1
        return created
