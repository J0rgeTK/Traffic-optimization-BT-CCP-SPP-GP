"""Importa insumos desde CSV canonicos a las bases SQLite.

Uso:
    python scripts/importar_insumos_tabulares.py fuentes/plantillas_csv

Antes de importar programaciones nuevas, ejecute:
    python scripts/aplicar_extensiones_db.py
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'src'))

from modelo_cruces.data.db import conectar
from modelo_cruces.importers.tabular import importar_carpeta
from modelo_cruces.validation.validators import validar_todo, resumen_validacion


def main(argv: list[str]) -> int:
    carpeta = Path(argv[1]) if len(argv) > 1 else RAIZ / 'fuentes' / 'plantillas_csv'
    if not carpeta.exists():
        raise SystemExit(f'No existe la carpeta de insumos: {carpeta}')

    con = conectar()
    try:
        resumen = importar_carpeta(con, carpeta)
        print('Importacion completada:')
        if resumen:
            for archivo, n in resumen.items():
                print(f'  {archivo}: {n} fila(s)')
        else:
            print('  No se encontraron CSV con datos para importar.')

        findings = validar_todo(con)
        res = resumen_validacion(findings)
        print(f'Validacion posterior: {res}')
        for f in findings[:50]:
            print(f'[{f["severity"]}] {f["rule"]}: {f["message"]} {f["detail"]}')
        if res['ERROR']:
            return 2
        return 0
    finally:
        con.close()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
