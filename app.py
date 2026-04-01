import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. Configuración de la página (DEBE SER EL PRIMER COMANDO DE STREAMLIT)
st.set_page_config(layout="wide", page_title="Gantt Jerárquico")

# -------------------- FECHA BASE --------------------
base_date = datetime(2026, 4, 1)

st.title("📊 Gantt jerárquico PV - Plantilla completa")

# -------------------- DATOS INICIALES --------------------
if "df" not in st.session_state:
    tasks = [
        {"Task": "1: Instalación eléctrica", "Level": 0, "Parent": None, "Start": base_date, "Finish": base_date + timedelta(days=15), "Status": "En curso"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: Instalación eléctrica", "Start": base_date, "Finish": base_date + timedelta(days=12), "Status": "En curso"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date, "Finish": base_date + timedelta(days=5), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=1), "Finish": base_date + timedelta(days=6), "Status": "Completado"},
        {"Task": "Cuadro Comunicaciones CT2", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=3), "Finish": base_date + timedelta(days=8), "Status": "Completado"},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=10), "Status": "En curso"},
        {"Task": "2: Comunicaciones", "Level": 0, "Parent": None, "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=20), "Status": "Sin iniciar"},
        {"Task": "Tendido Cableado", "Level": 1, "Parent": "2: Comunicaciones", "Start": base_date + timedelta(days=6), "Finish": base_date + timedelta(days=15), "Status": "Sin iniciar"},
        {"Task": "Rack", "Level": 2, "Parent": "Tendido Cableado", "Start": base_date + timedelta(days=7), "Finish": base_date + timedelta(days=12), "Status": "Sin iniciar"},
    ]
    st.session_state.df = pd.DataFrame(tasks)

# -------------------- PROCESAMIENTO Y GRÁFICO --------------------
st.subheader("📈 Gantt")

df_plot = st.session_state.df.copy()

# Función para aplicar el escalonado (indentación)
def format_task_name(row):
    # Usamos \u00A0 (espacio de no ruptura) para que el navegador no los colapse
    indent = "\u00A0" * (int(row["Level"]) * 8) 
    if row["Level"] == 0:
        return f"<b>{row['Task']}</b>"
    return f"{indent}{row['Task']}"

df_plot["Task_display"] = df_plot.apply(format_task_name, axis=1)

# Creamos el gráfico asegurando que las fechas no sean nulas para el plot
df_plot_filtered = df_plot.dropna(subset=['Start', 'Finish'])

fig = px.timeline(
    df_plot_filtered, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Status",
    category_orders={"Task_display": df_plot["Task_display"].tolist()} # Mantiene el orden jerárquico
)

fig.update_yaxes(autorange="reversed")
fig.update_layout(
    xaxis_title="Cronograma",
    yaxis_title=None,
    margin=dict(l=250), # Espacio para que las etiquetas largas no se corten
)

st.plotly_chart(fig, use_container_width=True)

# -------------------- TABLA DE EDICIÓN --------------------
st.subheader("📝 Editar tareas")
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
st.session_state.df = edited_df
