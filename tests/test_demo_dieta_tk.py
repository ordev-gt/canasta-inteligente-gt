"""Regresión del traslado y pruebas del flujo de la demo.

RUN_TK_TESTS=1 habilita la prueba de widgets con una ventana oculta.
"""

import os
from copy import deepcopy
import time
import unittest
from unittest.mock import patch

import pandas as pd

import test_notebook_coverage as notebook_tests
from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE, load_catalog_pickle
from canasta_inteligente.application.demo_dieta_tk import (
    DemoDieta, crear_persona, ejecutar_demo, leer_pesos, numero,
)
from canasta_inteligente.application.optimizacion_dieta import (
    minimizar_costo, tabla_nutrientes, validar_catalogo,
)
from canasta_inteligente.domain.persona import Persona
from canasta_inteligente.nutrition.service import evaluacion_de_requerimientos_diarios


def perfil():
    return Persona('Demo', 25, 'hombre', 70, naf='low', altura=1.70)


class DemoInputTests(unittest.TestCase):
    def test_evaluated_weight_drives_energy_and_dependent_requirements(self):
        for peso, peso_evaluado, energia in (
            (50, 50, 2239.8275), (70, 70, 2706.5945),
            (80, 63.58, 2556.762293), (90, 63.58, 2556.762293),
        ):
            with self.subTest(peso=peso):
                persona = Persona('Comparación', 25, 'hombre', peso, altura=1.70, naf='low')
                # Un valor previo no debe evitar la reevaluación del peso actual.
                persona.peso_para_calculos = 999
                consulta = ejecutar_demo(persona, '', 'Solo requerimientos')
                requisitos = consulta['requerimientos']
                self.assertEqual(requisitos, evaluacion_de_requerimientos_diarios(deepcopy(persona)))
                self.assertAlmostEqual(consulta['evaluacion_peso']['peso_para_calculos'], peso_evaluado)
                self.assertAlmostEqual(consulta['persona'].peso_para_calculos, peso_evaluado)
                self.assertAlmostEqual(requisitos['energia']['ree'], energia)
                self.assertAlmostEqual(requisitos['proteina']['rdd_dieta_mixta'], 1.12 * peso_evaluado)
                self.assertAlmostEqual(requisitos['carbohidratos']['rdd_min'], 0.55 * energia / 4)
                self.assertAlmostEqual(requisitos['lipidos']['total_min'], 0.2 * energia / 9)
                self.assertAlmostEqual(requisitos['azucar']['rdd'], 0.1 * energia / 4)
                self.assertAlmostEqual(requisitos['fibra']['rdd'], 12 * energia / 1000)
                for clave in ('escenarios_minimizacion', 'escenarios_maximizacion'):
                    for escenario in consulta[clave].values():
                        self.assertAlmostEqual(escenario['energia_kcal']['ct'], energia)
                self.assertEqual(persona.peso_para_calculos, 999)

    def test_food_contributions_use_selected_amount_and_edible_fraction(self):
        food = notebook_tests.CoverageNotebookTests.food
        foods = [
            food('carne', {'proteina_g': 10, 'calcio_mg': 0, 'vitamina_d_mcg': 0},
                 fraction=0.5, meat=True),
            food('otro', {'proteina_g': 0, 'calcio_mg': 10, 'vitamina_d_mcg': 0}),
        ]
        resultado = minimizar_costo(foods, {'base': {
            'proteina_g': {'min': 10}, 'calcio_mg': {'min': 5},
            'vitamina_d_mcg': {'max': 50}, 'carne_g': {'min': 0},
        }})[0]
        datos = resultado['aportes_por_alimento'].set_index(['alimento_id', 'nutriente'])
        carne = datos.loc[('carne', 'proteina_g')]
        self.assertAlmostEqual(carne['gramos_comprados'], 200)
        self.assertAlmostEqual(carne['gramos_comestibles'], 100)
        self.assertAlmostEqual(carne['aporte'], 10)
        self.assertAlmostEqual(carne['porcentaje_del_total'], 100)
        self.assertEqual(carne['unidad'], 'g')
        self.assertAlmostEqual(datos.loc[('carne', 'carne_g'), 'aporte'], 100)
        self.assertAlmostEqual(datos.loc[('otro', 'calcio_mg'), 'aporte'], 5)
        self.assertEqual(datos.loc[('otro', 'calcio_mg'), 'unidad'], 'mg')
        self.assertTrue(pd.isna(datos.loc[('carne', 'vitamina_d_mcg'), 'porcentaje_del_total']))
        resultado['variables']['carne'].varValue = 999
        self.assertAlmostEqual(datos.loc[('carne', 'proteina_g'), 'aporte'], 10)

    def test_finite_numbers_and_weights(self):
        self.assertEqual(numero('1,70', 'Talla'), 1.7)
        for texto in ('nan', 'inf', '-1', 'no'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                numero(texto, 'Presupuesto')
        self.assertEqual(leer_pesos('vitamina_d_mcg = 0,25\n\nfibra_dietetica_g = 2'),
                         {'vitamina_d_mcg': 0.25, 'fibra_dietetica_g': 2})
        for texto in ('a', '=1', 'a=-1', 'a=1\na=2'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                leer_pesos(texto)

    def test_maternal_profile_and_inactive_fields(self):
        datos = dict(nombre='Ana', edad='28', sexo='mujer', peso='65', altura='1,65',
                     actividad='Moderada', solar=True, sudoracion=False, embarazo=True,
                     lactancia=False, peso_previo='60', mes_embarazo='6', mes_lactancia='', reservas=True)
        persona = crear_persona(datos)
        self.assertEqual(persona.mes_de_embarazo, 6)
        self.assertEqual(persona.peso_preembarazo, 60)
        self.assertTrue(persona.reservas_de_energia_maternales)
        datos['mes_embarazo'] = '10'
        with self.assertRaises(ValueError):
            crear_persona(datos)
        datos['sexo'] = 'hombre'
        self.assertFalse(crear_persona(datos).esta_embarazada)

    def test_requirements_work_without_catalog_and_do_not_mutate_person(self):
        persona = perfil()
        original = vars(persona).copy()
        consulta = ejecutar_demo(persona, 'missing.pkl', 'Solo requerimientos')
        self.assertIn('energia', consulta['requerimientos'])
        self.assertEqual(vars(persona), original)
        self.assertEqual(consulta['resultados'], [])
        with self.assertRaisesRegex(ValueError, 'No se encontró'):
            ejecutar_demo(persona, 'missing.pkl', 'Costo mínimo')

    def test_incomplete_catalog_is_not_silently_zero_filled(self):
        food = notebook_tests.CoverageNotebookTests.food('incompleto', {'proteina_g': 10})
        with self.assertRaisesRegex(ValueError, 'vitamina_c_mg'):
            validar_catalogo([food], {'base': {'vitamina_c_mg': {'min': 75}}})


@unittest.skipUnless(DEFAULT_PICKLE.is_file(), 'Requiere el catálogo procesado local')
class DemoRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.consulta = ejecutar_demo(perfil(), DEFAULT_PICKLE, 'Comparar ambos')
        notebook_tests.CoverageNotebookTests.setUpClass()
        cls.notebook = notebook_tests.CoverageNotebookTests.namespace

    def test_all_eight_results_match_notebook(self):
        catalog = load_catalog_pickle()
        requerimientos = self.consulta['requerimientos']
        construir = self.notebook['construir_escenarios']
        originales = self.notebook['minimizar_costo'](catalog, construir(requerimientos))
        originales += self.notebook['maximizar_cobertura'](
            catalog, construir(requerimientos, maximizar=True), 15,
        )
        self.assertEqual(len(self.consulta['resultados']), 8)
        for actual, original in zip(self.consulta['resultados'], originales):
            with self.subTest(tipo=actual['tipo'], escenario=actual['escenario']):
                self.assertEqual(actual['estado'], original['estado'])
                self.assertAlmostEqual(actual['costo_total_q'], original['costo_total_q'])
                self.assertAlmostEqual(actual['valor_objetivo'], original['valor_objetivo'])
                pd.testing.assert_frame_equal(actual['alimentos'][original['alimentos'].columns], original['alimentos'])
                for fila in actual['alimentos'].itertuples():
                    self.assertEqual(fila.nombre_incap, catalog.get(fila.alimento_id).nutrition.incap_name)
                pd.testing.assert_series_equal(actual['aportes'], original['aportes'])
                desglose = actual['aportes_por_alimento']
                totales = desglose.groupby('nutriente')['aporte'].sum()
                for nutriente, aporte in actual['aportes'].items():
                    self.assertAlmostEqual(totales[nutriente], aporte)
                if 'coberturas' in actual:
                    pd.testing.assert_frame_equal(actual['coberturas'], original['coberturas'])
                    self.assertLessEqual(actual['costo_total_q'], 15 + 1e-5)
                self.assertTrue(all(c.valid(1e-3) for c in actual['modelo'].constraints.values()))

    def test_report_converts_meat_limits_to_grams(self):
        resultado = self.consulta['resultados'][1]
        fila = tabla_nutrientes(resultado).set_index('nutriente').loc['carne_g']
        self.assertEqual(fila['minimo'], 30)
        self.assertEqual(fila['maximo'], 90)
        self.assertGreaterEqual(fila['aporte'], 30 - 1e-4)

    def test_zero_budget_and_infeasible_scenarios(self):
        consulta = ejecutar_demo(perfil(), DEFAULT_PICKLE, 'Con presupuesto', presupuesto=0)
        self.assertEqual(consulta['resultados'][0]['estado'], 'Optimal')
        self.assertAlmostEqual(consulta['resultados'][0]['costo_total_q'], 0)
        for resultado in consulta['resultados'][1:]:
            self.assertEqual(resultado['estado'], 'Infeasible')
            self.assertIsNone(resultado['costo_total_q'])
            self.assertTrue(tabla_nutrientes(resultado).empty)
            self.assertTrue(resultado['aportes_por_alimento'].empty)


@unittest.skipUnless(os.environ.get('RUN_TK_TESTS') == '1' and DEFAULT_PICKLE.is_file(),
                     'Prueba de Tkinter opcional: RUN_TK_TESTS=1 y catálogo local')
class DemoWidgetTests(unittest.TestCase):
    def test_background_run_selection_and_error_recovery(self):
        app = DemoDieta()
        app.withdraw()
        errors = []
        app.report_callback_exception = lambda *args: errors.append(args)
        try:
            app.iniciar()
            deadline = time.monotonic() + 30
            while app.ocupada and time.monotonic() < deadline:
                app.update()
                time.sleep(0.02)
            app.update()
            self.assertFalse(app.ocupada, 'La consulta no terminó a tiempo')
            self.assertEqual(len(app.escenarios.tree.get_children()), 8)
            self.assertIsNotNone(app.seleccionado)
            self.assertIn('Peso usado: 70.00 kg', app.resumen.get())
            self.assertIn('Energía requerida: 2706.59 kcal/día', app.resumen.get())
            referencias = [app.tablas['Requerimientos'].tree.item(i, 'values')[0]
                           for i in app.tablas['Requerimientos'].tree.get_children()]
            self.assertIn('evaluacion_peso / peso_para_calculos', referencias)
            self.assertTrue(app.tablas['Alimentos'].tree.get_children())
            app.detalles.select(app.aportes_alimentos)
            app.aportes_alimentos.nutriente.set('proteina_g')
            app.aportes_alimentos.selector.event_generate('<<ComboboxSelected>>')
            app.update()
            self.assertTrue(app.aportes_alimentos.tabla.tree.get_children())
            self.assertIn('Total de la canasta:', app.aportes_alimentos.resumen.get())
            for indice in range(8):
                app.escenarios.tree.selection_set(str(indice))
                app.update()
                self.assertEqual(app.seleccionado, app.consulta['resultados'][indice])
                self.assertEqual(app.aportes_alimentos.nutriente.get(), 'proteina_g')
                self.assertEqual(app.detalles.select(), str(app.aportes_alimentos))
                self.assertIs(app.aportes_alimentos.resultado, app.seleccionado)
            app.variables['presupuesto'].set('0')
            app.variables['modo'].set('Con presupuesto')
            app.iniciar()
            deadline = time.monotonic() + 30
            while app.ocupada and time.monotonic() < deadline:
                app.update()
                time.sleep(0.02)
            app.update()
            self.assertFalse(app.ocupada)
            app.escenarios.tree.selection_set('1')
            app.update()
            self.assertEqual(app.seleccionado['estado'], 'Infeasible')
            self.assertFalse(app.tablas['Alimentos'].tree.get_children())
            self.assertFalse(app.aportes_alimentos.tabla.tree.get_children())
            self.assertIn('disabled', app.aportes_alimentos.selector.state())
            self.assertIn('disabled', app.boton_exportar.state())
            with patch('canasta_inteligente.application.demo_dieta_tk.messagebox.showerror') as dialog:
                app.variables['edad'].set('nan')
                app.iniciar()
                dialog.assert_called_once()
                self.assertFalse(app.ocupada)
            self.assertEqual(errors, [])
        finally:
            app.destroy()


if __name__ == '__main__':
    unittest.main()
