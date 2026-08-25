from dataclasses import dataclass

from ..domain.familia import Family
from .service import NutritionEvaluator


@dataclass(frozen=True)
class HouseholdRequirementsResult:
    individual: dict[str, dict]


class HouseholdRequirements:
    """Evalúa a cada integrante sin introducir reglas dentro de ``Family``."""

    @staticmethod
    def calculate(family: Family) -> HouseholdRequirementsResult:
        return HouseholdRequirementsResult({person.nombre: NutritionEvaluator.evaluate(person) for person in family.members})
