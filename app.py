import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(layout="wide", page_title="Gantt Obra Completo")

st.title("📊 Planificación de Obra - Listado Maestro")

# 2. CARGA DE DATOS COMPLETOS (SEGÚN TU EXCEL)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks = [
        # --- 1: INSTALACIÓN ELÉCTRICA ---
        {"Task": "1: Instalación eléctrica", "Level": 0, "Start": base, "Finish": base + timedelta(days=30)},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base, "Finish": base + timedelta(days=15)},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base, "Finish": base + timedelta(days=6)},
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
        {"Task": "Vallado", "Level": 2, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=15)},
        {"Task": "TSMs", "Level": 2, "Start": base + timedelta(days=13), "Finish": base + timedelta(days=16)},
        {"Task": "Box TSM", "Level": 2, "Start": base + timedelta(days=14), "Finish": base + timedelta(days=17)},
        {"Task": "CCTV", "Level": 2, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=18)},
        {"Task": "Trackers", "Level": 2, "Start": base + timedelta(days=16), "Finish": base + timedelta(days=19)},
        {"Task": "Pruebas", "Level": 1, "Start": base + timedelta(days=20), "Finish": base + timedelta(days=30)},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Start": base + timedelta(days=20), "Finish": base + timedelta(days=22)},
        {"Task": "Polaridades CT", "Level": 2, "Start": base + timedelta(days=22), "Finish": base + timedelta(days=24)},
        {"Task": "Curvas IV", "Level": 2, "Start": base + timedelta(days=24), "Finish": base + timedelta(days=28)},
        
        # --- 2: COMUNICACIONES ---
        {"Task": "2: COMUNICACIONES", "Level": 0, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=45)},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=35)},
        {"Task": "CT1 / CT2", "Level": 2, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=28)},
        {"Task": "Sensores Temperatura", "Level": 2, "Start": base + timedelta(days=28), "Finish": base + timedelta(days=31)},
        {"Task": "Rack / Cuadro Monit SC", "Level": 2, "Start": base + timedelta(days=31), "Finish": base + timedelta(days=34)},
        {"Task": "Fusionado Fibras", "Level": 1, "Start": base + timedelta(days=35), "Finish": base + timedelta(days=45)},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=35), "Finish": base + timedelta(days=38)},

        # --- 3: SENSORES ---
        {"Task": "3: SENSORES", "Level": 0, "Start": base + timedelta(days=45), "Finish": base + timedelta(days=55)},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base + timedelta(days=45), "Finish": base + timedelta(days=52)},
        {"Task": "Piranómetros / Estación Met.", "Level": 2, "Start": base + timedelta(days=47), "Finish": base + timedelta(days=52)},

        # --- RESTO DE GRUPOS ---
        {"Task": "5: CTs", "Level": 0, "Start": base + timedelta(days=55), "Finish": base + timedelta(days=65)},
        {"Task": "Equipamiento CT2", "Level": 1, "Start": base + timedelta(days=55), "Finish": base + timedelta(days=62)},
        {"Task": "7: CCTV", "Level": 0, "Start": base + timedelta(days=65), "Finish": base + timedelta(days=75)},
        {"Task": "9: Trackers", "Level": 0, "Start": base + timedelta(days=75), "Finish": base + timedelta(days=85)},
    ]
    st.session_state.df = pd.DataFrame(tasks)

# 3. PROCESAMIENTO
df_plot = st.session_state.df.copy()
df_plot['unique_id'] = range(len(df_plot))

def get_label(row):
    # Indentación basada en nivel (8 espacios por nivel)
    return "\u00A0" * (int(row["Level"]) * 8) + str(row["Task"])

df_plot["Task_display"] = df_plot.apply(get_label, axis=1)

# 4. GRÁFICO CON ALTURA DINÁMICA
dynamic_height = len(df_plot) * 30 + 150

fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="unique_id",
    color="Level",
    color_continuous_scale="Blues"
)

fig.update_yaxes(
    tickmode='array',
    tickvals=df_plot['unique_id'],
    ticktext=df_plot['Task_display'],
    autorange="reversed",
    title=None
)

fig.update_layout(
    height=dynamic_height,
    margin=dict(l=450, r=20, t=50, b=50),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# 5. EDITOR
st.subheader("📝 Editor de Datos (Excel Completo)")
st.session_state.df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
