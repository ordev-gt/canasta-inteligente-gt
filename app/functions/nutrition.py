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

    print(ree)
    return {
        "tmb": tmb
    }


if __name__ == '__main__':
    # Posibles NAF = low, moderate, intense
    p = Person(25, 'men', 81, 'low', 1.70)
    evaluate_requirements(p)