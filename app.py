import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(layout="wide", page_title="Planificación Escalonada")

st.title("📊 Planificación de Obra - Estructura en Cascada")

# 2. CARGA DE DATOS (Mantenemos tu lista completa de 1-12)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # [Aquí va la lista completa que ya tenemos de las 12 secciones]
    # Se genera el DataFrame st.session_state.df con columnas 'Task' y 'Level'
    # ... (omito la lista larga por brevedad, pero debe estar presente)
    
    raw_tasks = [
        ("1: INSTALACIÓN ELÉCTRICA", 0), ("Tendido Eléctrico BT", 1), ("Cuadro protecciones SC", 2),
        ("Cuadro Comunicaciones SC", 2), ("Cuadro Sensores SC", 2), ("2: COMUNICACIONES", 0),
        ("Tendido Cableado", 1), ("CT1", 2), ("CT2", 2), ("3: SENSORES", 0), ("Instalación Equipos", 1)
        # ... continuar con el resto de las 100+ tareas enviadas antes
    ]
    formatted = [{"Task": n, "Level": l, "Start": base + timedelta(days=i), "Finish": base + timedelta(days=i+2)} for i, (n, l) in enumerate(raw_tasks)]
    st.session_state.df = pd.DataFrame(formatted)

# 3. PROCESAMIENTO DE SANGRÍA "FÍSICA"
df_plot = st.session_state.df.copy()
df_plot['unique_id'] = range(len(df_plot))

def make_indent(row):
    level = row['Level']
    name = str(row['Task'])
    
    # Usamos espacios Unicode de diferentes anchos para forzar el desplazamiento
    # \u2003 es un espacio largo (Em space)
    if level == 0:
        return f"<b>{name}</b>"
    elif level == 1:
        return f"\u2003\u2003{name}"
    else:
        return f"\u2003\u2003\u2003\u2003• {name}"

df_plot["Task_display"] = df_plot.apply(make_indent, axis=1)

# 4. GRÁFICO CON ALINEACIÓN FORZADA
dynamic_height = len(df_plot) * 25 + 200

fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="unique_id",
    color="Level",
    color_continuous_scale="Viridis",
    template="plotly_white"
)

# EL TRUCO ESTÁ AQUÍ:
fig.update_yaxes(
    tickmode='array',
    tickvals=df_plot['unique_id'],
    ticktext=df_plot['Task_display'],
    autorange="reversed",
    title=None,
    # Forzamos la alineación a la izquierda para que la sangría se note
    side="left",
    tickfont=dict(family="Courier New, monospace", size=12) # Monospace ayuda a la alineación
)

fig.update_layout(
    height=dynamic_height,
    margin=dict(l=600, r=20, t=50, b=50), # Margen gigante para que quepa el escalonado
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)
