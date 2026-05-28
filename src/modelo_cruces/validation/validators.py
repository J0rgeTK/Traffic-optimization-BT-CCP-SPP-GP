"""Validadores de integridad para el modelo de cruces.

Cada validador devuelve hallazgos como diccionarios con severidad, regla,
mensaje y detalle. La app y los scripts pueden mostrarlos sin duplicar logica.
"""
from __future__ import annotations
import sqlite3
import unicodedata

CRUCES_RECONFIGURACION = {
    'Los Claveles', 'Diagonal Bio Bio', 'Michaihue', 'Masisa',
    'Lomas Coloradas', 'Portal San Pedro', 'Conavicop', 'Conavicoop',
    'Escuadron 2',
}


def _norm_nombre(value: str) -> str:
    txt = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode()
    return ' '.join(txt.lower().split())


def finding(severity: str, rule: str, message: str, detail: str = '') -> dict:
    return {'severity': severity, 'rule': rule, 'message': message, 'detail': detail}


def validar_fases(con: sqlite3.Connection) -> list[dict]:
    out = []
    rows = con.execute('''
        SELECT version_prog_id, cruce_id, plan_id, fase_id, cum_inicio_s, cum_fin_s, ciclo_s
        FROM infra.programacion_fases
        WHERE NOT (cum_inicio_s < cum_fin_s AND cum_fin_s <= ciclo_s)
    ''').fetchall()
    for r in rows:
        out.append(finding('ERROR', 'FASES_RANGO', 'Fase fuera de rango de ciclo', dict(r).__repr__()))

    rows = con.execute('''
        SELECT version_prog_id, cruce_id, plan_id
        FROM infra.programacion_fases
        GROUP BY version_prog_id, cruce_id, plan_id
        HAVING SUM(es_verde_lateral) = 0
    ''').fetchall()
    for r in rows:
        out.append(finding('ERROR', 'FASES_VERDE_LATERAL', 'Plan sin fase verde lateral modelada', dict(r).__repr__()))
    return out


def validar_planes(con: sqlite3.Connection) -> list[dict]:
    out = []
    if con.execute("SELECT 1 FROM infra.sqlite_master WHERE type='table' AND name='planes_horarios_cruce'").fetchone():
        rows = con.execute('''
            SELECT p.version_prog_id, p.cruce_id, p.tipo_dia, p.plan_id
            FROM infra.planes_horarios_cruce p
            LEFT JOIN infra.programacion_fases f
              ON f.version_prog_id = p.version_prog_id
             AND f.cruce_id = p.cruce_id
             AND f.plan_id = p.plan_id
            WHERE f.fase_pk IS NULL
        ''').fetchall()
        for r in rows:
            out.append(finding('ERROR', 'PLAN_SIN_FASES', 'Plan horario sin fases asociadas', dict(r).__repr__()))

        rows = con.execute('''
            SELECT a.version_prog_id, a.cruce_id, a.tipo_dia, a.hora_inicio_s, a.hora_fin_s,
                   b.hora_inicio_s AS inicio_superpuesto, b.hora_fin_s AS fin_superpuesto
            FROM infra.planes_horarios_cruce a
            JOIN infra.planes_horarios_cruce b
              ON a.plan_horario_id < b.plan_horario_id
             AND a.version_prog_id = b.version_prog_id
             AND a.cruce_id = b.cruce_id
             AND a.tipo_dia = b.tipo_dia
             AND a.hora_inicio_s < b.hora_fin_s
             AND b.hora_inicio_s < a.hora_fin_s
        ''').fetchall()
        for r in rows:
            out.append(finding('ERROR', 'PLANES_SUPERPUESTOS', 'Horarios de plan superpuestos', dict(r).__repr__()))
    return out


def validar_llegadas(con: sqlite3.Connection) -> list[dict]:
    out = []
    rows = con.execute('''
        SELECT campania_id, cruce_id, t_inicio_s, t_fin_s, flujo_veh_h
        FROM dem.llegadas_vehiculares
        WHERE NOT (t_inicio_s < t_fin_s AND flujo_veh_h >= 0)
    ''').fetchall()
    for r in rows:
        out.append(finding('ERROR', 'LLEGADAS_RANGO', 'Banda de flujo invalida', dict(r).__repr__()))

    rows = con.execute('''
        SELECT l.campania_id, l.cruce_id
        FROM dem.llegadas_vehiculares l
        LEFT JOIN infra.cruces c ON c.cruce_id = l.cruce_id
        WHERE c.cruce_id IS NULL
    ''').fetchall()
    for r in rows:
        out.append(finding('ERROR', 'LLEGADAS_CRUCE', 'Flujo asociado a cruce inexistente', dict(r).__repr__()))
    return out


def validar_hcall(con: sqlite3.Connection) -> list[dict]:
    out = []
    rows = con.execute('''
        SELECT itinerario_id, cruce_id, hcall_in_s, hcall_out_s
        FROM dem.eventos_barrera
        WHERE hcall_in_s > hcall_out_s
    ''').fetchall()
    for r in rows:
        out.append(finding('ERROR', 'HCALL_RANGO', 'Evento HCALL con cierre anterior a inicio', dict(r).__repr__()))

    rows = con.execute('''
        SELECT e.itinerario_id, e.cruce_id
        FROM dem.eventos_barrera e
        LEFT JOIN infra.cruces c ON c.cruce_id = e.cruce_id
        WHERE c.cruce_id IS NULL
    ''').fetchall()
    for r in rows:
        out.append(finding('ERROR', 'HCALL_CRUCE', 'Evento HCALL asociado a cruce inexistente', dict(r).__repr__()))
    return out


def validar_modelo_operacional(con: sqlite3.Connection) -> list[dict]:
    out = []
    if not con.execute("SELECT 1 FROM infra.sqlite_master WHERE type='table' AND name='modelo_operacional_cruce'").fetchone():
        out.append(finding('WARN', 'MODELO_OPERACIONAL_TABLA', 'No existe tabla de asignacion operacional por cruce', 'Se usara regla interna de respaldo.'))
        return out

    reconfig_norm = {_norm_nombre(x) for x in CRUCES_RECONFIGURACION}
    rows = con.execute('''
        SELECT c.cruce_id, c.nombre, m.tipo_modelo, m.usa_reconfiguracion, m.version_prog_id
        FROM infra.cruces c
        LEFT JOIN infra.modelo_operacional_cruce m ON m.cruce_id = c.cruce_id
        ORDER BY c.cruce_id
    ''').fetchall()
    for r in rows:
        if r['tipo_modelo'] is None:
            out.append(finding('ERROR', 'MODELO_OPERACIONAL_FALTANTE', f'Cruce sin modelo operacional: {r["nombre"]}', dict(r).__repr__()))
            continue
        esperado_reconfig = _norm_nombre(r['nombre']) in reconfig_norm
        version_esperada = 2 if esperado_reconfig else 1
        tipo_esperado = 'RECONFIG' if esperado_reconfig else 'NOREPROG'
        if int(r['version_prog_id']) != version_esperada or r['tipo_modelo'] != tipo_esperado:
            out.append(finding('ERROR', 'MODELO_OPERACIONAL_REGLA', f'Asignacion no coincide con la regla del proyecto: {r["nombre"]}', dict(r).__repr__()))

        fases = con.execute('''
            SELECT 1 FROM infra.programacion_fases
            WHERE cruce_id = ? AND version_prog_id = ? LIMIT 1
        ''', (r['cruce_id'], r['version_prog_id'])).fetchone()
        tiene_insumos = con.execute('''
            SELECT 1
            WHERE EXISTS (SELECT 1 FROM dem.llegadas_vehiculares WHERE cruce_id = ?)
               OR EXISTS (SELECT 1 FROM dem.eventos_barrera WHERE cruce_id = ?)
        ''', (r['cruce_id'], r['cruce_id'])).fetchone()
        if tiene_insumos and fases is None:
            out.append(finding('ERROR', 'MODELO_OPERACIONAL_SIN_FASES', f'Cruce con modelo asignado pero sin fases para esa version: {r["nombre"]}', dict(r).__repr__()))
    return out


def validar_cruces_simulables(con: sqlite3.Connection) -> list[dict]:
    out = []
    rows = con.execute('''
        SELECT c.cruce_id, c.nombre
        FROM infra.cruces c
        WHERE EXISTS (SELECT 1 FROM infra.programacion_fases f WHERE f.cruce_id = c.cruce_id)
           OR EXISTS (SELECT 1 FROM dem.llegadas_vehiculares l WHERE l.cruce_id = c.cruce_id)
           OR EXISTS (SELECT 1 FROM dem.eventos_barrera e WHERE e.cruce_id = c.cruce_id)
    ''').fetchall()
    for r in rows:
        cid = r['cruce_id']
        checks = {
            'fases': con.execute('SELECT 1 FROM infra.programacion_fases WHERE cruce_id=? LIMIT 1', (cid,)).fetchone(),
            'flujos': con.execute('SELECT 1 FROM dem.llegadas_vehiculares WHERE cruce_id=? LIMIT 1', (cid,)).fetchone(),
            'hcall': con.execute('SELECT 1 FROM dem.eventos_barrera WHERE cruce_id=? LIMIT 1', (cid,)).fetchone(),
        }
        missing = [k for k, v in checks.items() if v is None]
        if missing:
            out.append(finding('WARN', 'CRUCE_INCOMPLETO', f'Cruce con insumos parciales: {r["nombre"]}', ', '.join(missing)))
    return out


def validar_todo(con: sqlite3.Connection) -> list[dict]:
    out: list[dict] = []
    for fn in (validar_fases, validar_planes, validar_llegadas, validar_hcall,
               validar_modelo_operacional, validar_cruces_simulables):
        out.extend(fn(con))
    return out


def resumen_validacion(findings: list[dict]) -> dict[str, int]:
    return {
        'ERROR': sum(1 for f in findings if f['severity'] == 'ERROR'),
        'WARN': sum(1 for f in findings if f['severity'] == 'WARN'),
        'OK': 0 if findings else 1,
    }
