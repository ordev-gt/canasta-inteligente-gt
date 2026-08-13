from ..entities.Person import Persona
from ..data.extractors import cargar_referencia_peso_longitud_0_5, cargar_referencia_imc_edad_5_19

DATA_DIR = "../data"


"""
Evaluación del peso corporal
----------------------------

Las Recomendaciones Dietéticas Diarias del INCAP están formuladas para personas sanas y utilizan pesos corporales de referencia compatibles con un estado nutricional adecuado. Por este motivo, antes de calcular los requerimientos 
nutricionales individuales, el sistema evalúa si el peso corporal ingresado constituye una referencia apropiada para dichos cálculos.

El propósito de esta evaluación no es realizar un diagnóstico nutricional ni establecer un tratamiento para pérdida o ganancia de peso. El sistema está dirigido principalmente a población sana y busca estimar requerimientos
nutricionales de referencia para la planificación de la alimentación.

En adultos no embarazados se utiliza el índice de masa corporal (IMC) como indicador antropométrico preliminar. Cuando el peso de la persona se encuentra dentro del intervalo considerado saludable, se conserva el peso corporal
actual como referencia individual. Cuando se encuentra fuera de dicho intervalo, el peso actual puede no ser adecuado para estimar requerimientos destinados a representar una condición nutricional saludable. En esos casos
se determina un peso de referencia de acuerdo con los criterios establecidos para el grupo correspondiente.

Adultos
-----
El INCAP utiliza, para la construcción de las recomendaciones energéticas de adultos, un peso correspondiente a un IMC de 22. (Pagina 26)

No Adultos
-------
En menores de 18 años, la evaluación no puede realizarse utilizando los puntos de corte de IMC de adultos, debido a que el peso y la composición corporal esperados dependen de la edad y el sexo. 
Para estos grupos deben utilizarse referencias antropométricas específicas para la edad.


Niños de 0 a 2 años --- :

Para menores de cinco años se utilizará el indicador peso para longitud/talla de los estándares de crecimiento de la OMS. Se considerará que el peso no presenta emaciación ni sobrepeso cuando el puntaje Z se encuentre entre -2 y +2 desviaciones estándar respecto de la mediana de referencia. Valores inferiores a -2 DE indican emaciación y superiores a +2 DE indican sobrepeso, de acuerdo con los puntos de corte de la OMS.


Mujeres Embarazadas
----------------
Las mujeres embarazadas también requieren tratamiento separado, ya que el peso corporal durante la gestación incluye los cambios fisiológicos propios del embarazo y no debe interpretarse mediante los mismos criterios utilizados
para un adulto no embarazado.

El IMC se utiliza únicamente como herramienta de clasificación dentro del modelo. No constituye por sí solo una evaluación completa del estado nutricional, ya que no permite distinguir la composición corporal ni sustituye una 
valoración realizada por un profesional de la salud.

La función retorna tanto el peso corporal observado como el peso seleccionado para los cálculos posteriores, indicando explícitamente si se utilizó el peso real o un peso de referencia.
"""

def obtener_referencia_por_longitud(altura_m: float, referencia: dict) -> dict:
    """
    Busca en la tabla OMS la longitud/talla más cercana
    en incrementos de 0.5 cm.
    """

    altura_cm = altura_m * 100

    altura_referencia_cm = round(altura_cm * 2) / 2

    if altura_referencia_cm not in referencia:
        minimo = min(referencia.keys())
        maximo = max(referencia.keys())
        raise ValueError(f"La longitud/talla {altura_cm:.1f} cm está fuera del rango de la referencia OMS ({minimo}-{maximo} cm).")

    return {
        "altura_real_cm": altura_cm,
        "altura_referencia_cm": altura_referencia_cm,
        **referencia[altura_referencia_cm],
    }

def evaluacion_peso_adulto(p: Persona) -> dict:
    IMC_ADULTO_MIN = 18.5
    IMC_ADULTO_MAX = 24.9
    IMC_REFERENCIA_INCAP = 22.0
    IMC_OBESIDAD_MIN = 30.0

    imc = p.peso / (p.altura ** 2)

    peso_de_referencia = IMC_REFERENCIA_INCAP * (p.altura ** 2)

    if IMC_ADULTO_MIN <= imc <= IMC_ADULTO_MAX:
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"

        estado_peso = "normal"
        requiere_intervencion_profesional = False

    elif imc > IMC_ADULTO_MAX:
        peso_para_calculos = peso_de_referencia
        usa_peso_real = False
        fuente_de_peso = "imc_incap_22_de_referencia"

        if imc < IMC_OBESIDAD_MIN:
            estado_peso = "sobrepeso"
            requiere_intervencion_profesional = True
        else:
            estado_peso = "obesidad"
            requiere_intervencion_profesional = True


    else:
        # No asumir que una persona con bajo peso debe ser llevada a IMC 22. Posiblemente requiera intervención de recuperación nutricional.
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"
        estado_peso = "bajo_de_peso"
        requiere_intervencion_profesional = True

    return {
        "peso_real": p.peso,
        "peso_para_calculos": peso_para_calculos,
        "usa_peso_real": usa_peso_real,
        "peso_de_referencia": peso_de_referencia,
        "fuente_de_peso": fuente_de_peso,
        "imc_de_referencia": IMC_REFERENCIA_INCAP,
        "indicador": "imc",
        "valor_de_indicador": imc,
        "estado_de_indicador": estado_peso,
        "requiere_intervencion_profesional": requiere_intervencion_profesional,
    }

PESO_LONGITUD_NINAS_0_2 = cargar_referencia_peso_longitud_0_5( 'girls', '0-2')
PESO_ALTURA_NINOS_2_5 = cargar_referencia_peso_longitud_0_5('boys', '2-5')
PESO_LONGITUD_NINOS_0_2 = cargar_referencia_peso_longitud_0_5('boys', '0-2')
PESO_ALTURA_NINAS_2_5 = cargar_referencia_peso_longitud_0_5( 'girls', '2-5')

def evaluacion_peso_menor_5_con_referencia(p: Persona, referencia: dict, indicador: str) -> dict:

    datos = obtener_referencia_por_longitud(p.altura,referencia)

    peso_de_referencia = datos["M"]

    limite_menos_3 = datos["sd_3_neg"]
    limite_menos_2 = datos["sd_2_neg"]
    limite_mas_2 = datos["sd_2"]
    limite_mas_3 = datos["sd_3"]

    if p.peso < limite_menos_3: # Emaciación grave
        estado_peso = "emaciacion_grave"
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"
        requiere_intervencion_profesional = True

    elif p.peso < limite_menos_2: # Emaciación
        estado_peso = "emaciacion"
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"
        requiere_intervencion_profesional = True

    elif p.peso <= limite_mas_2: # Entre -2 y +2 DE
        estado_peso = "rango_de_referencia"
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"
        requiere_intervencion_profesional = False

    elif p.peso <= limite_mas_3: # Entre +2 y +3 DE
        estado_peso = "sobrepeso"
        peso_para_calculos = peso_de_referencia
        usa_peso_real = False
        fuente_de_peso = "mediana_oms_peso_longitud"
        requiere_intervencion_profesional = True

    else: # > +3 DE
        estado_peso = "obesidad"
        peso_para_calculos = peso_de_referencia
        usa_peso_real = False
        fuente_de_peso = "mediana_oms_peso_longitud"
        requiere_intervencion_profesional = True

    return {
        "peso_real": p.peso,
        "peso_para_calculos": peso_para_calculos,
        "usa_peso_real": usa_peso_real,
        "peso_de_referencia": peso_de_referencia,
        "fuente_de_peso": fuente_de_peso,
        "indicador": indicador,
        "valor_de_indicador": None,
        "estado_de_indicador": estado_peso,
        "altura_real_cm": datos["altura_real_cm"],
        "altura_referencia_cm": datos["altura_referencia_cm"],
        "limites_oms": {
            "menos_3_sd": limite_menos_3,
            "menos_2_sd": limite_menos_2,
            "mediana": peso_de_referencia,
            "mas_2_sd": limite_mas_2,
            "mas_3_sd": limite_mas_3,
        },
        "requiere_intervencion_profesional":
            requiere_intervencion_profesional,
    }

def evaluacion_peso_nino_0_a_2_anos(p: Persona) -> dict: return evaluacion_peso_menor_5_con_referencia(p, PESO_LONGITUD_NINOS_0_2, "peso_para_longitud_oms")

def evaluacion_peso_nina_0_a_2_anos(p: Persona) -> dict: return evaluacion_peso_menor_5_con_referencia(p, PESO_LONGITUD_NINAS_0_2, "peso_para_longitud_oms")

def evaluacion_peso_nino_2_a_5_anos(p: Persona) -> dict: return evaluacion_peso_menor_5_con_referencia(p,  PESO_ALTURA_NINOS_2_5,  "peso_para_talla_oms")

def evaluacion_peso_nina_2_a_5_anos(p: Persona) -> dict: return evaluacion_peso_menor_5_con_referencia(p, PESO_ALTURA_NINAS_2_5, "peso_para_talla_oms")

def evaluacion_peso_nino_menor_5(p: Persona) -> dict:

    if p.edad_meses > 60:
        raise ValueError("Esta función solo aplica hasta 60 meses.")

    if p.edad_meses <= 24:
        if p.sexo == "men":
            return evaluacion_peso_nino_0_a_2_anos(p)

        if p.sexo == "women":
            return evaluacion_peso_nina_0_a_2_anos(p)

    else:
        if p.sexo == "men":
            return evaluacion_peso_nino_2_a_5_anos(p)

        if p.sexo == "women":
            return evaluacion_peso_nina_2_a_5_anos(p)

IMC_EDAD_MESES_NINAS = cargar_referencia_imc_edad_5_19('girls')
IMC_EDAD_MESES_NINOS = cargar_referencia_imc_edad_5_19('boys')

def evaluacion_peso_nino_adolescente(p: Persona) -> dict:
    """
    Evalúa el peso de niños y adolescentes utilizando
    IMC para la edad según la referencia OMS 2007.

    Aplica aproximadamente de 5 a 18 años.
    """

    if p.sexo == "men":
        referencia = IMC_EDAD_MESES_NINOS
    elif p.sexo == "women":
        referencia = IMC_EDAD_MESES_NINAS
    else:
        raise ValueError(f"Sexo no reconocido: {p.sexo}")

    if p.edad_meses not in referencia:
        minimo = min(referencia.keys())
        maximo = max(referencia.keys())

        raise ValueError(f"La edad de {p.edad_meses} meses está fuera del rango de referencia OMS ({minimo}-{maximo} meses).")

    datos = referencia[p.edad_meses]

    imc = p.peso / (p.altura ** 2)

    imc_de_referencia = datos["M"]

    peso_de_referencia = (
        imc_de_referencia
        * (p.altura ** 2)
    )

    limite_menos_3 = datos["sd_3_neg"]
    limite_menos_2 = datos["sd_2_neg"]
    limite_mas_1 = datos["sd_1"]
    limite_mas_2 = datos["sd_2"]

    # Delgadez severa
    if imc < limite_menos_3:
        estado_peso = "delgadez_severa"
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"
        requiere_intervencion_profesional = True

    # Delgadez
    elif imc < limite_menos_2:
        estado_peso = "delgadez"
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"
        requiere_intervencion_profesional = True

    # Entre -2 SD y +1 SD
    elif imc <= limite_mas_1:
        estado_peso = "rango_de_referencia"
        peso_para_calculos = p.peso
        usa_peso_real = True
        fuente_de_peso = "peso_real"
        requiere_intervencion_profesional = False

    # Entre +1 SD y +2 SD
    elif imc <= limite_mas_2:
        estado_peso = "sobrepeso"

        peso_para_calculos = peso_de_referencia
        usa_peso_real = False
        fuente_de_peso = "mediana_oms_imc_para_edad"
        requiere_intervencion_profesional = True

    # Mayor a +2 SD
    else:
        estado_peso = "obesidad"

        peso_para_calculos = peso_de_referencia
        usa_peso_real = False
        fuente_de_peso = "mediana_oms_imc_para_edad"
        requiere_intervencion_profesional = True

    return {
        "peso_real": p.peso,
        "peso_para_calculos": peso_para_calculos,
        "usa_peso_real": usa_peso_real,
        "peso_de_referencia": peso_de_referencia,
        "fuente_de_peso": fuente_de_peso,
        "imc_de_referencia": imc_de_referencia,
        "indicador": "imc_para_edad_oms",
        "valor_de_indicador": imc,
        "estado_de_indicador": estado_peso,
        "edad_meses": p.edad_meses,
        "limites_oms": {
            "menos_3_sd": limite_menos_3,
            "menos_2_sd": limite_menos_2,
            "mediana": imc_de_referencia,
            "mas_1_sd": limite_mas_1,
            "mas_2_sd": limite_mas_2,
        },

        "requiere_intervencion_profesional":
            requiere_intervencion_profesional,
    }

def evaluacion_peso_embarazo(p: Persona) -> dict:
    IMC_ADULTO_MIN = 18.5
    IMC_ADULTO_MAX = 24.9
    IMC_OBESIDAD_MIN = 30.0

    if p.peso_preembarazo is None:
        raise ValueError("Se requiere el peso previo al embarazo para realizar la evaluación antropométrica.")

    if p.peso_preembarazo <= 0:
        raise ValueError("El peso previo al embarazo debe ser mayor que cero.")

    imc_preembarazo = (
        p.peso_preembarazo /
        (p.altura ** 2)
    )

    if IMC_ADULTO_MIN <= imc_preembarazo <= IMC_ADULTO_MAX:
        estado_peso = "normal"
        requiere_intervencion_profesional = False

    elif imc_preembarazo > IMC_ADULTO_MAX:
        if imc_preembarazo < IMC_OBESIDAD_MIN:
            estado_peso = "sobrepeso"
        else:
            estado_peso = "obesidad"

        requiere_intervencion_profesional = True

    else:
        estado_peso = "bajo_de_peso"
        requiere_intervencion_profesional = True

    return {
        "peso_real": p.peso,
        "peso_preembarazo": p.peso_preembarazo,

        # Se utiliza como peso basal para los cálculos.
        # Los requerimientos propios del embarazo se agregan después.
        "peso_para_calculos": p.peso_preembarazo,
        "usa_peso_real": False,

        # No es un peso de referencia teórico,
        # sino un peso observado antes del embarazo.
        "peso_de_referencia": None,
        "fuente_de_peso": "peso_preembarazo",

        "imc_de_referencia": None,

        "indicador": "imc_preembarazo",
        "valor_de_indicador": imc_preembarazo,
        "estado_de_indicador": estado_peso,

        "requiere_intervencion_profesional":
            requiere_intervencion_profesional,
    }

def evaluacion_peso(p: Persona) -> dict:

    if p.esta_embarazada:
        return evaluacion_peso_embarazo(p)

    if p.edad_meses <= 60: # Hasta 5 años
        return evaluacion_peso_nino_menor_5(p)

    if p.edad_meses <= 228: # Hasta 19 años
        return evaluacion_peso_nino_adolescente(p)

    return evaluacion_peso_adulto(p)

TMB = {
    "men": {
        3: lambda weight: 59.512 * weight - 30.4,
        10: lambda weight: 22.706 * weight + 504.3,
        18: lambda weight: 17.686 * weight + 658.2,
        30: lambda weight: 15.057 * weight + 692.2,
        60: lambda weight: 11.472 * weight + 873.1,
        float("inf"): lambda weight: 11.711 * weight + 587.7,
    },

    "women": {
        3: lambda weight: 58.317 * weight - 31.1,
        10: lambda weight: 20.315 * weight + 485.9,
        18: lambda weight: 13.384 * weight + 692.6,
        30: lambda weight: 14.818 * weight + 486.6,
        60: lambda weight: 8.126 * weight + 845.6,
        float("inf"): lambda weight: 9.082 * weight + 658.5,
    },
}


PROTEIN_REQUIREMENTS = {
    "all": {
        0.25: {
            "avg_weight_kg": 4.85,
            "rpe_g_per_kg": 1.32,
            "rdd_reference_g_per_kg": 1.64,
            "rdd_mixed_diet_g_per_kg": None,
        },
        0.5: {
            "avg_weight_kg": 6.67,
            "rpe_g_per_kg": 1.06,
            "rdd_reference_g_per_kg": 1.25,
            "rdd_mixed_diet_g_per_kg": None,
        },
        0.75: {
            "avg_weight_kg": 7.93,
            "rpe_g_per_kg": 1.12,
            "rdd_reference_g_per_kg": 1.31,
            "rdd_mixed_diet_g_per_kg": 1.76,
        },
        1: {
            "avg_weight_kg": 8.82,
            "rpe_g_per_kg": 1.12,
            "rdd_reference_g_per_kg": 1.31,
            "rdd_mixed_diet_g_per_kg": 1.76,
        },
        2: {
            "avg_weight_kg": 10.55,
            "rpe_g_per_kg": 0.95,
            "rdd_reference_g_per_kg": 1.14,
            "rdd_mixed_diet_g_per_kg": 1.54,
        },
        3: {
            "avg_weight_kg": 13.0,
            "rpe_g_per_kg": 0.79,
            "rdd_reference_g_per_kg": 0.97,
            "rdd_mixed_diet_g_per_kg": 1.31,
        },
        4: {
            "avg_weight_kg": 15.15,
            "rpe_g_per_kg": 0.73,
            "rdd_reference_g_per_kg": 0.90,
            "rdd_mixed_diet_g_per_kg": 1.21,
        },
        5: {
            "avg_weight_kg": 17.5,
            "rpe_g_per_kg": 0.69,
            "rdd_reference_g_per_kg": 0.86,
            "rdd_mixed_diet_g_per_kg": 1.16,
        },
    },

    "men": {
        6: {
            "avg_weight_kg": 18.26,
            "rpe_g_per_kg": 0.69,
            "rdd_reference_g_per_kg": 0.85,
            "rdd_mixed_diet_g_per_kg": 1.14,
        },
        7: {
            "avg_weight_kg": 20.36,
            "rpe_g_per_kg": 0.72,
            "rdd_reference_g_per_kg": 0.89,
            "rdd_mixed_diet_g_per_kg": 1.20,
        },
        8: {
            "avg_weight_kg": 22.58,
            "rpe_g_per_kg": 0.74,
            "rdd_reference_g_per_kg": 0.91,
            "rdd_mixed_diet_g_per_kg": 1.23,
        },
        9: {
            "avg_weight_kg": 25.01,
            "rpe_g_per_kg": 0.75,
            "rdd_reference_g_per_kg": 0.92,
            "rdd_mixed_diet_g_per_kg": 1.24,
        },
        10: {
            "avg_weight_kg": 27.57,
            "rpe_g_per_kg": 0.75,
            "rdd_reference_g_per_kg": 0.92,
            "rdd_mixed_diet_g_per_kg": 1.24,
        },
        12: {
            "avg_weight_kg": 32,
            "rpe_g_per_kg": 0.75,
            "rdd_reference_g_per_kg": 0.91,
            "rdd_mixed_diet_g_per_kg": 1.23,
        },
        14: {
            "avg_weight_kg": 41,
            "rpe_g_per_kg": 0.74,
            "rdd_reference_g_per_kg": 0.90,
            "rdd_mixed_diet_g_per_kg": 1.21,
        },
        16: {
            "avg_weight_kg": 53,
            "rpe_g_per_kg": 0.72,
            "rdd_reference_g_per_kg": 0.89,
            "rdd_mixed_diet_g_per_kg": 1.19,
        },
        18: {
            "avg_weight_kg": 61,
            "rpe_g_per_kg": 0.71,
            "rdd_reference_g_per_kg": 0.87,
            "rdd_mixed_diet_g_per_kg": 1.16,
        },
        float("inf"): {
            "avg_weight_kg": 64,
            "rpe_g_per_kg": 0.66,
            "rdd_reference_g_per_kg": 0.83,
            "rdd_mixed_diet_g_per_kg": 1.12,
        },
    },

    "women": {
        6: {
            "avg_weight_kg": 17.69,
            "rpe_g_per_kg": 0.69,
            "rdd_reference_g_per_kg": 0.85,
            "rdd_mixed_diet_g_per_kg": 1.14,
        },
        7: {
            "avg_weight_kg": 19.67,
            "rpe_g_per_kg": 0.72,
            "rdd_reference_g_per_kg": 0.89,
            "rdd_mixed_diet_g_per_kg": 1.20,
        },
        8: {
            "avg_weight_kg": 21.87,
            "rpe_g_per_kg": 0.74,
            "rdd_reference_g_per_kg": 0.91,
            "rdd_mixed_diet_g_per_kg": 1.23,
        },
        9: {
            "avg_weight_kg": 24.57,
            "rpe_g_per_kg": 0.75,
            "rdd_reference_g_per_kg": 0.92,
            "rdd_mixed_diet_g_per_kg": 1.24,
        },
        10: {
            "avg_weight_kg": 27.56,
            "rpe_g_per_kg": 0.75,
            "rdd_reference_g_per_kg": 0.92,
            "rdd_mixed_diet_g_per_kg": 1.24,
        },
        12: {
            "avg_weight_kg": 33,
            "rpe_g_per_kg": 0.74,
            "rdd_reference_g_per_kg": 0.91,
            "rdd_mixed_diet_g_per_kg": 1.22,
        },
        14: {
            "avg_weight_kg": 42,
            "rpe_g_per_kg": 0.72,
            "rdd_reference_g_per_kg": 0.89,
            "rdd_mixed_diet_g_per_kg": 1.19,
        },
        16: {
            "avg_weight_kg": 49,
            "rpe_g_per_kg": 0.70,
            "rdd_reference_g_per_kg": 0.86,
            "rdd_mixed_diet_g_per_kg": 1.16,
        },
        18: {
            "avg_weight_kg": 52,
            "rpe_g_per_kg": 0.68,
            "rdd_reference_g_per_kg": 0.84,
            "rdd_mixed_diet_g_per_kg": 1.12,
        },
        float("inf"): {
            "avg_weight_kg": 55,
            "rpe_g_per_kg": 0.66,
            "rdd_reference_g_per_kg": 0.83,
            "rdd_mixed_diet_g_per_kg": 1.12,
        },
    },
}

def get_fat_requirements(age: float) -> dict:

    # 0 a <6 meses
    if age < 0.5:
        return {
            "total_min_percent": 0.40,
            "total_max_percent": 0.60,

            "saturated_max_percent": None,

            "polyunsaturated_min_percent": None,
            "polyunsaturated_max_percent": None,

            "cholesterol_max_mg": None,
        }

    # 6 meses a <2 años
    if age < 2:
        return {
            "total_min_percent": 0.30,
            "total_max_percent": 0.35,

            "saturated_max_percent": None,

            "polyunsaturated_min_percent": None,
            "polyunsaturated_max_percent": 0.15,

            "cholesterol_max_mg": None,
        }

    # 2 a <19 años
    if age < 19:
        return {
            "total_min_percent": 0.25,
            "total_max_percent": 0.35,

            "saturated_max_percent": 0.08,

            "polyunsaturated_min_percent": None,
            "polyunsaturated_max_percent": 0.11,

            "cholesterol_max_mg": 300,
        }

    # Adultos
    return {
        "total_min_percent": 0.20,
        "total_max_percent": 0.30,

        "saturated_max_percent": 0.10,

        "polyunsaturated_min_percent": 0.06,
        "polyunsaturated_max_percent": 0.11,

        "cholesterol_max_mg": 300,
    }

def get_tmb(gender: str, age: float):
    equations = TMB[gender]

    for max_age, equation in equations.items():
        if age < max_age:
            return equation

    raise ValueError(f"No se encontró ecuación para edad {age}")


def get_protein_requirement(gender: str, age: float) -> dict:
    # De 0 a < 5 años no hay diferenciación por sexo
    if age < 5:
        requirements = PROTEIN_REQUIREMENTS["all"]
    else:
        requirements = PROTEIN_REQUIREMENTS[gender]

    for max_age, requirement in requirements.items():
        if age < max_age:
            return requirement

    raise ValueError(f"No se encontró requerimiento de proteína para edad {age} y sexo {gender}")


CARBOHYDRATE_REQUIREMENTS = {
    0.5: {
        "type": "ingesta_adecuada",
        "grams_per_day": 60,
    },
    1: {
        "type": "ingesta_adecuada",
        "grams_per_day": 95,
    },
    float("inf"): {
        "type": "rpe",
        "grams_per_day": 100,
    },
}
def get_carbohydrate_requirement(age: float) -> dict:
    for max_age, requirement in CARBOHYDRATE_REQUIREMENTS.items():
        if age < max_age:
            return requirement

    raise ValueError(f"No se encontró requerimiento de carbohidratos para edad {age}")

FAT_KCAL_PER_GRAM = 9
def percent_energy_to_fat_grams(energy: float, percent: float | None) -> float | None:

    if percent is None:
        return None

    return (energy * percent / FAT_KCAL_PER_GRAM)

def evaluacion_de_requerimientos_diarios(p: Persona) -> dict:

    weight_evaluation = evaluacion_peso(p)

    calculation_weight = weight_evaluation["peso_para_calculos"]

    tmb_formula = get_tmb(p.sexo, p.edad)
    tmb = tmb_formula(calculation_weight)

    # REE = Requerimiento Estimado de Energía (INCAP),
    
    ree = tmb * p.naf_indice if p.edad > 10 and p.naf_indice is not None else tmb


    """
    Energia
    """

    if p.esta_embarazada:
        if p.mes_de_embarazo > 3: # En el primer tremestre no cambia 
            # FAO/WHO/UNU recommendation:
            # trimester 1: no dietary increment
            # trimester 2: +360 kcal/day
            # trimester 3: +475 kcal/day
            ree += 360 if p.mes_de_embarazo <= 6 else 475 # 360 para segundo trimestre; 475 para tercer trimeste 


    if p.esta_en_lactancia: 
        ree += 505 if p.reservas_de_energia_maternales else 675


    """
    Proteina
    """
    protein_requirement = get_protein_requirement(p.sexo, p.edad)

    pregnancy_protein = 0

    if p.esta_embarazada:
        if 4 <= p.mes_de_embarazo <= 6:
            pregnancy_protein = 13
        elif 7 <= p.mes_de_embarazo <= 9:
            pregnancy_protein = 42

    lactation_protein = 0

    if p.esta_en_lactancia:
        if p.lactancy_month <= 6:
            lactation_protein = 26
        elif p.lactancy_month <= 12:
            lactation_protein = 18


    """
    Carbohydrates
    """
    CARBOHYDRATE_ENERGY_MIN = 0.45
    CARBOHYDRATE_ENERGY_MAX = 0.65
    REFINED_SUGAR_ENERGY_MAX = 0.10
    CARBOHYDRATE_KCAL_PER_GRAM = 4

    carbohydrate_requirement = get_carbohydrate_requirement(p.edad)
    carbohydrate_minimum = carbohydrate_requirement["grams_per_day"]
    refined_sugar_max = None

    if carbohydrate_requirement["type"] == "rpe":
        if p.esta_embarazada:
            carbohydrate_minimum += 33

        if p.esta_en_lactancia:
            carbohydrate_minimum += 60

    if p.edad >= 1:
        carbohydrate_energy_min = (ree * CARBOHYDRATE_ENERGY_MIN / CARBOHYDRATE_KCAL_PER_GRAM )
        refined_sugar_max = (ree * REFINED_SUGAR_ENERGY_MAX / CARBOHYDRATE_KCAL_PER_GRAM)
        carbohydrate_energy_max = (ree * CARBOHYDRATE_ENERGY_MAX / CARBOHYDRATE_KCAL_PER_GRAM )

        carbohydrate_effective_min = max(carbohydrate_minimum, carbohydrate_energy_min )

    else:
        carbohydrate_energy_min = None
        carbohydrate_energy_max = None
        carbohydrate_effective_min = carbohydrate_minimum

    """
    Fibra Dietetica
    """
    FIBER_GRAMS_PER_1000_KCAL = 12
    fiber_requirement = None

    if p.edad >= 1:
        fiber_requirement = (ree / 1000 * FIBER_GRAMS_PER_1000_KCAL)

    """
    Lipids
    """

    """
    Lipids
    """

    fat_requirement = get_fat_requirements(p.edad)

    fat_total_min = percent_energy_to_fat_grams(ree, fat_requirement["total_min_percent"])
    fat_total_max = percent_energy_to_fat_grams(ree, fat_requirement["total_max_percent"])
    saturated_max = percent_energy_to_fat_grams(ree, fat_requirement["saturated_max_percent"])
    polyunsaturated_min = percent_energy_to_fat_grams(ree, fat_requirement["polyunsaturated_min_percent"])
    polyunsaturated_max = percent_energy_to_fat_grams(ree, fat_requirement["polyunsaturated_max_percent"])
    cholesterol_max = fat_requirement["cholesterol_max_mg"]

    return {
        "energy":{
            "ree": ree,
            "unit": "kcal"
        },
        "protein":{
            'rpe': (protein_requirement["rpe_g_per_kg"] * calculation_weight)+pregnancy_protein+lactation_protein,
            'ree':{
                'refence_diet': (protein_requirement["rdd_reference_g_per_kg"] * calculation_weight)+pregnancy_protein+lactation_protein,
                'mixed': (protein_requirement["rdd_mixed_diet_g_per_kg"] * calculation_weight)+pregnancy_protein+lactation_protein if protein_requirement["rdd_mixed_diet_g_per_kg"] is not None else None
            },
            "unit": "g"

        },
        "carbohydrates": {
            "reference_type": carbohydrate_requirement["type"],

            "reference_minimum": carbohydrate_minimum,

            "energy_distribution": {
                "minimum_percent": 45,
                "maximum_percent": 65,
                "minimum_grams": carbohydrate_energy_min,
                "maximum_grams": carbohydrate_energy_max,
            },

            "effective_minimum": carbohydrate_effective_min,
            "effective_maximum": carbohydrate_energy_max,
            "refined_sugars": {
                "maximum_percent_energy": 10,
                "maximum_grams": refined_sugar_max,
            },
            "unit": "g",
        },
        "fiber": {
            "minimum": fiber_requirement,
            "reference": "12_g_per_1000_kcal",
            "unit": "g"
        },
        "fat": {
            "total": {
                "minimum": fat_total_min,
                "maximum": fat_total_max,
                "unit": "g",
            },

            "saturated": {
                "maximum": saturated_max,
                "unit": "g",
            },

            "polyunsaturated": {
                "minimum": polyunsaturated_min,
                "maximum": polyunsaturated_max,
                "unit": "g",
            },

            "cholesterol": {
                "maximum": cholesterol_max,
                "unit": "mg",
            },
        },
    }


if __name__ == "__main__":

    personas_prueba = {
        # 0 A 5 AÑOS
        "Niño <5 rango referencia": Persona(edad=0.1, sexo="men", peso=3.3, naf="low", altura=0.50),
        "Niño <5 sobrepeso": Persona(edad=0.1, sexo="men", peso=4.2, naf="low", altura=0.50),
        "Niña <5 rango referencia": Persona(edad=0.1, sexo="women", peso=3.35, naf="low", altura=0.50),
        "Niña <5 sobrepeso": Persona(edad=0.1, sexo="women", peso=4.2, naf="low", altura=0.50),

        # 5 A 19 AÑOS
        "Niño 10 años rango referencia": Persona(edad=10, sexo="men", peso=32, naf="low", altura=1.40),
        "Niño 10 años sobrepeso": Persona(edad=10, sexo="men", peso=45, naf="low", altura=1.40),
        "Niña 12 años rango referencia": Persona(edad=12.1, sexo="women", peso=41, naf="low", altura=1.50),
        "Niña 12 años sobrepeso": Persona(edad=12, sexo="women", peso=55, naf="low", altura=1.50),

        # ADULTOS
        "Hombre adulto normal": Persona(edad=25, sexo="men", peso=65, naf="low", altura=1.70),
        "Hombre adulto sobrepeso": Persona(edad=25, sexo="men", peso=85, naf="low", altura=1.70),
        "Mujer adulta normal": Persona(edad=25, sexo="women", peso=60, naf="low", altura=1.65),
        "Mujer adulta sobrepeso": Persona(edad=25, sexo="women", peso=75, naf="low", altura=1.65),

        # EMBARAZO
        "Embarazada peso pregestacional normal": Persona(edad=28, sexo="women", peso=70, naf="low", altura=1.65, esta_embarazada=True, mes_de_embarazo=5, peso_preembarazo=62),
        "Embarazada con sobrepeso pregestacional": Persona(edad=30, sexo="women", peso=85, naf="low", altura=1.65, esta_embarazada=True, mes_de_embarazo=8, peso_preembarazo=78),

        # LACTANCIA
        "Mujer lactante con reservas": Persona(edad=28, sexo="women", peso=64, naf="low", altura=1.65, esta_en_lactancia=True, reservas_de_energia_maternales=True),
        "Mujer lactante sin reservas": Persona(edad=28, sexo="women", peso=58, naf="low", altura=1.65, esta_en_lactancia=True, reservas_de_energia_maternales=False),
    }

    for nombre, persona in personas_prueba.items():

        print("\n" + "=" * 80)
        print(nombre)
        print("=" * 80)

        try:
            evaluacion_peso_resultado = evaluacion_peso(persona)
            requerimientos = evaluacion_de_requerimientos_diarios(persona)

            print(f"Edad: {persona.edad} años ({persona.edad_meses} meses)")
            print(f"Sexo: {persona.sexo}")
            print(f"Peso real: {persona.peso:.2f} kg")
            print(f"Altura: {persona.altura:.2f} m")
            print(f"NAF: {persona.naf}")
            print()

            print("EVALUACIÓN DEL PESO")
            print(f"Estado: {evaluacion_peso_resultado['estado_de_indicador']}")
            print(f"Peso para cálculos: {evaluacion_peso_resultado['peso_para_calculos']:.2f} kg")
            print(f"Fuente de peso: {evaluacion_peso_resultado['fuente_de_peso']}")
            print(f"Requiere intervención profesional: {evaluacion_peso_resultado['requiere_intervencion_profesional']}")
            print()

            print("REQUERIMIENTOS DIARIOS")
            print(f"Energía: {requerimientos['energy']['ree']:.2f} kcal/día")
            print(f"Proteína RPE: {requerimientos['protein']['rpe']:.2f} g/día")
            print(f"Proteína dieta de referencia: {requerimientos['protein']['ree']['refence_diet']:.2f} g/día")

            proteina_mixta = requerimientos["protein"]["ree"]["mixed"]

            if proteina_mixta is not None:
                print(f"Proteína dieta mixta: {proteina_mixta:.2f} g/día")
            else:
                print("Proteína dieta mixta: No disponible")

        except Exception as e:
            print(f"ERROR: {e}")