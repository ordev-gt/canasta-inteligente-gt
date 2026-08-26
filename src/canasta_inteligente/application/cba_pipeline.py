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
    minimum_probability: float = 0.20,
    probability_step: float = 0.05,
    initial_energy_tolerance: float = 30,
    maximum_energy_tolerance: float = 75,
    energy_tolerance_step: float = 20,
    maximum_attempts: int = 7,
    top_n: int = 25,
) -> dict[str, int]:
    """Segunda etapa: empareja el catálogo CBA terminado con el INCAP."""
    loader = Nutrition_INCAP(str(incap_pdf))
    return INCAPNutritionEnricher(loader, min_probability).enrich(
        catalog,
        minimum_probability=minimum_probability,
        probability_step=probability_step,
        initial_energy_tolerance=initial_energy_tolerance,
        maximum_energy_tolerance=maximum_energy_tolerance,
        energy_tolerance_step=energy_tolerance_step,
        maximum_attempts=maximum_attempts,
        top_n=top_n,
    )
