import argparse
import pickle
from pathlib import Path

from ..data.incap import INCAPNutritionEnricher, Nutrition_INCAP
from ..data.ine import CBADataLoader
from ..domain.food import FoodCatalog


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CBA_HISTORY = PROJECT_ROOT / "data" / "raw" / "ine" / "cba_historicos"
DEFAULT_INCAP_PDF = PROJECT_ROOT / "data" / "raw" / "incap" / "tabladecomposiciondealimentos.pdf"
DEFAULT_PICKLE = PROJECT_ROOT / "data" / "processed" / "cba_catalog.pkl"

MERGES = (
    ("arroz", "arroz_corriente"),
    ("avena_de_toda_clase", "avena_mosh"),
    ("fideos", "pastas_alimenticias"),
    ("fideos", "pastas_de_todos_los_tipos"),
    ("fideos", "fideos_en_todas_sus_formas_excepto_macarrones_y_espagueti"),
    ("tortillas_de_maiz", "tortillas_frescas"),
    ("carne_de_res_con_hueso", "carne_de_res_con_hueso_para_cocido"),
    ("carne_de_cerdo_sin_hueso", "posta_de_cerdo_sin_hueso"),
    ("carne_de_pollo_o_gallina", "carne_de_pollo_blanco"),
    ("leche_liquida", "leche_entera_liquida_industrializada"),
    ("embutidos", "salchichas_y_productos_similares_de_carne"),
    ("queso_fresco_o_duro", "queso_fresco_incluye_el_queso_supercremoso"),
    ("crema_fresca", "crema_artesanal"),
    ("aceites_comestibles", "aceite_vegetal_mixtos"),
    ("aguacates", "aguacates_frescos"),
    ("bananos_guineos", "bananos_frescos"),
    ("platanos", "platanos_frescos"),
    ("tomate", "tomate_fresco"),
    ("cebolla_blanca_sin_tallo", "cebollas"),
    ("hierbas", "macuy_hierba_mora_quilete"),
    ("frijol", "frijoles_negros_secos"),
    ("azucar", "azucar_de_cana_blanca"),
    ("incaparina", "preparacion_nutricional_a_base_de_maiz_y_soya"),
)

EXCLUDED_FOODS = (
    "desayuno_o_cena_continental_bebida_y_dos_acompanamientos_elaborados",
    "almuerzo_o_cena_simple_bebida_carne_de_pollo_y_acompanamiento_excluye_gaseosa",
)


def build_cba_catalog(history_dir: str | Path = DEFAULT_CBA_HISTORY) -> FoodCatalog:
    """Cargar y unificar todas las CBA desde 2017 a 2026"""
    return CBADataLoader(history_dir).load()


def consolidate_cba_catalog(catalog: FoodCatalog) -> FoodCatalog:
    """Aplica las fusiones y exclusiones validadas en el notebook."""
    for target, source in MERGES:
        catalog.merge_foods(target, source)
    for food_id in EXCLUDED_FOODS:
        catalog.remove(food_id)
    return catalog


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


def save_catalog_pickle(
    catalog: FoodCatalog,
    output_path: str | Path = DEFAULT_PICKLE,
) -> Path:
    """Serializa un catálogo procesado y devuelve la ruta escrita."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("wb") as file:
        pickle.dump(catalog, file, protocol=pickle.HIGHEST_PROTOCOL)
    temporary.replace(destination)
    return destination


def load_catalog_pickle(input_path: str | Path = DEFAULT_PICKLE) -> FoodCatalog:
    """Carga un catálogo creado por :func:`save_catalog_pickle`."""
    with Path(input_path).open("rb") as file:
        catalog = pickle.load(file)
    if not isinstance(catalog, FoodCatalog):
        raise TypeError("El archivo pickle no contiene un FoodCatalog")
    return catalog


def process_cba_pipeline(
    history_dir: str | Path = DEFAULT_CBA_HISTORY,
    incap_pdf: str | Path = DEFAULT_INCAP_PDF,
    output_path: str | Path = DEFAULT_PICKLE,
    *,
    enrich: bool = True,
) -> tuple[FoodCatalog, dict[str, int]]:
    """Construye, consolida, enriquece y serializa el catálogo de la CBA."""
    catalog = consolidate_cba_catalog(build_cba_catalog(history_dir))
    match_summary = (
        enrich_catalog_with_incap(catalog, incap_pdf)
        if enrich
        else {"matched": 0, "unmatched": len(catalog)}
    )
    save_catalog_pickle(catalog, output_path)
    return catalog, {"foods": len(catalog), **match_summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Procesa y serializa la CBA")
    parser.add_argument("--history-dir", type=Path, default=DEFAULT_CBA_HISTORY)
    parser.add_argument("--incap-pdf", type=Path, default=DEFAULT_INCAP_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_PICKLE)
    parser.add_argument("--without-incap", action="store_true")
    args = parser.parse_args()
    _, summary = process_cba_pipeline(
        history_dir=args.history_dir,
        incap_pdf=args.incap_pdf,
        output_path=args.output,
        enrich=not args.without_incap,
    )
    print(f"Catálogo guardado en: {args.output.resolve()}")
    print(f"Resumen: {summary}")


if __name__ == "__main__":
    main()
