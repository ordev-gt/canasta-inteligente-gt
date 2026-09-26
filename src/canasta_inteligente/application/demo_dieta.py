"""Perfil y flujo de optimizaci?n compartidos por consola y Tkinter."""

from math import isfinite
from pathlib import Path

from canasta_inteligente.application.cba_pipeline import load_catalog_pickle
from canasta_inteligente.application.optimizacion_dieta import (
    maximizar_cobertura, minimizar_costo, preparar_consulta, validar_catalogo,
)
from canasta_inteligente.domain.persona import Persona


def numero(texto, nombre, minimo=0, estricto=False, maximo=None, entero=False):
    try:
        valor = float(str(texto).strip().replace(',', '.'))
    except ValueError:
        raise ValueError(f'{nombre}: ingresa un número válido.') from None
    if (not isfinite(valor) or valor < minimo or (estricto and valor == minimo)
            or (maximo is not None and valor > maximo) or (entero and not valor.is_integer())):
        limite = 'mayor que' if estricto else 'mayor o igual a'
        raise ValueError(f'{nombre}: debe ser {limite} {minimo}'
                         + (f' y menor o igual a {maximo}' if maximo is not None else '')
                         + (' y entero.' if entero else '.'))
    return int(valor) if entero else valor


def leer_pesos(texto):
    pesos = {}
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        nombre, separador, valor = linea.partition('=')
        nombre = nombre.strip()
        if not separador or not nombre:
            raise ValueError('Escribe cada peso como nutriente = valor, uno por línea.')
        if nombre in pesos:
            raise ValueError(f'El peso de {nombre} aparece más de una vez.')
        pesos[nombre] = numero(valor, f'Peso de {nombre}')
    return pesos


def crear_persona(datos):
    mujer = datos['sexo'] == 'mujer'
    embarazo = mujer and datos['embarazo']
    lactancia = mujer and datos['lactancia']
    return Persona(
        nombre=datos['nombre'].strip() or 'Persona demo',
        edad=numero(datos['edad'], 'Edad'),
        sexo=datos['sexo'],
        peso=numero(datos['peso'], 'Peso', estricto=True),
        altura=numero(datos['altura'], 'Talla', estricto=True),
        naf={'Baja': 'low', 'Moderada': 'moderate', 'Alta': 'high'}[datos['actividad']],
        exposicion_solar_suficiente=datos['solar'],
        padece_sudoracion_profusa=datos['sudoracion'],
        esta_embarazada=embarazo,
        esta_en_lactancia=lactancia,
        peso_preembarazo=numero(datos['peso_previo'], 'Peso previo', estricto=True)
        if embarazo or lactancia else None,
        mes_de_embarazo=numero(datos['mes_embarazo'], 'Mes de embarazo', minimo=1,
                              maximo=9, entero=True) if embarazo else None,
        mes_de_lactancia=numero(datos['mes_lactancia'], 'Mes de lactancia', minimo=1,
                               entero=True) if lactancia else None,
        reservas_de_energia_maternales=embarazo and datos['reservas'],
    )


def ejecutar_demo(persona, catalog_path, modo, presupuesto=15, pesos=None,
                  penalizaciones_min=None, penalizaciones_max=None):
    """Entrada sin interfaz, también útil para pruebas y otras aplicaciones."""
    consulta = preparar_consulta(persona)
    consulta.update(resultados=[], propuestas={})
    if modo == 'Solo requerimientos':
        return consulta
    if modo not in ('Comparar ambos', 'Costo mínimo', 'Con presupuesto'):
        raise ValueError(f'Modo desconocido: {modo}')
    ruta = Path(catalog_path).expanduser()
    if not ruta.is_file():
        raise ValueError(
            f'No se encontró el catálogo: {ruta}\n'
            'Genera data/processed/cba_catalog.pkl ejecutando '
            'python -m canasta_inteligente.application.cba_pipeline.'
        )
    catalog = load_catalog_pickle(ruta)
    validar_catalogo(catalog, consulta['escenarios_minimizacion'])
    consulta['cantidad_alimentos'] = len(catalog)
    consulta['catalogo'] = str(ruta.resolve())
    if modo in ('Comparar ambos', 'Costo mínimo'):
        resultados = minimizar_costo(catalog, consulta['escenarios_minimizacion'], penalizaciones_min)
        for resultado in resultados:
            resultado['tipo'] = 'Costo mínimo'
        optimos = [r for r in resultados if r['estado'] == 'Optimal']
        consulta['propuestas']['Costo mínimo'] = min(
            optimos, key=lambda r: (r['valor_objetivo'], r['costo_total_q']), default=None,
        )
        consulta['resultados'].extend(resultados)
    if modo in ('Comparar ambos', 'Con presupuesto'):
        resultados = maximizar_cobertura(
            catalog, consulta['escenarios_maximizacion'], presupuesto, pesos, penalizaciones_max,
        )
        for resultado in resultados:
            resultado['tipo'] = 'Con presupuesto'
        optimos = [r for r in resultados if r['estado'] == 'Optimal']
        consulta['propuestas']['Con presupuesto'] = max(
            optimos, key=lambda r: (r['valor_objetivo'], -r['costo_total_q']), default=None,
        )
        consulta['resultados'].extend(resultados)
        consulta['presupuesto_q'] = presupuesto
    return consulta


