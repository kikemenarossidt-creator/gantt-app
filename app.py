import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Jerárquico Dinámico")

# ---------- 1. BASE DE DATOS INICIAL ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # Lista inicial de tareas (todas las 12 categorías)
    tasks_data = [
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None},
        {"Task": "Tendido Cableado Datos", "Level": 1, "Parent": "2: COMUNICACIONES"},
        {"Task": "3: SENSORES", "Level": 0, "Parent": None},
        {"Task": "4: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None},
        {"Task": "5: TRACKERS Y TSM", "Level": 0, "Parent": None},
        {"Task": "6: CTs", "Level": 0, "Parent": None},
        {"Task": "7: CCTV", "Level": 0, "Parent": None},
        {"Task": "8: SEGURIDAD", "Level": 0, "Parent": None},
        {"Task": "9: ENTRONQUE", "Level": 0, "Parent": None},
        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None},
        {"Task": "11: PERMISOS", "Level": 0, "Parent": None},
        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None}
    ]
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": float(i), # Usamos float para permitir ordenación precisa
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

# ---------- 3. PROCESAMIENTO Y ORDEN ----------
# Ordenamos por el ID actual para mantener la secuencia de filas
st.session_state.df = st.session_state.df.sort_values(by="id").reset_index(drop=True)
st.session_state.df = update_hierarchical_dates(st.session_state.df)

st.sidebar.header("Vista")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)

df_chart = st.session_state.df.copy()
df_chart = df_chart[df_chart['Level'] <= profundidad].copy()
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

# ---------- 4. GRÁFICO ----------
h = len(df_chart) * 25
# IMPORTANTE: Ordenamos por 'id' que ahora es nuestra secuencia de filas
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

# ---------- 5. EDITOR ----------
st.divider()
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)
if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

# ---------- 6. LÓGICA DE INSERCIÓN (REORDENAR IDs) ----------
with st.expander("➕ Añadir Tarea en su grupo"):
    c1, c2 = st.columns(2)
    new_name = c1.text_input("Nombre de la tarea")
    new_level = c1.selectbox("Nivel", [0, 1, 2])
    parents = [None] + st.session_state.df[st.session_state.df['Level'] < new_level]['Task'].tolist()
    new_parent = c2.selectbox("Padre", parents)
    
    if st.button("Insertar Tarea"):
        df = st.session_state.df.copy()
        
        # 1. Encontrar dónde debe ir (justo después del padre o de su último hijo)
        if new_parent:
            # Buscamos la última tarea que pertenece a ese grupo
            indices_grupo = df[(df['Task'] == new_parent) | (df['Parent'] == new_parent)].index
            insert_pos = indices_grupo.max() + 1
        else:
            insert_pos = len(df)

        # 2. Desplazar todos los IDs que van después de esa posición
        df.loc[df.index >= insert_pos, 'id'] += 1
        
        # 3. Crear la nueva fila con el ID que quedó libre
        new_row = pd.DataFrame([{
            "id": float(insert_pos),
            "Task": new_name,
            "Level": new_level,
            "Parent": new_parent,
            "Start": df['Start'].min(), 
            "End": df['Start'].min() + timedelta(days=2)
        }])
        
        # 4. Combinar y re-ordenar todo
        st.session_state.df = pd.concat([df, new_row]).sort_values(by="id").reset_index(drop=True)
        # Re-indexar IDs para que sean enteros limpios (0, 1, 2, 3...)
        st.session_state.df['id'] = range(len(st.session_state.df))
        
        st.success(f"Tarea insertada en la posición {insert_pos}")
        st.rerun()
