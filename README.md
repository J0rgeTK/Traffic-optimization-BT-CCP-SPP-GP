# Modelo de cruces ferroviarios — Línea 2 Biotren

Aplicación que estima la **espera vehicular en cruces a nivel** con prioridad semafórica GPS/SCATS (*pre-vaciado N2*) en la Línea 2 del Biotren. Reemplaza el modelo original en planilla Excel por un motor de simulación en Python, validado contra el Excel, con bases de datos SQLite e interfaz Streamlit.

Esta versión incorpora una primera mejora estructural para avanzar desde la réplica rígida del Excel hacia un **modelo de datos canónico**, con plantillas tabulares, validadores e importadores modulares.

---

## Qué hace

Simula segundo a segundo, para un cruce, la operación base y el efecto del pre-vaciado. La selección de programación semafórica **no se maneja como un escenario global manual**, sino como una asignación operacional por cruce:

- **Los Claveles, Diagonal Bio Bio, Michaihue, Masisa, Lomas Coloradas, Portal San Pedro, Conavicop y Escuadron 2** usan **Base + HCALL + pre-vaciado + reconfiguración**.
- **El resto de cruces** usa **Base + HCALL + pre-vaciado + noreprog/base**.

La asignación queda registrada en `infra.modelo_operacional_cruce`; si la tabla no existe, `datos.py` aplica la misma regla como respaldo compatible.

El modelo de cola es determinístico: la espera total corresponde a la integral discreta de la cola en el tiempo.

---

## Estructura del repositorio

```text
modelo-cruces-l2/
├── app.py
├── motor_sim.py
├── datos.py
├── pages/
│   ├── 1_Simulacion.py
│   ├── 2_Mapa.py
│   ├── 3_Comparacion.py
│   └── 4_Validacion.py
├── src/modelo_cruces/
│   ├── config.py
│   ├── core/
│   │   ├── models.py
│   │   └── trace_map.py
│   ├── data/
│   │   └── db.py
│   ├── importers/
│   │   ├── tabular.py
│   │   └── templates.py
│   ├── validation/
│   │   └── validators.py
│   └── ui/
├── data/
│   ├── schema/
│   │   ├── 1_infraestructura.sql
│   │   ├── 2_demanda.sql
│   │   └── 3_escenarios.sql
│   ├── infraestructura.db
│   ├── demanda.db
│   └── escenarios.db
├── scripts/
│   ├── migrar_xlsx.py
│   ├── aplicar_extensiones_db.py
│   ├── generar_plantillas_csv.py
│   ├── importar_insumos_tabulares.py
│   └── validar_bases.py
├── tests/
│   ├── test_validacion.py
│   └── test_validadores.py
├── docs/
│   ├── ARQUITECTURA_TECNICA.md
│   ├── FORMATO_INSUMOS.md
│   └── PLAN_IMPLEMENTACION.md
├── fuentes/
│   └── plantillas_csv/
├── requirements.txt
├── pyproject.toml
└── .streamlit/config.toml
```

---

## Uso local

```bash
pip install -r requirements.txt
streamlit run app.py
```

La app abre en `http://localhost:8501`.

---

## Regenerar bases desde el Excel original

El migrador original se mantiene por compatibilidad. Si cambian los modelos Excel fuente, copie los libros a `fuentes/` y ejecute:

```bash
python scripts/migrar_xlsx.py
python scripts/aplicar_extensiones_db.py
python scripts/validar_bases.py
```

---

## Crear plantillas tabulares de insumos

```bash
python scripts/generar_plantillas_csv.py
```

Esto genera archivos CSV en:

```text
fuentes/plantillas_csv/
```

Las plantillas permiten cargar nuevas programaciones semafóricas, asignaciones operacionales por cruce, flujos vehiculares, itinerarios y eventos HCALL sin depender de celdas fijas del Excel.

---

## Importar insumos tabulares

```bash
python scripts/importar_insumos_tabulares.py fuentes/plantillas_csv
python scripts/validar_bases.py
```

Antes de importar datos reales, se recomienda revisar y reemplazar las filas de ejemplo de las plantillas.

---

## Validar las bases

```bash
python scripts/validar_bases.py
```

También existe una página Streamlit nueva:

```text
Validación
```

Esta página muestra errores y advertencias sobre fases, planes, flujos, HCALL, asignación operacional por cruce y cruces con insumos parciales.

---

## Verificar el motor

```bash
python tests/test_validacion.py
python tests/test_validadores.py
```

El modo `faithful` se mantiene como auditoría contra el Excel original. El modo `corrected` debe usarse para comparaciones técnicas corregidas.

---

## Bases de datos

| Base | Contenido | Ciclo de cambio |
|---|---|---|
| `infraestructura.db` | Estaciones, cruces, barreras, programaciones semafóricas | Rara vez |
| `demanda.db` | Campañas de aforo, itinerarios, eventos HCALL | Por campaña o itinerario |
| `escenarios.db` | Configuración, parámetros y resultados de corridas | Cada análisis |

La separación original se mantiene, pero se agregan extensiones compatibles para mejorar trazabilidad y carga de insumos.

---

## Principales mejoras incorporadas

1. Asignación operacional por cruce mediante `modelo_operacional_cruce`, evitando tratar la reconfiguración como escenario global.
2. Compatibilidad con horarios de plan por cruce mediante `planes_horarios_cruce`.
3. Estructura `src/modelo_cruces/` para nuevos módulos sin romper la app actual.
4. Modelos tipados para fases, flujos, HCALL y escenarios.
5. Tabla de equivalencia entre columnas Excel y nombres semánticos.
6. Plantillas CSV canónicas.
7. Importador tabular independiente del Excel original.
8. Validadores de integridad.
9. Página Streamlit de validación.
10. Scripts para aplicar extensiones, generar plantillas, importar insumos y validar bases.

---

## Documentación adicional

- `docs/ARQUITECTURA_TECNICA.md`
- `docs/FORMATO_INSUMOS.md`
- `docs/PLAN_IMPLEMENTACION.md`
