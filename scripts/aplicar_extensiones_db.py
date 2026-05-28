"""Aplica extensiones compatibles sobre las bases SQLite existentes.

No recrea ni borra datos. Agrega columnas/tablas necesarias para el formato
canonico de insumos y copia, cuando corresponde, los planes horarios genericos
hacia planes_horarios_cruce para mantener trazabilidad por cruce.
"""
from __future__ import annotations
import sqlite3
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_DATA = RAIZ / 'data'
DB_INFRA = DIR_DATA / 'infraestructura.db'
DB_DEM = DIR_DATA / 'demanda.db'
DB_ESC = DIR_DATA / 'escenarios.db'

CRUCES_RECONFIGURACION = {
    'Los Claveles', 'Diagonal Bio Bio', 'Michaihue', 'Masisa',
    'Lomas Coloradas', 'Portal San Pedro', 'Conavicop', 'Conavicoop',
    'Escuadron 2',
}
VERSION_NOREPROG_DEFAULT = 1
VERSION_RECONFIG_DEFAULT = 2
DESC_RECONFIG = 'Base + HCALL + prevaciado + reconfiguracion'
DESC_NOREPROG = 'Base + HCALL + prevaciado + noreprog/base'


def norm_nombre(value: str) -> str:
    txt = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode()
    return ' '.join(txt.lower().split())


def col_exists(con: sqlite3.Connection, table: str, col: str) -> bool:
    return col in {r[1] for r in con.execute(f'PRAGMA table_info({table})')}


def add_col(con: sqlite3.Connection, table: str, col: str, spec: str) -> None:
    if not col_exists(con, table, col):
        con.execute(f'ALTER TABLE {table} ADD COLUMN {col} {spec}')


def poblar_modelo_operacional(con: sqlite3.Connection) -> None:
    """Actualiza la asignacion operacional por cruce segun la regla del proyecto."""
    reconfig_norm = {norm_nombre(x) for x in CRUCES_RECONFIGURACION}
    con.execute('''
        CREATE TABLE IF NOT EXISTS modelo_operacional_cruce (
            modelo_operacional_id INTEGER PRIMARY KEY,
            cruce_id              INTEGER NOT NULL UNIQUE REFERENCES cruces(cruce_id),
            tipo_modelo           TEXT    NOT NULL CHECK (tipo_modelo IN ('RECONFIG','NOREPROG')),
            usa_reconfiguracion   INTEGER NOT NULL CHECK (usa_reconfiguracion IN (0,1)),
            version_prog_id       INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
            descripcion           TEXT    NOT NULL,
            fuente                TEXT,
            actualizado_en        TEXT DEFAULT (datetime('now'))
        )
    ''')
    for row in con.execute('SELECT cruce_id, nombre FROM cruces ORDER BY cruce_id').fetchall():
        usa = norm_nombre(row[1]) in reconfig_norm
        con.execute('''
            INSERT INTO modelo_operacional_cruce
            (cruce_id,tipo_modelo,usa_reconfiguracion,version_prog_id,descripcion,fuente)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(cruce_id) DO UPDATE SET
                tipo_modelo=excluded.tipo_modelo,
                usa_reconfiguracion=excluded.usa_reconfiguracion,
                version_prog_id=excluded.version_prog_id,
                descripcion=excluded.descripcion,
                fuente=excluded.fuente,
                actualizado_en=datetime('now')
        ''', (
            row[0],
            'RECONFIG' if usa else 'NOREPROG',
            1 if usa else 0,
            VERSION_RECONFIG_DEFAULT if usa else VERSION_NOREPROG_DEFAULT,
            DESC_RECONFIG if usa else DESC_NOREPROG,
            'Regla de proyecto: 8 cruces con reconfiguracion; resto noreprog/base',
        ))
    con.execute('CREATE INDEX IF NOT EXISTS ix_modelo_operacional_version ON modelo_operacional_cruce (version_prog_id, tipo_modelo)')


def migrar_infra() -> None:
    con = sqlite3.connect(DB_INFRA)
    try:
        add_col(con, 'versiones_programacion', 'tipo_version', "TEXT DEFAULT 'base'")
        add_col(con, 'versiones_programacion', 'fuente', 'TEXT')
        add_col(con, 'programacion_fases', 'fuente', 'TEXT')
        add_col(con, 'programacion_fases', 'observaciones', 'TEXT')
        con.executescript('''
            CREATE TABLE IF NOT EXISTS planes_horarios_cruce (
                plan_horario_id INTEGER PRIMARY KEY,
                version_prog_id INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
                cruce_id         INTEGER NOT NULL REFERENCES cruces(cruce_id),
                tipo_dia         TEXT NOT NULL DEFAULT 'Laboral',
                hora_inicio_s    INTEGER NOT NULL,
                hora_fin_s       INTEGER NOT NULL,
                plan_id          INTEGER NOT NULL,
                fuente           TEXT,
                observaciones    TEXT,
                UNIQUE (version_prog_id, cruce_id, tipo_dia, hora_inicio_s)
            );
            CREATE TABLE IF NOT EXISTS movimientos_cruce (
                movimiento_id INTEGER PRIMARY KEY,
                cruce_id      INTEGER NOT NULL REFERENCES cruces(cruce_id),
                nombre        TEXT NOT NULL,
                tipo          TEXT,
                sentido       TEXT,
                descripcion   TEXT,
                UNIQUE (cruce_id, nombre)
            );
            CREATE TABLE IF NOT EXISTS fase_movimiento (
                version_prog_id INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
                cruce_id         INTEGER NOT NULL REFERENCES cruces(cruce_id),
                plan_id          INTEGER NOT NULL,
                fase_id          INTEGER NOT NULL,
                movimiento_id    INTEGER NOT NULL REFERENCES movimientos_cruce(movimiento_id),
                habilitado       INTEGER NOT NULL CHECK (habilitado IN (0,1)),
                PRIMARY KEY (version_prog_id, cruce_id, plan_id, fase_id, movimiento_id)
            );
            CREATE INDEX IF NOT EXISTS ix_planes_cruce_version
                ON planes_horarios_cruce (version_prog_id, cruce_id, tipo_dia, hora_inicio_s);
        ''')
        con.execute('''
            INSERT OR IGNORE INTO movimientos_cruce (cruce_id,nombre,tipo,descripcion)
            SELECT cruce_id, 'Lateral', 'lateral', 'Movimiento lateral modelado originalmente como es_verde_lateral'
            FROM cruces
        ''')
        con.execute('''
            INSERT OR IGNORE INTO planes_horarios_cruce
            (version_prog_id, cruce_id, tipo_dia, hora_inicio_s, hora_fin_s, plan_id, fuente, observaciones)
            SELECT DISTINCT p.version_prog_id, f.cruce_id, 'Laboral', p.hora_inicio_s, p.hora_fin_s,
                   p.plan_id, 'Migracion compatible', 'Derivado desde planes_horarios generico'
            FROM planes_horarios p
            JOIN programacion_fases f
              ON f.version_prog_id = p.version_prog_id
             AND f.plan_id = p.plan_id
        ''')
        poblar_modelo_operacional(con)
        con.commit()
    finally:
        con.close()


def migrar_demanda() -> None:
    con = sqlite3.connect(DB_DEM)
    try:
        for col, spec in [
            ('movimiento_id', 'INTEGER'),
            ('tipo_dia', "TEXT DEFAULT 'Laboral'"),
            ('n_muestras', 'INTEGER'),
            ('desviacion', 'REAL'),
            ('percentil_85', 'REAL'),
            ('fuente', 'TEXT'),
            ('observaciones', 'TEXT'),
        ]:
            add_col(con, 'llegadas_vehiculares', col, spec)
        for col, spec in [('tipo_dia', "TEXT DEFAULT 'Laboral'"), ('fuente', 'TEXT')]:
            add_col(con, 'itinerario_versiones', col, spec)
        for col, spec in [
            ('servicio_id', 'INTEGER'),
            ('tiempo_barrera_s', 'INTEGER'),
            ('fuente', 'TEXT'),
            ('metodo_calculo', 'TEXT'),
            ('nivel_confianza', 'TEXT'),
            ('observaciones', 'TEXT'),
        ]:
            add_col(con, 'eventos_barrera', col, spec)
        con.commit()
    finally:
        con.close()


def migrar_escenarios() -> None:
    con = sqlite3.connect(DB_ESC)
    try:
        add_col(con, 'escenarios', 'tipo_dia', "TEXT NOT NULL DEFAULT 'Laboral'")
        con.executescript('''
            CREATE TABLE IF NOT EXISTS parametros_modelo (
                parametro_id  INTEGER PRIMARY KEY,
                nombre        TEXT NOT NULL UNIQUE,
                unidad        TEXT,
                descripcion   TEXT,
                valor_default REAL,
                minimo        REAL,
                maximo        REAL
            );
            CREATE TABLE IF NOT EXISTS escenario_parametros (
                escenario_id  INTEGER NOT NULL REFERENCES escenarios(escenario_id),
                parametro_id  INTEGER NOT NULL REFERENCES parametros_modelo(parametro_id),
                valor         REAL NOT NULL,
                PRIMARY KEY (escenario_id, parametro_id)
            );
            CREATE TABLE IF NOT EXISTS resultados_series (
                escenario_id INTEGER NOT NULL REFERENCES escenarios(escenario_id),
                segundo_dia  INTEGER NOT NULL,
                llegada_veh  REAL,
                cola_base    REAL,
                cola_pre     REAL,
                hcall_activo INTEGER,
                rojo_base    INTEGER,
                rojo_pre     INTEGER,
                plan_id      INTEGER,
                PRIMARY KEY (escenario_id, segundo_dia)
            );
        ''')
        con.commit()
    finally:
        con.close()


def main() -> int:
    migrar_infra()
    migrar_demanda()
    migrar_escenarios()
    print('OK: extensiones aplicadas sobre las bases SQLite existentes.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
