import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(layout="wide", page_title="Gantt Orden Correcto")

st.title("📊 Planificación de Obra")

# -------------------- DATOS --------------------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # Lista en el orden que quieres ver de ARRIBA hacia ABAJO
    tasks = [
        {"Task": "1: Instalación eléctrica", "Level": 0, "Start": base, "Finish": base + timedelta(days=20)},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base, "Finish": base + timedelta(days=12)},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base, "Finish": base + timedelta(days=5)},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=2), "Finish": base + timedelta(days=7)},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Start": base + timedelta(days=3), "Finish": base + timedelta(days=8)},
        {"Task": "Cuadro Comunicaciones CT2", "Level": 2, "Start": base + timedelta(days=4), "Finish": base + timedelta(days=9)},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Start": base + timedelta(days=5), "Finish": base + timedelta(days=10)},
        {"Task": "2: COMUNICACIONES", "Level": 0, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=30)},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=25)},
        {"Task": "3: SENSORES", "Level": 0, "Start": base + timedelta(days=30), "Finish": base + timedelta(days=40)},
        {"Task": "5: CTs", "Level": 0, "Start": base + timedelta(days=35), "Finish": base + timedelta(days=45)},
        {"Task": "7: CCTV", "Level": 0, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=50)},
        {"Task": "9: Trackers", "Level": 0, "Start": base + timedelta(days=45), "Finish": base + timedelta(days=55)},
    ]
    st.session_state.df = pd.DataFrame(tasks)
    st.session_state.df["Status"] = "Sin iniciar"

# -------------------- PROCESAMIENTO --------------------
df_plot = st.session_state.df.copy()

# Crear indentación visual
def format_label(row):
    prefix = "\u00A0" * (int(row["Level"]) * 8)
    return f"{prefix}{row['Task']}"

df_plot["Task_display"] = df_plot.apply(format_label, axis=1)

# CAPTURAR EL ORDEN ORIGINAL (1 al 9)
# Invertimos la lista de etiquetas porque Plotly lee el eje Y de abajo hacia arriba
lista_ordenada_inversa = df_plot["Task_display"].tolist()[::-1]

# -------------------- GRÁFICO --------------------
fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Level",
    # Forzamos a Plotly a usar el orden inverso de la lista para que el tope sea el "1"
    category_orders={"Task_display": lista_ordenada_inversa}
)

# Ajustes de diseño
fig.update_yaxes(title=None)
fig.update_layout(
    height=800,
    margin=dict(l=300),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# -------------------- EDITOR --------------------
st.subheader("📝 Tabla de Datos")
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df
    st.rerun()
