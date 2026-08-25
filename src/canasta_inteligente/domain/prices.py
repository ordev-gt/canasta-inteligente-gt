from dataclasses import dataclass
from typing import Iterator


GENERAL = "general"
RURAL = "rural"
URBAN = "urbana"
VALID_REGIONS = frozenset({GENERAL, RURAL, URBAN})


@dataclass(frozen=True)
class PricePoint:
    year: int
    month: int
    region: str
    original_name: str
    source: str
    cost_per_gram: float | None = None
    price_per_100g: float | None = None
    daily_grams: float | None = None
    monthly_grams: float | None = None
    daily_cost: float | None = None
    monthly_cost: float | None = None
    daily_kcal: float | None = None
    monthly_kcal: float | None = None
    base_quantity: float | None = None
    base_unit: str | None = None
    base_unit_price: float | None = None
    derived: bool = False

    def __post_init__(self) -> None:
        if self.region not in VALID_REGIONS:
            raise ValueError(f"Región inválida: {self.region}")
        if not 1 <= self.month <= 12:
            raise ValueError(f"Mes inválido: {self.month}")


class PriceTimeline:
    """Serie de precios de una única región, indexada por ``(año, mes)``."""

    def __init__(self, region: str):
        if region not in VALID_REGIONS:
            raise ValueError(f"Región inválida: {region}")
        self.region = region
        self._points: dict[tuple[int, int], PricePoint] = {}

    def add(self, point: PricePoint, *, replace: bool = False) -> None:
        if point.region != self.region:
            raise ValueError(f"El punto {point.region} no pertenece a la serie {self.region}")
        key = (point.year, point.month)
        if key in self._points and not replace:
            raise ValueError(f"Ya existe una observación {self.region} para {key}")
        self._points[key] = point

    def get(self, year: int, month: int) -> PricePoint | None:
        return self._points.get((year, month))

    def avg_daily_grams(self):
        accumulated_grams = 0
        for _, point in self._points.items():
            accumulated_grams += point.daily_grams
        return accumulated_grams / len(self._points)
    
    def __contains__(self, key: tuple[int, int]) -> bool:
        return key in self._points

    def __iter__(self) -> Iterator[PricePoint]:
        for key in sorted(self._points):
            yield self._points[key]

    def __len__(self) -> int:
        return len(self._points)

    def keys(self) -> set[tuple[int, int]]:
        return set(self._points)
