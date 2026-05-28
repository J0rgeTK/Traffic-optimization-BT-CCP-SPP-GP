"""
Modelo de cruces ferroviarios L2 - aplicacion Streamlit
=======================================================
Pagina principal. Las paginas de simulacion, mapa, comparacion y validacion
estan en la carpeta pages/ y aparecen en el menu lateral.
"""
import streamlit as st

import datos

st.set_page_config(
    page_title='Modelo cruces ferroviarios L2',
    page_icon='🚦',
    layout='wide',
)

st.title('Modelo de cruces ferroviarios — Línea 2 Biotren')
st.caption('Estimación de espera vehicular en cruces a nivel con prioridad '
           'semafórica GPS/SCATS (pre-vaciado N2)')

st.markdown("""
Esta aplicación reemplaza el modelo en planilla Excel por un motor de
simulación en Python, validado celda a celda contra el original, leyendo
desde bases de datos relacionales separadas.

**Enfoque operacional actualizado**

La programación semafórica no se selecciona como un escenario global. Cada
cruce tiene un **modelo operacional asignado**:

- **Los Claveles, Diagonal Bio Bio, Michaihue, Masisa, Lomas Coloradas,
  Portal San Pedro, Conavicop y Escuadron 2**: Base + HCALL + pre-vaciado
  + reconfiguración.
- **Resto de cruces**: Base + HCALL + pre-vaciado + noreprog/base.

**Cómo está organizado**

- **Simulación** — corre el modelo segundo a segundo para un cruce usando
  automáticamente la programación correspondiente a ese cruce.
- **Mapa** — ubica los cruces de la línea sobre el territorio e identifica
  el modelo operacional asignado.
- **Comparación** — contrasta varios cruces respetando la asignación
  operacional individual de cada cruce.
- **Validación** — revisa integridad de programaciones, flujos, HCALL y
  asignaciones por cruce antes de usar nuevas cargas.
""")

con = datos.conectar()

c1, c2, c3, c4 = st.columns(4)
n_cruces = con.execute('SELECT count(*) FROM infra.cruces').fetchone()[0]
n_sim = len(datos.cruces_simulables(con))
n_esc = con.execute('SELECT count(*) FROM escenarios').fetchone()[0]
modelos = datos.listar_modelos_operacionales(con)
n_reconfig = sum(1 for m in modelos if m['usa_reconfiguracion'])
c1.metric('Cruces en la base', n_cruces)
c2.metric('Cruces simulables', n_sim)
c3.metric('Con reconfiguración', n_reconfig)
c4.metric('Escenarios guardados', n_esc)

st.subheader('Cruces simulables')
st.caption('Cruces que tienen aforos vehiculares y eventos de barrera cargados. La programación se asigna por cruce.')
filas = datos.cruces_simulables_detalle(con)
st.dataframe(filas, use_container_width=True, hide_index=True)

st.subheader('Asignación operacional de todos los cruces')
st.dataframe(modelos, use_container_width=True, hide_index=True)

st.info('Modelo de referencia: cola determinística de Newell + preempción '
        'anticipada de cruce ferroviario. Las cifras del modelo deben '
        'interpretarse junto con el informe de verificación del motor. '
        'Para nuevas programaciones use las plantillas CSV y la página de validación.')

con.close()
