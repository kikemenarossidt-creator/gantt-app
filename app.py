import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from collections import defaultdict

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================
st.set_page_config(layout="wide", page_title="Control Integral de Proyecto")
st.title("☀️ Control Integral de Proyecto")

SHEET_ID = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
TASK_COLUMNS = [
    "id",
    "Task",
    "Level",
    "Parent",
    "DependsOn",
    "Start",
    "End",
    "DurationDays",
    "Progress",
    "Empresa a Cargo",
]
RED_COLUMNS = ["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"]
CREDS_COLUMNS = ["EMPRESA", "PLATAFORMA", "USUARIO", "CONTRASEÑA"]
HITOS_COLUMNS = ["TIPO", "HITO", "PORCENTAJE", "PAGADO"]
SPARE_COLUMNS = ["CATEGORIA", "DESCRIPCION", "UNIDADES"]


# ==========================================================
# UTILIDADES DE GOOGLE SHEETS
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
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    if len(values) == 1:
        return pd.DataFrame(columns=values[0])
    return pd.DataFrame(values[1:], columns=values[0])


def write_sheet(sheet_name: str, df: pd.DataFrame):
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    clean_df = df.copy().fillna("")
    ws.clear()
    ws.update([clean_df.columns.tolist()] + clean_df.astype(str).values.tolist())
    read_sheet.clear()


# ==========================================================
# UTILIDADES GENERALES
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


def to_int(value, default=0):
    try:
        if value == "" or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def to_float(value, default=0.0):
    try:
        if value == "" or pd.isna(value):
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def parse_date(value):
    if value is None or value == "" or pd.isna(value):
        return pd.NaT
    return pd.to_datetime(value, dayfirst=True, errors="coerce")


def fmt_date(value):
    if pd.isna(value):
        return ""
    return pd.to_datetime(value).strftime("%d/%m/%Y")


def normalize_text_id(value: str) -> str:
    return str(value).strip()


# ==========================================================
# TAREAS / GANTT
# ==========================================================
def load_tasks() -> pd.DataFrame:
    df = read_sheet("Tareas")
    df = ensure_columns(df, TASK_COLUMNS)

    for col in ["id", "Level", "DurationDays", "Progress"]:
        df[col] = df[col].apply(lambda x: to_float(x, 0))

    df["id"] = df["id"].astype(int)
    df["Level"] = df["Level"].astype(int)
    df["DurationDays"] = df["DurationDays"].astype(int)
    df["Progress"] = df["Progress"].astype(float)
    df["Task"] = df["Task"].fillna("").astype(str)
    df["Parent"] = df["Parent"].fillna("").astype(str)
    df["DependsOn"] = df["DependsOn"].fillna("").astype(str)
    df["Empresa a Cargo"] = df["Empresa a Cargo"].fillna("").astype(str)
    df["Start"] = df["Start"].apply(parse_date)
    df["End"] = df["End"].apply(parse_date)

    df = df.sort_values(by=["id", "Level", "Task"], kind="stable").reset_index(drop=True)
    return df


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


def build_children_map(df: pd.DataFrame) -> dict[str, list[int]]:
    children = defaultdict(list)
    for idx, row in df.iterrows():
        parent = normalize_text_id(row["Parent"])
        if parent:
            children[parent].append(idx)
    return children


def build_id_index(df: pd.DataFrame) -> dict[int, int]:
    return {int(row["id"]): idx for idx, row in df.iterrows()}


def calculate_task_dates(df: pd.DataFrame) -> pd.DataFrame:
    calc = df.copy()
    children_map = build_children_map(calc)
    id_map = build_id_index(calc)

    resolved = {}
    visiting = set()

    def resolve_row(idx: int):
        if idx in resolved:
            return resolved[idx]
        if idx in visiting:
            return pd.NaT, pd.NaT

        visiting.add(idx)
        row = calc.loc[idx]
        task_id = str(row["id"])
        child_indices = children_map.get(task_id, [])

        # CASO 1: resumen/parent -> toma min/max de hijos
        if child_indices:
            child_dates = [resolve_row(c) for c in child_indices]
            starts = [s for s, e in child_dates if pd.notna(s)]
            ends = [e for s, e in child_dates if pd.notna(e)]
            start = min(starts) if starts else pd.NaT
            end = max(ends) if ends else pd.NaT
            calc.at[idx, "Start"] = start
            calc.at[idx, "End"] = end
            if pd.notna(start) and pd.notna(end):
                calc.at[idx, "DurationDays"] = max((end - start).days + 1, 1)
            visiting.remove(idx)
            resolved[idx] = (start, end)
            return start, end

        # CASO 2: tarea hoja -> calcula desde fechas manuales + dependencias
        manual_start = row["Start"]
        manual_end = row["End"]
        duration = int(row["DurationDays"]) if int(row["DurationDays"]) > 0 else None

        dep_ids = split_dependencies(row["DependsOn"])
        dep_ends = []
        for dep_id in dep_ids:
            if dep_id in id_map:
                _, dep_end = resolve_row(id_map[dep_id])
                if pd.notna(dep_end):
                    dep_ends.append(dep_end)

        dependency_start = max(dep_ends) + timedelta(days=1) if dep_ends else pd.NaT

        # Reglas:
        # - Si hay dependencia, la tarea no puede empezar antes del fin de su precedente + 1 día.
        # - Si hay Start manual posterior, se respeta la mayor.
        # - Si sólo hay End manual y duración, se deduce Start.
        # - Si sólo hay Start manual y duración, se deduce End.
        if pd.notna(dependency_start) and pd.notna(manual_start):
            start = max(dependency_start, manual_start)
        elif pd.notna(dependency_start):
            start = dependency_start
        else:
            start = manual_start

        if pd.notna(start) and duration:
            end = start + timedelta(days=duration - 1)
        elif pd.notna(manual_end) and duration and pd.isna(start):
            start = manual_end - timedelta(days=duration - 1)
            end = manual_end
        else:
            end = manual_end

        if pd.notna(start) and pd.notna(end) and end < start:
            end = start

        if pd.notna(start) and pd.notna(end):
            calc.at[idx, "DurationDays"] = max((end - start).days + 1, 1)

        calc.at[idx, "Start"] = start
        calc.at[idx, "End"] = end
        visiting.remove(idx)
        resolved[idx] = (start, end)
        return start, end

    for idx in calc.index:
        resolve_row(idx)

    return calc


def prepare_gantt_dataframe(df: pd.DataFrame, max_level: int) -> pd.DataFrame:
    plot_df = calculate_task_dates(df)
    plot_df = plot_df[(plot_df["Level"] <= max_level)].copy()
    plot_df = plot_df.dropna(subset=["Start", "End"])
    plot_df = plot_df.sort_values(by="id", kind="stable").reset_index(drop=True)

    if plot_df.empty:
        return plot_df

    plot_df["row_order"] = list(range(len(plot_df)))
    plot_df["row_key"] = plot_df["row_order"].astype(str)
    plot_df["DisplayTask"] = plot_df.apply(
        lambda r: ("    " * int(r["Level"])) + str(r["Task"]), axis=1
    )
    plot_df["ProgressText"] = plot_df["Progress"].apply(lambda x: f"{x:.0f}%")
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

    labels = base.mark_text(align="left", dx=-6).encode(
        text="DisplayTask:N"
    ).properties(width=380, height=height)

    bars = base.mark_bar(cornerRadius=4).encode(
        x=alt.X("Start:T", title="Cronograma", axis=alt.Axis(format="%d/%m/%Y")),
        x2="End:T",
        color=alt.Color(
            "Level:N",
            scale=alt.Scale(range=["#184e77", "#1f78b4", "#76c7ff"]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("id:Q", title="ID"),
            alt.Tooltip("Task:N", title="Tarea"),
            alt.Tooltip("Start:T", title="Inicio", format="%d/%m/%Y"),
            alt.Tooltip("End:T", title="Fin", format="%d/%m/%Y"),
            alt.Tooltip("DurationDays:Q", title="Duración (días)"),
            alt.Tooltip("DependsOn:N", title="Depende de"),
            alt.Tooltip("Empresa a Cargo:N", title="Responsable"),
            alt.Tooltip("ProgressText:N", title="Avance"),
        ],
    ).properties(width=900, height=height)

    percent = base.mark_text(baseline="middle", align="center").encode(
        x=alt.X("Start:T"),
        text="ProgressText:N"
    ).properties(width=900, height=height)

    chart = alt.hconcat(labels, alt.layer(bars, percent)).resolve_scale(y="shared")
    st.altair_chart(chart, use_container_width=False)


# ==========================================================
# MÉTRICAS
# ==========================================================
def calculate_hitos_progress(df_hitos: pd.DataFrame) -> float:
    if df_hitos.empty:
        return 0.0
    tmp = df_hitos.copy()
    tmp = ensure_columns(tmp, HITOS_COLUMNS)
    tmp["pct"] = tmp["PORCENTAJE"].apply(pct_to_float)
    tmp["paid"] = tmp["PAGADO"].apply(to_bool)
    total = tmp["pct"].sum()
    paid = tmp.loc[tmp["paid"], "pct"].sum()
    return (paid / total) if total > 0 else 0.0


def calculate_task_progress(tasks_df: pd.DataFrame) -> float:
    if tasks_df.empty:
        return 0.0
    leafs = tasks_df.copy()
    child_parents = set(leafs["Parent"].fillna("").astype(str).tolist())
    leafs = leafs[~leafs["id"].astype(str).isin(child_parents)].copy()
    if leafs.empty:
        leafs = tasks_df.copy()
    leafs["Progress"] = leafs["Progress"].apply(lambda x: max(0.0, min(100.0, to_float(x, 0.0))))
    return leafs["Progress"].mean() / 100.0


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
# SECCIÓN TAREAS
# ==========================================================
def save_tasks_editor(edited_df: pd.DataFrame):
    df = edited_df.copy()
    df = ensure_columns(df, TASK_COLUMNS)

    df["id"] = df["id"].apply(lambda x: to_int(x, 0))
    df["Level"] = df["Level"].apply(lambda x: to_int(x, 0))
    df["DurationDays"] = df["DurationDays"].apply(lambda x: to_int(x, 0))
    df["Progress"] = df["Progress"].apply(lambda x: to_float(x, 0.0))
    df["Start"] = df["Start"].apply(parse_date).apply(fmt_date)
    df["End"] = df["End"].apply(parse_date).apply(fmt_date)
    df = df.sort_values(by="id", kind="stable").reset_index(drop=True)
    write_sheet("Tareas", df[TASK_COLUMNS])


# ==========================================================
# TABLAS EDITABLES GENÉRICAS
# ==========================================================
def render_red():
    st.header("🌐 Configuración de Red e IPs")
    df = read_sheet("Red")
    df = ensure_columns(df, RED_COLUMNS)
    if not df.empty:
        df["ESTADO"] = df["ESTADO"].apply(to_bool)

    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        key="red_editor",
        column_config={
            "ESTADO": st.column_config.CheckboxColumn("Comunicando"),
        },
    )

    c1, c2 = st.columns([1, 1])
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
                    new_row = pd.DataFrame([
                        {
                            "PROVEEDOR": proveedor,
                            "REFERENCIA": referencia,
                            "MARCA": marca,
                            "USO": uso,
                            "DIRECCION IP": ip,
                            "ESTADO": "FALSE",
                        }
                    ])
                    write_sheet("Red", pd.concat([ensure_columns(df, RED_COLUMNS), new_row], ignore_index=True)[RED_COLUMNS])
                    st.success("IP añadida.")
                    st.rerun()


def render_creds():
    st.header("🔑 Credenciales")
    df = ensure_columns(read_sheet("Credenciales"), CREDS_COLUMNS)
    edited = st.data_editor(df, hide_index=True, use_container_width=True, key="creds_editor")

    c1, c2 = st.columns([1, 1])
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
                    new_row = pd.DataFrame([
                        {
                            "EMPRESA": empresa,
                            "PLATAFORMA": plataforma,
                            "USUARIO": usuario,
                            "CONTRASEÑA": password,
                        }
                    ])
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
        ed_off = st.data_editor(
            df_off,
            hide_index=True,
            use_container_width=True,
            key="off_editor",
            column_config=config,
            column_order=["HITO", "PORCENTAJE", "PAGADO"],
        )
    with on:
        df_on = df_hitos[df_hitos["TIPO"] == "Onshore"].copy()
        ed_on = st.data_editor(
            df_on,
            hide_index=True,
            use_container_width=True,
            key="on_editor",
            column_config=config,
            column_order=["HITO", "PORCENTAJE", "PAGADO"],
        )

    c1, c2 = st.columns([1, 1])
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
                    new_row = pd.DataFrame([
                        {
                            "TIPO": tipo,
                            "HITO": hito,
                            "PORCENTAJE": porcentaje,
                            "PAGADO": "FALSE",
                        }
                    ])
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

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("💾 Guardar Inventario"):
            if search.strip():
                updated = df.copy().reset_index(drop=True)
                edited = edited.reset_index(drop=True)
                match_idx = updated[updated["DESCRIPCION"].fillna("").str.contains(search, case=False, na=False)].index.tolist()
                for local_i, global_i in enumerate(match_idx[: len(edited)]):
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
                categoria = a.selectbox(
                    "Categoría",
                    ["PANELS", "LV/MV COMPONENTS", "INVERTERS", "STRUCTURE", "SECURITY", "MONITORING", "OTROS"],
                )
                descripcion = b.text_input("Descripción")
                unidades = c.number_input("Unidades", min_value=1, value=1)
                submitted = st.form_submit_button("Añadir")
                if submitted:
                    new_row = pd.DataFrame([
                        {
                            "CATEGORIA": categoria,
                            "DESCRIPCION": descripcion,
                            "UNIDADES": int(unidades),
                        }
                    ])
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
    tareas_progress = calculate_task_progress(tareas_df)

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

    # ------------------ GANTT ------------------
    st.header("📅 Cronograma de Obra")
    detail = st.radio(
        "🔍 Nivel de detalle del cronograma",
        options=[0, 1, 2],
        format_func=lambda x: ["Básico", "Intermedio", "Detallado"][x],
        horizontal=True,
    )

    gantt_calc = calculate_task_dates(tareas_df)
    render_gantt(gantt_calc, detail)

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
            "Parent": st.column_config.TextColumn("Parent ID"),
            "DependsOn": st.column_config.TextColumn("DependsOn IDs"),
            "DurationDays": st.column_config.NumberColumn("Duración", step=1, min_value=0),
            "Progress": st.column_config.NumberColumn("Avance %", step=1, min_value=0, max_value=100),
        },
        column_order=TASK_COLUMNS,
    )

    a, b, c = st.columns([1, 1, 1])
    with a:
        if st.button("💾 Sincronizar Tareas"):
            save_tasks_editor(edited_tasks)
            st.success("Tareas sincronizadas con Google Sheets.")
            st.rerun()

    with b:
        with st.expander("➕ Añadir Tarea"):
            with st.form("add_task_form"):
                t1, t2, t3 = st.columns(3)
                new_id = t1.number_input(
                    "ID",
                    min_value=0,
                    value=(int(tareas_df["id"].max()) + 1) if not tareas_df.empty else 1,
                    step=1,
                )
                new_task = t2.text_input("Tarea")
                new_level = t3.selectbox("Nivel", [0, 1, 2])

                t4, t5, t6 = st.columns(3)
                new_parent = t4.text_input("Parent ID")
                new_depends = t5.text_input("DependsOn IDs")
                new_empresa = t6.text_input("Empresa a cargo")

                t7, t8, t9, t10 = st.columns(4)
                new_start = t7.text_input("Inicio (dd/mm/yyyy)")
                new_end = t8.text_input("Fin (dd/mm/yyyy)")
                new_duration = t9.number_input("Duración (días)", min_value=0, value=0, step=1)
                new_progress = t10.number_input("Avance %", min_value=0, max_value=100, value=0, step=1)

                submitted = st.form_submit_button("Añadir")
                if submitted:
                    new_row = pd.DataFrame([
                        {
                            "id": int(new_id),
                            "Task": new_task,
                            "Level": int(new_level),
                            "Parent": str(new_parent).strip(),
                            "DependsOn": str(new_depends).strip(),
                            "Start": new_start,
                            "End": new_end,
                            "DurationDays": int(new_duration),
                            "Progress": float(new_progress),
                            "Empresa a Cargo": new_empresa,
                        }
                    ])
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
