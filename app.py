import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Jerárquico Editable")

# ---------- 1. BASE DE DATOS INICIAL ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks_data = [
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Vallado", "Level": 2, "Parent": "Puestas a Tierra"},
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None},
        {"Task": "Tendido Cableado", "Level": 1, "Parent": "2: COMUNICACIONES"},
        {"Task": "CT1", "Level": 2, "Parent": "Tendido Cableado"},
        {"Task": "3: SENSORES", "Level": 0, "Parent": None},
        {"Task": "Instalación Equipos", "Level": 1, "Parent": "3: SENSORES"},
    ]
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i,
            "Task": t["Task"],
            "Level": t["Level"],
            "Parent": t["Parent"],
            "Start": base + timedelta(days=i*2),
            "End": base + timedelta(days=i*2 + 3)
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 2. FUNCIÓN RECURSIVA PARA ACTUALIZAR FECHAS ----------
def update_hierarchical_dates(df):
    df = df.copy()
    if 'Parent' not in df.columns:
        df['Parent'] = None

    # Función recursiva para calcular fechas de un nodo
    def compute_dates(task_name):
        children = df[df['Parent'] == task_name]
        if not children.empty:
            # Recurre a cada hijo
            for child in children['Task']:
                compute_dates(child)
            # Actualiza la fecha del padre considerando todos los hijos recursivos
            df.loc[df['Task'] == task_name, 'Start'] = children['Start'].min()
            df.loc[df['Task'] == task_name, 'End'] = children['End'].max()

    # Ejecutar para todas las tareas de nivel 0
    for root in df[df['Level'] == 0]['Task']:
        compute_dates(root)

    return df

# Ejecutar actualización de fechas
df_final = update_hierarchical_dates(st.session_state.df)

# ---------- 3. FILTRADO POR NIVEL ----------
st.sidebar.header("Vista de Diagrama")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
df_chart = df_final[df_final['Level'] <= profundidad].copy()
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 4 * int(x['Level']) + x['Task'], axis=1)

# ---------- 4. GRÁFICO ALTair ----------
h = len(df_chart) * 25
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

# Texto jerárquico
base_text = alt.Chart(df_chart).encode(
    text='Display_Task:N',
    **col_config
).properties(width=300, height=h)

text_layer = alt.layer(
    base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold'),
    base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left'),
    base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
)

# Barras Gantt
bars = alt.Chart(df_chart).mark_bar(cornerRadius=2).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None),
    **col_config
).properties(width=600, height=h)

st.altair_chart(alt.hconcat(text_layer, bars, spacing=10).configure_view(stroke=None))

# ---------- 5. EDITOR MAESTRO Y AÑADIR TAREAS ----------
st.divider()
st.subheader("📝 Editor y Añadir Tareas")

# Editor existente
st.session_state.df = st.data_editor(
    st.session_state.df,
    hide_index=True,
    use_container_width=True
)

# Añadir nueva tarea
with st.expander("➕ Añadir Nueva Tarea"):
    new_task_name = st.text_input("Nombre de la Tarea")
    new_task_level = st.selectbox("Nivel", [0,1,2])
    
    possible_parents = [None] + st.session_state.df[st.session_state.df['Level'] < new_task_level]['Task'].tolist()
    new_task_parent = st.selectbox("Grupo Padre", possible_parents)
    
    new_task_start = st.date_input("Fecha Inicio", datetime.today())
    new_task_end = st.date_input("Fecha Fin", datetime.today() + timedelta(days=2))
    
    if st.button("Añadir Tarea"):
        new_id = st.session_state.df['id'].max() + 1
        st.session_state.df.loc[new_id] = {
            "id": new_id,
            "Task": new_task_name,
            "Level": new_task_level,
            "Parent": new_task_parent,
            "Start": pd.Timestamp(new_task_start),
            "End": pd.Timestamp(new_task_end)
        }
        st.session_state.df = update_hierarchical_dates(st.session_state.df)
        st.success(f"Tarea '{new_task_name}' añadida correctamente.")
        st.experimental_rerun()
