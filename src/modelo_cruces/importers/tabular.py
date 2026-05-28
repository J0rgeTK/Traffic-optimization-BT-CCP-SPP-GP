"""Importador de insumos tabulares canonicos.

Carga CSV simples desde una carpeta. El importador esta pensado como capa
complementaria al migrador del Excel original: no elimina el script historico,
sino que permite incorporar nuevas programaciones, aforos y HCALL sin depender
de celdas fijas.
"""
from __future__ import annotations
import csv
import sqlite3
from pathlib import Path
from typing import Iterable


def norm_text(value: str | None) -> str:
    return (value or '').strip()


def to_seconds(value: str | int | float | None) -> int | None:
    if value is None or str(value).strip() == '':
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    if ':' in s:
        parts = [int(float(p)) for p in s.split(':')]
        while len(parts) < 3:
            parts.append(0)
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return int(float(s.replace(',', '.')))


def to_float(value: str | None) -> float | None:
    if value is None or str(value).strip() == '':
        return None
    return float(str(value).replace(',', '.'))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def cruce_id(con: sqlite3.Connection, nombre: str) -> int:
    row = con.execute('SELECT cruce_id FROM infra.cruces WHERE nombre = ?', (nombre,)).fetchone()
    if row is None:
        raise ValueError(f'Cruce no encontrado en infraestructura: {nombre}')
    return row['cruce_id']


def movimiento_id(con: sqlite3.Connection, cruce: str, movimiento: str | None) -> int | None:
    movimiento = norm_text(movimiento)
    if not movimiento:
        return None
    cid = cruce_id(con, cruce)
    row = con.execute('SELECT movimiento_id FROM infra.movimientos_cruce WHERE cruce_id=? AND nombre=?',
                      (cid, movimiento)).fetchone()
    if row:
        return row['movimiento_id']
    cur = con.execute('INSERT INTO infra.movimientos_cruce (cruce_id,nombre,tipo) VALUES (?,?,?)',
                      (cid, movimiento, 'lateral' if movimiento.lower() == 'lateral' else 'otro'))
    return cur.lastrowid


def importar_versiones(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        con.execute('''
            INSERT OR REPLACE INTO infra.versiones_programacion
            (version_prog_id,nombre,fecha,tipo_version,fuente,descripcion)
            VALUES (?,?,?,?,?,?)
        ''', (int(r['version_prog_id']), r['nombre'], norm_text(r.get('fecha')) or None,
              norm_text(r.get('tipo_version')) or 'base', norm_text(r.get('fuente')) or None,
              norm_text(r.get('descripcion')) or None))
        n += 1
    return n



def importar_modelos_operacionales(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        cid = cruce_id(con, r['cruce'])
        con.execute("""
            INSERT INTO infra.modelo_operacional_cruce
            (cruce_id,tipo_modelo,usa_reconfiguracion,version_prog_id,descripcion,fuente)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(cruce_id) DO UPDATE SET
                tipo_modelo=excluded.tipo_modelo,
                usa_reconfiguracion=excluded.usa_reconfiguracion,
                version_prog_id=excluded.version_prog_id,
                descripcion=excluded.descripcion,
                fuente=excluded.fuente,
                actualizado_en=datetime('now')
        """, (
            cid,
            norm_text(r.get('tipo_modelo')) or 'NOREPROG',
            int(r.get('usa_reconfiguracion') or 0),
            int(r['version_prog_id']),
            norm_text(r.get('descripcion')) or '',
            norm_text(r.get('fuente')) or None,
        ))
        n += 1
    return n

def importar_planes(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        cid = cruce_id(con, r['cruce'])
        con.execute('''
            INSERT OR REPLACE INTO infra.planes_horarios_cruce
            (version_prog_id,cruce_id,tipo_dia,hora_inicio_s,hora_fin_s,plan_id,fuente,observaciones)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (int(r['version_prog_id']), cid, norm_text(r.get('tipo_dia')) or 'Laboral',
              to_seconds(r['hora_inicio']), to_seconds(r['hora_fin']), int(r['plan_id']),
              norm_text(r.get('fuente')) or None, norm_text(r.get('observaciones')) or None))
        n += 1
    return n


def importar_fases(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        cid = cruce_id(con, r['cruce'])
        con.execute('''
            INSERT OR REPLACE INTO infra.programacion_fases
            (version_prog_id,cruce_id,plan_id,fase_id,duracion_s,entreverde_s,
             cum_inicio_s,cum_fin_s,es_verde_lateral,ciclo_s,fuente,observaciones)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (int(r['version_prog_id']), cid, int(r['plan_id']), int(r['fase_id']),
              int(r['duracion_s']), int(r.get('entreverde_s') or 0),
              int(r['cum_inicio_s']), int(r['cum_fin_s']), int(r.get('es_verde_lateral') or 0),
              int(r['ciclo_s']), norm_text(r.get('fuente')) or None,
              norm_text(r.get('observaciones')) or None))
        n += 1
    return n


def importar_campanias(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        con.execute('''
            INSERT OR REPLACE INTO dem.campanias_medicion
            (campania_id,nombre,fecha,fuente,descripcion) VALUES (?,?,?,?,?)
        ''', (int(r['campania_id']), r['nombre'], norm_text(r.get('fecha')) or None,
              norm_text(r.get('fuente')) or None, norm_text(r.get('descripcion')) or None))
        n += 1
    return n


def importar_llegadas(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        cid = cruce_id(con, r['cruce'])
        mid = movimiento_id(con, r['cruce'], r.get('movimiento'))
        con.execute('''
            INSERT OR REPLACE INTO dem.llegadas_vehiculares
            (campania_id,cruce_id,movimiento_id,tipo_dia,t_inicio_s,t_fin_s,
             flujo_veh_h,n_muestras,desviacion,percentil_85,fuente,observaciones)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (int(r['campania_id']), cid, mid, norm_text(r.get('tipo_dia')) or 'Laboral',
              to_seconds(r['t_inicio']), to_seconds(r['t_fin']), to_float(r['flujo_veh_h']),
              int(r['n_muestras']) if norm_text(r.get('n_muestras')) else None,
              to_float(r.get('desviacion')), to_float(r.get('percentil_85')),
              norm_text(r.get('fuente')) or None, norm_text(r.get('observaciones')) or None))
        n += 1
    return n


def importar_itinerarios(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        con.execute('''
            INSERT OR REPLACE INTO dem.itinerario_versiones
            (itinerario_id,nombre,fecha,tipo_dia,fuente,descripcion) VALUES (?,?,?,?,?,?)
        ''', (int(r['itinerario_id']), r['nombre'], norm_text(r.get('fecha')) or None,
              norm_text(r.get('tipo_dia')) or 'Laboral', norm_text(r.get('fuente')) or None,
              norm_text(r.get('descripcion')) or None))
        n += 1
    return n


def importar_eventos_hcall(con: sqlite3.Connection, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    for r in rows:
        cid = cruce_id(con, r['cruce'])
        con.execute('''
            INSERT INTO dem.eventos_barrera
            (itinerario_id,cruce_id,sentido,instante_paso_s,hcall_in_s,hcall_out_s,
             tiempo_barrera_s,fuente,metodo_calculo,nivel_confianza,observaciones)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (int(r['itinerario_id']), cid, norm_text(r.get('sentido')) or None,
              to_seconds(r.get('instante_paso')), to_seconds(r['hcall_in']), to_seconds(r['hcall_out']),
              int(r['tiempo_barrera_s']) if norm_text(r.get('tiempo_barrera_s')) else None,
              norm_text(r.get('fuente')) or None, norm_text(r.get('metodo_calculo')) or None,
              norm_text(r.get('nivel_confianza')) or None, norm_text(r.get('observaciones')) or None))
        n += 1
    return n


def importar_carpeta(con: sqlite3.Connection, carpeta: Path) -> dict[str, int]:
    """Carga los CSV canonicos que existan en la carpeta indicada."""
    carpeta = Path(carpeta)
    resumen = {}
    loaders = [
        ('versiones_programacion.csv', importar_versiones),
        ('modelo_operacional_cruce.csv', importar_modelos_operacionales),
        ('planes_horarios_cruce.csv', importar_planes),
        ('programacion_fases.csv', importar_fases),
        ('campanias_medicion.csv', importar_campanias),
        ('llegadas_vehiculares.csv', importar_llegadas),
        ('itinerario_versiones.csv', importar_itinerarios),
        ('eventos_barrera.csv', importar_eventos_hcall),
    ]
    for filename, loader in loaders:
        rows = read_csv(carpeta / filename)
        if rows:
            resumen[filename] = loader(con, rows)
    con.commit()
    return resumen
