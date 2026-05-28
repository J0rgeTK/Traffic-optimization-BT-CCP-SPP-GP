# Arquitectura técnica propuesta

## Objetivo

El proyecto mantiene la compatibilidad con la aplicación Streamlit original, pero incorpora una estructura preparada para crecer con nuevas programaciones semafóricas, campañas de aforo, eventos HCALL y validaciones técnicas.

## Principio de diseño

La planilla Excel original deja de ser la arquitectura del sistema y pasa a ser solo una fuente de datos posible. La arquitectura recomendada es:

```text
Insumos tabulares normalizados -> Validadores -> SQLite canonico -> Motor modular -> Streamlit
```

## Estructura incorporada

```text
src/modelo_cruces/
├─ config.py
├─ core/
│  ├─ models.py
│  └─ trace_map.py
├─ data/
│  └─ db.py
├─ importers/
│  ├─ tabular.py
│  └─ templates.py
├─ validation/
│  └─ validators.py
└─ ui/
```

## Compatibilidad

Se mantienen los archivos originales:

- `app.py`
- `datos.py`
- `motor_sim.py`
- `pages/1_Simulacion.py`
- `pages/2_Mapa.py`
- `pages/3_Comparacion.py`
- `scripts/migrar_xlsx.py`
- `tests/test_validacion.py`

Las modificaciones principales en `datos.py` son:

- uso de `modelo_operacional_cruce` para resolver automáticamente la versión de programación por cruce;
- uso de `planes_horarios_cruce` cuando existe;
- respaldo compatible a la regla interna de 8 cruces con reconfiguración si la tabla de asignación no existe;
- eliminación del selector global de programación semafórica en las páginas principales.

## Nuevos componentes

### Modelos tipados

`src/modelo_cruces/core/models.py` define contratos de dominio para:

- fase semafórica;
- plan horario por cruce;
- banda de flujo vehicular;
- evento HCALL;
- escenario de simulación.

### Trazabilidad Excel

`src/modelo_cruces/core/trace_map.py` contiene la equivalencia entre columnas heredadas del Excel y nombres semánticos del modelo. Esto permite mejorar legibilidad sin perder capacidad de auditoría.

### Validadores

`src/modelo_cruces/validation/validators.py` valida:

- rangos de fases;
- existencia de fase verde lateral;
- planes sin fases;
- horarios superpuestos;
- bandas de flujo inválidas;
- eventos HCALL inválidos;
- asignación operacional por cruce;
- cruces con insumos parciales.

### Importador tabular

`src/modelo_cruces/importers/tabular.py` permite cargar CSV canónicos desde `fuentes/plantillas_csv/`.

## Página nueva de Streamlit

Se agregó:

```text
pages/4_Validacion.py
```

Esta página muestra errores y advertencias de integridad sin modificar los datos.
