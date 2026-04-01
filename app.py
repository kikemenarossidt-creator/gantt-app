import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gestión de Proyecto Solar")

# ---------- 1. INFORMACIÓN DEL PROYECTO (CABECERA) ----------
st.title("☀️ Control de Proyecto Fotovoltaico")

with st.container():
    st.subheader("📋 Información General")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte, Chile")
        st.text_input("Dirección URL (Google Maps)", "https://maps.google.com/...")
    with c2:
        st.number_input("Potencia Pico (MWp)", value=10.5, step=0.1)
        st.number_input("Potencia Nominal (MWn)", value=9.0, step=0.1)
        st.text_input("Marca / Modelo Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Marca / Modelo Paneles", "JINKO Solar 550W")
        st.text_input("Marca / Configuración Trackers", "NextTracker 1P")
        st.text_input("Proveedor Seguridad", "Prosegur / Hikvision")
    
    c4, c5, c6 = st.columns(3)
    with c4:
        st.text_input("Proveedor Comunicaciones", "Entel Empresas")
    with c5:
        st.text_input("Proveedor Internet", "Starlink Business")

st.divider()

# ---------- 2. BASE DE DATOS INICIAL ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks_data = [
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None, "Empresa": "Instaladora AC/DC"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Empresa": "Instaladora AC/DC"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Empresa": "Subcontrato Tableros"},
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None, "Empresa": "Telco Solutions"},
        {"Task": "3: SENSORES", "Level": 0, "Parent": None, "Empresa": "Meteo Chile"},
        {"Task": "4: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None, "Empresa": "Civiles S.A."},
        {"Task": "5: TRACKERS Y TSM", "Level": 0, "Parent": None, "Empresa": "Tracker Support"},
        {"Task": "6: CTs", "Level": 0, "Parent": None, "Empresa": "Power Grid"},
        {"Task": "7: CCTV", "Level": 0, "Parent": None, "Empresa": "Security Ops"},
        {"Task": "8: SEGURIDAD", "Level": 0, "Parent": None, "Empresa": "Cercados Pro"},
        {"Task": "9: ENTRONQUE", "Level": 0, "Parent": None, "Empresa": "Utility Corp"},
        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None, "Empresa": "Comisionado SpA"},
        {"Task": "11: PERMISOS", "Level": 0, "Parent": None, "Empresa": "Gestoría Legal"},
        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None, "Empresa": "O&M Services"}
    ]
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i, "Task": t["Task"], "Level": t["Level"], "Parent": t["Parent"],
            "Empresa a Cargo": t.get("Empresa", "N/A"),
            "Start": pd.to_datetime(base + timedelta(days=i*2)),
            "End": pd.to_datetime(base + timedelta(days=i*2 + 4))
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 3. FUNCIONES DE CÁLCULO ----------
def update_hierarchical_dates(df):
    df = df.copy()
    df['Start'] = pd.to_datetime(df['Start'])
    df['End'] = pd.to_datetime(df['End'])
    calculated = {}
    def compute_dates(task_name):
        children = df[df['Parent'] == task_name]
        if children.empty:
            match = df[df['Task'] == task_name]
            if match.empty: return None, None
            row = match.iloc[0]
            start, end = row['Start'], row['End']
        else:
            starts, ends = [], []
            for child in children['Task']:
                s, e = compute_dates(child)
                if s and e:
                    starts.append(s); ends.append(e)
            start, end = (min(starts), max(ends)) if starts else (df[df['Task'] == task_name]['Start'].iloc[0], df[df['Task'] == task_name]['End'].iloc[0])
        calculated[task_name] = (start, end)
        return start, end
    for root in df[df['Level'] == 0]['Task']:
        compute_dates(root)
    for task, (start, end) in calculated.items():
        df.loc[df['Task'] == task, 'Start'] = start
        df.loc[df['Task'] == task, 'End'] = end
    return df

# ---------- 4. PROCESAMIENTO Y GRÁFICA ----------
st.session_state.df = st.session_state.df.sort_values('id').reset_index(drop=True)
st.session_state.df = update_hierarchical_dates(st.session_state.df)

st.sidebar.header("Filtros de Vista")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
df_chart = st.session_state.df[st.session_state.df['Level'] <= profundidad].copy()
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

h_total = len(df_chart) * 30
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

base_text = alt.Chart(df_chart).encode(text='Display_Task:N', **col_config).properties(width=350, height=h_total)
text_layer = alt.layer(
    base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold'),
    base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left'),
    base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
)
bars = alt.Chart(df_chart).mark_bar(cornerRadius=3).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
    **col_config
).properties(width=700, height=h_total)

st.altair_chart(alt.hconcat(text_layer, bars, spacing=5).configure_view(stroke=None))

# ---------- 5. EDITOR Y ACCIONES ----------
st.divider()
st.subheader("📝 Tabla de Tareas y Responsables")
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True, key=f"ed_{len(st.session_state.df)}")
if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

col_add, col_del = st.columns(2)
with col_add:
    with st.expander("➕ Añadir Nueva Tarea"):
        n_name = st.text_input("Nombre de tarea")
        n_emp = st.text_input("Empresa a cargo")
        n_level = st.selectbox("Nivel", [0, 1, 2])
        n_parent = st.selectbox("Grupo Padre", [None] + st.session_state.df[st.session_state.df['Level'] < n_level]['Task'].tolist())
        if st.button("Insertar"):
            df = st.session_state.df.copy()
            if n_parent:
                p_idx = df[df['Task'] == n_parent].index[0]
                ins_pos = p_idx + 1
                for i in range(p_idx + 1, len(df)):
                    if df.iloc[i]['Level'] > df.loc[p_idx, 'Level']: ins_pos = i + 1
                    else: break
            else: ins_pos = len(df)
            new_r = pd.DataFrame([{"id": 0, "Task": n_name, "Level": n_level, "Parent": n_parent, "Empresa a Cargo": n_emp, "Start": df['Start'].min(), "End": df['Start'].min() + timedelta(days=2)}])
            df = pd.concat([df.iloc[:ins_pos], new_r, df.iloc[ins_pos:]]).reset_index(drop=True)
            df['id'] = range(len(df))
            st.session_state.df = df
            st.rerun()

with col_del:
    with st.expander("🗑️ Eliminar Tarea"):
        t_to_del = st.selectbox("Seleccionar para borrar", ["---"] + st.session_state.df['Task'].tolist())
        if st.button("Confirmar Borrado"):
            if t_to_del != "---":
                df = st.session_state.df.copy()
                to_remove = [t_to_del]
                def find_ch(p_name):
                    chs = df[df['Parent'] == p_name]['Task'].tolist()
                    for c in chs: to_remove.append(c); find_ch(c)
                find_ch(t_to_del)
                df = df[~df['Task'].isin(to_remove)].copy()
                df['id'] = range(len(df))
                st.session_state.df = df
                st.rerun()
