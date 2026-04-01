import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Profesional Compacto")

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

df = st.session_state.df.copy()

# --- EL TRUCO PARA EL ESCALONADO COMPACTO ---
# Calculamos el desplazamiento físico (padding) en una columna nueva
# Nivel 0 = 0px, Nivel 1 = 15px, Nivel 2 = 30px
df['padding'] = df['Level'] * 15

# 2. GRÁFICO
h = len(df) * 22

# Columna de nombres con desplazamiento calculado desde Pandas
task_labels = alt.Chart(df).mark_text(align='left', size=11).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='Task:N',
    x=alt.X('padding:Q', axis=None), # Usamos una escala cuantitativa invisible para la posición X
    fontWeight=alt.condition('datum.Level == 0', alt.value('bold'), alt.value('normal')),
    color=alt.condition('datum.Level == 2', alt.value('#666'), alt.value('black'))
).properties(width=350, height=h)

# Barras del cronograma
bars = alt.Chart(df).mark_bar(cornerRadius=2, size=16).encode(
    x=alt.X('Start:T', axis=alt.Axis(title=None, format='%d/%m')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None)
).properties(width=600, height=h)

# Concatenamos con un espacio mínimo (spacing=5) para que estén pegados
layout = alt.hconcat(task_labels, bars, spacing=5).configure_view(stroke=None)

st.altair_chart(layout, use_container_width=False)

# 3. EDITOR
st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)
