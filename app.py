import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(layout="wide", page_title="Gantt Jerárquico Completo")

# -------------------- FECHA BASE --------------------
base_date = datetime(2026, 4, 1)

st.title("📊 Planificación de Obra - Plantilla Completa")
st.markdown("---")

# -------------------- CARGA DE TODAS LAS TAREAS --------------------
if "df" not in st.session_state:
    tasks = [
        # 1. INSTALACIÓN ELÉCTRICA
        {"Task": "1: Instalación eléctrica", "Level": 0, "Start": base_date, "Finish": base_date + timedelta(days=30), "Status": "En curso"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base_date, "Finish": base_date + timedelta(days=15), "Status": "En curso"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base_date, "Finish": base_date + timedelta(days=3), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base_date + timedelta(days=2), "Finish": base_date + timedelta(days=5), "Status": "En curso"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Start": base_date + timedelta(days=3), "Finish": base_date + timedelta(days=6), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones CT2", "Level": 2, "Start": base_date + timedelta(days=4), "Finish": base_date + timedelta(days=7), "Status": "Sin iniciar"},
        {"Task": "Cuadro Sensores CT2", "Level": 2, "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=8), "Status": "Sin iniciar"},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Start": base_date + timedelta(days=6), "Finish": base_date + timedelta(days=9), "Status": "Sin iniciar"},
        {"Task": "Alimentaciones TSM", "Level": 2, "Start": base_date + timedelta(days=7), "Finish": base_date + timedelta(days=10), "Status": "Sin iniciar"},
        {"Task": "Alimentaciones Cuadros Monitorización", "Level": 2, "Start": base_date + timedelta(days=8), "Finish": base_date + timedelta(days=11), "Status": "Sin iniciar"},
        {"Task": "Alimentaciones Cuadros Seguridad", "Level": 2, "Start": base_date + timedelta(days=9), "Finish": base_date + timedelta(days=12), "Status": "Sin iniciar"},
        {"Task": "Alimentación Rack", "Level": 2, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=13), "Status": "Sin iniciar"},
        {"Task": "Alimentación Alumbrado y Secundarios", "Level": 2, "Start": base_date + timedelta(days=11), "Finish": base_date + timedelta(days=14), "Status": "Sin iniciar"},
        
        {"Task": "Puestas a Tierra", "Level": 1, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=20), "Status": "Sin iniciar"},
        {"Task": "Vallado", "Level": 2, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=15), "Status": "Sin iniciar"},
        {"Task": "TSMs", "Level": 2, "Start": base_date + timedelta(days=11), "Finish": base_date + timedelta(days=16), "Status": "Sin iniciar"},
        {"Task": "Box TSM", "Level": 2, "Start": base_date + timedelta(days=12), "Finish": base_date + timedelta(days=17), "Status": "Sin iniciar"},
        {"Task": "CCTV", "Level": 2, "Start": base_date + timedelta(days=13), "Finish": base_date + timedelta(days=18), "Status": "Sin iniciar"},
        {"Task": "Trackers", "Level": 2, "Start": base_date + timedelta(days=14), "Finish": base_date + timedelta(days=19), "Status": "Sin iniciar"},
        
        {"Task": "Pruebas", "Level": 1, "Start": base_date + timedelta(days=20), "Finish": base_date + timedelta(days=30), "Status": "Sin iniciar"},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Start": base_date + timedelta(days=20), "Finish": base_date + timedelta(days=22), "Status": "Sin iniciar"},
        {"Task": "Polaridades CT", "Level": 2, "Start": base_date + timedelta(days=22), "Finish": base_date + timedelta(days=24), "Status": "Sin iniciar"},
        {"Task": "Curvas IV", "Level": 2, "Start": base_date + timedelta(days=24), "Finish": base_date + timedelta(days=28), "Status": "Sin iniciar"},

        # 2. COMUNICACIONES
        {"Task": "2: Comunicaciones", "Level": 0, "Start": base_date + timedelta(days=15), "Finish": base_date + timedelta(days=45), "Status": "Sin iniciar"},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base_date + timedelta(days=15), "Finish": base_date + timedelta(days=30), "Status": "Sin iniciar"},
        {"Task": "CT1 / CT2", "Level": 2, "Start": base_date + timedelta(days=15), "Finish": base_date + timedelta(days=20), "Status": "Sin iniciar"},
        {"Task": "Sensores Temperatura", "Level": 2, "Start": base_date + timedelta(days=20), "Finish": base_date + timedelta(days=22), "Status": "Sin iniciar"},
        {"Task": "Rack / Cuadro Monit SC", "Level": 2, "Start": base_date + timedelta(days=22), "Finish": base_date + timedelta(days=25), "Status": "Sin iniciar"},
        
        {"Task": "Fusionado Fibras", "Level": 1, "Start": base_date + timedelta(days=30), "Finish": base_date + timedelta(days=40), "Status": "Sin iniciar"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base_date + timedelta(days=30), "Finish": base_date + timedelta(days=33), "Status": "Sin iniciar"},
        
        # 3. SENSORES
        {"Task": "3: Sensores", "Level": 0, "Start": base_date + timedelta(days=35), "Finish": base_date + timedelta(days=50), "Status": "Sin iniciar"},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base_date + timedelta(days=35), "Finish": base_date + timedelta(days=45), "Status": "Sin iniciar"},
        {"Task": "Piranómetros / Estación Met.", "Level": 2, "Start": base_date + timedelta(days=35), "Finish": base_date + timedelta(days=40), "Status": "Sin iniciar"},

        # 5. CTs
        {"Task": "5: CTs", "Level": 0, "Start": base_date + timedelta(days=40), "Finish": base_date + timedelta(days=55), "Status": "Sin iniciar"},
        {"Task": "Equipamiento CT2", "Level": 1, "Start": base_date + timedelta(days=40), "Finish": base_date + timedelta(days=50), "Status": "Sin iniciar"},
        
        # 7. CCTV
        {"Task": "7: CCTV", "Level": 0, "Start": base_date + timedelta(days=45), "Finish": base_date + timedelta(days=60), "Status": "Sin iniciar"},
        
        # 9. TRACKERS
        {"Task": "9: Trackers", "Level": 0, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=40), "Status": "Sin iniciar"},
    ]
    st.session_state.df = pd.DataFrame(tasks)

# -------------------- PROCESAMIENTO VISUAL (ESCALONADO) --------------------
df_plot = st.session_state.df.copy()

def format_task_name(row):
    name = str(row["Task"])
    level = int(row["Level"])
    # Indentación agresiva para
