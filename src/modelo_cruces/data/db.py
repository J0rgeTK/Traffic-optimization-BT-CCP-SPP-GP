"""Utilidades de conexion SQLite para los dominios del proyecto."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from modelo_cruces.config import DB_ESCENARIOS, DB_INFRA, DB_DEMANDA


def conectar(db_escenarios: Path = DB_ESCENARIOS,
             db_infra: Path = DB_INFRA,
             db_demanda: Path = DB_DEMANDA) -> sqlite3.Connection:
    con = sqlite3.connect(db_escenarios)
    con.row_factory = sqlite3.Row
    con.execute('ATTACH DATABASE ? AS infra', (str(db_infra),))
    con.execute('ATTACH DATABASE ? AS dem', (str(db_demanda),))
    con.execute('PRAGMA foreign_keys = ON')
    return con


def table_exists(con: sqlite3.Connection, schema: str, table: str) -> bool:
    return con.execute(
        f"SELECT 1 FROM {schema}.sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def column_exists(con: sqlite3.Connection, schema: str, table: str, column: str) -> bool:
    if not table_exists(con, schema, table):
        return False
    cols = con.execute(f'PRAGMA {schema}.table_info({table})').fetchall()
    return column in {c['name'] for c in cols}
