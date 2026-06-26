# Canasta Inteligente GT

Universidad Del Valle De Guatemala

Proyecto de graduación. 



# Fase 1: Exploración de datos de canasta basica y alimentos de la región 

## Setup

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m ipykernel install --user --name canasta-inteligente-gt --display-name "canasta-inteligente-gt"
```

In VS Code/Jupyter, select the `canasta-inteligente-gt` kernel before running notebooks.

Quick dependency check:

```powershell
.\venv\Scripts\python.exe -c "from data_loaders.nutrition_table_incap_data_loader import Nutrition_INCAP; incap_data = Nutrition_INCAP('./data/raw/tabladecomposiciondealimentos.pdf'); print(incap_data.data.shape)"
```

