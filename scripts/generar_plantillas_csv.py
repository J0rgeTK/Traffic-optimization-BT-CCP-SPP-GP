"""Genera plantillas CSV canonicas para cargar insumos del modelo.

Uso:
    python scripts/generar_plantillas_csv.py

Salida:
    fuentes/plantillas_csv/*.csv
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'src'))

from modelo_cruces.importers.templates import TEMPLATES, EXAMPLE_ROWS
from modelo_cruces.config import TEMPLATES_DIR


def main() -> int:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    for filename, headers in TEMPLATES.items():
        path = TEMPLATES_DIR / filename
        with path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in EXAMPLE_ROWS.get(filename, []):
                writer.writerow(row)
        print(f'OK: {path.relative_to(RAIZ)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
