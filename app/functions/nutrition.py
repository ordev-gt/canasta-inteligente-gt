from ..entities.Person import Person

""" height_weight_population = {
    # (edad_min, edad_max, sexo)
    #
    (0, 0.25): { # 0 a 3 meses
        "avg_weight_kg": 4.3,
        "energy__kcalKgDia": 102
    },
    (0.25, 0.5): { # 3 a 6 meses
        "avg_weight_kg": 6.7,
        "energy__kcalKgDia": 82
    },
    (0.5, 0.67): { # 6 a 9 meses
        "avg_weight_kg": 7.9,
        "energy__kcalKgDia": 79
    },
    (0.67, 1): { # 9 a 12 meses
        "avg_weight_kg": 8.8,
        "energy__kcalKgDia": 80
    },
    (1, 2): { # 1 a 2 años
        "avg_weight_kg": 10.6,
        "energy__kcalKgDia": 81
    },
    (2, 3): { 
        "avg_weight_kg": 13,
        "energy__kcalKgDia": 83
    },
    (3, 4): { 
        "avg_weight_kg": 15.2,
        "energy__kcalKgDia": 79
    },
    (4, 5): { 
        "avg_weight_kg": 17.3,
        "energy__kcalKgDia": 76
    },
    (5, 6): { 
        "men":{
            "avg_weight_kg": 18.3,
            "energy__kcalKgDia": 74
        },
        "woman":{
            "avg_weight_kg": 17.7,
            "energy__kcalKgDia": 72
        }
    },
    (6, 7): { 
        "men":{
            "avg_weight_kg": 20.4,
            "energy__kcalKgDia": 73
        },
        "woman":{
            "avg_weight_kg": 19.7,
            "energy__kcalKgDia": 69
        }
    },
    (7, 8): { 
        "men":{
            "avg_weight_kg": 22.6,
            "energy__kcalKgDia": 71
        },
        "woman":{
            "avg_weight_kg": 21.9,
            "energy__kcalKgDia": 67
        }
    },
    (8, 9): { 
        "men":{
            "avg_weight_kg": 25,
            "energy__kcalKgDia": 69
        },
        "woman":{
            "avg_weight_kg": 24.6,
            "energy__kcalKgDia": 64
        }
    },
    (9, 10): { 
        "men":{
            "avg_weight_kg": 27.6,
            "energy__kcalKgDia": 67
        },
        "woman":{
            "avg_weight_kg": 27.6,
            "energy__kcalKgDia": 61
        }
    },
    (10, 11): { 
        "men":{
            "avg_weight_kg": 27.6,
            "energy__kcalKgDia": 67
        },
        "woman":{
            "avg_weight_kg": 27.6,
            "energy__kcalKgDia": 61
        }
    },
      
}
 """
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
            "avg_requirement_g_per_kg": 1.32,
            "safe_reference_g_per_kg": 1.64,
            "safe_mixed_diet_g_per_kg": None,
        },
        0.5: {
            "avg_weight_kg": 6.67,
            "avg_requirement_g_per_kg": 1.06,
            "safe_reference_g_per_kg": 1.25,
            "safe_mixed_diet_g_per_kg": None,
        },
        0.75: {
            "avg_weight_kg": 7.93,
            "avg_requirement_g_per_kg": 1.12,
            "safe_reference_g_per_kg": 1.31,
            "safe_mixed_diet_g_per_kg": 1.76,
        },
        1: {
            "avg_weight_kg": 8.82,
            "avg_requirement_g_per_kg": 1.12,
            "safe_reference_g_per_kg": 1.31,
            "safe_mixed_diet_g_per_kg": 1.76,
        },
        2: {
            "avg_weight_kg": 10.55,
            "avg_requirement_g_per_kg": 0.95,
            "safe_reference_g_per_kg": 1.14,
            "safe_mixed_diet_g_per_kg": 1.54,
        },
        3: {
            "avg_weight_kg": 13.0,
            "avg_requirement_g_per_kg": 0.79,
            "safe_reference_g_per_kg": 0.97,
            "safe_mixed_diet_g_per_kg": 1.31,
        },
        4: {
            "avg_weight_kg": 15.15,
            "avg_requirement_g_per_kg": 0.73,
            "safe_reference_g_per_kg": 0.90,
            "safe_mixed_diet_g_per_kg": 1.21,
        },
        5: {
            "avg_weight_kg": 17.5,
            "avg_requirement_g_per_kg": 0.69,
            "safe_reference_g_per_kg": 0.86,
            "safe_mixed_diet_g_per_kg": 1.16,
        },
    },

    "men": {
        6: {
            "avg_weight_kg": 18.26,
            "avg_requirement_g_per_kg": 0.69,
            "safe_reference_g_per_kg": 0.85,
            "safe_mixed_diet_g_per_kg": 1.14,
        },
        7: {
            "avg_weight_kg": 20.36,
            "avg_requirement_g_per_kg": 0.72,
            "safe_reference_g_per_kg": 0.89,
            "safe_mixed_diet_g_per_kg": 1.20,
        },
        8: {
            "avg_weight_kg": 22.58,
            "avg_requirement_g_per_kg": 0.74,
            "safe_reference_g_per_kg": 0.91,
            "safe_mixed_diet_g_per_kg": 1.23,
        },
        9: {
            "avg_weight_kg": 25.01,
            "avg_requirement_g_per_kg": 0.75,
            "safe_reference_g_per_kg": 0.92,
            "safe_mixed_diet_g_per_kg": 1.24,
        },
        10: {
            "avg_weight_kg": 27.57,
            "avg_requirement_g_per_kg": 0.75,
            "safe_reference_g_per_kg": 0.92,
            "safe_mixed_diet_g_per_kg": 1.24,
        },
        12: {
            "avg_weight_kg": 32,
            "avg_requirement_g_per_kg": 0.75,
            "safe_reference_g_per_kg": 0.91,
            "safe_mixed_diet_g_per_kg": 1.23,
        },
        14: {
            "avg_weight_kg": 41,
            "avg_requirement_g_per_kg": 0.74,
            "safe_reference_g_per_kg": 0.90,
            "safe_mixed_diet_g_per_kg": 1.21,
        },
        16: {
            "avg_weight_kg": 53,
            "avg_requirement_g_per_kg": 0.72,
            "safe_reference_g_per_kg": 0.89,
            "safe_mixed_diet_g_per_kg": 1.19,
        },
        18: {
            "avg_weight_kg": 61,
            "avg_requirement_g_per_kg": 0.71,
            "safe_reference_g_per_kg": 0.87,
            "safe_mixed_diet_g_per_kg": 1.16,
        },
        float("inf"): {
            "avg_weight_kg": 64,
            "avg_requirement_g_per_kg": 0.66,
            "safe_reference_g_per_kg": 0.83,
            "safe_mixed_diet_g_per_kg": 1.12,
        },
    },

    "women": {
        6: {
            "avg_weight_kg": 17.69,
            "avg_requirement_g_per_kg": 0.69,
            "safe_reference_g_per_kg": 0.85,
            "safe_mixed_diet_g_per_kg": 1.14,
        },
        7: {
            "avg_weight_kg": 19.67,
            "avg_requirement_g_per_kg": 0.72,
            "safe_reference_g_per_kg": 0.89,
            "safe_mixed_diet_g_per_kg": 1.20,
        },
        8: {
            "avg_weight_kg": 21.87,
            "avg_requirement_g_per_kg": 0.74,
            "safe_reference_g_per_kg": 0.91,
            "safe_mixed_diet_g_per_kg": 1.23,
        },
        9: {
            "avg_weight_kg": 24.57,
            "avg_requirement_g_per_kg": 0.75,
            "safe_reference_g_per_kg": 0.92,
            "safe_mixed_diet_g_per_kg": 1.24,
        },
        10: {
            "avg_weight_kg": 27.56,
            "avg_requirement_g_per_kg": 0.75,
            "safe_reference_g_per_kg": 0.92,
            "safe_mixed_diet_g_per_kg": 1.24,
        },
        12: {
            "avg_weight_kg": 33,
            "avg_requirement_g_per_kg": 0.74,
            "safe_reference_g_per_kg": 0.91,
            "safe_mixed_diet_g_per_kg": 1.22,
        },
        14: {
            "avg_weight_kg": 42,
            "avg_requirement_g_per_kg": 0.72,
            "safe_reference_g_per_kg": 0.89,
            "safe_mixed_diet_g_per_kg": 1.19,
        },
        16: {
            "avg_weight_kg": 49,
            "avg_requirement_g_per_kg": 0.70,
            "safe_reference_g_per_kg": 0.86,
            "safe_mixed_diet_g_per_kg": 1.16,
        },
        18: {
            "avg_weight_kg": 52,
            "avg_requirement_g_per_kg": 0.68,
            "safe_reference_g_per_kg": 0.84,
            "safe_mixed_diet_g_per_kg": 1.12,
        },
    },
}
def get_tmb(gender: str, age: float):
    equations = TMB[gender]

    for max_age, equation in equations.items():
        if age < max_age:
            return equation

    raise ValueError(f"No se encontró ecuación para edad {age}")

def evaluate_requirements(p: Person) -> dict:
    tmb_formula = get_tmb(p.gender, p.age)
    tmb = tmb_formula(p.weight)

    ree = tmb * p.naf_index if p.naf_index is not None else tmb

    if p.is_pregnant:
        if p.pregnancy_month > 3: # En el primer tremestre no cambia 
            # FAO/WHO/UNU recommendation:
            # trimester 1: no dietary increment
            # trimester 2: +360 kcal/day
            # trimester 3: +475 kcal/day
            ree += 360 if p.pregnancy_month <= 6 else 475 # 360 para segundo trimestre; 475 para tercer trimeste 


    if p.in_lactancy: 
        ree += 505 if p.has_adequate_maternal_energy_stores else 675

    return {
        "tmb": tmb
    }


if __name__ == '__main__':
    # Posibles NAF = low, moderate, intense
    p = Person(25, 'women', 81, 'low', 1.63, True, 5, True, True)
    evaluate_requirements(p)