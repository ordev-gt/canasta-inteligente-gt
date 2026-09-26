"""Comprueba que el notebook consume Family sin definir otro optimizador del hogar."""

import ast
from contextlib import redirect_stdout
import io
import json
import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import test_notebook_coverage as notebook_tests
from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE, load_catalog_pickle


class NotebookHogarTests(unittest.TestCase):
    def test_notebook_keeps_only_presentation_and_configured_profiles(self):
        notebook = json.loads(notebook_tests.NOTEBOOK.read_text(encoding='utf-8'))
        cells = [c for c in notebook['cells'] if c.get('id', '').startswith('hogar-')]
        functions = []
        for cell in cells:
            if cell['cell_type'] == 'code':
                tree = ast.parse(''.join(cell['source']))
                functions.extend(n.name for n in tree.body if isinstance(n, ast.FunctionDef))
                self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                                     and n.func.id == 'input' for n in ast.walk(tree)))
        self.assertEqual(functions, ['mostrar_etapa_hogar'])

    @unittest.skipUnless(DEFAULT_PICKLE.exists(), 'Requiere catálogo procesado')
    def test_complete_notebook_household_flow_uses_family_and_preserves_results(self):
        notebook_tests.CoverageNotebookTests.setUpClass()
        ns = notebook_tests.CoverageNotebookTests.namespace
        ns.update(
            catalog=load_catalog_pickle(),
            penalizaciones_minimizacion={'energia': 1, 'colesterol': 0.1},
            penalizaciones_cobertura={'energia': 1, 'colesterol': 0.1},
            pesos_nutrientes={},
        )
        notebook = json.loads(notebook_tests.NOTEBOOK.read_text(encoding='utf-8'))
        try:
            with patch('builtins.input', side_effect=AssertionError('No se debe solicitar input')), \
                    patch('matplotlib.pyplot.show'), redirect_stdout(io.StringIO()):
                for cell in notebook['cells']:
                    if cell.get('id', '').startswith('hogar-') and cell['cell_type'] == 'code':
                        exec(compile(''.join(cell['source']), cell['id'], 'exec'), ns)
            resultado = ns['consulta_hogar']
            self.assertEqual(len(resultado['integrantes']), 4)
            self.assertTrue(resultado['convergio'])
            self.assertEqual(resultado['estado'], 'Optimal')
            self.assertAlmostEqual(sum(p['presupuesto_q'] for p in resultado['integrantes']), 45)
            self.assertLessEqual(resultado['costo_total_q'], 45 + 1e-5)
            ultimo = resultado['historial_ajuste'].groupby('iteracion')['media_hogar_pct'].first().iloc[-1]
            self.assertAlmostEqual(ultimo, 87.030226, places=4)
            self.assertTrue(all(p.peso_para_calculos is None for p in ns['familia_demo']))
            self.assertEqual(len(plt.gcf().axes), 2)
        finally:
            plt.close('all')


if __name__ == '__main__':
    unittest.main()
