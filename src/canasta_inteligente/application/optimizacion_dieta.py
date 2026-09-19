"""Modelos del experimento optimizacion_dieta, utilizables sin Jupyter.

Las variables representan porciones compradas de 100 g. Los aportes incorporan
la fraccion comestible. Se conservan las condiciones experimentales de hierro,
las metas y las penalizaciones del notebook.
"""

from copy import deepcopy
from math import isfinite

import pandas as pd
from pulp import (
    LpMaximize, LpMinimize, LpProblem, LpStatus, LpStatusOptimal,
    LpVariable, PULP_CBC_CMD, lpSum, value,
)

from canasta_inteligente.nutrition.service import evaluacion_de_requerimientos_diarios
from canasta_inteligente.nutrition.evaluation import Peso


def preparar_consulta(persona):
    """Calcula referencias sin modificar el perfil recibido."""
    perfil = deepcopy(persona)
    requisitos = evaluacion_de_requerimientos_diarios(perfil)
    return {
        'persona': perfil,
        # Igual que el notebook: conservar la evaluación para poder inspeccionarla.
        # El servicio ya usa este peso antes de calcular energía y macronutrientes.
        'evaluacion_peso': Peso.evaluacion_peso(perfil),
        'requerimientos': requisitos,
        'escenarios_minimizacion': construir_escenarios(requisitos),
        'escenarios_maximizacion': construir_escenarios(requisitos, maximizar=True),
    }


def validar_catalogo(catalog, escenarios):
    """Rechaza datos incompletos; no convierte nutrientes desconocidos en cero."""
    if not len(catalog):
        raise ValueError('El catálogo está vacío.')
    nutrientes = set().union(*(set(r) for r in escenarios.values())) - {'carne_g'}
    for food in catalog:
        get_latest_price_any_region(food)
        if food.nutrition is None:
            raise ValueError(f'{food.name} no tiene información nutricional.')
        datos = food.nutrition.values_per_100g
        for nombre in nutrientes | {'fraccion_comestible_pct'}:
            valor = datos.get(nombre)
            if valor is None or not isfinite(valor) or valor < 0:
                raise ValueError(f'{food.name}: falta un valor válido para {nombre}.')
        if not 0 < datos['fraccion_comestible_pct'] <= 1:
            raise ValueError(f'{food.name}: la fracción comestible debe estar entre 0 y 1.')


def tabla_nutrientes(resultado):
    """Compara aportes y límites; convierte las porciones de carne a gramos."""
    filas = []
    if resultado['estado'] != 'Optimal':
        return pd.DataFrame()
    for nutriente, limites in resultado['restricciones'].items():
        escala = 100 if nutriente == 'carne_g' else 1
        meta = limites.get('meta', limites.get('min'))
        aporte = resultado['aportes'][nutriente]
        referencia = meta * escala if meta is not None else None
        filas.append({
            'nutriente': nutriente,
            'aporte': aporte,
            'meta': referencia,
            'minimo': limites['min'] * escala if 'min' in limites else None,
            'maximo': limites['max'] * escala if 'max' in limites else None,
            'referencia_flexible': limites.get('ct'),
            'cobertura_pct': min(100, max(0, aporte / referencia * 100))
            if referencia is not None and referencia > 0 else None,
            'deficit': max(0, referencia - aporte) if referencia is not None else None,
        })
    return pd.DataFrame(filas)


def get_latest_price_any_region(food):
    """Ultimo precio general; en su ausencia, urbano y luego rural."""
    for region in ('general', 'urbana', 'rural'):
        point = food.price_summary(region=region)['latest']
        if point is not None:
            price = point.cost_per_gram
            if price is None or not isfinite(price) or price <= 0:
                raise ValueError(f'Precio invalido para {food.name} en {region}.')
            return price
    raise ValueError(f'{food.name} no tiene precios disponibles.')



def construir_restricciones_base(requerimientos):
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
            'carne_g': {'min': 0.30, 'max': 0.90}
        
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
    # None significa que el evaluador no proporciona ese limite para este perfil.
    for limites in constraints_keys_base.values():
        for tipo, valor in list(limites.items()):
            if valor is None:
                del limites[tipo]
    return constraints_keys_base, hierro_constraints


def combinar_escenarios(base, hierro, maximizar=False):
    """Combina las condiciones de hierro sin modificar las entradas."""
    escenarios = {}
    for nombre, condiciones in hierro.items():
        restricciones = deepcopy(base)
        if maximizar:
            for limites in restricciones.values():
                if 'min' in limites:
                    limites['meta'] = limites.pop('min')
        restricciones['hierro_mg'] = {
            'meta' if maximizar else 'min': condiciones['hierro_mg']['min'],
        }
        restricciones['carne_g'] = deepcopy(condiciones['carne_g'])
        vitamina_c = restricciones['vitamina_c_mg']
        for tipo, valor in condiciones['vitamina_c_mg'].items():
            combinar = max if tipo == 'min' else min
            vitamina_c[tipo] = combinar(vitamina_c.get(tipo, valor), valor)
        # Conservar los escenarios incompatibles para reportarlos como Infeasible.
        escenarios[f'hierro_{nombre}'] = restricciones
    return escenarios


def construir_escenarios(requerimientos, maximizar=False):
    base, hierro = construir_restricciones_base(requerimientos)
    return combinar_escenarios(base, hierro, maximizar=maximizar)


def extraer_resultado(escenario, modelo, catalog_variables, restricciones,
                     desviaciones, penalizaciones):
    """Guarda una instantánea numérica y las referencias al modelo resuelto."""
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

    filas_aportes = []
    if es_optimo:
        for food, variable in catalog_variables:
            porciones = variable.varValue
            if porciones <= 0:
                continue
            fraccion = food.nutrition.values_per_100g['fraccion_comestible_pct']
            for nutriente in restricciones:
                cantidad = 100 * food.is_meat if nutriente == 'carne_g' else food[nutriente]
                aporte = porciones * cantidad * fraccion
                total = aportes[nutriente]
                filas_aportes.append({
                    'alimento_id': food.id, 'alimento': food.name,
                    'nombre_incap': getattr(food.nutrition, 'incap_name', None),
                    'nutriente': nutriente, 'unidad': nutriente.rsplit('_', 1)[-1],
                    'gramos_comprados': porciones * 100,
                    'gramos_comestibles': porciones * 100 * fraccion,
                    'aporte': aporte,
                    'porcentaje_del_total': aporte / total * 100 if total > 0 else None,
                })
    aportes_por_alimento = pd.DataFrame(filas_aportes, columns=[
        'alimento_id', 'alimento', 'nombre_incap', 'nutriente', 'unidad', 'gramos_comprados',
        'gramos_comestibles', 'aporte', 'porcentaje_del_total',
    ])

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
        'aportes_por_alimento': aportes_por_alimento,
        'restricciones': deepcopy(restricciones),
        'diagnostico_restricciones': diagnostico,
        'modelo': modelo,
        'variables': {food.id: variable for food, variable in catalog_variables},
    }


def minimizar_costo(catalog, escenarios, penalizaciones=None):
    """Minimiza costo mas penalizaciones, con minimos y maximos obligatorios."""
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
        modelo = LpProblem(f"MinimizeCost_{escenario}", LpMinimize)
        variables = [
            (food, LpVariable(f'no_portions_{food.id}', lowBound=0))
            for food in catalog
        ]
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

        resultado = extraer_resultado(
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


def maximizar_cobertura(catalog, escenarios, presupuesto, pesos_nutrientes=None,
                       penalizaciones=None):
    """Resuelve cada escenario con metas flexibles y limites obligatorios."""
    if not isfinite(presupuesto) or presupuesto < 0:
        raise ValueError('El presupuesto debe ser finito y no negativo.')

    # Los nutrientes omitidos conservan peso 1. Copia para no modificar la entrada.
    pesos_configurados = dict(pesos_nutrientes or {})
    nutrientes_con_meta = {
        nutriente for restricciones in escenarios.values()
        for nutriente, limites in restricciones.items()
        if nutriente != 'carne_g' and limites.get('meta') is not None
        and limites['meta'] > 0
    }
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

    resultados = []
    for escenario, restricciones in escenarios.items():
        modelo = LpProblem(f"MaximizeCoverage_{escenario}", LpMaximize)
        variables = [
            (food, LpVariable(f'no_portions_{food.id}', lowBound=0))
            for food in catalog
        ]
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

        metas = {
            nutriente: limites['meta']
            for nutriente, limites in restricciones.items()
            if nutriente != 'carne_g' and limites.get('meta') is not None
            and limites['meta'] > 0
        }
        if not metas:
            raise ValueError(f'El escenario {escenario} no tiene metas positivas.')
        pesos = {nutriente: pesos_configurados.get(nutriente, 1.0) for nutriente in metas}
        suma_pesos = sum(pesos.values())
        if not isfinite(suma_pesos) or suma_pesos <= 0:
            raise ValueError(f'El escenario {escenario} requiere una suma de pesos positiva y finita.')
        coberturas = {
            nutriente: LpVariable(f'cobertura_{nutriente}', lowBound=0, upBound=1)
            for nutriente in metas
        }
        puntuacion_cobertura = lpSum(
            pesos[nutriente] * cobertura for nutriente, cobertura in coberturas.items()
        )
        desviaciones = {}
        terminos_penalizacion = []
        for nutriente, meta in metas.items():
            modelo += aportes[nutriente] >= meta * coberturas[nutriente], f'cobertura_de_{nutriente}'

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
        modelo += costo <= presupuesto, 'presupuesto_diario'
        modelo += puntuacion_cobertura - lpSum(terminos_penalizacion), 'cobertura_menos_penalizaciones'
        modelo.solve(PULP_CBC_CMD(msg=0))

        resultado = extraer_resultado(
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


def resumir_consulta(resultados):
    return pd.DataFrame([
        {
            'escenario': r['escenario'], 'estado': r['estado'],
            'costo_total_q': r['costo_total_q'], 'valor_objetivo': r['valor_objetivo'],
            'energia_deficit_kcal': r['desviaciones'].get('energia_deficit_kcal'),
            'energia_exceso_kcal': r['desviaciones'].get('energia_exceso_kcal'),
            'colesterol_exceso_mg': r['desviaciones'].get('colesterol_exceso_mg'),
            'cobertura_ponderada_pct': r.get('cobertura_ponderada_pct'),
        }
        for r in resultados
    ])
