import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Gantt Solar con Scroll Real")

# ---------- 1. BASE DE DATOS INICIAL ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks_data = [
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Hincado de picas", "Level": 2, "Parent": "Puestas a Tierra"},
        {"Task": "Vallado Eléctrico", "Level": 2, "Parent": "Puestas a Tierra"},
        {"Task": "Pruebas Eléctricas", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Certificación de Aislamiento", "Level": 2, "Parent": "Pruebas Eléctricas"},
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None},
        {"Task": "Tendido Fibra Óptica", "Level": 1, "Parent": "2: COMUNICACIONES"},
        {"Task": "Fusión de fibras CT1", "Level": 2, "Parent": "Tendido Fibra Óptica"},
        {"Task": "Fusión de fibras CT2", "Level": 2, "Parent": "Tendido Fibra Óptica"},
        {"Task": "Equipos de Red", "Level": 1, "Parent": "2: COMUNICACIONES"},
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
            "id": i, "Task": t["Task"], "Level": t["Level"], "Parent": t["Parent"],
            "Start": pd.to_datetime(base + timedelta(days=i)),
            "End": pd.to_datetime(base + timedelta(days=i + 3))
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 2. FUNCIONES DE CÁLCULO ----------
def update_hierarchical_dates(df):
    if df.empty: return df
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
                    starts.append(s)
                    ends.append(e)
            if not starts:
                row = df[df['Task'] == task_name].iloc[0]
                start, end = row['Start'], row['End']
            else:
                start, end = min(starts), max(ends)
        calculated[task_name] = (start, end)
        return start, end
    for root in df[df['Level'] == 0]['Task']:
        compute_dates(root)
    for task, (start, end) in calculated.items():
        if start and end:
            df.loc[df['Task'] == task, 'Start'] = start
            df.loc[df['Task'] == task, 'End'] = end
    return df

# ---------- 3. PROCESAMIENTO ----------
st.session_state.df = st.session_state.df.sort_values('id').reset_index(drop=True)
st.session_state.df = update_hierarchical_dates(st.session_state.df)

st.sidebar.header("Vista")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
alt_visor = st.sidebar.slider("Altura del visor (px)", 200, 1000, 500)

df_chart = st.session_state.df[st.session_state.df['Level'] <= profundidad].copy()
df_chart['Display_Task'] = df_chart.apply(lambda x: "&nbsp;" * 6 * int(x['Level']) + x['Task'], axis=1)

# ---------- 4. CONSTRUCCIÓN DEL GRÁFICO (ALTAIR A HTML) ----------
h_por_fila = 30
h_total = max(len(df_chart) * h_por_fila, 150)
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

base_text = alt.Chart(df_chart).encode(text='Display_Task:N', **col_config).properties(width=300, height=h_total)
text_layer = alt.layer(
    base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold', fontSize=13),
    base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left', fontSize=12),
    base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray', fontSize=11)
)
bars = alt.Chart(df_chart).mark_bar(cornerRadius=3).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m', title="Fecha")),
    x2='End:T',
    color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
    tooltip=['Task', 'Start', 'End'],
    **col_config
).properties(width=600, height=h_total)

chart_html = alt.hconcat(text_layer, bars, spacing=10).configure_view(stroke=None).to_json()

# ---------- 5. RENDERIZADO CON IFRAME (SCROLL REAL) ----------
st.subheader("📊 Cronograma de Obra")

# Usamos un componente de HTML puro para forzar el scroll
html_string = f"""
    <div id="vis" style="width: 1000px; height: {h_total}px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    <script>
        vegaEmbed('#vis', {chart_html});
    </script>
    <style>
        body {{ margin: 0; overflow-y: hidden; background-color: transparent; }}
        /* Estilizar el scroll para que se vea moderno */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 4px; }}
    </style>
"""

# Esta función de Streamlit crea el visor con scroll vertical
components.html(html_string, height=alt_visor, scrolling=True)

# ---------- 6. EDITOR Y ACCIONES ----------
st.divider()
st.subheader("📝 Gestión de Datos")
edited_df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True, key=f"ed_{len(st.session_state.df)}")
if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

col_add, col_del = st.columns(2)
with col_add:
    with st.expander("➕ Añadir Tarea"):
        n_name = st.text_input("Nombre")
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
            new_r = pd.DataFrame([{"id": 0, "Task": n_name, "Level": n_level, "Parent": n_parent, "Start": df['Start'].min(), "End": df['Start'].min() + timedelta(days=2)}])
            df = pd.concat([df.iloc[:ins_pos], new_r, df.iloc[ins_pos:]]).reset_index(drop=True)
            df['id'] = range(len(df))
            st.session_state.df = df
            st.rerun()

with col_del:
    with st.expander("🗑️ Eliminar Tarea"):
        t_to_del = st.selectbox("Tarea a eliminar", ["---"] + st.session_state.df['Task'].tolist())
        if st.button("Borrar"):
            if t_to_del != "---":
                df = st.session_state.df.copy()
                to_remove = [t_to_del]
                def find_ch(p_name):
                    chs = df[df['Parent'] == p_name]['Task'].tolist()
                    for c in chs:
                        to_remove.append(c)
                        find_ch(c)
                find_ch(t_to_del)
                df = df[~df['Task'].isin(to_remove)].copy()
                df['id'] = range(len(df))
                st.session_state.df = df
                st.rerun()
