"""
Capa de acceso a datos
======================
Conecta las tres bases SQLite y construye objetos `Inputs` para el motor
 de simulacion. Este modulo mantiene compatibilidad con el esquema original
 y agrega una regla operacional por cruce: algunos cruces usan
 `base + HCALL + prevaciado + reconfiguracion` y el resto usa
 `base + HCALL + prevaciado + noreprog`.
"""
from __future__ import annotations
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

from motor_sim import Inputs, Resultados

DIR_DATA = Path(__file__).resolve().parent / 'data'
DB_INFRA = DIR_DATA / 'infraestructura.db'
DB_DEM   = DIR_DATA / 'demanda.db'
DB_ESC   = DIR_DATA / 'escenarios.db'

VERSION_NOREPROG_DEFAULT = 1
VERSION_RECONFIG_DEFAULT = 2

# Cruces definidos por el proyecto para operar con reconfiguracion.
# Se incluye Conavicoop como alias escrito por proyecto; la base usa Conavicop.
CRUCES_RECONFIGURACION = {
    'Los Claveles', 'Diagonal Bio Bio', 'Michaihue', 'Masisa',
    'Lomas Coloradas', 'Portal San Pedro', 'Conavicop', 'Conavicoop',
    'Escuadron 2',
}

TIPO_MODELO_RECONFIG = 'RECONFIG'
TIPO_MODELO_NOREPROG = 'NOREPROG'
DESC_RECONFIG = 'Base + HCALL + prevaciado + reconfiguracion'
DESC_NOREPROG = 'Base + HCALL + prevaciado + noreprog/base'


def _norm_nombre(s: str | None) -> str:
    """Normaliza nombres para comparaciones robustas."""
    if s is None:
        return ''
    txt = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return ' '.join(txt.lower().split())


CRUCES_RECONFIGURACION_NORM = {_norm_nombre(x) for x in CRUCES_RECONFIGURACION}


def _hhmmss(seg: int) -> str:
    """Segundos del dia -> 'HH:MM:SS' (formato que espera el motor)."""
    seg = int(seg) % 86400
    return f'{seg // 3600:02d}:{(seg % 3600) // 60:02d}:{seg % 60:02d}'


def conectar() -> sqlite3.Connection:
    """Abre escenarios.db y adjunta infraestructura y demanda."""
    con = sqlite3.connect(DB_ESC, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute('ATTACH DATABASE ? AS infra', (str(DB_INFRA),))
    con.execute('ATTACH DATABASE ? AS dem',   (str(DB_DEM),))
    con.execute('PRAGMA foreign_keys = ON')
    return con


def _tabla_existe(con: sqlite3.Connection, schema: str, tabla: str) -> bool:
    """Indica si una tabla existe en el esquema SQLite indicado."""
    row = con.execute(
        f"SELECT 1 FROM {schema}.sqlite_master WHERE type='table' AND name=?",
        (tabla,),
    ).fetchone()
    return row is not None


def _columna_existe(con: sqlite3.Connection, schema: str, tabla: str,
                    columna: str) -> bool:
    """Indica si una columna existe. Se usa para compatibilidad v1/v2."""
    if not _tabla_existe(con, schema, tabla):
        return False
    cols = con.execute(f'PRAGMA {schema}.table_info({tabla})').fetchall()
    return columna in {c['name'] for c in cols}


# --------------------------------------------------------------------- #
#  regla operacional por cruce
# --------------------------------------------------------------------- #
def _modelo_derivado(nombre_cruce: str, cruce_id: int | None = None) -> dict[str, Any]:
    """Regla de respaldo cuando la tabla de asignacion no existe o no tiene fila."""
    usa_reconfig = _norm_nombre(nombre_cruce) in CRUCES_RECONFIGURACION_NORM
    return {
        'cruce_id': cruce_id,
        'cruce': nombre_cruce,
        'tipo_modelo': TIPO_MODELO_RECONFIG if usa_reconfig else TIPO_MODELO_NOREPROG,
        'usa_reconfiguracion': 1 if usa_reconfig else 0,
        'version_prog_id': VERSION_RECONFIG_DEFAULT if usa_reconfig else VERSION_NOREPROG_DEFAULT,
        'programacion': 'Reprogramado Mar9' if usa_reconfig else 'Base real',
        'descripcion': DESC_RECONFIG if usa_reconfig else DESC_NOREPROG,
        'fuente': 'Regla interna de proyecto',
    }


def modelo_operacional_para_cruce(con: sqlite3.Connection, cruce: str) -> dict[str, Any]:
    """Devuelve el modelo operativo asignado al cruce.

    Fuente principal: infra.modelo_operacional_cruce.
    Respaldo compatible: regla fija de los 8 cruces con reconfiguracion.
    """
    row_cruce = con.execute(
        'SELECT cruce_id, nombre FROM infra.cruces WHERE nombre = ?', (cruce,)
    ).fetchone()
    if row_cruce is None:
        raise ValueError(f'Cruce no encontrado: {cruce}')

    if _tabla_existe(con, 'infra', 'modelo_operacional_cruce'):
        row = con.execute('''
            SELECT c.cruce_id, c.nombre AS cruce,
                   m.tipo_modelo, m.usa_reconfiguracion, m.version_prog_id,
                   COALESCE(v.nombre, '') AS programacion,
                   m.descripcion, m.fuente
            FROM infra.cruces c
            JOIN infra.modelo_operacional_cruce m ON m.cruce_id = c.cruce_id
            LEFT JOIN infra.versiones_programacion v ON v.version_prog_id = m.version_prog_id
            WHERE c.cruce_id = ?
        ''', (row_cruce['cruce_id'],)).fetchone()
        if row is not None:
            return dict(row)

    return _modelo_derivado(row_cruce['nombre'], row_cruce['cruce_id'])


def version_programacion_para_cruce(con: sqlite3.Connection, cruce: str) -> int:
    """Version semaforica que debe usar el cruce segun su modelo operacional."""
    return int(modelo_operacional_para_cruce(con, cruce)['version_prog_id'])


def listar_modelos_operacionales(con: sqlite3.Connection) -> list[dict[str, Any]]:
    """Lista todos los cruces con su modelo operacional asignado."""
    out: list[dict[str, Any]] = []
    for r in listar_cruces(con):
        modelo = modelo_operacional_para_cruce(con, r['nombre'])
        out.append({
            'cruce_id': r['cruce_id'],
            'nombre': r['nombre'],
            'comuna': r['comuna'],
            'tipo_modelo': modelo['tipo_modelo'],
            'modelo_operacional': modelo['descripcion'],
            'usa_reconfiguracion': modelo['usa_reconfiguracion'],
            'version_prog_id': modelo['version_prog_id'],
            'programacion_asignada': modelo['programacion'],
            'fuente_modelo': modelo.get('fuente'),
        })
    return out


# --------------------------------------------------------------------- #
#  consultas de catalogo (para selectores y mapa)
# --------------------------------------------------------------------- #
def listar_cruces(con) -> list[sqlite3.Row]:
    """Todos los cruces con georreferencia."""
    return con.execute(
        'SELECT * FROM infra.cruces ORDER BY cruce_id').fetchall()


def cruces_simulables(con) -> list[str]:
    """Cruces que tienen aforos Y eventos de barrera."""
    return [r['nombre'] for r in con.execute("""
        SELECT DISTINCT c.nombre
        FROM   infra.cruces c
        JOIN   dem.llegadas_vehiculares l ON l.cruce_id = c.cruce_id
        JOIN   dem.eventos_barrera      e ON e.cruce_id = c.cruce_id
        ORDER  BY c.nombre""")]


def cruces_simulables_detalle(con) -> list[dict[str, Any]]:
    """Cruces simulables con version/modelo operacional asignado."""
    simulables = set(cruces_simulables(con))
    out: list[dict[str, Any]] = []
    for r in listar_cruces(con):
        if r['nombre'] not in simulables:
            continue
        modelo = modelo_operacional_para_cruce(con, r['nombre'])
        out.append({
            'Cruce': r['nombre'],
            'Comuna': r['comuna'],
            'Pistas': r['num_pistas_total'],
            'Semáforo': 'Sí' if r['tiene_semaforo'] else 'No',
            'Sentido': r['sentido_afectacion'],
            'Modelo operacional': modelo['descripcion'],
            'Programación asignada': modelo['programacion'],
            'version_prog_id': modelo['version_prog_id'],
        })
    return out


def listar_escenarios(con) -> list[sqlite3.Row]:
    return con.execute('SELECT * FROM escenarios ORDER BY escenario_id').fetchall()


def listar_versiones(con) -> list[sqlite3.Row]:
    return con.execute(
        'SELECT * FROM infra.versiones_programacion').fetchall()


def listar_campanias(con) -> list[sqlite3.Row]:
    return con.execute('SELECT * FROM dem.campanias_medicion').fetchall()


def listar_itinerarios(con) -> list[sqlite3.Row]:
    return con.execute('SELECT * FROM dem.itinerario_versiones').fetchall()


# --------------------------------------------------------------------- #
#  construccion de Inputs para el motor
# --------------------------------------------------------------------- #
def _planes_para_cruce(con: sqlite3.Connection, version_prog_id: int,
                       cruce_id: int, tipo_dia: str) -> list[dict]:
    """Obtiene plan horario por cruce si existe; si no, usa la tabla v1."""
    filas = []
    if _tabla_existe(con, 'infra', 'planes_horarios_cruce'):
        filas = con.execute("""
            SELECT hora_inicio_s, hora_fin_s, plan_id
            FROM infra.planes_horarios_cruce
            WHERE version_prog_id = ?
              AND cruce_id = ?
              AND (tipo_dia = ? OR tipo_dia IS NULL)
            ORDER BY hora_inicio_s
        """, (version_prog_id, cruce_id, tipo_dia)).fetchall()

    if not filas:
        filas = con.execute(
            'SELECT hora_inicio_s, hora_fin_s, plan_id '
            'FROM infra.planes_horarios WHERE version_prog_id = ? '
            'ORDER BY hora_inicio_s',
            (version_prog_id,),
        ).fetchall()

    return [{
        'ini': _hhmmss(r['hora_inicio_s']),
        'fin': _hhmmss(r['hora_fin_s']),
        'plan': r['plan_id'],
    } for r in filas]


def _llegadas_para_cruce(con: sqlite3.Connection, campania_id: int,
                         cruce_id: int, cruce: str,
                         tipo_dia: str) -> list[dict]:
    """Obtiene bandas de flujo. Si existe tipo_dia, filtra de forma compatible."""
    if _columna_existe(con, 'dem', 'llegadas_vehiculares', 'tipo_dia'):
        rows = con.execute("""
            SELECT t_inicio_s, t_fin_s, flujo_veh_h
            FROM dem.llegadas_vehiculares
            WHERE campania_id = ?
              AND cruce_id = ?
              AND (tipo_dia = ? OR tipo_dia IS NULL)
            ORDER BY t_inicio_s
        """, (campania_id, cruce_id, tipo_dia)).fetchall()
    else:
        rows = con.execute("""
            SELECT t_inicio_s, t_fin_s, flujo_veh_h
            FROM dem.llegadas_vehiculares
            WHERE campania_id = ? AND cruce_id = ?
            ORDER BY t_inicio_s
        """, (campania_id, cruce_id)).fetchall()

    return [{
        'cruce': cruce,
        't_ini': r['t_inicio_s'],
        't_fin': r['t_fin_s'],
        'lambda': r['flujo_veh_h'] / 3600.0,  # CRUDO; k_dem lo aplica el motor
    } for r in rows]


def construir_inputs(con, cruce: str, version_prog_id: int | None = None,
                     campania_id: int = 1, itinerario_id: int = 1,
                     hora_inicio_s: int = 21600, hora_fin_s: int = 75600,
                     h: float = 2.0, n_carriles: float = 2.0,
                     buffer: int = 0, k_dem: float = 1.1,
                     tipo_dia: str = 'Laboral') -> Inputs:
    """Arma un objeto Inputs leyendo los insumos desde las bases.

    Si `version_prog_id` es None, la version semaforica se determina por cruce:
    - 8 cruces definidos por proyecto -> Base + HCALL + prevaciado + reconfiguracion.
    - resto de cruces -> Base + HCALL + prevaciado + noreprog/base.

    El flujo en la base es CRUDO; aqui lambda = flujo_veh_h / 3600 y el
    motor aplica k_dem. Para reproducir el Excel original usar k_dem=1.1.
    """
    cid = con.execute('SELECT cruce_id FROM infra.cruces WHERE nombre = ?',
                       (cruce,)).fetchone()
    if cid is None:
        raise ValueError(f'Cruce no encontrado: {cruce}')
    cid = cid['cruce_id']

    if version_prog_id is None:
        version_prog_id = version_programacion_para_cruce(con, cruce)

    prog_fases = [{
        'cross': cruce, 'plan': r['plan_id'], 'phase': r['fase_id'],
        'dur': r['duracion_s'], 'entreverde': r['entreverde_s'],
        'cumend': r['cum_fin_s'], 'cumstart': r['cum_inicio_s'],
        'green_movx': r['es_verde_lateral'], 'ciclo': r['ciclo_s'],
    } for r in con.execute(
        'SELECT * FROM infra.programacion_fases '
        'WHERE version_prog_id = ? AND cruce_id = ? '
        'ORDER BY plan_id, fase_id', (version_prog_id, cid))]

    plan = _planes_para_cruce(con, version_prog_id, cid, tipo_dia)
    llegadas = _llegadas_para_cruce(con, campania_id, cid, cruce, tipo_dia)

    eventos = con.execute(
        'SELECT hcall_in_s, hcall_out_s FROM dem.eventos_barrera '
        'WHERE itinerario_id = ? AND cruce_id = ? ORDER BY hcall_in_s',
        (itinerario_id, cid)).fetchall()
    hcall_in  = sorted(r['hcall_in_s']  for r in eventos)
    hcall_out = sorted(r['hcall_out_s'] for r in eventos)

    if not prog_fases:
        raise ValueError(
            f'No hay fases cargadas para {cruce} / version {version_prog_id}. '
            'Revise la asignacion de modelo operacional por cruce.'
        )
    if not plan:
        raise ValueError(f'No hay planes horarios para version {version_prog_id}')
    if not llegadas:
        raise ValueError(f'No hay flujos cargados para {cruce} / campania {campania_id}')
    if not hcall_in:
        raise ValueError(f'No hay eventos HCALL para {cruce} / itinerario {itinerario_id}')

    return Inputs(
        crossing=cruce, start_s=hora_inicio_s, end_s=hora_fin_s,
        h=h, n_carriles=n_carriles, buffer=buffer, k_dem=k_dem,
        prog_fases=prog_fases, plan=plan, llegadas=llegadas,
        hcall_in=hcall_in, hcall_out=hcall_out,
    )


def inputs_de_escenario(con, escenario_id: int) -> tuple[Inputs, sqlite3.Row]:
    """Construye Inputs a partir de un escenario guardado.

    Por compatibilidad, si el escenario guarda una version, se respeta.
    La interfaz principal usa la asignacion automatica por cruce.
    """
    e = con.execute('SELECT * FROM escenarios WHERE escenario_id = ?',
                     (escenario_id,)).fetchone()
    if e is None:
        raise ValueError(f'Escenario inexistente: {escenario_id}')
    cruce = con.execute('SELECT nombre FROM infra.cruces WHERE cruce_id = ?',
                        (e['cruce_id'],)).fetchone()['nombre']
    tipo_dia = e['tipo_dia'] if 'tipo_dia' in e.keys() else 'Laboral'
    inp = construir_inputs(
        con, cruce, version_prog_id=e['version_prog_id'],
        campania_id=e['campania_id'], itinerario_id=e['itinerario_id'],
        hora_inicio_s=e['hora_inicio_s'], hora_fin_s=e['hora_fin_s'],
        h=e['headway_s'], n_carriles=e['num_carriles'],
        buffer=e['buffer_pre_s'], k_dem=e['k_dem'], tipo_dia=tipo_dia)
    return inp, e


# --------------------------------------------------------------------- #
#  persistencia de resultados
# --------------------------------------------------------------------- #
def guardar_resultado(con, escenario_id: int, res: Resultados) -> None:
    """Inserta o actualiza los KPIs de un escenario.

    Nota: en Streamlit Community Cloud el sistema de archivos es efimero;
    estas escrituras no persisten entre reinicios. Para persistencia real
    multiusuario, migrar escenarios.db a un servicio externo (p.ej. Turso).
    """
    alpha = con.execute('SELECT alpha FROM escenarios WHERE escenario_id = ?',
                         (escenario_id,)).fetchone()['alpha']
    con.execute('DELETE FROM resultados WHERE escenario_id = ?', (escenario_id,))
    con.execute("""
        INSERT INTO resultados (
            escenario_id, demanda_veh,
            espera_base_vs, espera_base_vh, demora_base_s,
            cola_max_base, cola_final_base,
            espera_pre_vs, espera_pre_vh, demora_pre_s,
            cola_max_pre, cola_final_pre,
            reduccion_vh, reduccion_pct, reduccion_demora_s,
            reduccion_ajustada_vh)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        escenario_id, res.demanda,
        res.espera_vs, res.espera_vh, res.demora_prom,
        res.cola_max, res.cola_final,
        res.espera_pre_vs, res.espera_pre_vh, res.demora_pre,
        res.cola_max_pre, res.cola_final_pre,
        res.reduccion_vh, res.reduccion_pct, res.reduccion_demora,
        res.reduccion_vh * alpha))
    con.commit()
