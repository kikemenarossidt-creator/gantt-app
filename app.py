import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Profesional")

# 1. BASE DE DATOS COMPLETA
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks_data = [
        ("1: INSTALACIÓN ELÉCTRICA", 0), ("Tendido Eléctrico BT", 1), 
        ("Cuadro protecciones SC", 2), ("Cuadro Comunicaciones SC", 2), ("Cuadro Sensores SC", 2),
        ("Cuadro Comunicaciones CT2", 2), ("Cuadro Sensores CT2", 2), ("Alimentaciones CCTV", 2),
        ("Alimentaciones TSM", 2), ("Alimentaciones Cuadros Monitorización", 2),
        ("Alimentaciones Cuadros Seguridad", 2), ("Alimentación Rack", 2),
        ("Alimentación Alumbrado y Secundarios", 2), ("Puestas a Tierra", 1),
        ("Vallado", 2), ("TSMs", 2), ("Box TSM", 2), ("CCTV", 2), ("Vallado CT", 2),
        ("Bodega", 2), ("Trackers", 2), ("String Box", 2), ("Pruebas", 1),
        ("Pruebas de aislamiento CT - Entronque", 2), ("Pruebas de aislamiento CTs", 2),
        ("2: COMUNICACIONES", 0), ("Tendido Cableado", 1), ("Internet", 1),
        ("3: SENSORES", 0), ("5: TRACKERS Y TSM", 0), ("6: CTs", 0), ("7: CCTV", 0),
        ("8: SEGURIDAD", 0), ("9: ENTRONQUE", 0), ("10: PEM", 0), ("11: PERMISOS", 0), ("12: SERVICIOS", 0)
    ]
    
    rows = []
    for i, (name, level) in enumerate(tasks_data):
        rows.append({
            "id": i,
            "Task": name,
            "Level": level,
            "Start": base + timedelta(days=i),
            "End": base + timedelta(days=i+3),
        })
    st.session_state.df = pd.DataFrame(rows)

# 2. PROCESAMIENTO
df = st.session_state.df.copy()
df['L0'] = df.apply(lambda x: x['Task'] if x['Level'] == 0 else "", axis=1)
df['L1'] = df.apply(lambda x: x['Task'] if x['Level'] == 1 else "", axis=1)
df['L2'] = df.apply(lambda x: x['Task'] if x['Level'] == 2 else "", axis=1)

# 3. GRÁFICO ALTAIR (CON TEXTO PEGADO)
h = len(df) * 20 

# Configuramos columnas muy estrechas para que el texto "empuje" a la siguiente
# Nivel 0
col0 = alt.Chart(df).mark_text(align='left', fontWeight='bold', size=11).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L0:N'
).properties(width=130, height=h)

# Nivel 1 (dx=10 para pegarlo un poco a la derecha del nivel 0)
col1 = alt.Chart(df).mark_text(align='left', dx=10, size=10).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L1:N'
).properties(width=110, height=h)

# Nivel 2 (dx=20 para pegarlo un poco a la derecha del nivel 1)
col2 = alt.Chart(df).mark_text(align='left', dx=20, fontStyle='italic', size=10, color='#555').encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L2:N'
).properties(width=160, height=h)

# Barras del Gantt
bars = alt.Chart(df).mark_bar(cornerRadius=1, size=15).encode(
    x=alt.X('Start:T', axis=alt.Axis(title=None, format='%d/%m')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None)
).properties(width=600, height=h)

# El secreto es spacing=0 para que no haya aire entre las columnas de nombres
gantt = alt.hconcat(col0, col1, col2, bars, spacing=0).configure_view(stroke=None)

st.altair_chart(gantt, use_container_width=False)

# 4. TABLA
st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)
