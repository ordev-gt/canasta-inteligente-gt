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
└── optimization/ Frontera para el futuro optimizador
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
