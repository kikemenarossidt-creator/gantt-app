import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(layout="wide", page_title="Gantt Jerárquico Ordenado")

# -------------------- DATOS INICIALES (ORDENADOS) --------------------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # He organizado la lista siguiendo exactamente el orden de tu imagen
    tasks = [
        # GRUPO 1: INSTALACIÓN ELÉCTRICA
        {"Task": "1: Instalación eléctrica", "Level": 0, "Start": base, "Finish": base + timedelta(days=20), "Status": "En curso"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base, "Finish": base + timedelta(days=12), "Status": "En curso"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base, "Finish": base + timedelta(days=5), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=2), "Finish": base + timedelta(days=7), "Status": "Completado"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Start": base + timedelta(days=3), "Finish": base + timedelta(days=8), "Status": "Completado"},
        {"Task": "Cuadro Comunicaciones CT2", "Level": 2, "Start": base + timedelta(days=4), "Finish": base + timedelta(days=9), "Status": "Sin iniciar"},
        {"Task": "Cuadro Sensores CT2", "Level": 2, "Start": base + timedelta(days=5), "Finish": base + timedelta(days=10), "Status": "Sin iniciar"},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Start": base + timedelta(days=6), "Finish": base + timedelta(days=11), "Status": "En curso"},
        {"Task": "Alimentaciones TSM", "Level": 2, "Start": base + timedelta(days=7), "Finish": base + timedelta(days=12), "Status": "Sin iniciar"},
        {"Task": "Alimentaciones Cuadros Monitorización", "Level": 2, "Start": base + timedelta(days=8), "Finish": base + timedelta(days=13), "Status": "Sin iniciar"},
        {"Task": "Alimentaciones Cuadros Seguridad", "Level": 2, "Start": base + timedelta(days=9), "Finish": base + timedelta(days=14), "Status": "Sin iniciar"},
        {"Task": "Alimentación Rack", "Level": 2, "Start": base + timedelta(days=10), "Finish": base + timedelta(days=15), "Status": "Sin iniciar"},
        {"Task": "Alimentación Alumbrado y Secundarios", "Level": 2, "Start": base + timedelta(days=11), "Finish": base + timedelta(days=16), "Status": "Sin iniciar"},
        {"Task": "Puestas a Tierra", "Level": 1, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=18), "Status": "Sin iniciar"},
        {"Task": "Vallado", "Level": 2, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=15), "Status": "Sin iniciar"},
        {"Task": "TSMs", "Level": 2, "Start": base + timedelta(days=13), "Finish": base + timedelta(days=16), "Status": "Sin iniciar"},
        {"Task": "Box TSM", "Level": 2, "Start": base + timedelta(days=14), "Finish": base + timedelta(days=17), "Status": "Sin iniciar"},
        {"Task": "CCTV", "Level": 2, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=18), "Status": "Sin iniciar"},
        {"Task": "Trackers", "Level": 2, "Start": base + timedelta(days=16), "Finish": base + timedelta(days=19), "Status": "Sin iniciar"},
        {"Task": "Pruebas", "Level": 1, "Start": base + timedelta(days=19), "Finish": base + timedelta(days=25), "Status": "Sin iniciar"},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Start": base + timedelta(days=19), "Finish": base + timedelta(days=21), "Status": "Sin iniciar"},
        {"Task": "Polaridades CT", "Level": 2, "Start": base + timedelta(days=21), "Finish": base + timedelta(days=23), "Status": "Sin iniciar"},
        {"Task": "Curvas IV", "Level": 2, "Start": base + timedelta(days=23), "Finish": base + timedelta(days=25), "Status": "Sin iniciar"},

        # GRUPO 2: COMUNICACIONES
        {"Task": "2: Comunicaciones", "Level": 0, "Start": base + timedelta(days=20), "Finish": base + timedelta(days=35), "Status": "Sin iniciar"},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base + timedelta(days=20), "Finish": base + timedelta(days=28), "Status": "Sin iniciar"},
        {"Task": "CT1 / CT2", "Level": 2, "Start": base + timedelta(days=20), "Finish": base + timedelta(days=23), "Status": "Sin iniciar"},
        {"Task": "Sensores Temperatura", "Level": 2, "Start": base + timedelta(days=22), "Finish": base + timedelta(days=24), "Status": "Sin iniciar"},
        {"Task": "Rack / Cuadro Monit SC", "Level": 2, "Start": base + timedelta(days=24), "Finish": base + timedelta(days=27), "Status": "Sin iniciar"},
        {"Task": "Fusionado Fibras", "Level": 1, "Start": base + timedelta(days=28), "Finish": base + timedelta(days=33), "Status": "Sin iniciar"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=28), "Finish": base + timedelta(days=31), "Status": "Sin iniciar"},

        # GRUPO 3: SENSORES
        {"Task": "3: Sensores", "Level": 0, "Start": base + timedelta(days=30), "Finish": base + timedelta(days=40), "Status": "Sin iniciar"},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base + timedelta(days=30), "Finish": base + timedelta(days=38), "Status": "Sin iniciar"},
        {"Task": "Piranómetros / Estación Met.", "Level": 2, "Start": base + timedelta(days=32), "Finish": base + timedelta(days=37), "Status": "Sin iniciar"},

        # GRUPO 5: CTS
        {"Task": "5: CTs", "Level": 0, "Start": base + timedelta(days=35), "Finish": base + timedelta(days=45), "Status": "Sin iniciar"},
        {"Task": "Equipamiento CT2", "Level": 1, "Start": base + timedelta(days=35), "Finish": base + timedelta(days=42), "Status": "Sin iniciar"},

        # OTROS GRUPOS
        {"Task": "7: CCTV", "Level": 0, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=50), "Status": "Sin iniciar"},
        {"Task": "9: Trackers", "Level": 0, "Start": base + timedelta(days=45), "Finish": base + timedelta(days=55), "Status": "Sin iniciar"},
    ]
    st.session_state.df = pd.DataFrame(tasks)

# -------------------- PROCESAMIENTO VISUAL --------------------
df_plot = st.session_state.df.copy()

# Función para aplicar el escalonado (indentación)
def format_task_name(row):
    name = str(row["Task"])
    level = int(row["Level"])
    # Usamos espacios de no ruptura para forzar la escalera visual
    indent = "\u00A0" * (level * 10) 
    if level == 0:
        return f"<b>{name.upper()}</b>"
    return f"{indent}{name}"

df_plot["Task_display"] = df_plot.apply(format_task_name, axis=1)

# -------------------- RENDERIZADO DEL GANTT --------------------
st.title("📊 Planificación de Obra (Orden Jerárquico Correcto)")

# CRUCIAL: Definir el orden exacto de las etiquetas para que Plotly no las mueva
orden_fijo = df_plot["Task_display"].tolist()

fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Status",
    # Esto obliga al gráfico a seguir el orden de tu lista
    category_orders={"Task_display": orden_fijo},
    color_discrete_map={
        "Completado": "#27AE60", # Verde
        "En curso": "#2980B9",   # Azul
        "Sin iniciar": "#BDC3C7" # Gris
    }
)

# Invertimos el eje Y para que la Tarea 1 aparezca ARRIBA
fig.update_yaxes(autorange="reversed", title=None)
fig.update_xaxes(title="Cronograma 2026")

fig.update_layout(
    height=900,
    margin=dict(l=350), # Espacio para los nombres con sangría
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

# -------------------- EDITOR DE TABLA --------------------
st.subheader("📝 Tabla de Edición")
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df
    st.rerun()
