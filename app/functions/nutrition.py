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



def evaluate_daily_requirements(p: Persona) -> dict:

    weight_evaluation = evaluacion_peso(p)

    calculation_weight = weight_evaluation["peso_para_calculos"]

    tmb_formula = get_tmb(p.sexo, p.edad)
    tmb = tmb_formula(calculation_weight)

    # REE = Requerimiento Estimado de Energía (INCAP),
    ree = tmb * p.naf_indice if p.naf_indice is not None else tmb\


    """
    Energy
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
    Protein
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
    return {
        "energy":{
            "ree": ree,
            "unit": "kcal"
        },
        "protein":{
            'rpe': protein_requirement["rpe_g_per_kg"] * calculation_weight ,
            'ree':{
                'refence_diet': protein_requirement["rdd_reference_g_per_kg"] * calculation_weight,
                'mixed': protein_requirement["rdd_mixed_diet_g_per_kg"] * calculation_weight if protein_requirement["rdd_mixed_diet_g_per_kg"] is not None else None
            },
            "unit": "g"

        }
    }


if __name__ == "__main__":

    personas_prueba = {

        # ==========================================
        # 0 A 5 AÑOS
        # ==========================================

        "Niño <5 rango referencia": Persona(
            0.1,
            "men",
            3.3,
            "low",
            0.50
        ),

        "Niño <5 sobrepeso": Persona(
            0.1,
            "men",
            4.2,
            "low",
            0.50
        ),

        "Niña <5 rango referencia": Persona(
            0.1,
            "women",
            3.35,
            "low",
            0.50
        ),

        "Niña <5 sobrepeso": Persona(
            0.1,
            "women",
            4.2,
            "low",
            0.50
        ),


        # ==========================================
        # 5 A 19 AÑOS
        # ==========================================

        # 10 años, 1.40 m
        "Niño 10 años rango referencia": Persona(
            10,
            "men",
            32,
            "low",
            1.40
        ),

        "Niño 10 años sobrepeso": Persona(
            10,
            "men",
            45,
            "low",
            1.40
        ),

        # 12 años, 1.50 m
        "Niña 12 años rango referencia": Persona(
            12,
            "women",
            40,
            "low",
            1.50
        ),

        "Niña 12 años sobrepeso": Persona(
            12,
            "women",
            55,
            "low",
            1.50
        ),


        # ==========================================
        # ADULTOS
        # ==========================================

        "Hombre adulto normal": Persona(
            25,
            "men",
            65,
            "low",
            1.70
        ),

        "Hombre adulto sobrepeso": Persona(
            25,
            "men",
            85,
            "low",
            1.70
        ),

        "Mujer adulta normal": Persona(
            25,
            "women",
            60,
            "low",
            1.65
        ),

        "Mujer adulta sobrepeso": Persona(
            25,
            "women",
            75,
            "low",
            1.65
        ),
    }


    for nombre, persona in personas_prueba.items():

        try:
            resultado = evaluacion_peso(persona)

            print("\n" + "=" * 70)
            print(nombre)
            print("=" * 70)

            print(
                f"Edad: "
                f"{persona.edad} años "
                f"({persona.edad_meses} meses)"
            )

            print(
                f"Sexo: {persona.sexo}"
            )

            print(
                f"Peso real: "
                f"{resultado['peso_real']:.2f} kg"
            )

            print(
                f"Peso para cálculos: "
                f"{resultado['peso_para_calculos']:.2f} kg"
            )

            print(
                f"Indicador: "
                f"{resultado['indicador']}"
            )

            valor = resultado[
                "valor_de_indicador"
            ]

            if valor is not None:
                print(
                    f"Valor indicador: "
                    f"{valor:.2f}"
                )

            print(
                f"Estado: "
                f"{resultado['estado_de_indicador']}"
            )

            print(
                f"Usa peso real: "
                f"{resultado['usa_peso_real']}"
            )

            print(
                f"Fuente: "
                f"{resultado['fuente_de_peso']}"
            )

            print(
                "Requiere intervención profesional: "
                f"{resultado['requiere_intervencion_profesional']}"
            )

        except Exception as e:

            print("\n" + "=" * 70)
            print(nombre)
            print("=" * 70)
            print(
                f"ERROR: {e}"
            )