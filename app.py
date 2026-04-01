import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Solar Pro - Gestión Completa")

# ---------- 1. BASE DE DATOS INICIAL (42 TAREAS) ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks_data = [
        # 1. INSTALACIÓN ELÉCTRICA
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Hincado de picas", "Level": 2, "Parent": "Puestas a Tierra"},
        {"Task": "Vallado Eléctrico", "Level": 2, "Parent": "Puestas a Tierra"},
        {"Task": "Pruebas Eléctricas", "Level": 1, "Parent": "1: INSTALACIÓN EL ELÉCTRICA"},
        {"Task": "Certificación de Aislamiento", "Level": 2, "Parent": "Pruebas Eléctricas"},
        # 2. COMUNICACIONES
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None},
        {"Task": "Tendido Fibra Óptica", "Level": 1, "Parent": "2: COMUNICACIONES"},
        {"Task": "Fusión de fibras CT1", "Level": 2, "Parent": "Tendido Fibra Óptica"},
        {"Task": "Fusión de fibras CT2", "Level": 2, "Parent": "Tendido Fibra Óptica"},
        {"Task": "Equipos de Red", "Level": 1, "Parent": "2: COMUNICACIONES"},
        {"Task": "Configuración Router/Switch", "Level": 2, "Parent": "Equipos de Red"},
        # 3. SENSORES
        {"Task": "3: SENSORES", "Level": 0, "Parent": None},
        {"Task": "Montaje de Estación Meteo", "Level": 1, "Parent": "3: SENSORES"},
        {"Task": "Instalación Piranómetros", "Level": 2, "Parent": "Montaje de Estación Meteo"},
        {"Task": "Sensores de Temperatura Módulo", "Level": 2, "Parent": "Montaje de Estación Meteo"},
        {"Task": "Calibración de Señal", "Level": 2, "Parent": "Montaje de Estación Meteo"},
        # 4. ESTRUCTURAS
        {"Task": "4: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None},
        {"Task": "Hincado de Perfiles", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS"},
        {"Task": "Montaje de Vigas y Correas", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS"},
        {"Task": "Instalación de Módulos FV", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS"},
        # 5. TRACKERS
        {"Task": "5: TRACKERS Y TSM", "Level": 0, "Parent": None},
        {"Task": "Montaje Motores Tracker", "Level": 1, "Parent": "5: TRACKERS Y TSM"},
        {"Task": "Instalación Controladores TSM", "Level": 1, "Parent": "5: TRACKERS Y TSM"},
        {"Task": "Puesta en marcha Tracker", "Level": 1, "Parent": "5: TRACKERS Y TSM"},
        # 6. CTs
        {"Task": "6: CTs", "Level": 0, "Parent": None},
        {"Task": "Posicionamiento de Inversores", "Level": 1, "Parent": "6: CTs"},
        {"Task": "Conexionado de Potencia BT/MT", "Level": 1, "Parent": "6: CTs"},
        # 7. CCTV
        {"Task": "7: CCTV", "Level": 0, "Parent": None},
        {"Task": "Instalación de Cámaras", "Level": 1, "Parent": "7: CCTV"},
        {"Task": "Configuración de Grabado VMS", "Level": 1, "Parent": "7: CCTV"},
        # 8 a 12 (Simplificados para brevedad de código, pero manteniendo estructura)
        {"Task": "8: SEGURIDAD", "Level": 0, "Parent": None},
        {"Task": "9: ENTRONQUE", "Level": 0, "Parent": None},
        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None},
        {"Task": "11: PERMISOS", "Level": 0, "Parent": None},
        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None}
    ]
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i, "Task": t["Task"], "Level": t["Level"], "Parent": t["Parent"],
            "Start": pd.to_datetime(base + timedelta(days=i)),
            "End": pd.to_datetime(base + timedelta(days=i + 3))
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 2. FUNCIONES DE CÁLCULO ----------
def update_hierarchical_dates(df):
    df = df.copy()
    df['Start'] = pd.to_datetime(df['Start'])
    df['End'] = pd.to_datetime(df['End'])
    calculated = {}
    def compute_dates(task_name):
        children = df[df['Parent'] == task_name]
        if children.empty:
            row = df[df['Task'] == task_name].iloc[0]
            start, end = row['Start'], row['End']
        else:
            starts, ends = [], []
            for child in children['Task']:
                s, e = compute_dates(child)
                starts.append(s)
                ends.append(e)
            start, end = min(starts), max(ends)
        calculated[task_name] = (start, end)
        return start, end
    for root in df[df['Level'] == 0]['Task']:
        compute_dates(root)
    for task, (start, end) in calculated.items():
        df.loc[df['Task'] == task, 'Start'] = start
        df.loc[df['Task'] == task, 'End'] = end
    return df

# ---------- 3. GESTIÓN DE BORRADO (SIDEBAR) ----------
st.sidebar.header("🗑️ Eliminar Tareas")
task_to_delete = st.sidebar.selectbox("Selecciona tarea para borrar", ["---"] + st.session_state.df['Task'].tolist())

if st.sidebar.button("Eliminar definitivamente"):
    if task_to_delete != "---":
        df = st.session_state.df.copy()
        # Encontrar la tarea y TODOS sus descendientes recursivamente
        tasks_to_remove = [task_to_delete]
        
        def find_children(parent_name):
            children = df[df['Parent'] == parent_name]['Task'].tolist()
            for child in children:
                tasks_to_remove.append(child)
                find_children(child)
        
        find_children(task_to_delete)
        # Filtrar el dataframe
        new_df = df[~df['Task'].isin(tasks_to_remove)].copy()
        # Resetear IDs
        new_df = new_df.sort_values('id').reset_index(drop=True)
        new_df['id'] = range(len(new_df))
        st.session_state.df = new_df
        st.sidebar.success(f"Eliminada '{task_to_delete}' y sus sub-tareas.")
        st.rerun()

# ---------- 4. PROCESAMIENTO Y FILTRADO ----------
st.session_state.df = st.session_state.df.sort_values('id').reset_index(drop=True)
st.session_state.df = update_hierarchical_dates(st.session_state.df)

profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
df_chart = st.session_state.df[st.session_state.df['Level'] <= profundidad].copy()
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

# ---------- 5. GRÁFICO ALTAIR ----------
h = len(df_chart) * 25
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}
base_text = alt.Chart(df_chart).encode(text='Display_Task:N', **col_config).properties(width=350, height=h)
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
).properties(width=700, height=h)
st.altair_chart(alt.hconcat(text_layer, bars, spacing=5).configure_view(stroke=None))

# ---------- 6. EDITOR Y AÑADIR ----------
st.divider()
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True, key=f"ed_{len(st.session_state.df)}")
if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

with st.expander("➕ Añadir Nueva Tarea"):
    c1, c2 = st.columns(2)
    new_name = c1.text_input("Nombre tarea")
    new_level = c1.selectbox("Nivel", [0, 1, 2])
    parents = [None] + st.session_state.df[st.session_state.df['Level'] < new_level]['Task'].tolist()
    new_parent = c2.selectbox("Padre", parents)
    if st.button("Insertar"):
        df = st.session_state.df.copy()
        if new_parent:
            parent_idx = df[df['Task'] == new_parent].index[0]
            ins_pos = parent_idx + 1
            for i in range(parent_idx + 1, len(df)):
                if df.iloc[i]['Level'] > df.loc[parent_idx, 'Level']: ins_pos = i + 1
                else: break
        else: ins_pos = len(df)
        new_row = pd.DataFrame([{"id": 0, "Task": new_name, "Level": new_level, "Parent": new_parent, "Start": df['Start'].min(), "End": df['Start'].min() + timedelta(days=3)}])
        new_df = pd.concat([df.iloc[:ins_pos], new_row, df.iloc[ins_pos:]]).reset_index(drop=True)
        new_df['id'] = range(len(new_df))
        st.session_state.df = new_df
        st.rerun()
