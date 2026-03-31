import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(layout="wide")

st.title("📊 Gantt editable")

# ---------- GOOGLE SHEETS ----------
def connect_to_gsheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)
    return client.open("gantt_data").sheet1


def load_data():
    sheet = connect_to_gsheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        df["Start"] = pd.to_datetime(df["Start"])
        df["Finish"] = pd.to_datetime(df["Finish"])

    return df


def save_data(df):
    sheet = connect_to_gsheet()
    sheet.clear()

    # encabezados
    sheet.append_row(["Task", "Start", "Finish", "Level"])

    # datos
    for _, row in df.iterrows():
        sheet.append_row([
            row["Task"],
            str(row["Start"]),
            str(row["Finish"]),
            int(row["Level"])
        ])


# ---------- CARGA INICIAL ----------
if "df" not in st.session_state:
    try:
        st.session_state.df = load_data()
    except:
        base_date = datetime(2026, 4, 1)
        st.session_state.df = pd.DataFrame([
            {"Task": "Instalación eléctrica", "Start": base_date, "Finish": base_date + timedelta(days=5), "Level": 0},
            {"Task": "Tendido eléctrico", "Start": base_date + timedelta(days=3), "Finish": base_date + timedelta(days=8), "Level": 1},
        ])
        save_data(st.session_state.df)

df = st.session_state.df

# ---------- GANTT ----------
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

# ---------- AÑADIR ----------
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
    if new_task != "":
        new_row = {
            "Task": new_task,
            "Start": pd.to_datetime(new_start),
            "Finish": pd.to_datetime(new_start) + timedelta(days=int(new_duration)),
            "Level": new_level
        }

        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame([new_row])],
            ignore_index=True
        )

        save_data(st.session_state.df)
        st.rerun()
    else:
        st.warning("Pon un nombre de tarea")

# ---------- EDITAR ----------
st.subheader("📝 Editar tareas")

edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True
)

st.session_state.df = edited_df
save_data(st.session_state.df)

# ---------- BORRAR ----------
st.subheader("🗑️ Borrar tarea")

if not st.session_state.df.empty:
    task_to_delete = st.selectbox("Selecciona tarea", st.session_state.df["Task"])

    if st.button("Eliminar"):
        st.session_state.df = st.session_state.df[
            st.session_state.df["Task"] != task_to_delete
        ]

        save_data(st.session_state.df)
        st.rerun()
