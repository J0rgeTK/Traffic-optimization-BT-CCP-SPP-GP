"""Pruebas basicas de validadores estructurales."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

import datos
from modelo_cruces.validation.validators import validar_todo, resumen_validacion


def main() -> int:
    con = datos.conectar()
    try:
        findings = validar_todo(con)
        resumen = resumen_validacion(findings)
    finally:
        con.close()

    print(f'Resumen validadores: {resumen}')
    for f in findings:
        print(f'[{f["severity"]}] {f["rule"]}: {f["message"]} {f["detail"]}')

    # Se permiten advertencias por cruces con insumos parciales, pero no errores.
    return 1 if resumen['ERROR'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
