from ..entities.Persona import Persona
from .requerimientos import (
    PESO_LONGITUD_NINAS_0_2, PESO_ALTURA_NINAS_2_5, PESO_ALTURA_NINOS_2_5, PESO_LONGITUD_NINOS_0_2, 
    IMC_ADULTO_MIN, IMC_ADULTO_MAX, IMC_REFERENCIA_INCAP, IMC_OBESIDAD_MIN,
    TMB, ENERGIA_ADICIONAL_EMBARAZDA_SEGUNDO_TRIMESTRE, ENERGIA_ADICIONAL_EMBARAZDA_TERCER_TRIMESTRE,
    REQUERIMIENTOS_PROTEINA, PROTEINA_DE_REFERENCIA_ADICIONAL_EMBARAZO_SEGUNDO_TRIMESTRE,
    PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_SEGUNDO_TRIMESTRE,
    PROTEINA_DE_REFERENCIA_ADICIONAL_EMBARAZO_TERCER_TRIMESTRE,
    PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_TERCER_TRIMESTRE,
    PROTEINA_DE_REFERENCIA_ADICIONAL_LACTANCIA_PRIMER_SEMESTRE,
    PROTEINA_DIETA_MIXTA_ADICIONAL_LACTANCIA_PRIMER_SEMESTRE,
    PROTEINA_DE_REFERENCIA_ADICIONAL_LACTANCIA_SEGUNDO_SEMESTRE,
    PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_SEGUNDO_SEMESTRE,

    RDD_LIPIDOS, RECOMENDACION_MAXIMO_COLESTEROL_MG,REQUERIMIENTOS_CARBOHIDRATOS, KCAL_POR_GRAMO_GRASA, CARBOHIDRATOS_ENERGIA_MIN, 
    CARBOHIDRATOS_ENERGIA_MAX, AZUCARES_REFINADOS_ENERGIA_MAX, KCAL_POR_GRAMO_CARBOHIDRATO,
    REQUERIMIENTOS_VITAMINA_A, IMT_RETINOL, 
    IA_ACIDO_PANTOTENICO, ACIDO_PANTOTENICO_ADICIONAL_EMBARAZO, ACIDO_PANTOTENICO_ADICIONAL_LACTANCIA,
    GRAMOS_DE_FIBRA_POR_1000_KCAL, IMC_EDAD_MESES_NINAS, IMC_EDAD_MESES_NINOS,
    VITAMINA_C_ADICIONAL_EMBARAZO, VITAMINA_C_ADICIONAL_LACTANCIA,  REQUERIMIENTOS_VITAMINA_C,
    REQUERIMIENTOS_VITAMINA_D, IMT_LACTANTES_SUPLEMENTO_VITAMINAD, IMT_NINOS_ADULTOS_SUPLEMENTO_VITAMINAD,
    REQUERIMIENTOS_VITAMINA_E, 
    REQUERIMIENTOS_VITAMINA_K_INFANTES, REQUERIMIENTOS_VITAMINA_K_MCG_POR_KG,
    REQUERIMIENTOS_TIAMINA, REQUERIMIENTO_ADICIONAL_TIAMINA_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_TIAMINA_LACTANCIA,
    REQUERIMIENTO_ADICIONAL_RIBOFLAVINA_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_RIBOFLAVINA_LACTANCIA, REQUERIMIENTOS_RIBOFLAVINA,
    REQUERIMIENTO_ADICIONAL_NIACINA_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_NIACINA_LACTANCIA, REQUERIMIENTOS_NIACINA,
    REQUERIMIENTO_ADICIONAL_VITAMINAB6_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_VITAMINAB6_LACTANCIA, REQUERIMIENTOS_VITAMINAB6, IMT_VITAMINA_B6,
    REQUERIMIENTOS_FOLATOS, REQUERIMIENTO_ADICIONAL_FOLATOS_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_FOLATOS_LACTANCIA, IMT_FOLATO_SINTETICO,
    REQUERIMIENTOS_VITAMINAB12, REQUERIMIENTO_ADICIONAL_VITAMINAB12_EMBARAZO, REQUERIMIENTO_ADICIONAL_VITAMINAB12_LACTANCIA,
    REQUERIMIENTO_ADICIONAL_VITAMINA_A_EMBARAZADAS, REQUERIMIENTO_ADICIONAL_VITAMINA_A_LACTANTES,
    CARBOHIDRATOS_ADICIONALES_EMBARAZADA_ULTIMO_TRIMESTRE, CARBOHIDRATOS_ADICIONALES_LACTANCIA,
    REQUERIMIENTO_ADICIONAL_VITAMINA_E_LACTANTES,
    IMT_VITAMINA_E,
    INGESTA_ADECUADA_CALCIO, IMT_NINOS_Y_ADULTOS_CALCIO,
    REQUERIMIENTO_FOSFORO,
    REQUERIMIENTO_MAGNESIO_INFANTES, REQUERIMIENTO_MAGNESIO_POR_KG, RPE_ADICIONAL_EMBARAZADAS_MAGNESIO,
    REQUERIMIENTOS_HIERRO, REQUERIMIENTO_ADICIONAL_EMBARZADAS_SEGUNDO_TRIMESTRE, REQUERIMIENTO_ADICIONAL_EMBARZADAS_TERCER_TRIMESTRE, REQUERIMIENTO_ADICIONAL_MUJER_EN_LACTANCIA,
    REQUERIMIENTOS_ZINC, REQUERIMIENTO_ADICIONAL_ZINC_EMBARAZADAS,  REQUERIMIENTO_ADICIONAL_ZINC_MUJERES_EN_LACTANCIA
    
    )
from typing import Dict, AnyStr
from abc import ABC, abstractmethod

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

class Requerimiento(ABC):

    @staticmethod
    def calcular_rpe(rdd: float, cv:float):
        """Calcula RPE a partir del RDD, en caso siga una distribucion normal el requerimiento. 
    
        Args:
        rdd (float): Recomendacion dietetica diaria (RDD) 
        cv (float): Coeficiente de variacion del requerimiento para la poblacion. 
        
        Returns:
        float: Requerimiento Promedio Estimado (RPE)
        """
        return rdd / (2 * cv + 1)

    @staticmethod
    def calcular_rdd(rpe: float, cv: float):
        """Calcula RDD a partir del RPE, en caso siga una distribucion normal el requerimiento. 
    
        Args:
        rdd (float): Recomendacion dietetica diaria (RDD) 
        cv (float): Coeficiente de variacion del requerimiento para la poblacion. 
        
        Returns:
        float: Requerimiento Promedio Estimado (RPE)
        """
        return rpe + 2 * (cv * rpe)

    @staticmethod
    @abstractmethod
    def obtener_requerimiento(p: Persona) -> dict:
        pass


class Peso:

    @staticmethod
    def __obtener_referencia_por_longitud(altura_m: float, referencia: dict) -> dict:
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

    @staticmethod
    def __evaluacion_peso_menor_5_con_referencia(p: Persona, referencia: dict, indicador: str) -> dict:

        datos = Peso.__obtener_referencia_por_longitud(p.altura, referencia)

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

    @staticmethod
    def __evaluacion_peso_nino_0_a_2_anos(p: Persona) -> dict: return Peso.__evaluacion_peso_menor_5_con_referencia(p, PESO_LONGITUD_NINOS_0_2, "peso_para_longitud_oms")

    @staticmethod
    def __evaluacion_peso_nina_0_a_2_anos(p: Persona) -> dict: return Peso.__evaluacion_peso_menor_5_con_referencia(p, PESO_LONGITUD_NINAS_0_2, "peso_para_longitud_oms")

    @staticmethod
    def __evaluacion_peso_nino_2_a_5_anos(p: Persona) -> dict: return Peso.__evaluacion_peso_menor_5_con_referencia(p,  PESO_ALTURA_NINOS_2_5,  "peso_para_talla_oms")

    @staticmethod
    def __evaluacion_peso_nina_2_a_5_anos(p: Persona) -> dict: return Peso.__evaluacion_peso_menor_5_con_referencia(p, PESO_ALTURA_NINAS_2_5, "peso_para_talla_oms")

    @staticmethod
    def evaluacion_peso_nino_menor_5(p: Persona) -> dict:

        if p.edad_meses > 60:
            raise ValueError("Esta función solo aplica hasta 60 meses.")

        if p.edad_meses <= 24:
            if p.sexo == "hombre":
                return Peso.__evaluacion_peso_nino_0_a_2_anos(p)

            elif p.sexo == "mujer":
                return Peso.__evaluacion_peso_nina_0_a_2_anos(p)

        else:
            if p.sexo == "hombre":
                return Peso.__evaluacion_peso_nino_2_a_5_anos(p)

            elif p.sexo == "mujer":
                return Peso.__evaluacion_peso_nina_2_a_5_anos(p)

        raise ValueError(f"Sexo no reconocido: {p.sexo}")

    @staticmethod
    def evaluacion_peso_adulto(p: Persona) -> dict:

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

    @staticmethod
    def evaluacion_peso_nino_adolescente(p: Persona) -> dict:
        """
        Evalúa el peso de niños y adolescentes utilizando
        IMC para la edad según la referencia OMS 2007.

        Aplica aproximadamente de 5 a 18 años.
        """

        if p.sexo == "hombre":
            referencia = IMC_EDAD_MESES_NINOS
        elif p.sexo == "mujer":
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

    @staticmethod
    def evaluacion_peso_embarazo(p: Persona) -> dict:

        if p.peso_preembarazo is None:
            raise ValueError("Se requiere el peso previo al embarazo para realizar la evaluación antropométrica.")

        if p.peso_preembarazo <= 0:
            raise ValueError("El peso previo al embarazo debe ser mayor que cero.")

        imc_preembarazo = p.peso_preembarazo / (p.altura ** 2)

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

    @staticmethod
    def evaluacion_peso(p: Persona) -> dict:

        if p.esta_embarazada:
            return Peso.evaluacion_peso_embarazo(p)

        if p.edad_meses <= 60: # Hasta 5 años
            return Peso.evaluacion_peso_nino_menor_5(p)

        if p.edad_meses <= 228: # Hasta 19 años
            return Peso.evaluacion_peso_nino_adolescente(p)

        return Peso.evaluacion_peso_adulto(p)

class Energia:

    @staticmethod
    def obtener_requerimiento(p: Persona):
        if p.peso_para_calculos is None:
            raise AttributeError(f'Persona con nombre: "{p.nombre}", debe definir el peso para calculos para obtener el requerimiento de energia.')
        
        tmb = Energia.obtener_tmb(p)(p.peso_para_calculos)
        ree_base = tmb * p.naf_indice if p.edad > 10 and p.naf_indice is not None else tmb

        ree_adicional = 0

        
        if p.esta_embarazada:
            if p.mes_de_embarazo > 3: # En el primer tremestre no cambia 
                ree_adicional += ENERGIA_ADICIONAL_EMBARAZDA_SEGUNDO_TRIMESTRE if p.mes_de_embarazo <= 6 else ENERGIA_ADICIONAL_EMBARAZDA_TERCER_TRIMESTRE

        if p.esta_en_lactancia: 
            ree_adicional += 505 if p.reservas_de_energia_maternales else 675        


        ree = ree_base + ree_adicional
        return {'ree': ree, 'unidad': 'kCal'}

    @staticmethod
    def obtener_tmb(p: Persona):
        ecuaciones = TMB[p.sexo]

        for edad_maxima, ecuacion in ecuaciones.items():
            if p.edad < edad_maxima:
                return ecuacion

        raise ValueError(f"No se encontró ecuación para edad {p.edad}")

class Proteina:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:
        if p.peso_para_calculos is None:
            raise AttributeError(f'Persona con nombre: "{p.nombre}", debe definir el peso para calculos para obtener el requerimiento de proteina.')

        proteina_de_referencia_adicional = 0
        proteina_dieta_mixta_adicional = 0

        if p.esta_embarazada:
            if 4 <= p.mes_de_embarazo <= 6:
                proteina_de_referencia_adicional += PROTEINA_DE_REFERENCIA_ADICIONAL_EMBARAZO_SEGUNDO_TRIMESTRE
                proteina_dieta_mixta_adicional += PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_SEGUNDO_TRIMESTRE

            elif 7 <= p.mes_de_embarazo <= 9:
                proteina_de_referencia_adicional += PROTEINA_DE_REFERENCIA_ADICIONAL_EMBARAZO_TERCER_TRIMESTRE
                proteina_dieta_mixta_adicional += PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_TERCER_TRIMESTRE


        if p.esta_en_lactancia:
            if p.mes_de_lactancia <= 6:
                proteina_de_referencia_adicional += PROTEINA_DE_REFERENCIA_ADICIONAL_LACTANCIA_PRIMER_SEMESTRE
                proteina_dieta_mixta_adicional += PROTEINA_DIETA_MIXTA_ADICIONAL_LACTANCIA_PRIMER_SEMESTRE
            elif p.mes_de_lactancia <= 12:
                proteina_de_referencia_adicional += PROTEINA_DE_REFERENCIA_ADICIONAL_LACTANCIA_SEGUNDO_SEMESTRE
                proteina_dieta_mixta_adicional += PROTEINA_DIETA_MIXTA_ADICIONAL_EMBARAZO_SEGUNDO_SEMESTRE
        
        requerimientos = REQUERIMIENTOS_PROTEINA["todos"] if p.edad < 5 else REQUERIMIENTOS_PROTEINA[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return {
                    'rpe': requerimiento['rpe_g_por_kg']*p.peso_para_calculos,
                    'rdd_referencia':(requerimiento['rdd_referencia_g_por_kg']*p.peso_para_calculos)+proteina_de_referencia_adicional,
                    'rdd_dieta_mixta':  (requerimiento['rdd_dieta_mixta_g_por_kg']*p.peso_para_calculos)+proteina_dieta_mixta_adicional if requerimiento['rdd_dieta_mixta_g_por_kg'] is not None else None,
                    'unidad': 'g'
                }

        raise ValueError(f"No se encontró requerimiento de proteína para edad {p.edad} y sexo {p.sexo}")

class Lipidos:

    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:

        for edad_maxima, requerimiento in RDD_LIPIDOS.items():
            if p.edad < edad_maxima:
                _requerimiento = requerimiento.copy()
                _requerimiento['unidad'] = 'P/E'
                return _requerimiento
        raise ValueError(f"No se encontró requerimiento de lipidos para edad {p.edad}")   

    @staticmethod
    def obtener_requerimiento_gramos(p: Persona, ree: float):
        requerimiento_pe = Lipidos.obtener_requerimiento(p)
        requerimiento_gramos = {}
        for ag, pe in requerimiento_pe.items():
            if ag != 'unidad':
                if pe is not None:
                    requerimiento_gramos[ag] = pe * ree / KCAL_POR_GRAMO_GRASA
                else:
                    requerimiento_gramos[ag] = None
        requerimiento_gramos['unidad'] = 'g'
        return requerimiento_gramos 
    
    @staticmethod
    def recomendacion_colesterol(p):
        limite = None
        if p.edad >= 2:
            limite = RECOMENDACION_MAXIMO_COLESTEROL_MG
        return {'maximo': limite, 'unidad': 'mg'}

class Carbohidratos:  

    @staticmethod
    def obtener_requerimiento_gramos(p: Persona, ree: float):
        rdd = None
        unidad = 'g'
        if p.edad > 6:
            rdd = {'rdd_min': CARBOHIDRATOS_ENERGIA_MIN * ree / KCAL_POR_GRAMO_CARBOHIDRATO, 'rdd_max': CARBOHIDRATOS_ENERGIA_MAX * ree / KCAL_POR_GRAMO_CARBOHIDRATO } 
        else:
            rdd = {'rdd_min': None, 'rdd_max': None } 

        requerimiento_carbohidratos_adicional = 0
        if p.esta_embarazada:
            if 7 <= p.mes_de_embarazo <= 9:
                requerimiento_carbohidratos_adicional += CARBOHIDRATOS_ADICIONALES_EMBARAZADA_ULTIMO_TRIMESTRE

        if p.esta_en_lactancia:
            requerimiento_carbohidratos_adicional += CARBOHIDRATOS_ADICIONALES_LACTANCIA

        for max_age, requerimiento in REQUERIMIENTOS_CARBOHIDRATOS.items():
            if p.edad<max_age:
                if requerimiento['ia'] is not None:
                    _requerimiento = requerimiento.copy()
                    _requerimiento['unidad'] = unidad
                    return _requerimiento
                else:
                    return {
                        'ia': None,
                        'rpe': requerimiento['rpe'] + requerimiento_carbohidratos_adicional,
                        'rdd_min': rdd['rdd_min'],
                        'rdd_max': rdd['rdd_max'],
                        'unidad': unidad
                    }

        raise ValueError(f"No se encontró requerimiento de carbos para edad {p.edad}")   

    @staticmethod
    def obtener_requerimiento_azucar_gramos(ree: float):
        return {
            'ia': None,
            'rpe': None,
            'rdd': AZUCARES_REFINADOS_ENERGIA_MAX * ree / KCAL_POR_GRAMO_CARBOHIDRATO,
            'unidad': 'g'
        }

    @staticmethod
    def obtener_requerimiento_fibra(p: Persona, ree: float):
        if p.edad >= 1:
            return {
                'ia': None, 
                'rpe': None, 
                'rdd':  (ree / 1000 * GRAMOS_DE_FIBRA_POR_1000_KCAL),
                'unidad': 'g'
            }
        else:
            return {
                'ia': None, 
                'rpe': None, 
                'rdd': None,
                 'unidad': 'g'
            }

class VitaminaA:

    CV = 0.2

    @staticmethod
    def calcular_rdd(rpe: float):
        """
        Aplica para niños, adolescentes y adultos. 

        Usado para embarzadas y lactantes cuyo RPE es calculado en tiempo de ejecucion.
        """
        return rpe + 2 * (VitaminaA.CV * rpe)

    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:
        requerimiento_adicional:int = 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_VITAMINA_A_EMBARAZADAS if p.esta_embarazada else 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_VITAMINA_A_LACTANTES if p.esta_en_lactancia else 0

        requerimientos = REQUERIMIENTOS_VITAMINA_A["todos"] if p.edad < 10 else REQUERIMIENTOS_VITAMINA_A[p.sexo]
        unidad = 'mcg EAR'

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento_individuo = requerimiento.copy()
                    requerimiento_individuo['unidad'] = unidad
                    return requerimiento_individuo
                else:
                    new_requirment = {}
                    new_requirment['unidad'] = unidad
                    if requerimiento['ia'] is not None:
                        # En casos reales inalcanzable, bebe embarazado? Lo dejo por si se expande el sistema y permite aumentar requerimiento del bebe por x o y motivo?
                        new_requirment['ia'] = requerimiento.get('ia') + requerimiento_adicional
                    else:
                        if requerimiento['rpe'] is None:
                            raise KeyError('Requerimiento no tiene RPE requerido para calculo.')

                        new_requirment['rpe'] = requerimiento.get('rpe')
                        new_requirment['rdd'] = VitaminaA.calcular_rdd(requerimiento['rpe']+requerimiento_adicional)
                        return new_requirment
                
        raise ValueError(f"No se encontró requerimiento de vitamina A para edad {p.edad} y sexo {p.sexo}")   

    @staticmethod
    def obtener_retinol_imt(age: float) -> float:
        """
        Corresponde especificamente a la parte de la vitamina de A proveniente del Retinol. 
        """

        for edad_maxima, maximo in IMT_RETINOL.items():
            if age < edad_maxima:
                return {"imt": maximo, 'unidad': 'mcg'}

        raise ValueError(f"No se encontró ingesta máxima tolerable de retinol para edad {age}")

class Tiamina:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:
        requerimiento_adicional:int = 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_TIAMINA_EMBARAZADAS if p.esta_embarazada else 0
        requerimiento_adicional += REQUERIMIENTOS_ADICIONAL_TIAMINA_LACTANCIA if p.esta_en_lactancia else 0

        requerimientos = REQUERIMIENTOS_TIAMINA["todos"] if p.edad < 10 else REQUERIMIENTOS_TIAMINA[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento_individuo = requerimiento.copy()
                    requerimiento_individuo['unidad'] = 'mg'
                    return requerimiento_individuo
                else:
                    new_requirment = {}
                    for idr, value in requerimiento.items():
                        if value is None: 
                            new_requirment[idr] = value
                        else: 
                            new_requirment[idr] = value + requerimiento_adicional
                    new_requirment['unidad'] = 'mg'
                    return new_requirment
                
        raise ValueError(f"No se encontró un requerimiento apropiado de tiamina para el individuo")

class Riboflavina:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:
        requerimiento_adicional:int = 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_RIBOFLAVINA_EMBARAZADAS if p.esta_embarazada else 0
        requerimiento_adicional += REQUERIMIENTOS_ADICIONAL_RIBOFLAVINA_LACTANCIA if p.esta_en_lactancia else 0      

        requerimientos = REQUERIMIENTOS_RIBOFLAVINA["todos"] if p.edad < 10 else REQUERIMIENTOS_RIBOFLAVINA[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento_individuo = requerimiento.copy()
                    requerimiento_individuo['unidad'] = 'mg'
                    return requerimiento_individuo
                else:
                    new_requirment = {}
                    for idr, value in requerimiento.items():
                        if value is None: 
                            new_requirment[idr] = value
                        else: 
                            new_requirment[idr] = value + requerimiento_adicional
                    new_requirment['unidad'] = 'mg'
                    return new_requirment

        raise ValueError(f"No se encontró un requerimiento apropiado de Riboflavina para el individuo")

class Niacina:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:
        requerimiento_adicional: int = 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_NIACINA_EMBARAZADAS if p.esta_embarazada else 0
        requerimiento_adicional += REQUERIMIENTOS_ADICIONAL_NIACINA_LACTANCIA if p.esta_en_lactancia else 0      
        requerimientos = REQUERIMIENTOS_NIACINA["todos"] if p.edad < 10 else REQUERIMIENTOS_NIACINA[p.sexo]
        unidad = 'mg EN'

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento_individuo = requerimiento.copy()
                    requerimiento_individuo['unidad'] = unidad
                    return requerimiento_individuo
                else:
                    new_requirment = {}
                    for idr, value in requerimiento.items():
                        if value is None: 
                            new_requirment[idr] = value
                        else: 
                            new_requirment[idr] = value + requerimiento_adicional
                    new_requirment['unidad'] = unidad
                    return new_requirment

        raise ValueError(f"No se encontró un requerimiento apropiado de Niacina para el individuo")

class VitaminaB6:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:
        requerimiento_adicional: int = 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_VITAMINAB6_EMBARAZADAS if p.esta_embarazada else 0
        requerimiento_adicional += REQUERIMIENTOS_ADICIONAL_VITAMINAB6_LACTANCIA if p.esta_en_lactancia else 0      
        requerimientos = REQUERIMIENTOS_VITAMINAB6["todos"] if p.edad < 10 else REQUERIMIENTOS_VITAMINAB6[p.sexo]
        imt = [imt for edad_maxima, imt in IMT_VITAMINA_B6.items() if p.edad < edad_maxima][0]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento_individuo = requerimiento.copy()
                    requerimiento_individuo['imt'] = imt
                    requerimiento_individuo['unidad'] = 'mg'
                    return requerimiento_individuo
                else:
                    new_requirment = {}
                    for idr, value in requerimiento.items():
                        if value is None: 
                            new_requirment[idr] = value
                        else: 
                            new_requirment[idr] = value + requerimiento_adicional
                    new_requirment['imt'] = imt
                    new_requirment['unidad'] = 'mg'
                    return new_requirment

        raise ValueError(f"No se encontró un requerimiento apropiado de VitaminaB6 para el individuo")

class Folatos:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:
        requerimiento_adicional: int = 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_FOLATOS_EMBARAZADAS if p.esta_embarazada else 0
        requerimiento_adicional += REQUERIMIENTOS_ADICIONAL_FOLATOS_LACTANCIA if p.esta_en_lactancia else 0      
        requerimientos = REQUERIMIENTOS_FOLATOS["todos"] if p.edad < 10 else REQUERIMIENTOS_FOLATOS[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento_individual = requerimiento.copy()
                    requerimiento_individual['unidad'] = 'mcg EFD'
                    return requerimiento_individual
                else:
                    new_requirment = {}
                    for idr, value in requerimiento.items():
                        if value is None: 
                            new_requirment[idr] = value
                        else: 
                            new_requirment[idr] = value + requerimiento_adicional
                    
                    new_requirment['unidad'] = 'mcg EFD'
                    return new_requirment

        raise ValueError(f"No se encontró un requerimiento apropiado de Folato para el individuo")

    @staticmethod
    def obtener_imt_folato_sintetico(p):
        imt = [imt for edad_maxima, imt in IMT_FOLATO_SINTETICO.items() if p.edad < edad_maxima][0]
        return {'imt':imt, 'unidad': 'mcg'}
    
class VitaminaB12:
    @staticmethod
    def obtener_requerimiento(p:Persona):
        requerimiento_adicional: int = 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_VITAMINAB12_EMBARAZO if p.esta_embarazada else 0
        requerimiento_adicional += REQUERIMIENTO_ADICIONAL_VITAMINAB12_LACTANCIA if p.esta_en_lactancia else 0      
        requerimientos = REQUERIMIENTOS_VITAMINAB12["todos"] if p.edad < 10 else REQUERIMIENTOS_VITAMINAB12[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento_individual = requerimiento.copy()
                    requerimiento_individual['unidad'] = 'mcg'
                    return requerimiento_individual
                else:
                    new_requirment = {}
                    for idr, value in requerimiento.items():
                        if value is None: 
                            new_requirment[idr] = value
                        else: 
                            new_requirment[idr] = value + requerimiento_adicional
                    new_requirment['unidad'] = 'mcg'
                    return new_requirment

        raise ValueError(f"No se encontró un requerimiento apropiado de VitaminaB12 para el individuo")

class AcidoPantotenico:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:

        acido_adicional = 0
        if p.esta_en_lactancia:
            acido_adicional += ACIDO_PANTOTENICO_ADICIONAL_LACTANCIA

        if p.esta_embarazada:
            acido_adicional +=  ACIDO_PANTOTENICO_ADICIONAL_EMBARAZO

        requerimientos = IA_ACIDO_PANTOTENICO["todos"] if p.edad < 10 else IA_ACIDO_PANTOTENICO[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return {'ia': requerimiento, 'rpe': None, 'rdd': None, 'unidad': 'mg'}

        raise ValueError(f"No se encontraron requerimientos de ácido pantoténico {p.edad} y sexo {p.sexo}")

class VitaminaC:
    CV = 0.1
    @staticmethod
    def calcular_rpe(rdd: float):
        """
        Tabla del Recomendaciones no incluye RPE para la mayoria de los casos, es necesario calcularlo indicanco 
        """
        return rdd / (2 * VitaminaC.CV + 1)

    @staticmethod
    def calcular_rdd(rpe: float):
        """
        Tabla del Recomendaciones no incluye RPE para la mayoria de los casos, es necesario calcularlo indicanco 
        """
        return rpe + 2 * (VitaminaC.CV * rpe)
    
    @staticmethod
    def preprocesamiento_requerimientos_rpe_apartir_de_rdd() -> Dict[AnyStr, Dict]:
        requerimiento_preprocesados = {}
        for sexo, requerimiento in REQUERIMIENTOS_VITAMINA_C.items():
            requerimiento_preprocesados[sexo] = {}
            for edad_maxima, idrs in requerimiento.items():
                if idrs['ia'] is not None:
                    requerimiento_preprocesados[sexo][edad_maxima] = idrs.copy()
                elif idrs['rdd'] is not None:
                    if idrs['rpe'] is None:
                        _idrs = idrs.copy()
                        _idrs['rpe'] = VitaminaC.calcular_rpe(idrs['rdd'])
                        requerimiento_preprocesados[sexo][edad_maxima] = _idrs
                    else:
                        requerimiento_preprocesados[sexo][edad_maxima] = idrs.copy()
                else:
                    raise ValueError('No existe recomendacion valida')
        
        return requerimiento_preprocesados

    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:

        requerimientos_vitamina_c = VitaminaC.preprocesamiento_requerimientos_rpe_apartir_de_rdd()
        unidad = 'mg'
        requerimiento_adicional = 0

        if p.esta_en_lactancia:
            requerimiento_adicional += VITAMINA_C_ADICIONAL_LACTANCIA

        if p.esta_embarazada:
            requerimiento_adicional += VITAMINA_C_ADICIONAL_EMBARAZO

        requerimientos = requerimientos_vitamina_c["todos"] if p.edad < 10 else requerimientos_vitamina_c[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    _requerimiento = requerimiento.copy()
                    _requerimiento['unidad'] = unidad
                    return _requerimiento
                else:
                    if requerimiento['rpe'] is None:
                        raise ValueError('rpe debe estar definido para personas con requerimientos adiiconales (embarzadas y lactantes)')
                    _requerimiento = requerimiento.copy()
                    _rpe =  _requerimiento['rpe'] + requerimiento_adicional
                    _rdd = VitaminaC.calcular_rdd(_rpe)
                    _requerimiento['rpe'] = _rpe
                    _requerimiento['rdd'] = _rdd
                    _requerimiento['unidad'] = unidad
                    return _requerimiento

        raise ValueError(f"No se encontró requerimiento de vitamina C para edad {p.edad} y sexo {p.sexo}")

class VitaminaD:

    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict: 
        unidad = 'mcg'
        for maximo_edad, requerimiento in REQUERIMIENTOS_VITAMINA_D.items():
            if p.edad < maximo_edad:
                _requerimiento = requerimiento.copy()
                _requerimiento['unidad'] = unidad
                return _requerimiento

    @staticmethod
    def obtener_imt(p: Persona):
        unidad = 'mcg'

        if p.edad < 1:
            return {'imt': IMT_LACTANTES_SUPLEMENTO_VITAMINAD, 'unidad':unidad }


        return {'imt': IMT_NINOS_ADULTOS_SUPLEMENTO_VITAMINAD, 'unidad':unidad } # niños y adultos
            
class VitaminaE:

    CV = 0.10

    def calcular_rpe(rdd: float):
        """
        Tabla del Recomendaciones no incluye RPE para la mayoria de los casos, es necesario calcularlo indicanco 
        """
        return rdd / (2 * VitaminaE.CV + 1)

    @staticmethod
    def calcular_rdd(rpe: float):
        """
        Tabla del Recomendaciones no incluye RPE para la mayoria de los casos, es necesario calcularlo indicanco 
        """
        return rpe + 2 * (VitaminaE.CV * rpe)

    @staticmethod
    def preprocesamiento_requerimientos_rpe_apartir_de_rdd() -> Dict[AnyStr, Dict]:
        requerimiento_preprocesados = {}
        for sexo, requerimiento in REQUERIMIENTOS_VITAMINA_E.items():
            requerimiento_preprocesados[sexo] = {}
            for edad_maxima, idrs in requerimiento.items():
                if idrs['ia'] is not None:
                    requerimiento_preprocesados[sexo][edad_maxima] = idrs.copy()
                elif idrs['rdd'] is not None:
                    if idrs['rpe'] is None:
                        _idrs = idrs.copy()
                        _idrs['rpe'] = VitaminaE.calcular_rpe(idrs['rdd'])
                        requerimiento_preprocesados[sexo][edad_maxima] = _idrs
                    else:
                        requerimiento_preprocesados[sexo][edad_maxima] = idrs.copy()
                else:
                    raise ValueError('No existe recomendacion valida')
        
        return requerimiento_preprocesados

    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:
        unidad = 'mg alfa-tocoferol'
        requerimientos_vitamina_c = VitaminaE.preprocesamiento_requerimientos_rpe_apartir_de_rdd()
        requerimiento_adicional = REQUERIMIENTO_ADICIONAL_VITAMINA_E_LACTANTES if p.esta_en_lactancia else 0

        requerimientos = requerimientos_vitamina_c["todos"] if p.edad < 10 else requerimientos_vitamina_c[p.sexo]
        _imt = VitaminaE.obtener_imt(p)
        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    _requerimiento = requerimiento.copy()
                    _requerimiento['imt'] = _imt['imt']
                    _requerimiento['unidad'] = unidad

                    return _requerimiento 
                else:
                    if requerimiento['rpe'] is None:
                        raise ValueError('rpe debe estar definido para personas con requerimientos adiiconales (embarzadas y lactantes)')
                    _requerimiento = requerimiento.copy()
                    _rpe =  _requerimiento['rpe'] + requerimiento_adicional
                    _rdd = VitaminaE.calcular_rdd(_rpe)
                    _requerimiento['rpe'] = _rpe
                    _requerimiento['rdd'] = _rdd
                    _requerimiento['imt'] = _imt['imt']
                    _requerimiento['unidad'] = unidad
                    return _requerimiento

        raise ValueError(f"No se encontró requerimiento de vitamina C para edad {p.edad} y sexo {p.sexo}")
    @staticmethod
    def obtener_imt(p:Persona):
        unidad = 'mg alfa-tocoferol'
        for edad_max, imt in IMT_VITAMINA_E.items():
            if p.edad < edad_max:
                return {"imt": imt, 'unidad': unidad}

class VitaminaK:

    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:
        unidad = 'mcg'

        if p.edad < 0.5:
            return {'ia':REQUERIMIENTOS_VITAMINA_K_INFANTES[0.5], 'rpe': None, 'rdd': None, 'unidad': unidad}
        if p.edad < 1:
            return {'ia':REQUERIMIENTOS_VITAMINA_K_INFANTES[1], 'rpe': None, 'rdd': None, 'unidad': unidad}

        return {'ia':REQUERIMIENTOS_VITAMINA_K_MCG_POR_KG*p.peso_para_calculos, 'rpe': None, 'rdd': None, 'unidad': unidad}

class Calcio:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:
        unidad = 'mg'
        for max_age, requerimiento in INGESTA_ADECUADA_CALCIO.items(): 
            if p.edad < max_age:
                return {'ia': requerimiento, 'imt':IMT_NINOS_Y_ADULTOS_CALCIO, 'rpe: None, ''rdd': None,'unidad': unidad }
        raise ValueError(f'No se encontro requerimiento de calcio para edad {p.edad}')

class Fosforo:
    CV = 0.1 # quizas sirve en el futuro
    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:
        unidad = 'mg'
        for max_age, requerimiento in REQUERIMIENTO_FOSFORO.items():
            if p.edad < max_age:
                _requerimiento = requerimiento.copy()
                _requerimiento = _requerimiento | {'unidad': unidad}
                return _requerimiento
        raise ValueError(f'No se encontro requerimiento de fosforo para edad {p.edad}')

class Magensio:
    CV = 0.1

    @staticmethod
    def calcular_rdd(rpe: float):
        """
        Tabla del Recomendaciones no incluye RPE para la mayoria de los casos, es necesario calcularlo indicanco 
        """
        return rpe + 2 * (Magensio.CV * rpe)

    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:
        unidad = 'mg'
        if p.edad < 1:
            _requerimiento = REQUERIMIENTO_MAGNESIO_INFANTES[0.5].copy()if p.edad < 0.5 else REQUERIMIENTO_MAGNESIO_INFANTES[1].copy()
            return _requerimiento | {'unidad': unidad}

        requerimiento_adicional = RPE_ADICIONAL_EMBARAZADAS_MAGNESIO if p.esta_embarazada else 0

        for max_age, requerimiento in REQUERIMIENTO_MAGNESIO_POR_KG.items():
            if p.edad < max_age:
                rpe  = (requerimiento['rpe_por_kg'] * p.peso_para_calculos) + requerimiento_adicional
                rdd = Magensio.calcular_rdd(rpe)
                return {'ia': None, 'rpe': rpe, 'rdd': rdd, 'unidad': unidad}

class Hierro:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:
        unidad = 'mg'
        requerimiento_adicional = 0
        if p.esta_embarazada:
            if p.mes_de_embarazo > 3:
                requerimiento_adicional += REQUERIMIENTO_ADICIONAL_EMBARZADAS_SEGUNDO_TRIMESTRE if p.mes_de_embarazo < 6 else REQUERIMIENTO_ADICIONAL_EMBARZADAS_TERCER_TRIMESTRE

        if p.esta_en_lactancia:
            requerimiento_adicional += REQUERIMIENTO_ADICIONAL_MUJER_EN_LACTANCIA

        requerimientos = REQUERIMIENTOS_HIERRO["todos"] if p.edad < 9 else REQUERIMIENTOS_HIERRO[p.sexo]

        for max_age, requerimiento in requerimientos.items():
            if p.edad < max_age:
                if requerimiento_adicional == 0:
                    return requerimiento | {'unidad': unidad}
                else: 
                    _requerimiento = {}
                    for biodisponibilidad, i_requerimiento in requerimiento.items():
                        i_requerimiento_modif_req_adicional = i_requerimiento.copy()
                        i_requerimiento_modif_req_adicional['rpe'] = requerimiento_adicional + i_requerimiento_modif_req_adicional.get('rpe') 
                        i_requerimiento_modif_req_adicional['rdd'] = requerimiento_adicional + i_requerimiento_modif_req_adicional.get('rdd') 
                        _requerimiento[biodisponibilidad] = i_requerimiento_modif_req_adicional.copy()
                    return _requerimiento | {'unidad': unidad}
        raise ValueError(f'No se encontro requerimiento de Hierro para edad {p.edad}')

class Zinc(Requerimiento):
    CV = 0.1

    def obtener_requerimiento(self, p: Persona):
        unidad = 'mg'
        requerimiento_adicional = 0
        if p.esta_embarazada:
                requerimiento_adicional += REQUERIMIENTO_ADICIONAL_ZINC_EMBARAZADAS

        if p.esta_en_lactancia:
            requerimiento_adicional += REQUERIMIENTO_ADICIONAL_ZINC_MUJERES_EN_LACTANCIA

        requerimientos = REQUERIMIENTOS_ZINC["todos"] if p.edad < 9 else REQUERIMIENTOS_ZINC[p.sexo]

        for max_age, requerimiento in requerimientos.items():
            if p.edad < max_age:
                if requerimiento_adicional == 0:
                    return requerimiento | {'unidad': unidad}
                else: 
                    _requerimiento = {}
                    for biodisponibilidad, i_requerimiento in requerimiento.items():
                        i_requerimiento_modif_req_adicional = i_requerimiento.copy()
                        rpe: float = requerimiento_adicional + i_requerimiento_modif_req_adicional.get('rpe') 
                        i_requerimiento_modif_req_adicional['rpe'] = rpe
                        i_requerimiento_modif_req_adicional['rdd'] = self.calcular_rdd(rpe, Zinc.CV)
                        _requerimiento[biodisponibilidad] = i_requerimiento_modif_req_adicional.copy()
                    return _requerimiento | {'unidad': unidad}
        raise ValueError(f'No se encontro requerimiento de Hierro para edad {p.edad}')

def evaluacion_de_requerimientos_diarios(p: Persona) -> dict:

    evaluacion_peso_resultado = Peso.evaluacion_peso(p)
    p.peso_para_calculos = evaluacion_peso_resultado["peso_para_calculos"]


    """
    Energia
    """
    recomendacion_energia = Energia.obtener_requerimiento(p)
    ree =  recomendacion_energia['ree']


    """
    Proteina
    """
    requerimiento_proteina = Proteina.obtener_requerimiento(p)

    """
    Carbohidratos, azucar y fibra dietetica
    """
    requerimiento_carbohidratos = Carbohidratos.obtener_requerimiento_gramos(p, ree)
    maximo_azucar = Carbohidratos.obtener_requerimiento_azucar_gramos(ree)
    recomendacion_fibra = Carbohidratos.obtener_requerimiento_fibra(p, ree)

    """
    Lípidos
    """

    requerimiento_lipidos = Lipidos.obtener_requerimiento_gramos(p, ree)
    maximo_colesterol = Lipidos.recomendacion_colesterol(p)
    """
    Vitamina A
    """
    requerimiento_vitamina_a = VitaminaA.obtener_requerimiento(p)
    imt_retinol = VitaminaA.obtener_retinol_imt(p.edad)

    """
    Tiamina
    """
    requerimiento_tiamina = Tiamina.obtener_requerimiento(p)
    """
    Riboflavina
    """
    requerimiento_riboflavina = Riboflavina.obtener_requerimiento(p)
    """
    Niacina
    """
    requerimiento_niacina = Niacina.obtener_requerimiento(p)
    """
    Vitamina B6
    """
    requerimiento_vitaminab6 = VitaminaB6.obtener_requerimiento(p)
    """
    Folatos
    """
    requerimiento_folatos = Folatos.obtener_requerimiento(p)
    imt_folato_sintetico = Folatos.obtener_imt_folato_sintetico(p)
    """
    Vitamina B12
    """
    requerimientos_vitaminab12 = VitaminaB12.obtener_requerimiento(p)
    """
    Acido Pantotenico
    """
    requerimiento_acido_pantotenico = AcidoPantotenico.obtener_requerimiento(p)

    """
    Vitamina C
    """
    requerimiento_vitamina_c = VitaminaC.obtener_requerimiento(p)

    """
    Vitamina D
    """
    requerimiento_e_imt_vitamina_d = VitaminaD.obtener_requerimiento(p) | VitaminaD.obtener_imt(p) 

    """
    Vitamina E
    """
    requerimiento_vitamina_e = VitaminaE.obtener_requerimiento(p)

    """
    Vitamina K
    """
    requerimiento_vitamina_k = VitaminaK.obtener_requerimiento(p)
    """
    Calcio
    """
    requerimiento_calcio = Calcio.obtener_requerimiento(p)
    """
    Fosforo
    """
    requerimiento_fosforo = Fosforo.obtener_requerimiento(p)
    """
    Magnesio
    """
    requerimiento_magnesio = Magensio.obtener_requerimiento(p)
    """
    Hierro
    """
    requerimiento_hierro = Hierro.obtener_requerimiento(p)
    """
    Zinc
    """
    requerimiento_zinc = Zinc().obtener_requerimiento(p)


    """
    Estandarizacion de Vitaminas pendientes:

    Minerales pendientes:
    - Zinc
    - Cobre
    - Selenio

    Electrolitos
    - Sodio
    - Potasio 
    """

    return {
        "energia": recomendacion_energia,
        "proteina": requerimiento_proteina,
        "carbohidratos": requerimiento_carbohidratos,
        'azucar': maximo_azucar,
        "fibra": recomendacion_fibra,
        "lipidos": requerimiento_lipidos,
        'colesterol': maximo_colesterol,
        "micronutrientes": {
            "vitamina_a": requerimiento_vitamina_a,
            "retinol": imt_retinol,

            "tiamina": requerimiento_tiamina,
            "riboflavina": requerimiento_riboflavina,
            "niacina": requerimiento_niacina,
            "vitamina_b6": requerimiento_vitaminab6,

            "folatos": requerimiento_folatos,
            "folato_sintetico":imt_folato_sintetico,

            "vitamina_b12": requerimientos_vitaminab12,
            "acido_pantotenico": requerimiento_acido_pantotenico,
            "vitamina_c": requerimiento_vitamina_c,
            "vitamina_d": requerimiento_e_imt_vitamina_d,

            "vitamina_e": requerimiento_vitamina_e,

            "vitamina_k": requerimiento_vitamina_k,
        },
        "minerales": {
            'calcio': requerimiento_calcio,
            'fosforo': requerimiento_fosforo,
            'magnesio': requerimiento_magnesio,
            'hierro': requerimiento_hierro,
            'zinc': requerimiento_zinc,

        }
        
    }

