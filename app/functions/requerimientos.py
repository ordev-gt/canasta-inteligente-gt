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
            "peso_promedio_kg": 4.85,
            "rpe_g_por_kg": 1.32,
            "rdd_referencia_g_por_kg": 1.64,
            "rdd_dieta_mixta_g_por_kg": None,
        },
        0.5: {
            "peso_promedio_kg": 6.67,
            "rpe_g_por_kg": 1.06,
            "rdd_referencia_g_por_kg": 1.25,
            "rdd_dieta_mixta_g_por_kg": None,
        },
        0.75: {
            "peso_promedio_kg": 7.93,
            "rpe_g_por_kg": 1.12,
            "rdd_referencia_g_por_kg": 1.31,
            "rdd_dieta_mixta_g_por_kg": 1.76,
        },
        1: {
            "peso_promedio_kg": 8.82,
            "rpe_g_por_kg": 1.12,
            "rdd_referencia_g_por_kg": 1.31,
            "rdd_dieta_mixta_g_por_kg": 1.76,
        },
        2: {
            "peso_promedio_kg": 10.55,
            "rpe_g_por_kg": 0.95,
            "rdd_referencia_g_por_kg": 1.14,
            "rdd_dieta_mixta_g_por_kg": 1.54,
        },
        3: {
            "peso_promedio_kg": 13.0,
            "rpe_g_por_kg": 0.79,
            "rdd_referencia_g_por_kg": 0.97,
            "rdd_dieta_mixta_g_por_kg": 1.31,
        },
        4: {
            "peso_promedio_kg": 15.15,
            "rpe_g_por_kg": 0.73,
            "rdd_referencia_g_por_kg": 0.90,
            "rdd_dieta_mixta_g_por_kg": 1.21,
        },
        5: {
            "peso_promedio_kg": 17.5,
            "rpe_g_por_kg": 0.69,
            "rdd_referencia_g_por_kg": 0.86,
            "rdd_dieta_mixta_g_por_kg": 1.16,
        },
    },

    "hombre": {
        6: {
            "peso_promedio_kg": 18.26,
            "rpe_g_por_kg": 0.69,
            "rdd_referencia_g_por_kg": 0.85,
            "rdd_dieta_mixta_g_por_kg": 1.14,
        },
        7: {
            "peso_promedio_kg": 20.36,
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.20,
        },
        8: {
            "peso_promedio_kg": 22.58,
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.23,
        },
        9: {
            "peso_promedio_kg": 25.01,
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        10: {
            "peso_promedio_kg": 27.57,
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        12: {
            "peso_promedio_kg": 32,
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.23,
        },
        14: {
            "peso_promedio_kg": 41,
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.90,
            "rdd_dieta_mixta_g_por_kg": 1.21,
        },
        16: {
            "peso_promedio_kg": 53,
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.19,
        },
        18: {
            "peso_promedio_kg": 61,
            "rpe_g_por_kg": 0.71,
            "rdd_referencia_g_por_kg": 0.87,
            "rdd_dieta_mixta_g_por_kg": 1.16,
        },
        float("inf"): {
            "peso_promedio_kg": 64,
            "rpe_g_por_kg": 0.66,
            "rdd_referencia_g_por_kg": 0.83,
            "rdd_dieta_mixta_g_por_kg": 1.12,
        },
    },

    "mujer": {
        6: {
            "peso_promedio_kg": 17.69,
            "rpe_g_por_kg": 0.69,
            "rdd_referencia_g_por_kg": 0.85,
            "rdd_dieta_mixta_g_por_kg": 1.14,
        },
        7: {
            "peso_promedio_kg": 19.67,
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.20,
        },
        8: {
            "peso_promedio_kg": 21.87,
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.23,
        },
        9: {
            "peso_promedio_kg": 24.57,
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        10: {
            "peso_promedio_kg": 27.56,
            "rpe_g_por_kg": 0.75,
            "rdd_referencia_g_por_kg": 0.92,
            "rdd_dieta_mixta_g_por_kg": 1.24,
        },
        12: {
            "peso_promedio_kg": 33,
            "rpe_g_por_kg": 0.74,
            "rdd_referencia_g_por_kg": 0.91,
            "rdd_dieta_mixta_g_por_kg": 1.22,
        },
        14: {
            "peso_promedio_kg": 42,
            "rpe_g_por_kg": 0.72,
            "rdd_referencia_g_por_kg": 0.89,
            "rdd_dieta_mixta_g_por_kg": 1.19,
        },
        16: {
            "peso_promedio_kg": 49,
            "rpe_g_por_kg": 0.70,
            "rdd_referencia_g_por_kg": 0.86,
            "rdd_dieta_mixta_g_por_kg": 1.16,
        },
        18: {
            "peso_promedio_kg": 52,
            "rpe_g_por_kg": 0.68,
            "rdd_referencia_g_por_kg": 0.84,
            "rdd_dieta_mixta_g_por_kg": 1.12,
        },
        float("inf"): {
            "peso_promedio_kg": 55,
            "rpe_g_por_kg": 0.66,
            "rdd_referencia_g_por_kg": 0.83,
            "rdd_dieta_mixta_g_por_kg": 1.12,
        },
    },
}

"""
####
LIPIDOS
####
"""
KCAL_POR_GRAMO_GRASA = 9
REQUERIMIENTOS_LIPIDOS = {
    0.5:{ # 0 a 6 meses
        "grasa_total_porcentaje_min": 0.40,
        "grasa_total_porcentaje_max": 0.60,
        "saturados_porcentaje_max": None,
        "poliinsaturados_porcentaje_min": None,
        "poliinsaturados_porcentaje_max": None,
        "colesterol_max_mg": None,
    },
    2: {
        "grasa_total_porcentaje_min": 0.30,
        "grasa_total_porcentaje_max": 0.35,
        "saturados_porcentaje_max": None,
        "poliinsaturados_porcentaje_min": None,
        "poliinsaturados_porcentaje_max": 0.15,
        "colesterol_max_mg": None
    },
    19: {
        "grasa_total_porcentaje_min": 0.25,
        "grasa_total_porcentaje_max": 0.35,
        "saturados_porcentaje_max": 0.08,
        "poliinsaturados_porcentaje_min": None,
        "poliinsaturados_porcentaje_max": 0.11,
        "colesterol_max_mg": 300,
    },
    float("inf"):{
        "grasa_total_porcentaje_min": 0.20,
        "grasa_total_porcentaje_max": 0.30,
        "saturados_porcentaje_max": 0.10,
        "poliinsaturados_porcentaje_min": 0.06,
        "poliinsaturados_porcentaje_max": 0.11,
        "colesterol_max_mg": 300,
    }

}

"""
####
Carbohidratos
####
"""
CARBOHIDRATOS_ENERGIA_MIN = 0.45
CARBOHIDRATOS_ENERGIA_MAX = 0.65
AZUCARES_REFINADOS_ENERGIA_MAX = 0.10
KCAL_POR_GRAMO_CARBOHIDRATO = 4

REQUERIMIENTOS_CARBOHIDRATOS = {
    0.5: {
        "tipo": "ingesta_adecuada",
        "gramos_por_dia": 60,
    },
    1: {
        "tipo": "ingesta_adecuada",
        "gramos_por_dia": 95,
    },
    float("inf"): {
        "tipo": "rpe",
        "gramos_por_dia": 100,
    },
}

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
        14: {
            "rpe": 500,
            "rdd": 700,
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
            "rdd": 500,
            "ia": None,
        },
        14: {
            "rpe": 400,
            "rdd": 600,
            "ia": None,
        },
        16: {
            "rpe": 450,
            "rdd": 650,
            "ia": None,
        },
        18: {
            "rpe": 450,
            "rdd": 650,
            "ia": None,
        },
        float("inf"): {
            "rpe": 450,
            "rdd": 650,
            "ia": None,
        },
    },
}

LIMITE_SUPERIOR_VITAMINA_A = {
    4: 600,
    9: 900,
    14: 1700,
    19: 2800,
    float("inf"): 3000,
}
VITAMINA_A_EMBARAZO = {
    "rpe": 500,
    "rdd": 700,
    "ia": None,
}

VITAMINA_A_LACTANCIA = {
    "rpe": 825,
    "rdd": 1000,
    "ia": None,
}



"""
####
Vitamina Complejo B
####
"""
REQUERIMIENTOS_VITAMINAS_B = {
    "todos": {
        0.5: {
            "rpe": {
                "tiamina": 0.2,
                "riboflavina": 0.3,
                "niacina": 2,
                "vitamina_b6": 0.1,
                "folatos": 52,
                "vitamina_b12": 0.4,
            },
            "rdd": {
                "tiamina": 0.2,
                "riboflavina": 0.3,
                "niacina": 2,
                "vitamina_b6": 0.1,
                "folatos": 52,
                "vitamina_b12": 0.4,
            },
        },

        1: {
            "rpe": {
                "tiamina": 0.3,
                "riboflavina": 0.4,
                "niacina": 4,
                "vitamina_b6": 0.3,
                "folatos": 75,
                "vitamina_b12": 0.5,
            },
            "rdd": {
                "tiamina": 0.3,
                "riboflavina": 0.4,
                "niacina": 4,
                "vitamina_b6": 0.3,
                "folatos": 75,
                "vitamina_b12": 0.5,
            },
        },

        4: {
            "rpe": {
                "tiamina": 0.4,
                "riboflavina": 0.4,
                "niacina": 4,
                "vitamina_b6": 0.4,
                "folatos": 120,
                "vitamina_b12": 0.7,
            },
            "rdd": {
                "tiamina": 0.4,
                "riboflavina": 0.5,
                "niacina": 6,
                "vitamina_b6": 0.5,
                "folatos": 150,
                "vitamina_b12": 0.9,
            },
        },

        7: {
            "rpe": {
                "tiamina": 0.4,
                "riboflavina": 0.4,
                "niacina": 5,
                "vitamina_b6": 0.5,
                "folatos": 140,
                "vitamina_b12": 0.9,
            },
            "rdd": {
                "tiamina": 0.5,
                "riboflavina": 0.5,
                "niacina": 6,
                "vitamina_b6": 0.6,
                "folatos": 170,
                "vitamina_b12": 1.1,
            },
        },

        10: {
            "rpe": {
                "tiamina": 0.5,
                "riboflavina": 0.5,
                "niacina": 6,
                "vitamina_b6": 0.6,
                "folatos": 170,
                "vitamina_b12": 1.1,
            },
            "rdd": {
                "tiamina": 0.6,
                "riboflavina": 0.6,
                "niacina": 8,
                "vitamina_b6": 0.7,
                "folatos": 200,
                "vitamina_b12": 1.3,
            },
        },
    },

    "hombre": {
        12: {
            "rpe": {"tiamina": 0.6, "riboflavina": 0.7, "niacina": 7, "vitamina_b6": 0.7, "folatos": 200, "vitamina_b12": 1.2},
            "rdd": {"tiamina": 0.7, "riboflavina": 0.8, "niacina": 9, "vitamina_b6": 0.8, "folatos": 250, "vitamina_b12": 1.5},
        },
        14: {
            "rpe": {"tiamina": 0.7, "riboflavina": 0.8, "niacina": 9, "vitamina_b6": 0.8, "folatos": 250, "vitamina_b12": 1.5},
            "rdd": {"tiamina": 0.9, "riboflavina": 1.0, "niacina": 11, "vitamina_b6": 1.0, "folatos": 300, "vitamina_b12": 1.8},
        },
        16: {
            "rpe": {"tiamina": 0.9, "riboflavina": 1.0, "niacina": 10, "vitamina_b6": 1.0, "folatos": 280, "vitamina_b12": 1.8},
            "rdd": {"tiamina": 1.0, "riboflavina": 1.2, "niacina": 14, "vitamina_b6": 1.2, "folatos": 350, "vitamina_b12": 2.2},
        },
        18: {
            "rpe": {"tiamina": 1.0, "riboflavina": 1.1, "niacina": 12, "vitamina_b6": 1.1, "folatos": 310, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.2, "riboflavina": 1.3, "niacina": 15, "vitamina_b6": 1.3, "folatos": 375, "vitamina_b12": 2.4},
        },
        30: {
            "rpe": {"tiamina": 1.0, "riboflavina": 1.1, "niacina": 12, "vitamina_b6": 1.1, "folatos": 320, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.2, "riboflavina": 1.3, "niacina": 16, "vitamina_b6": 1.3, "folatos": 400, "vitamina_b12": 2.4},
        },
        65: {
            "rpe": {"tiamina": 1.0, "riboflavina": 1.1, "niacina": 12, "vitamina_b6": 1.1, "folatos": 320, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.2, "riboflavina": 1.3, "niacina": 16, "vitamina_b6": 1.3, "folatos": 400, "vitamina_b12": 2.4},
        },
        float("inf"): {
            "rpe": {"tiamina": 1.0, "riboflavina": 1.1, "niacina": 12, "vitamina_b6": 1.4, "folatos": 320, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.2, "riboflavina": 1.3, "niacina": 16, "vitamina_b6": 1.7, "folatos": 400, "vitamina_b12": 2.4},
        },
    },

    "mujer": {
        12: {
            "rpe": {"tiamina": 0.7, "riboflavina": 0.7, "niacina": 8, "vitamina_b6": 0.8, "folatos": 225, "vitamina_b12": 1.5},
            "rdd": {"tiamina": 0.8, "riboflavina": 0.8, "niacina": 10, "vitamina_b6": 1.0, "folatos": 280, "vitamina_b12": 1.8},
        },
        14: {
            "rpe": {"tiamina": 0.8, "riboflavina": 0.8, "niacina": 10, "vitamina_b6": 1.0, "folatos": 280, "vitamina_b12": 1.5},
            "rdd": {"tiamina": 0.9, "riboflavina": 0.9, "niacina": 13, "vitamina_b6": 1.2, "folatos": 350, "vitamina_b12": 1.8},
        },
        16: {
            "rpe": {"tiamina": 0.9, "riboflavina": 0.9, "niacina": 11, "vitamina_b6": 1.1, "folatos": 310, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.1, "riboflavina": 1.1, "niacina": 14, "vitamina_b6": 1.3, "folatos": 375, "vitamina_b12": 2.4},
        },
        18: {
            "rpe": {"tiamina": 0.9, "riboflavina": 0.9, "niacina": 11, "vitamina_b6": 1.1, "folatos": 325, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.1, "riboflavina": 1.1, "niacina": 15, "vitamina_b6": 1.3, "folatos": 400, "vitamina_b12": 2.4},
        },
        30: {
            "rpe": {"tiamina": 0.9, "riboflavina": 0.9, "niacina": 11, "vitamina_b6": 1.1, "folatos": 320, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.1, "riboflavina": 1.1, "niacina": 14, "vitamina_b6": 1.3, "folatos": 400, "vitamina_b12": 2.4},
        },
        65: {
            "rpe": {"tiamina": 0.9, "riboflavina": 0.9, "niacina": 11, "vitamina_b6": 1.1, "folatos": 320, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.1, "riboflavina": 1.1, "niacina": 14, "vitamina_b6": 1.3, "folatos": 400, "vitamina_b12": 2.4},
        },
        float("inf"): {
            "rpe": {"tiamina": 0.9, "riboflavina": 0.9, "niacina": 11, "vitamina_b6": 1.3, "folatos": 320, "vitamina_b12": 2.0},
            "rdd": {"tiamina": 1.1, "riboflavina": 1.1, "niacina": 14, "vitamina_b6": 1.6, "folatos": 400, "vitamina_b12": 2.4},
        },
    },
}

VITAMINAS_B_EMBARAZO = {
    "rpe": {
        "tiamina": 1.2,
        "riboflavina": 1.2,
        "niacina": 14,
        "vitamina_b6": 1.6,
        "folatos": 520,
        "vitamina_b12": 2.2,
    },
    "rdd": {
        "tiamina": 1.4,
        "riboflavina": 1.4,
        "niacina": 18,
        "vitamina_b6": 1.9,
        "folatos": 600,
        "vitamina_b12": 2.6,
    },
}

VITAMINAS_B_LACTANCIA = {
    "rpe": {
        "tiamina": 1.1,
        "riboflavina": 1.3,
        "niacina": 13,
        "vitamina_b6": 1.7,
        "folatos": 450,
        "vitamina_b12": 2.4,
    },
    "rdd": {
        "tiamina": 1.3,
        "riboflavina": 1.6,
        "niacina": 17,
        "vitamina_b6": 2.0,
        "folatos": 500,
        "vitamina_b12": 2.8,
    },
}
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
        18: 5.0,
        float("inf"):  5.0,
    },
    "mujer": {
        12: 4.0 ,
        14: 4.0,
        18: 5.0,
        float("inf"):  5.0,
    },
}
ACIDO_PANTOTENICO_EMBARAZO = 6.0
ACIDO_PANTOTENICO_LACTANCIA = 7.0