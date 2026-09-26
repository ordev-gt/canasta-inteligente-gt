"""Ejecuta por consola el mismo flujo de optimización que la demo de Tkinter."""

import argparse
from pathlib import Path
from pprint import pprint

import pandas as pd
from pulp import PulpSolverError

from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE
from canasta_inteligente.application.demo_dieta import (
    crear_persona, ejecutar_demo, leer_pesos, numero,
)
from canasta_inteligente.application.optimizacion_dieta import tabla_nutrientes


MODOS = {
    'comparar': 'Comparar ambos',
    'costo': 'Costo mínimo',
    'presupuesto': 'Con presupuesto',
    'requerimientos': 'Solo requerimientos',
}


def crear_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_PICKLE,
                        help='Catálogo procesado (.pkl).')
    parser.add_argument('--modo', choices=MODOS, default='comparar',
                        help='Modelo a ejecutar (predeterminado: comparar).')
    perfil = parser.add_argument_group('Perfil de la persona')
    perfil.add_argument('--nombre', default='Persona demo')
    perfil.add_argument('--edad', default='25', help='Edad en años.')
    perfil.add_argument('--sexo', choices=('hombre', 'mujer'), default='hombre')
    perfil.add_argument('--peso', default='70', help='Peso actual en kg.')
    perfil.add_argument('--altura', default='1.70', help='Talla en metros.')
    perfil.add_argument('--actividad', choices=('baja', 'moderada', 'alta'), default='baja')
    perfil.add_argument('--solar', action=argparse.BooleanOptionalAction, default=True,
                        help='Exposición solar suficiente; --no-solar para desactivar.')
    perfil.add_argument('--sudoracion', action='store_true', help='Sudoración profusa.')
    perfil.add_argument('--embarazo', action='store_true')
    perfil.add_argument('--mes-embarazo', default='6')
    perfil.add_argument('--lactancia', action='store_true')
    perfil.add_argument('--mes-lactancia', default='3')
    perfil.add_argument('--peso-previo', default='60', help='Peso previo en kg.')
    perfil.add_argument('--reservas', action='store_true', help='Reservas de energía maternales.')
    modelo = parser.add_argument_group('Presupuesto, pesos y penalizaciones')
    modelo.add_argument('--presupuesto', default='15', help='Presupuesto diario en quetzales.')
    modelo.add_argument('--peso-nutriente', action='append', default=[], metavar='NUTRIENTE=VALOR',
                        help='Peso para cobertura; se puede repetir con distintos nutrientes.')
    for prefijo in ('min', 'max'):
        modelo.add_argument(f'--{prefijo}-energia', default='1',
                            help=f'Penalización de energía para {prefijo}.')
        modelo.add_argument(f'--{prefijo}-colesterol', default='0.1',
                            help=f'Penalización de colesterol para {prefijo}.')
    parser.add_argument('--detalle', choices=('propuestas', 'todos'), default='propuestas',
                        help='Escenarios con tablas completas (predeterminado: propuestas).')
    parser.add_argument('--aporte-nutriente', metavar='NUTRIENTE',
                        help='Mostrar también el aporte por alimento de este nutriente.')
    return parser


def ejecutar_desde_argumentos(args):
    datos = vars(args).copy()
    datos['actividad'] = args.actividad.capitalize()
    if args.sexo == 'hombre' and (args.embarazo or args.lactancia):
        raise ValueError('Embarazo y lactancia requieren --sexo mujer.')
    persona = crear_persona(datos)
    opciones = {}
    if args.modo in ('comparar', 'costo'):
        opciones['penalizaciones_min'] = {
            n: numero(getattr(args, f'min_{n}'), f'Penalización costo: {n}')
            for n in ('energia', 'colesterol')
        }
    if args.modo in ('comparar', 'presupuesto'):
        opciones['presupuesto'] = numero(args.presupuesto, 'Presupuesto')
        opciones['pesos'] = leer_pesos('\n'.join(args.peso_nutriente))
        opciones['penalizaciones_max'] = {
            n: numero(getattr(args, f'max_{n}'), f'Penalización cobertura: {n}')
            for n in ('energia', 'colesterol')
        }

    # Coloca un breakpoint aquí para entrar en el flujo y en los modelos con F11.
    consulta = ejecutar_demo(persona, args.catalog, MODOS[args.modo], **opciones)
    if args.aporte_nutriente and consulta['resultados']:
        nutrientes = consulta['resultados'][0]['restricciones']
        if args.aporte_nutriente not in nutrientes:
            raise ValueError(f'Nutriente desconocido: {args.aporte_nutriente}. '
                             f'Opciones: {", ".join(nutrientes)}')
    return consulta


def mostrar_tabla(titulo, tabla):
    print(f'\n{titulo}')
    print(tabla.to_string(index=False, float_format=lambda v: f'{v:.4f}', na_rep='—')
          if not tabla.empty else 'Sin datos.')


def mostrar_consulta(consulta, detalle='propuestas', aporte_nutriente=None):
    persona = consulta['persona']
    print(f'\n{persona.nombre} | {persona.sexo} | {persona.edad:g} años | '
          f'{persona.peso:g} kg | {persona.altura:g} m | Actividad: {persona.naf}')
    print(f'Peso usado en los cálculos: {persona.peso_para_calculos:.2f} kg')
    print(f"Energía requerida: {consulta['requerimientos']['energia']['ree']:.2f} kcal/día")
    print('\nEvaluación del peso')
    pprint(consulta['evaluacion_peso'], sort_dicts=False)
    print('\nRequerimientos diarios')
    pprint(consulta['requerimientos'], sort_dicts=False)
    if not consulta['resultados']:
        return

    print(f"\nCatálogo: {consulta['catalogo']} ({consulta['cantidad_alimentos']} alimentos)")
    if 'presupuesto_q' in consulta:
        print(f"Presupuesto diario: Q {consulta['presupuesto_q']:.2f}")
    resumen = []
    for resultado in consulta['resultados']:
        propuesta = consulta['propuestas'].get(resultado['tipo']) is resultado
        resumen.append({
            'propuesta': '*' if propuesta else '', 'modelo': resultado['tipo'],
            'escenario': resultado['escenario'], 'estado': resultado['estado'],
            'costo_Q': resultado['costo_total_q'], 'objetivo': resultado['valor_objetivo'],
            'penalizacion': resultado['penalizacion_total'],
            'cobertura_ponderada_%': resultado.get('cobertura_ponderada_pct'),
        })
    mostrar_tabla('Escenarios (* propuesta según la función objetivo de cada modelo)',
                  pd.DataFrame(resumen))
    for tipo, propuesta in consulta['propuestas'].items():
        if propuesta is None:
            print(f'{tipo}: no hay una propuesta con solución óptima.')
    for resultado in consulta['resultados']:
        propuesta = consulta['propuestas'].get(resultado['tipo']) is resultado
        if detalle != 'todos' and not propuesta:
            continue
        print(f"\n{resultado['tipo']} / {resultado['escenario']} — {resultado['estado']}")
        if resultado['estado'] != 'Optimal':
            print('Sin solución óptima; no hay cantidades ni costos válidos.')
            continue
        alimentos = resultado['alimentos']
        mostrar_tabla('Alimentos (cantidades diarias compradas)',
                      alimentos.loc[alimentos['porciones_100g'] > 1e-6])
        mostrar_tabla('Nutrientes', tabla_nutrientes(resultado))
        mostrar_tabla('Diagnóstico de restricciones', resultado['diagnostico_restricciones'])
        if aporte_nutriente:
            aportes = resultado['aportes_por_alimento']
            mostrar_tabla(f'Aporte por alimento: {aporte_nutriente}',
                          aportes.loc[aportes['nutriente'] == aporte_nutriente]
                          .sort_values('aporte', ascending=False))
    print('\nEl costo de alimentos y las penalizaciones se muestran por separado. '
          'Los aportes incorporan la fracción comestible. '
          'La cobertura media puede ocultar déficits individuales.')


def main(argv=None):
    parser = crear_parser()
    args = parser.parse_args(argv)
    try:
        consulta = ejecutar_desde_argumentos(args)
    except (ValueError, OSError, PulpSolverError) as error:
        parser.exit(2, f'Error: {error}\n')
    mostrar_consulta(consulta, args.detalle, args.aporte_nutriente)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
