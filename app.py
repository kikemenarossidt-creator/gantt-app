import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Estructural")

# 1. BASE DE DATOS COMPLETA (1-12) CON NOMBRES DE COLUMNA FIJOS
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    # Lista completa basada en tus requerimientos
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
        ("Pruebas de aislamiento BT", 2), ("Polaridades CT", 2), ("Termografías", 2),
        ("Curvas IV", 2), ("Continuidad de Tierras", 2), ("Arc Flash", 2),
        ("2: COMUNICACIONES", 0), ("Tendido Cableado", 1), ("CT1", 2), ("CT2", 2),
        ("Piranómetros", 2), ("Sensores Temperatura", 2), ("Estación Meteorológica", 2),
        ("TSMs", 2), ("Cuadro Monit CT2", 2), ("Cuadro Seguridad CT2", 2), ("Rack", 2),
        ("Internet", 1), ("Router Medidor Entronque", 2), ("Antena / FO Entronque", 2),
        ("3: SENSORES", 0), ("Instalación Equipos", 1), ("Soportes Piranómetros", 2),
        ("5: TRACKERS Y TSM", 0), ("TSM", 1), ("TSC", 1), ("Comisionado Tracker", 1),
        ("6: CTs", 0), ("Preparación PEM CT", 1), ("Comisionado", 1),
        ("7: CCTV", 0), ("Instalación Equipos", 1), ("Comisionado", 1),
        ("8: SEGURIDAD", 0), ("Guardias", 1),
        ("9: ENTRONQUE", 0), ("Reconectador", 1), ("Medidor", 1), ("Empalme Línea", 1),
        ("10: PEM (CONEXIONADO)", 0), ("CT", 1), ("Medidor", 1), ("Reco", 1),
        ("11: PERMISOS", 0), ("SEC (TE1/TE7)", 1), ("CEN", 1), ("SEREMI", 1),
        ("12: SERVICIOS", 0), ("Limpieza Módulos", 1), ("Desbroce", 1)
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

# 2. PREPARACIÓN DE COLUMNAS PARA EL ESCALONADO (Sin KeyErrors)
df = st.session_state.df.copy()

# Creamos las columnas de niveles asegurándonos de que existan
df['L0'] = df.apply(lambda x: x['Task'] if x['Level'] == 0 else "", axis=1)
df['L1'] = df.apply(lambda x: x['Task'] if x['Level'] == 1 else "", axis=1)
df['L2'] = df.apply(lambda x: x['Task'] if x['Level'] == 2 else "", axis=1)

# 3. GRÁFICO DE ALTAIR (Estructura de celdas real)
# Definimos la altura dinámica
h = len(df) * 22

# Columna Nivel 0 (Padres)
col0 = alt.Chart(df).mark_text(align='left', fontWeight='bold', size=12).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L0:N'
).properties(width=180, height=h)

# Columna Nivel 1 (Hijos)
col1 = alt.Chart(df).mark_text(align='left', dx=15, color='#333').encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L1:N'
).properties(width=180, height=h)

# Columna Nivel 2 (Sub-hijos)
col2 = alt.Chart(df).mark_text(align='left', dx=30, fontStyle='italic', color='#666').encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L2:N'
).properties(width=200, height=h)

# Barras del Gantt
bars = alt.Chart(df).mark_bar(cornerRadius=2, size=18).encode(
    x=alt.X('Start:T', title='Abril 2026', axis=alt.Axis(format='%d %b')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#1f77b4', '#4db3ff', '#a1d9ff']), legend=None)
).properties(width=600, height=h)

# Unión final (H-Concat) para que se vea como un Excel
st.altair_chart(alt.hconcat(col0, col1, col2, bars).configure_view(stroke=None), use_container_width=False)

# 4. EDITOR
st.subheader("📝 Editar Datos")
st.session_state.df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)
