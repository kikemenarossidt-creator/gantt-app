import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN (Debe ser la primera línea)
st.set_page_config(layout="wide", page_title="Gantt Profesional")

st.title("📊 Planificación de Obra - Listado Completo")

# 2. TODAS LAS TAREAS (Basado en tus imágenes)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks = [
        # GRUPO 1: ELÉCTRICA
        {"Task": "1: Instalación eléctrica", "Level": 0, "Start": base, "Finish": base + timedelta(days=20)},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base, "Finish": base + timedelta(days=12)},
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
        {"Task": "Puestas a Tierra", "Level": 1, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=18)},
        {"Task": "Vallado", "Level": 2, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=15)},
        {"Task": "TSMs", "Level": 2, "Start": base + timedelta(days=13), "Finish": base + timedelta(days=16)},
        {"Task": "Box TSM", "Level": 2, "Start": base + timedelta(days=14), "Finish": base + timedelta(days=17)},
        {"Task": "CCTV", "Level": 2, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=18)},
        {"Task": "Trackers", "Level": 2, "Start": base + timedelta(days=16), "Finish": base + timedelta(days=19)},
        {"Task": "Pruebas", "Level": 1, "Start": base + timedelta(days=19), "Finish": base + timedelta(days=25)},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Start": base + timedelta(days=19), "Finish": base + timedelta(days=21)},
        {"Task": "Polaridades CT", "Level": 2, "Start": base + timedelta(days=21), "Finish": base + timedelta(days=23)},
        {"Task": "Curvas IV", "Level": 2, "Start": base + timedelta(days=23), "Finish": base + timedelta(days=25)},

        # GRUPO 2: COMUNICACIONES
        {"Task": "2: COMUNICACIONES", "Level": 0, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=40)},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=32)},
        {"Task": "CT1 / CT2", "Level": 2, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=28)},
        {"Task": "Sensores Temperatura", "Level": 2, "Start": base + timedelta(days=27), "Finish": base + timedelta(days=30)},
        {"Task": "Rack / Cuadro Monit SC", "Level": 2, "Start": base + timedelta(days=29), "Finish": base + timedelta(days=32)},
        {"Task": "Fusionado Fibras", "Level": 1, "Start": base + timedelta(days=33), "Finish": base + timedelta(days=40)},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=33), "Finish": base + timedelta(days=36)},

        # GRUPO 3: SENSORES
        {"Task": "3: SENSORES", "Level": 0, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=50)},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=48)},
        {"Task": "Piranómetros / Estación Met.", "Level": 2, "Start": base + timedelta(days=42), "Finish": base + timedelta(days=46)},

        # OTROS
        {"Task": "5: CTs", "Level": 0, "Start": base + timedelta(days=50), "Finish": base + timedelta(days=60)},
        {"Task": "7: CCTV", "Level": 0, "Start": base + timedelta(days=60), "Finish": base + timedelta(days=70)},
        {"Task": "9: Trackers", "Level": 0, "Start": base + timedelta(days=70), "Finish": base + timedelta(days=80)},
    ]
    st.session_state.df = pd.DataFrame(tasks)
    st.session_state.df["Status"] = "Sin iniciar"

# 3. FORMATEO Y ALTURA DINÁMICA
df_plot = st.session_state.df.copy()
def format_task(row):
    return "\u00A0" * (int(row["Level"]) * 8) + row["Task"]

df_plot["Task_display"] = df_plot.apply(format_task, axis=1)
labels_ordered = df_plot["Task_display"].tolist()

# Calculamos altura: 25 píxeles por cada tarea + 100 de márgenes
dynamic_height = len(df_plot) * 25 + 100

# 4. GRÁFICO SIN ERRORES DE EJE
fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Level",
    category_orders={"Task_display": labels_ordered[::-1]}, # Inverso para que el 1 esté arriba
    color_continuous_scale="Blues"
)

fig.update_yaxes(
    autorange=True,
    dtick=1, # FUERZA A MOSTRAR TODAS LAS TAREAS
    title=None
)

fig.update_layout(
    height=dynamic_height, 
    margin=dict(l=400, r=20, t=20, b=20), # Margen izquierdo grande para nombres
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# 5. TABLA DE CONTROL
st.subheader("📝 Tabla de Datos")
st.session_state.df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
