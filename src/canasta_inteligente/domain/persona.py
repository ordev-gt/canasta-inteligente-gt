from math import isfinite

from ..nutrition.activity import PhysicalActivityLevel
from pulp import *
import pandas as pd
from copy import deepcopy
from .food import FoodCatalog


def get_latest_price_any_region(food_item): 
    return food_item.price_summary(region='general')['latest'].cost_per_gram if food_item.price_summary(region='general')['latest'] is not None else (food_item.price_summary(region='urbana')['latest'].cost_per_gram if food_item.price_summary(region='urbana')['latest'] is not None else  food_item.price_summary(region='rural')['latest'].cost_per_gram)


class Persona:
    nombre: str
    edad: int # years
    edad_meses: int
    sexo: str
    peso: float
    altura: float = None
    naf: str # liviana, moderada, intensa
    naf_indice: float = None
    esta_embarazada: bool
    mes_de_embarazo:int 
    reservas_de_energia_maternales: bool
    esta_en_lactancia: bool
    peso_preembarazo: float | None
    mes_de_lactancia: int

    peso_para_calculos:float
    padece_sudoracion_profusa: bool

    
    def __init__(self, nombre, edad, sexo, peso, naf, altura, 
                 esta_embarazada=False, mes_de_embarazo=None, reservas_de_energia_maternales=False,
                  esta_en_lactancia=False, peso_preembarazo: float = None, mes_de_lactancia: int = None,
                  exposicion_solar_suficiente = True, padece_sudoracion_profusa:bool = False):
    
        if not sexo in ['hombre', 'mujer']: 
            raise ValueError('Gender must be either hombre or mujer ')

        if edad < 0:
            raise ValueError("Edad must be greater than 0")

        if naf not in ['low', 'moderate', 'high']:
            raise ValueError('NAF must be either low, moderate or high')
        if sexo=='hombre': 
            if esta_embarazada or esta_en_lactancia: 
                raise ValueError('Cannot instanciate hombre pregnant or in lactancy.')

        else:
            if esta_embarazada:
                if not mes_de_embarazo is None:
                    if not (mes_de_embarazo < 10 and  mes_de_embarazo >= 0 ):
                        raise ValueError(f'Pregnancy month not a valid value, must be a number between 0-9 ()')
                else: 
                    raise ValueError('Must define pregnancy in case mujer is pregnant') 


        self.nombre = nombre
        self.edad = edad
        self.edad_meses = round(edad * 12) # Aproximacion, preguntar si es conveniente indicar que se ingrese la edad exacta con meses. Ingresar fecha de nacimiento?
        self.sexo = sexo
        self.peso = peso
        self.naf = naf
        self.altura = altura
        self.esta_embarazada = esta_embarazada
        self.mes_de_embarazo = mes_de_embarazo
        self.esta_en_lactancia = esta_en_lactancia
        self.mes_de_lactancia = mes_de_lactancia
        self.reservas_de_energia_maternales = reservas_de_energia_maternales
        self.peso_preembarazo = peso_preembarazo
        self.exposicion_solar_suficiente = exposicion_solar_suficiente
        self.peso_para_calculos = None
        self.padece_sudoracion_profusa = padece_sudoracion_profusa
        self.calculate_naf_index()

    
    def calculate_naf_index(self): 
        """Compatibilidad: delega la regla nutricional al servicio de actividad."""
        self.naf_indice = PhysicalActivityLevel.factor(self.sexo, self.naf)
        return self.naf_indice

    def __construir_restricciones_base(self, requerimientos):
        """Traduce los requisitos de este perfil a nutrientes del catalogo."""
        escalar = lambda valor, divisor: None if valor is None else valor / divisor
        get_min_req = lambda nutrient, subrequerimientos: subrequerimientos[nutrient].get('rdd') if subrequerimientos[nutrient].get('rdd') is not None else subrequerimientos[nutrient].get('ia') 
        # ct = close to 
        constraints_keys_base = {
            'energia_kcal': {"ct": requerimientos['energia']['ree']},
            'proteina_g': {"min": requerimientos['proteina']['rdd_dieta_mixta']},
            'carbohidratos_g': {"min": requerimientos['carbohidratos']['rdd_min']},
            'azucares_g': {"max": requerimientos["azucar"]["rdd"]},
            'fibra_dietetica_g': {"min": requerimientos["fibra"]['rdd']},
            'grasa_total_g': {"min": requerimientos["lipidos"]["total_min"], 'max': requerimientos['lipidos']['total_max']},
            'ag_sat_g': {"max": requerimientos["lipidos"]['saturados_max']},
            'ag_poli_g': {"min": requerimientos["lipidos"]["poliinsaturados_min"], 'max': requerimientos["lipidos"]["poliinsaturados_max"]},
            'colesterol_mg': {"ct": requerimientos['colesterol']["maximo"]},
            'vitamina_a_rae_mcg': {"min": get_min_req('vitamina_a', requerimientos["micronutrientes"])},
            'retinol_mcg': {"max": requerimientos['micronutrientes']['retinol']['imt']},
            'tiamina_mg': {"min": get_min_req('tiamina', requerimientos["micronutrientes"]) },
            'riboflavina_mg': {"min": get_min_req('riboflavina', requerimientos["micronutrientes"]) },
            'niacina_mg': {"min": get_min_req('niacina', requerimientos["micronutrientes"]) },
            'vitamina_b6_mg': {"min": get_min_req('vitamina_b6', requerimientos["micronutrientes"]), 'max': requerimientos['micronutrientes']['vitamina_b6']['imt']},
            'folato_fde_mcg': {"min": get_min_req('folatos', requerimientos["micronutrientes"])},
            'ac_folico_mcg': {"max": requerimientos['micronutrientes']["folato_sintetico"]["imt"]},
            'vitamina_b12_mcg': {'min': get_min_req('vitamina_b12', requerimientos["micronutrientes"])},
            'ac_pantotenico_mg': {'min': get_min_req('acido_pantotenico', requerimientos["micronutrientes"])},
            'vitamina_c_mg': {"min": get_min_req('vitamina_c', requerimientos["micronutrientes"])},
            'vitamina_d_mcg': {"min": get_min_req('vitamina_d', requerimientos["micronutrientes"]), "max": requerimientos['micronutrientes']['vitamina_d']['imt']},
            'vitamina_e_mg': {"min": get_min_req('vitamina_e', requerimientos["micronutrientes"]), "max": requerimientos['micronutrientes']['vitamina_e']['imt']},
            'vitamina_k_mcg': {"min": get_min_req("vitamina_k", requerimientos["micronutrientes"])},
            'calcio_mg': {"min": get_min_req("calcio", requerimientos["minerales"]), "max":  requerimientos['minerales']['calcio']['imt']},
            'magnesio_mg': {"min": get_min_req("magnesio", requerimientos["minerales"])},
            'fosforo_mg': {"min": get_min_req("fosforo", requerimientos["minerales"])},
            'selenio_mcg': {"min": get_min_req("selenio", requerimientos["minerales"]), "max":  requerimientos['minerales']['selenio']['imt']},
            'cobre_mg': {"min": escalar(get_min_req("cobre", requerimientos["minerales"]), 1000), "max":  escalar(requerimientos['minerales']['cobre']['imt'], 1000)},
            'zinc_mg':{"min": get_min_req("baja_biodisponibilidad", requerimientos['minerales']['zinc'])}, # Asumimos baja biodisponibildiad  dados los multiples factores que afecta la aborcion del zinc. 
            'potasio_mg': {"min": get_min_req("potasio", requerimientos["electrolitos"])},
            'sodio_mg': {"min": get_min_req("sodio", requerimientos["electrolitos"]), "max":  requerimientos["electrolitos"]['sodio']['limite_sugerido']},
        }



        hierro_constraints = {
            'baja_disponiblidad': {
                "hierro_mg": {'min': get_min_req("baja_biodisponibilidad", requerimientos['minerales']['hierro'])},
                "vitamina_c_mg": {'min': 0.00},
                'carne_g': {'min': 0.00}
            },# Sin restricciones
            'media_disponiblidad': {
                "hierro_mg": {'min': get_min_req("media_biodisponibilidad", requerimientos['minerales']['hierro'])},
                "vitamina_c_mg": { 'min': 25, 'max': 75 },
                'carne_g': {'min': 0.30, 'max': 0.90} # Dado en porcion de 100g 0.9 son 90g
            
            },

            'alta_disponiblidad_A': {
                "hierro_mg": {'min': get_min_req("alta_biodisponibilidad", requerimientos['minerales']['hierro'])},
                "vitamina_c_mg": { 'min': 25, 'max': 75 },
                'carne_g': {'min': 0.3}

            },
            'alta_disponiblidad_B': {
                "hierro_mg": {'min': get_min_req("alta_biodisponibilidad", requerimientos['minerales']['hierro'])},
                "vitamina_c_mg": {'min': 25},
                'carne_g': {'min': 0.9}

            },
        }
        for limites in constraints_keys_base.values():
            for tipo, valor in list(limites.items()):
                if valor is None:
                    del limites[tipo]
        return constraints_keys_base, hierro_constraints

    def __combinar_escenarios(self, base, hierro, maximizar=False):
        """
        
        Combina las condiciones de hierro sin modificar las entradas.
        
        Si se usa para minimizar costo, se usa la key: 'min'
 
        Si se usa para maximizar el minimo se convierte en 'meta'
        """
        escenarios = {}
        for nombre, condiciones in hierro.items():
            restricciones = deepcopy(base)
            if maximizar:
                for limites in restricciones.values():
                    if 'min' in limites:
                        limites['meta'] = limites.pop('min') # sustitucion meta por min en caso de maximizar en restricciones base
            restricciones['hierro_mg'] = {
                'meta' if maximizar else 'min': condiciones['hierro_mg']['min'],
            } # sustitucion meta por min en caso de maximizar para restricciones en escenario hierro. 
            restricciones['carne_g'] = deepcopy(condiciones['carne_g'])

            vitamina_c = restricciones['vitamina_c_mg'] # requisitos base vitamina_c

            # La vitamina c es un restriccion en comun entre la base y escenarios, 
            # En caso de minmizar costo, se toma el requisito , se busca el requisito mayor, 
            # en el caso de maximizar el requisito minimo. 
            for tipo, valor in condiciones['vitamina_c_mg'].items():
                combinar = max if tipo == 'min' else min  # seleccion de funcion. 
                vitamina_c[tipo] = combinar(vitamina_c.get(tipo, valor), valor)
            # Conservar los escenarios incompatibles para reportarlos como Infeasible.
            escenarios[f'hierro_{nombre}'] = restricciones # se almacena el escenario. 
        return escenarios

    def __construir_escenarios(self, requerimientos, maximizar=False):
        base, hierro = self.__construir_restricciones_base(requerimientos)
        return self.__combinar_escenarios(base, hierro, maximizar=maximizar)

    def __extraer_resultado(self, escenario, modelo, catalog_variables, restricciones,
                        desviaciones, penalizaciones):
        es_optimo = modelo.status == LpStatusOptimal
        filas = []
        if es_optimo:
            for food, variable in catalog_variables:
                porciones = variable.varValue
                gramos = porciones * 100
                precio = get_latest_price_any_region(food)
                filas.append({
                    'alimento_id': food.id, 'alimento': food.name,
                    'nombre_incap': getattr(food.nutrition, 'incap_name', None),
                    'porciones_100g': porciones, 'gramos': gramos,
                    'precio_q_por_gramo': precio, 'costo_q': gramos * precio,
                })

        alimentos = pd.DataFrame(filas, columns=[
            'alimento_id', 'alimento', 'nombre_incap', 'porciones_100g', 'gramos',
            'precio_q_por_gramo', 'costo_q',
        ])
        aportes = {}
        if es_optimo:
            for nutriente in restricciones:
                # El modelo usa porciones de 100 g para carne_g; aquí mostramos gramos.
                aportes[nutriente] = sum(
                    variable.varValue * (100 * food.is_meat if nutriente == 'carne_g'
                                        else food[nutriente])
                    * food.nutrition.values_per_100g['fraccion_comestible_pct']
                    for food, variable in catalog_variables
                )

        diagnostico = pd.DataFrame([
            {
                'restriccion': nombre,
                'expresion': str(restriccion),
                'holgura_solver': restriccion.slack if es_optimo else None,
                'precio_sombra': restriccion.pi if es_optimo else None,
            }
            for nombre, restriccion in modelo.constraints.items()
        ])
        return {
            'escenario': escenario,
            'estado': LpStatus[modelo.status],
            'codigo_estado': modelo.status,
            'costo_total_q': float(alimentos['costo_q'].sum()) if es_optimo else None,
            'valor_objetivo': value(modelo.objective) if es_optimo else None,
            'desviaciones': {
                nombre: variable.varValue if es_optimo else None
                for nombre, variable in desviaciones.items()
            },
            'penalizaciones': penalizaciones.copy(),
            'alimentos': alimentos,
            'aportes': pd.Series(aportes, dtype=float, name='aporte_total'),
            'restricciones': deepcopy(restricciones),
            'diagnostico_restricciones': diagnostico,
            'modelo': modelo,
            'variables': {food.id: variable for food, variable in catalog_variables},
        }

    def __minimizar_costo(self, catalog, escenarios, limites_de_alimentos_diario, penalizaciones=None):
        """Minimiza costo mas penalizaciones, con minimos y maximos obligatorios."""

        """
        Validaciones
        """
        coeficientes = {'energia': 1.0, 'colesterol': 0.1}
        configuradas = dict(penalizaciones or {})
        desconocidas = set(configuradas) - set(coeficientes)
        if desconocidas:
            raise ValueError(f'Penalizaciones desconocidas: {sorted(desconocidas)}')
        coeficientes.update(configuradas)
        for nombre, coeficiente in coeficientes.items():
            try:
                coeficiente = float(coeficiente)
            except (TypeError, ValueError):
                raise ValueError(f'Penalizacion invalida para {nombre}: debe ser numerica.') from None
            if not isfinite(coeficiente) or coeficiente < 0:
                raise ValueError(f'Penalizacion invalida para {nombre}: debe ser finita y no negativa.')
            coeficientes[nombre] = coeficiente


        resultados = []
        for escenario, restricciones in escenarios.items():
            # Inicializacion de problema
            modelo = LpProblem(f"MinimizeCost_{escenario}", LpMinimize)
            # Creacion de variables, una por alimento. Representando la cantidad de porciones. 1 porcion es de 100g. 
            variables = [(food, LpVariable(f'no_portions_{food.id}', lowBound=0)) for food in catalog ]
            por_id = {food.id: variable for food, variable in variables} # Diccionario auxiliar para acceder a variables

            if limites_de_alimentos_diario is not None: # Restriccion adicional por alimento. Para evitar excesos inviables. 
                for _food_id, limite_diario in limites_de_alimentos_diario.items():
                    modelo += por_id[_food_id] * 100 <= limite_diario

            aportes = {}
            for nutriente in restricciones:
                if nutriente == 'carne_g':
                    aportes[nutriente] = lpSum(
                        variable * food.nutrition.values_per_100g['fraccion_comestible_pct']
                        for food, variable in variables if food.is_meat
                    )
                else:
                    aportes[nutriente] = lpSum(
                        variable * food[nutriente]
                        * food.nutrition.values_per_100g['fraccion_comestible_pct']
                        for food, variable in variables
                    )

            desviaciones = {}
            terminos_penalizacion = []
            for nutriente, limites in restricciones.items():
                if 'ct' in limites:
                    referencia = limites['ct']
                    if not isfinite(referencia) or referencia < 0:
                        raise ValueError(f'Referencia ct invalida para {nutriente}.')
                    if nutriente == 'energia_kcal':
                        deficit = LpVariable('deEminus', lowBound=0)
                        exceso = LpVariable('deEplus', lowBound=0)
                        modelo += aportes[nutriente] + deficit - exceso == referencia, 'REE'
                        desviaciones['energia_deficit_kcal'] = deficit
                        desviaciones['energia_exceso_kcal'] = exceso
                        terminos_penalizacion.append(coeficientes['energia'] * (deficit + exceso))
                    elif nutriente == 'colesterol_mg':
                        exceso = LpVariable('deCPlus', lowBound=0)
                        modelo += aportes[nutriente] - exceso <= referencia, 'Colesterol'
                        desviaciones['colesterol_exceso_mg'] = exceso
                        terminos_penalizacion.append(coeficientes['colesterol'] * exceso)
                    else:
                        raise ValueError(f'Nutriente con referencia ct no admitido: {nutriente}')
                if 'min' in limites:
                    modelo += aportes[nutriente] >= limites['min'], f'limite_inferior_de_{nutriente}'
                if 'max' in limites:
                    modelo += aportes[nutriente] <= limites['max'], f'limite_superior_de_{nutriente}'

            costo = lpSum(
                variable * get_latest_price_any_region(food) * 100
                for food, variable in variables
            )
            modelo += costo + lpSum(terminos_penalizacion), 'costo_mas_penalizaciones'
            modelo.solve(PULP_CBC_CMD(msg=0))

            resultado = self.__extraer_resultado(
                escenario, modelo, variables, restricciones,
                desviaciones=desviaciones, penalizaciones=coeficientes,
            )
            # Reportar desviaciones reales incluso si un coeficiente es cero:
            # en ese caso el solver no esta obligado a minimizar las holguras.
            if modelo.status == LpStatusOptimal:
                if 'energia_deficit_kcal' in desviaciones:
                    diferencia = resultado['aportes']['energia_kcal'] - restricciones['energia_kcal']['ct']
                    resultado['desviaciones']['energia_deficit_kcal'] = max(0.0, -diferencia)
                    resultado['desviaciones']['energia_exceso_kcal'] = max(0.0, diferencia)
                if 'colesterol_exceso_mg' in desviaciones:
                    resultado['desviaciones']['colesterol_exceso_mg'] = max(
                        0.0, resultado['aportes']['colesterol_mg'] - restricciones['colesterol_mg']['ct'],
                    )
            resultado['penalizacion_total'] = (
                coeficientes['energia'] * (
                    resultado['desviaciones'].get('energia_deficit_kcal', 0.0)
                    + resultado['desviaciones'].get('energia_exceso_kcal', 0.0)
                ) + coeficientes['colesterol'] * resultado['desviaciones'].get('colesterol_exceso_mg', 0.0)
                if modelo.status == LpStatusOptimal else None
            )
            resultados.append(resultado)
        return resultados

    def calcular_requerimientos(self):
        """Evalúa el peso y calcula los requerimientos diarios de esta persona."""
        from ..nutrition.service import evaluacion_de_requerimientos_diarios
        return evaluacion_de_requerimientos_diarios(self)

    def calculo_canasta_diaria_costo_minimizado(self, catalog: FoodCatalog, *, limite_de_alimentos_diario=None, penalizaciones=None):
        """Devuelve los cuatro escenarios, conservando sus estados y resultados."""
        requerimientos = self.calcular_requerimientos()
        escenarios = self.__construir_escenarios(requerimientos)
        return self.__minimizar_costo(catalog, escenarios, limite_de_alimentos_diario, penalizaciones)


    def __maximizar_cobertura(self, catalog, escenarios, presupuesto, pesos_nutrientes=None,
                        penalizaciones=None, limite_de_alimentos_diario=None):

        """
        Validaciones
        """
        if not isfinite(presupuesto) or presupuesto < 0:
            raise ValueError('El presupuesto debe ser finito y no negativo.')

        # Los nutrientes omitidos conservan peso 1. Copia para no modificar la entrada.
        pesos_configurados = dict(pesos_nutrientes or {})
        """
        Identificacion de requisitos 
        """
        nutrientes_con_meta = {
            nutriente for restricciones in escenarios.values()
            for nutriente, limites in restricciones.items()
            if nutriente != 'carne_g' and limites.get('meta') is not None
            and limites['meta'] > 0
        }
        """
        Mas validaciones
        """
        desconocidos = set(pesos_configurados) - nutrientes_con_meta
        if desconocidos:
            raise ValueError(f'Pesos sin una meta nutricional positiva: {sorted(desconocidos)}')
        for nutriente, peso in pesos_configurados.items():
            try:
                peso = float(peso)
            except (TypeError, ValueError):
                raise ValueError(f'Peso invalido para {nutriente}: debe ser numerico.') from None
            if not isfinite(peso) or peso < 0:
                raise ValueError(f'Peso invalido para {nutriente}: debe ser finito y no negativo.')
            pesos_configurados[nutriente] = peso

        coeficientes = {'energia': 1.0, 'colesterol': 0.1}
        configuradas = dict(penalizaciones or {})
        desconocidas = set(configuradas) - set(coeficientes)
        if desconocidas:
            raise ValueError(f'Penalizaciones desconocidas: {sorted(desconocidas)}')
        coeficientes.update(configuradas)
        for nombre, coeficiente in coeficientes.items():
            try:
                coeficiente = float(coeficiente)
            except (TypeError, ValueError):
                raise ValueError(f'Penalizacion invalida para {nombre}: debe ser numerica.') from None
            if not isfinite(coeficiente) or coeficiente < 0:
                raise ValueError(f'Penalizacion invalida para {nombre}: debe ser finita y no negativa.')
            coeficientes[nombre] = coeficiente


        """
        Inicia planteo del problema
        """
        resultados = []
        for escenario, restricciones in escenarios.items():
            modelo = LpProblem(f"MaximizeCoverage_{escenario}", LpMaximize) # Inicializa problema
            # Crea una variable por cada alimento. La variable representa el numero de porciones. Una porcion de 100g
            variables = [(food, LpVariable(f'no_portions_{food.id}', lowBound=0)) for food in catalog ] 
            por_id = {food.id: variable for food, variable in variables} # Diccionario auxiliar para acceder a variables
            for food_id, gramos in (limite_de_alimentos_diario or {}).items():
                modelo += por_id[food_id] * 100 <= gramos # Restriccion adicional por alimento. Para evitar excesos inviables. 


            # Sumatoria de aporte por nutriente por alimento. 
            aportes = {}
            for nutriente in restricciones:
                if nutriente == 'carne_g': # trato especial porque no es un nutriente y se necesita comparar la cantidad neta de gramos
                    aportes[nutriente] = lpSum(
                        variable * food.nutrition.values_per_100g['fraccion_comestible_pct']
                        for food, variable in variables if food.is_meat
                    )
                else:
                    aportes[nutriente] = lpSum(
                        variable * food[nutriente]
                        * food.nutrition.values_per_100g['fraccion_comestible_pct']
                        for food, variable in variables
                    )


            # Identificacion de parte derecha de restriccion la meta por nutriente. La meta. 
            metas = {
                nutriente: limites['meta']
                for nutriente, limites in restricciones.items()
                if nutriente != 'carne_g' and limites.get('meta') is not None
                and limites['meta'] > 0
            }
            if not metas:
                raise ValueError(f'El escenario {escenario} no tiene metas positivas.')

            # Ponderacion de importancia de nutriente. Default 1.0
            pesos = {nutriente: pesos_configurados.get(nutriente, 1.0) for nutriente in metas}
            suma_pesos = sum(pesos.values())
            if not isfinite(suma_pesos) or suma_pesos <= 0:
                raise ValueError(f'El escenario {escenario} requiere una suma de pesos positiva y finita.')

            # Cobertura porcentual de nutrientes, variable. Una por nutriente.  
            coberturas = {
                nutriente: LpVariable(f'cobertura_{nutriente}', lowBound=0, upBound=1)
                for nutriente in metas
            }

            puntuacion_cobertura = lpSum(
                pesos[nutriente] * cobertura for nutriente, cobertura in coberturas.items()
            )
            # Restriccioens blandas, Colesterol, Energia.
            desviaciones = {}  
            terminos_penalizacion = []

            # Restriccion de cobertura. El aporte debe ser mayor o igual a la meta planteada multiplicado por la cobertura. 
            # Idealmente 1, pero su ajuste dependera de la restriccion de costo. 

            for nutriente, meta in metas.items():
                modelo += aportes[nutriente] >= meta * coberturas[nutriente], f'cobertura_de_{nutriente}'

            # Restricciones de
            # - IMT, para evitar ingestas desproporcionadas y superar limites por compensar otros nutrientes o la parte economica.
            # - Minimo para entrar en los escenarios de biodisponibilidad: Aplica solo Vitamina c y Carne 
            for nutriente, limites in restricciones.items():
                if 'ct' in limites: # Energia y colesterol. Restricciones blandas. 
                    referencia = limites['ct']
                    if not isfinite(referencia) or referencia < 0:
                        raise ValueError(f'Referencia ct invalida para {nutriente}.')
                    if nutriente == 'energia_kcal':
                        deficit = LpVariable('deEminus', lowBound=0)
                        exceso = LpVariable('deEplus', lowBound=0)
                        modelo += aportes[nutriente] + deficit - exceso == referencia, 'REE'
                        desviaciones['energia_deficit_kcal'] = deficit
                        desviaciones['energia_exceso_kcal'] = exceso
                        terminos_penalizacion.append(coeficientes['energia'] * (deficit + exceso))
                    elif nutriente == 'colesterol_mg':
                        exceso = LpVariable('deCPlus', lowBound=0)
                        modelo += aportes[nutriente] - exceso <= referencia, 'Colesterol'
                        desviaciones['colesterol_exceso_mg'] = exceso
                        terminos_penalizacion.append(coeficientes['colesterol'] * exceso)
                    else:
                        raise ValueError(f'Nutriente con referencia ct no admitido: {nutriente}')
                if 'min' in limites: # Para la maximizacion el unico minimo es la restriccion de carne. 
                    modelo += aportes[nutriente] >= limites['min'], f'limite_inferior_de_{nutriente}'
                if 'max' in limites:
                    modelo += aportes[nutriente] <= limites['max'], f'limite_superior_de_{nutriente}'


            # Restriccion de costo / presupuesto
            costo = lpSum(
                variable * get_latest_price_any_region(food) * 100
                for food, variable in variables
            )
            modelo += costo <= presupuesto, 'presupuesto_diario'

            # Funcion objetivo usando sumatoria de cobertura nutricional
            modelo += puntuacion_cobertura - lpSum(terminos_penalizacion), 'cobertura_menos_penalizaciones'


            #Busqueda de solucion optima de modelo 
            modelo.solve(PULP_CBC_CMD(msg=1))

            # Almacenamiento de resultado por 
            resultado = self.__extraer_resultado(
                escenario, modelo, variables, restricciones,
                desviaciones=desviaciones, penalizaciones=coeficientes,
            )


            if modelo.status == LpStatusOptimal:
                if 'energia_deficit_kcal' in desviaciones:
                    diferencia = resultado['aportes']['energia_kcal'] - restricciones['energia_kcal']['ct']
                    resultado['desviaciones']['energia_deficit_kcal'] = max(0.0, -diferencia)
                    resultado['desviaciones']['energia_exceso_kcal'] = max(0.0, diferencia)
                if 'colesterol_exceso_mg' in desviaciones:
                    resultado['desviaciones']['colesterol_exceso_mg'] = max(
                        0.0, resultado['aportes']['colesterol_mg'] - restricciones['colesterol_mg']['ct'],
                    )
            resultado['penalizacion_total'] = (
                coeficientes['energia'] * (
                    resultado['desviaciones'].get('energia_deficit_kcal', 0.0)
                    + resultado['desviaciones'].get('energia_exceso_kcal', 0.0)
                ) + coeficientes['colesterol'] * resultado['desviaciones'].get('colesterol_exceso_mg', 0.0)
                if modelo.status == LpStatusOptimal else None
            )
            resultado['presupuesto_q'] = presupuesto
            resultado['pesos_nutrientes'] = pesos.copy()
            filas = []
            if modelo.status == LpStatusOptimal:
                for nutriente, meta in metas.items():
                    aporte = resultado['aportes'][nutriente]
                    filas.append({
                        'nutriente': nutriente, 'meta': meta, 'aporte': aporte,
                        'peso': pesos[nutriente],
                        'cobertura_pct': min(1.0, max(0.0, aporte / meta)) * 100,
                        'deficit': max(0.0, meta - aporte),
                    })
            resultado['coberturas'] = pd.DataFrame(filas, columns=[
                'nutriente', 'meta', 'aporte', 'peso', 'cobertura_pct', 'deficit',
            ]).set_index('nutriente')
            resultado['cobertura_media_pct'] = (
                float(resultado['coberturas']['cobertura_pct'].mean())
                if modelo.status == LpStatusOptimal else None
            )
            resultado['cobertura_ponderada_pct'] = (
                float((resultado['coberturas']['cobertura_pct']
                    * resultado['coberturas']['peso']).sum() / suma_pesos)
                if modelo.status == LpStatusOptimal else None
            )
            resultados.append(resultado)
        return resultados

    def calculo_canasta_diaria_maximizacion_cobertura_nutricional(
        self, catalog: FoodCatalog, presupuesto, *, pesos_nutrientes=None, penalizaciones=None,
        limite_de_alimentos_diario=None,
    ):
        """Resuelve los escenarios con el presupuesto diario de esta persona."""
        requerimientos = self.calcular_requerimientos()
        escenarios = self.__construir_escenarios(requerimientos, maximizar=True)
        return self.__maximizar_cobertura(
            catalog, escenarios, presupuesto, pesos_nutrientes, penalizaciones=penalizaciones,
            limite_de_alimentos_diario=limite_de_alimentos_diario,
        )
