from typing import List
import pdfplumber
import pandas as pd

from data_loader import DataLoader


class Nutrition_INCAP(DataLoader):
    """
    Clase para cargar, procesar y almacenar la Tabla de Composición de Alimentos
    del INCAP.

    Responsabilidades:
    - Leer datos desde caché si existen.
    - Extraer información nutricional desde el PDF oficial del INCAP.
    - Detectar tablas de macronutrientes y vitaminas.
    - Consolidar registros nutricionales por código de alimento.
    - Generar self.data como DataFrame final.
    """

    CACHE_SCHEMA = {
        "data": "./cache/incap_data.pkl",
        "categories": "./cache/incap_categories.pkl",
    }

    categories: dict

    COLS_MACRO: List[str] = [
        "codigo", "nombre", "agua_pct", "energia_kcal",
        "proteina_g", "grasa_total_g", "ag_sat_g", "ag_mono_g", "ag_poli_g",
        "colesterol_mg", "carbohidratos_g", "azucares_g", "ceniza_g",
        "fibra_dietetica_g", "calcio_mg", "hierro_mg", "magnesio_mg",
        "fosforo_mg", "potasio_mg", "sodio_mg", "zinc_mg", "cobre_mg",
        "selenio_mcg", "fraccion_comestible_pct", "_extra",
    ]

    COLS_VITA: List[str] = [
        "_blank", "codigo", "nombre", "energia_kcal",
        "vitamina_c_mg", "tiamina_mg", "riboflavina_mg", "niacina_mg",
        "ac_pantotenico_mg", "vitamina_b6_mg", "ac_folico_mcg",
        "folato_alimentos_mcg", "folato_fde_mcg", "vitamina_b12_mcg",
        "vitamina_a_rae_mcg", "retinol_mcg", "b_carotenos_mcg",
        "vitamina_e_mg", "vitamina_d_mcg", "vitamina_k_mcg",
        "fraccion_comestible_pct",
    ]

    def __init__(self, source_filename: str):
        """
        Inicializa la clase CT_INCAP y carga los datos nutricionales.

        Args:
            source_filename (str): Ruta del PDF de la Tabla de Composición
                de Alimentos del INCAP.
        """
        super().__init__()
        self.categories = {}
        self.load_data(source_filename)

    def load_data(self, source_filename: str) -> pd.DataFrame:
        """
        Carga los datos nutricionales desde caché o desde el PDF fuente.

        Si la caché existe, carga los atributos definidos en CACHE_SCHEMA.
        Si no existe, procesa el PDF, genera self.data y guarda los resultados.

        Args:
            source_filename (str): Ruta del archivo PDF fuente.

        Returns:
            pd.DataFrame: DataFrame consolidado de composición nutricional.
        """
        if self._get_from_cache():
            if self.data is None:
                raise ValueError("Cache loaded but self.data is None.")

            if self.NORMALIZED_NAME_COL not in self.data.columns:
                self.data = self._ensure_normalized_columns(self.data)

            return self.data

        self.categories, self.data = self.__extract_from_pdf(source_filename)

        if self.NORMALIZED_NAME_COL not in self.data.columns:
            self.data = self._ensure_normalized_columns(self.data)

        self._save_to_cache()

        return self.data

    def __get_row_type(self, row, codigo_idx):
        """
        Clasifica el tipo de fila extraída de una tabla del PDF.

        Returns:
            str | bool:
                "category" si la fila corresponde a una categoría.
                "data" si corresponde a un alimento.
                "other" si corresponde a encabezados u otro contenido.
                False si la fila no es válida.
        """
        if not row or len(row) <= codigo_idx:
            return False

        try:
            code = str(row[codigo_idx] or "").strip()
            int(code)
            is_category = len(code) <= 2

            return "category" if is_category else "data"

        except ValueError:
            return "other"

    def __extract_row(self, table, cols, codigo_idx, categories=None):
        """
        Extrae filas de datos desde una tabla del PDF.
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
        Detecta si una tabla corresponde a macronutrientes o vitaminas.
        """
        if not table or len(table) < 3:
            return None

        ncols = len(table[0])

        if ncols == 25:
            return "macro"

        if ncols == 21:
            return "vita"

        return None

    def __extract_from_pdf(
        
        self,
        source_filename: str,
        start_page: int = 26,
        show_logs: bool = True
    ):
        """
        Extrae y consolida la información nutricional desde el PDF del INCAP.

        Args:
            source_filename (str): Ruta del PDF del INCAP.
            start_page (int): Página inicial de procesamiento.
            show_logs (bool): Indica si se muestran mensajes de avance.

        Returns:
            tuple:
                categories (dict): Categorías detectadas.
                data (pd.DataFrame): Tabla nutricional consolidada.
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

                nutrition_tables = [
                    table for table in tables
                    if table and len(table[0]) > 20
                ]

                if len(nutrition_tables) != 1:
                    if len(nutrition_tables) == 0:
                        print(f"Pagina {page} sin tabla de nutricion valida")
                        continue

                    print(f"Pagina Invalida {page}")
                    raise ValueError(f"Pagina Invalida {page}")

                table = nutrition_tables[0]
                tipo = self.__detect_page_type(table)

                if tipo == "macro":
                    for row in self.__extract_row(
                        table,
                        self.COLS_MACRO,
                        codigo_idx=0,
                        categories=categories
                    ):
                        macro_records[row["codigo"]] = row

                elif tipo == "vita":
                    for row in self.__extract_row(
                        table,
                        self.COLS_VITA,
                        codigo_idx=1,
                        categories=categories
                    ):
                        vita_records[row["codigo"]] = row

                if show_logs and (i + 1) % 50 == 0:
                    print(
                        f"Página {i + 1}/{total}  |  "
                        f"macro={len(macro_records)}  "
                        f"vita={len(vita_records)}"
                    )

        if show_logs:
            print(f"\nRegistros macro: {len(macro_records)}")
            print(f"Registros vita:  {len(vita_records)}")
            print(f"Categorias: {categories}")

        codes = set(macro_records) | set(vita_records)
        rows = []

        for cod in sorted(codes, key=lambda x: int(x) if x and x.isdigit() else 0):
            macro_row = macro_records.get(cod, {})
            vita_row = vita_records.get(cod, {})

            name = " ".join(
                (macro_row.get("nombre") or vita_row.get("nombre") or "").split()
            )

            final_row = {
                "codigo": cod,
                "nombre": name,
            }

            for key, value in macro_row.items():
                if key not in ("codigo", "nombre"):
                    final_row[key] = value

            for key, value in vita_row.items():
                if key not in (
                    "codigo",
                    "nombre",
                    "energia_kcal",
                    "fraccion_comestible_pct"
                ):
                    final_row[key] = value

            rows.append(final_row)

        data = pd.DataFrame(rows)

        firsts = [
            "codigo",
            "nombre",
            "energia_kcal",
            "agua_pct",
            "fraccion_comestible_pct",
        ]

        others = [column for column in data.columns if column not in firsts]

        data = data[
            [column for column in firsts if column in data.columns] + others
        ]

        data = self._ensure_normalized_columns(data)

        return categories, data
    

if __name__ == "__main__":
    incap_data = Nutrition_INCAP("./data/raw/tabladecomposiciondealimentos.pdf")

    matches = incap_data.search_word_matches(
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