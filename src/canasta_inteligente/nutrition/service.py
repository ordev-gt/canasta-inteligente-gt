from ..domain.persona import Persona
from .evaluation._implementation import evaluacion_de_requerimientos_diarios


class NutritionEvaluator:
    """Fachada estable para evaluar requerimientos nutricionales individuales."""

    @staticmethod
    def evaluate(person: Persona) -> dict:
        return evaluacion_de_requerimientos_diarios(person)


__all__ = ["NutritionEvaluator", "evaluacion_de_requerimientos_diarios"]
