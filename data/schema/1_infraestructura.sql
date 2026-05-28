-- infraestructura.db -- datos maestros: estaciones, cruces, barreras y programaciones semaforicas
PRAGMA foreign_keys = ON;

CREATE TABLE estaciones (
    estacion_id INTEGER PRIMARY KEY,
    nombre      TEXT    NOT NULL UNIQUE,
    orden_linea INTEGER NOT NULL UNIQUE,
    comuna      TEXT,
    latitud     REAL,
    longitud    REAL
);

CREATE TABLE cruces (
    cruce_id             INTEGER PRIMARY KEY,
    nombre               TEXT    NOT NULL UNIQUE,
    comuna               TEXT,
    latitud              REAL,
    longitud             REAL,
    num_pistas_total     INTEGER,
    num_carriles_lateral INTEGER NOT NULL DEFAULT 2,
    tiene_semaforo       INTEGER NOT NULL DEFAULT 1 CHECK (tiene_semaforo IN (0,1)),
    afecta_lateral       INTEGER NOT NULL DEFAULT 1 CHECK (afecta_lateral IN (0,1)),
    sentido_afectacion   TEXT CHECK (sentido_afectacion IN ('CC','CW') OR sentido_afectacion IS NULL),
    estacion_cercana_id  INTEGER REFERENCES estaciones(estacion_id),
    dist_estacion_m      REAL,
    estado_camaras       TEXT,
    observaciones        TEXT
);

CREATE TABLE cruce_tramo (
    cruce_id          INTEGER NOT NULL REFERENCES cruces(cruce_id),
    sentido           TEXT    NOT NULL CHECK (sentido IN ('CC','CW')),
    estacion_desde_id INTEGER REFERENCES estaciones(estacion_id),
    estacion_hasta_id INTEGER REFERENCES estaciones(estacion_id),
    dist_desde_m      REAL,
    dist_total_m      REAL,
    PRIMARY KEY (cruce_id, sentido)
);

CREATE TABLE parametros_barrera (
    cruce_id         INTEGER NOT NULL REFERENCES cruces(cruce_id),
    sentido          TEXT    NOT NULL CHECK (sentido IN ('CC','CW')),
    tiempo_barrera_s INTEGER NOT NULL,
    margen_pre_s     INTEGER NOT NULL DEFAULT 10,
    margen_post_s    INTEGER NOT NULL DEFAULT 10,
    tiempo_alarma_s  INTEGER,
    fuente           TEXT,
    fecha_medicion   TEXT,
    PRIMARY KEY (cruce_id, sentido)
);

-- Versiones de programacion. Se agregan metadatos sin romper el migrador v1.
CREATE TABLE versiones_programacion (
    version_prog_id INTEGER PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE,
    fecha           TEXT,
    tipo_version    TEXT DEFAULT 'base',
    fuente          TEXT,
    descripcion     TEXT
);

-- Asignacion operacional por cruce. Define que programacion debe usar cada cruce
-- sin tratar la reconfiguracion como un escenario global seleccionable.
CREATE TABLE modelo_operacional_cruce (
    modelo_operacional_id INTEGER PRIMARY KEY,
    cruce_id              INTEGER NOT NULL UNIQUE REFERENCES cruces(cruce_id),
    tipo_modelo           TEXT    NOT NULL CHECK (tipo_modelo IN ('RECONFIG','NOREPROG')),
    usa_reconfiguracion   INTEGER NOT NULL CHECK (usa_reconfiguracion IN (0,1)),
    version_prog_id       INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
    descripcion           TEXT    NOT NULL,
    fuente                TEXT,
    actualizado_en        TEXT DEFAULT (datetime('now'))
);

CREATE INDEX ix_modelo_operacional_version ON modelo_operacional_cruce (version_prog_id, tipo_modelo);

-- Tabla original: se mantiene para compatibilidad con migrar_xlsx.py.
CREATE TABLE planes_horarios (
    plan_horario_id INTEGER PRIMARY KEY,
    version_prog_id INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
    hora_inicio_s   INTEGER NOT NULL CHECK (hora_inicio_s BETWEEN 0 AND 86399),
    hora_fin_s      INTEGER NOT NULL CHECK (hora_fin_s   BETWEEN 0 AND 86400),
    plan_id         INTEGER NOT NULL
);

-- Tabla extendida recomendada: horarios de plan por cruce y tipo de dia.
CREATE TABLE planes_horarios_cruce (
    plan_horario_id INTEGER PRIMARY KEY,
    version_prog_id INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
    cruce_id         INTEGER NOT NULL REFERENCES cruces(cruce_id),
    tipo_dia         TEXT NOT NULL DEFAULT 'Laboral',
    hora_inicio_s    INTEGER NOT NULL CHECK (hora_inicio_s BETWEEN 0 AND 86399),
    hora_fin_s       INTEGER NOT NULL CHECK (hora_fin_s BETWEEN 0 AND 86400),
    plan_id          INTEGER NOT NULL,
    fuente           TEXT,
    observaciones    TEXT,
    UNIQUE (version_prog_id, cruce_id, tipo_dia, hora_inicio_s)
);

CREATE TABLE movimientos_cruce (
    movimiento_id INTEGER PRIMARY KEY,
    cruce_id      INTEGER NOT NULL REFERENCES cruces(cruce_id),
    nombre        TEXT NOT NULL,
    tipo          TEXT CHECK (tipo IN ('principal','lateral','giro','peatonal','otro') OR tipo IS NULL),
    sentido       TEXT,
    descripcion   TEXT,
    UNIQUE (cruce_id, nombre)
);

CREATE TABLE programacion_fases (
    fase_pk          INTEGER PRIMARY KEY,
    version_prog_id  INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
    cruce_id         INTEGER NOT NULL REFERENCES cruces(cruce_id),
    plan_id          INTEGER NOT NULL,
    fase_id          INTEGER NOT NULL,
    duracion_s       INTEGER NOT NULL CHECK (duracion_s >= 0),
    entreverde_s     INTEGER NOT NULL DEFAULT 0 CHECK (entreverde_s >= 0),
    cum_inicio_s     INTEGER NOT NULL CHECK (cum_inicio_s >= 0),
    cum_fin_s        INTEGER NOT NULL CHECK (cum_fin_s >= 0),
    es_verde_lateral INTEGER NOT NULL DEFAULT 0 CHECK (es_verde_lateral IN (0,1)),
    ciclo_s          INTEGER NOT NULL CHECK (ciclo_s > 0),
    fuente           TEXT,
    observaciones    TEXT,
    CHECK (cum_inicio_s < cum_fin_s),
    CHECK (cum_fin_s <= ciclo_s),
    UNIQUE (version_prog_id, cruce_id, plan_id, fase_id)
);

CREATE TABLE fase_movimiento (
    version_prog_id INTEGER NOT NULL REFERENCES versiones_programacion(version_prog_id),
    cruce_id         INTEGER NOT NULL REFERENCES cruces(cruce_id),
    plan_id          INTEGER NOT NULL,
    fase_id          INTEGER NOT NULL,
    movimiento_id    INTEGER NOT NULL REFERENCES movimientos_cruce(movimiento_id),
    habilitado       INTEGER NOT NULL CHECK (habilitado IN (0,1)),
    PRIMARY KEY (version_prog_id, cruce_id, plan_id, fase_id, movimiento_id)
);

CREATE INDEX ix_fases_cruce_plan       ON programacion_fases (version_prog_id, cruce_id, plan_id);
CREATE INDEX ix_planes_version         ON planes_horarios (version_prog_id);
CREATE INDEX ix_planes_cruce_version   ON planes_horarios_cruce (version_prog_id, cruce_id, tipo_dia, hora_inicio_s);
CREATE INDEX ix_movimientos_cruce      ON movimientos_cruce (cruce_id);
