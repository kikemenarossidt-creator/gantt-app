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

TASK_COLUMNS = ["id","Task","Level","DependsOn","DurationDays","Start","End","Empresa a Cargo"]
RED_COLUMNS = ["PROVEEDOR","REFERENCIA","MARCA","USO","DIRECCION IP","ESTADO"]
HITOS_COLUMNS = ["TIPO","HITO","PORCENTAJE","PAGADO"]
SPARE_COLUMNS = ["CATEGORIA","DESCRIPCION","UNIDADES","EN_STOCK"]

# ==========================================================
# GOOGLE SHEETS
# ==========================================================
@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
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
    return str(x).upper()=="TRUE"

def to_int(x):
    try: return int(float(x))
    except: return 0

# ==========================================================
# LOAD TASKS
# ==========================================================
def load_tasks():
    df = read_sheet("Tareas")
    if df.empty:
        return pd.DataFrame(columns=TASK_COLUMNS)

    for col in TASK_COLUMNS:
        if col not in df.columns:
            df[col] = ""

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
    id_map = {row["id"]:i for i,row in df.iterrows()}

    for i,row in df.iterrows():
        deps = str(row["DependsOn"]).split(",")
        deps = [to_int(d) for d in deps if d]

        if deps:
            max_end = None
            for d in deps:
                if d in id_map:
                    dep_end = df.loc[id_map[d],"End"]
                    if pd.notna(dep_end):
                        max_end = dep_end if max_end is None else max(max_end, dep_end)

            if max_end is not None and row["DurationDays"]>0:
                start = max_end + timedelta(days=1)
                end = start + timedelta(days=row["DurationDays"]-1)
                df.at[i,"Start"] = start
                df.at[i,"End"] = end

    return df

def rollup(df):
    df = df.copy()

    # nivel 1 desde nivel 2
    for i,row in df.iterrows():
        if row["Level"]==1:
            children = df[(df.index>i) & (df["Level"]==2)]
            if not children.empty:
                df.at[i,"Start"] = children["Start"].min()
                df.at[i,"End"] = children["End"].max()

    # nivel 0 desde nivel 1
    for i,row in df.iterrows():
        if row["Level"]==0:
            children = df[(df.index>i) & (df["Level"]==1)]
            if not children.empty:
                df.at[i,"Start"] = children["Start"].min()
                df.at[i,"End"] = children["End"].max()

    return df

def compute_gantt(df):
    df = calc_dependencies(df)
    df = rollup(df)
    df["Completed"] = df["End"].apply(lambda x: pd.notna(x) and x<HOY)
    return df

# ==========================================================
# GANTT DRAW
# ==========================================================
def render_gantt(df, level):
    df = compute_gantt(df)
    df = df[df["Level"]<=level]
    df = df.dropna(subset=["Start","End"])

    if df.empty:
        st.warning("Sin datos")
        return

    df["row"] = range(len(df))

    base = alt.Chart(df).encode(
        y=alt.Y("row:O", axis=None)
    )

    labels = base.mark_text(align="left").encode(
        text="Task"
    ).properties(width=300)

    bars = base.mark_bar().encode(
        x="Start:T",
        x2="End:T",
        color=alt.Color("Level:Q",
            scale=alt.Scale(domain=[0,1,2],
            range=["#1b4332","#2d6a4f","#95d5b2"])
        )
    ).properties(width=800)

    st.altair_chart(alt.hconcat(labels,bars), use_container_width=False)

# ==========================================================
# PROGRESS
# ==========================================================
def progress_tasks(df):
    df = compute_gantt(df)
    df = df[df["End"].notna()]
    if len(df)==0: return 0
    return df["Completed"].mean()

def progress_red(df):
    if df.empty: return 0
    return df["ESTADO"].apply(to_bool).mean()

def progress_hitos(df):
    if df.empty: return 0
    df["pct"]=df["PORCENTAJE"].str.replace("%","").astype(float)
    total=df["pct"].sum()
    paid=df[df["PAGADO"].apply(to_bool)]["pct"].sum()
    return paid/total if total>0 else 0

def progress_spares(df):
    if df.empty: return 0
    return df["EN_STOCK"].apply(to_bool).mean()

# ==========================================================
# APP
# ==========================================================
st.title("☀️ Control Proyecto")

tareas = load_tasks()
red = read_sheet("Red")
hitos = read_sheet("Hitos")
spares = read_sheet("Repuestos")

col1,col2,col3,col4 = st.columns(4)

with col1:
    p=progress_tasks(tareas)
    st.write(f"Avance obra {p*100:.1f}%")
    st.progress(p)

with col2:
    p=progress_red(red)
    st.write(f"Red {p*100:.1f}%")
    st.progress(p)

with col3:
    p=progress_hitos(hitos)
    st.write(f"Hitos {p*100:.1f}%")
    st.progress(p)

with col4:
    p=progress_spares(spares)
    st.write(f"Repuestos {p*100:.1f}%")
    st.progress(p)

st.divider()

level = st.radio("Nivel",[0,1,2])
render_gantt(tareas, level)

st.divider()

edited = st.data_editor(tareas)

if st.button("Guardar tareas"):
    write_sheet("Tareas", edited)
    st.rerun()
