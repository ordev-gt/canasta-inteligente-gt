import unittest

from canasta_inteligente.application.cba_pipeline import build_cba_catalog
from canasta_inteligente.data.ine.cba_loader import CBADataLoader
from canasta_inteligente.domain.food import Food, FoodCatalog
from canasta_inteligente.domain.prices import GENERAL, RURAL, URBAN, PricePoint


class PriceDomainTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
