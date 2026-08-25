from pathlib import Path

from ..data.incap import INCAPNutritionEnricher, Nutrition_INCAP
from ..data.ine import CBADataLoader
from ..domain.food import FoodCatalog


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CBA_HISTORY = PROJECT_ROOT / "data" / "raw" / "ine" / "cba_historicos"
DEFAULT_INCAP_PDF = PROJECT_ROOT / "data" / "raw" / "incap" / "tabladecomposiciondealimentos.pdf"


def build_cba_catalog(history_dir: str | Path = DEFAULT_CBA_HISTORY) -> FoodCatalog:
    """Cargar y unificar todas las CBA desde 2017 a 2026"""
    return CBADataLoader(history_dir).load()


def enrich_catalog_with_incap(
    catalog: FoodCatalog,
    incap_pdf: str | Path = DEFAULT_INCAP_PDF,
    min_probability: float = 0.50,
) -> dict[str, int]:
    """Segunda etapa: empareja el catálogo CBA terminado con el INCAP."""
    loader = Nutrition_INCAP(str(incap_pdf))
    return INCAPNutritionEnricher(loader, min_probability).enrich(catalog)
