from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional, Any
from difflib import SequenceMatcher
import unicodedata
from dataclasses import dataclass, field
from data_loaders.data_loader import DataLoader

class TimeLine:
    key_size: int
    data: List[Tuple[Tuple[int, ...], Any]]
    MONTHS: list = [
    'enero', 
    'febrero',
    'marzo', 
    'abril', 
    'mayo',
    'junio',
    'julio',
    'agosto',
    'septiembre',
    'octubre',
    'noviembre',
    'diciembre' 
    ]

    def __init__(self, key_size: int = 1):
        self.key_size = key_size
        self.data = []

    def add_item(self, new_item: Any, key: Tuple[int, ...]):

        if not isinstance(key, tuple):
            raise TypeError("key must be a tuple")

        if len(key) != self.key_size:
            raise ValueError(
                f"Cannot add item with key length {len(key)}. "
                f"Expected key length: {self.key_size}"
            )

        for index, current_item in enumerate(self.data):
            current_key = current_item[0]

            if key < current_key:
                self.data.insert(index, (key, new_item))
                return

        self.data.append((key, new_item))

    def get_item(self, key: Tuple[int, ...]):
        if not isinstance(key, tuple):
            raise TypeError("key must be a tuple")

        if len(key) != self.key_size:
            raise ValueError(
                f"Cannot get item with key length {len(key)}. "
                f"Expected key length: {self.key_size}"
            )

        for current_key, current_item in self.data:
            if key == current_key:
                return current_item

            if current_key > key:
                return None

        return None
    
    @staticmethod
    def month_name_to_index(month_name: str):
        month_name = month_name.lower()
        try: 
            month_index = TimeLine.MONTHS.index(month_name)     
            return month_index
        except ValueError: 
            raise ValueError(f'Month {month_name} is not a valid month name, make sure its included in next list {TimeLine.MONTHS}')

@dataclass
class ProductPoint:
    name: str
    cost_per_gram: float
    daily_kcal: float
    daily_grams: float
    daily_cost: float
    days_in_month: int
    base_quantity: float
    energy_per_100g_kcal: float
    region: str

@dataclass
class ProductNutrition:
    code: str
    category: str
    name: str
    energy_per_100g_kcal: float
    water_pct: float
    consumable_fraction_pct: float
    protein_g: float
    total_fat_g: float
    saturated_fatty_acid_g: float
    monounsaturated_fatty_acid_g: float
    polyunsaturated_fatty_acid_g: float
    cholesterol_mg: float
    carbohydrates_g: float
    sugars_g: float
    ash_g: float
    fiber_g: float
    calcium_mg: float
    iron_mg: float
    magnesium_mg: float
    phosphorus_mg: float
    potassium_mg: float
    sodium_mg: float
    zinc_mg: float
    copper_mg: float
    selenium_mcg: float
    vitamin_c_mg: float
    thiamine_mg: float
    riboflavin_mg: float
    niacin_mg: float
    pantothenic_acid_mg: float
    vitamin_b6_mg: float
    folic_acid_mcg: float
    food_folate_mcg: float
    folate_dfe_mcg: float
    vitamin_b12_mcg: float
    vitamin_a_rae_mcg: float
    retinol_mcg: float
    beta_carotene_mcg: float
    vitamin_e_mg: float
    vitamin_d_mcg: float
    vitamin_k_mcg: float
    

@dataclass
class Product:
    name: str
    energy_per_100g_kcal: float
    timelines: Dict[str, TimeLine]
    nutrition: List[Tuple[float, ProductNutrition]]
    nutrtition_meta: str
    nutrition_similarity_score: float
    simple_name = None

    def __init__(
            self, 
            name: str,
            product_point: ProductPoint, 
            pp_year: int,
            pp_month: int, 
            energy_per_100g_kcal=None, 
            nutrition: List[Tuple[float, ProductNutrition]] = None, 
            nutrtition_meta:str = None,
            nutrition_similarity_score: float = None
            ):
        self.name = name
        self.energy_per_100g_kcal = energy_per_100g_kcal
        self.nutrition = nutrition
        self.nutrtition_meta = nutrtition_meta
        self.nutrition_similarity_score = nutrition_similarity_score

        self.timeline = TimeLine(key_size=2)
        self.add_product_point_to_timeline((pp_year, pp_month), product_point)

    def add_product_point_to_timeline(
            self, 
            key: Tuple,
            product_point: ProductPoint
            ):
        self.timeline.add_item(product_point, key)

    def set_nutrition(self, nutrition: ProductNutrition):
        self.nutrition = nutrition
     
class Products:
    items: List[Product]

    def __init__(self, regions:List[str] = []):
        self.items: List[Product] = []

    def add_data(
        self,
        region: str,
        name: str,
        energy_per_100g_kcal: float,
        year: int,
        month_name: str, 
        cost_per_gram: float,
        daily_kcal: float,
        daily_grams: float,
        days_in_month: int,
        base_quantity: float,
        daily_cost: float, 
        nutrition: ProductNutrition = None, 
        nutrition_meta: str = None, 
        force_new_product: bool = False,
        nutrition_similarity_score: float = None
    ):
        existing_product = None
        existing_product: Optional[Product] = self.__find_existing_product(name)
        
        product_point = ProductPoint(name, cost_per_gram, daily_kcal, daily_grams, daily_cost, days_in_month, base_quantity, energy_per_100g_kcal, region)
        
        if existing_product is not None and not force_new_product:
            existing_product.add_product_point_to_timeline((year, TimeLine.month_name_to_index(month_name)), product_point)
            print(f"Producto ({name} ; {year}, {month_name} ) agredado a timeline de Producto existente {existing_product.name}")
            product = existing_product
        else: 
            product = Product(name, product_point, year, TimeLine.month_name_to_index(month_name), energy_per_100g_kcal, nutrition, nutrition_meta, nutrition_similarity_score)
            self.items.append(product)
            print(f"Nuevo producto creado para {name} ; {year}, {month_name}")
        return product

    def __find_existing_product(
        self,
        name: str,
        min_similarity: float = 0.85,
    ) -> Optional[Product]:
        """
        Busca si ya existe un producto en la región por nombre normalizado.

        Primero revisa coincidencia exacta.
        Luego revisa similitud textual.
        """

        normalized_name = self._normalize_text(name)

        for product in self.items:
            existing_name = self._normalize_text(product.name)

            if normalized_name == existing_name:
                return product

        best_product = None
        best_score = 0.0

        for product in self.items:
            existing_name = self._normalize_text(product.name)

            results = DataLoader.score_search_match(normalized_name, existing_name)

            score = SequenceMatcher(
                None,
                normalized_name,
                existing_name,
            ).ratio() 

            if score > best_score:
                best_score = score
                best_product = product

        if best_score >= min_similarity:
            return best_product

        return None

    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto para comparar nombres:
        - minúsculas
        - sin tildes
        - sin espacios dobles
        """

        if text is None:
            return ""

        text = str(text).lower().strip()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            char for char in text
            if unicodedata.category(char) != "Mn"
        )

        return " ".join(text.split())