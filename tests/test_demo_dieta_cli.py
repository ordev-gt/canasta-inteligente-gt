"""Pruebas del flujo de consola, sin crear ventanas."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest

from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE
from canasta_inteligente.application.demo_dieta_cli import (
    crear_parser, ejecutar_desde_argumentos, main, mostrar_consulta,
)


class DietaCliTests(unittest.TestCase):
    def test_script_runs_without_tkinter_from_another_directory(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/demo_optimizacion_dieta_cli.py'
        code = ('import runpy, sys; sys.modules["tkinter"] = None; '
                'script = sys.argv[1]; sys.argv = sys.argv[1:]; '
                'runpy.run_path(script, run_name="__main__")')
        result = subprocess.run(
            [sys.executable, '-X', 'utf8', '-c', code, str(script),
             '--modo', 'requerimientos', '--catalog', 'missing.pkl'],
            cwd=script.parent, capture_output=True, text=True, encoding='utf-8', timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('2706.59 kcal/día', result.stdout)
        self.assertIn('Requerimientos diarios', result.stdout)

    def test_maternal_profile_and_decimal_comma(self):
        args = crear_parser().parse_args([
            '--modo', 'requerimientos', '--sexo', 'mujer', '--embarazo',
            '--edad', '28', '--peso', '65', '--altura', '1,65',
            '--actividad', 'moderada', '--mes-embarazo', '6', '--peso-previo', '60',
            '--reservas', '--no-solar',
        ])
        consulta = ejecutar_desde_argumentos(args)
        persona = consulta['persona']
        self.assertEqual(persona.altura, 1.65)
        self.assertEqual(persona.naf, 'moderate')
        self.assertEqual(persona.mes_de_embarazo, 6)
        self.assertTrue(persona.reservas_de_energia_maternales)
        self.assertFalse(persona.exposicion_solar_suficiente)
        self.assertFalse(consulta['resultados'])

    def test_errors_return_nonzero_with_explanation(self):
        cases = [
            (['--edad', 'nan'], 'Edad'),
            (['--presupuesto', '-1'], 'Presupuesto'),
            (['--peso-nutriente', 'proteina_g=1', '--peso-nutriente', 'proteina_g=2'],
             'más de una vez'),
            (['--catalog', 'missing.pkl'], 'No se encontró el catálogo'),
            (['--embarazo'], '--sexo mujer'),
        ]
        for args, message in cases:
            with self.subTest(args=args), redirect_stderr(StringIO()) as output:
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)
                self.assertIn(message, output.getvalue())

    @unittest.skipUnless(DEFAULT_PICKLE.is_file(), 'Requiere el catálogo procesado local')
    def test_budget_weights_penalties_and_infeasible_reporting(self):
        args = crear_parser().parse_args([
            '--modo', 'presupuesto', '--presupuesto', '0',
            '--peso-nutriente', 'proteina_g=2',
            '--max-energia', '0.5', '--max-colesterol', '0.2',
        ])
        consulta = ejecutar_desde_argumentos(args)
        self.assertEqual(len(consulta['resultados']), 4)
        base = consulta['resultados'][0]
        self.assertEqual(base['estado'], 'Optimal')
        self.assertAlmostEqual(base['costo_total_q'], 0)
        self.assertEqual(base['pesos_nutrientes']['proteina_g'], 2)
        self.assertEqual(base['penalizaciones'], {'energia': 0.5, 'colesterol': 0.2})
        self.assertTrue(any(r['estado'] == 'Infeasible' for r in consulta['resultados']))
        with redirect_stdout(StringIO()) as output:
            mostrar_consulta(consulta, 'todos', 'proteina_g')
        self.assertIn('Sin solución óptima; no hay cantidades ni costos válidos.', output.getvalue())
        self.assertIn('Aporte por alimento: proteina_g', output.getvalue())


if __name__ == '__main__':
    unittest.main()
