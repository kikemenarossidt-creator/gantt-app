import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gestión Solar Pro - 42 Tareas")

# ---------- 1. INFORMACIÓN DEL PROYECTO (CABECERA) ----------
st.title("☀️ Control de Proyecto Fotovoltaico")

with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte, Chile")
        st.text_input("Dirección URL", "http://maps.google.com/...")
    with c2:
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.number_input("Potencia Nominal (MWn)", value=9.0)
        st.text_input("Marca / Modelo Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Marca / Modelo Paneles", "JINKO Solar 550W")
        st.text_input("Marca / Configuración Trackers", "NextTracker 1P")
        st.text_input("Proveedor Seguridad", "Prosegur")

# ---------- 2. BASE DE DATOS MAESTRA (42 TAREAS CON EMPRESA) ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    tasks_data = [
        # 1. ELÉCTRICA
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None, "Emp": "Contratista Eléctrico A"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Emp": "Contratista Eléctrico A"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Emp": "Fabricante Tableros X"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Emp": "Fabricante Tableros X"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Emp": "Fabricante Tableros X"},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Emp": "Contratista Eléctrico A"},
        {"Task": "Hincado de picas", "Level": 2, "Parent": "Puestas a Tierra", "Emp": "Empresa Obras Civiles"},
        {"Task": "Vallado Eléctrico", "Level": 2, "Parent": "Puestas a Tierra", "Emp": "Contratista Eléctrico A"},
        {"Task": "Pruebas Eléctricas", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Emp": "QA/QC Interno"},
        {"Task": "Certificación de Aislamiento", "Level": 2, "Parent": "Pruebas Eléctricas", "Emp": "Organismo Certificador"},

        # 2. COMUNICACIONES
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None, "Emp": "Telco Solutions"},
        {"Task": "Tendido Fibra Óptica", "Level": 1, "Parent": "2: COMUNICACIONES", "Emp": "Telco Solutions"},
        {"Task": "Fusión de fibras CT1", "Level": 2, "Parent": "Tendido Fibra Óptica", "Emp": "Técnicos FO"},
        {"Task": "Fusión de fibras CT2", "Level": 2, "Parent": "Tendido Fibra Óptica", "Emp": "Técnicos FO"},
        {"Task": "Equipos de Red", "Level": 1, "Parent": "2: COMUNICACIONES", "Emp": "IT Global"},
        {"Task": "Configuración Router/Switch", "Level": 2, "Parent": "Equipos de Red", "Emp": "IT Global"},

        # 3. SENSORES
        {"Task": "3: SENSORES", "Level": 0, "Parent": None, "Emp": "Meteo Tech"},
        {"Task": "Montaje de Estación Meteo", "Level": 1, "Parent": "3: SENSORES", "Emp": "Meteo Tech"},
        {"Task": "Instalación Piranómetros", "Level": 2, "Parent": "Montaje de Estación Meteo", "Emp": "Meteo Tech"},
        {"Task": "Sensores de Temperatura Módulo", "Level": 2, "Parent": "Montaje de Estación Meteo", "Emp": "Meteo Tech"},
        {"Task": "Calibración de Señal", "Level": 2, "Parent": "Montaje de Estación Meteo", "Emp": "QA/QC Interno"},

        # 4. ESTRUCTURAS
        {"Task": "4: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None, "Emp": "Steel Build"},
        {"Task": "Hincado de Perfiles", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Emp": "Empresa Obras Civiles"},
        {"Task": "Montaje de Vigas y Correas", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Emp": "Steel Build"},
        {"Task": "Instalación de Módulos FV", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Emp": "Steel Build"},

        # 5. TRACKERS
        {"Task": "5: TRACKERS Y TSM", "Level": 0, "Parent": None, "Emp": "NextTracker Services"},
        {"Task": "Montaje Motores Tracker", "Level": 1, "Parent": "5: TRACKERS Y TSM", "Emp": "NextTracker Services"},
        {"Task": "Instalación Controladores TSM", "Level": 1, "Parent": "5: TRACKERS Y TSM", "Emp": "NextTracker Services"},
        {"Task": "Puesta en marcha Tracker", "Level": 1, "Parent": "5: TRACKERS Y TSM", "Emp": "Commissioning Team"},

        # 6 a 12 (Simplificados para el ejemplo, pero manteniendo Empresa)
        {"Task": "6: CTs", "Level": 0, "Parent": None, "Emp": "Power Grid SpA"},
        {"Task": "7: CCTV", "Level": 0, "Parent": None, "Emp": "Security Ops"},
        {"Task": "8: SEGURIDAD", "Level": 0, "Parent": None, "Emp": "Security Ops"},
        {"Task": "9: ENTRONQUE", "Level": 0, "Parent": None, "Emp": "Utility Company"},
        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None, "Emp": "QA/QC Interno"},
        {"Task": "11: PERMISOS", "Level": 0, "Parent": None, "Emp": "Gestoría Legal"},
        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None, "Emp": "Limpiezas Industriales"}
    ]
    
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i, "Task": t["Task"], "Level": t["Level"], "Parent": t["Parent"],
            "Empresa a Cargo": t["Emp"],
            "Start": pd.to_datetime(base + timedelta(days=i*2)),
            "End": pd.to_datetime(base + timedelta(days=i*2 + 4))
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 3. LÓGICA DE ACTUALIZACIÓN ----------
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
                if s and e: starts.append(s); ends.append(e)
            start, end = (min(starts), max(ends)) if starts else (df[df['Task'] == task_name]['Start'].iloc[0], df[df['Task'] == task_name]['End'].iloc[0])
        calculated[task_name] = (start, end)
        return start, end
    for root in df[df['Level'] == 0]['Task']: compute_dates(root)
    for task, (start, end) in calculated.items():
        df.loc[df['Task'] == task, 'Start'] = start
        df.loc[df['Task'] == task, 'End'] = end
    return df

# ---------- 4. RENDERIZADO ----------
st.session_state.df = st.session_state.df.sort_values('id').reset_index(drop=True)
st.session_state.df = update_hierarchical_dates(st.session_state.df)

profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
df_chart = st.session_state.df[st.session_state.df['Level'] <= profundidad].copy()
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

# GRÁFICA
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

# TABLA Y ACCIONES
st.divider()
st.subheader("📝 Tabla Maestra")
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True, key=f"ed_{len(st.session_state.df)}")
if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

col_add, col_del = st.columns(2)
with col_add:
    with st.expander("➕ Añadir Nueva Tarea"):
        n_name = st.text_input("Nombre")
        n_emp = st.text_input("Empresa Responsable")
        n_level = st.selectbox("Nivel", [0, 1, 2])
        n_parent = st.selectbox("Padre", [None] + st.session_state.df[st.session_state.df['Level'] < n_level]['Task'].tolist())
        if st.button("Insertar"):
            df = st.session_state.df.copy()
            new_r = pd.DataFrame([{"id": len(df), "Task": n_name, "Level": n_level, "Parent": n_parent, "Empresa a Cargo": n_emp, "Start": base, "End": base + timedelta(days=2)}])
            st.session_state.df = pd.concat([df, new_r]).reset_index(drop=True)
            st.rerun()

with col_del:
    with st.expander("🗑️ Eliminar Tarea"):
        t_to_del = st.selectbox("Tarea a borrar", ["---"] + st.session_state.df['Task'].tolist())
        if st.button("Borrar"):
            if t_to_del != "---":
                st.session_state.df = st.session_state.df[st.session_state.df['Task'] != t_to_del]
                st.rerun()
