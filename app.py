import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# -------------------- FECHA BASE --------------------
base_date = datetime(2026, 4, 1)

st.set_page_config(layout="wide")
st.title("📊 Gantt jerárquico PV - Plantilla completa")

# -------------------- DATOS INICIALES --------------------
if "df" not in st.session_state:
    tasks = [
        # 1: Instalación eléctrica
        {"Task": "1: Instalación eléctrica", "Level": 0, "Parent": None, "Start": None, "Finish": None, "Status": None},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: Instalación eléctrica", "Start": None, "Finish": None, "Status": None},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date, "Finish": base_date + timedelta(days=5), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=1), "Finish": base_date + timedelta(days=6), "Status": "Completado"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=2), "Finish": base_date + timedelta(days=7), "Status": "Completado"},
        {"Task": "Cuadro Comunicaciones CT2", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=3), "Finish": base_date + timedelta(days=8), "Status": "Completado"},
        {"Task": "Cuadro Sensores CT2", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=4), "Finish": base_date + timedelta(days=9), "Status": "En curso"},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=10), "Status": "En curso"},
        {"Task": "Alimentaciones TSM", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": base_date + timedelta(days=6), "Finish": base_date + timedelta(days=11), "Status": "En curso"},
        {"Task": "Alimentaciones Cuadros Monitorización", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Alimentaciones Cuadros Seguridad", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Alimentación Rack", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Alimentación Alumbrado y Secundarios", "Level": 2, "Parent": "Tendido Eléctrico BT", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: Instalación eléctrica", "Start": None, "Finish": None, "Status": None},
        {"Task": "Vallado", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "TSMs", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Box TSM", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "CCTV", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Vallado CT", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Bodega", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Trackers", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "String Box", "Level": 2, "Parent": "Puestas a Tierra", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Pruebas", "Level": 1, "Parent": "1: Instalación eléctrica", "Start": None, "Finish": None, "Status": None},
        {"Task": "Pruebas de aislamiento CT - Entronque", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Pruebas de aislamiento BT", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Polaridades CT", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Termografías", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Curvas IV", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Continuidad de Tierras", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Arc Flash", "Level": 2, "Parent": "Pruebas", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        # 2: Comunicaciones
        {"Task": "2: Comunicaciones", "Level": 0, "Parent": None, "Start": None, "Finish": None, "Status": None},
        {"Task": "Tendido Cableado", "Level": 1, "Parent": "2: Comunicaciones", "Start": None, "Finish": None, "Status": None},
        {"Task": "CT1", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "CT2", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Piranómetros", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Sensores Temperatura", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Estación Meteorológica", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "TSMs", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Cuadro Monit CT2", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Cuadro Seguridad CT2", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Rack", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Cuadro Monit SC", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Cuadro Seguridad SC", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Cableado", "Start": None, "Finish": None, "Status": "Sin iniciar"},
        # ... Puedes seguir agregando 3: Sensores, 5: Trackers y TSM, 6: CTs, 7: CCTV siguiendo la misma lógica
    ]
    st.session_state.df = pd.DataFrame(tasks)

# -------------------- GRAFICO GANTT --------------------
st.subheader("📈 Gantt")

df_plot = st.session_state.df.copy()
df_plot["Task_display"] = df_plot.apply(lambda row: "   " * int(row["Level"]) + row["Task"], axis=1)

fig = px.timeline(df_plot, x_start="Start", x_end="Finish", y="Task_display", color="Status")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, use_container_width=True)

# -------------------- EDITAR DATOS --------------------
st.subheader("📝 Editar tareas")
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
st.session_state.df = edited_df
