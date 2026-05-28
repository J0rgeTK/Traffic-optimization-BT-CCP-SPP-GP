"""Configuracion central del proyecto."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / 'data'
SCHEMA_DIR = DATA_DIR / 'schema'
TEMPLATES_DIR = ROOT / 'fuentes' / 'plantillas_csv'

DB_INFRA = DATA_DIR / 'infraestructura.db'
DB_DEMANDA = DATA_DIR / 'demanda.db'
DB_ESCENARIOS = DATA_DIR / 'escenarios.db'

DEFAULT_TIPO_DIA = 'Laboral'
