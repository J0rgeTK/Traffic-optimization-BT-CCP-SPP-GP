"""Definicion de plantillas CSV canonicas."""
from __future__ import annotations

TEMPLATES = {
    'versiones_programacion.csv': [
        'version_prog_id', 'nombre', 'fecha', 'tipo_version', 'fuente', 'descripcion'
    ],
    'modelo_operacional_cruce.csv': [
        'cruce', 'tipo_modelo', 'usa_reconfiguracion', 'version_prog_id',
        'descripcion', 'fuente'
    ],
    'planes_horarios_cruce.csv': [
        'version_prog_id', 'cruce', 'tipo_dia', 'hora_inicio', 'hora_fin',
        'plan_id', 'fuente', 'observaciones'
    ],
    'programacion_fases.csv': [
        'version_prog_id', 'cruce', 'plan_id', 'fase_id', 'duracion_s',
        'entreverde_s', 'cum_inicio_s', 'cum_fin_s', 'es_verde_lateral',
        'ciclo_s', 'fuente', 'observaciones'
    ],
    'campanias_medicion.csv': [
        'campania_id', 'nombre', 'fecha', 'fuente', 'descripcion'
    ],
    'llegadas_vehiculares.csv': [
        'campania_id', 'cruce', 'movimiento', 'tipo_dia', 't_inicio', 't_fin',
        'flujo_veh_h', 'n_muestras', 'desviacion', 'percentil_85', 'fuente',
        'observaciones'
    ],
    'itinerario_versiones.csv': [
        'itinerario_id', 'nombre', 'fecha', 'tipo_dia', 'fuente', 'descripcion'
    ],
    'eventos_barrera.csv': [
        'itinerario_id', 'cruce', 'servicio_codigo', 'sentido', 'instante_paso',
        'hcall_in', 'hcall_out', 'tiempo_barrera_s', 'fuente', 'metodo_calculo',
        'nivel_confianza', 'observaciones'
    ],
    'escenarios_base.csv': [
        'escenario_id', 'nombre', 'cruce', 'version_prog_id', 'campania_id',
        'itinerario_id', 'tipo_dia', 'hora_inicio', 'hora_fin', 'headway_s',
        'num_carriles', 'buffer_pre_s', 'k_dem', 'alpha', 'modo', 'notas'
    ],
}

EXAMPLE_ROWS = {
    'versiones_programacion.csv': [
        ['3', 'Reprogramacion N2 extendida', '2026-03-09', 'reprog', 'UOCT/SCATS', 'Version tabular de prueba']
    ],
    'modelo_operacional_cruce.csv': [
        ['Diagonal Bio Bio', 'RECONFIG', '1', '2', 'Base + HCALL + prevaciado + reconfiguracion', 'Regla de proyecto'],
        ['Costa Verde', 'NOREPROG', '0', '1', 'Base + HCALL + prevaciado + noreprog/base', 'Regla de proyecto']
    ],
    'planes_horarios_cruce.csv': [
        ['3', 'Costa Verde', 'Laboral', '06:00:00', '09:00:00', '1', 'UOCT/SCATS', 'Plan por cruce']
    ],
    'programacion_fases.csv': [
        ['3', 'Costa Verde', '1', '1', '60', '4', '0', '64', '0', '142', 'UOCT/SCATS', 'Fase principal'],
        ['3', 'Costa Verde', '1', '2', '30', '4', '64', '98', '1', '142', 'UOCT/SCATS', 'Fase lateral modelada']
    ],
    'campanias_medicion.csv': [
        ['3', 'Aforos actualizados 2026', '2026-03-09', 'Aforo/camara', 'Flujo crudo sin k_dem']
    ],
    'llegadas_vehiculares.csv': [
        ['3', 'Costa Verde', 'Lateral', 'Laboral', '06:00:00', '06:15:00', '420', '3', '', '', 'Camara', 'Flujo horario crudo']
    ],
    'itinerario_versiones.csv': [
        ['2', 'Itinerario L2 marzo 2026', '2026-03-09', 'Laboral', 'Itinerario operacional', 'Base para HCALL']
    ],
    'eventos_barrera.csv': [
        ['2', 'Costa Verde', '20245', 'CW', '06:31:20', '06:30:45', '06:32:05', '80', 'Estimado', 'paso_tren_margen', 'Media', 'Ejemplo']
    ],
    'escenarios_base.csv': [
        ['10', 'Costa Verde - Reprog N2 extendida', 'Costa Verde', '3', '3', '2', 'Laboral', '06:00:00', '21:00:00', '2.0', '2', '0', '1.1', '0.75', 'corrected', 'Escenario de prueba']
    ],
}
