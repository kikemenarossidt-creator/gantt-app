import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================
st.set_page_config(layout="wide", page_title="Control Integral de Proyecto")
st.title("☀️ Control Integral de Proyecto")

SHEET_ID = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
HOY = pd.Timestamp.today().normalize()

TASK_COLUMNS = [
    "id",
    "Task",
    "Level",
    "DependsOn",
    "DurationDays",
    "Start",
    "End",
    "Empresa a Cargo",
]
RED_COLUMNS = ["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"]
CREDS_COLUMNS = ["EMPRESA", "PLATAFORMA", "USUARIO", "CONTRASEÑA"]
HITOS_COLUMNS = ["TIPO", "HITO", "PORCENTAJE", "PAGADO"]
SPARE_COLUMNS = ["CATEGORIA", "DESCRIPCION", "UNIDADES", "EN_STOCK"]


# ==========================================================
# GOOGLE SHEETS
# ==========================================================
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    client = get_gspread_client()
    return client.open_by_key(SHEET_ID)


@st.cache_data(ttl=30, show_spinner=False)
def read_sheet(sheet_name: str) -> pd.DataFrame:
    ws = get_spreadsheet().worksheet(sheet_name)
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    if len(values) == 1:
        return pd.DataFrame(columns=values[0])
    return pd.DataFrame(values[1:], columns=values[0])


def write_sheet(sheet_name: str, df: pd.DataFrame):
    ws = get_spreadsheet().worksheet(sheet_name)
    clean_df = df.copy().fillna("")
    ws.clear()
    ws.update([clean_df.columns.tolist()] + clean_df.astype(str).values.tolist())
    read_sheet.clear()


# ==========================================================
# UTILIDADES
# ==========================================================
def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns + [c for c in df.columns if c not in columns]]


def to_bool(value) -> bool:
    return str(value).strip().upper() == "TRUE"


def pct_to_float(value) -> float:
    text = str(value).strip().replace("%", "").replace(",", ".")
    if text == "":
        return 0.0
    try:
    tareas_df = load_tasks()
    hitos_df = ensure_columns(read_sheet("Hitos"), HITOS_COLUMNS)
    red_df = ensure_columns(read_sheet("Red"), RED_COLUMNS)
    spares_df = ensure_columns(read_sheet("Repuestos"), SPARE_COLUMNS)

    hitos_progress = calculate_hitos_progress(hitos_df)
    tareas_progress = calculate_project_progress(tareas_df)
    red_progress = calculate_red_progress(red_df)
    spares_progress = calculate_spares_progress(spares_df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write(f"**Avance Obra: {tareas_progress * 100:.1f}%**")
        st.progress(min(tareas_progress, 1.0))
    with col2:
        st.write(f"**Configuración de Red: {red_progress * 100:.1f}%**")
        st.progress(min(red_progress, 1.0))
    with col3:
        st.write(f"**Hitos de Pago: {hitos_progress * 100:.1f}%**")
        st.progress(min(hitos_progress, 1.0))
    with col4:
        st.write(f"**Repuestos en Stock: {spares_progress * 100:.1f}%**")
        st.progress(min(spares_progress, 1.0))

    st.divider()
    render_ficha_tecnica()
    st.divider()

    st.header("📅 Cronograma de Obra")
    detail = st.radio(
        "🔍 Nivel de detalle del cronograma",
        options=[0, 1, 2],
        format_func=lambda x: ["Básico", "Intermedio", "Detallado"][x],
        horizontal=True,
    )

    render_gantt(tareas_df, detail)

    st.subheader("📝 Gestión de Tareas")
    tasks_editor_df = tareas_df.copy()
    tasks_editor_df["Start"] = tasks_editor_df["Start"].apply(fmt_date)
    tasks_editor_df["End"] = tasks_editor_df["End"].apply(fmt_date)

    edited_tasks = st.data_editor(
        tasks_editor_df,
        hide_index=True,
        use_container_width=True,
        key="tasks_editor",
        column_config={
            "id": st.column_config.NumberColumn("ID", step=1, min_value=0),
            "Level": st.column_config.SelectboxColumn("Nivel", options=[0, 1, 2]),
            "DependsOn": st.column_config.TextColumn("Depende de (IDs)"),
            "DurationDays": st.column_config.NumberColumn("Duración (días)", step=1, min_value=0),
        },
        column_order=TASK_COLUMNS,
    )

    a, b, c = st.columns(3)
    with a:
        if st.button("💾 Sincronizar Tareas"):
            save_tasks_editor(edited_tasks)
            st.success("Tareas sincronizadas con Google Sheets.")
            st.rerun()

    with b:
        with st.expander("➕ Añadir Tarea"):
            st.caption("Opción 1: poner Inicio y Fin manualmente. Opción 2: poner Depende de + Duración.")
            with st.form("add_task_form"):
                t1, t2, t3 = st.columns(3)
                new_id = t1.number_input("ID", min_value=0, value=(int(tareas_df["id"].max()) + 1) if not tareas_df.empty else 1, step=1)
                new_task = t2.text_input("Tarea")
                new_level = t3.selectbox("Nivel", [0, 1, 2])

                t4, t5, t6 = st.columns(3)
                new_depends = t4.text_input("Depende de (IDs)")
                new_duration = t5.number_input("Duración (días)", min_value=0, value=0, step=1)
                new_empresa = t6.text_input("Empresa a cargo")

                t7, t8 = st.columns(2)
                new_start = t7.text_input("Inicio manual (dd/mm/yyyy)")
                new_end = t8.text_input("Fin manual (dd/mm/yyyy)")

                submitted = st.form_submit_button("Añadir")
                if submitted:
                    new_row = pd.DataFrame([{
                        "id": int(new_id),
                        "Task": new_task,
                        "Level": int(new_level),
                        "DependsOn": str(new_depends).strip(),
                        "DurationDays": int(new_duration),
                        "Start": new_start,
                        "End": new_end,
                        "Empresa a Cargo": new_empresa,
                    }])
                    to_save = pd.concat([tasks_editor_df, new_row], ignore_index=True)
                    save_tasks_editor(to_save)
                    st.success("Tarea añadida.")
                    st.rerun()

    with c:
        with st.expander("🗑️ Eliminar Tarea"):
            delete_options = [""] + [f"{row['id']} - {row['Task']}" for _, row in tareas_df.iterrows()]
            selected = st.selectbox("Selecciona tarea", delete_options)
            if st.button("Confirmar borrado") and selected:
                delete_id = int(selected.split(" - ")[0])
                filtered = tareas_df[tareas_df["id"] != delete_id].copy()
                filtered["Start"] = filtered["Start"].apply(fmt_date)
                filtered["End"] = filtered["End"].apply(fmt_date)
                save_tasks_editor(filtered)
                st.success("Tarea eliminada.")
                st.rerun()

    st.divider()
    render_red()
    st.divider()
    render_creds()
    st.divider()
    render_hitos(hitos_df)
    st.divider()
    render_spares()

except Exception as e:
    st.error("No se pudo cargar la aplicación.")
    st.exception(e)
