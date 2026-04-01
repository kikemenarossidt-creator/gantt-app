import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Jerárquico Profesional")

# ---------- 1. BASE DE DATOS INICIAL ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
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

# ---------- 3. PROCESAMIENTO Y FILTRADO ----------
# Forzamos orden por ID siempre antes de mostrar
st.session_state.df = st.session_state.df.sort_values('id').reset_index(drop=True)
st.session_state.df = update_hierarchical_dates(st.session_state.df)

st.sidebar.header("Vista")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)

df_chart = st.session_state.df[st.session_state.df['Level'] <= profundidad].copy()
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

# ---------- 4. GRÁFICO ----------
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

# ---------- 5. EDITOR ----------
st.divider()
st.subheader("📝 Editor de Datos")
# Usamos un key dinámico basado en la longitud para forzar refresco al insertar
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True, key=f"editor_{len(st.session_state.df)}")
if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

# ---------- 6. LÓGICA DE INSERCIÓN "CORTAR Y PEGAR" ----------
with st.expander("➕ Añadir Nueva Tarea en su Posición Correcta"):
    c1, c2 = st.columns(2)
    new_name = c1.text_input("Nombre de la tarea")
    new_level = c1.selectbox("Nivel", [0, 1, 2])
    parents = [None] + st.session_state.df[st.session_state.df['Level'] < new_level]['Task'].tolist()
    new_parent = c2.selectbox("Padre", parents)
    
    if st.button("Insertar Tarea"):
        df = st.session_state.df.copy()
        
        if new_parent:
            # 1. Encontrar el índice del padre
            parent_idx = df[df['Task'] == new_parent].index[0]
            insert_pos = parent_idx + 1
            
            # 2. Buscar hasta dónde llegan sus descendientes
            for i in range(parent_idx + 1, len(df)):
                if df.iloc[i]['Level'] > df.loc[parent_idx, 'Level']:
                    insert_pos = i + 1
                else:
                    break
        else:
            insert_pos = len(df)

        # 3. Crear la nueva fila
        new_row = pd.DataFrame([{
            "id": 999, # Temporal
            "Task": new_name,
            "Level": new_level,
            "Parent": new_parent,
            "Start": df['Start'].min(), 
            "End": df['Start'].min() + timedelta(days=2)
        }])

        # 4. RECONSTRUIR EL DATAFRAME POR PARTES
        # Parte superior + Nueva fila + Parte inferior
        df_top = df.iloc[:insert_pos]
        df_bottom = df.iloc[insert_pos:]
        
        new_df = pd.concat([df_top, new_row, df_bottom]).reset_index(drop=True)
        
        # 5. REASIGNAR IDs DESDE CERO
        new_df['id'] = range(len(new_df))
        
        st.session_state.df = new_df
        st.rerun()
