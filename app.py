import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("📊 Gantt editable")

# ---------- INTENTO GOOGLE SHEETS ----------
def load_data_safe():
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )

        client = gspread.authorize(creds)
        sheet = client.open("gantt_data").sheet1

        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty:
            df["Start"] = pd.to_datetime(df["Start"])
            df["Finish"] = pd.to_datetime(df["Finish"])

        return df, sheet

    except Exception as e:
        st.error("⚠️ Error conectando con Google Sheets")
        st.text(str(e))
        return None, None


def save_data_safe(df, sheet):
    try:
        if sheet is None:
            return

        sheet.clear()
        sheet.append_row(["Task", "Start", "Finish", "Level"])

        for _, row in df.iterrows():
            sheet.append_row([
                row["Task"],
                str(row["Start"]),
                str(row["Finish"]),
                int(row["Level"])
            ])
    except:
        st.warning("No se pudo guardar en Google Sheets")


# ---------- CARGA ----------
if "df" not in st.session_state:
    df_loaded, sheet = load_data_safe()

    if df_loaded is not None and not df_loaded.empty:
        st.session_state.df = df_loaded
    else:
        base_date = datetime(2026, 4, 1)
        st.session_state.df = pd.DataFrame([
            {"Task": "Instalación eléctrica", "Start": base_date, "Finish": base_date + timedelta(days=5), "Level": 0},
        ])

    st.session_state.sheet = sheet

df = st.session_state.df
sheet = st.session_state.sheet

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
    st.warning("No hay tareas")

# ---------- AÑADIR ----------
st.subheader("➕ Añadir tarea")

col1, col2, col3, col4 = st.columns(4)

new_task = col1.text_input("Nombre tarea")
new_level = col2.number_input("Nivel", 0, 5, 0)
new_start = col3.date_input("Inicio", datetime(2026, 4, 1))
new_duration = col4.number_input("Duración", 1, 30, 5)

if st.button("Añadir"):
    if new_task:
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

        save_data_safe(st.session_state.df, sheet)
        st.rerun()

# ---------- EDITAR ----------
st.subheader("📝 Editar tareas")

edited_df = st.data_editor(df, num_rows="dynamic")

st.session_state.df = edited_df
save_data_safe(st.session_state.df, sheet)

# ---------- BORRAR ----------
st.subheader("🗑️ Borrar")

if not df.empty:
    task = st.selectbox("Tarea", df["Task"])

    if st.button("Eliminar"):
        st.session_state.df = df[df["Task"] != task]
        save_data_safe(st.session_state.df, sheet)
        st.rerun()
