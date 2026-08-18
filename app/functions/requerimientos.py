from ..data.extractors import cargar_referencia_peso_longitud_0_5, cargar_referencia_imc_edad_5_19

"""
Contiene requerimiento nutricionales y valores de referencia para las evaluaciones (evaluacion.py) a realizar

- Pesos de referencia para grupos poblacionales 
- Valores de IMC para adultos 
- Requerimientos de proteina, lipidos, carbohidratos, micronutrientes y otros



"""

"""
####
PESO
####
"""


PESO_LONGITUD_NINAS_0_2 = cargar_referencia_peso_longitud_0_5( 'girls', '0-2')
PESO_ALTURA_NINOS_2_5 = cargar_referencia_peso_longitud_0_5('boys', '2-5')
PESO_LONGITUD_NINOS_0_2 = cargar_referencia_peso_longitud_0_5('boys', '0-2')
PESO_ALTURA_NINAS_2_5 = cargar_referencia_peso_longitud_0_5( 'girls', '2-5')


IMC_EDAD_MESES_NINAS = cargar_referencia_imc_edad_5_19('girls')
IMC_EDAD_MESES_NINOS = cargar_referencia_imc_edad_5_19('boys')


IMC_ADULTO_MIN = 18.5
IMC_ADULTO_MAX = 24.9
IMC_REFERENCIA_INCAP = 22.0
IMC_OBESIDAD_MIN = 30.0

"""
####
Energia
####
"""

TMB = {
    "hombre": {
        3: lambda peso: 59.512 * peso - 30.4,
        10: lambda peso: 22.706 * peso + 504.3,
        18: lambda peso: 17.686 * peso + 658.2,
        30: lambda peso: 15.057 * peso + 692.2,
        60: lambda peso: 11.472 * peso + 873.1,
        float("inf"): lambda peso: 11.711 * peso + 587.7,
    },

    "mujer": {
        3: lambda peso: 58.317 * peso - 31.1,
        10: lambda peso: 20.315 * peso + 485.9,
        18: lambda peso: 13.384 * peso + 692.6,
        30: lambda peso: 14.818 * peso + 486.6,
        60: lambda peso: 8.126 * peso + 845.6,
        float("inf"): lambda peso: 9.082 * peso + 658.5,
    },
}
# Recomendación FAO/OMS/UNU:
# primer trimestre: sin incremento dietético
# segundo trimestre: +360 kcal/día
# tercer trimestre: +475 kcal/día
ENERGIA_ADICIONAL_EMBARAZDA_SEGUNDO_TRIMESTRE = 360
ENERGIA_ADICIONAL_EMBARAZDA_TERCER_TRIMESTRE = 475

"""
####
####
####

Macronutrientes

####
####
####
"""
"""
####
PROTEINA
####
"""

REQUERIMIENTOS_PROTEINA = {
    "todos": {
        0.25: {
            "rpe_g_por_kg": 1.32,
            "rdd_referencia_g_por_kg": 1.64,
            "rdd_dieta_mixta_g_por_kg": None,
        },
        0.5: {
            "rpe_g_por_kg": 1.06,
            "rdd_referencia_g_por_kg": 1.25,
            "rdd_dieta_mixta_g_por_kg": None,
        },
        0.75: {
            "rpe_g_por_kg": 1.12,
            "rdd_referencia_g_por_kg": 1.31,
            "rdd_dieta_mixta_g_por_kg": 1.76,
        },
        1: {
            "rpe_g_por_kg": 1.12,
            "rdd_referencia_g_por_kg": 1.31,
            "rdd_dieta_mixta_g_por_kg": 1.76,
        },
        2: {
            "rpe_g_por_kg": 0.95,
            "rdd_referencia_g_por_kg": 1.14,
            "rdd_dieta_mixta_g_por_kg": 1.54,
        },
        3: {
            "rpe_g_por_kg": 0.79,
            "rdd_referencia_g_por_kg": 0.97,
            "rdd_dieta_mixta_g_por_kg": 1.31,
        },
        4: {
            "rpe_g_por_kg": 0.73,
            "rdd_referencia_g_por_kg": 0.90,
            "rdd_dieta_mixta_g_por_kg": 1.21,
        },
        5: {
            "rpe_g_por_kg": 0.69,
            "rdd_referencia_g_por_kg": 0.86,
            "rdd_dieta_mixta_g_por_kg": 1.16,
        },
    },

    "hombre": {
        6: {
            "rpe_g_por_kg": 0.69,
            "rdd_referencia_g_por_kg": 0.85,
            "rdd_dieta_mixta_g_por_kg": 1.14,
        },
        7: {
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.20,
        },
        8: {
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.23,
        },
        9: {
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        10: {
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        12: {
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.23,
        },
        14: {
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.90,
            "rdd_dieta_mixta_g_por_kg": 1.21,
        },
        16: {
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.19,
        },
        18: {
            "rpe_g_por_kg": 0.71,
            "rdd_referencia_g_por_kg": 0.87,
            "rdd_dieta_mixta_g_por_kg": 1.16,
        },
        float("inf"): {
            "rpe_g_por_kg": 0.66,
            "rdd_referencia_g_por_kg": 0.83,
            "rdd_dieta_mixta_g_por_kg": 1.12,
        },
    },

    "mujer": {
        6: {
            "rpe_g_por_kg": 0.69,
            "rdd_referencia_g_por_kg": 0.85,
            "rdd_dieta_mixta_g_por_kg": 1.14,
        },
        7: {
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.20,
        },
        8: {
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.23,
        },
        9: {
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        10: {
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        12: {
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.22,
        },
        14: {
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.19,
        },
        16: {
            "rpe_g_por_kg": 0.70,
            "rdd_referencia_g_por_kg": 0.86,
            "rdd_dieta_mixta_g_por_kg": 1.16,
        },
        18: {
            "rpe_g_por_kg": 0.68,
            "rdd_referencia_g_por_kg": 0.84,
            "rdd_dieta_mixta_g_por_kg": 1.12,
        },
        float("inf"): {
            "rpe_g_por_kg": 0.66,
            "rdd_referencia_g_por_kg": 0.83,
            "rdd_dieta_mixta_g_por_kg": 1.12,
        },
    },
}

PROTEINA_DE_REFERENCIA_ADICIONAL_EMBARAZO_SEGUNDO_TRIMESTRE = 10
PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_SEGUNDO_TRIMESTRE = 13
PROTEINA_DE_REFERENCIA_ADICIONAL_EMBARAZO_TERCER_TRIMESTRE = 31
PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_TERCER_TRIMESTRE = 42

PROTEINA_DE_REFERENCIA_ADICIONAL_LACTANCIA_PRIMER_SEMESTRE = 19
PROTEINA_DIETA_MIXTA_ADICIONAL_LACTANCIA_PRIMER_SEMESTRE = 26
PROTEINA_DE_REFERENCIA_ADICIONAL_LACTANCIA_SEGUNDO_SEMESTRE = 13
PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_SEGUNDO_SEMESTRE = 18

"""
####
LIPIDOS
####
"""
KCAL_POR_GRAMO_GRASA = 9
'''
RADM = Rango Aceptable de distribucion de macronutrientes: Es la distribucion de macros asociada a un menor riesgo 
de padecer enfermedades cronicas, al tiempo que asegura una ingesta suficiente. 
'''
RDD_LIPIDOS = {
    0.5:{ # 0 a 6 meses
        "total_min": 0.40,
        "total_max": 0.60,
        "saturados_max": None,
        "poliinsaturados_min": None,
        "poliinsaturados_max": None,
        "trans_max": None
    },
    2: {
        "total_min": 0.30,
        "total_max": 0.35,
        "saturados_max": None,
        "poliinsaturados_min": None,
        "poliinsaturados_max": 0.15,
        "trans_max": 0.01
    },
    19: {
        "total_min": 0.25,
        "total_max": 0.35,
        "saturados_max": 0.08,
        "poliinsaturados_min": None,
        "poliinsaturados_max": 0.11,
        "trans_max": 0.01

    },
    float("inf"):{
        "total_min": 0.20,
        "total_max": 0.30,
        "saturados_max": 0.10,
        "poliinsaturados_min": 0.06,
        "poliinsaturados_max": 0.11,
        "trans_max": 0.01
    }
}

RECOMENDACION_MAXIMO_COLESTEROL_MG = 300

"""
####
Carbohidratos
####
"""
CARBOHIDRATOS_ENERGIA_MIN = 0.55
CARBOHIDRATOS_ENERGIA_MAX = 0.70
AZUCARES_REFINADOS_ENERGIA_MAX = 0.10
KCAL_POR_GRAMO_CARBOHIDRATO = 4

REQUERIMIENTOS_CARBOHIDRATOS = {
    0.5: {
        "ia": 60,
        'rpe': None,
    },
    1: {
        "ia": 95,
        'rpe': None,
    },
    float("inf"): {
        "ia": None,
        "rpe": 100,
    },
}
CARBOHIDRATOS_ADICIONALES_EMBARAZADA_ULTIMO_TRIMESTRE = 35
CARBOHIDRATOS_ADICIONALES_LACTANCIA = 60


"""
####
Fibra
####
"""
GRAMOS_DE_FIBRA_POR_1000_KCAL = 12


"""
####
####
####

Micronutrientes

####
####
####
"""


"""
####
Vitamina A
####
"""
REQUERIMIENTOS_VITAMINA_A = {
    "todos": {
        0.5: {
            "rpe": None,
            "rdd": None,
            "ia": 375,
        },
        1: {
            "rpe": None,
            "rdd": None,
            "ia": 450,
        },
        4: {
            "rpe": 210,
            "rdd": 300,
            "ia": None,
        },
        7: {
            "rpe": 250,
            "rdd": 350,
            "ia": None,
        },
        10: {
            "rpe": 300,
            "rdd": 450,
            "ia": None,
        },
    },

    "hombre": {
        12: {
            "rpe": 400,
            "rdd": 600,
            "ia": None,
        },
        16: {
            "rpe": 500,
            "rdd": 700,
            "ia": None,
        },
        18: {
            "rpe": 525,
            "rdd": 750,
            "ia": None,
        },
        float("inf"): {
            "rpe": 525,
            "rdd": 750,
            "ia": None,
        },
    },

    "mujer": {
        12: {
            "rpe": 350,
            "ia": None,
        },
        14: {
            "rpe": 400,
            "ia": None,
        },
        18: {
            "rpe": 450,
            "ia": None,
        },
        float("inf"): {
            "rpe": 450,
            "ia": None,
        },
    },
}

IMT_RETINOL = {
    4: 600,
    9: 900,
    14: 1700,
    19: 2800,
    float("inf"): 3000,
}

REQUERIMIENTO_ADICIONAL_VITAMINA_A_EMBARAZADAS = 50
REQUERIMIENTO_ADICIONAL_VITAMINA_A_LACTANTES = 50

VITAMINA_A_LACTANCIA = {
    "rpe": 825,
    "ia": None,
}

"""
Tiamina
"""
REQUERIMIENTOS_TIAMINA = {
    "todos": {
        0.5: {
            "ia": 0.2,
            "rpe": None, 
            "rdd": None
        },
        1: {
            "ia": None, 
            "rpe": 0.3, 
            "rdd": 0.3
        },
        4: {
            "ia": None, 
            "rpe": 0.4, 
            "rdd": 0.4 
        },
        7: {
            "ia": None, 
            "rpe": 0.4, 
            "rdd": 0.5 
        },
        10: {
            "ia": None, 
            "rpe": 0.5, 
            "rdd": 0.6 
        },
    },
    "hombre":{
        12: {
            "ia": None, 
            "rpe": 0.6, 
            "rdd": 0.7 
        },
        14: {
            "ia": None, 
            "rpe": 0.7, 
            "rdd": 0.9
        },
        16: {
            "ia": None, 
            "rpe": 0.9, 
            "rdd": 1
        },
        float("inf"): {
            "ia": None, 
            "rpe": 1, 
            "rdd": 1.2
        }
    },
    "mujer":{
        12: {
            "ia": None, 
            "rpe": 0.7, 
            "rdd": 0.8
        },
        14: {
            "ia": None, 
            "rpe": 0.8, 
            "rdd": 0.9
        },
        float("inf"): {
            "ia": None, 
            "rpe": 0.9, 
            "rdd": 1.1
        },
    }
}

REQUERIMIENTO_ADICIONAL_TIAMINA_EMBARAZADAS = 0.3
REQUERIMIENTOS_ADICIONAL_TIAMINA_LACTANCIA =  0.16


"""
Riboflavina
"""

REQUERIMIENTOS_RIBOFLAVINA = {
    "todos": {
        0.5: {
            "ia": 0.3,
            "rpe": None, 
            "rdd": None
        },
        1: {
            "ia": 0.4, 
            "rpe": None, 
            "rdd": None
        },
        7: {
            "ia": None, 
            "rpe": 0.4, 
            "rdd": 0.5 
        },
        10: {
            "ia": None, 
            "rpe": 0.5, 
            "rdd": 0.6 
        },
    },
    "hombre":{
        12: {
            "ia": None, 
            "rpe": 0.7, 
            "rdd": 0.8 
        },
        14: {
            "ia": None, 
            "rpe": 0.8, 
            "rdd": 1
        },
        16: {
            "ia": None, 
            "rpe": 1, 
            "rdd": 1.2
        },
        float("inf"): {
            "ia": None, 
            "rpe": 1.1, 
            "rdd": 1.3
        }
    },
    "mujer":{
        12: {
            "ia": None, 
            "rpe": 0.7, 
            "rdd": 0.8
        },
        14: {
            "ia": None, 
            "rpe": 0.8, 
            "rdd": 0.9
        },
        float("inf"): {
            "ia": None, 
            "rpe": 0.9, 
            "rdd": 1.1
        },
    }
}

REQUERIMIENTO_ADICIONAL_RIBOFLAVINA_EMBARAZADAS = 0.3
REQUERIMIENTOS_ADICIONAL_RIBOFLAVINA_LACTANCIA =  0.4

"""
Niacina

Para infantes (menores de 1 año), el requerimiento es de niacina performada.  

Equivalente de Niacina (EN)
"""
REQUERIMIENTOS_NIACINA = {
    "todos": {
        0.5: {
            "ia": 2,
            "rpe": None, 
            "rdd": None
        },
        1: {
            "ia": 4, 
            "rpe": None, 
            "rdd": None
        },
        4: {
            "ia": None, 
            "rpe": 4, 
            "rdd": 6 
        },
        7: {
            "ia": None, 
            "rpe": 5, 
            "rdd": 6 
        },
        10: {
            "ia": None, 
            "rpe": 6, 
            "rdd": 8
        },
    },
    "hombre":{
        12: {
            "ia": None, 
            "rpe": 7, 
            "rdd": 9 
        },
        14: {
            "ia": None, 
            "rpe": 9, 
            "rdd": 11
        },
        16: {
            "ia": None, 
            "rpe": 10, 
            "rdd": 14
        },
        18: {
            "ia": None, 
            "rpe": 12, 
            "rdd": 15
        },
        float("inf"): {
            "ia": None, 
            "rpe": 12, 
            "rdd": 16
        }
    },
    "mujer":{
        12: {
            "ia": None, 
            "rpe": 8, 
            "rdd": 10
        },
        14: {
            "ia": None, 
            "rpe": 10, 
            "rdd": 13
        },
        16: {
            "ia": None, 
            "rpe": 11, 
            "rdd": 14
        },
        18: {
            "ia": None, 
            "rpe": 11, 
            "rdd": 15
        },
        float("inf"): {
            "ia": None, 
            "rpe": 11, 
            "rdd": 14
        },
    }
}
REQUERIMIENTO_ADICIONAL_NIACINA_EMBARAZADAS = 3
REQUERIMIENTOS_ADICIONAL_NIACINA_LACTANCIA =  2.4


"""
Vitamina B6
"""
REQUERIMIENTOS_VITAMINAB6 = {
    "todos": {
        0.5: {
            "ia": 0.1,
            "rpe": None, 
            "rdd": None
        },
        1: {
            "ia": 0.3, 
            "rpe": None, 
            "rdd": None
        },
        4: {
            "ia": None, 
            "rpe": 0.4, 
            "rdd": 0.5 
        },
        7: {
            "ia": None, 
            "rpe": 0.5, 
            "rdd": 0.6 
        },
        10: {
            "ia": None, 
            "rpe": 0.6, 
            "rdd": 0.7
        },
    },
    "hombre":{
        12: {
            "ia": None, 
            "rpe": 0.7, 
            "rdd": 0.8 
        },
        14: {
            "ia": None, 
            "rpe": 0.8, 
            "rdd": 1
        },
        16: {
            "ia": None, 
            "rpe": 1, 
            "rdd": 1.2
        },
        65: {
            "ia": None, 
            "rpe": 1.1, 
            "rdd": 1.3
        },
        float("inf"): {
            "ia": None, 
            "rpe": 1.4, 
            "rdd": 1.7
        }
    },
    "mujer":{
        12: {
            "ia": None, 
            "rpe": 0.8, 
            "rdd": 1
        },
        14: {
            "ia": None, 
            "rpe": 1, 
            "rdd": 1.2
        },
        65: {
            "ia": None, 
            "rpe": 1.1, 
            "rdd": 1.3
        },
        float("inf"): {
            "ia": None, 
            "rpe": 1.3, 
            "rdd": 1.6
        },
    } 
}

REQUERIMIENTO_ADICIONAL_VITAMINAB6_EMBARAZADAS = 0.5
REQUERIMIENTOS_ADICIONAL_VITAMINAB6_LACTANCIA =  0.6

IMT_VITAMINA_B6 = {
    3: 30,
    8: 40, 
    13: 60,
    18: 80, 
    float('inf'): 100
}
"""
Folatos

"""
REQUERIMIENTOS_FOLATOS =  { # EFD = Equivalentes de Folato Dietetico
    "todos": {
        0.5: {
            "ia": 52,
            "rpe": None, 
            "rdd": None
        },
        1: {
            "ia": 75, 
            "rpe": None, 
            "rdd": None
        },
        4: {
            "ia": None, 
            "rpe": 120, 
            "rdd": 150 
        },
        7: {
            "ia": None, 
            "rpe": 140, 
            "rdd": 170 
        },
        10: {
            "ia": None, 
            "rpe": 170, 
            "rdd": 200
        },
    },
    "hombre":{
        12: {
            "ia": None, 
            "rpe": 200, 
            "rdd": 250 
        },
        14: {
            "ia": None, 
            "rpe": 250, 
            "rdd": 300
        },
        16: {
            "ia": None, 
            "rpe": 280, 
            "rdd": 350
        },
        18: {
            "ia": None, 
            "rpe": 310, 
            "rdd": 375
        },
        float("inf"): {
            "ia": None, 
            "rpe": 320, 
            "rdd": 400
        }
    },
    "mujer":{
        12: {
            "ia": None, 
            "rpe": 225, 
            "rdd": 280
        },
        14: {
            "ia": None, 
            "rpe": 280, 
            "rdd": 350
        },
        16: {
            "ia": None, 
            "rpe": 310, 
            "rdd": 375
        },
        18: {
            "ia": None, 
            "rpe": 325, 
            "rdd": 400
        },
        float("inf"): {
            "ia": None, 
            "rpe": 320, 
            "rdd": 400
        },
    } 
}

REQUERIMIENTO_ADICIONAL_FOLATOS_EMBARAZADAS = 250
REQUERIMIENTOS_ADICIONAL_FOLATOS_LACTANCIA =  130
RECOMENDACION_ACIDO_FOLICO_SUPLEMENTARIO_EMBARAZO = 400  

IMT_FOLATO_SINTETICO = {
    12: 300, 
    18: 600,
    float('inf'): 1000
}

"""
Vitamina B12
"""
REQUERIMIENTOS_VITAMINAB12 =  { 
    "todos": {
        0.5: {
            "ia": 0.4,
            "rpe": None, 
            "rdd": None
        },
        1: {
            "ia": 0.5, 
            "rpe": None, 
            "rdd": None
        },
        4: {
            "ia": None, 
            "rpe": 0.7, 
            "rdd": 0.9 
        },
        7: {
            "ia": None, 
            "rpe": 0.9, 
            "rdd": 1.1 
        },
        10: {
            "ia": None, 
            "rpe": 1.1, 
            "rdd": 1.3
        },
    },
    "hombre":{
        12: {
            "ia": None, 
            "rpe": 1.2, 
            "rdd": 1.5 
        },
        14: {
            "ia": None, 
            "rpe": 1.5, 
            "rdd": 1.8
        },
        16: {
            "ia": None, 
            "rpe": 1.8, 
            "rdd": 2.2
        },
        float("inf"): {
            "ia": None, 
            "rpe": 2.0, 
            "rdd": 2.4
        }
    },
    "mujer":{
        14: {
            "ia": None, 
            "rpe": 1.5, 
            "rdd": 1.8 
        },

        float("inf"): {
            "ia": None, 
            "rpe": 2.0, 
            "rdd": 2.4
        }
    } 
}

REQUERIMIENTO_ADICIONAL_VITAMINAB12_EMBARAZO = 0.2
REQUERIMIENTO_ADICIONAL_VITAMINAB12_LACTANCIA = 0.4
"""

####
Vitamina Complejo B
####
"""

"""
####
Acido Pantotenico
####
"""
IA_ACIDO_PANTOTENICO = {
    "todos": {
        0.5: 1.7,
        1: 1.8,
        4: 2.0,
        7: 2.5,
        10:  3.0,
    },
    "hombre": {
        12:  3.0,
        14:  4.0,
        float("inf"):  5.0,
    },
    "mujer": {
        12: 4.0 ,
        14: 4.0,
        float("inf"):  5.0,
    },
}
ACIDO_PANTOTENICO_ADICIONAL_EMBARAZO = 1
ACIDO_PANTOTENICO_ADICIONAL_LACTANCIA = 1


"""
####
Vitamina C
####
"""
REQUERIMIENTOS_VITAMINA_C = {
    "todos": {
        0.5: {"ia": 35, "rdd": None},
        1:   {"ia": 50, "rdd": None},
        4:   {"ia": None, "rdd": 15},
        7:   {"ia": None, "rdd": 25},
        10:  {"ia": None, "rdd": 35},
    },

    "hombre": {
        12: {"ia": None, "rdd": 40},
        14: {"ia": None, "rdd": 50},
        16: {"ia": None, "rdd": 60},
        18: {"ia": None, "rdd": 70},
        65: {"ia": None, "rdd": 75},
        float("inf"): {"ia": None, "rdd": 75},
    },

    "mujer": {
        12: {"ia": None, "rdd": 40},
        14: {"ia": None, "rdd": 50},
        16: {"ia": None, "rdd": 60},
        18: {"ia": None, "rdd": 60},
        65: {"ia": None, "rdd": 65},
        float("inf"): {"ia": None, "rdd": 65},
    },
}

VITAMINA_C_EMBARAZO = {"ia": None, "rdd": 75}
VITAMINA_C_LACTANCIA = {"ia": None, "rdd": 100}

"""
####
Vitamina D
####
"""

IA_VITAMINA_D = {
    50: 5,
    70: 10,
    float("inf"): 15,
}

VITAMINA_D_EMBARAZO = 5
VITAMINA_D_LACTANCIA = 5

LIMITE_SUPERIOR_VITAMINA_D = {
    1: 25,               # lactantes
    float("inf"): 50,    # niños y adultos
}

"""
####
Vitamina E
####
"""

REQUERIMIENTOS_VITAMINA_E = {
    "todos": {
        0.5: {"ia":4, "rdd": None},
        1: {"ia":5, "rdd": None},
        4: {"ia":None, "rdd": 5},
        7: {"ia":None, "rdd": 6},
        10: {"ia":None, "rdd": 8},
    },

    "hombre": {
        12: 9,
        14: 10,
        16: 13,
        18: 14,
        65: 15,
        float("inf"): 15,
    },

    "mujer": {
        12: 11,
        14: 13,
        16: 14,
        18: 15,
        65: 15,
        float("inf"): 15,
    },
}

VITAMINA_E_EMBARAZO = 15
VITAMINA_E_LACTANCIA = 19


"""
####
Vitamina K
####
"""

REQUERIMIENTOS_VITAMINA_K = {
    "todos": {
        0.5: 5,
        1: 10,
        4: 15,
        7: 20,
        10: 25,
    },

    "hombre": {
        12: 35,
        14: 45,
        16: 55,
        18: 60,
        65: 65,
        float("inf"): 65,
    },

    "mujer": {
        12: 35,
        14: 45,
        16: 50,
        18: 55,
        65: 55,
        float("inf"): 55,
    },
}

VITAMINA_K_EMBARAZO = 55
VITAMINA_K_LACTANCIA = 55