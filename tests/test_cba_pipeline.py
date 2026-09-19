import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from canasta_inteligente.application.cba_pipeline import (
    build_cba_catalog,
    load_catalog_pickle,
    process_cba_pipeline,
    save_catalog_pickle,
)
from canasta_inteligente.data.incap import INCAPNutritionEnricher
from canasta_inteligente.data.ine.cba_loader import CBADataLoader
from canasta_inteligente.domain.food import Food, FoodCatalog
from canasta_inteligente.domain.prices import GENERAL, RURAL, URBAN, PricePoint


class PriceDomainTests(unittest.TestCase):
    def test_timeline_summarizes_energy_variation(self):
        from canasta_inteligente.domain.prices import PriceTimeline

        timeline = PriceTimeline(GENERAL)
        timeline.add(PricePoint(2024, 1, GENERAL, "Arroz", "test", daily_grams=100, daily_kcal=350))
        timeline.add(PricePoint(2024, 2, GENERAL, "Arroz", "test", daily_grams=100, daily_kcal=370))

        summary = timeline.avg_energy()

        self.assertEqual(summary["avg"], 360)
        self.assertEqual(summary["variance"], 100)
        self.assertEqual(summary["std_dev"], 10)
        self.assertAlmostEqual(summary["coefficient_of_variation"], 10 / 360)
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["dates_used"], [(2024, 1), (2024, 2)])

    def test_food_keeps_one_timeline_per_region(self):
        food = Food("arroz", "Arroz")
        for region in (GENERAL, RURAL, URBAN):
            food.add_price_point(PricePoint(2024, 1, region, "Arroz", "test", cost_per_gram=1.0))
        self.assertEqual(set(food.price_timelines), {GENERAL, RURAL, URBAN})

    def test_food_summarizes_years_by_region(self):
        food = Food("arroz", "Arroz")
        food.add_price_point(PricePoint(2023, 1, GENERAL, "Arroz", "test"))
        food.add_price_point(PricePoint(2024, 1, GENERAL, "Arroz", "test"))
        food.add_price_point(PricePoint(2024, 2, GENERAL, "Arroz", "test"))
        food.add_price_point(PricePoint(2024, 1, RURAL, "Arroz", "test"))

        self.assertEqual(
            food.years_by_region(),
            {
                GENERAL: [2023, 2024],
                RURAL: [2024],
                URBAN: [],
            },
        )

    def test_food_returns_first_and_latest_price_by_region(self):
        food = Food("arroz", "Arroz")
        latest = PricePoint(2024, 5, GENERAL, "Arroz", "latest", price_per_100g=3.0)
        first = PricePoint(2023, 10, GENERAL, "Arroz", "first", price_per_100g=2.0)
        food.add_price_point(latest)
        food.add_price_point(first)

        self.assertIs(food.first_price(GENERAL), first)
        self.assertIs(food.latest_price(GENERAL), latest)
        self.assertIsNone(food.first_price(RURAL))
        self.assertIsNone(food.latest_price(RURAL))

    def test_food_returns_lowest_and_highest_price_by_region(self):
        food = Food("arroz", "Arroz")
        lowest = PricePoint(2024, 1, GENERAL, "Arroz", "low", price_per_100g=1.5)
        highest = PricePoint(2024, 2, GENERAL, "Arroz", "high", price_per_100g=4.0)
        food.add_price_point(PricePoint(2024, 3, GENERAL, "Arroz", "missing"))
        food.add_price_point(highest)
        food.add_price_point(lowest)

        self.assertIs(food.lowest_price(GENERAL), lowest)
        self.assertIs(food.highest_price(GENERAL), highest)
        self.assertIsNone(food.lowest_price(RURAL))
        self.assertIsNone(food.highest_price(RURAL))

    def test_food_returns_a_price_summary(self):
        food = Food("arroz", "Arroz")
        first_and_highest = PricePoint(
            2023, 1, GENERAL, "Arroz", "first", price_per_100g=4.0
        )
        latest_and_lowest = PricePoint(
            2024, 2, GENERAL, "Arroz", "latest", price_per_100g=2.0
        )
        food.add_price_point(latest_and_lowest)
        food.add_price_point(first_and_highest)

        self.assertEqual(
            food.price_summary(GENERAL),
            {
                "first": first_and_highest,
                "latest": latest_and_lowest,
                "lowest": latest_and_lowest,
                "highest": first_and_highest,
            },
        )

    def test_duplicate_region_and_month_is_rejected(self):
        food = Food("arroz", "Arroz")
        point = PricePoint(2024, 1, RURAL, "Arroz", "test")
        food.add_price_point(point)
        with self.assertRaises(ValueError):
            food.add_price_point(point)

    def test_food_can_plot_its_price_timelines(self):
        food = Food("arroz", "Arroz")
        food.add_price_point(
            PricePoint(2024, 1, GENERAL, "Arroz", "test", price_per_100g=2.5)
        )

        fig, ax = food.plot_timeline()

        self.assertEqual(ax.get_title(), "Evolución histórica del precio de Arroz")
        self.assertEqual(len(ax.lines), 1)
        self.assertEqual(list(ax.lines[0].get_ydata()), [2.5])
        fig.clf()

    def test_food_can_plot_only_the_selected_region(self):
        food = Food("arroz", "Arroz")
        food.add_price_point(PricePoint(2024, 1, GENERAL, "Arroz", "test", price_per_100g=2.5))
        food.add_price_point(PricePoint(2024, 1, RURAL, "Arroz", "test", price_per_100g=3.0))

        fig, ax = food.plot_timeline(region=RURAL)

        self.assertEqual(len(ax.lines), 1)
        self.assertEqual(ax.lines[0].get_label(), "Rural")
        self.assertEqual(list(ax.lines[0].get_ydata()), [3.0])
        fig.clf()

    def test_plot_rejects_an_invalid_region(self):
        food = Food("arroz", "Arroz")

        with self.assertRaisesRegex(ValueError, "Región inválida"):
            food.plot_timeline(region="otra")

    def test_plot_rejects_food_without_prices(self):
        food = Food("arroz", "Arroz")

        with self.assertRaisesRegex(ValueError, "no tiene precios"):
            food.plot_timeline()

    def test_catalog_merges_foods_and_redirects_aliases(self):
        catalog = FoodCatalog()
        target = catalog.add(Food("arroz", "Arroz", category="Cereales"), {"arroz"})
        source = catalog.add(Food("arroz_corriente", "Arroz corriente"), {"arroz corriente"})
        source.add_price_point(PricePoint(2024, 1, RURAL, "Arroz corriente", "test"))

        result = catalog.merge_foods("arroz", "arroz_corriente")

        self.assertIs(result, target)
        self.assertEqual(len(catalog), 1)
        self.assertIs(catalog.find_by_normalized_alias("arroz corriente"), target)
        self.assertIn("Arroz corriente", target.aliases)
        self.assertIsNotNone(target.price_timelines[RURAL].get(2024, 1))
        with self.assertRaises(KeyError):
            catalog.get("arroz_corriente")

    def test_catalog_merge_rejects_collisions_without_changes(self):
        catalog = FoodCatalog()
        target = catalog.add(Food("arroz", "Arroz"))
        source = catalog.add(Food("arroz_corriente", "Arroz corriente"))
        target.add_price_point(PricePoint(2024, 1, RURAL, "Arroz", "target"))
        source.add_price_point(PricePoint(2024, 1, RURAL, "Arroz corriente", "source"))

        with self.assertRaisesRegex(ValueError, "rural:2024-01"):
            catalog.merge_foods(target, source)

        self.assertEqual(len(catalog), 2)
        self.assertEqual(target.price_timelines[RURAL].get(2024, 1).source, "target")

    def test_catalog_remove_deletes_food_and_registered_aliases(self):
        catalog = FoodCatalog()
        food = catalog.add(Food("comida_compuesta", "Comida compuesta"), {"comida compuesta"})

        removed = catalog.remove("comida_compuesta")

        self.assertIs(removed, food)
        self.assertEqual(len(catalog), 0)
        self.assertIsNone(catalog.find_by_normalized_alias("comida compuesta"))
        with self.assertRaises(KeyError):
            catalog.get("comida_compuesta")


class CBAPipelineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_cba_catalog()

    def test_real_sources_are_unified(self):
        self.assertGreater(len(self.catalog), 0)
        self.assertTrue(any(RURAL in food.price_timelines for food in self.catalog))
        self.assertTrue(any(URBAN in food.price_timelines for food in self.catalog))

    def test_general_2024_point_is_mean_of_both_regions(self):
        for food in self.catalog:
            derived = [point for point in food.price_timelines.get(GENERAL, ()) if point.derived]
            if not derived:
                continue
            general = derived[0]
            rural = food.price_timelines[RURAL].get(general.year, general.month)
            urban = food.price_timelines[URBAN].get(general.year, general.month)
            self.assertIsNotNone(rural)
            self.assertIsNotNone(urban)
            self.assertAlmostEqual(general.cost_per_gram, (rural.cost_per_gram + urban.cost_per_gram) / 2)
            return
        self.fail("No se generó ninguna media regional")


class CBAPriceNormalizationTests(unittest.TestCase):
    def test_base_price_is_normalized_from_grams(self):
        price = CBADataLoader._base_price_per_100g(
            "Frijoles negros, secos", 9.08, 454, "Gramos"
        )

        self.assertAlmostEqual(price, 2.0)

    def test_milliliters_are_converted_with_product_density(self):
        price = CBADataLoader._base_price_per_100g(
            "Leche entera líquida industrializada", 10.30, 1000, "Mililitros"
        )

        self.assertAlmostEqual(price, 1.0)

    def test_liquid_without_known_density_has_no_normalized_price(self):
        price = CBADataLoader._base_price_per_100g(
            "Bebida líquida sin densidad configurada", 5.0, 1000, "Mililitros"
        )

        self.assertIsNone(price)


class INCAPNutritionEnricherTests(unittest.TestCase):
    def setUp(self):
        loader = SimpleNamespace(
            NORMALIZED_NAME_COL="nombre_normalizado",
            categories={
                1: "LÁCTEOS Y SIMILARES",
                9: "LEGUMINOSAS",
                12: "FRUTAS Y JUGOS NATURALES",
            },
            data=pd.DataFrame(
                [
                    {
                        "codigo": "9001",
                        "nombre": "FRIJOL NEGRO, SECO",
                        "nombre_normalizado": "frijol negro seco",
                        "energia_kcal": "341",
                    },
                    {
                        "codigo": "12001",
                        "nombre": "MANZANA CON CASCARA",
                        "nombre_normalizado": "manzana con cascara",
                        "energia_kcal": "52",
                    },
                    {
                        "codigo": "9002",
                        "nombre": "FRIJOL NEGRO, COCIDO",
                        "nombre_normalizado": "frijol negro cocido",
                        "energia_kcal": "130",
                    },
                ]
            ),
        )
        self.enricher = INCAPNutritionEnricher(loader)

    def test_automatic_enrichment_uses_energy_and_keeps_alternatives(self):
        catalog = FoodCatalog()
        food = catalog.add(Food("frijol", "Frijol", aliases={"frijol negro"}))
        food.add_price_point(
            PricePoint(
                2024, 1, GENERAL, "Frijol", "test",
                daily_grams=100, daily_kcal=340,
            )
        )

        result = self.enricher.enrich(
            catalog,
            initial_energy_tolerance=250,
            maximum_energy_tolerance=250,
        )

        self.assertEqual(result, {"matched": 1, "unmatched": 0})
        self.assertEqual(food.nutrition.incap_code, "9001")
        self.assertEqual(food.nutrition_candidates["codigo"].tolist(), ["9002"])
        self.assertIn("energy_difference_kcal", food.nutrition_candidates.columns)

    def test_enrich_food_returns_and_updates_the_same_food(self):
        food = Food("frijol", "Frijol")

        result = self.enricher.enrich_food(9, "frijol negro seco", 0.50, food)

        self.assertIs(result, food)
        self.assertEqual(food.nutrition.incap_code, "9001")
        self.assertEqual(food.nutrition.category, "LEGUMINOSAS")
        self.assertEqual(food.nutrition.values_per_100g["energia_kcal"], 341.0)

    def test_enrich_food_accepts_the_category_name(self):
        food = Food("manzana", "Manzana")

        self.enricher.enrich_food(
            "FRUTAS Y JUGOS NATURALES", "manzana con cascara", 0.50, food
        )

        self.assertEqual(food.nutrition.incap_code, "12001")

    def test_enrich_food_keeps_food_unchanged_without_a_match(self):
        food = Food("frijol", "Frijol")

        result = self.enricher.enrich_food(12, "frijol negro seco", 0.90, food)

        self.assertIs(result, food)
        self.assertIsNone(food.nutrition)

    def test_enrich_food_rejects_invalid_probability(self):
        with self.assertRaisesRegex(ValueError, "entre 0 y 1"):
            self.enricher.enrich_food(9, "frijol", 1.1, Food("frijol", "Frijol"))

    def test_search_food_candidates_exposes_ranked_category_matches(self):
        matches = self.enricher.search_food_candidates(
            category=9, name="frijol negro", min_probability=0.25, top_n=5
        )

        self.assertEqual(matches["codigo"].tolist(), ["9001", "9002"])
        self.assertIn("match_probability", matches.columns)
        self.assertIn("match_methods", matches.columns)

    def test_search_food_candidates_filters_out_other_categories(self):
        matches = self.enricher.search_food_candidates(
            category="FRUTAS Y JUGOS NATURALES",
            name="frijol negro",
            min_probability=0.90,
        )

        self.assertTrue(matches.empty)

    def test_search_food_candidates_can_filter_by_energy(self):
        matches = self.enricher.search_food_candidates(
            category=9,
            name="frijol negro",
            min_probability=0.25,
            energy_per_100g=340,
            energy_tolerance=10,
        )

        self.assertEqual(matches["codigo"].tolist(), ["9001"])
        self.assertEqual(matches.iloc[0]["energy_difference_kcal"], 1)
        self.assertAlmostEqual(matches.iloc[0]["energy_difference_pct"], 100 / 340)

    def test_energy_filter_is_optional(self):
        matches = self.enricher.search_food_candidates(
            category=9, name="frijol negro", min_probability=0.25
        )

        self.assertEqual(set(matches["codigo"]), {"9001", "9002"})
        self.assertNotIn("energy_difference_kcal", matches.columns)

    def test_energy_tolerance_requires_a_reference(self):
        with self.assertRaisesRegex(ValueError, "requiere energy_per_100g"):
            self.enricher.search_food_candidates(
                category=9, name="frijol", energy_tolerance=20
            )

    def test_empty_search_preserves_result_columns(self):
        matches = self.enricher.search_food_candidates(
            category=9,
            name="sin coincidencia",
            min_probability=1.0,
            energy_per_100g=340,
            energy_tolerance=1,
        )

        self.assertTrue(matches.empty)
        self.assertIn("codigo", matches.columns)
        self.assertIn("energy_difference_kcal", matches.columns)

    def test_search_can_allow_candidates_without_strong_match_methods(self):
        strict = self.enricher.search_food_candidates(
            category=9, name="frijol diferente", min_probability=0.0
        )
        tolerant = self.enricher.search_food_candidates(
            category=9,
            name="frijol diferente",
            min_probability=0.0,
            require_match_methods=False,
        )

        self.assertLess(len(strict), len(tolerant))

    def test_category_uses_the_code_prefix_before_the_last_three_digits(self):
        self.assertEqual(
            self.enricher._category_for("1016"),
            "LÁCTEOS Y SIMILARES",
        )


class CBAPersistenceTests(unittest.TestCase):
    def test_catalog_pickle_round_trip(self):
        catalog = FoodCatalog()
        catalog.add(Food("arroz", "Arroz"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "catalog.pkl"
            self.assertEqual(save_catalog_pickle(catalog, output), output)
            loaded = load_catalog_pickle(output)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded.get("arroz").name, "Arroz")

    def test_pipeline_consolidates_and_saves_without_incap(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cba.pkl"
            catalog, summary = process_cba_pipeline(output_path=output, enrich=False)
            loaded = load_catalog_pickle(output)

        self.assertEqual(summary, {"foods": 77, "matched": 0, "unmatched": 77})
        self.assertEqual(len(catalog), 77)
        self.assertEqual(len(loaded), 77)
        self.assertIn("Arroz corriente", loaded.get("arroz").aliases)


if __name__ == "__main__":
    unittest.main()
