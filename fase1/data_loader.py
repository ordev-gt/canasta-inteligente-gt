from typing import Dict, Any, Tuple, List
from difflib import SequenceMatcher
from abc import ABC, abstractmethod
import unicodedata
import pickle
import os
import re

import pandas as pd
from rapidfuzz import fuzz


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

        CACHE_SCHEMA debe tener la forma:
            {
                "nombre_atributo": "ruta/archivo.pkl"
            }

        Ejemplo:
            {
                "data": "./cache/incap_data.pkl",
                "categories": "./cache/incap_categories.pkl"
            }
        """
        if not self.CACHE_SCHEMA:
            return

        for attr_name, filename in self.CACHE_SCHEMA.items():
            value = getattr(self, attr_name, None)

            directory = os.path.dirname(filename)
            if directory:
                os.makedirs(directory, exist_ok=True)

            with open(filename, "wb") as f:
                pickle.dump(value, f)

    def _get_from_cache(self) -> bool:
        """
        Carga desde caché los atributos definidos en CACHE_SCHEMA.

        Si todos los archivos definidos existen y pueden cargarse, asigna cada
        valor al atributo correspondiente de la instancia.

        Returns:
            bool: True si la caché se cargó correctamente, False si falló.
        """
        if not self.CACHE_SCHEMA:
            return False

        loaded_values: Dict[str, Any] = {}

        try:
            for attr_name, filename in self.CACHE_SCHEMA.items():
                with open(filename, "rb") as f:
                    loaded_values[attr_name] = pickle.load(f)

            for attr_name, value in loaded_values.items():
                setattr(self, attr_name, value)

            print("Loaded data from cache serialized data")
            return True

        except Exception:
            print("Couldnt load from caches serialized data")
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

    def __char_ngrams(self, text: str, n: int = 3) -> set:
        text = f" {text} "

        if len(text) < n:
            return {text.strip()} if text.strip() else set()

        return {
            text[i:i + n]
            for i in range(len(text) - n + 1)
        }

    def __jaccard_similarity(
        self,
        a: str,
        b: str,
        ngram_size: int = 3
    ) -> float:
        grams_a = self.__char_ngrams(a, n=ngram_size)
        grams_b = self.__char_ngrams(b, n=ngram_size)

        if not grams_a or not grams_b:
            return 0.0

        return len(grams_a & grams_b) / len(grams_a | grams_b)

    def __sequence_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return SequenceMatcher(None, a, b).ratio()

    def __token_sort_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return fuzz.token_sort_ratio(a, b) / 100

    def __token_set_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return fuzz.token_set_ratio(a, b) / 100

    def __partial_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0

        return fuzz.partial_ratio(a, b) / 100

    def __score_search_match(
        self,
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
            "sequence": self.__sequence_similarity(
                query_normalized,
                candidate_normalized
            ),
            "token_sort": self.__token_sort_similarity(
                query_normalized,
                candidate_normalized
            ),
            "token_set": self.__token_set_similarity(
                query_normalized,
                candidate_normalized
            ),
            "partial": self.__partial_similarity(
                query_normalized,
                candidate_normalized
            ),
            "char_ngram_jaccard": self.__jaccard_similarity(
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

            probability, valid_methods, method_scores = self.__score_search_match(
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