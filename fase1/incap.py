import re
import pickle 
import pdfplumber
import unicodedata
import pandas as pd
from difflib import SequenceMatcher
from typing import List, Tuple, Dict
from rapidfuzz import fuzz
"""
Módulo de carga y procesamiento de datos del INCAP.

Este script extrae la Tabla de Composición de Alimentos del INCAP desde un archivo PDF,
procesa las tablas de macronutrientes y vitaminas, consolida la información por alimento
y almacena los resultados en archivos serializados para evitar reprocesamientos.

La clase principal es CT_INCAP, que permite cargar los datos desde caché si ya existen,
o extraerlos directamente desde el PDF si no se encuentran disponibles.
"""


class CT_INCAP: 
    """
    Clase para cargar, procesar y almacenar la Tabla de Composición de Alimentos del INCAP.

    La clase permite:
    - Leer datos desde archivos serializados en caché.
    - Extraer información nutricional desde el PDF oficial del INCAP.
    - Detectar páginas con tablas de macronutrientes o vitaminas.
    - Consolidar los registros nutricionales por código de alimento.
    - Generar un DataFrame final con la composición nutricional de cada alimento.

    Atributos principales:
        categories: Diccionario con las categorías de alimentos identificadas en el PDF.
        composition_table_food: DataFrame con la composición nutricional consolidada.
    """

    composition_table_food_df_serialized_filename: str = "./cache/composition_table_food.pkl"
    categories_serialized_filename: str = "./cache/categories.pkl"
    incap_pdf_filename: str
    categories: dict
    composition_table_food: pd.DataFrame

    COLS_MACRO: List = [
        "codigo", "nombre", "agua_pct", "energia_kcal",
        "proteina_g", "grasa_total_g", "ag_sat_g", "ag_mono_g", "ag_poli_g",
        "colesterol_mg", "carbohidratos_g", "azucares_g", "ceniza_g",
        "fibra_dietetica_g", "calcio_mg", "hierro_mg", "magnesio_mg",
        "fosforo_mg", "potasio_mg", "sodio_mg", "zinc_mg", "cobre_mg",
        "selenio_mcg", "fraccion_comestible_pct", "_extra",
    ]
 
    COLS_VITA: List = [
        "_blank", "codigo", "nombre", "energia_kcal",
        "vitamina_c_mg", "tiamina_mg", "riboflavina_mg", "niacina_mg",
        "ac_pantotenico_mg", "vitamina_b6_mg", "ac_folico_mcg",
        "folato_alimentos_mcg", "folato_fde_mcg", "vitamina_b12_mcg",
        "vitamina_a_rae_mcg", "retinol_mcg", "b_carotenos_mcg",
        "vitamina_e_mg", "vitamina_d_mcg", "vitamina_k_mcg",
        "fraccion_comestible_pct",
    ]

    NORMALIZED_NAME_COL: str = "nombre_normalizado"

    def __init__(self, source_filename):
        """
        Inicializa la clase CT_INCAP y carga los datos nutricionales.

        Al crear una instancia de la clase, se intenta cargar primero la información
        desde los archivos serializados en caché. Si estos no existen o no pueden leerse,
        se procesa directamente el archivo PDF indicado.

        Args:
            source_filename (str): Ruta del archivo PDF de la Tabla de Composición
                de Alimentos del INCAP.

        Returns:
            None
        """
        self.load_data(source_filename)


    def load_data(self, source_filename):
        """
        Carga los datos nutricionales desde caché o desde el PDF fuente.

        El método primero intenta recuperar los datos previamente procesados mediante
        archivos serializados. Si la caché está disponible, asigna directamente las
        categorías y la tabla de composición al objeto. Si no existe caché válida,
        extrae la información desde el PDF y luego guarda el resultado en caché.

        Args:
            source_filename (str): Ruta del archivo PDF fuente.

        Returns:
            None
        """
        cache_result = self.__get_from_cache()
        if cache_result is not None: 
            self.categories = cache_result[0]
            self.composition_table_food = cache_result[1]

            if self.NORMALIZED_NAME_COL not in self.composition_table_food.columns:
                self.composition_table_food = self.__ensure_normalized_columns(
                    self.composition_table_food
                )

            return
        self.categories, self.composition_table_food = self.__extract_from_pdf(source_filename)
        
        self.source_filename = source_filename
        self.__save_to_cache()


    def __save_to_cache(self):
        """
        Guarda en caché los datos procesados del INCAP.

        Serializa dos objetos usando pickle:
        - El DataFrame con la tabla de composición nutricional.
        - El diccionario de categorías de alimentos.

        Esto evita tener que reprocesar el PDF en ejecuciones posteriores.

        Args:
            None

        Returns:
            None
        """
        with open(self.composition_table_food_df_serialized_filename, 'wb') as f:
            pickle.dump(self.composition_table_food, f) 

        with open(self.categories_serialized_filename, 'wb') as f:
            pickle.dump(self.categories, f) 


    def __get_from_cache(self) -> Tuple:
        """
        Intenta cargar los datos nutricionales previamente procesados desde caché.

        Busca los archivos serializados correspondientes a:
        - La tabla de composición nutricional.
        - Las categorías de alimentos.

        Si ambos archivos existen y pueden cargarse correctamente, devuelve ambos
        objetos. Si ocurre algún error durante la lectura, devuelve None para indicar
        que debe procesarse nuevamente el PDF.

        Args:
            None

        Returns:
            Tuple | None: Tupla con el diccionario de categorías y el DataFrame de
            composición nutricional. Devuelve None si no se puede cargar la caché.
        """

        try: 
            with open(self.composition_table_food_df_serialized_filename, 'rb') as f:
                composition_table_food = pickle.load(f) 

            with open(self.categories_serialized_filename, 'rb') as f:
                categories = pickle.load(f) 

            print("Loaded data from cache serialized data")
            return categories, composition_table_food

        except:
            print('Couldnt load from caches serialized data')
            return None
        

    def __get_row_type(self, row, codigo_idx):
        """
        Clasifica el tipo de fila extraída de una tabla del PDF.

        La función evalúa el contenido de la columna donde debería estar el código
        del alimento. Según el formato observado en la tabla del INCAP:
        - Si el código es numérico y tiene dos dígitos o menos, se interpreta como categoría.
        - Si el código es numérico y tiene más de dos dígitos, se interpreta como alimento.
        - Si no es numérico, se interpreta como encabezado u otro tipo de fila.

        Args:
            row (list): Fila extraída desde una tabla del PDF.
            codigo_idx (int): Índice de la columna donde se encuentra el código.

        Returns:
            str | bool: 
                "category" si la fila corresponde a una categoría.
                "data" si la fila corresponde a un alimento.
                "other" si la fila corresponde a encabezados u otro contenido.
                False si la fila está vacía o no tiene suficientes columnas.
        """
        if not row or len(row) <= codigo_idx:
            return False

        try:
            code: str = str(row[codigo_idx] or "").strip() 
            int(code)
            is_category = len(code) <= 2

            return "category" if is_category else "data"

        except ValueError:
            return "other"
 

    def __extract_row(self, table, cols, codigo_idx, categories=None):
        """
        Extrae y normaliza las filas de datos de una tabla del PDF.

        Recorre las filas de una tabla extraída con pdfplumber, identifica si cada fila
        corresponde a un alimento o a una categoría, y transforma las filas de alimentos
        en diccionarios con nombres de columnas estandarizados.

        Las columnas internas que empiezan con "_" se omiten, ya que se utilizan solo
        como apoyo para manejar columnas vacías o sobrantes del PDF.

        Args:
            table (list): Tabla extraída desde una página del PDF.
            cols (list): Lista de nombres de columnas esperadas para el tipo de tabla.
            codigo_idx (int): Índice donde se encuentra el código del alimento.
            categories (dict, optional): Diccionario donde se almacenan las categorías
                detectadas. Si es None, no se guardan categorías.

        Returns:
            list: Lista de diccionarios, donde cada diccionario representa un alimento
            con sus valores nutricionales.
        """
        filas = []

        for row in table:
            row_type = self.__get_row_type(row, codigo_idx) 

            if row_type == "data":
                padded = list(row) + [None] * max(0, len(cols) - len(row))
                record = {}

                for col, val in zip(cols, padded):
                    if col.startswith("_"):
                        continue

                    record[col] = str(val).strip() if val else None

                filas.append(record)

            elif row_type == "category": 
                if categories is not None:
                    code = int(row[codigo_idx])
                    categories[code] = row[codigo_idx + 1]
                
        return filas
    

    def __detect_page_type(self, table):
        """
        Detecta si una tabla del PDF corresponde a macronutrientes o vitaminas.

        La detección se realiza con base en el número de columnas de la tabla:
        - 25 columnas: tabla de macronutrientes.
        - 21 columnas: tabla de vitaminas.
        - Cualquier otro número de columnas: tabla no reconocida.

        Args:
            table (list): Tabla extraída desde una página del PDF.

        Returns:
            str | None:
                "macro" si la tabla corresponde a macronutrientes.
                "vita" si la tabla corresponde a vitaminas.
                None si la tabla no cumple con el formato esperado.
        """
        if not table or len(table) < 3:
            return None

        ncols = len(table[0])

        if ncols == 25:
            return "macro"

        if ncols == 21:
            return "vita"

        return None
    

    def __extract_from_pdf(self, source_filename, start_page=26, show_logs=True):
        """
        Extrae y consolida la información nutricional desde el PDF del INCAP.

        Procesa el PDF a partir de una página inicial, identifica las tablas válidas
        de composición nutricional y separa los registros según su tipo:
        - Macronutrientes.
        - Vitaminas y micronutrientes relacionados.

        Después de extraer ambos conjuntos de datos, consolida los registros usando
        el código del alimento como llave. El resultado final es un DataFrame donde
        cada fila representa un alimento y cada columna representa un nutriente o
        atributo nutricional.

        Args:
            source_filename (str): Ruta del archivo PDF del INCAP.
            start_page (int, optional): Página inicial desde donde se empezará a procesar
                el PDF. Por defecto es 26.
            show_logs (bool, optional): Indica si se deben mostrar mensajes de avance
                durante el procesamiento. Por defecto es True.

        Returns:
            tuple:
                categories (dict): Diccionario con las categorías de alimentos detectadas.
                df (pd.DataFrame): DataFrame consolidado con la composición nutricional
                de los alimentos.
        """
        print(f"Abriendo: {source_filename}")

        macro_records = {}
        vita_records = {}
        categories = {}

        with pdfplumber.open(source_filename) as pdf:
            total = len(pdf.pages) 
            print(f"Total páginas: {total} | Procesando desde página {start_page}\n")

            for i in range(start_page - 1, total):
                page = pdf.pages[i]
                tables = page.extract_tables()

                if not tables:
                    print(f"Pagina {page} sin tabla")
                    continue

                nutrition_tables = [_table for _table in tables if len(_table[0]) > 20]  

                if len(nutrition_tables) != 1:
                    if len(nutrition_tables) == 0: 
                        print(f"Pagina {page} sin tabla de nutricion valida")
                        continue
                    else: 
                        print(f"Pagina Invalida {page}")
                        raise ValueError(f"Pagina Invalida {page}")
                
                table = nutrition_tables[0]
                tipo = self.__detect_page_type(table)

                if tipo == "macro":
                    for f in self.__extract_row(
                        table,
                        self.COLS_MACRO,
                        codigo_idx=0,
                        categories=categories
                    ):
                        macro_records[f["codigo"]] = f

                elif tipo == "vita":
                    for f in self.__extract_row(
                        table,
                        self.COLS_VITA,
                        codigo_idx=1,
                        categories=categories
                    ):
                        vita_records[f["codigo"]] = f

                if show_logs and (i + 1) % 50 == 0:
                    print(
                        f"Página {i + 1}/{total}  |  "
                        f"macro={len(macro_records)}  vita={len(vita_records)}"
                    )

        if show_logs: 
            print(f"\nRegistros macro: {len(macro_records)}")
            print(f"Registros vita:  {len(vita_records)}")
            print(f"Categorias: {categories}")

        codes = set(macro_records) | set(vita_records)
        rows = []

        for cod in sorted(codes, key=lambda x: int(x) if x and x.isdigit() else 0):
            m = macro_records.get(cod, {})
            v = vita_records.get(cod, {})

            name = " ".join((m.get("nombre") or v.get("nombre") or "").split())

            fila = {
                "codigo": cod,
                "nombre": name
            }

            for k, val in m.items():
                if k not in ("codigo", "nombre"):
                    fila[k] = val

            for k, val in v.items():
                if k not in (
                    "codigo",
                    "nombre",
                    "energia_kcal",
                    "fraccion_comestible_pct"
                ):
                    fila[k] = val

            rows.append(fila)

        df = pd.DataFrame(rows)

        firsts = [
            "codigo",
            "nombre",
            "energia_kcal",
            "agua_pct",
            "fraccion_comestible_pct"
        ]

        others = [c for c in df.columns if c not in firsts]

        df = df[[c for c in firsts if c in df.columns] + others]
        df = df[self.NORMALIZED_NAME_COL] = (
            df["nombre"]
            .fillna("")
            .apply(self.__normalize_text)
        )

        return categories, df
        

    def __normalize_text(self, text: str) -> str:
        """
        Normaliza un texto para facilitar la comparación entre nombres de alimentos.

        El proceso aplicado incluye:
        - Conversión a minúsculas.
        - Eliminación de tildes.
        - Eliminación de signos de puntuación.
        - Normalización de espacios múltiples.
        - Eliminación de palabras vacías frecuentes en descripciones alimentarias.

        Args:
            text (str): Texto original a normalizar.

        Returns:
            str: Texto normalizado.
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


    def __ensure_normalized_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Asegura que el DataFrame tenga columnas auxiliares para búsqueda aproximada.

        Actualmente agrega la columna nombre_normalizado, calculada a partir de la
        columna nombre. Esta columna permite evitar reprocesar los nombres en cada
        búsqueda y queda persistida cuando el DataFrame se guarda en caché.

        Args:
            df (pd.DataFrame): DataFrame de composición nutricional.

        Returns:
            pd.DataFrame: DataFrame con columnas normalizadas agregadas.
        """
        if "nombre" not in df.columns:
            raise ValueError("El DataFrame debe contener una columna llamada 'nombre'.")

        df = df.copy()

        df[self.NORMALIZED_NAME_COL] = (
            df["nombre"]
            .fillna("")
            .apply(self.__normalize_text)
        )

        return df


    def __char_ngrams(self, text: str, n: int = 3) -> set:
        """
        Genera n-gramas de caracteres para medir similitud textual aproximada.

        Args:
            text (str): Texto normalizado.
            n (int): Tamaño del n-grama. Por defecto es 3.

        Returns:
            set: Conjunto de n-gramas generados.
        """
        text = f" {text} "

        if len(text) < n:
            return {text.strip()} if text.strip() else set()

        return {
            text[i:i + n]
            for i in range(len(text) - n + 1)
        }


    def __jaccard_similarity(self, a: str, b: str, ngram_size: int = 3) -> float:
        """
        Calcula similitud Jaccard usando n-gramas de caracteres.

        Args:
            a (str): Primer texto normalizado.
            b (str): Segundo texto normalizado.
            ngram_size (int): Tamaño de los n-gramas de caracteres. Valores menores
                aumentan la sensibilidad a coincidencias parciales, mientras que
                valores mayores hacen la comparación más estricta.

        Returns:
            float: Similitud entre 0 y 1.
        """
        grams_a = self.__char_ngrams(a, n=ngram_size)
        grams_b = self.__char_ngrams(b, n=ngram_size)

        if not grams_a or not grams_b:
            return 0.0

        return len(grams_a & grams_b) / len(grams_a | grams_b)

    def __sequence_similarity(self, a: str, b: str) -> float:
        """
        Calcula similitud secuencial entre dos cadenas.

        Se usa como alternativa liviana a Levenshtein cuando no se requiere una
        dependencia externa. El resultado está entre 0 y 1.

        Args:
            a (str): Primer texto normalizado.
            b (str): Segundo texto normalizado.

        Returns:
            float: Similitud entre 0 y 1.
        """
        if not a or not b:
            return 0.0

        return SequenceMatcher(None, a, b).ratio()


    def __token_sort_similarity(self, a: str, b: str) -> float:
        """
        Calcula similitud entre textos ignorando parcialmente el orden de palabras.

        Args:
            a (str): Primer texto normalizado.
            b (str): Segundo texto normalizado.

        Returns:
            float: Similitud entre 0 y 1.
        """
        if not a or not b:
            return 0.0

        if fuzz is not None:
            return fuzz.token_sort_ratio(a, b) / 100

        sorted_a = " ".join(sorted(a.split()))
        sorted_b = " ".join(sorted(b.split()))

        return self.__sequence_similarity(sorted_a, sorted_b)


    def __token_set_similarity(self, a: str, b: str) -> float:
        """
        Calcula similitud entre conjuntos de palabras.

        Es útil cuando un nombre contiene palabras adicionales respecto al otro,
        por ejemplo: 'arroz blanco' contra 'arroz blanco corriente'.

        Args:
            a (str): Primer texto normalizado.
            b (str): Segundo texto normalizado.

        Returns:
            float: Similitud entre 0 y 1.
        """
        if not a or not b:
            return 0.0

        if fuzz is not None:
            return fuzz.token_set_ratio(a, b) / 100

        tokens_a = set(a.split())
        tokens_b = set(b.split())

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b

        return len(intersection) / len(union)


    def __partial_similarity(self, a: str, b: str) -> float:
        """
        Calcula similitud parcial entre dos cadenas.

        Esta métrica ayuda cuando una cadena está contenida dentro de otra o cuando
        una descripción es mucho más larga que la otra.

        Args:
            a (str): Primer texto normalizado.
            b (str): Segundo texto normalizado.

        Returns:
            float: Similitud entre 0 y 1.
        """
        if not a or not b:
            return 0.0

        if fuzz is not None:
            return fuzz.partial_ratio(a, b) / 100

        shorter, longer = sorted([a, b], key=len)

        if shorter in longer:
            return 1.0

        return self.__sequence_similarity(shorter, longer)


    def __score_food_match(
        self,
        query_normalized: str,
        candidate_normalized: str,
        method_threshold: float = 0.75,
        ngram_size: int = 3

    ) -> Tuple[float, List[str], Dict[str, float]]:
        """
        Calcula la probabilidad de coincidencia entre un texto buscado y un alimento.

        La probabilidad se calcula como el promedio de varias métricas normalizadas
        entre 0 y 1. Todas las métricas tienen el mismo peso para evitar que una sola
        domine el resultado. Además de la probabilidad agregada, la función devuelve
        qué métodos superaron el umbral definido y, por tanto, respaldan la posible
        coincidencia.

        Métodos utilizados:
            - exact:
                Verifica si el texto buscado y el nombre candidato son exactamente
                iguales después de la normalización. Es el criterio más estricto.

            - contains:
                Verifica si uno de los textos está contenido dentro del otro. Es útil
                cuando el usuario busca un término corto y el alimento tiene una
                descripción más larga, por ejemplo: 'arroz' contra 'arroz blanco crudo'.

            - sequence:
                Calcula la similitud secuencial entre ambas cadenas usando comparación
                de caracteres. Ayuda a detectar textos parecidos con pequeñas diferencias
                ortográficas.

            - token_sort:
                Compara los textos después de ordenar alfabéticamente sus palabras.
                Es útil cuando ambos nombres tienen palabras similares, pero en distinto
                orden, por ejemplo: 'leche entera polvo' contra 'polvo leche entera'.

            - token_set:
                Compara los conjuntos de palabras de ambos textos. Tolera palabras
                adicionales en uno de los nombres, por ejemplo: 'frijol negro' contra
                'frijol negro seco'.

            - partial:
                Calcula una similitud parcial entre cadenas. Es útil cuando una cadena
                representa solo una parte relevante de la otra.

            - char_ngram_jaccard:
                Divide los textos en fragmentos cortos de caracteres y calcula el
                traslape entre ellos mediante similitud Jaccard. Ayuda a capturar
                variaciones menores, errores de escritura, plurales o diferencias
                morfológicas.

        Args:
            query_normalized (str): Texto de búsqueda ya normalizado.
            candidate_normalized (str): Nombre del alimento ya normalizado.
            method_threshold (float): Umbral mínimo para considerar que un método
                encontró una posible coincidencia.

        Returns:
            Tuple[float, List[str], Dict[str, float]]:
                - Probabilidad agregada entre 0 y 1.
                - Lista de métodos que consideran posible la coincidencia.
                - Diccionario con el detalle de puntajes por método.
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
            "sequence": self.__sequence_similarity(query_normalized, candidate_normalized),
            "token_sort": self.__token_sort_similarity(query_normalized, candidate_normalized),
            "token_set": self.__token_set_similarity(query_normalized, candidate_normalized),
            "partial": self.__partial_similarity(query_normalized, candidate_normalized),
            "char_ngram_jaccard": self.__jaccard_similarity(query_normalized, candidate_normalized, ngram_size),
        }

        probability = sum(scores.values()) / len(scores)

        valid_methods = [
            method
            for method, score in scores.items()
            if score >= method_threshold
        ]

        return probability, valid_methods, scores


    def search_food_matches(
        self,
        palabra: str,
        top_n: int = 10,
        min_probability: float = 0.55,
        method_threshold: float = 0.75,
        ngram_size: int = 3

    ) -> List[Tuple[pd.Series, float, List[str], Dict[str, float]]]:
        """
        Busca alimentos similares a una palabra o frase dentro de la tabla INCAP.

        La función compara la palabra recibida contra la columna nombre_normalizado.
        Retorna una lista ordenada de posibles coincidencias. Cada resultado contiene:
        - La fila completa del alimento como pd.Series.
        - Una probabilidad agregada entre 0 y 1.
        - La lista de métodos que detectaron una posible coincidencia.
        - Un diccionario con el score obtenido por cada método.

        Args:
            palabra (str): Texto de búsqueda ingresado por el usuario.
            top_n (int): Cantidad máxima de resultados a retornar.
            min_probability (float): Probabilidad mínima para incluir un resultado.
            method_threshold (float): Umbral usado para registrar qué métodos encontraron
                una coincidencia posible.

        Returns:
            List[Tuple[pd.Series, float, List[str], Dict[str, float]]]:
                Lista de tuplas con los resultados. Cada tupla contiene:
                    - pd.Series: fila completa del alimento candidato.
                    - float: probabilidad agregada de coincidencia entre 0 y 1.
                    - List[str]: métodos que superaron el umbral de coincidencia.
                    - Dict[str, float]: score individual obtenido por cada método.
        """
        if self.composition_table_food is None or self.composition_table_food.empty:
            return []

        if self.NORMALIZED_NAME_COL not in self.composition_table_food.columns:
            self.composition_table_food = self.__ensure_normalized_columns(
                self.composition_table_food
            )
        if ngram_size < 2:
            raise ValueError("ngram_size debe ser mayor o igual a 2.")

        if ngram_size > 5:
            raise ValueError("ngram_size no debería ser mayor a 5 para nombres de alimentos.")
        query_normalized = self.__normalize_text(palabra)

        if not query_normalized:
            return []

        results = []

        for _, row in self.composition_table_food.iterrows():
            candidate_normalized = row.get(self.NORMALIZED_NAME_COL, "")

            probability, valid_methods, method_scores = self.__score_food_match(
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


if __name__ == '__main__':
    """
    Punto de entrada del script.

    Ejecuta la carga de datos del INCAP utilizando el archivo PDF ubicado en
    ./data/raw/tabladecomposiciondealimentos.pdf. Al instanciar CT_INCAP,
    se cargan los datos desde caché o se extraen directamente del PDF.
    """
    incapdata = CT_INCAP("./data/raw/tabladecomposiciondealimentos.pdf")
    matches = incapdata.search_food_matches(
        palabra="frijol negro",
        top_n=5,
        min_probability=0.55,
        method_threshold=0.75
    )
    for row, probability, methods, scores in matches:
        print(row["codigo"], row["nombre"])
        print("Probabilidad:", probability)
        print("Métodos válidos:", methods)
        print("Scores:", scores)
        print()