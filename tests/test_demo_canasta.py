"""Compra por período y nutrición de las vistas personal y familiar."""

import unittest

import pandas as pd

from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE, load_catalog_pickle
from canasta_inteligente.application.demo_canasta import (
    ejecutar_canasta, resultado_hogar, seleccionar_catalogo_region, tabla_alimentos,
)
from canasta_inteligente.domain.familia import Family
from canasta_inteligente.domain.food import Food, FoodCatalog
from canasta_inteligente.domain.persona import Persona, get_latest_price_any_region
from canasta_inteligente.domain.prices import PricePoint


def personas():
    # Nombres repetidos deben conservar dietas e identidades independientes.
    return [Persona('Ana', 25, 'mujer', peso, altura=1.65, naf='low') for peso in (55, 65)]


class RequerimientosTests(unittest.TestCase):
    def test_requirements_without_catalog_and_no_members(self):
        resultado = ejecutar_canasta(personas(), 'missing.pkl', solo_requerimientos=True)
        self.assertEqual(len(resultado['perfiles']), 2)
        self.assertIsNone(resultado['hogar'])
        with self.assertRaisesRegex(ValueError, 'integrante'):
            ejecutar_canasta([], 'missing.pkl')


class RegionCatalogoTests(unittest.TestCase):
    def setUp(self):
        self.catalog = FoodCatalog()
        for food_id, precios in (
            ('arroz', {'general': 0.01, 'urbana': 0.03, 'rural': 0.02}),
            ('solo_urbano', {'urbana': 0.04}), ('sin_precio', {'rural': None}),
        ):
            food = self.catalog.add(Food(food_id, food_id), {food_id})
            for region, precio in precios.items():
                food.add_price_point(PricePoint(2026, 1, region, food_id, 'test', cost_per_gram=precio))

    def test_general_preserves_current_price_priority(self):
        catalog = seleccionar_catalogo_region(self.catalog)
        self.assertEqual(len(catalog), 3)
        self.assertEqual(get_latest_price_any_region(catalog.get('arroz')), 0.01)
        self.assertEqual(get_latest_price_any_region(catalog.get('solo_urbano')), 0.04)

    def test_regional_prices_never_fall_back_and_source_is_unchanged(self):
        for region, precio, cantidad in (('urbana', 0.03, 2), ('rural', 0.02, 1)):
            with self.subTest(region=region):
                catalog = seleccionar_catalogo_region(self.catalog, region)
                self.assertEqual(len(catalog), cantidad)
                self.assertEqual(get_latest_price_any_region(catalog.get('arroz')), precio)
                self.assertEqual(set(catalog.get('arroz').price_timelines), {region})
                self.assertIsNone(catalog.find_by_normalized_alias('sin_precio'))
                catalog.get('arroz').name = 'Cambiado'
                self.assertEqual(self.catalog.get('arroz').name, 'arroz')
                self.assertEqual(set(self.catalog.get('arroz').price_timelines), {'general', 'urbana', 'rural'})

    def test_invalid_region_and_empty_regional_catalog(self):
        with self.assertRaisesRegex(ValueError, 'Región inválida'):
            seleccionar_catalogo_region(self.catalog, 'otra')
        catalog = FoodCatalog()
        catalog.add(self.catalog.get('solo_urbano'))
        with self.assertRaisesRegex(ValueError, 'No hay alimentos'):
            seleccionar_catalogo_region(catalog, 'rural')


@unittest.skipUnless(DEFAULT_PICKLE.is_file(), 'Requiere catálogo local')
class CanastaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.personas = personas()
        cls.consulta = ejecutar_canasta(cls.personas, DEFAULT_PICKLE, dias=7, presupuesto=210)

    def test_daily_food_contributions_match_every_person_and_family(self):
        self.assertEqual(len(self.consulta['vistas']), 3)
        self.assertNotEqual(self.consulta['vistas'][1]['nombre'], self.consulta['vistas'][2]['nombre'])
        for vista in self.consulta['vistas']:
            for resultado in vista['resultados']:
                with self.subTest(vista=vista['nombre'], escenario=resultado['escenario'], tipo=resultado['tipo']):
                    if resultado['estado'] != 'Optimal':
                        self.assertTrue(resultado['aportes_por_alimento'].empty)
                        continue
                    totales = resultado['aportes_por_alimento'].groupby('nutriente')['aporte'].sum()
                    for nutriente, aporte in resultado['aportes'].items():
                        self.assertAlmostEqual(totales[nutriente], aporte)
                    diario = tabla_alimentos(resultado)
                    periodo = tabla_alimentos(resultado, 7)
                    for columna in ('gramos', 'costo_q', 'energia_kcal', 'proteina_g'):
                        pd.testing.assert_series_equal(periodo[columna], diario[columna] * 7)
        hogar = self.consulta['hogar']
        self.assertLessEqual(hogar['costo_total_q'], 210 + 1e-4)
        self.assertEqual(hogar['presupuesto_hogar_q'], 30)
        self.assertTrue(all(p.peso_para_calculos is None for p in self.personas))

    def test_personal_diet_and_family_sum_agree(self):
        consulta = ejecutar_canasta(self.personas[:1], DEFAULT_PICKLE, dias=3, presupuesto=None)
        total = consulta['vistas'][0]['resultados'][0]
        personal = next(r for r in consulta['vistas'][1]['resultados'] if r['propuesta'])
        pd.testing.assert_series_equal(total['aportes'], personal['aportes'], check_names=False)
        self.assertAlmostEqual(total['costo_total_q'], personal['costo_total_q'])
        self.assertEqual(consulta['hogar']['etapa'], 'minimizacion')

    def test_exclusions_and_limits_apply_to_both_models(self):
        catalog = load_catalog_pickle()
        propuesta = self.consulta['hogar']['integrantes'][0]['propuesta_maximizacion']
        usados = propuesta['alimentos'].sort_values('gramos', ascending=False)
        limitado, excluido = usados['alimento_id'].iloc[:2]
        limite = float(usados['gramos'].iloc[0]) / 2
        resultado = Family(self.personas[:1]).calcular_canasta(
            dias=2, presupuesto=60, catalog=catalog, alimentos_a_excluir=[excluido],
            limite_diario_de_alimentos_en_gramos={limitado: limite, excluido: 1},
        )
        self.assertEqual(len(catalog), len(load_catalog_pickle()))
        self.assertEqual(resultado['limites_diarios'], {limitado: limite})
        for etapa in ('minimizacion', 'maximizacion'):
            optimos = [r for r in resultado['integrantes'][0][f'resultados_{etapa}'] if r['estado'] == 'Optimal']
            self.assertTrue(optimos)
            for r in optimos:
                alimentos = r['alimentos'].set_index('alimento_id')
                self.assertNotIn(excluido, alimentos.index)
                self.assertLessEqual(alimentos.loc[limitado, 'gramos'], limite + 1e-4)

    def test_failed_family_proposal_does_not_report_partial_nutrition(self):
        hogar = dict(self.consulta['hogar'])
        hogar['integrantes'] = [dict(p) for p in hogar['integrantes']]
        hogar['integrantes'][1]['propuesta_maximizacion'] = None
        hogar['canasta_maximizacion'] = None
        hogar['costo_maximizacion_hogar_q'] = None
        resultado = resultado_hogar(hogar, 'maximizacion', load_catalog_pickle())
        self.assertEqual(resultado['estado'], 'Sin propuesta completa')
        self.assertFalse(resultado['propuesta'])
        self.assertTrue(tabla_alimentos(resultado).empty)
        self.assertTrue(resultado['aportes_por_alimento'].empty)
        self.assertIsNone(resultado['costo_total_q'])

    def test_invalid_food_restrictions_are_rejected_before_solving(self):
        familia = Family(self.personas[:1])
        catalog = load_catalog_pickle()
        food_id = next(iter(catalog)).id
        for limite in (-1, float('nan'), float('inf'), True):
            with self.subTest(limite=limite), self.assertRaisesRegex(ValueError, 'Límite diario'):
                familia.calcular_canasta(catalog=catalog, limite_diario_de_alimentos_en_gramos={food_id: limite})
        with self.assertRaisesRegex(ValueError, 'desconocidos'):
            familia.calcular_canasta(catalog=catalog, alimentos_a_excluir=['no-existe'])
        with self.assertRaisesRegex(ValueError, 'al menos un alimento'):
            familia.calcular_canasta(catalog=catalog, alimentos_a_excluir=[food.id for food in catalog])

    def test_region_prices_reach_each_person_and_household_with_nutrition(self):
        catalog = load_catalog_pickle()
        for region in ('urbana', 'rural'):
            with self.subTest(region=region):
                consulta = ejecutar_canasta(self.personas, DEFAULT_PICKLE, dias=2, presupuesto=60, region=region)
                self.assertEqual(consulta['region_catalogo'], region)
                self.assertEqual(consulta['hogar']['estado'], 'Optimal')
                self.assertLessEqual(consulta['hogar']['costo_total_q'], 60 + 1e-4)
                for vista in consulta['vistas']:
                    for resultado in vista['resultados']:
                        if resultado['estado'] != 'Optimal':
                            continue
                        diario = tabla_alimentos(resultado)
                        self.assertTrue((diario['region_catalogo'] == region).all())
                        self.assertAlmostEqual(diario['energia_kcal'].sum(), resultado['aportes']['energia_kcal'])
                        for fila in diario.itertuples():
                            precio = catalog.get(fila.alimento_id).latest_price(region).cost_per_gram
                            self.assertAlmostEqual(fila.costo_q, fila.gramos * precio)


if __name__ == '__main__':
    unittest.main()
