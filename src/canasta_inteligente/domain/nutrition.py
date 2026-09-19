from dataclasses import dataclass, field
from typing import Any


@dataclass
class NutritionProfile:
    """Composición por 100 g de porción comestible proveniente del INCAP."""

    incap_code: str | None
    incap_name: str
    category: str | None
    values_per_100g: dict[str, Any] = field(default_factory=dict)

    def set_value(self, nutrient: str, value: Any) -> None:
        """Asigna o reemplaza el valor de un nutriente."""
        self.values_per_100g[nutrient] = value

    def update_values(self, values: dict[str, Any]) -> None:
        """Actualiza varios nutrientes simultáneamente."""
        self.values_per_100g.update(values)