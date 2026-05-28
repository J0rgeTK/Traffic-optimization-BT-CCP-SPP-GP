# Formato canónico de insumos

## Objetivo

Permitir que nuevas programaciones semafóricas, asignaciones operacionales por cruce, flujos vehiculares y eventos HCALL se incorporen al modelo sin depender de hojas, filas o celdas específicas del Excel original.

Las plantillas se generan con:

```bash
python scripts/generar_plantillas_csv.py
```

Salida:

```text
fuentes/plantillas_csv/
├─ versiones_programacion.csv
├─ modelo_operacional_cruce.csv
├─ planes_horarios_cruce.csv
├─ programacion_fases.csv
├─ campanias_medicion.csv
├─ llegadas_vehiculares.csv
├─ itinerario_versiones.csv
├─ eventos_barrera.csv
└─ escenarios_base.csv
```

## Programaciones semafóricas

### `versiones_programacion.csv`

Una fila por versión de programación.

Campos:

```text
version_prog_id,nombre,fecha,tipo_version,fuente,descripcion
```


### `modelo_operacional_cruce.csv`

Una fila por cruce. Define si el cruce usa la versión con reconfiguración o la versión noreprog/base. Esta tabla evita cambiar manualmente la programación como si fuese un escenario global.

Campos:

```text
cruce,tipo_modelo,usa_reconfiguracion,version_prog_id,descripcion,fuente
```

Regla actualmente aplicada:

```text
Los Claveles, Diagonal Bio Bio, Michaihue, Masisa, Lomas Coloradas,
Portal San Pedro, Conavicop y Escuadron 2 -> RECONFIG / version_prog_id = 2
Resto de cruces -> NOREPROG / version_prog_id = 1
```

Descripción recomendada:

```text
RECONFIG: Base + HCALL + prevaciado + reconfiguración
NOREPROG: Base + HCALL + prevaciado + noreprog/base
```

### `planes_horarios_cruce.csv`

Una fila por cruce, tipo de día y franja horaria de plan.

Campos:

```text
version_prog_id,cruce,tipo_dia,hora_inicio,hora_fin,plan_id,fuente,observaciones
```

Este formato corrige la limitación del esquema original, donde los horarios de plan estaban a nivel de versión general y no explícitamente por cruce.

### `programacion_fases.csv`

Una fila por fase de cada plan.

Campos:

```text
version_prog_id,cruce,plan_id,fase_id,duracion_s,entreverde_s,cum_inicio_s,cum_fin_s,es_verde_lateral,ciclo_s,fuente,observaciones
```

Reglas mínimas:

- `cum_inicio_s < cum_fin_s`;
- `cum_fin_s <= ciclo_s`;
- cada plan debe tener al menos una fase con `es_verde_lateral = 1` para el movimiento modelado.

## Flujo vehicular

### `campanias_medicion.csv`

Una fila por campaña de aforo.

```text
campania_id,nombre,fecha,fuente,descripcion
```

### `llegadas_vehiculares.csv`

Una fila por intervalo de flujo.

```text
campania_id,cruce,movimiento,tipo_dia,t_inicio,t_fin,flujo_veh_h,n_muestras,desviacion,percentil_85,fuente,observaciones
```

Regla principal:

```text
flujo_veh_h debe almacenarse crudo, sin aplicar k_dem.
```

El parámetro `k_dem` se aplica en el motor al construir la tasa `lambda`.

## Eventos ferroviarios y HCALL

### `itinerario_versiones.csv`

```text
itinerario_id,nombre,fecha,tipo_dia,fuente,descripcion
```

### `eventos_barrera.csv`

```text
itinerario_id,cruce,servicio_codigo,sentido,instante_paso,hcall_in,hcall_out,tiempo_barrera_s,fuente,metodo_calculo,nivel_confianza,observaciones
```

Reglas mínimas:

- `hcall_in <= hcall_out`;
- el cruce debe existir en `infraestructura.db`;
- la fuente y el método de cálculo deben quedar documentados cuando el evento sea estimado.

## Escenarios

### `escenarios_base.csv`

```text
escenario_id,nombre,cruce,version_prog_id,campania_id,itinerario_id,tipo_dia,hora_inicio,hora_fin,headway_s,num_carriles,buffer_pre_s,k_dem,alpha,modo,notas
```

Modos actualmente soportados por el motor:

- `faithful`;
- `corrected`;
- `stochastic`.


Nota: para la interfaz principal, `version_prog_id` se resuelve automáticamente desde `modelo_operacional_cruce`. El campo se mantiene en `escenarios_base.csv` por compatibilidad y para corridas históricas guardadas.
