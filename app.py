import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN (Debe ser lo primero)
st.set_page_config(layout="wide", page_title="Gantt Orden Estricto")

st.title("📊 Planificación de Obra - Orden Jerárquico Real")

# -------------------- DATOS INICIALES (ORDEN DE TU IMAGEN) --------------------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # Lista organizada exactamente como tu Excel
    tasks = [
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Start": base, "Finish": base + timedelta(days=30)},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base, "Finish": base + timedelta(days=15)},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base, "Finish": base + timedelta(days=5)},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=2), "Finish": base + timedelta(days=7)},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Start": base + timedelta(days=3), "Finish": base + timedelta(days=8)},
        {"Task": "Cuadro Comunicaciones CT2", "Level": 2, "Start": base + timedelta(days=4), "Finish": base + timedelta(days=9)},
        {"Task": "Cuadro Sensores CT2", "Level": 2, "Start": base + timedelta(days=5), "Finish": base + timedelta(days=10)},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Start": base + timedelta(days=6), "Finish": base + timedelta(days=11)},
        {"Task": "Alimentaciones TSM", "Level": 2, "Start": base + timedelta(days=7), "Finish": base + timedelta(days=12)},
        {"Task": "Alimentaciones Cuadros Monitorización", "Level": 2, "Start": base + timedelta(days=8), "Finish": base + timedelta(days=13)},
        {"Task": "Alimentaciones Cuadros Seguridad", "Level": 2, "Start": base + timedelta(days=9), "Finish": base + timedelta(days=14)},
        {"Task": "Alimentación Rack", "Level": 2, "Start": base + timedelta(days=10), "Finish": base + timedelta(days=15)},
        {"Task": "Alimentación Alumbrado y Secundarios", "Level": 2, "Start": base + timedelta(days=11), "Finish": base + timedelta(days=16)},
        {"Task": "Puestas a Tierra", "Level": 1, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=20)},
        {"Task": "Vallado", "Level": 2, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=17)},
        {"Task": "TSMs", "Level": 2, "Start": base + timedelta(days=13), "Finish": base + timedelta(days=18)},
        {"Task": "Box TSM", "Level": 2, "Start": base + timedelta(days=14), "Finish": base + timedelta(days=19)},
        {"Task": "CCTV", "Level": 2, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=20)},
        {"Task": "Trackers", "Level": 2, "Start": base + timedelta(days=16), "Finish": base + timedelta(days=21)},
        {"Task": "Pruebas", "Level": 1, "Start": base + timedelta(days=21), "Finish": base + timedelta(days=28)},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Start": base + timedelta(days=21), "Finish": base + timedelta(days=23)},
        {"Task": "Polaridades CT", "Level": 2, "Start": base + timedelta(days=23), "Finish": base + timedelta(days=25)},
        {"Task": "Curvas IV", "Level": 2, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=28)},
        {"Task": "2: COMUNICACIONES", "Level": 0, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=40)},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=25)},
        {"Task": "CT1 / CT2", "Level": 2, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=18)},
        {"Task": "Sensores Temperatura", "Level": 2, "Start": base + timedelta(days=18), "Finish": base + timedelta(days=21)},
        {"Task": "Rack / Cuadro Monit SC", "Level": 2, "Start": base + timedelta(days=21), "Finish": base + timedelta(days=24)},
        {"Task": "Fusionado Fibras", "Level": 1, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=35)},
        {"Task": "3: SENSORES", "Level": 0, "Start": base + timedelta(days=30), "Finish": base + timedelta(days=45)},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base + timedelta(days=30), "Finish": base + timedelta(days=40)},
        {"Task": "Piranómetros / Estación Met.", "Level": 2, "Start": base + timedelta(days=32), "Finish": base + timedelta(days=37)},
        {"Task": "5: CTS", "Level": 0, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=55)},
        {"Task": "7: CCTV", "Level": 0, "Start": base + timedelta(days=45), "Finish": base + timedelta(days=60)},
        {"Task": "9: TRACKERS", "Level": 0, "Start": base + timedelta(days=5), "Finish": base + timedelta(days=50)},
    ]
    st.session_state.df = pd.DataFrame(tasks)
    st.session_state.df["Status"] = "Sin iniciar"

# -------------------- FORMATEO VISUAL --------------------
df_plot = st.session_state.df.copy()

# Creamos una columna auxiliar para asegurar el orden
df_plot['order_id'] = range(len(df_plot))

def make_label(row):
    # Indentación exagerada para que se note la jerarquía
    spaces = "\u00A0" * (int(row["Level"]) * 8)
    return f"{spaces}{row['Task']}"

df_plot["Task_display"] = df_plot.apply(make_label, axis=1)

# -------------------- GRÁFICO GANTT --------------------
# Crucial: Ordenamos por 'order_id' y forzamos a Plotly a respetar ese orden
df_plot = df_plot.sort_values("order_id")

fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Level", # Color por nivel para ayudar a la vista
    category_orders={"Task_display": df_plot["Task_display"].tolist()} # ESTO FIJA EL ORDEN
)

# Invertimos el eje para que el índice 0 esté arriba
fig.update_yaxes(autorange="reversed", title=None)
fig.update_layout(height=1000, margin=dict(l=300))

st.plotly_chart(fig, use_container_width=True)

# -------------------- EDITOR DE DATOS --------------------
st.subheader("📝 Tabla de control")
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df
    st.rerun()
