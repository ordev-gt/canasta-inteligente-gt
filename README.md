# Canasta Inteligente GT

Universidad del Valle de Guatemala — proyecto de graduación.

## Fase 1: datos y evaluación nutricional

El proyecto explora la Canasta Básica Alimentaria y los alimentos de la región.
El código usa un layout `src` que separa dominio, reglas nutricionales y acceso a datos:

```text
src/canasta_inteligente/
├── domain/       Persona, familia, alimentos, nutrición y precios
├── nutrition/    Requerimientos, evaluadores y fachada de servicio
├── data/         Cargadores por fuente: INCAP, INE y OMS
├── application/  Puntos de entrada ejecutables
└── optimization/ Canastas individuales de costo mínimo o con presupuesto
```

Los archivos externos se organizan en `data/raw/{incap,ine,who}`; los resultados
derivados y cachés viven en `data/processed` y `data/cache`.

## Instalación

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m ipykernel install --user --name canasta-inteligente-gt --display-name "canasta-inteligente-gt"
```

En VS Code/Jupyter, selecciona el kernel `canasta-inteligente-gt`.

## Comprobación rápida

```powershell
.\venv\Scripts\python.exe -c "from canasta_inteligente.data.incap import Nutrition_INCAP; data = Nutrition_INCAP('./data/raw/incap/tabladecomposiciondealimentos.pdf'); print(data.data.shape)"
```

La configuración `Debug main nutrition evaluation` de VS Code ejecuta
`canasta_inteligente.application.main` con `src` en `PYTHONPATH`.

## Pipeline CBA

El notebook activo [notebooks/cba_pipeline.ipynb](notebooks/cba_pipeline.ipynb)
ejecuta el flujo en dos etapas:

1. Unifica la CBA general 2017–2023 con las CBA rural y urbana desde 2024.
2. Crea una observación general desde 2024 únicamente cuando existen ambas
   regiones, usando su media aritmética.
3. Después de completar el catálogo, empareja sus alimentos con el INCAP.

Los notebooks exploratorios anteriores se conservan en
`legacy/notebooks_originales/` como referencia histórica.

## Procesamiento reproducible y Pickle

El flujo productivo del notebook está disponible como módulo Python. Construye
el catálogo, aplica las fusiones y exclusiones revisadas, lo enriquece con INCAP
y guarda `data/processed/cba_catalog.pkl`:

```powershell
.\venv\Scripts\python.exe -m canasta_inteligente.application.cba_pipeline
```

Para omitir el enriquecimiento INCAP o elegir otra salida:

```powershell
.\venv\Scripts\python.exe -m canasta_inteligente.application.cba_pipeline --without-incap --output data/processed/cba_solo_precios.pkl
```

También puede utilizarse desde Python:

```python
from canasta_inteligente.application.cba_pipeline import (
    load_catalog_pickle,
    process_cba_pipeline,
)

catalog, summary = process_cba_pipeline()
catalog = load_catalog_pickle()
```

## Optimización de dieta por consola y depuración

La consola comparte con Tkinter la creación del perfil y el flujo de
`optimizacion_dieta`: evalúa requerimientos, resuelve los cuatro escenarios de cada
modelo y selecciona una propuesta según su función objetivo. Sin argumentos usa
el mismo perfil inicial de la demo (hombre de 25 años, 70 kg, 1.70 m, actividad baja)
y compara costo mínimo con cobertura bajo un presupuesto diario de Q15.

```powershell
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta_cli.py
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta_cli.py --modo requerimientos
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta_cli.py --modo costo --sexo mujer --edad 30 --peso 60 --altura 1.60
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta_cli.py --modo presupuesto --presupuesto 20 --peso-nutriente proteina_g=2 --max-energia 1 --max-colesterol 0.1
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta_cli.py --detalle todos --aporte-nutriente proteina_g
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta_cli.py --help
```

También se ejecuta como módulo con
`python -m canasta_inteligente.application.demo_dieta_cli` si el proyecto está
instalado. `--catalog` permite elegir el catálogo; el modo `requerimientos` no lo
necesita. `--help` enumera las opciones de embarazo, lactancia, exposición solar,
actividad, pesos nutricionales y penalizaciones. Se aceptan decimales con punto o coma.
La salida incluye los requerimientos, el resumen de todos los escenarios y las
tablas de alimentos, nutrientes y diagnóstico de las propuestas; `--detalle todos`
amplía el detalle al resto. Los escenarios sin solución óptima se indican con su estado.
Una ejecución completada devuelve código 0, incluso si hay escenarios infactibles;
los errores de argumentos, catálogo ausente o ejecución del solver devuelven código 2.

Para depurar, abre **Ejecutar y depurar** en VS Code, selecciona
**Debug optimización dieta (consola)** y pulsa **F5**. La configuración usa el Python
de `venv`, la terminal integrada y los argumentos de `.vscode/launch.json`, que
puedes editar. Coloca un breakpoint en `ejecutar_desde_argumentos` de
`src/canasta_inteligente/application/demo_dieta_cli.py` y entra con **F11** en
`ejecutar_demo`, `preparar_consulta`, `minimizar_costo` o `maximizar_cobertura`.
Después de ejecutar puedes inspeccionar `consulta`, incluidos los modelos PuLP,
variables, restricciones, resultados y propuestas.

## Demo de optimización de dieta en Tkinter

La lógica de [optimizacion_dieta.ipynb](notebooks/optimizacion_dieta.ipynb) también
está disponible como módulo Python y como demo de escritorio. Desde la raíz del
proyecto, con las dependencias instaladas:

```powershell
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta.py
```

La demo sigue el flujo de `streamlit_demo.py` en cuatro pasos:

1. **Integrantes:** agrega, edita o elimina perfiles, incluidos embarazo y lactancia.
   Un integrante produce una dieta personal; varios, una canasta familiar.
2. **Configuración:** indica los días y el presupuesto **total del período y del hogar**.
   Elige la **región del catálogo**: `general` conserva todos los alimentos y prioriza
   precios generales (si faltan, urbanos y luego rurales); `urbana` y `rural` usan
   exclusivamente alimentos con precio válido de la región seleccionada.
   La interfaz informa cuántos alimentos están disponibles. Al cambiar de región,
   se retiran las restricciones de alimentos no disponibles y se pide recalcular.
   Puedes excluir alimentos y limitar sus gramos comprados **por persona y día**;
   los límites se respetan tanto en costo mínimo como con presupuesto.
3. **Calcular canasta:** revisa el resumen y calcula, o consulta solo los requerimientos
   sin necesitar el catálogo. El cálculo se ejecuta sin bloquear la interfaz.
4. **Resultados:** selecciona el hogar completo o una persona para consultar sus dietas.
   También se muestran la comparación del reparto de presupuesto y la distribución
   de alimentos entre integrantes para el período.

**Costo mínimo** calcula sin un tope de presupuesto. **Con presupuesto** conserva
también los escenarios de costo mínimo para compararlos con la propuesta final.
En **Modelo y pesos** puedes ajustar los pesos por nutriente y las penalizaciones
de energía y colesterol. Los pesos se escriben como `vitamina_d_mcg = 0.25`, uno
por línea; los omitidos valen 1. **Requerimientos** conserva la evaluación del peso
usado para calcular energía y los nutrientes que dependen de ella.

Selecciona una fila para ver alimentos, aportes, límites, déficits y diagnóstico.
La estrella identifica la propuesta por función objetivo de cada modelo.
El costo de alimentos se muestra separado de las penalizaciones. Los escenarios
sin solución óptima conservan su estado, sin presentar cantidades como válidas.
**Alimentos / día** muestra los nutrientes de cada alimento en la cantidad diaria
calculada. **Compra del período** y la exportación CSV incluyen cantidades, costos
y aportes nutricionales multiplicados por los días, tanto para la dieta personal
como para la familiar. Se conserva el **Nombre INCAP** junto al nombre de la canasta.
La región utilizada también aparece en los resultados y en el CSV.

En **Aporte por alimento**, elige un nutriente para ver la contribución diaria de
cada alimento, su unidad y su porcentaje del total de la canasta, ordenados de mayor
a menor aporte. Se muestran los gramos comprados y comestibles; el cálculo utiliza
la cantidad de la solución y descuenta la fracción no comestible. El total coincide
con la tabla **Nutrientes**. El porcentaje indica participación en la canasta,
no cobertura del requerimiento diario.

Se usa `data/processed/cba_catalog.pkl`; si falta, genera el catálogo con el pipeline
descrito arriba. También puedes seleccionar otro catálogo generado por el proyecto:

```powershell
.\venv\Scripts\python.exe scripts/demo_optimizacion_dieta.py --catalog data/processed/cba_catalog.pkl
```

Tkinter forma parte de la instalación estándar de Python para Windows; debe estar
habilitado el componente Tcl/Tk. No se necesita Jupyter para esta demo.
La interfaz está en `src/canasta_inteligente/application/demo_dieta_tk.py`; utiliza
`demo_canasta.py` para presentar las canastas calculadas por `Family` y `Persona`.
El notebook se conserva como referencia; las pruebas comparan sus resultados con
los del módulo extraído.

Se mantienen los cuatro escenarios de hierro y las reglas del notebook: porciones
compradas de 100 g, aportes ajustados por fracción comestible y último precio general
(con alternativa urbana y rural). En la tabla de nutrientes, la carne se expresa en
gramos comestibles. La cobertura media puede ocultar déficits individuales; revisa
la tabla **Nutrientes**. No se distribuyen comidas ni se impone variedad.

## Canastas para varias personas

### Canasta del hogar con `Family`

`Family.calcular_canasta` utiliza los métodos individuales de `Persona`: minimiza
las canastas, reparte el presupuesto según sus costos y ajusta ese reparto para
aproximar las coberturas a la media del hogar. El notebook `optimizacion_dieta.ipynb`
ya llama a esta clase; no necesitas ejecutar el notebook para usarla desde Python.

```python
from canasta_inteligente.domain.familia import Family
from canasta_inteligente.domain.persona import Persona
from canasta_inteligente.application.cba_pipeline import load_catalog_pickle

familia = Family([
    Persona("Ana", 35, "mujer", 60, altura=1.60, naf="low"),
    Persona("Luis", 38, "hombre", 75, altura=1.72, naf="moderate"),
    Persona("Sofía", 15, "mujer", 50, altura=1.60, naf="moderate"),
    Persona("Diego", 11, "hombre", 34, altura=1.43, naf="low"),
])
resultado = familia.calcular_canasta(dias=7, presupuesto=315, catalog=load_catalog_pickle())
print(resultado["canasta_periodo"])
print(resultado["reparto_periodo"])
print(resultado["comparacion_repartos"])
```

**El presupuesto es el total del período:** Q315 para siete días equivale a Q45
diarios para todo el hogar. Los modelos, porcentajes e historial permanecen en
unidades diarias. `canasta_periodo` y `reparto_periodo` multiplican los gramos,
porciones y costos por los días; no multiplican precios unitarios ni coberturas.
`costo_diario_q` y `costo_total_q` distinguen ambos costos. Al omitir `presupuesto`
se devuelve únicamente la minimización. Si omites `catalog`, se carga el catálogo
procesado predeterminado.

Los parámetros `pesos_nutrientes`, `penalizaciones_min`, `penalizaciones_max`,
`tolerancia_pp`, `paso_fraccion` y `max_iteraciones` permiten ajustar el experimento.
`convergio` y `motivo_parada` explican cómo terminó el ajuste; una solución del solver
puede ser óptima sin que las coberturas hayan alcanzado la tolerancia de equidad.
No se modifican los perfiles originales. Si falta una solución individual, no se
presenta una compra parcial como canasta completa del hogar.

Ejemplo ejecutable (también disponible como **Debug canasta familiar** en VS Code):

```powershell
.\venv\Scripts\python.exe -X utf8 -m canasta_inteligente.application.probar_familia
```

El ejemplo ejecutable está en [notebooks/canastas_personas.ipynb](notebooks/canastas_personas.ipynb).
Con el catálogo procesado, crea el generador una vez y obtén una canasta por persona:

```python
from canasta_inteligente.application.cba_pipeline import load_catalog_pickle
from canasta_inteligente.domain.persona import Persona
from canasta_inteligente.optimization import GeneradorCanastas

personas = [
    Persona("Ana", 30, "mujer", 60, naf="low", altura=1.60),
    Persona("Luis", 25, "hombre", 70, naf="low", altura=1.70),
]
generador = GeneradorCanastas(load_catalog_pickle(), region="general")
resultados = generador.generar_varias(personas)

for resultado in resultados:
    print(resultado.persona.nombre, resultado.estado, resultado.costo_diario_q)
    print(resultado.alimentos[["alimento", "gramos", "costo_Q"]])
```

Para un solo perfil: `resultado = generador.generar(personas[0])`.
Sin presupuesto se minimiza el costo diario respetando los mínimos del modelo.
Con `generador.generar(personas[0], presupuesto_diario_q=15)` se maximiza la
cobertura nutricional dentro de Q15 diarios. Este escenario puede tener déficits;
`resultado.nutrientes` muestra aportes, referencias, máximos, déficit y cobertura.
`cobertura_minima=0.8` exige al menos 80 % de cada referencia y puede resultar infactible.
Se pueden priorizar nutrientes con `pesos_nutrientes={"proteina_g": 2.0}` al usar presupuesto.

`generar_varias` devuelve una lista en el orden de entrada, incluso con nombres
repetidos. El presupuesto indicado se aplica **a cada persona**, no al grupo.
Para presupuestos diferentes, llama a `generar` con el presupuesto de cada perfil.
Las personas originales no se modifican. Solo se interpretan valores cuando CBC
devuelve `Optimal`; en otro estado, costo y cobertura son `None` y las tablas de
alimentos y nutrientes están vacías. Los datos o parámetros inválidos producen
un error descriptivo.

Las cantidades son gramos diarios de porción comestible; el precio corresponde
a la última observación disponible de cada alimento en la región (su fecha aparece
en `fecha_precio`). `resultado.excluidos` explica los alimentos descartados.
Se conservan los nutrientes, exclusiones y condiciones experimentales de hierro
y zinc de `optimizacion_dieta.ipynb`. Para cambiar las exclusiones, pasa
`alimentos_excluidos={...}` al constructor; un conjunto vacío permite todos los
alimentos que tengan datos completos. Los demás parámetros del constructor
permiten elegir biodisponibilidad de hierro/zinc, aplicar sus condiciones y
ajustar el margen superior de energía. El resultado mantiene el alcance del
experimento: no distribuye comidas ni impone variedad o cantidades enteras.

### Prueba con vitaminas y minerales completos del evaluador

Para incluir sus 12 vitaminas y 9 minerales, usa
`GeneradorCanastas(catalog, perfil_nutricional="ampliado")`. El perfil predeterminado
`"original"` conserva el experimento de 11 componentes. La ampliación usa RDD o IA,
convierte las unidades del cobre y separa los máximos de retinol y ácido fólico.
`resultado.notas` detalla los supuestos de niacina, vitamina D, vitamina E y sodio.
No completa nutrientes desconocidos con cero.

La comparación reproducible se ejecuta con:

```powershell
.\venv\Scripts\python.exe -X utf8 scripts/probar_micronutrientes.py
```

La [revisión de la formulación](docs/revision_formulacion_micronutrientes.md) presenta
resultados, conflicto de factibilidad y diferencias frente al documento de tesis.
La ampliación puede ser infactible con las condiciones experimentales de hierro medio;
un promedio alto de cobertura con presupuesto puede ocultar déficits individuales.
