import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Dinámico Retráctil")

# 1. BASE DE DATOS COMPLETA (Recuperando toda la jerarquía)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks_data = [
        ("1: INSTALACIÓN ELÉCTRICA", 0), 
        ("Tendido Eléctrico BT", 1), ("Cuadro protecciones SC", 2), ("Cuadro Comunicaciones SC", 2),
        ("Puestas a Tierra", 1), ("Vallado", 2), ("TSMs", 2),
        ("2: COMUNICACIONES", 0), 
        ("Tendido Cableado", 1), ("CT1", 2), ("CT2", 2),
        ("3: SENSORES", 0), ("Instalación Equipos", 1),
        ("4: MONTAJE ESTRUCTURAS", 0), ("Hincado", 1), ("Montaje Módulos", 1),
        ("5: TRACKERS Y TSM", 0), ("Instalación TSM", 1),
        ("9: ENTRONQUE", 0), ("Reconectador", 1), ("Medidor", 1),
        ("11: PERMISOS", 0), ("SEC (TE1/TE7)", 1),
        ("12: SERVICIOS", 0), ("Limpieza Módulos", 1)
    ]
    
    rows = []
    for i, (name, level) in enumerate(tasks_data):
        rows.append({
            "id": i,
            "Task": name,
            "Level": level,
            "Start": base + timedelta(days=i),
            "End": base + timedelta(days=i+2),
        })
    st.session_state.df = pd.DataFrame(rows)

# --- CONTROL RETRÁCTIL (TIPO EXCEL) ---
st.sidebar.header("Niveles de Detalle")
# Creamos botones que actúan como el selector 1, 2, 3 de Excel
nivel_seleccionado = st.sidebar.radio(
    "Selecciona profundidad de vista:",
    options=[0, 1, 2],
    format_func=lambda x: f"Nivel {x} (Solo Títulos)" if x == 0 else (f"Nivel {x} (Detalle Medio)" if x == 1 else "Nivel 2 (Mostrar Todo)"),
    index=2
)

# Filtramos el dataframe según el nivel seleccionado
df_filtered = st.session_state.df[st.session_state.df['Level'] <= nivel_seleccionado].copy()

# 2. PROCESAMIENTO DE COLUMNAS
df_filtered['L0'] = df_filtered.apply(lambda x: x['Task'] if x['Level'] == 0 else "", axis=1)
df_filtered['L1'] = df_filtered.apply(lambda x: x['Task'] if x['Level'] == 1 else "", axis=1)
df_filtered['L2'] = df_filtered.apply(lambda x: x['Task'] if x['Level'] == 2 else "", axis=1)

# 3. GRÁFICA AJUSTABLE
h = len(df_filtered) * 25

col0 = alt.Chart(df_filtered).mark_text(align='left', fontWeight='bold').encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L0:N'
).properties(width=160, height=h)

col1 = alt.Chart(df_filtered).mark_text(align='left', dx=10).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L1:N'
).properties(width=160, height=h)

col2 = alt.Chart(df_filtered).mark_text(align='left', dx=20, fontStyle='italic', color='#555').encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L2:N'
).properties(width=200, height=h)

bars = alt.Chart(df_filtered).mark_bar(cornerRadius=1).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None)
).properties(width=600, height=h)

gantt = alt.hconcat(col0, col1, col2, bars, spacing=0).configure_view(stroke=None)

st.altair_chart(gantt, use_container_width=False)

st.info(f"Mostrando hasta el Nivel {nivel_seleccionado}. Usa el panel de la izquierda para contraer o expandir.")
