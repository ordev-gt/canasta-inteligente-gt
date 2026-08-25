from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NutritionProfile:
    """Composición por 100 g de porción comestible proveniente del INCAP."""

    incap_code: str | None
    incap_name: str
    category: str | None
    values_per_100g: dict[str, Any] = field(default_factory=dict)
