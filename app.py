import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(layout="wide", page_title="Gantt Profesional Ordenado")

# -------------------- DATOS DE LA IMAGEN (ORDENADOS) --------------------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # Definimos la lista en el orden EXACTO que debe aparecer
    tasks = [
        # GRUPO 1
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Start": base, "Finish": base + timedelta(days=20), "Status": "En curso"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base, "Finish": base + timedelta(days=12), "Status": "En curso"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base, "Finish": base + timedelta(days=5), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=2), "Finish": base + timedelta(days=7), "Status": "Completado"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Start": base + timedelta(days=3), "Finish": base + timedelta(days=8), "Status": "Completado"},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Start": base + timedelta(days=5), "Finish": base + timedelta(days=10), "Status": "En curso"},
        {"Task": "Puestas a Tierra", "Level": 1, "Start": base + timedelta(days=10), "Finish": base + timedelta(days=15), "Status": "Sin iniciar"},
        {"Task": "Vallado", "Level": 2, "Start": base + timedelta(days=10), "Finish": base + timedelta(days=13), "Status": "Sin iniciar"},
        
        # GRUPO 2
        {"Task": "2: COMUNICACIONES", "Level": 0, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=30), "Status": "Sin iniciar"},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=25), "Status": "Sin iniciar"},
        {"Task": "Rack / Cuadro Monit SC", "Level": 2, "Start": base + timedelta(days=18), "Finish": base + timedelta(days=24), "Status": "Sin iniciar"},
        {"Task": "Fusionado Fibras", "Level": 1, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=30), "Status": "Sin iniciar"},

        # GRUPO 3
        {"Task": "3: SENSORES", "Level": 0, "Start": base + timedelta(days=30), "Finish": base + timedelta(days=40), "Status": "Sin iniciar"},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base + timedelta(days=30), "Finish": base + timedelta(days=38), "Status": "Sin iniciar"},
        {"Task": "Piranómetros / Estación Met.", "Level": 2, "Start": base + timedelta(days=32), "Finish": base + timedelta(days=37), "Status": "Sin iniciar"},

        # GRUPO 5
        {"Task": "5: CTS", "Level": 0, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=50), "Status": "Sin iniciar"},
        {"Task": "Equipamiento CT2", "Level": 1, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=48), "Status": "Sin iniciar"},
    ]
    st.session_state.df = pd.DataFrame(tasks)

# -------------------- PROCESAMIENTO --------------------
df_plot = st.session_state.df.copy()

# Formateo de nombres con indentación (escalonado)
def format_task(row):
    indent = "\u00A0" * (int(row["Level"]) * 10)
    name = str(row["Task"])
    return f"{indent}{name}"

df_plot["Task_display"] = df_plot.apply(format_task, axis=1)

# IMPORTANTE: Crear la lista de orden basado en la tabla actual
lista_ordenada = df_plot["Task_display"].tolist()

# -------------------- GRÁFICO --------------------
st.title("📊 Planificación de Obra (Orden Jerárquico)")

fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Status",
    # ESTA LÍNEA ARREGLA EL DESORDEN:
    category_orders={"Task_display": lista_ordenada},
    color_discrete_map={"Completado": "#27AE60", "En curso": "#2980B9", "Sin iniciar": "#BDC3C7"}
)

fig.update_yaxes(autorange="reversed") # Pone la tarea 1 arriba
fig.update_layout(
    height=700, 
    margin=dict(l=350), # Margen para que se vean los nombres largos
    xaxis_title="Abril - Mayo 2026",
    yaxis_title=None
)

st.plotly_chart(fig, use_container_width=True)

# -------------------- EDITOR --------------------
st.subheader("📝 Editar o Añadir Tareas")
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df
    st.rerun()
