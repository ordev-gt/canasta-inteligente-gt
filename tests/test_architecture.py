import unittest

from canasta_inteligente.data.matcher import FoodMatcher
from canasta_inteligente.data.text import TextNormalizer
from canasta_inteligente.domain.familia import Family
from canasta_inteligente.domain.persona import Persona
from canasta_inteligente.nutrition.household import HouseholdRequirements
from canasta_inteligente.nutrition.service import NutritionEvaluator


class ArchitectureTests(unittest.TestCase):
    def test_text_matching_is_independent_from_loaders(self):
        self.assertEqual(TextNormalizer.normalize("Café de grano"), "cafe grano")
        probability, methods, _ = FoodMatcher.score("cafe grano", "cafe grano")
        self.assertEqual(probability, 1.0)
        self.assertIn("exact", methods)

    def test_family_and_nutrition_facades(self):
        person = Persona("Adulto", 25, "hombre", 65, naf="low", altura=1.70)
        family = Family([person])
        result = HouseholdRequirements.calculate(family)
        self.assertIn("Adulto", result.individual)
        self.assertIn("energia", NutritionEvaluator.evaluate(person))


if __name__ == "__main__":
    unittest.main()
