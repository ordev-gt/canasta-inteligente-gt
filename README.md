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

## Demo de optimización de dieta en Tkinter

La lógica de [optimizacion_dieta.ipynb](notebooks/optimizacion_dieta.ipynb) también
está disponible como módulo Python y como demo de escritorio. Desde la raíz del
proyecto, con las dependencias instaladas:

```powershell
.\venv\Scripts\python.exe -X utf8 scripts/demo_optimizacion_dieta.py
```

La demo permite editar el perfil (incluidos embarazo y lactancia), consultar sus
requerimientos y ejecutar costo mínimo, cobertura con presupuesto o ambos.
El encabezado muestra el peso evaluado usado en los cálculos y la energía requerida;
la pestaña **Requerimientos** incluye la evaluación del peso. Se utiliza el mismo
servicio del notebook: evalúa el peso antes de calcular energía y los nutrientes
que dependen de ella. La energía aportada por la canasta puede diferir del
requerimiento, ya que el modelo penaliza su desviación respecto a esa referencia.
En **Modelo y pesos** puedes ajustar el presupuesto diario, los pesos por nutriente
y las penalizaciones de energía y colesterol de cada modelo. Los pesos se escriben
como `vitamina_d_mcg = 0.25`, uno por línea; los omitidos valen 1.

Selecciona una fila para ver alimentos, aportes, límites, déficits y diagnóstico.
La estrella identifica la propuesta por función objetivo de cada modelo.
El costo de alimentos se muestra separado de las penalizaciones. Los escenarios
sin solución óptima conservan su estado, sin presentar cantidades como válidas.
Puedes exportar los alimentos del escenario seleccionado a CSV.
Las tablas **Alimentos** y **Aporte por alimento** muestran el **Nombre INCAP**
del alimento emparejado, junto al nombre de la canasta. También se incluye en el CSV.

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
La lógica está en `src/canasta_inteligente/application/optimizacion_dieta.py` y la
interfaz en `src/canasta_inteligente/application/demo_dieta_tk.py`.
El notebook se conserva como referencia; las pruebas comparan sus resultados con
los del módulo extraído.

Se mantienen los cuatro escenarios de hierro y las reglas del notebook: porciones
compradas de 100 g, aportes ajustados por fracción comestible y último precio general
(con alternativa urbana y rural). En la tabla de nutrientes, la carne se expresa en
gramos comestibles. La cobertura media puede ocultar déficits individuales; revisa
la tabla **Nutrientes**. No se distribuyen comidas ni se impone variedad.

## Canastas para varias personas

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
