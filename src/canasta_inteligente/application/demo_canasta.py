"""Adaptación de las canastas del hogar para la interfaz de escritorio."""

from copy import deepcopy
from math import isfinite
from pathlib import Path

import pandas as pd

from canasta_inteligente.application.cba_pipeline import load_catalog_pickle
from canasta_inteligente.application.optimizacion_dieta import preparar_consulta, validar_catalogo
from canasta_inteligente.domain.familia import Family
from canasta_inteligente.domain.prices import VALID_REGIONS


def seleccionar_catalogo_region(catalog, region='general'):
    """Copia el catálogo; las regiones específicas usan únicamente sus propios precios.

    General conserva la selección histórica: general, luego urbana y luego rural.
    En urbana/rural se omiten alimentos sin un último precio válido en esa región.
    Se conserva toda la información nutricional y el catálogo de origen no cambia.
    """
    if region not in VALID_REGIONS:
        raise ValueError(f'Región inválida: {region}. Usa general, urbana o rural.')
    seleccionado = deepcopy(catalog)
    if region != 'general':
        for food in list(seleccionado):
            precio = food.latest_price(region)
            if (precio is None or precio.cost_per_gram is None
                    or not isfinite(precio.cost_per_gram) or precio.cost_per_gram <= 0):
                seleccionado.remove(food)
            else:
                # Los optimizadores solo podrán consultar precios de esta región.
                food.price_timelines = {region: food.price_timelines[region]}
    if not len(seleccionado):
        raise ValueError(f'No hay alimentos con precios disponibles para la región {region}.')
    return seleccionado


def agregar_aportes(resultado, catalog):
    """Calcula el detalle sobre cantidades resueltas, sin consultar variables del solver."""
    alimentos = {food.id: food for food in catalog}
    filas = []
    if resultado['estado'] == 'Optimal':
        for fila in resultado['alimentos'].itertuples(index=False):
            if fila.gramos <= 0:
                continue
            food = alimentos[fila.alimento_id]
            comestibles = fila.gramos * food.nutrition.values_per_100g['fraccion_comestible_pct']
            for nutriente in resultado['restricciones']:
                cantidad = 100 * food.is_meat if nutriente == 'carne_g' else food[nutriente]
                aporte = comestibles / 100 * cantidad
                total = resultado['aportes'][nutriente]
                filas.append({
                    'alimento_id': food.id, 'alimento': food.name,
                    'nombre_incap': getattr(food.nutrition, 'incap_name', None),
                    'nutriente': nutriente, 'unidad': nutriente.rsplit('_', 1)[-1],
                    'gramos_comprados': fila.gramos, 'gramos_comestibles': comestibles,
                    'aporte': aporte, 'porcentaje_del_total': aporte / total * 100 if total > 0 else None,
                })
    resultado['aportes_por_alimento'] = pd.DataFrame(filas, columns=[
        'alimento_id', 'alimento', 'nombre_incap', 'nutriente', 'unidad',
        'gramos_comprados', 'gramos_comestibles', 'aporte', 'porcentaje_del_total',
    ])


def tabla_alimentos(resultado, dias=1):
    """Compra y valores nutricionales para el período solicitado, alimento por alimento."""
    tabla = resultado['alimentos'].copy()
    tabla = tabla.loc[tabla['gramos'] > 0]
    detalle = resultado['aportes_por_alimento']
    if not detalle.empty:
        nutrientes = detalle.pivot(index='alimento_id', columns='nutriente', values='aporte')
        tabla = tabla.join(nutrientes, on='alimento_id')
        for nutriente in nutrientes.columns:
            tabla[nutriente] *= dias
    for columna in ('porciones_100g', 'gramos', 'costo_q'):
        tabla[columna] *= dias
    if 'region_catalogo' in resultado:
        tabla['region_catalogo'] = resultado['region_catalogo']
    return tabla


def resultado_hogar(consulta, etapa, catalog):
    """Suma únicamente propuestas completas; conserva aportes en unidades diarias."""
    propuestas = [p[f'propuesta_{etapa}'] for p in consulta['integrantes']]
    completa = all(r is not None for r in propuestas)
    resultado = {
        'tipo': 'Costo mínimo' if etapa == 'minimizacion' else 'Con presupuesto',
        'escenario': 'Propuesta del hogar', 'propuesta': completa,
        'estado': 'Optimal' if completa else 'Sin propuesta completa',
        'costo_total_q': consulta[f'costo_{etapa}_hogar_q'],
        'restricciones': {}, 'aportes': pd.Series(dtype=float),
        'alimentos': pd.DataFrame(columns=['alimento_id', 'gramos', 'porciones_100g', 'costo_q']),
        'diagnostico_restricciones': pd.DataFrame(),
    }
    if completa:
        resultado['alimentos'] = consulta[f'canasta_{etapa}'].copy()
        resultado['aportes'] = pd.concat([r['aportes'] for r in propuestas], axis=1).sum(axis=1)
        for nutriente in resultado['aportes'].index:
            limites = [r['restricciones'].get(nutriente, {}) for r in propuestas]
            claves = set.intersection(*(set(limite) for limite in limites))
            resultado['restricciones'][nutriente] = {
                clave: sum(limite[clave] for limite in limites)
                for clave in claves if all(limite[clave] is not None for limite in limites)
            }
    agregar_aportes(resultado, catalog)
    return resultado


def ejecutar_canasta(personas, catalog_path, dias=30, presupuesto=2500, *,
                     exclusiones=(), limites=None, solo_requerimientos=False,
                     pesos=None, penalizaciones_min=None, penalizaciones_max=None,
                     region='general'):
    """Una persona produce una dieta personal; varias producen una canasta familiar."""
    if not personas:
        raise ValueError('Agrega al menos un integrante antes de calcular.')
    perfiles = [preparar_consulta(persona) for persona in personas]
    if solo_requerimientos:
        return {'perfiles': perfiles, 'hogar': None, 'vistas': [], 'dias': dias}
    ruta = Path(catalog_path).expanduser()
    catalog = seleccionar_catalogo_region(load_catalog_pickle(ruta), region)
    disponibles = [food for food in catalog if food.id not in exclusiones]
    for perfil in perfiles:
        validar_catalogo(disponibles, perfil['escenarios_minimizacion'])
    hogar = Family(personas).calcular_canasta(
        dias=dias, presupuesto=presupuesto, catalog=catalog,
        alimentos_a_excluir=list(exclusiones), limite_diario_de_alimentos_en_gramos=limites,
        pesos_nutrientes=pesos, penalizaciones_min=penalizaciones_min,
        penalizaciones_max=penalizaciones_max,
    )
    etapas = ['minimizacion'] + (['maximizacion'] if presupuesto is not None else [])
    vistas = [{'nombre': 'Hogar completo', 'perfil': None, 'resultados': [
        resultado_hogar(hogar, etapa, catalog) for etapa in etapas
    ]}]
    for integrante, perfil in zip(hogar['integrantes'], perfiles):
        resultados = []
        for etapa in etapas:
            for original in integrante[f'resultados_{etapa}']:
                resultado = dict(original)
                resultado['tipo'] = 'Costo mínimo' if etapa == 'minimizacion' else 'Con presupuesto'
                resultado['propuesta'] = original is integrante[f'propuesta_{etapa}']
                agregar_aportes(resultado, catalog)
                resultados.append(resultado)
        vistas.append({
            'nombre': f"{integrante['perfil_id']}. {integrante['persona'].nombre}",
            'perfil': perfil, 'resultados': resultados,
        })
    for vista in vistas:
        for resultado in vista['resultados']:
            resultado['region_catalogo'] = region
    return {'perfiles': perfiles, 'hogar': hogar, 'vistas': vistas, 'dias': dias,
            'region_catalogo': region, 'cantidad_alimentos': len(catalog)}
