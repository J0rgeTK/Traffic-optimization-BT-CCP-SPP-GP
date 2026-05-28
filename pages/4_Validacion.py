"""Pagina de validacion tecnica de insumos del modelo."""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

import datos

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'src'))

from modelo_cruces.validation.validators import validar_todo, resumen_validacion

st.set_page_config(page_title='Validación', page_icon='✅', layout='wide')
st.title('Validación de insumos')
st.caption('Revisión de integridad para programación semafórica, flujos, HCALL y cruces simulables.')

con = datos.conectar()
try:
    findings = validar_todo(con)
    resumen = resumen_validacion(findings)
finally:
    con.close()

c1, c2, c3 = st.columns(3)
c1.metric('Errores', resumen['ERROR'])
c2.metric('Advertencias', resumen['WARN'])
c3.metric('Estado general', 'OK' if not findings else 'Revisar')

if not findings:
    st.success('No se detectaron errores ni advertencias en los insumos cargados.')
    st.stop()

df = pd.DataFrame(findings)
st.subheader('Hallazgos')
st.dataframe(df, use_container_width=True, hide_index=True)

st.info(
    'Las advertencias no impiden ejecutar el modelo, pero identifican cruces o insumos parciales. '
    'Los errores deben corregirse antes de usar una programación o campaña como escenario oficial.'
)
