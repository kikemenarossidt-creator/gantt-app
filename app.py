import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gestión de Proyecto Solar Pro")

# ---------- 1. INFORMACIÓN DEL PROYECTO (CABECERA) ----------
st.title("☀️ Control de Proyecto Fotovoltaico")

with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte, Chile")
        st.text_input("Dirección URL", "https://maps.google.com/...")
    with c2:
        st.number_input("Potencia Pico (MWp)", value=10.5, step=0.1)
        st.number_input("Potencia Nominal (MWn)", value=9.0, step=0.1)
        st.text_input("Marca / Modelo Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Marca / Modelo Paneles", "JINKO Solar 550W")
        st.text_input("Marca / Configuración Trackers", "NextTracker 1P")
        st.text_input("Proveedor Seguridad", "Prosegur / Hikvision")
    
    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("Proveedor Comunicaciones", "Entel Empresas")
    with c5: st.text_input("Proveedor Internet", "Starlink Business")

st.divider()

# ---------- 2. BASE DE DATOS MAESTRA (42 TAREAS) ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    # LISTADO COMPLETO DE TAREAS
    tasks_data = [
        # 1. ELÉCTRICA
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None, "Emp": "Principal"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Emp": "Sub-Eléctrica"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Emp": "Tableros Co."},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Emp": "Tableros Co."},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Emp": "Tableros Co."},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Emp": "Sub-Eléctrica"},
        {"Task": "Hincado de picas", "Level": 2, "Parent": "Puestas a Tierra", "Emp": "Civiles"},
        {"Task": "Vallado Eléctrico", "Level": 2, "Parent": "Puestas a Tierra", "Emp": "Sub-Eléctrica"},
        {"Task": "Pruebas Eléctricas", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Emp": "QA/QC"},
        {"Task": "Certificación de Aislamiento", "Level": 2, "Parent": "Pruebas Eléctricas", "Emp": "QA/QC"},

        # 2. COMUNICACIONES
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None, "Emp": "Telco"},
        {"Task": "Tendido Fibra Óptica", "Level": 1, "Parent": "2: COMUNICACIONES", "Emp": "Telco"},
        {"Task": "Fusión de fibras CT1", "Level": 2, "Parent": "Tendido Fibra Óptica", "Emp": "Telco"},
        {"Task": "Fusión de fibras CT2", "Level": 2, "Parent": "Tendido Fibra Óptica", "Emp": "Telco"},
        {"Task": "Equipos de Red", "Level": 1, "Parent": "2: COMUNICACIONES", "Emp": "IT Support"},
        {"Task": "Configuración Router/Switch", "Level": 2, "Parent": "Equipos de Red", "Emp": "IT Support"},

        # 3. SENSORES
        {"Task": "3: SENSORES", "Level": 0, "Parent": None, "Emp": "Meteo"},
        {"Task": "Montaje de Estación Meteo", "Level": 1, "Parent": "3: SENSORES", "Emp": "Meteo"},
        {"Task": "Instalación Piranómetros", "Level": 2, "Parent": "Montaje de Estación Meteo", "Emp": "Meteo"},
        {"Task": "Sensores de Temperatura Módulo", "Level": 2, "Parent": "Montaje de Estación Meteo", "Emp": "Meteo"},
        {"Task": "Calibración de Señal", "Level": 2, "Parent": "Montaje de Estación Meteo", "Emp": "Meteo"},

        # 4. ESTRUCTURAS
        {"Task": "4: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None, "Emp": "Montaje Pro"},
        {"Task": "Hincado de Perfiles", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Emp": "Civiles"},
        {"Task": "Montaje de Vigas y Correas", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Emp": "Montaje Pro"},
        {"Task": "Instalación de Módulos FV", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Emp": "Montaje Pro"},

        # 5. TRACKERS
        {"Task": "5: TRACKERS Y TSM", "Level": 0, "Parent": None, "Emp": "Tracker Co"},
        {"Task": "Montaje Motores Tracker", "Level": 1, "Parent": "5: TRACKERS Y TSM", "Emp": "Tracker Co"},
        {"Task": "Instalación Controladores TSM", "Level": 1, "Parent": "5: TRACKERS Y TSM", "Emp": "Tracker Co"},
        {"Task": "Puesta en marcha Tracker", "Level": 1, "Parent": "5: TRACKERS Y TSM", "Emp": "Tracker Co"},

        # 6 a 12
        {"Task": "6: CTs", "Level": 0, "Parent": None, "Emp": "Power SpA"},
        {"Task": "7: CCTV", "Level": 0, "Parent": None, "Emp": "Security"},
        {"Task": "8: SEGURIDAD", "Level": 0, "Parent": None, "Emp": "Security"},
        {"Task": "9: ENTRONQUE", "Level": 0, "Parent": None, "Emp": "Utility"},
        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None, "Emp": "QA/QC"},
        {"Task": "11: PERMISOS", "Level": 0, "Parent": None, "Emp": "Legal"},
        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None, "Emp": "O&M"}
    ]
    
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i, "Task": t["Task"], "Level": t["Level"], "Parent": t["Parent"],
            "Empresa a Cargo": t.get("Emp", "N/A"),
            "Start": pd.to_datetime(base + timedelta(days=i)),
            "End": pd.to_datetime(base + timedelta(days=i + 3))
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 3. LÓGICA DE FECHAS ----------
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

# ---------- 4. PROCESAMIENTO Y GRÁFICA ----------
st.session_state.df = st.session_state.df.sort_values('id').reset_index(drop=True)
st.session_state.df = update_hierarchical_dates(st.session_state.df)

st.sidebar.header("Vista")
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

# ---------- 5. EDITOR Y GESTIÓN ----------
st.divider()
st.subheader("📝 Tabla Maestra de Tareas")
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True, key=f"ed_{len(st.session_state.df)}")
if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

col_add, col_del = st.columns(2)
with col_add:
    with st.expander("➕ Añadir Nueva Tarea"):
        n_name = st.text_input("Nombre de tarea")
        n_emp = st.text_input("Empresa Responsable")
        n_level = st.selectbox("Nivel", [0, 1, 2])
        n_parent = st.selectbox("Padre", [None] + st.session_state.df[st.session_state.df['Level'] < n_level]['Task'].tolist())
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
        t_to_del = st.selectbox("Borrar tarea", ["---"] + st.session_state.df['Task'].tolist())
        if st.button("Confirmar Borrar"):
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
