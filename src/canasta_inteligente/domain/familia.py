"""Canastas familiares a partir de la optimización individual de Persona."""

from copy import deepcopy
from dataclasses import dataclass, field
from math import isfinite

import pandas as pd

from .persona import Persona


@dataclass
class Family:
    """Hogar que reúne canastas individuales y equilibra su presupuesto diario."""

    members: list[Persona] = field(default_factory=list)

    def add_member(self, person: Persona) -> None:
        self.members.append(person)

    def remove_member(self, person: Persona) -> None:
        self.members.remove(person)

    def calcular_canasta(
        self, dias=1, presupuesto=None, *, catalog=None, alimentos_a_excluir= None, limite_diario_de_alimentos_en_gramos=None, pesos_nutrientes=None,
        penalizaciones_min=None, penalizaciones_max=None, tolerancia_pp=0.5,
        paso_fraccion=0.01, max_iteraciones=30, minimo_ajuste_q=0.001, max_reintentos=8,
        metrica='cobertura_ponderada_pct', mostrar_progreso=False,
    ):
        """Calcula la compra y el reparto del hogar para un período.

        presupuesto es el TOTAL en Q para todos los días e integrantes.
        Sin presupuesto devuelve la minimización; con presupuesto ejecuta también
        la maximización individual y el ajuste de equidad. Los escenarios y el
        historial conservan unidades diarias; canasta_periodo y reparto_periodo
        multiplican únicamente cantidades y costos por dias. Los perfiles
        originales no se modifican y los nombres repetidos conservan su identidad.
        """
        if isinstance(dias, bool) or not isinstance(dias, int) or dias < 1:
            raise ValueError('dias debe ser un entero positivo.')
        if not self.members:
            raise ValueError('La familia debe tener al menos un integrante.')
        if presupuesto is not None:
            if isinstance(presupuesto, bool):
                raise ValueError('El presupuesto total debe ser finito y no negativo.')
            try:
                presupuesto = float(presupuesto)
            except (TypeError, ValueError):
                raise ValueError('El presupuesto total debe ser numérico.') from None
            if not isfinite(presupuesto) or presupuesto < 0:
                raise ValueError('El presupuesto total debe ser finito y no negativo.')
        if catalog is None:
            # Importación local para no crear un ciclo entre dominio y cargadores.
            from ..application.cba_pipeline import load_catalog_pickle
            catalog = load_catalog_pickle()
        else:
            catalog = deepcopy(catalog)
        if not len(catalog):
            raise ValueError('El catálogo está vacío.')
        limites = dict(limite_diario_de_alimentos_en_gramos or {})
        ids = {food.id for food in catalog}
        desconocidos = (set(limites) | set(alimentos_a_excluir or [])) - ids
        if desconocidos:
            raise ValueError(f'Alimentos desconocidos: {sorted(desconocidos)}')
        for food_id, gramos in limites.items():
            if isinstance(gramos, bool) or not isinstance(gramos, (int, float)) or not isfinite(gramos) or gramos < 0:
                raise ValueError(f'Límite diario inválido para {food_id}.')
        if alimentos_a_excluir:
            for _alimento_id in alimentos_a_excluir:
                catalog.remove(_alimento_id)
                limites.pop(_alimento_id, None)
        if not len(catalog):
            raise ValueError('Debe quedar al menos un alimento disponible.')

        
        consulta = self.minimizar_canastas(catalog, limites, penalizaciones_min)
        consulta['resumen_minimizacion'] = self.resumir_canastas(consulta, 'minimizacion')
        etapa = 'minimizacion' if presupuesto is None else 'maximizacion'
        presupuesto_diario = presupuesto / dias if presupuesto is not None else None
        if presupuesto is not None:
            if any(p['proporcion_presupuesto'] is None for p in consulta['integrantes']):
                consulta.update(
                    convergio=False, motivo_parada='minimización incompleta o costo total no positivo',
                    presupuesto_hogar_q=presupuesto_diario,
                )
            else:
                consulta = self.equilibrar_presupuesto(
                    consulta, catalog, presupuesto_diario, pesos_nutrientes, penalizaciones_max,
                    tolerancia_pp=tolerancia_pp, paso_fraccion=paso_fraccion,
                    max_iteraciones=max_iteraciones, minimo_ajuste_q=minimo_ajuste_q,
                    max_reintentos=max_reintentos, metrica=metrica, mostrar_progreso=mostrar_progreso,
                )
        else:
            consulta.update(convergio=None, motivo_parada='sin presupuesto: solo minimización')
        consulta.setdefault('historial_ajuste', pd.DataFrame())
        consulta.setdefault('historial_intentos', pd.DataFrame())
        consulta.setdefault('maximizacion_inicial', None)
        consulta['comparacion_repartos'] = self._comparar_repartos(consulta['historial_ajuste'])
        consulta['resumen_maximizacion'] = self.resumir_canastas(consulta, 'maximizacion')
        compra = consulta[f'canasta_{etapa}']
        reparto = consulta[f'reparto_{etapa}']
        costo = consulta[f'costo_{etapa}_hogar_q']
        consulta.update(
            dias=dias, presupuesto_total_q=presupuesto, etapa=etapa,
            estado='Optimal' if compra is not None else 'Sin propuesta completa',
            canasta_diaria=compra, reparto_diario=reparto,
            canasta_periodo=self._escalar_periodo(compra, dias),
            reparto_periodo=self._escalar_periodo(reparto, dias),
            costo_diario_q=costo, costo_total_q=costo * dias if costo is not None else None,
            costo_minimizacion_periodo_q=consulta['costo_minimizacion_hogar_q'] * dias
            if consulta['costo_minimizacion_hogar_q'] is not None else None,
        )
        return consulta


    @staticmethod
    def _escalar_periodo(tabla, dias):
        if tabla is None:
            return None
        resultado = tabla.copy(deep=True)
        for columna in ('porciones_100g', 'gramos', 'costo_q'):
            resultado[columna] = resultado[columna] * dias
        return resultado


    @staticmethod
    def _comparar_repartos(historial):
        if historial.empty:
            return pd.DataFrame()
        inicial = historial.loc[historial['iteracion'] == 0,
                               ['perfil_id', 'persona', 'presupuesto_q', 'cobertura_pct']].rename(
            columns={'presupuesto_q': 'presupuesto_inicial_q', 'cobertura_pct': 'cobertura_inicial_pct'})
        final = historial.loc[historial['iteracion'] == historial['iteracion'].max(),
                             ['perfil_id', 'presupuesto_q', 'cobertura_pct']].rename(
            columns={'presupuesto_q': 'presupuesto_final_q', 'cobertura_pct': 'cobertura_final_pct'})
        return inicial.merge(final, on='perfil_id', validate='one_to_one')


    @staticmethod
    def resumir_canastas(consulta, etapa):
        if etapa not in ('minimizacion', 'maximizacion'):
            raise ValueError('Etapa inválida.')
        filas = []
        for p in consulta['integrantes']:
            r = p[f'propuesta_{etapa}']
            filas.append({
                'perfil_id': p['perfil_id'], 'persona': p['persona'].nombre,
                'peso_para_calculos_kg': p['persona'].peso_para_calculos,
                'energia_requerida_kcal': p['requerimientos']['energia']['ree'],
                'escenario_propuesto': r['escenario'] if r else None,
                'estado': 'Optimal' if r else 'Sin propuesta óptima',
                'costo_alimentos_q': r['costo_total_q'] if r else None,
                'participacion_inicial_pct': 100 * p['proporcion_presupuesto']
                if p['proporcion_presupuesto'] is not None else None,
                'participacion_final_pct': 100 * p['proporcion_presupuesto_final']
                if p.get('proporcion_presupuesto_final') is not None else None,
                'presupuesto_asignado_q': p['presupuesto_q'],
                'cobertura_ponderada_pct': r.get('cobertura_ponderada_pct') if r else None,
            })
        return pd.DataFrame(filas)


    def _tablas_compra(self, integrantes, etapa):
        # Una canasta familiar solo se reporta si TODOS tienen una propuesta óptima.
        propuestas = [p[f'propuesta_{etapa}'] for p in integrantes]
        if not propuestas or any(r is None for r in propuestas):
            return None, None
        tablas = [
            r['alimentos'].assign(perfil_id=p['perfil_id'], persona=p['persona'].nombre)
            for p, r in zip(integrantes, propuestas)
        ]
        reparto = pd.concat(tablas, ignore_index=True)
        # Sumar antes de filtrar: conservar las cantidades pequeñas en el total.
        compra = reparto.groupby(['alimento_id', 'alimento'], as_index=False)[
            ['porciones_100g', 'gramos', 'costo_q']
        ].sum()
        if 'nombre_incap' in reparto.columns:
            nombres = reparto.drop_duplicates('alimento_id').set_index('alimento_id')['nombre_incap']
            compra.insert(2, 'nombre_incap', compra['alimento_id'].map(nombres))
        return reparto.loc[reparto['gramos'] > 0].copy(), compra.loc[compra['gramos'] > 0].copy()

    def minimizar_canastas(self, catalog, limite_de_alimentos_diario=None, penalizaciones=None):
        if not self.members:
            raise ValueError('Ingresa al menos un integrante.')
        integrantes = []
        for indice, original in enumerate(self.members, 1):
            persona = deepcopy(original)
            requisitos = persona.calcular_requerimientos()
            opciones = {'limite_de_alimentos_diario': limite_de_alimentos_diario} if limite_de_alimentos_diario else {}
            resultados = persona.calculo_canasta_diaria_costo_minimizado(catalog, penalizaciones=penalizaciones, **opciones)
            escenarios = {r['escenario']: r['restricciones'] for r in resultados}
            optimos = [r for r in resultados if r['estado'] == 'Optimal']
            # Mismo criterio del experimento: costo + penalizaciones; desempate por costo.
            propuesta = min(optimos, key=lambda r: (r['valor_objetivo'], r['costo_total_q']), default=None)
            integrantes.append({
                'perfil_id': indice, 'persona': persona, 'requerimientos': requisitos,
                'escenarios_minimizacion': escenarios,
                'resultados_minimizacion': resultados, 'propuesta_minimizacion': propuesta,
                'proporcion_presupuesto': None, 'presupuesto_q': None,
                'resultados_maximizacion': [], 'propuesta_maximizacion': None,
            })
        completa = all(p['propuesta_minimizacion'] is not None for p in integrantes)
        total = sum(p['propuesta_minimizacion']['costo_total_q'] for p in integrantes) if completa else None
        if total is not None and isfinite(total) and total > 0:
            for p in integrantes:
                p['proporcion_presupuesto'] = p['propuesta_minimizacion']['costo_total_q'] / total
        reparto, compra = self._tablas_compra(integrantes, 'minimizacion')
        return {
            'limites_diarios': dict(limite_de_alimentos_diario or {}),
            'integrantes': integrantes, 'costo_minimizacion_hogar_q': total,
            'presupuesto_hogar_q': None, 'reparto_minimizacion': reparto,
            'canasta_minimizacion': compra, 'reparto_maximizacion': None,
            'canasta_maximizacion': None, 'costo_maximizacion_hogar_q': None,
        }

    def maximizar_canastas(self, consulta, catalog, presupuesto, pesos=None, penalizaciones=None, asignaciones=None):
        if not isfinite(presupuesto) or presupuesto < 0:
            raise ValueError('El presupuesto familiar debe ser finito y no negativo.')
        if not consulta['integrantes'] or any(p['proporcion_presupuesto'] is None for p in consulta['integrantes']):
            raise ValueError('No se puede repartir: falta una solución mínima óptima o el costo total no es positivo.')
        if asignaciones is None:
            asignaciones = [presupuesto * p['proporcion_presupuesto'] for p in consulta['integrantes']]
        asignaciones = list(asignaciones)
        if (len(asignaciones) != len(consulta['integrantes'])
                or any(not isfinite(b) or b < 0 for b in asignaciones)
                or abs(sum(asignaciones) - presupuesto) > 1e-8 * max(1, presupuesto)):
            raise ValueError('Las asignaciones deben ser no negativas y sumar el presupuesto del hogar.')
        actualizada = dict(consulta)
        integrantes = []
        for anterior, asignacion in zip(consulta['integrantes'], asignaciones):
            p = dict(anterior)
            p['persona'] = deepcopy(anterior['persona'])
            opciones = {'limite_de_alimentos_diario': consulta['limites_diarios']} if consulta.get('limites_diarios') else {}
            resultados = p['persona'].calculo_canasta_diaria_maximizacion_cobertura_nutricional(
                catalog, asignacion, pesos_nutrientes=pesos, penalizaciones=penalizaciones,
                **opciones,
            )
            escenarios = {r['escenario']: r['restricciones'] for r in resultados}
            optimos = [r for r in resultados if r['estado'] == 'Optimal']
            propuesta = max(optimos, key=lambda r: (r['valor_objetivo'], -r['costo_total_q']), default=None)
            p.update(presupuesto_q=asignacion, escenarios_maximizacion=escenarios,
                     proporcion_presupuesto_final=asignacion / presupuesto if presupuesto > 0 else None,
                     resultados_maximizacion=resultados, propuesta_maximizacion=propuesta)
            integrantes.append(p)
        reparto, compra = self._tablas_compra(integrantes, 'maximizacion')
        actualizada.update(
            integrantes=integrantes, presupuesto_hogar_q=presupuesto,
            reparto_maximizacion=reparto, canasta_maximizacion=compra,
            costo_maximizacion_hogar_q=sum(p['propuesta_maximizacion']['costo_total_q'] for p in integrantes)
            if compra is not None else None,
        )
        return actualizada

    def _estadisticas_cobertura(self, consulta, metrica):
        propuestas = [p['propuesta_maximizacion'] for p in consulta['integrantes']]
        if not propuestas or any(r is None or r['estado'] != 'Optimal' for r in propuestas):
            return None
        coberturas = [r[metrica] for r in propuestas]
        if any(c is None or not isfinite(c) for c in coberturas):
            return None
        media = sum(coberturas) / len(coberturas)
        return {
            'coberturas': coberturas, 'media_pct': media, 'minima_pct': min(coberturas),
            'brecha_pp': max(coberturas) - min(coberturas),
            'desviacion_max_pp': max(abs(c - media) for c in coberturas),
        }

    def _registrar_iteracion(self, historial, consulta, iteracion, metrica):
        estadisticas = self._estadisticas_cobertura(consulta, metrica)
        for p in consulta['integrantes']:
            propuesta = p['propuesta_maximizacion']
            cobertura = propuesta[metrica] if propuesta is not None else None
            media = estadisticas['media_pct'] if estadisticas is not None else None
            historial.append({
                'iteracion': iteracion, 'perfil_id': p['perfil_id'], 'persona': p['persona'].nombre,
                'presupuesto_q': p['presupuesto_q'],
                'participacion_inicial_pct': 100 * p['proporcion_presupuesto'],
                'participacion_actual_pct': 100 * p['proporcion_presupuesto_final']
                if p['proporcion_presupuesto_final'] is not None else None,
                'cobertura_pct': cobertura, 'media_hogar_pct': media,
                'distancia_a_media_pp': cobertura - media if media is not None else None,
                'desviacion_max_pp': estadisticas['desviacion_max_pp'] if estadisticas else None,
                'brecha_pp': estadisticas['brecha_pp'] if estadisticas else None,
            })

    def equilibrar_presupuesto(self, consulta, catalog, presupuesto, pesos=None, penalizaciones=None,
                                     tolerancia_pp=0.5, paso_fraccion=0.01, max_iteraciones=30,
                                     minimo_ajuste_q=0.001, max_reintentos=8,
                                     metrica='cobertura_ponderada_pct', mostrar_progreso=False):
        if metrica not in ('cobertura_ponderada_pct', 'cobertura_media_pct'):
            raise ValueError('Selecciona cobertura_ponderada_pct o cobertura_media_pct.')
        if (not isfinite(tolerancia_pp) or tolerancia_pp < 0
                or not isfinite(paso_fraccion) or not 0 < paso_fraccion <= 1
                or not isfinite(minimo_ajuste_q) or minimo_ajuste_q <= 0
                or not isinstance(max_iteraciones, int) or max_iteraciones < 0
                or not isinstance(max_reintentos, int) or max_reintentos < 1):
            raise ValueError('Revisa la tolerancia, el paso y los límites de iteración.')
        # Iteración 0: distribución original según los costos individuales.
        inicial = self.maximizar_canastas(consulta, catalog, presupuesto, pesos, penalizaciones)
        actual = inicial
        historial, intentos = [], []
        self._registrar_iteracion(historial, actual, 0, metrica)
        estadisticas = self._estadisticas_cobertura(actual, metrica)
        motivo = 'límite de iteraciones'
        if estadisticas is None:
            motivo = 'sin propuesta óptima para todos con el reparto inicial'
        else:
            for iteracion in range(1, max_iteraciones + 1):
                if estadisticas['desviacion_max_pp'] <= tolerancia_pp:
                    motivo = 'tolerancia alcanzada'
                    break
                media = estadisticas['media_pct']
                coberturas = estadisticas['coberturas']
                presupuestos = [p['presupuesto_q'] for p in actual['integrantes']]
                donantes = [max(0.0, c - media) if b > 0 else 0.0
                            for c, b in zip(coberturas, presupuestos)]
                receptores = [max(0.0, media - c) for c in coberturas]
                if sum(donantes) <= 1e-12 or sum(receptores) <= 1e-12:
                    motivo = 'sin presupuesto transferible'
                    break
                donantes = [d / sum(donantes) for d in donantes]
                receptores = [r / sum(receptores) for r in receptores]
                # Transferir como máximo el paso configurado y un 25 % de cada presupuesto donante.
                transferencia = min(presupuesto * paso_fraccion,
                                    min(0.25 * b / d for b, d in zip(presupuestos, donantes) if d > 0))
                aceptado = False
                for intento in range(max_reintentos):
                    paso = transferencia / (2 ** intento)
                    if paso < minimo_ajuste_q:
                        break
                    asignaciones = [b + paso * (r - d)
                                    for b, r, d in zip(presupuestos, receptores, donantes)]
                    # Corregir únicamente el residuo de punto flotante; nunca redondear a centavos aquí.
                    receptor = max(range(len(receptores)), key=receptores.__getitem__)
                    asignaciones[receptor] += presupuesto - sum(asignaciones)
                    candidato = self.maximizar_canastas(consulta, catalog, presupuesto, pesos, penalizaciones, asignaciones)
                    nuevas = self._estadisticas_cobertura(candidato, metrica)
                    # Reducir la dispersión sin empeorar la cobertura del integrante peor cubierto.
                    mejora = nuevas is not None and (
                        nuevas['desviacion_max_pp'] < estadisticas['desviacion_max_pp'] - 1e-6
                        and nuevas['minima_pct'] >= estadisticas['minima_pct'] - 1e-6
                    )
                    intentos.append({
                        'iteracion': iteracion, 'intento': intento + 1, 'transferencia_q': paso,
                        'aceptado': mejora, 'soluciones_completas': nuevas is not None,
                        'media_pct': nuevas['media_pct'] if nuevas else None,
                        'desviacion_max_pp': nuevas['desviacion_max_pp'] if nuevas else None,
                    })
                    if mejora:
                        actual, estadisticas = candidato, nuevas
                        self._registrar_iteracion(historial, actual, iteracion, metrica)
                        aceptado = True
                        if mostrar_progreso:
                            print(f"Iteración {iteracion}: media {nuevas['media_pct']:.2f} %; "
                                  f"desviación máxima {nuevas['desviacion_max_pp']:.3f} puntos; "
                                  f"transferencia Q {paso:.4f}")
                        break
                if not aceptado:
                    motivo = 'sin mejora con los ajustes probados'
                    break
            if estadisticas['desviacion_max_pp'] <= tolerancia_pp:
                motivo = 'tolerancia alcanzada'
        resultado = dict(actual)
        resultado.update(
            maximizacion_inicial=inicial, historial_ajuste=pd.DataFrame(historial),
            historial_intentos=pd.DataFrame(intentos), motivo_parada=motivo,
            convergio=estadisticas is not None and estadisticas['desviacion_max_pp'] <= tolerancia_pp,
            metrica_equidad=metrica, tolerancia_pp=tolerancia_pp,
        )
        return resultado


# Alias en español.
Familia = Family
    
