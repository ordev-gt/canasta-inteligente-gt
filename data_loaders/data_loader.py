from typing import Dict, Any, Tuple, List
from difflib import SequenceMatcher
from abc import ABC, abstractmethod
import unicodedata
import pickle
import os
import re

import pandas as pd
from rapidfuzz import fuzz
from pathlib import Path

class DataLoader(ABC):
    """
    Clase base abstracta para cargadores de datos.

    Provee:
    - Estructura común de datos mediante self.data.
    - Normalización textual.
    - Búsqueda aproximada de registros.
    - Caché genérica basada en CACHE_SCHEMA.

    Las clases hijas deben definir:
    - CACHE_SCHEMA
    - load_data()
    """
    BASE_DIR = Path(__file__).resolve().parent
    CACHE_DIR = BASE_DIR / "cache"
    NORMALIZED_NAME_COL: str = "nombre_normalizado"

    CACHE_SCHEMA: Dict[str, str] = {}

    def __init__(self):
        self.data: pd.DataFrame | None = None

    @abstractmethod
    def load_data(self, *args, **kwargs) -> pd.DataFrame:
        """
        Carga los datos desde la fuente correspondiente.

        Returns:
            pd.DataFrame: Datos cargados y procesados.
        """
        pass

    def _save_to_cache(self) -> None:
        """
        Guarda en caché los atributos definidos en CACHE_SCHEMA.
        """
        if not self.CACHE_SCHEMA:
            return

        for attr_name, filename in self.CACHE_SCHEMA.items():
            value = getattr(self, attr_name, None)

            cache_path = Path(filename)
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            with open(cache_path, "wb") as f:
                pickle.dump(value, f)

    def _get_from_cache(self) -> bool:
        """
        Carga desde caché los atributos definidos en CACHE_SCHEMA.
        """
        if not self.CACHE_SCHEMA:
            return False

        loaded_values = {}

        try:
            for attr_name, filename in self.CACHE_SCHEMA.items():
                cache_path = Path(filename)

                if not cache_path.exists():
                    print(f"Cache file not found: {cache_path}")
                    return False

                with open(cache_path, "rb") as f:
                    loaded_values[attr_name] = pickle.load(f)

            for attr_name, value in loaded_values.items():
                setattr(self, attr_name, value)

            print("Loaded data from cache serialized data")
            return True

        except Exception as error:
            print(
                "Couldnt load from cache serialized data. "
                "The cache may have been created with optional pandas "
                f"dependencies that are missing in this environment: {error}"
            )
            return False

    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto para comparación aproximada.
        """
        if text is None:
            return ""

        text = str(text).lower().strip()

        text = "".join(
            char for char in unicodedata.normalize("NFD", text)
            if unicodedata.category(char) != "Mn"
        )

        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        stopwords = {
            "de", "del", "la", "el", "los", "las", "y", "con",
            "sin", "para", "en", "por", "tipo"
        }

        tokens = [
            token for token in text.split()
            if token not in stopwords
        ]

        return " ".join(tokens)

    def _ensure_normalized_columns(
        self,
        df: pd.DataFrame,
        source_column: str = "nombre"
    ) -> pd.DataFrame:
        """
        Asegura que exista una columna normalizada para búsqueda.
        """
        if source_column not in df.columns:
            raise ValueError(
                f"El DataFrame debe contener una columna llamada '{source_column}'."
            )

        df = df.copy()

        df[self.NORMALIZED_NAME_COL] = (
            df[source_column]
            .fillna("")
            .apply(self._normalize_text)
        )

        return df

    @staticmethod
    def char_ngrams(text: str, n: int = 3) -> set:
        text = f" {text} "

        if len(text) < n:
            return {text.strip()} if text.strip() else set()

        return {
            text[i:i + n]
            for i in range(len(text) - n + 1)
        }

    @staticmethod
    def jaccard_similarity(
        a: str,
        b: str,
        ngram_size: int = 3
    ) -> float:
        grams_a = DataLoader.char_ngrams(a, n=ngram_size)
        grams_b = DataLoader.char_ngrams(b, n=ngram_size)

        if not grams_a or not grams_b:
            return 0.0

        return len(grams_a & grams_b) / len(grams_a | grams_b)

    @staticmethod
    def sequence_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def token_sort_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return fuzz.token_sort_ratio(a, b) / 100

    @staticmethod
    def token_set_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return fuzz.token_set_ratio(a, b) / 100

    @staticmethod
    def _partial_similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return fuzz.partial_ratio(a, b) / 100

    @staticmethod
    def score_search_match(
        query_normalized: str,
        candidate_normalized: str,
        method_threshold: float = 0.75,
        ngram_size: int = 3
    ) -> Tuple[float, List[str], Dict[str, float]]:
        """
        Calcula probabilidad de coincidencia entre una búsqueda y un candidato.
        """
        if not query_normalized or not candidate_normalized:
            return 0.0, [], {}

        exact_score = 1.0 if query_normalized == candidate_normalized else 0.0

        contains_score = (
            1.0
            if query_normalized in candidate_normalized
            or candidate_normalized in query_normalized
            else 0.0
        )

        scores = {
            "exact": exact_score,
            "contains": contains_score,
            "sequence": DataLoader.sequence_similarity(
                query_normalized,
                candidate_normalized
            ),
            "token_sort": DataLoader.token_sort_similarity(
                query_normalized,
                candidate_normalized
            ),
            "token_set": DataLoader.token_set_similarity(
                query_normalized,
                candidate_normalized
            ),
            "partial": DataLoader._partial_similarity(
                query_normalized,
                candidate_normalized
            ),
            "char_ngram_jaccard": DataLoader.jaccard_similarity(
                query_normalized,
                candidate_normalized,
                ngram_size
            ),
        }

        probability = sum(scores.values()) / len(scores)

        valid_methods = [
            method
            for method, score in scores.items()
            if score >= method_threshold
        ]

        return probability, valid_methods, scores
    
    
    def search_word_matches(
        self,
        palabra: str,
        target_field: str | None = None,
        top_n: int = 10,
        min_probability: float = 0.55,
        method_threshold: float = 0.75,
        ngram_size: int = 3
    ) -> List[Tuple[pd.Series, float, List[str], Dict[str, float]]]:
        """
        Busca registros similares dentro de self.data.

        Returns:
            List[Tuple[pd.Series, float, List[str], Dict[str, float]]]
        """
        if self.data is None or self.data.empty:
            return []

        if ngram_size < 2:
            raise ValueError("ngram_size debe ser mayor o igual a 2.")

        if ngram_size > 5:
            raise ValueError("ngram_size no debería ser mayor a 5.")

        target_field = target_field or self.NORMALIZED_NAME_COL

        if target_field not in self.data.columns:
            raise KeyError(
                f"Target field '{target_field}' does not exist in data."
            )

        query_normalized = self._normalize_text(palabra)

        if not query_normalized:
            return []

        results = []

        for _, row in self.data.iterrows():
            candidate_value = row.get(target_field, "")

            if target_field == self.NORMALIZED_NAME_COL:
                candidate_normalized = str(candidate_value or "")
            else:
                candidate_normalized = self._normalize_text(candidate_value)

            probability, valid_methods, method_scores = DataLoader.score_search_match(
                query_normalized=query_normalized,
                candidate_normalized=candidate_normalized,
                method_threshold=method_threshold,
                ngram_size=ngram_size
            )

            if probability >= min_probability and valid_methods:
                results.append(
                    (
                        row,
                        round(float(probability), 4),
                        valid_methods,
                        {
                            method: round(float(score), 4)
                            for method, score in method_scores.items()
                        }
                    )
                )

        results.sort(key=lambda item: item[1], reverse=True)

        return results[:top_n]
