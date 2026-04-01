import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Jerárquico")

# 1. BASE DE DATOS (Se mantiene en el estado de la sesión)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    tasks_data = [
        ("1: INSTALACIÓN ELÉCTRICA", 0), ("Tendido Eléctrico BT", 1), 
        ("Cuadro protecciones SC", 2), ("Cuadro Comunicaciones SC", 2),
        ("Puestas a Tierra", 1), ("Vallado", 2),
        ("2: COMUNICACIONES", 0), ("Tendido Cableado", 1), ("CT1", 2),
        ("3: SENSORES", 0), ("Instalación Equipos", 1)
    ]
    rows = []
    for i, (name, level) in enumerate(tasks_data):
        rows.append({
            "id": i, "Task": name, "Level": level,
            "Start": base + timedelta(days=i*2),
            "End": base + timedelta(days=i*2 + 3),
        })
    st.session_state.df = pd.DataFrame(rows)

# 2. LÓGICA DE FECHAS (Niveles 0 y 1 dependen del nivel inferior)
def update_hierarchical_dates(df):
    df = df.copy()
    for level in [1, 0]:
        for i in range(len(df)):
            if df.loc[i, 'Level'] == level:
                children = df[(df.index > i) & (df['Level'] > level)]
                # Solo tomamos los hijos hasta que aparezca otro del mismo nivel o superior
                valid_children = []
                for _, child in children.iterrows():
                    if child['Level'] <= level: break
                    valid_children.append(child)
                
                if valid_children:
                    child_df = pd.DataFrame(valid_children)
                    df.loc[i, 'Start'] = child_df['Start'].min()
                    df.loc[i, 'End'] = child_df['End'].max()
    return df

# Ejecutamos el cálculo de fechas
df_final = update_hierarchical_dates(st.session_state.df)

# 3. FILTRADO POR NIVEL (Para el efecto retráctil)
st.sidebar.header("Vista de Diagrama")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)

# AQUÍ SE DEFINE df_chart (Antes de usarlo)
df_chart = df_final[df_final['Level'] <= profundidad].copy()

# CREACIÓN DE LA SANGRÍA (Para evitar los espacios en blanco de las columnas)
# Usamos \xa0 para que el navegador respete los espacios al inicio
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 4 * int(x['Level']) + x['Task'], axis=1)

# 4. CONFIGURACIÓN DEL GRÁFICO
h = len(df_chart) * 25
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

# Capa de texto única (Simula el árbol de Excel)
base_text = alt.Chart(df_chart).encode(
    text='Display_Task:N',
    **col_config
).properties(width=300, height=h)

# Aplicamos estilos según el nivel para que se vea como en tu imagen
text_layer = alt.layer(
    base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold'),
    base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left'),
    base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
)

# Barras de Gantt
bars = alt.Chart(df_chart).mark_bar(cornerRadius=2).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None),
    **col_config
).properties(width=600, height=h)

# Unión final sin espacios intermedios
st.altair_chart(alt.hconcat(text_layer, bars, spacing=10).configure_view(stroke=None))

# 5. EDITOR MAESTRO
st.divider()
st.subheader("📝 Editor Maestro")
st.session_state.df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)
