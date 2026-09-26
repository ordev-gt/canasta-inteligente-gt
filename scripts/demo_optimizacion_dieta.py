"""Ejecutar desde cualquier directorio: python scripts/demo_optimizacion_dieta.py."""

from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from canasta_inteligente.application.demo_dieta_tk import main


if __name__ == "__main__":
    main()
