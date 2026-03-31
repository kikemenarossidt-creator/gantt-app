import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("📊 Gantt editable")

# ---------- DATOS INICIALES ----------
if "df" not in st.session_state:
    base_date = datetime(2026, 4, 1)

    st.session_state.df = pd.DataFrame([
        {"Task": "Instalación eléctrica", "Start": base_date, "Finish": base_date + timedelta(days=5), "Level": 0},
        {"Task": "Tendido eléctrico", "Start": base_date + timedelta(days=3), "Finish": base_date + timedelta(days=8), "Level": 1},
        {"Task": "Cuadro protecciones SC", "Start": base_date + timedelta(days=6), "Finish": base_date + timedelta(days=11), "Level": 2},
    ])

df = st.session_state.df

# ---------- GANTT ARRIBA ----------
st.subheader("📈 Gantt")

if not df.empty:
    df_plot = df.copy()
    df_plot["Task_display"] = df_plot.apply(
        lambda row: "   " * int(row["Level"]) + row["Task"], axis=1
    )

    fig = px.timeline(
        df_plot,
        x_start="Start",
        x_end="Finish",
        y="Task_display",
        color="Level"
    )

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay tareas aún")

# ---------- CONTROLES ----------
st.subheader("➕ Añadir tarea")

col1, col2, col3, col4 = st.columns(4)

with col1:
    new_task = st.text_input("Nombre tarea")

with col2:
    new_level = st.number_input("Nivel", min_value=0, max_value=5, value=0)

with col3:
    new_start = st.date_input("Inicio", value=datetime(2026, 4, 1))

with col4:
    new_duration = st.number_input("Duración (días)", min_value=1, value=5)

if st.button("Añadir"):
    new_row = {
        "Task": new_task,
        "Start": pd.to_datetime(new_start),
        "Finish": pd.to_datetime(new_start) + timedelta(days=int(new_duration)),
        "Level": new_level
    }

    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
    st.rerun()

# ---------- TABLA EDITABLE ----------
st.subheader("📝 Editar tareas")

edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True
)

# Guardar cambios automáticamente
st.session_state.df = edited_df

# ---------- BORRAR ----------
st.subheader("🗑️ Borrar tarea")

task_to_delete = st.selectbox("Selecciona tarea", st.session_state.df["Task"])

if st.button("Eliminar"):
    st.session_state.df = st.session_state.df[
        st.session_state.df["Task"] != task_to_delete
    ]
    st.rerun()