from ..entities.Persona import Persona
from .requerimientos import (
    PESO_LONGITUD_NINAS_0_2, PESO_ALTURA_NINAS_2_5, PESO_ALTURA_NINOS_2_5, PESO_LONGITUD_NINOS_0_2, 
    IMC_ADULTO_MIN, IMC_ADULTO_MAX, IMC_REFERENCIA_INCAP, IMC_OBESIDAD_MIN,
    TMB, REQUERIMIENTOS_PROTEINA,
    REQUERIMIENTOS_LIPIDOS, REQUERIMIENTOS_CARBOHIDRATOS, KCAL_POR_GRAMO_GRASA, CARBOHIDRATOS_ENERGIA_MIN, 
    CARBOHIDRATOS_ENERGIA_MAX, AZUCARES_REFINADOS_ENERGIA_MAX, KCAL_POR_GRAMO_CARBOHIDRATO,
    VITAMINA_A_EMBARAZO, VITAMINA_A_LACTANCIA, REQUERIMIENTOS_VITAMINA_A, IMT_RETINOL, 
    VITAMINAS_B_EMBARAZO, VITAMINAS_B_LACTANCIA, REQUERIMIENTOS_VITAMINAS_B,
    IA_ACIDO_PANTOTENICO, ACIDO_PANTOTENICO_EMBARAZO, ACIDO_PANTOTENICO_LACTANCIA,
    GRAMOS_DE_FIBRA_POR_1000_KCAL, IMC_EDAD_MESES_NINAS, IMC_EDAD_MESES_NINOS,
    VITAMINA_C_EMBARAZO, VITAMINA_C_LACTANCIA,  REQUERIMIENTOS_VITAMINA_C,
    IA_VITAMINA_D, VITAMINA_D_EMBARAZO, VITAMINA_D_LACTANCIA, 
    REQUERIMIENTOS_VITAMINA_E, VITAMINA_E_EMBARAZO, VITAMINA_E_LACTANCIA, 
    REQUERIMIENTOS_VITAMINA_K, VITAMINA_K_EMBARAZO, VITAMINA_K_LACTANCIA,
    REQUERIMIENTOS_TIAMINA, REQUERIMIENTO_ADICIONAL_TIAMINA_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_TIAMINA_LACTANCIA,
    REQUERIMIENTO_ADICIONAL_RIBOFLAVINA_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_RIBOFLAVINA_LACTANCIA, REQUERIMIENTOS_RIBOFLAVINA,
    REQUERIMIENTO_ADICIONAL_NIACINA_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_NIACINA_LACTANCIA, REQUERIMIENTOS_NIACINA,
    REQUERIMIENTO_ADICIONAL_VITAMINAB6_EMBARAZADAS, REQUERIMIENTOS_ADICIONAL_VITAMINAB6_LACTANCIA, REQUERIMIENTOS_VITAMINAB6, IMT_VITAMINA_B6
    
    )


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
    def obtener_tmb(sexo: str, edad: float):
        ecuaciones = TMB[sexo]

        for edad_maxima, ecuacion in ecuaciones.items():
            if edad < edad_maxima:
                return ecuacion

        raise ValueError(f"No se encontró ecuación para edad {edad}")


class Proteina:
    @staticmethod
    def obtener_requerimiento(sexo: str, edad: float) -> dict:
        # De 0 a < 5 años no hay diferenciación por sexo
        if edad < 5:
            requerimientos = REQUERIMIENTOS_PROTEINA["todos"]
        else:
            requerimientos = REQUERIMIENTOS_PROTEINA[sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if edad < edad_maxima:
                return requerimiento

        raise ValueError(f"No se encontró requerimiento de proteína para edad {edad} y sexo {sexo}")


class Lipidos:

    @staticmethod
    def obtener_requerimiento(edad: float) -> dict:
        for edad_maxima, requerimiento in REQUERIMIENTOS_LIPIDOS.items():
            if edad < edad_maxima:
                return requerimiento
        raise ValueError(f"No se encontró requerimiento de lipidos para edad {edad}")   

    @staticmethod
    def porcentaje_energia_a_gramos(energia: float, porcentaje: float | None) -> float | None:
        if porcentaje is None:
            return None

        return (energia * porcentaje / KCAL_POR_GRAMO_GRASA)


class Carbohidratos:
    @staticmethod
    def obtener_requerimiento(edad: float) -> dict:
        for edad_maxima, requerimiento in REQUERIMIENTOS_CARBOHIDRATOS.items():
            if edad < edad_maxima:
                return requerimiento

        raise ValueError(f"No se encontró requerimiento de carbohidratos para edad {edad}")   


class VitaminaA:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:

        if p.esta_en_lactancia:
            return VITAMINA_A_LACTANCIA

        if p.esta_embarazada:
            return VITAMINA_A_EMBARAZO

        if p.edad < 10:
            requerimientos = REQUERIMIENTOS_VITAMINA_A["todos"]
        else:
            requerimientos = REQUERIMIENTOS_VITAMINA_A[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return requerimiento

        raise ValueError(f"No se encontró requerimiento de vitamina A para edad {p.edad} y sexo {p.sexo}")   

    @staticmethod
    def obtener_imt(age: float) -> float:
        """
        Corresponde especificamente a la parte de la vitamina de A proveniente del Retinol. 
        """

        for edad_maxima, maximo in IMT_RETINOL.items():
            if age < edad_maxima:
                return maximo

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
                    requerimiento['unidad'] = 'mg'
                    return requerimiento
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
                    requerimiento['unidad'] = 'mg'
                    return requerimiento
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

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                if requerimiento_adicional == 0:
                    requerimiento['unidad'] = 'mg'
                    return requerimiento
                else:
                    new_requirment = {}
                    for idr, value in requerimiento.items():
                        if value is None: 
                            new_requirment[idr] = value
                        else: 
                            new_requirment[idr] = value + requerimiento_adicional
                    new_requirment['unidad'] = 'mg'
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
                    requerimiento['imt'] = imt
                    requerimiento['unidad'] = 'mg'
                    return requerimiento
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

class VitaminasComplejoB:
    @staticmethod
    def obtener_requerimiento_vitaminas_b(p: Persona) -> dict:
        if p.esta_en_lactancia:
            return VITAMINAS_B_LACTANCIA

        if p.esta_embarazada:
            return VITAMINAS_B_EMBARAZO

        if p.edad < 10:
            requerimientos = REQUERIMIENTOS_VITAMINAS_B["todos"]
        else:
            requerimientos = REQUERIMIENTOS_VITAMINAS_B[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return requerimiento

        raise ValueError(f"No se encontraron requerimientos de vitaminas B para edad {p.edad} y sexo {p.sexo}")

class AcidoPantotenico:
    @staticmethod
    def obtener_requerimiento(p: Persona) -> dict:

        if p.esta_en_lactancia:
            return ACIDO_PANTOTENICO_LACTANCIA

        if p.esta_embarazada:
            return ACIDO_PANTOTENICO_EMBARAZO

        if p.edad < 10:
            requerimientos = IA_ACIDO_PANTOTENICO["todos"]
        else:
            requerimientos = IA_ACIDO_PANTOTENICO[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return requerimiento

        raise ValueError(f"No se encontraron requerimientos de ácido pantoténico {p.edad} y sexo {p.sexo}")


class VitaminaC:

    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:

        if p.esta_en_lactancia:
            return VITAMINA_C_LACTANCIA

        if p.esta_embarazada:
            return VITAMINA_C_EMBARAZO

        if p.edad < 10:
            requerimientos = REQUERIMIENTOS_VITAMINA_C["todos"]
        else:
            requerimientos = REQUERIMIENTOS_VITAMINA_C[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return requerimiento

        raise ValueError(
            f"No se encontró requerimiento de vitamina C "
            f"para edad {p.edad} y sexo {p.sexo}"
        )

class VitaminaD:

    @staticmethod
    def obtener_ia(p: Persona) -> float:

        if p.esta_embarazada or p.esta_en_lactancia:
            return 5

        if p.edad < 50:
            return 5

        if p.edad <= 70:
            return 10

        return 15

    @staticmethod
    def obtener_limite_superior(p: Persona) -> float:
        return 25 if p.edad < 1 else 50

    @staticmethod
    def evaluar(p: Persona) -> dict:

        ia = VitaminaD.obtener_ia(p)
        maximo = VitaminaD.obtener_limite_superior(p)

        # INCAP mantiene explícitamente la recomendación
        # dietética en niños pequeños y adultos mayores.
        requiere_fuente_dietetica = (
            p.edad < 4
            or p.edad > 50
            or p.esta_embarazada
            or p.esta_en_lactancia
            or not p.exposicion_solar_suficiente
        )

        return {
            "ia": ia,
            "minimo_efectivo": ia if requiere_fuente_dietetica else None,
            "idr": "ingesta_adecuada",
            "requiere_fuente_dietetica": requiere_fuente_dietetica,
            "exposicion_solar_suficiente": p.exposicion_solar_suficiente,
            "maximo": maximo,
            "unidad": "ug",
        }
class VitaminaE:

    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:

        if p.esta_en_lactancia:
            return VITAMINA_E_LACTANCIA

        if p.esta_embarazada:
            return VITAMINA_E_EMBARAZO

        if p.edad < 10:
            requerimientos = REQUERIMIENTOS_VITAMINA_E["todos"]
        else:
            requerimientos = REQUERIMIENTOS_VITAMINA_E[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return requerimiento

        raise ValueError(
            f"No se encontró requerimiento de vitamina E "
            f"para edad {p.edad} y sexo {p.sexo}"
        )


class VitaminaK:

    @staticmethod
    def obtener_requerimiento(p: Persona) -> float:

        if p.esta_en_lactancia:
            return VITAMINA_K_LACTANCIA

        if p.esta_embarazada:
            return VITAMINA_K_EMBARAZO

        if p.edad < 10:
            requerimientos = REQUERIMIENTOS_VITAMINA_K["todos"]
        else:
            requerimientos = REQUERIMIENTOS_VITAMINA_K[p.sexo]

        for edad_maxima, requerimiento in requerimientos.items():
            if p.edad < edad_maxima:
                return requerimiento

        raise ValueError(
            f"No se encontró requerimiento de vitamina K "
            f"para edad {p.edad} y sexo {p.sexo}"
        )


def evaluacion_de_requerimientos_diarios(p: Persona) -> dict:

    evaluacion_peso_resultado = Peso.evaluacion_peso(p)

    peso_para_calculos = evaluacion_peso_resultado["peso_para_calculos"]

    tmb_formula = Energia.obtener_tmb(p.sexo, p.edad)
    tmb = tmb_formula(peso_para_calculos)

    # REE = Requerimiento Estimado de Energía (INCAP),
    
    ree = tmb * p.naf_indice if p.edad > 10 and p.naf_indice is not None else tmb


    """
    Energia
    """

    if p.esta_embarazada:
        if p.mes_de_embarazo > 3: # En el primer tremestre no cambia 
            # Recomendación FAO/OMS/UNU:
            # primer trimestre: sin incremento dietético
            # segundo trimestre: +360 kcal/día
            # tercer trimestre: +475 kcal/día
            ree += 360 if p.mes_de_embarazo <= 6 else 475 # 360 para segundo trimestre; 475 para tercer trimeste 


    if p.esta_en_lactancia: 
        ree += 505 if p.reservas_de_energia_maternales else 675


    """
    Proteina
    """
    requerimiento_proteina = Proteina.obtener_requerimiento(p.sexo, p.edad)

    proteina_embarazo = 0

    if p.esta_embarazada:
        if 4 <= p.mes_de_embarazo <= 6:
            proteina_embarazo = 13
        elif 7 <= p.mes_de_embarazo <= 9:
            proteina_embarazo = 42

    proteina_lactancia = 0

    if p.esta_en_lactancia:
        if p.mes_de_lactancia <= 6:
            proteina_lactancia = 26
        elif p.mes_de_lactancia <= 12:
            proteina_lactancia = 18


    """
    Carbohidratos
    """


    requerimiento_carbohidratos = Carbohidratos.obtener_requerimiento(p.edad)
    carbohidratos_minimos = requerimiento_carbohidratos["gramos_por_dia"]
    azucares_refinados_max = None

    if requerimiento_carbohidratos["tipo"] == "rpe":
        if p.esta_embarazada:
            carbohidratos_minimos += 33

        if p.esta_en_lactancia:
            carbohidratos_minimos += 60

    if p.edad >= 1:
        carbohydrate_energy_min = (ree * CARBOHIDRATOS_ENERGIA_MIN / KCAL_POR_GRAMO_CARBOHIDRATO )
        azucares_refinados_max = (ree * AZUCARES_REFINADOS_ENERGIA_MAX / KCAL_POR_GRAMO_CARBOHIDRATO)
        carbohydrate_energy_max = (ree * CARBOHIDRATOS_ENERGIA_MAX / KCAL_POR_GRAMO_CARBOHIDRATO )

        carbohydrate_effective_min = max(carbohidratos_minimos, carbohydrate_energy_min )

    else:
        carbohydrate_energy_min = None
        carbohydrate_energy_max = None
        carbohydrate_effective_min = carbohidratos_minimos

    """
    Fibra Dietetica
    """
    
    fiber_requirement = None

    if p.edad >= 1:
        fiber_requirement = (ree / 1000 * GRAMOS_DE_FIBRA_POR_1000_KCAL)

    """
    Lípidos
    """

    requerimiento_lipidos = Lipidos.obtener_requerimiento(p.edad)

    grasa_total_min = Lipidos.porcentaje_energia_a_gramos(ree, requerimiento_lipidos["grasa_total_porcentaje_min"])
    grasa_total_max = Lipidos.porcentaje_energia_a_gramos(ree, requerimiento_lipidos["grasa_total_porcentaje_max"])
    saturados_max = Lipidos.porcentaje_energia_a_gramos(ree, requerimiento_lipidos["saturados_porcentaje_max"])
    poliinsaturados_min = Lipidos.porcentaje_energia_a_gramos(ree, requerimiento_lipidos["poliinsaturados_porcentaje_min"])
    poliinsaturados_max = Lipidos.porcentaje_energia_a_gramos(ree, requerimiento_lipidos["poliinsaturados_porcentaje_max"])
    colesterol_max = requerimiento_lipidos["colesterol_max_mg"]
    """
    Vitamina A
    """

    requerimiento_vitamina_a = VitaminaA.obtener_requerimiento(p)

    imt_vitamina_a = VitaminaA.obtener_imt(p.edad)

    if requerimiento_vitamina_a["rdd"] is not None:
        minimo_vitamina_a = requerimiento_vitamina_a["rdd"]
        tipo_referencia_vitamina_a = "rdd"
    else:
        minimo_vitamina_a = requerimiento_vitamina_a["ia"]
        tipo_referencia_vitamina_a = "ingesta_adecuada"

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
    Vitaminas del complejo B
    """

    requerimiento_vitaminas_b = VitaminasComplejoB.obtener_requerimiento_vitaminas_b(p)

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
    evaluacion_vitamina_d = VitaminaD.evaluar(p)

    """
    Vitamina E
    """
    requerimiento_vitamina_e = VitaminaE.obtener_requerimiento(p)

    """
    Vitamina K
    """
    requerimiento_vitamina_k = VitaminaK.obtener_requerimiento(p)

    return {
        "energia":{
            "ree": ree,
            "unidad": "kcal"
        },
        "proteina":{
            'rpe': (requerimiento_proteina["rpe_g_por_kg"] * peso_para_calculos)+proteina_embarazo+proteina_lactancia,
            'rdd':{
                'dieta_de_referencia': (requerimiento_proteina["rdd_referencia_g_por_kg"] * peso_para_calculos)+proteina_embarazo+proteina_lactancia,
                'dieta_mixta': (requerimiento_proteina["rdd_dieta_mixta_g_por_kg"] * peso_para_calculos)+proteina_embarazo+proteina_lactancia if requerimiento_proteina["rdd_dieta_mixta_g_por_kg"] is not None else None
            },
            "unidad": "g"

        },
        "carbohidratos": {
            "idr": requerimiento_carbohidratos["tipo"],
            "minimo_de_referencia": carbohidratos_minimos,

            "distribucion_energia": {
                "minimo_porcentaje": 45,
                "maximo_porcentaje": 65,
                "minimo_gramos": carbohydrate_energy_min,
                "maximo_gramos": carbohydrate_energy_max,
            },

            "minimo_efectivo": carbohydrate_effective_min,
            "maximo_efectivo": carbohydrate_energy_max,
            "azucares_refinados": {
                "maximo_porcentaje_energia": 10,
                "maximo_gramos": azucares_refinados_max,
            },
            "unidad": "g",
        },
        "fibra": {
            "minimo": fiber_requirement,
            "referencia": "12_g_per_1000_kcal",
            "unidad": "g"
        },
        "lipidos": {
            "total": {
                "minimo": grasa_total_min,
                "maximo": grasa_total_max,
                "unidad": "g",
            },

            "saturados": {
                "maximo": saturados_max,
                "unidad": "g",
            },

            "poliinsaturados": {
                "minimo": poliinsaturados_min,
                "maximo": poliinsaturados_max,
                "unidad": "g",
            },

            "colesterol": {
                "maximo": colesterol_max,
                "unidad": "mg",
            },
        },
        "micronutrientes": {
        "vitamina_a": {
            "rpe": requerimiento_vitamina_a["rpe"],
            "rdd": requerimiento_vitamina_a["rdd"],
            "ia": requerimiento_vitamina_a["ia"],
            "minimo_efectivo": minimo_vitamina_a,
            "idr": tipo_referencia_vitamina_a,
            "unidad": "ug_EAR",

            "limite_retinol": {
                "maximo": imt_vitamina_a,
                "unidad": "ug_retinol",
            },
            },
            "tiamina": requerimiento_tiamina,
            "riboflavina": requerimiento_riboflavina,
            "niacina": requerimiento_niacina,
            "vitamina_b6": requerimiento_vitaminab6,

            "folatos": {
                "rpe": requerimiento_vitaminas_b["rpe"]["folatos"],
                "rdd": requerimiento_vitaminas_b["rdd"]["folatos"],
                "minimo_efectivo": requerimiento_vitaminas_b["rdd"]["folatos"],
                "idr": "rdd",
                "unidad": "ug_EFD",
            },

            "vitamina_b12": {
                "rpe": requerimiento_vitaminas_b["rpe"]["vitamina_b12"],
                "rdd": requerimiento_vitaminas_b["rdd"]["vitamina_b12"],
                "minimo_efectivo": requerimiento_vitaminas_b["rdd"]["vitamina_b12"],
                "idr": "rdd",
                "unidad": "ug",
            },

            "acido_pantotenico": {
                "ia": requerimiento_acido_pantotenico,
                "minimo_efectivo": requerimiento_acido_pantotenico,
                "idr": "ingesta_adecuada",
                "unidad": "mg",
            },
            "vitamina_c": {
                "ia": requerimiento_vitamina_c,
                "minimo_efectivo": requerimiento_vitamina_c,
                "idr": "ingesta_adecuada",
                "unidad": "mg",
            },

            "vitamina_d": evaluacion_vitamina_d,

            "vitamina_e": {
                "ia": requerimiento_vitamina_e,
                "minimo_efectivo": requerimiento_vitamina_e,
                "idr": "ingesta_adecuada",
                "unidad": "mg_alfa_tocoferol",
            },

            "vitamina_k": {
                "ia": requerimiento_vitamina_k,
                "minimo_efectivo": requerimiento_vitamina_k,
                "idr": "ingesta_adecuada",
                "unidad": "ug",
            },
        }
        
    }

