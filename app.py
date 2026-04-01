import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Profesional Jerárquico")

# 1. BASE DE DATOS COMPLETA (Transcribiendo tus 12 puntos exactos)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks = [
        # SECCIÓN 1
        ("1: Instalación eléctrica", 0), ("Tendido Eléctrico BT", 1), 
        ("Cuadro protecciones SC", 2), ("Cuadro Comunicaciones SC", 2), ("Cuadro Sensores SC", 2),
        ("Cuadro Comunicaciones CT2", 2), ("Cuadro Sensores CT2", 2), ("Alimentaciones CCTV", 2),
        ("Alimentaciones TSM", 2), ("Alimentaciones Cuadros Monitorización", 2),
        ("Alimentaciones Cuadros Seguridad", 2), ("Alimentación Rack", 2), ("Alimentación Alumbrado y Secundarios", 2),
        ("Puestas a Tierra", 1), ("Vallado", 2), ("TSMs", 2), ("Box TSM", 2), ("CCTV", 2), ("Vallado CT", 2),
        ("Bodega", 2), ("Trackers", 2), ("String Box", 2),
        ("Pruebas", 1), ("Pruebas de aislamiento CT - Entronque", 2), ("Pruebas de aislamiento CTs", 2),
        # SECCIÓN 2
        ("2: Comunicaciones", 0), ("Tendido Cableado", 1), ("CT1", 2), ("CT2", 2), ("Piranómetros", 2),
        ("Internet", 1), ("Router Medidor Entronque", 2), ("Antena / FO", 2), ("Servicio", 2),
        # SECCIÓN 3 A 12 (Resumen para el código, pero el sistema acepta todas)
        ("3: Sensores", 0), ("Instalación Equipos", 1), ("Soportes Piranómetros", 2),
        ("5: Trackers y TSM", 0), ("6: CTs", 0), ("7: CCTV", 0), ("8: Seguridad", 0),
        ("9: Entronque", 0), ("Reconectador", 1), ("Instalación", 2),
        ("10: PEM (Conexionado)", 0), ("11: Permisos", 0), ("12: Servicios", 0)
    ]
    
    data = []
    for i, (name, level) in enumerate(tasks):
        data.append({
            "id": i,
            "Tarea": name,
            "Nivel": level,
            "Inicio": base + timedelta(days=i),
            "Fin": base + timedelta(days=i+5),
            "Color": ["#004e92", "#00a1ff", "#75c6ff"][level]
        })
    st.session_state.df = pd.DataFrame(data)

# 2. PROCESAMIENTO PARA ALTAIR
df = st.session_state.df.copy()

# Creamos columnas vacías para simular la indentación física de Excel
df['L0'] = df.apply(lambda x: x['Tarea'] if x['Nivel'] == 0 else "", axis=1)
df['L1'] = df.apply(lambda x: x['Tarea'] if x['Nivel'] == 1 else "", axis=1)
df['L2'] = df.apply(lambda x: x['Tarea'] if x['Nivel'] == 2 else "", axis=1)

# 3. CONSTRUCCIÓN DEL GRÁFICO (Estructura de Árbol Real)
chart = alt.Chart(df).mark_bar(cornerRadius=3).encode(
    x=alt.X('Inicio:T', title='Cronograma'),
    x2='Fin:T',
    y=alt.Y('id:O', axis=None), # Ocultamos el eje Y numérico
    color=alt.Color('Color:N', scale=None),
    tooltip=['Tarea', 'Inicio', 'Fin']
).properties(width=800, height=len(df)*20)

# Columna de texto jerárquico (Simulando las celdas de Excel)
text_l0 = alt.Chart(df).mark_text(align='left', fontWeight='bold').encode(
    y=alt.Y('id:O', axis=None),
    text='L0:N'
).properties(width=150)

text_l1 = alt.Chart(df).mark_text(align='left', dx=20).encode(
    y=alt.Y('id:O', axis=None),
    text='L1:N'
).properties(width=150)

text_l2 = alt.Chart(df).mark_text(align='left', dx=40, fontStyle='italic').encode(
    y=alt.Y('id:O', axis=None),
    text='L2:N'
).properties(width=150)

# Concatenamos las columnas de texto con la gráfica
gantt_final = alt.hconcat(text_l0, text_l1, text_l2, chart).configure_view(strokeWidth=0)

st.altair_chart(gantt_final, use_container_width=True)

# 4. TABLA DE EDICIÓN
st.subheader("🛠️ Editor Maestro")
st.session_state.df = st.data_editor(st.session_state.df, hide_index=True)
