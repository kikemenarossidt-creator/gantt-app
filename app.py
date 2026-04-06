import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import timedelta

# ==========================================================
# CONFIG
# ==========================================================
st.set_page_config(layout="wide", page_title="Control Proyecto")

SHEET_ID = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
HOY = pd.Timestamp.today().normalize()

TASK_COLUMNS = ["id", "Task", "Level", "DependsOn", "DurationDays", "Start", "End", "Empresa a Cargo"]
RED_COLUMNS = ["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"]
HITOS_COLUMNS = ["TIPO", "HITO", "PORCENTAJE", "PAGADO"]
SPARE_COLUMNS = ["CATEGORIA", "DESCRIPCION", "UNIDADES", "EN_STOCK"]

# ==========================================================
# GOOGLE SHEETS
# ==========================================================
@st.cache_resource
def get_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )
    return gspread.authorize(creds)

def read_sheet(name):
    ws = get_client().open_by_key(SHEET_ID).worksheet(name)
    data = ws.get_all_values()
    if len(data) <= 1:
        return pd.DataFrame(columns=data[0] if data else [])
    return pd.DataFrame(data[1:], columns=data[0])

def write_sheet(name, df):
    ws = get_client().open_by_key(SHEET_ID).worksheet(name)
    ws.clear()
    ws.update([df.columns.tolist()] + df.fillna("").astype(str).values.tolist())

# ==========================================================
# UTILS
# ==========================================================
def parse_date(x):
    return pd.to_datetime(x, dayfirst=True, errors="coerce")

def fmt_date(x):
    return "" if pd.isna(x) else pd.to_datetime(x).strftime("%d/%m/%Y")

def to_bool(x):
    return str(x).strip().upper() == "TRUE"

def to_int(x):
    try:
        return int(float(x))
    except:
        return 0

def ensure_columns(df, columns):
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df

# ==========================================================
# LOAD TASKS
# ==========================================================
def load_tasks():
    df = read_sheet("Tareas")
    if df.empty:
        return pd.DataFrame(columns=TASK_COLUMNS)

    df = ensure_columns(df, TASK_COLUMNS)

    df["id"] = df["id"].apply(to_int)
    df["Level"] = df["Level"].apply(to_int)
    df["DurationDays"] = df["DurationDays"].apply(to_int)
    df["Start"] = df["Start"].apply(parse_date)
    df["End"] = df["End"].apply(parse_date)

    return df.sort_values("id").reset_index(drop=True)

# ==========================================================
# GANTT LOGIC
# ==========================================================
def calc_dependencies(df):
    df = df.copy()
    id_map = {row["id"]: i for i, row in df.iterrows()}

    for i, row in df.iterrows():
        deps = str(row["DependsOn"]).split(",")
        deps = [to_int(d) for d in deps if str(d).strip() != ""]

        if deps:
            max_end = None
            for d in deps:
                if d in id_map:
                    dep_end = df.loc[id_map[d], "End"]
                    if pd.notna(dep_end):
                        max_end = dep_end if max_end is None else max(max_end, dep_end)

            if max_end is not None and row["DurationDays"] > 0:
                start = max_end + timedelta(days=1)
                end = start + timedelta(days=row["DurationDays"] - 1)
                df.at[i, "Start"] = start
                df.at[i, "End"] = end

    return df

def rollup(df):
    df = df.copy()

    # nivel 1 desde nivel 2
    for i, row in df.iterrows():
        if row["Level"] == 1:
            next_l1 = next((j for j in df.index if j > i and df.loc[j, "Level"] == 1), len(df))
            next_l0 = next((j for j in df.index if j > i and df.loc[j, "Level"] == 0), len(df))
            stop = min(next_l1, next_l0)

            children = df.iloc[i + 1:stop]
            children = children[children["Level"] == 2]

            if not children.empty:
                df.at[i, "Start"] = children["Start"].min()
                df.at[i, "End"] = children["End"].max()

    # nivel 0 desde nivel 1
    for i, row in df.iterrows():
        if row["Level"] == 0:
            next_l0 = next((j for j in df.index if j > i and df.loc[j, "Level"] == 0), len(df))

            children = df.iloc[i + 1:next_l0]
            children = children[children["Level"] == 1]

            if not children.empty:
                df.at[i, "Start"] = children["Start"].min()
                df.at[i, "End"] = children["End"].max()

    return df

def compute_gantt(df):
    df = calc_dependencies(df)
    df = rollup(df)
    df["Completed"] = df["End"].apply(lambda x: pd.notna(x) and x < HOY)
    return df

# ==========================================================
# GANTT DRAW
# ==========================================================
def render_gantt(df, level):
    df = compute_gantt(df)
    df = df[df["Level"] <= level]
    df = df.dropna(subset=["Start", "End"])

    if df.empty:
        st.warning("Sin datos")
        return

    df = df.copy().reset_index(drop=True)
    df["row"] = range(len(df))
    df["row_str"] = df["row"].astype(str)
    df["TaskLabel"] = df.apply(lambda r: ("    " * int(r["Level"])) + str(r["Task"]), axis=1)

    base = alt.Chart(df).encode(
        y=alt.Y("row_str:O", axis=None, sort=df["row_str"].tolist())
    )

    labels_l0 = base.transform_filter(alt.datum.Level == 0).mark_text(
        align="left",
        dx=-6,
        fontWeight="bold",
        fontSize=14,
        color="#0d3b66"
    ).encode(text="TaskLabel:N")

    labels_l1 = base.transform_filter(alt.datum.Level == 1).mark_text(
        align="left",
        dx=-6,
        fontWeight="bold",
        fontSize=12,
        color="#1d3557"
    ).encode(text="TaskLabel:N")

    labels_l2 = base.transform_filter(alt.datum.Level == 2).mark_text(
        align="left",
        dx=-6,
        fontStyle="italic",
        fontSize=11,
        color="#457b9d"
    ).encode(text="TaskLabel:N")

    labels = alt.layer(labels_l0, labels_l1, labels_l2).properties(
        width=350,
        height=max(200, len(df) * 32)
    )

    bars = base.mark_bar(cornerRadius=4).encode(
        x=alt.X("Start:T", title="Cronograma", axis=alt.Axis(format="%d/%m/%Y")),
        x2="End:T",
        color=alt.Color(
            "Level:Q",
            scale=alt.Scale(
                domain=[0, 1, 2],
                range=["#1b4332", "#2d6a4f", "#95d5b2"]
            ),
            legend=alt.Legend(title="Nivel")
        ),
        tooltip=[
            alt.Tooltip("id:Q", title="ID"),
            alt.Tooltip("Task:N", title="Tarea"),
            alt.Tooltip("Level:Q", title="Nivel"),
            alt.Tooltip("Start:T", title="Inicio", format="%d/%m/%Y"),
            alt.Tooltip("End:T", title="Fin", format="%d/%m/%Y"),
            alt.Tooltip("DependsOn:N", title="Depende de"),
            alt.Tooltip("DurationDays:Q", title="Duración (días)"),
            alt.Tooltip("Empresa a Cargo:N", title="Responsable"),
        ]
    ).properties(
        width=850,
        height=max(200, len(df) * 32)
    )

    chart = alt.hconcat(labels, bars).resolve_scale(y="shared")
    st.altair_chart(chart, use_container_width=False)

# ==========================================================
# PROGRESS
# ==========================================================
def progress_tasks(df):
    df = compute_gantt(df)
    df = df[df["End"].notna()]
    if len(df) == 0:
        return 0
    return df["Completed"].mean()

def progress_red(df):
    if df.empty or "ESTADO" not in df.columns:
        return 0
    vals = df["ESTADO"].apply(to_bool)
    return vals.mean() if len(vals) > 0 else 0

def progress_hitos(df):
    if df.empty or "PORCENTAJE" not in df.columns or "PAGADO" not in df.columns:
        return 0

    tmp = df.copy()

    tmp["pct"] = (
        tmp["PORCENTAJE"]
        .astype(str)
        .str.strip()
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    tmp["pct"] = pd.to_numeric(tmp["pct"], errors="coerce").fillna(0)

    total = tmp["pct"].sum()
    paid = tmp.loc[tmp["PAGADO"].apply(to_bool), "pct"].sum()

    return paid / total if total > 0 else 0

def progress_spares(df):
    if df.empty or "EN_STOCK" not in df.columns:
        return 0
    vals = df["EN_STOCK"].apply(to_bool)
    return vals.mean() if len(vals) > 0 else 0

# ==========================================================
# APP
# ==========================================================
st.title("☀️ Control Proyecto")

tareas = load_tasks()
red = read_sheet("Red")
hitos = read_sheet("Hitos")
spares = read_sheet("Repuestos")

col1, col2, col3, col4 = st.columns(4)

with col1:
    p = progress_tasks(tareas)
    st.write(f"Avance obra {p * 100:.1f}%")
    st.progress(p)

with col2:
    p = progress_red(red)
    st.write(f"Red {p * 100:.1f}%")
    st.progress(p)

with col3:
    p = progress_hitos(hitos)
    st.write(f"Hitos {p * 100:.1f}%")
    st.progress(p)

with col4:
    p = progress_spares(spares)
    st.write(f"Repuestos {p * 100:.1f}%")
    st.progress(p)

st.divider()

level = st.radio("Nivel", [0, 1, 2], horizontal=True)
render_gantt(tareas, level)

st.divider()

edited = st.data_editor(
    tareas.assign(
        Start=tareas["Start"].apply(fmt_date) if "Start" in tareas.columns else "",
        End=tareas["End"].apply(fmt_date) if "End" in tareas.columns else ""
    ),
    use_container_width=True,
    hide_index=True
)

if st.button("Guardar tareas"):
    write_sheet("Tareas", edited)
    st.rerun()
