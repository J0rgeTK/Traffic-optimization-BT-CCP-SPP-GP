# Plan de implementación por etapas

## Etapa 1 — Compatibilidad y base extendida

Implementado en esta versión:

- Se mantiene la app original.
- Se mantiene el motor `motor_sim.py`.
- Se mantiene el test de validación contra el Excel.
- Se agrega estructura `src/modelo_cruces/`.
- Se agregan modelos tipados de dominio.
- Se agrega tabla `modelo_operacional_cruce` para asignar reconfiguración/noreprog por cruce.
- Se agrega tabla extendida `planes_horarios_cruce`.
- Se agregan tablas `movimientos_cruce`, `fase_movimiento`, `parametros_modelo`, `escenario_parametros` y `resultados_series`.
- Se agregan columnas de fuente, tipo de día y trazabilidad.
- Se agregan scripts de generación de plantillas, importación tabular y validación.

## Etapa 2 — Carga de nuevas programaciones

Siguiente paso recomendado:

1. Revisar `modelo_operacional_cruce.csv` para confirmar qué cruces usan reconfiguración y qué cruces usan noreprog/base.
2. Completar `programacion_fases.csv` para cada cruce y plan.
3. Completar `planes_horarios_cruce.csv` con horarios reales por cruce.
4. Cargar las plantillas con `scripts/importar_insumos_tabulares.py`.
5. Ejecutar `scripts/validar_bases.py`.
6. Comparar resultados en Streamlit.

## Etapa 3 — Modularización del motor

Separar gradualmente `motor_sim.py` en:

- `core/hcall.py`;
- `core/signal_plan.py`;
- `core/pre_vaciado.py`;
- `core/queue_model.py`;
- `core/metrics.py`.

Criterio: no eliminar `motor_sim.py` hasta que las pruebas de regresión confirmen equivalencia con el modo `faithful` y consistencia con el modo `corrected`.

## Etapa 4 — Pruebas unitarias completas

Agregar pruebas específicas para:

- activación de HCALL;
- término de HCALL;
- selección de plan vigente;
- rojo efectivo base;
- rojo efectivo con pre-vaciado;
- cola base;
- cola pre-vaciado;
- KPIs;
- importación de insumos tabulares.

## Etapa 5 — Consolidación operativa

Cuando el modelo esté validado con más cruces y programaciones:

- migrar escenarios persistentes a base externa si se requiere uso multiusuario;
- agregar exportación de reporte técnico;
- agregar comparación de versiones semafóricas por cruce;
- incorporar análisis de sensibilidad GPS/ETA.
