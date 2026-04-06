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
SPARE_COLUMNS = ["CATEGORIA", "DESCRIPCION", "UNIDADES"]


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
        return float(text)
    except Exception:
        return 0.0


def to_int(value, default=0) -> int:
    try:
        if value == "" or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def parse_date(value):
    if value is None or value == "" or pd.isna(value):
        return pd.NaT
    return pd.to_datetime(value, dayfirst=True, errors="coerce")


def fmt_date(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.to_datetime(value).strftime("%d/%m/%Y")


def split_dependencies(depends_on: str) -> list[int]:
    raw = str(depends_on).strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.replace(";", ",").split(",")]
    out = []
    for p in parts:
        if p:
            try:
                out.append(int(float(p)))
            except Exception:
                pass
    return out


def first_valid(series: pd.Series):
    vals = [v for v in series if pd.notna(v)]
    return vals[0] if vals else pd.NaT


# ==========================================================
# CARGA DE DATOS
# ==========================================================
def load_tasks() -> pd.DataFrame:
    df = ensure_columns(read_sheet("Tareas"), TASK_COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=TASK_COLUMNS)

    df["id"] = df["id"].apply(lambda x: to_int(x, 0)).astype(int)
    df["Task"] = df["Task"].fillna("").astype(str)
    df["Level"] = df["Level"].apply(lambda x: to_int(x, 0)).astype(int)
    df["DependsOn"] = df["DependsOn"].fillna("").astype(str)
    df["DurationDays"] = df["DurationDays"].apply(lambda x: to_int(x, 0)).astype(int)
    df["Start"] = df["Start"].apply(parse_date)
    df["End"] = df["End"].apply(parse_date)
    df["Empresa a Cargo"] = df["Empresa a Cargo"].fillna("").astype(str)

    return df.sort_values("id", kind="stable").reset_index(drop=True)


# ==========================================================
# LÓGICA GANTT
# ==========================================================
def apply_dependency_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Solo para tareas hoja (normalmente nivel 2, o cualquier tarea sin hijos reales en el bloque).
    Reglas:
    - Si una tarea tiene Start y End manuales, se respetan.
    - Si tiene DependsOn + DurationDays, se calcula Start = End(predecesora)+1 y End = Start + duración - 1.
    - Si tiene Start + DurationDays, se calcula End.
    - Si tiene End + DurationDays, se calcula Start.
    """
    calc = df.copy()
    id_to_idx = {int(row["id"]): idx for idx, row in calc.iterrows()}

    resolved = {}
    visiting = set()

    def resolve_leaf(idx: int):
        if idx in resolved:
            return resolved[idx]
        if idx in visiting:
            return pd.NaT, pd.NaT

        visiting.add(idx)
        row = calc.loc[idx]
        start = row["Start"]
        end = row["End"]
        duration = int(row["DurationDays"])
        deps = split_dependencies(row["DependsOn"])

        dep_ends = []
        for dep_id in deps:
            dep_idx = id_to_idx.get(dep_id)
            if dep_idx is not None:
                _, dep_end = resolve_leaf(dep_idx)
                if pd.notna(dep_end):
                    dep_ends.append(dep_end)

        dep_start = max(dep_ends) + timedelta(days=1) if dep_ends else pd.NaT

        if pd.notna(start) and pd.notna(end):
            final_start, final_end = start, end
        elif pd.notna(dep_start) and duration > 0:
            final_start = dep_start
            final_end = dep_start + timedelta(days=duration - 1)
        elif pd.notna(start) and duration > 0:
            final_start = start
            final_end = start + timedelta(days=duration - 1)
        elif pd.notna(end) and duration > 0:
            final_end = end
            final_start = end - timedelta(days=duration - 1)
        else:
            final_start, final_end = start, end

        if pd.notna(final_start) and pd.notna(final_end) and final_end < final_start:
            final_end = final_start

        calc.at[idx, "Start"] = final_start
        calc.at[idx, "End"] = final_end

        visiting.remove(idx)
        resolved[idx] = (final_start, final_end)
        return final_start, final_end

    for idx in calc.index:
        resolve_leaf(idx)

    return calc


def rollup_hierarchy_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reglas pedidas:
    - Las tareas nivel 0 toman las fechas mín/max de las tareas nivel 1 inferiores hasta la siguiente nivel 0.
    - Las tareas nivel 1 toman las fechas mín/max de las tareas nivel 2 inferiores hasta la siguiente nivel 1.
    """
    calc = df.copy().reset_index(drop=True)

    # Primero nivel 1 a partir de nivel 2
    level1_idx = calc.index[calc["Level"] == 1].tolist()
    level0_idx = calc.index[calc["Level"] == 0].tolist()

    for pos, idx in enumerate(level1_idx):
        next_level1 = next((i for i in level1_idx if i > idx), len(calc))
        next_level0 = next((i for i in level0_idx if i > idx), len(calc))
        block_end = min(next_level1, next_level0)

        children = calc.iloc[idx + 1:block_end]
        children = children[children["Level"] == 2]

        if not children.empty:
            start = children["Start"].min()
            end = children["End"].max()
            calc.at[idx, "Start"] = start
            calc.at[idx, "End"] = end

    # Luego nivel 0 a partir de nivel 1
    for pos, idx in enumerate(level0_idx):
        next_level0 = next((i for i in level0_idx if i > idx), len(calc))
        children = calc.iloc[idx + 1:next_level0]
        children = children[children["Level"] == 1]

        if not children.empty:
            start = children["Start"].min()
            end = children["End"].max()
            calc.at[idx, "Start"] = start
            calc.at[idx, "End"] = end

    return calc


def calculate_task_completion(df: pd.DataFrame) -> pd.DataFrame:
    calc = df.copy()
    calc["Completed"] = calc["End"].apply(lambda x: pd.notna(x) and pd.Timestamp(x).normalize() < HOY)
    calc["CompletedText"] = calc["Completed"].apply(lambda x: "Sí" if x else "No")
    return calc


def calculate_full_gantt(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    calc = apply_dependency_dates(df)
    calc = rollup_hierarchy_dates(calc)
    calc = calculate_task_completion(calc)
    return calc


def prepare_gantt_dataframe(df: pd.DataFrame, max_level: int) -> pd.DataFrame:
    plot_df = calculate_full_gantt(df)
    plot_df = plot_df[plot_df["Level"] <= max_level].copy()
    plot_df = plot_df.dropna(subset=["Start", "End"])
    plot_df = plot_df.sort_values("id", kind="stable").reset_index(drop=True)

    if plot_df.empty:
        return plot_df

    plot_df["row_order"] = range(len(plot_df))
    plot_df["row_key"] = plot_df["row_order"].astype(str)
    plot_df["DisplayTask"] = plot_df.apply(lambda r: ("    " * int(r["Level"])) + str(r["Task"]), axis=1)
    return plot_df


def render_gantt(df: pd.DataFrame, max_level: int):
    plot_df = prepare_gantt_dataframe(df, max_level)
    if plot_df.empty:
        st.info("No hay tareas con fechas válidas para mostrar en el Gantt.")
        return

    height = max(240, len(plot_df) * 34)
    order = plot_df["row_key"].tolist()

    base = alt.Chart(plot_df).encode(
        y=alt.Y("row_key:O", axis=None, sort=order)
    )

    # Etiquetas izquierda por nivel
    labels_l0 = base.transform_filter(alt.datum.Level == 0).mark_text(
        align="left", dx=-6, fontWeight="bo


# ==========================================================
# MÉTRICAS
# ==========================================================
def calculate_hitos_progress(df_hitos: pd.DataFrame) -> float:
    if df_hitos.empty:
        return 0.0
    tmp = ensure_columns(df_hitos, HITOS_COLUMNS)
    tmp["pct"] = tmp["PORCENTAJE"].apply(pct_to_float)
    tmp["paid"] = tmp["PAGADO"].apply(to_bool)
    total = tmp["pct"].sum()
    paid = tmp.loc[tmp["paid"], "pct"].sum()
    return (paid / total) if total > 0 else 0.0


def calculate_project_progress(tasks_df: pd.DataFrame) -> float:
    if tasks_df.empty:
        return 0.0
    calc = calculate_full_gantt(tasks_df)
    leafs = calc[calc["Level"] == 2].copy()
    if leafs.empty:
        leafs = calc[calc["Level"] == calc["Level"].max()].copy()
    if leafs.empty:
        return 0.0
    return leafs["Completed"].mean()


# ==========================================================
# FICHA TÉCNICA
# ==========================================================
def render_ficha_tecnica():
    with st.expander("📋 Ficha técnica del proyecto", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("📍 Ubicación y contacto")
            st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
            st.text_input("Dirección", "Km 45, Ruta 5 Norte")
            st.text_area("Teléfonos de despacho", "+56 7 1263 5132\n+56 7 1263 5133", height=80)
        with c2:
            st.subheader("⚡ Datos técnicos")
            st.number_input("Potencia Pico (MWp)", value=10.5)
            st.text_input("Inversores", "SUNGROW SG250HX")
            st.text_input("Paneles", "JINKO Solar 550W")
        with c3:
            st.subheader("🏢 CGE / Seguridad")
            st.text_input("Nombre proyecto para CGE", "Maule X")
            st.text_input("Nombre del alimentador", "DUAO 15 kV")
            st.text_input("Proveedor Seguridad", "Prosegur")


# ==========================================================
# TAREAS
# ==========================================================
def save_tasks_editor(edited_df: pd.DataFrame):
    df = ensure_columns(edited_df.copy(), TASK_COLUMNS)
    df["id"] = df["id"].apply(lambda x: to_int(x, 0))
    df["Level"] = df["Level"].apply(lambda x: to_int(x, 0))
    df["DurationDays"] = df["DurationDays"].apply(lambda x: to_int(x, 0))
    df["Start"] = df["Start"].apply(parse_date).apply(fmt_date)
    df["End"] = df["End"].apply(parse_date).apply(fmt_date)
    df = df.sort_values("id", kind="stable").reset_index(drop=True)
    write_sheet("Tareas", df[TASK_COLUMNS])


# ==========================================================
# TABLAS GENÉRICAS
# ==========================================================
def render_red():
    st.header("🌐 Configuración de Red e IPs")
    df = ensure_columns(read_sheet("Red"), RED_COLUMNS)
    if not df.empty:
        df["ESTADO"] = df["ESTADO"].apply(to_bool)

    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        key="red_editor",
        column_config={"ESTADO": st.column_config.CheckboxColumn("Comunicando")},
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Red"):
            out = edited.copy()
            out["ESTADO"] = out["ESTADO"].apply(lambda x: "TRUE" if bool(x) else "FALSE")
            write_sheet("Red", out[RED_COLUMNS])
            st.success("Red actualizada.")
            st.rerun()
    with c2:
        with st.expander("➕ Añadir IP"):
            with st.form("add_ip_form"):
                a, b, c, d, e = st.columns(5)
                proveedor = a.text_input("Proveedor")
                referencia = b.text_input("Referencia")
                marca = c.text_input("Marca")
                uso = d.text_input("Uso")
                ip = e.text_input("IP")
                submitted = st.form_submit_button("Añadir")
                if submitted:
                    new_row = pd.DataFrame([{
                        "PROVEEDOR": proveedor,
                        "REFERENCIA": referencia,
                        "MARCA": marca,
                        "USO": uso,
                        "DIRECCION IP": ip,
                        "ESTADO": "FALSE",
                    }])
                    write_sheet("Red", pd.concat([df, new_row], ignore_index=True)[RED_COLUMNS])
                    st.success("IP añadida.")
                    st.rerun()


def render_creds():
    st.header("🔑 Credenciales")
    df = ensure_columns(read_sheet("Credenciales"), CREDS_COLUMNS)
    edited = st.data_editor(df, hide_index=True, use_container_width=True, key="creds_editor")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Credenciales"):
            write_sheet("Credenciales", ensure_columns(edited, CREDS_COLUMNS)[CREDS_COLUMNS])
            st.success("Credenciales actualizadas.")
            st.rerun()
    with c2:
        with st.expander("➕ Añadir Credencial"):
            with st.form("add_cred_form"):
                a, b, c, d = st.columns(4)
                empresa = a.text_input("Empresa")
                plataforma = b.text_input("Plataforma")
                usuario = c.text_input("Usuario")
                password = d.text_input("Contraseña")
                submitted = st.form_submit_button("Añadir")
                if submitted:
                    new_row = pd.DataFrame([{
                        "EMPRESA": empresa,
                        "PLATAFORMA": plataforma,
                        "USUARIO": usuario,
                        "CONTRASEÑA": password,
                    }])
                    write_sheet("Credenciales", pd.concat([df, new_row], ignore_index=True)[CREDS_COLUMNS])
                    st.success("Credencial añadida.")
                    st.rerun()


def render_hitos(df_hitos: pd.DataFrame):
    st.header("💰 Hitos de Pago")
    df_hitos = ensure_columns(df_hitos, HITOS_COLUMNS)
    if not df_hitos.empty:
        df_hitos["PAGADO"] = df_hitos["PAGADO"].apply(to_bool)

    off, on = st.tabs(["🚢 Offshore", "🏗️ Onshore"])
    config = {
        "PAGADO": st.column_config.CheckboxColumn("Pagado"),
        "PORCENTAJE": st.column_config.TextColumn("Cuota %"),
    }

    with off:
        df_off = df_hitos[df_hitos["TIPO"] == "Offshore"].copy()
        ed_off = st.data_editor(df_off, hide_index=True, use_container_width=True, key="off_editor", column_config=config, column_order=["HITO", "PORCENTAJE", "PAGADO"])
    with on:
        df_on = df_hitos[df_hitos["TIPO"] == "Onshore"].copy()
        ed_on = st.data_editor(df_on, hide_index=True, use_container_width=True, key="on_editor", column_config=config, column_order=["HITO", "PORCENTAJE", "PAGADO"])

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Hitos"):
            ed_off = ensure_columns(ed_off, HITOS_COLUMNS)
            ed_on = ensure_columns(ed_on, HITOS_COLUMNS)
            ed_off["TIPO"] = "Offshore"
            ed_on["TIPO"] = "Onshore"
            final_df = pd.concat([ed_off, ed_on], ignore_index=True)
            final_df["PAGADO"] = final_df["PAGADO"].apply(lambda x: "TRUE" if bool(x) else "FALSE")
            write_sheet("Hitos", final_df[HITOS_COLUMNS])
            st.success("Hitos actualizados.")
            st.rerun()
    with c2:
        with st.expander("➕ Añadir Hito"):
            with st.form("add_hito_form"):
                a, b, c = st.columns(3)
                tipo = a.selectbox("Tipo", ["Offshore", "Onshore"])
                hito = b.text_input("Hito")
                porcentaje = c.text_input("Porcentaje")
                submitted = st.form_submit_button("Añadir")
                if submitted:
                    new_row = pd.DataFrame([{
                        "TIPO": tipo,
                        "HITO": hito,
                        "PORCENTAJE": porcentaje,
                        "PAGADO": "FALSE",
                    }])
                    write_sheet("Hitos", pd.concat([df_hitos, new_row], ignore_index=True)[HITOS_COLUMNS])
                    st.success("Hito añadido.")
                    st.rerun()


def render_spares():
    st.header("📦 Repuestos")
    df = ensure_columns(read_sheet("Repuestos"), SPARE_COLUMNS)
    search = st.text_input("🔍 Buscar repuesto", "")

    if search.strip():
        view = df[df["DESCRIPCION"].fillna("").str.contains(search, case=False, na=False)].copy()
    else:
        view = df.copy()

    edited = st.data_editor(view, hide_index=True, use_container_width=True, key="spare_editor")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Inventario"):
            if search.strip():
                updated = df.copy().reset_index(drop=True)
                edited = edited.reset_index(drop=True)
                match_idx = updated[updated["DESCRIPCION"].fillna("").str.contains(search, case=False, na=False)].index.tolist()
                for local_i, global_i in enumerate(match_idx[:len(edited)]):
                    updated.loc[global_i, SPARE_COLUMNS] = edited.loc[local_i, SPARE_COLUMNS].values
                write_sheet("Repuestos", updated[SPARE_COLUMNS])
            else:
                write_sheet("Repuestos", ensure_columns(edited, SPARE_COLUMNS)[SPARE_COLUMNS])
            st.success("Inventario actualizado.")
            st.rerun()
    with c2:
        with st.expander("➕ Registrar Nuevo Repuesto"):
            with st.form("add_spare_form"):
                a, b, c = st.columns([2, 3, 1])
                categoria = a.selectbox("Categoría", ["PANELS", "LV/MV COMPONENTS", "INVERTERS", "STRUCTURE", "SECURITY", "MONITORING", "OTROS"])
                descripcion = b.text_input("Descripción")
                unidades = c.number_input("Unidades", min_value=1, value=1)
                submitted = st.form_submit_button("Añadir")
                if submitted:
                    new_row = pd.DataFrame([{
                        "CATEGORIA": categoria,
                        "DESCRIPCION": descripcion,
                        "UNIDADES": int(unidades),
                    }])
                    write_sheet("Repuestos", pd.concat([df, new_row], ignore_index=True)[SPARE_COLUMNS])
                    st.success("Repuesto añadido.")
                    st.rerun()


# ==========================================================
# APP PRINCIPAL
# ==========================================================
try:
    tareas_df = load_tasks()
    hitos_df = ensure_columns(read_sheet("Hitos"), HITOS_COLUMNS)

    hitos_progress = calculate_hitos_progress(hitos_df)
    tareas_progress = calculate_project_progress(tareas_df)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Payment Milestones: {hitos_progress * 100:.1f}%**")
        st.progress(min(hitos_progress, 1.0))
    with col2:
        st.write(f"**Avance Obra: {tareas_progress * 100:.1f}%**")
        st.progress(min(tareas_progress, 1.0))

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
