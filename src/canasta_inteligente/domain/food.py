from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

from .nutrition import NutritionProfile
from .prices import GENERAL, RURAL, URBAN, VALID_REGIONS, PricePoint, PriceTimeline


@dataclass
class Food:
    id: str
    name: str
    category: str | None = None
    aliases: set[str] = field(default_factory=set)
    price_timelines: dict[str, PriceTimeline] = field(default_factory=dict)
    nutrition: NutritionProfile | None = None
    nutrition_match_score: float | None = None
    nutrition_match_methods: tuple[str, ...] = ()

    def add_price_point(self, point: PricePoint, *, replace: bool = False) -> None:
        timeline = self.price_timelines.setdefault(point.region, PriceTimeline(point.region))
        timeline.add(point, replace=replace)
        self.aliases.add(point.original_name)

    def timeline(self, region: str) -> PriceTimeline:
        return self.price_timelines.setdefault(region, PriceTimeline(region))

    def years_by_region(self) -> dict[str, list[int]]:
        """Devuelve los años con observaciones disponibles en cada región."""
        return {
            region: sorted({point.year for point in self.price_timelines.get(region, ())})
            for region in (GENERAL, RURAL, URBAN)
        }

    def first_price(self, region: str) -> PricePoint | None:
        """Devuelve la primera observación cronológica de una región."""
        timeline = self.price_timelines.get(region)
        return next(iter(timeline), None) if timeline is not None else None

    def latest_price(self, region: str) -> PricePoint | None:
        """Devuelve la última observación cronológica de una región."""
        timeline = self.price_timelines.get(region)
        return next(reversed(list(timeline)), None) if timeline is not None else None

    def lowest_price(self, region: str) -> PricePoint | None:
        """Devuelve la observación con el menor precio por 100 g."""
        timeline = self.price_timelines.get(region)
        points = (
            (point for point in timeline if point.price_per_100g is not None)
            if timeline is not None
            else ()
        )
        return min(points, key=lambda point: point.price_per_100g, default=None)

    def highest_price(self, region: str) -> PricePoint | None:
        """Devuelve la observación con el mayor precio por 100 g."""
        timeline = self.price_timelines.get(region)
        points = (
            (point for point in timeline if point.price_per_100g is not None)
            if timeline is not None
            else ()
        )
        return max(points, key=lambda point: point.price_per_100g, default=None)

    def price_summary(self, region: str) -> dict[str, PricePoint | None]:
        """Resume los puntos cronológicos y precios extremos de una región."""
        return {
            "first": self.first_price(region),
            "latest": self.latest_price(region),
            "lowest": self.lowest_price(region),
            "highest": self.highest_price(region),
        }

    def plot_timeline(self, region: str | None = None):
        """Grafica el precio por 100 g de una región o de todas ellas.

        Devuelve la figura y los ejes de Matplotlib para permitir que quien llama
        personalice o guarde la gráfica. Los puntos que no tienen precio por
        100 gramos se omiten. Si ``region`` es ``None``, grafica todas las
        regiones disponibles.
        """
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt

        if region is not None and region not in VALID_REGIONS:
            raise ValueError(f"Región inválida: {region}")

        fig, ax = plt.subplots(figsize=(14, 6))
        plotted_regions = 0
        timelines = (
            ((region, self.price_timelines.get(region)),)
            if region is not None
            else self.price_timelines.items()
        )

        for current_region, timeline in timelines:
            if timeline is None:
                continue
            points = [point for point in timeline if point.price_per_100g is not None]
            if not points:
                continue

            dates = [datetime(point.year, point.month, 1) for point in points]
            prices = [point.price_per_100g for point in points]
            ax.plot(dates, prices, marker="o", markersize=3, label=current_region.title())
            plotted_regions += 1

        if not plotted_regions:
            plt.close(fig)
            region_detail = f" en la región {region}" if region is not None else ""
            raise ValueError(f"{self.name} no tiene precios por 100 g{region_detail} para graficar")

        ax.set_title(f"Evolución histórica del precio de {self.name}")
        ax.set_xlabel("Año")
        ax.set_ylabel("Precio por 100 g (Q)")
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(True, alpha=0.3)
        if plotted_regions > 1:
            ax.legend(title="Región")
        fig.autofmt_xdate()
        fig.tight_layout()
        return fig, ax


class FoodCatalog:
    """Colección de alimentos canónicos compartida por todas las fuentes."""

    def __init__(self) -> None:
        self._foods: dict[str, Food] = {}
        self._aliases: dict[str, str] = {}

    def add(self, food: Food, normalized_aliases: set[str] | None = None) -> Food:
        if food.id in self._foods:
            raise ValueError(f"Ya existe el alimento canónico {food.id}")
        self._foods[food.id] = food
        for alias in normalized_aliases or set():
            self._aliases[alias] = food.id
        return food

    def register_alias(self, food: Food, alias: str, normalized_alias: str) -> None:
        food.aliases.add(alias)
        self._aliases[normalized_alias] = food.id

    def find_by_normalized_alias(self, alias: str) -> Food | None:
        food_id = self._aliases.get(alias)
        return self._foods.get(food_id) if food_id else None

    def get(self, food_id: str) -> Food:
        return self._foods[food_id]

    def merge_foods(
        self,
        target: str | Food,
        source: str | Food,
        *,
        replace: bool = False,
    ) -> Food:
        """Fusiona ``source`` dentro de ``target`` y elimina el alimento origen.

        ``target`` y ``source`` pueden ser identificadores o instancias de
        :class:`Food` pertenecientes al catálogo. Si hay observaciones para la
        misma región, año y mes, se produce un error salvo que ``replace`` sea
        verdadero; en ese caso prevalece la observación del alimento origen.
        """
        target_food = self._resolve_member(target)
        source_food = self._resolve_member(source)
        if target_food is source_food:
            raise ValueError("El alimento destino y el origen deben ser diferentes")

        collisions = []
        for region, source_timeline in source_food.price_timelines.items():
            target_timeline = target_food.price_timelines.get(region)
            if target_timeline is not None:
                collisions.extend((region, year, month) for year, month in target_timeline.keys() & source_timeline.keys())
        if collisions and not replace:
            details = ", ".join(f"{region}:{year}-{month:02d}" for region, year, month in sorted(collisions))
            raise ValueError(f"Hay observaciones duplicadas al fusionar: {details}")

        for source_timeline in source_food.price_timelines.values():
            for point in source_timeline:
                target_food.add_price_point(point, replace=replace)

        target_food.aliases.update(source_food.aliases)
        target_food.aliases.add(source_food.name)
        if target_food.category is None:
            target_food.category = source_food.category
        if target_food.nutrition is None:
            target_food.nutrition = source_food.nutrition
            target_food.nutrition_match_score = source_food.nutrition_match_score
            target_food.nutrition_match_methods = source_food.nutrition_match_methods

        for alias, food_id in tuple(self._aliases.items()):
            if food_id == source_food.id:
                self._aliases[alias] = target_food.id
        del self._foods[source_food.id]
        return target_food

    def _resolve_member(self, food: str | Food) -> Food:
        food_id = food if isinstance(food, str) else food.id
        member = self._foods.get(food_id)
        if member is None or (isinstance(food, Food) and member is not food):
            raise ValueError(f"El alimento {food_id!r} no pertenece al catálogo")
        return member

    def __iter__(self) -> Iterator[Food]:
        return iter(self._foods.values())

    def __len__(self) -> int:
        return len(self._foods)

    @property
    def items(self) -> list[Food]:
        return list(self._foods.values())


# Alias temporales para consumidores anteriores al nuevo modelo.
Product = Food
Products = FoodCatalog
ProductPoint = PricePoint
ProductNutrition = NutritionProfile
TimeLine = PriceTimeline
