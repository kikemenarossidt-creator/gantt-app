import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Jerárquico Profesional")

# ---------- 1. BASE DE DATOS COMPLETA (TODAS LAS TAREAS) ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    tasks_data = [
        {"Task": "01: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None},
        {"Task": "01.1: Tendido Eléctrico BT", "Level": 1, "Parent": "01: INSTALACIÓN ELÉCTRICA"},
        {"Task": "01.1.1: Cuadro protecciones SC", "Level": 2, "Parent": "01.1: Tendido Eléctrico BT"},
        {"Task": "01.1.2: Cuadro Comunicaciones SC", "Level": 2, "Parent": "01.1: Tendido Eléctrico BT"},
        {"Task": "01.1.3: Cuadro Sensores SC", "Level": 2, "Parent": "01.1: Tendido Eléctrico BT"},
        {"Task": "01.2: Puestas a Tierra", "Level": 1, "Parent": "01: INSTALACIÓN ELÉCTRICA"},
        {"Task": "01.2.1: Vallado Eléctrico", "Level": 2, "Parent": "01.2: Puestas a Tierra"},
        {"Task": "01.3: Pruebas Eléctricas", "Level": 1, "Parent": "01: INSTALACIÓN ELÉCTRICA"},
        {"Task": "01.3.1: Pruebas Aislamiento", "Level": 2, "Parent": "01.3: Pruebas Eléctricas"},

        {"Task": "02: COMUNICACIONES", "Level": 0, "Parent": None},
        {"Task": "02.1: Tendido Cableado Datos", "Level": 1, "Parent": "02: COMUNICACIONES"},
        {"Task": "02.1.1: Configuración Router", "Level": 2, "Parent": "02.1: Tendido Cableado Datos"},
        {"Task": "02.1.2: Antena / FO", "Level": 2, "Parent": "02.1: Tendido Cableado Datos"},

        {"Task": "03: SENSORES", "Level": 0, "Parent": None},
        {"Task": "03.1: Instalación Equipos", "Level": 1, "Parent": "03: SENSORES"},
        {"Task": "03.1.1: Soportes Piranómetros", "Level": 2, "Parent": "03.1: Instalación Equipos"},
        {"Task": "03.1.2: Sensores Temp", "Level": 2, "Parent": "03.1: Instalación Equipos"},

        {"Task": "04: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None},
        {"Task": "04.1: Hincado", "Level": 1, "Parent": "04: MONTAJE ESTRUCTURAS"},
        {"Task": "04.2: Montaje Perfiles", "Level": 1, "Parent": "04: MONTAJE ESTRUCTURAS"},
        {"Task": "04.2.1: Montaje Módulos", "Level": 2, "Parent": "04.2: Montaje Perfiles"},

        {"Task": "05: TRACKERS Y TSM", "Level": 0, "Parent": None},
        {"Task": "05.1: Instalación TSM", "Level": 1, "Parent": "05: TRACKERS Y TSM"},
        {"Task": "05.2: Comisionado Tracker", "Level": 1, "Parent": "05: TRACKERS Y TSM"},

        {"Task": "06: CTs", "Level": 0, "Parent": None},
        {"Task": "06.1: Instalación Celdas", "Level": 1, "Parent": "06: CTs"},
        {"Task": "06.2: Conexionado MT/BT", "Level": 1, "Parent": "06: CTs"},

        {"Task": "07: CCTV", "Level": 0, "Parent": None},
        {"Task": "07.1: Montaje Cámaras", "Level": 1, "Parent": "07: CCTV"},
        {"Task": "07.2: Configuración NVR", "Level": 1, "Parent": "07: CCTV"},

        {"Task": "08: SEGURIDAD", "Level": 0, "Parent": None},
        {"Task": "08.1: Cercado Perimetral", "Level": 1, "Parent": "08: SEGURIDAD"},
        {"Task": "08.2: Sistemas Alarma", "Level": 1, "Parent": "08: SEGURIDAD"},

        {"Task": "09: ENTRONQUE", "Level": 0, "Parent": None},
        {"Task": "09.1: Montaje Reconectador", "Level": 1, "Parent": "09: ENTRONQUE"},
        {"Task": "09.2: Medidor Energía", "Level": 1, "Parent": "09: ENTRONQUE"},

        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None},
        {"Task": "10.1: Protocolos Pruebas", "Level": 1, "Parent": "10: PEM (CONEXIONADO)"},
        {"Task": "10.2: Energización", "Level": 1, "Parent": "10: PEM (CONEXIONADO)"},

        {"Task": "11: PERMISOS", "Level": 0, "Parent": None},
        {"Task": "11.1: Tramitación SEC", "Level": 1, "Parent": "11: PERMISOS"},
        {"Task": "11.2: Recepción Municipal", "Level": 1, "Parent": "11: PERMISOS"},

        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None},
        {"Task": "12.1: Limpieza Módulos", "Level": 1, "Parent": "12: SERVICIOS"},
        {"Task": "12.2: Entrega Obra", "Level": 1, "Parent": "12: SERVICIOS"}
    ]
    
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i,
            "Task": t["Task"],
            "Level": t["Level"],
            "Parent": t["Parent"],
            "Start": pd.to_datetime(base + timedelta(days=i*2)),
            "End": pd.to_datetime(base + timedelta(days=i*2 + 4))
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 2. FUNCIÓN DE CÁLCULO DE FECHAS ----------
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

# ---------- 3. PROCESAMIENTO, ORDEN Y FILTRADO ----------
# Recalcular fechas
st.session_state.df = update_hierarchical_dates(st.session_state.df)

# ORDENAR ALFABÉTICAMENTE para que las nuevas tareas se agrupen con sus padres
st.session_state.df = st.session_state.df.sort_values(by="Task").reset_index(drop=True)

st.sidebar.header("Configuración de Vista")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)

df_chart = st.session_state.df.copy()
df_chart = df_chart[df_chart['Level'] <= profundidad].copy()

# Sangría visual (Usa el orden alfabético actual)
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

# ---------- 4. GRÁFICO ALTAIR ----------
h = len(df_chart) * 25
# Usamos sort=None para que respete el orden alfabético del DataFrame
col_config = {"y": alt.Y('Task:N', axis=None, sort=None)}

base_text = alt.Chart(df_chart).encode(
    text='Display_Task:N',
    **col_config
).properties(width=350, height=h)

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

# ---------- 5. EDITOR MAESTRO ----------
st.divider()
st.subheader("📝 Editor de Tareas")
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)

if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

# ---------- 6. AÑADIR TAREAS ----------
with st.expander("➕ Añadir Nueva Tarea"):
    c1, c2 = st.columns(2)
    new_name = c1.text_input("Nombre (ej: 01.4: Nueva Tarea)")
    new_level = c1.selectbox("Nivel", [0, 1, 2])
    
    parents = [None] + st.session_state.df[st.session_state.df['Level'] < new_level]['Task'].tolist()
    new_parent = c2.selectbox("Padre", parents)
    
    new_start = c2.date_input("Inicio")
    new_end = c2.date_input("Fin")

    if st.button("Añadir"):
        new_row = pd.DataFrame([{
            "id": st.session_state.df['id'].max() + 1,
            "Task": new_name,
            "Level": new_level,
            "Parent": new_parent,
            "Start": pd.to_datetime(new_start),
            "End": pd.to_datetime(new_end)
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.rerun()
