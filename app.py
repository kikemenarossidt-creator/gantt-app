import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Jerárquico Automatizado")

# 1. ESTRUCTURA DE DATOS INICIAL
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # Definimos la estructura. Las fechas de Nivel 0 y 1 se sobrescribirán.
    tasks_data = [
        ("1: INSTALACIÓN ELÉCTRICA", 0), 
        ("Tendido Eléctrico BT", 1), 
        ("Cuadro protecciones SC", 2), ("Cuadro Comunicaciones SC", 2), ("Cuadro Sensores SC", 2),
        ("Cuadro Comunicaciones CT2", 2), ("Cuadro Sensores CT2", 2), ("Alimentaciones CCTV", 2),
        ("Alimentaciones TSM", 2), ("Alimentaciones Cuadros Monitorización", 2),
        ("Alimentaciones Cuadros Seguridad", 2), ("Alimentación Rack", 2),
        ("Alimentación Alumbrado y Secundarios", 2), 
        ("Puestas a Tierra", 1),
        ("Vallado", 2), ("TSMs", 2), ("Box TSM", 2), ("CCTV", 2), ("Vallado CT", 2),
        ("Pruebas", 1),
        ("Pruebas de aislamiento CT - Entronque", 2), ("Pruebas de aislamiento CTs", 2),
        ("2: COMUNICACIONES", 0), 
        ("Tendido Cableado", 1), ("CT1", 2), ("CT2", 2), ("Piranómetros", 2),
        ("Internet", 1), ("Router Medidor Entronque", 2), ("Antena / FO Entronque", 2),
        ("3: SENSORES", 0), 
        ("Instalación Equipos", 1), ("Soportes Piranómetros", 2), ("Sensores Temperatura", 2)
    ]
    
    rows = []
    for i, (name, level) in enumerate(tasks_data):
        rows.append({
            "id": i, "Task": name, "Level": level,
            "Start": base + timedelta(days=i*2),
            "End": base + timedelta(days=i*2 + 5),
        })
    st.session_state.df = pd.DataFrame(rows)

# --- FUNCIÓN DE CÁLCULO DE FECHAS DEPENDIENTES ---
def update_hierarchical_dates(df):
    df = df.copy()
    # Iteramos de abajo hacia arriba para que el Nivel 1 sume al 2, y el 0 al 1
    for level in [1, 0]:
        current_parent_idx = None
        for i in range(len(df)):
            if df.loc[i, 'Level'] == level:
                current_parent_idx = i
                # Buscamos todas las tareas que están "debajo" de este padre hasta el siguiente del mismo nivel o superior
                children_start = []
                children_end = []
                for j in range(i + 1, len(df)):
                    if df.loc[j, 'Level'] > level:
                        children_start.append(df.loc[j, 'Start'])
                        children_end.append(df.loc[j, 'End'])
                    else:
                        break
                
                if children_start and children_end:
                    df.loc[current_parent_idx, 'Start'] = min(children_start)
                    df.loc[current_parent_idx, 'End'] = max(children_end)
    return df

# 2. PROCESAMIENTO
# Aplicamos la lógica de dependencia de fechas
df_final = update_hierarchical_dates(st.session_state.df)

# Sidebar para el control retráctil
st.sidebar.header("Vista de Diagrama")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)

# Filtrado para la gráfica
df_chart = df_final[df_final['Level'] <= profundidad].copy()
df_chart['L0'] = df_chart.apply(lambda x: x['Task'] if x['Level'] == 0 else "", axis=1)
df_chart['L1'] = df_chart.apply(lambda x: x['Task'] if x['Level'] == 1 else "", axis=1)
df_chart['L2'] = df_chart.apply(lambda x: x['Task'] if x['Level'] == 2 else "", axis=1)

# 3. GRÁFICO ALTAIR
h = len(df_chart) * 22
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

c0 = alt.Chart(df_chart).mark_text(align='left', fontWeight='bold').encode(text='L0:N', **col_config).properties(width=160, height=h)
c1 = alt.Chart(df_chart).mark_text(align='left', dx=10).encode(text='L1:N', **col_config).properties(width=160, height=h)
c2 = alt.Chart(df_chart).mark_text(align='left', dx=20, fontStyle='italic', color='#555').encode(text='L2:N', **col_config).properties(width=200, height=h)

bars = alt.Chart(df_chart).mark_bar(cornerRadius=1).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None)
).properties(width=600, height=h)

st.altair_chart(alt.hconcat(c0, c1, c2, bars, spacing=0).configure_view(stroke=None))

# 4. EDITOR MAESTRO (Sin filtro)
st.divider()
st.subheader("📝 Editor de Tareas (Modifica Nivel 2 para actualizar Niveles 0 y 1)")
# El usuario edita st.session_state.df, y al recargar, la función update_hierarchical_dates recalcula todo
st.session_state.df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)
