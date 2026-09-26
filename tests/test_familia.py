from copy import deepcopy
import unittest
from unittest.mock import patch

import pandas as pd

import test_notebook_coverage as notebook_tests
from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE, load_catalog_pickle
from canasta_inteligente.application.optimizacion_dieta import minimizar_costo, maximizar_cobertura
from canasta_inteligente.domain.familia import Family, Familia
from canasta_inteligente.domain.persona import Persona


class PerfilPrueba(Persona):
    """Perfiles pequeños con soluciones conocidas, manteniendo la API de Persona."""

    def calcular_requerimientos(self):
        self.peso_para_calculos = self.peso
        return {'necesidad': self.peso, 'energia': {'ree': 100}}

    def escenarios(self, maximizar=False):
        limites = {'meta' if maximizar else 'min': getattr(self, 'necesidad', self.peso)}
        if hasattr(self, 'tope'):
            limites['max'] = self.tope
        if maximizar and hasattr(self, 'minimo_obligatorio'):
            limites['min'] = self.minimo_obligatorio
        return {'base': {'proteina_g': limites}}

    def calculo_canasta_diaria_costo_minimizado(self, catalog, *, penalizaciones=None):
        return minimizar_costo(catalog, self.escenarios(), penalizaciones)

    def calculo_canasta_diaria_maximizacion_cobertura_nutricional(
        self, catalog, presupuesto, *, pesos_nutrientes=None, penalizaciones=None,
    ):
        return maximizar_cobertura(catalog, self.escenarios(True), presupuesto, pesos_nutrientes, penalizaciones)


class FamilyTests(unittest.TestCase):
    def setUp(self):
        self.personas = [PerfilPrueba('Ana', 25, 'hombre', p, altura=1.7, naf='low') for p in (10, 30)]
        self.familia = Family(self.personas)
        self.catalog = [notebook_tests.CoverageNotebookTests.food('uno', {'proteina_g': 10})]

    def test_period_budget_and_quantities_preserve_daily_results_and_names(self):
        resultado = self.familia.calcular_canasta(dias=7, presupuesto=14, catalog=self.catalog)
        self.assertIs(Familia, Family)
        self.assertEqual(resultado['presupuesto_hogar_q'], 2)
        self.assertEqual(resultado['presupuesto_total_q'], 14)
        self.assertEqual([p['perfil_id'] for p in resultado['integrantes']], [1, 2])
        self.assertEqual([p['persona'].nombre for p in resultado['integrantes']], ['Ana', 'Ana'])
        self.assertEqual([p['presupuesto_q'] for p in resultado['integrantes']], [0.5, 1.5])
        self.assertEqual([p['proporcion_presupuesto'] for p in resultado['integrantes']], [0.25, 0.75])
        self.assertAlmostEqual(resultado['costo_diario_q'], 2)
        self.assertAlmostEqual(resultado['costo_total_q'], 14)
        self.assertAlmostEqual(resultado['canasta_diaria']['gramos'].sum(), 200)
        self.assertAlmostEqual(resultado['canasta_periodo']['gramos'].sum(), 1400)
        self.assertTrue(resultado['convergio'])
        self.assertEqual(resultado['historial_ajuste']['iteracion'].max(), 0)
        for p in resultado['integrantes']:
            self.assertAlmostEqual(p['propuesta_maximizacion']['cobertura_media_pct'], 50)
        pd.testing.assert_series_equal(
            resultado['reparto_periodo']['precio_q_por_gramo'],
            resultado['reparto_diario']['precio_q_por_gramo'],
        )
        self.assertTrue(all(p.peso_para_calculos is None for p in self.personas))

    def test_without_budget_only_minimizes_and_scales_cost(self):
        with patch.object(PerfilPrueba, 'calculo_canasta_diaria_maximizacion_cobertura_nutricional') as maximize:
            resultado = self.familia.calcular_canasta(dias=7, catalog=self.catalog)
        maximize.assert_not_called()
        self.assertEqual(resultado['etapa'], 'minimizacion')
        self.assertAlmostEqual(resultado['costo_diario_q'], 4)
        self.assertAlmostEqual(resultado['costo_total_q'], 28)
        self.assertIsNone(resultado['convergio'])
        self.assertTrue(resultado['historial_ajuste'].empty)
        self.assertEqual(resultado['estado'], 'Optimal')

    def test_person_settings_are_forwarded_and_calls_are_independent(self):
        resultado = self.familia.calcular_canasta(
            presupuesto=2, catalog=self.catalog, pesos_nutrientes={'proteina_g': 2},
            penalizaciones_min={'energia': 0}, penalizaciones_max={'colesterol': 0},
        )
        for p in resultado['integrantes']:
            self.assertEqual(p['propuesta_minimizacion']['penalizaciones']['energia'], 0)
            self.assertEqual(p['propuesta_maximizacion']['penalizaciones']['colesterol'], 0)
            self.assertEqual(p['propuesta_maximizacion']['pesos_nutrientes']['proteina_g'], 2)
        antes = resultado['canasta_diaria'].copy(deep=True)
        otro = self.familia.calcular_canasta(presupuesto=3, catalog=self.catalog)
        pd.testing.assert_frame_equal(resultado['canasta_diaria'], antes)
        self.assertNotEqual(otro['costo_total_q'], resultado['costo_total_q'])

    def test_validation_and_default_catalog(self):
        for dias in (0, -1, 1.5, True):
            with self.subTest(dias=dias), self.assertRaises(ValueError):
                self.familia.calcular_canasta(dias=dias, catalog=self.catalog)
        for presupuesto in (-1, float('nan'), float('inf'), 'incorrecto', True):
            with self.subTest(presupuesto=presupuesto), self.assertRaises(ValueError):
                self.familia.calcular_canasta(presupuesto=presupuesto, catalog=self.catalog)
        with self.assertRaises(ValueError):
            Family().calcular_canasta(catalog=self.catalog)
        with self.assertRaises(ValueError):
            self.familia.calcular_canasta(catalog=[])
        with patch('canasta_inteligente.application.cba_pipeline.load_catalog_pickle', return_value=self.catalog) as load:
            self.familia.calcular_canasta()
            load.assert_called_once_with()

    def test_missing_minimum_prevents_allocation_and_partial_purchase(self):
        self.personas[1].tope = 20
        resultado = self.familia.calcular_canasta(presupuesto=10, catalog=self.catalog)
        self.assertFalse(resultado['convergio'])
        self.assertIsNone(resultado['costo_minimizacion_hogar_q'])
        self.assertIsNone(resultado['canasta_periodo'])
        self.assertTrue(all(p['proporcion_presupuesto'] is None for p in resultado['integrantes']))
        with self.assertRaises(ValueError):
            self.familia.maximizar_canastas(resultado, self.catalog, 10)

    def test_zero_cost_and_zero_budget_are_distinct(self):
        cero = self.familia.calcular_canasta(presupuesto=0, catalog=self.catalog)
        self.assertEqual(cero['costo_total_q'], 0)
        self.assertTrue(cero['convergio'])
        for p in self.personas:
            p.necesidad = 0
        resultado = self.familia.calcular_canasta(presupuesto=10, catalog=self.catalog)
        self.assertEqual(resultado['costo_minimizacion_hogar_q'], 0)
        self.assertFalse(resultado['convergio'])
        self.assertIsNone(resultado['canasta_periodo'])

    def test_failed_maximization_preserves_minimum(self):
        self.personas[1].minimo_obligatorio = 1
        resultado = self.familia.calcular_canasta(presupuesto=0, catalog=self.catalog)
        self.assertIsNone(resultado['canasta_maximizacion'])
        self.assertIsNone(resultado['costo_total_q'])
        self.assertAlmostEqual(resultado['costo_minimizacion_hogar_q'], 4)
        self.assertFalse(resultado['convergio'])
        self.assertEqual(resultado['estado'], 'Sin propuesta completa')

    def test_custom_allocations_conserve_budget(self):
        consulta = self.familia.minimizar_canastas(self.catalog)
        for asignaciones in ([], [-1, 2], [float('nan'), 0], [float('inf'), 0], [2, 2], [1]):
            with self.subTest(asignaciones=asignaciones), self.assertRaises(ValueError):
                self.familia.maximizar_canastas(consulta, self.catalog, 1, asignaciones=asignaciones)

    def respuesta_simulada(self, cobertura, sin_solucion=False):
        def resolver(consulta, catalog, presupuesto, pesos=None, penalizaciones=None, asignaciones=None):
            asignaciones = [presupuesto / 2] * 2 if asignaciones is None else asignaciones
            integrantes = []
            for i, b in enumerate(asignaciones):
                c = cobertura(i, b)
                integrantes.append({
                    'perfil_id': i + 1, 'persona': self.personas[i],
                    'presupuesto_q': b, 'proporcion_presupuesto': 0.5,
                    'proporcion_presupuesto_final': b / presupuesto if presupuesto else None,
                    'propuesta_maximizacion': None if sin_solucion and i == 1 else {
                        'estado': 'Optimal', 'cobertura_ponderada_pct': c, 'cobertura_media_pct': c,
                    },
                })
            return {'integrantes': integrantes}
        return resolver

    def test_iteration_backtracks_and_improves_equity(self):
        respuesta = self.respuesta_simulada(lambda i, b: min(100, b * (10 if i == 0 else 5)))
        with patch.object(self.familia, 'maximizar_canastas', side_effect=respuesta):
            resultado = self.familia.equilibrar_presupuesto({}, [], 10, paso_fraccion=0.8, tolerancia_pp=0.05)
        self.assertTrue(resultado['convergio'])
        historia = resultado['historial_ajuste']
        grupos = historia.groupby('iteracion')
        self.assertTrue((grupos['presupuesto_q'].sum() - 10).abs().lt(1e-9).all())
        self.assertTrue(historia['presupuesto_q'].ge(0).all())
        self.assertTrue(grupos['desviacion_max_pp'].first().diff().dropna().lt(0).all())
        self.assertTrue(grupos['cobertura_pct'].min().diff().dropna().ge(-1e-6).all())
        self.assertTrue((~resultado['historial_intentos']['aceptado']).any())
        self.assertEqual(resultado['maximizacion_inicial']['integrantes'][0]['presupuesto_q'], 5)

    def test_plateau_and_iteration_limit_keep_best_solution(self):
        respuesta = self.respuesta_simulada(lambda i, b: 80 if i == 0 else 40)
        with patch.object(self.familia, 'maximizar_canastas', side_effect=respuesta):
            resultado = self.familia.equilibrar_presupuesto({}, [], 10)
            limite = self.familia.equilibrar_presupuesto({}, [], 10, max_iteraciones=0)
        self.assertFalse(resultado['convergio'])
        self.assertEqual(resultado['motivo_parada'], 'sin mejora con los ajustes probados')
        self.assertEqual(resultado['historial_ajuste']['iteracion'].max(), 0)
        self.assertEqual(limite['motivo_parada'], 'límite de iteraciones')

    def test_missing_initial_solution_does_not_become_zero_coverage(self):
        respuesta = self.respuesta_simulada(lambda i, b: 80, sin_solucion=True)
        with patch.object(self.familia, 'maximizar_canastas', side_effect=respuesta):
            resultado = self.familia.equilibrar_presupuesto({}, [], 10)
        self.assertFalse(resultado['convergio'])
        self.assertTrue(resultado['historial_intentos'].empty)
        self.assertTrue(resultado['historial_ajuste']['media_hogar_pct'].isna().all())

    def test_infeasible_trial_reduces_step(self):
        base = self.respuesta_simulada(lambda i, b: b * (10 if i == 0 else 5))
        def resolver(*args, **kwargs):
            resultado = base(*args, **kwargs)
            if resultado['integrantes'][0]['presupuesto_q'] < 3:
                resultado['integrantes'][0]['propuesta_maximizacion'] = None
            return resultado
        with patch.object(self.familia, 'maximizar_canastas', side_effect=resolver):
            resultado = self.familia.equilibrar_presupuesto({}, [], 10, paso_fraccion=0.8, tolerancia_pp=0.05)
        self.assertTrue(resultado['convergio'])
        self.assertTrue((~resultado['historial_intentos']['soluciones_completas']).any())

    @unittest.skipUnless(DEFAULT_PICKLE.exists(), 'Requiere catálogo procesado')
    def test_persona_matches_individual_notebook_models(self):
        notebook_tests.CoverageNotebookTests.setUpClass()
        ns = notebook_tests.CoverageNotebookTests.namespace
        persona = Persona('Prueba', 25, 'hombre', 90, altura=1.7, naf='low')
        catalog = load_catalog_pickle()
        requisitos = deepcopy(persona).calcular_requerimientos()
        original_min = ns['minimizar_costo'](catalog, ns['construir_escenarios'](requisitos))
        original_max = ns['maximizar_cobertura'](catalog, ns['construir_escenarios'](requisitos, maximizar=True), 15)
        actuales = persona.calculo_canasta_diaria_costo_minimizado(catalog)
        actuales += persona.calculo_canasta_diaria_maximizacion_cobertura_nutricional(catalog, 15)
        for actual, original in zip(actuales, original_min + original_max):
            self.assertEqual(actual['estado'], original['estado'])
            self.assertAlmostEqual(actual['costo_total_q'], original['costo_total_q'])
            self.assertAlmostEqual(actual['valor_objetivo'], original['valor_objetivo'])
            pd.testing.assert_series_equal(actual['aportes'], original['aportes'])
            pd.testing.assert_frame_equal(actual['alimentos'][original['alimentos'].columns], original['alimentos'])


if __name__ == '__main__':
    unittest.main()
