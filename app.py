import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(layout="wide", page_title="Gantt Obra Completo")

st.title("📊 Planificación de Obra - Listado Completo")

# -------------------- DATOS COMPLETOS (SIGUIENDO TUS IMÁGENES) --------------------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # He incluido todas las tareas que aparecen en tus capturas de pantalla
    tasks = [
        # 1. INSTALACIÓN ELÉCTRICA
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
        {"Task": "Puestas a Tierra", "Level": 1, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=20)},
        {"Task": "Vallado", "Level": 2, "Start": base + timedelta(days=12), "Finish": base + timedelta(days=15)},
        {"Task": "TSMs", "Level": 2, "Start": base + timedelta(days=13), "Finish": base + timedelta(days=16)},
        {"Task": "Box TSM", "Level": 2, "Start": base + timedelta(days=14), "Finish": base + timedelta(days=17)},
        {"Task": "CCTV", "Level": 2, "Start": base + timedelta(days=15), "Finish": base + timedelta(days=18)},
        {"Task": "Trackers", "Level": 2, "Start": base + timedelta(days=16), "Finish": base + timedelta(days=19)},
        {"Task": "Pruebas", "Level": 1, "Start": base + timedelta(days=20), "Finish": base + timedelta(days=28)},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Start": base + timedelta(days=20), "Finish": base + timedelta(days=22)},
        {"Task": "Polaridades CT", "Level": 2, "Start": base + timedelta(days=22), "Finish": base + timedelta(days=24)},
        {"Task": "Curvas IV", "Level": 2, "Start": base + timedelta(days=24), "Finish": base + timedelta(days=28)},

        # 2. COMUNICACIONES
        {"Task": "2: COMUNICACIONES", "Level": 0, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=45)},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=35)},
        {"Task": "CT1 / CT2", "Level": 2, "Start": base + timedelta(days=25), "Finish": base + timedelta(days=28)},
        {"Task": "Sensores Temperatura", "Level": 2, "Start": base + timedelta(days=27), "Finish": base + timedelta(days=30)},
        {"Task": "Rack / Cuadro Monit SC", "Level": 2, "Start": base + timedelta(days=29), "Finish": base + timedelta(days=32)},
        {"Task": "Fusionado Fibras", "Level": 1, "Start": base + timedelta(days=35), "Finish": base + timedelta(days=45)},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base + timedelta(days=35), "Finish": base + timedelta(days=38)},

        # 3. SENSORES
        {"Task": "3: SENSORES", "Level": 0, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=50)},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base + timedelta(days=40), "Finish": base + timedelta(days=48)},
        {"Task": "Piranómetros / Estación Met.", "Level": 2, "Start": base + timedelta(days=42), "Finish": base + timedelta(days=46)},

        # 5. CTs
        {"Task": "5: CTs", "Level": 0, "Start": base + timedelta(days=50), "Finish": base + timedelta(days=60)},
        {"Task": "Equipamiento CT2", "Level": 1, "Start": base + timedelta(days=50), "Finish": base + timedelta(days=58)},

        # 7. CCTV
        {"Task": "7: CCTV", "Level": 0, "Start": base + timedelta(days=60), "Finish": base + timedelta(days=70)},

        # 9. TRACKERS
        {"Task": "9: Trackers", "Level": 0, "Start": base + timedelta(days=70), "Finish": base + timedelta(days=80)},
    ]
    st.session_state.df = pd.DataFrame(tasks)
    st.session_state.df["Status"] = "Sin iniciar"

# -------------------- TRUCO DE ORDEN --------------------
df_plot = st.session_state.df.copy()

# 1. Crear sangría visual
def indent(row):
    return "\u00A0" * (int(row["Level"]) * 10) + row["Task"]

df_plot["Task_display"] = df_plot.apply(indent, axis=1)

# 2. LISTA DE ORDEN INVERSO
# Plotly dibuja de ABAJO hacia ARRIBA. Para que el "1" esté arriba,
# le pasamos la lista de tareas al revés.
reverse_order = df_plot["Task_display"].tolist()[::-1]

# -------------------- GRÁFICO --------------------
fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="Task_display", 
    color="Level",
    category_orders={"Task_display": reverse_order},
    color_continuous_scale="Blues"
)

fig.update_yaxes(title=None)
fig.update_layout(height=1200, margin=dict(l=350), showlegend=False)

st.plotly_chart(fig, use_container_width=True)

# -------------------- TABLA COMPLETA --------------------
st.subheader("📝 Editor de Tareas (Cualquier cambio actualiza el gráfico)")
st.session_state.df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
