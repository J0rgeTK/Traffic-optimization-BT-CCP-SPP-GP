"""Valida integridad de las bases SQLite del modelo.

Uso:
    python scripts/validar_bases.py
"""
from __future__ import annotations
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'src'))

from modelo_cruces.data.db import conectar
from modelo_cruces.validation.validators import validar_todo, resumen_validacion


def main() -> int:
    con = conectar()
    try:
        findings = validar_todo(con)
        resumen = resumen_validacion(findings)
        print(f'Resumen validacion: {resumen}')
        if not findings:
            print('OK: no se detectaron errores ni advertencias.')
            return 0
        for f in findings:
            print(f'[{f["severity"]}] {f["rule"]}: {f["message"]} {f["detail"]}')
        return 1 if resumen['ERROR'] else 0
    finally:
        con.close()


if __name__ == '__main__':
    raise SystemExit(main())
