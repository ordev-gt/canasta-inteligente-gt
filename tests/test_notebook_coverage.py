import ast
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from math import isfinite
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pandas as pd
import pulp


NOTEBOOK = Path(__file__).resolve().parents[1] / 'notebooks' / 'optimizacion_dieta.ipynb'


class CoverageNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
        sources = [''.join(cell['source']) for cell in notebook['cells']]
        namespace = {name: getattr(pulp, name) for name in dir(pulp)}
        namespace.update(pd=pd, isfinite=isfinite, display=lambda *args: None)
        helper = next(source for source in sources if 'def extraer_resultado(' in source)
        exec(compile(helper, str(NOTEBOOK), 'exec'), namespace)
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                functions = [node for node in ast.parse(''.join(cell['source'])).body
                             if isinstance(node, ast.FunctionDef)]
                exec(compile(ast.Module(body=functions, type_ignores=[]), str(NOTEBOOK), 'exec'), namespace)
        cls.solve = staticmethod(namespace['maximizar_cobertura'])
        cls.minimize = staticmethod(namespace['minimizar_costo'])
        cls.combine = staticmethod(namespace['combinar_escenarios'])
        cls.namespace = namespace

    @staticmethod
    def food(name, nutrients, fraction=1.0, meat=False, price=0.01):
        class Food:
            def __getitem__(self, key):
                return self.nutrition.values_per_100g[key]

            def price_summary(self, region):
                return {'latest': SimpleNamespace(cost_per_gram=price)}

        food = Food()
        food.id = food.name = name
        food.is_meat = meat
        food.nutrition = SimpleNamespace(values_per_100g={
            **nutrients, 'fraccion_comestible_pct': fraction,
        })
        return food

    def test_partial_coverage_and_zero_budget(self):
        food = self.food('uno', {'proteina_g': 10})
        scenarios = {'base': {'proteina_g': {'meta': 20}, 'carne_g': {'min': 0}}}
        for budget, expected in [(0, 0), (1, 50), (2, 100), (10, 100)]:
            with self.subTest(budget=budget):
                result = self.solve([food], scenarios, budget)[0]
                self.assertEqual(result['estado'], 'Optimal')
                self.assertAlmostEqual(result['cobertura_media_pct'], expected)
                self.assertLessEqual(result['costo_total_q'], budget + 1e-6)
                self.assertEqual(result['desviaciones'], {})
                self.assertNotIn('carne_g', result['coberturas'].index)

    def test_excess_does_not_replace_other_nutrient_coverage(self):
        foods = [
            self.food('a', {'a': 100, 'b': 0}),
            self.food('b', {'a': 0, 'b': 10}),
        ]
        result = self.solve(foods, {'base': {'a': {'meta': 10}, 'b': {'meta': 10}}}, 1.1)[0]
        self.assertEqual(result['estado'], 'Optimal')
        self.assertAlmostEqual(result['cobertura_media_pct'], 100)
        self.assertAlmostEqual(result['valor_objetivo'], 2)
        self.assertAlmostEqual(result['variables']['a'].varValue, 0.1)
        self.assertAlmostEqual(result['variables']['b'].varValue, 1)

    def test_hard_limits_and_edible_fraction_match_report(self):
        food = self.food('carne', {'vitamina_c_mg': 100}, fraction=0.5, meat=True)
        scenarios = {'base': {
            'vitamina_c_mg': {'meta': 100, 'min': 25, 'max': 75},
            'carne_g': {'min': 0.3, 'max': 0.9},
        }}
        result = self.solve([food], scenarios, 10)[0]
        self.assertEqual(result['estado'], 'Optimal')
        self.assertAlmostEqual(result['aportes']['vitamina_c_mg'], 75)
        self.assertAlmostEqual(result['aportes']['carne_g'], 75)
        self.assertAlmostEqual(result['cobertura_media_pct'], 75)
        self.assertAlmostEqual(result['costo_total_q'], 1.5)
        self.assertTrue(all(c.valid(1e-6) for c in result['modelo'].constraints.values()))

        infeasible = self.solve([food], scenarios, 0)[0]
        self.assertEqual(infeasible['estado'], 'Infeasible')
        self.assertIsNone(infeasible['cobertura_media_pct'])
        self.assertIsNone(infeasible['costo_total_q'])
        self.assertTrue(infeasible['coberturas'].empty)

    def test_scenario_keeps_target_above_maximum_and_isolates_copies(self):
        base = {'vitamina_c_mg': {'min': 100}, 'proteina_g': {'min': 10}}
        iron = {'medio': {
            'hierro_mg': {'min': 20}, 'vitamina_c_mg': {'min': 25, 'max': 75},
            'carne_g': {'min': 0.3},
        }}
        original = deepcopy((base, iron))
        scenario = self.combine(base, iron, maximizar=True)['hierro_medio']
        self.assertEqual(scenario['vitamina_c_mg'], {'meta': 100, 'min': 25, 'max': 75})
        self.assertEqual(scenario['hierro_mg'], {'meta': 20})
        self.assertEqual(scenario['proteina_g'], {'meta': 10})
        scenario['carne_g']['min'] = 9
        self.assertEqual((base, iron), original)

    def test_zero_target_is_not_scored(self):
        food = self.food('uno', {'a': 10, 'b': 0})
        result = self.solve([food], {'base': {'a': {'meta': 10}, 'b': {'meta': 0}}}, 1)[0]
        self.assertEqual(list(result['coberturas'].index), ['a'])
        self.assertAlmostEqual(result['cobertura_media_pct'], 100)

    def test_invalid_budget(self):
        for budget in [-1, float('inf'), float('nan')]:
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                self.solve([], {}, budget)

    def test_weights_change_priority_under_limited_budget(self):
        foods = [self.food('a', {'a': 10, 'b': 0}), self.food('b', {'a': 0, 'b': 10})]
        scenarios = {'base': {'a': {'meta': 10}, 'b': {'meta': 10}}}
        for weights, preferred in [({'a': 0.25}, 'b'), ({'b': 0.25}, 'a')]:
            with self.subTest(weights=weights):
                original = weights.copy()
                result = self.solve(foods, scenarios, 1, weights)[0]
                self.assertAlmostEqual(result['variables'][preferred].varValue, 1)
                self.assertAlmostEqual(result['cobertura_media_pct'], 50)
                self.assertAlmostEqual(result['cobertura_ponderada_pct'], 80)
                self.assertAlmostEqual(result['valor_objetivo'], 1)
                self.assertEqual(result['pesos_nutrientes'][preferred], 1)
                self.assertEqual(weights, original)

    def test_zero_weight_keeps_limits_and_reports_actual_coverage(self):
        food = self.food('uno', {'a': 10, 'b': 10})
        scenarios = {'base': {'a': {'meta': 10}, 'b': {'meta': 10, 'min': 2, 'max': 5}}}
        result = self.solve([food], scenarios, 1, {'b': 0})[0]
        self.assertEqual(result['estado'], 'Optimal')
        self.assertAlmostEqual(result['aportes']['b'], 5)
        self.assertAlmostEqual(result['coberturas'].loc['b', 'cobertura_pct'], 50)
        self.assertAlmostEqual(result['cobertura_ponderada_pct'], 50)
        self.assertAlmostEqual(result['valor_objetivo'], 0.5)
        infeasible = self.solve([food], scenarios, 0, {'b': 0})[0]
        self.assertEqual(infeasible['estado'], 'Infeasible')
        self.assertIsNone(infeasible['cobertura_ponderada_pct'])

    def test_default_weights_preserve_unweighted_objective(self):
        food = self.food('uno', {'a': 10})
        scenarios = {'base': {'a': {'meta': 20}}}
        for weights in [None, {}, {'a': 1}]:
            result = self.solve([food], scenarios, 1, weights)[0]
            self.assertAlmostEqual(result['valor_objetivo'], 0.5)
            self.assertAlmostEqual(result['cobertura_ponderada_pct'], result['cobertura_media_pct'])

    def test_invalid_weights(self):
        food = self.food('uno', {'a': 10})
        scenarios = {'base': {'a': {'meta': 10}}}
        invalid = [{'typo': 1}, {'a': -1}, {'a': float('inf')}, {'a': float('nan')},
                   {'a': None}, {'a': 'invalid'}, {'a': 0}]
        for weights in invalid:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                self.solve([food], scenarios, 1, weights)

    def test_energy_penalty_controls_excess_and_reports_deficit(self):
        food = self.food('uno', {'a': 10, 'energia_kcal': 200})
        scenarios = {'base': {'a': {'meta': 10}, 'energia_kcal': {'ct': 100}}}
        result = self.solve([food], scenarios, 1)[0]
        self.assertEqual(result['estado'], 'Optimal')
        self.assertAlmostEqual(result['aportes']['energia_kcal'], 100)
        self.assertAlmostEqual(result['cobertura_media_pct'], 50)
        self.assertAlmostEqual(result['penalizacion_total'], 0)

        unpenalized = self.solve([food], scenarios, 1, penalizaciones={'energia': 0})[0]
        self.assertAlmostEqual(unpenalized['cobertura_media_pct'], 100)
        self.assertAlmostEqual(unpenalized['desviaciones']['energia_exceso_kcal'], 100)
        self.assertAlmostEqual(unpenalized['desviaciones']['energia_deficit_kcal'], 0)
        self.assertAlmostEqual(unpenalized['penalizacion_total'], 0)

        deficit = self.solve([food], scenarios, 0.25)[0]
        self.assertEqual(deficit['estado'], 'Optimal')
        self.assertAlmostEqual(deficit['desviaciones']['energia_deficit_kcal'], 50)
        self.assertAlmostEqual(deficit['desviaciones']['energia_exceso_kcal'], 0)
        self.assertAlmostEqual(deficit['penalizacion_total'], 50)
        self.assertAlmostEqual(deficit['valor_objetivo'], 0.25 - 50)

    def test_cholesterol_is_soft_and_penalty_is_subtracted(self):
        food = self.food('uno', {'a': 10, 'colesterol_mg': 200})
        scenarios = {'base': {'a': {'meta': 10}, 'colesterol_mg': {'ct': 100}}}
        strong = self.solve([food], scenarios, 1)[0]
        self.assertAlmostEqual(strong['aportes']['colesterol_mg'], 100)
        self.assertAlmostEqual(strong['desviaciones']['colesterol_exceso_mg'], 0)
        coefficients = {'colesterol': 0.001}
        weak = self.solve([food], scenarios, 1, penalizaciones=coefficients)[0]
        self.assertEqual(weak['estado'], 'Optimal')
        self.assertAlmostEqual(weak['aportes']['colesterol_mg'], 200)
        self.assertAlmostEqual(weak['desviaciones']['colesterol_exceso_mg'], 100)
        self.assertAlmostEqual(weak['penalizacion_total'], 0.1)
        self.assertAlmostEqual(weak['valor_objetivo'], 0.9)
        self.assertEqual(coefficients, {'colesterol': 0.001})
        self.assertAlmostEqual(strong['desviaciones']['colesterol_exceso_mg'], 0)
        below = self.solve([food], scenarios, 0.25)[0]
        self.assertAlmostEqual(below['penalizacion_total'], 0)

    def test_invalid_penalties(self):
        food = self.food('uno', {'a': 10})
        scenarios = {'base': {'a': {'meta': 10}}}
        for coefficients in [{'typo': 1}, {'energia': -1}, {'energia': float('nan')},
                             {'colesterol': float('inf')}, {'colesterol': 'invalid'}]:
            with self.subTest(coefficients=coefficients), self.assertRaises(ValueError):
                self.solve([food], scenarios, 1, penalizaciones=coefficients)

    def test_minimization_cost_limits_and_independent_calls(self):
        foods = [self.food('barato', {'a': 10}, fraction=0.5),
                 self.food('caro', {'a': 10}, price=0.04)]
        scenarios = {'base': {'a': {'min': 10, 'max': 15}}}
        original = deepcopy(scenarios)
        result = self.minimize(foods, scenarios)[0]
        self.assertEqual(result['estado'], 'Optimal')
        self.assertAlmostEqual(result['costo_total_q'], 2)
        self.assertAlmostEqual(result['aportes']['a'], 10)
        self.assertAlmostEqual(result['variables']['barato'].varValue, 2)
        other = self.minimize(foods, {'base': {'a': {'min': 20}}})[0]
        self.assertAlmostEqual(other['costo_total_q'], 4)
        self.assertAlmostEqual(result['costo_total_q'], 2)
        self.assertIsNot(result['variables']['barato'], other['variables']['barato'])
        self.assertEqual(scenarios, original)
        infeasible = self.minimize(foods, {'base': {'a': {'min': 20, 'max': 10}}})[0]
        self.assertEqual(infeasible['estado'], 'Infeasible')
        self.assertIsNone(infeasible['costo_total_q'])

    def test_minimization_penalties_are_added_and_fresh(self):
        food = self.food('uno', {'a': 10, 'energia_kcal': 200, 'colesterol_mg': 200})
        scenarios = {'base': {'a': {'min': 10}, 'energia_kcal': {'ct': 100},
                              'colesterol_mg': {'ct': 100}}}
        result = self.minimize([food], scenarios)[0]
        self.assertAlmostEqual(result['costo_total_q'], 1)
        self.assertAlmostEqual(result['penalizacion_total'], 110)
        self.assertAlmostEqual(result['valor_objetivo'], 111)
        zero = self.minimize([food], scenarios, {'energia': 0, 'colesterol': 0})[0]
        self.assertAlmostEqual(zero['valor_objetivo'], 1)
        self.assertAlmostEqual(zero['desviaciones']['energia_exceso_kcal'], 100)
        self.assertAlmostEqual(zero['desviaciones']['colesterol_exceso_mg'], 100)
        self.assertAlmostEqual(result['penalizacion_total'], 110)

    def test_profile_questions_validate_inputs_and_collect_pregnancy(self):
        answers = iter(['Ana', 'nan', '-1', '28', 'mujer', '0', '65', '1,65',
                        'incorrecta', 'moderada', 'si', 'no', 'si', 'no', '60', '10', '6', 'si'])
        with patch.dict(self.namespace, Persona=lambda **kwargs: SimpleNamespace(**kwargs)), redirect_stdout(io.StringIO()):
            persona = self.namespace['solicitar_persona'](leer=lambda _: next(answers))
        self.assertEqual(persona.edad, 28)
        self.assertEqual(persona.peso, 65)
        self.assertEqual(persona.altura, 1.65)
        self.assertEqual(persona.naf, 'moderate')
        self.assertEqual(persona.mes_de_embarazo, 6)
        self.assertEqual(persona.peso_preembarazo, 60)
        self.assertTrue(persona.reservas_de_energia_maternales)

    def test_budget_flow_skips_or_runs_maximization_without_losing_minimum(self):
        food = self.food('uno', {'a': 10})
        consultation = {'escenarios_minimizacion': {'base': {'a': {'min': 20}}},
                        'escenarios_maximizacion': {'base': {'a': {'meta': 20}}}}
        with redirect_stdout(io.StringIO()):
            consultation = self.namespace['minimizar_consulta'](consultation, [food])
            answered = self.namespace['consultar_presupuesto'](consultation, [food], leer=lambda _: 'no')
        self.assertIsNone(answered['presupuesto_q'])
        self.assertEqual(answered['resultados_maximizacion'], [])
        answers = iter(['si', '-5', '1'])
        with redirect_stdout(io.StringIO()):
            answered = self.namespace['consultar_presupuesto'](consultation, [food], leer=lambda _: next(answers))
        self.assertEqual(answered['presupuesto_q'], 1)
        self.assertAlmostEqual(answered['propuesta_maximizacion']['cobertura_media_pct'], 50)
        self.assertIs(answered['resultados_minimizacion'], consultation['resultados_minimizacion'])
        with redirect_stdout(io.StringIO()):
            reset = self.namespace['consultar_presupuesto'](answered, [food], leer=lambda _: 'no')
        self.assertEqual(reset['resultados_maximizacion'], [])
        self.assertIsNone(reset['propuesta_maximizacion'])
        self.assertEqual(len(answered['resultados_maximizacion']), 1)

    def test_infeasible_minimum_can_fall_back_to_budget(self):
        food = self.food('uno', {'a': 10})
        consultation = {'escenarios_minimizacion': {'base': {'a': {'min': 20, 'max': 10}}},
                        'escenarios_maximizacion': {'base': {'a': {'meta': 20, 'max': 10}}}}
        answers = iter(['si', '1'])
        with redirect_stdout(io.StringIO()):
            consultation = self.namespace['minimizar_consulta'](consultation, [food])
            self.assertIsNone(consultation['propuesta_minimizacion'])
            result = self.namespace['consultar_presupuesto'](consultation, [food], leer=lambda _: next(answers))
        self.assertEqual(result['propuesta_maximizacion']['estado'], 'Optimal')
        self.assertAlmostEqual(result['propuesta_maximizacion']['cobertura_media_pct'], 50)

    def test_consultation_recomputes_requirements_for_each_profile(self):
        evaluator = Mock(side_effect=[{'profile': 'uno'}, {'profile': 'dos'}])
        builder = Mock(side_effect=lambda req, maximizar=False: {'perfil': req['profile'], 'maximizar': maximizar})
        with patch.dict(self.namespace, evaluacion_de_requerimientos_diarios=evaluator,
                        construir_escenarios=builder):
            first = self.namespace['preparar_consulta']('persona1')
            second = self.namespace['preparar_consulta']('persona2')
        self.assertEqual(first['escenarios_minimizacion']['perfil'], 'uno')
        self.assertEqual(second['escenarios_maximizacion']['perfil'], 'dos')
        self.assertTrue(second['escenarios_maximizacion']['maximizar'])
        self.assertIsNot(first['resultados_minimizacion'], second['resultados_minimizacion'])


if __name__ == '__main__':
    unittest.main()
