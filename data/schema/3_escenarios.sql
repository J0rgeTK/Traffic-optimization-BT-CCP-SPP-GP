-- escenarios.db -- configuracion de corridas, parametros y resultados del modelo
PRAGMA foreign_keys = ON;

CREATE TABLE escenarios (
    escenario_id    INTEGER PRIMARY KEY,
    nombre          TEXT NOT NULL,
    cruce_id        INTEGER NOT NULL,   -- FK logica -> infraestructura.cruces
    version_prog_id INTEGER NOT NULL,   -- FK logica -> infraestructura.versiones_programacion
    campania_id     INTEGER NOT NULL,   -- FK logica -> demanda.campanias_medicion
    itinerario_id   INTEGER NOT NULL,   -- FK logica -> demanda.itinerario_versiones
    tipo_dia        TEXT    NOT NULL DEFAULT 'Laboral',
    hora_inicio_s   INTEGER NOT NULL DEFAULT 21600,
    hora_fin_s      INTEGER NOT NULL DEFAULT 75600,
    headway_s       REAL    NOT NULL DEFAULT 2.0,
    num_carriles    REAL    NOT NULL DEFAULT 2.0,
    buffer_pre_s    INTEGER NOT NULL DEFAULT 0,
    k_dem           REAL    NOT NULL DEFAULT 1.1,
    alpha           REAL    NOT NULL DEFAULT 0.75,
    modo            TEXT    NOT NULL DEFAULT 'corrected'
                    CHECK (modo IN ('faithful','corrected','stochastic')),
    creado_en       TEXT    DEFAULT (datetime('now')),
    notas           TEXT
);

CREATE TABLE parametros_modelo (
    parametro_id  INTEGER PRIMARY KEY,
    nombre        TEXT NOT NULL UNIQUE,
    unidad        TEXT,
    descripcion   TEXT,
    valor_default REAL,
    minimo        REAL,
    maximo        REAL
);

CREATE TABLE escenario_parametros (
    escenario_id  INTEGER NOT NULL REFERENCES escenarios(escenario_id),
    parametro_id  INTEGER NOT NULL REFERENCES parametros_modelo(parametro_id),
    valor         REAL NOT NULL,
    PRIMARY KEY (escenario_id, parametro_id)
);

CREATE TABLE resultados (
    escenario_id          INTEGER PRIMARY KEY REFERENCES escenarios(escenario_id),
    demanda_veh           REAL,
    espera_base_vs        REAL,
    espera_base_vh        REAL,
    demora_base_s         REAL,
    cola_max_base         REAL,
    cola_final_base       REAL,
    espera_pre_vs         REAL,
    espera_pre_vh         REAL,
    demora_pre_s          REAL,
    cola_max_pre          REAL,
    cola_final_pre        REAL,
    reduccion_vh          REAL,
    reduccion_pct         REAL,
    reduccion_demora_s    REAL,
    reduccion_ajustada_vh REAL,
    calculado_en          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE resultados_series (
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

CREATE VIEW v_resumen_escenarios AS
SELECT e.escenario_id, e.nombre, e.cruce_id, e.modo, e.tipo_dia, e.k_dem, e.alpha,
       r.demanda_veh, r.espera_base_vh, r.espera_pre_vh,
       r.reduccion_vh, r.reduccion_pct, r.reduccion_ajustada_vh, r.calculado_en
FROM      escenarios e
LEFT JOIN resultados  r ON r.escenario_id = e.escenario_id;
