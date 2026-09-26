"""Reglas de evaluación de la CBA observada y límites de inferencia con datos faltantes."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd

from canasta_inteligente.application.analisis_cobertura_cba import (
    analizar_cobertura, aportes_canasta, cargar_canastas, evaluar_aporte,
)
from canasta_inteligente.domain.food import Food, FoodCatalog
from canasta_inteligente.domain.nutrition import NutritionProfile


class CoberturaCbaTests(unittest.TestCase):
    def setUp(self):
        self.catalog = FoodCatalog()
        self.catalog.add(Food('arroz', 'Arroz', nutrition=NutritionProfile(
            '001', 'Arroz de prueba', None,
            {'energia_kcal': 200, 'proteina_g': 10, 'sodio_mg': 1, 'fraccion_comestible_pct': 0.5},
        )))

    @staticmethod
    def fila(producto='Arroz', mes='Agosto', gramos=100, costo=2, energia=200):
        return {'Año': 2026, 'Mes': mes, 'Producto': producto, 'Cantidad gramos diarios': gramos,
                'Costo diario': costo, 'Kilocalorías diarias': energia}

    def test_latest_common_month_keeps_all_products_and_full_cost(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            urbana = [self.fila(), self.fila('Comida preparada', costo=4), self.fila(mes='Septiembre')]
            rural = [self.fila(costo=1), self.fila('Comida preparada', costo=3)]
            for region, filas in (('CBAU', urbana), ('CBAR', rural)):
                pd.DataFrame(filas).to_excel(root / f'Historico-por-grupo-alimenticio-y-por-producto-{region}.xlsx',
                                           sheet_name='Por producto', index=False)
            canastas = cargar_canastas(root, self.catalog)
            self.assertEqual(set(canastas['periodo']), {'2026-08'})
            self.assertEqual(len(canastas), 4)
            self.assertEqual(canastas.groupby('region')['costo_diario_q'].sum().to_dict(), {'rural': 4, 'urbana': 6})
            self.assertEqual(canastas['alimento_id'].isna().sum(), 2)
            self.assertTrue((canastas.groupby('region')['proporcion_gramos_pct'].sum() == 100).all())
            with self.assertRaisesRegex(ValueError, 'no está disponible'):
                cargar_canastas(root, self.catalog, (2026, 9))
            # Una equivalencia explícita puede completar el dato, sin sustituir cantidades ni costos.
            manual = cargar_canastas(root, self.catalog, equivalencias={'Comida preparada': 'arroz'})
            self.assertFalse(manual['alimento_id'].isna().any())
            self.assertEqual(manual['costo_diario_q'].sum(), canastas['costo_diario_q'].sum())

    def canastas(self, faltante=False):
        filas = []
        for region, costo in (('urbana', 2), ('rural', 1)):
            filas.append({'region': region, 'periodo': '2026-08', 'producto': 'Arroz', 'alimento_id': 'arroz',
                          'nombre_incap': 'Arroz de prueba', 'gramos_diarios': 100,
                          'costo_diario_q': costo, 'energia_ine_kcal': 200})
            if faltante:
                filas.append({'region': region, 'periodo': '2026-08', 'producto': 'Otro', 'alimento_id': None,
                              'nombre_incap': None, 'gramos_diarios': 50,
                              'costo_diario_q': 3, 'energia_ine_kcal': 100})
        return pd.DataFrame(filas)

    def test_edible_fraction_and_missing_values_are_distinct_from_zero(self):
        detalle = aportes_canasta(self.canastas(True), self.catalog, ['proteina_g', 'vitamina_c_mg'])
        arroz = detalle.loc[(detalle['producto'] == 'Arroz') & (detalle['nutriente'] == 'proteina_g')]
        self.assertTrue((arroz['aporte'] == 5).all())
        self.assertTrue(detalle.loc[detalle['producto'] == 'Otro', 'aporte'].isna().all())
        self.assertTrue(detalle.loc[detalle['nutriente'] == 'vitamina_c_mg', 'aporte'].isna().all())
        sin_ajuste = aportes_canasta(self.canastas(), self.catalog, ['proteina_g'], False)
        self.assertTrue((sin_ajuste['aporte'] == 10).all())

    def test_partial_evidence_does_not_prove_deficiency_or_upper_limit_compliance(self):
        parcial = evaluar_aporte(5, False, 10, 10, 20)
        self.assertEqual(parcial['estado'], 'No concluyente: datos parciales')
        self.assertTrue(pd.isna(parcial['deficit_confirmado']))
        self.assertEqual(evaluar_aporte(5, True, 10, 10, 20)['deficit_confirmado'], 5)
        self.assertEqual(evaluar_aporte(12, False, 10, 10, 20)['estado'], 'Mínimo cubierto; máximo no evaluable')
        self.assertTrue(evaluar_aporte(25, False, 10, 10, 20)['estado'].startswith('Supera máximo'))
        self.assertEqual(evaluar_aporte(12, True, 10, 10, 20)['cobertura_documentada_pct'], 120)
        self.assertTrue(pd.isna(evaluar_aporte(12, True, None, None, 20)['cobertura_documentada_pct']))
        self.assertEqual(evaluar_aporte(12, False, None, None, None)['estado'], 'Sin referencia')

    def test_energy_scaling_uses_full_ine_energy_cost_and_preserves_all_food_ratios(self):
        perfil = SimpleNamespace(nombre='Persona', edad=30, sexo='mujer', peso=55, altura=1.6,
                                 naf='low', peso_para_calculos=55)
        refs = pd.DataFrame([
            {'nutriente': 'energia_kcal', 'unidad': 'kcal', 'meta': 600, 'minimo': 540, 'maximo': 660},
            {'nutriente': 'proteina_g', 'unidad': 'g', 'meta': 10, 'minimo': 10, 'maximo': None},
        ])
        with patch('canasta_inteligente.application.analisis_cobertura_cba.referencias_persona', return_value=(perfil, refs)):
            resultado = analizar_cobertura(self.canastas(True), self.catalog, [perfil], dias=7)
        resumen = resultado['resumen'].set_index(['region', 'escenario'])
        for region, costo in (('urbana', 5), ('rural', 4)):
            actual = resumen.loc[(region, 'Ración actual')]
            ajustada = resumen.loc[(region, 'Ajustada a energía')]
            self.assertEqual(actual['costo_diario_q'], costo)
            self.assertEqual(actual['cobertura_energia_pct'], 50)
            self.assertEqual(ajustada['factor_racion'], 2)
            self.assertEqual(ajustada['costo_periodo_q'], costo * 2 * 7)
            self.assertEqual(ajustada['cobertura_energia_pct'], 100)
        energia = resultado['cobertura'].loc[lambda t: t['nutriente'] == 'energia_kcal']
        self.assertTrue(energia['datos_completos'].all())
        proteina = resultado['cobertura'].loc[lambda t: t['nutriente'] == 'proteina_g']
        self.assertFalse(proteina['datos_completos'].any())
        self.assertTrue(proteina['deficit_confirmado'].isna().all())


class NotebookCoberturaTests(unittest.TestCase):
    def test_saved_notebook_has_executed_cells_and_figures_without_errors(self):
        root = Path(__file__).resolve().parents[1]
        nb = json.loads((root / 'notebooks' / 'analisis_cobertura_cba.ipynb').read_text(encoding='utf-8'))
        codes = [c for c in nb['cells'] if c['cell_type'] == 'code']
        self.assertGreaterEqual(len(codes), 10)
        self.assertTrue(all(c['execution_count'] is not None for c in codes))
        outputs = [o for c in codes for o in c['outputs']]
        self.assertFalse(any(o['output_type'] == 'error' for o in outputs))
        self.assertEqual(sum('image/png' in o.get('data', {}) for o in outputs), 4)


if __name__ == '__main__':
    unittest.main()
