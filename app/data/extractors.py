import pandas as pd
from typing import Dict, AnyStr
from pathlib import Path

def cargar_referencia_peso_longitud_0_5(sex, range) -> dict:
    """
    Carga una tabla OMS de peso para longitud/talla.

    Retorna un diccionario indexado por longitud/talla en centímetros.

    Es compatible con:
    - Weight-for-length 0 a 2 años
    - Weight-for-height 2 a 5 años
    """

    files: Dict[AnyStr, Dict] = {
        'boys':{
            '0-2': 'wfl_boys_0-to-2-years_zscores.xlsx',
            '2-5': 'wfh_boys_2-to-5-years_zscores.xlsx'
        },
        'girls':{
            '0-2': 'wfl_girls_0-to-2-years_zscores.xlsx',
            '2-5': 'wfh_girls_2-to-5-years_zscores.xlsx'
        },
    }

    if sex not in files.keys():
        raise KeyError("Key first value must be eithter 'boys' or 'girls'")

    if range not in files[sex].keys():
        raise KeyError(f"For key '{sex}' possible subkeys are: {','.join(list(files[sex].keys()))}")

    directorio_actual = Path(__file__).resolve().parent

    ruta_archivo = directorio_actual / files[sex][range]
    df = pd.read_excel(ruta_archivo)

    if "Length" in df.columns:
        columna_longitud = "Length"
    elif "Height" in df.columns:
        columna_longitud = "Height"
    else:
        raise ValueError(
            "La tabla no contiene una columna 'Length' o 'Height'"
        )

    referencia = {}

    for _, row in df.iterrows():
        longitud = float(row[columna_longitud])

        referencia[longitud] = {
            "L": float(row["L"]),
            "M": float(row["M"]),
            "S": float(row["S"]),

            "sd_3_neg": float(row["SD3neg"]),
            "sd_2_neg": float(row["SD2neg"]),
            "sd_1_neg": float(row["SD1neg"]),

            "sd_0": float(row["SD0"]),

            "sd_1": float(row["SD1"]),
            "sd_2": float(row["SD2"]),
            "sd_3": float(row["SD3"]),
        }

    return referencia


def cargar_referencia_imc_edad_5_19(sexo: str) -> dict:
    """
    Carga la referencia OMS 2007 de IMC para la edad
    para niños y adolescentes de 5 a 19 años.

    Retorna un diccionario indexado por edad en meses.
    """

    archivos = {
        "boys": "bmi-boys-z-who-2007-exp.xlsx",
        "girls": "bmi-girls-z-who-2007-exp.xlsx",
    }

    if sexo not in archivos:
        raise KeyError(
            "El sexo debe ser 'boys' o 'girls'"
        )

    directorio_actual = Path(__file__).resolve().parent
    ruta = directorio_actual / archivos[sexo]

    df = pd.read_excel(ruta)

    columnas_requeridas = {
        "Month",
        "L",
        "M",
        "S",
        "SD4neg",
        "SD3neg",
        "SD2neg",
        "SD1neg",
        "SD0",
        "SD1",
        "SD2",
        "SD3",
        "SD4",
    }

    faltantes = columnas_requeridas - set(df.columns)

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas: {faltantes}"
        )

    referencia = {}

    for _, fila in df.iterrows():
        mes = int(fila["Month"])

        referencia[mes] = {
            "L": float(fila["L"]),
            "M": float(fila["M"]),
            "S": float(fila["S"]),

            "sd_4_neg": float(fila["SD4neg"]),
            "sd_3_neg": float(fila["SD3neg"]),
            "sd_2_neg": float(fila["SD2neg"]),
            "sd_1_neg": float(fila["SD1neg"]),

            "sd_0": float(fila["SD0"]),

            "sd_1": float(fila["SD1"]),
            "sd_2": float(fila["SD2"]),
            "sd_3": float(fila["SD3"]),
            "sd_4": float(fila["SD4"]),
        }

    return referencia