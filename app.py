import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN DE LA PÁGINA (Debe ser lo primero)
st.set_page_config(layout="wide", page_title="Gantt Jerárquico")

# -------------------- FECHA BASE --------------------
base_date = datetime(2026, 4, 1)

st.title("📊 Control de Proyecto - Gantt Jerárquico")
st.markdown("---")

# -------------------- DATOS INICIALES --------------------
# Si no hay datos guardados, cargamos la estructura inicial
if "df" not in st.session_state:
    tasks = [
        # NIVEL 0: Título principal
        {"Task": "1: Instalación eléctrica", "Level": 0, "Start": base_date, "Finish": base_date + timedelta(days=15), "Status": "En curso"},
        # NIVEL 1: Subgrupo
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base_date, "Finish": base_date + timedelta(days=12), "Status": "En curso"},
        # NIVEL 2: Tareas específicas
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base_date, "Finish": base_date + timedelta(days=5), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base_date + timedelta(days=1), "Finish": base_date + timedelta(days=6), "Status": "Completado"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Start": base_date + timedelta(days=2), "Finish": base_date + timedelta(days=7), "Status": "Completado"},
        {"Task": "Cuadro Comunicaciones CT2", "Level": 2, "Start": base_date + timedelta(days=3), "Finish": base_date + timedelta(days=8), "Status": "Completado"},
        {"Task": "Cuadro Sensores CT2", "Level": 2, "Start": base_date + timedelta(days=4), "Finish": base_date + timedelta(days=9), "Status": "En curso"},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=10), "Status": "En curso"},
        
        # OTRO GRUPO
        {"Task": "2: Comunicaciones", "Level": 0, "Start": base_date + timedelta(days=6), "Finish": base_date + timedelta(days=20), "Status": "Sin iniciar"},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base_date + timedelta(days=7), "Finish": base_date + timedelta(days=18), "Status": "Sin iniciar"},
        {"Task": "Rack", "Level": 2, "Start": base_date + timedelta(days=8), "Finish": base_date + timedelta(days=12), "Status": "Sin iniciar"},
    ]
    st.session_state.df = pd.DataFrame(tasks)

# -------------------- PROCESAMIENTO VISUAL --------------------
df_plot = st.session_state.df.copy()

# Esta función crea el efecto de "escalera" en los nombres
def format_task_name(row):
    name = str(row["Task"])
    level = int(row["Level"])
    
    # \u00A0 es un espacio especial que Plotly NO puede ignorar
    # Multiplicamos por 8 para que se note mucho el escalonado
    indent = "\u00A0" * (level * 8) 
    
    if level == 0:
        return f"<b>{name.upper()}</b>"  # Negrita y Mayúsculas para el nivel principal
    elif level == 1:
        return f"{indent}<b>{name}</b>"   # Negrita e indentado para el nivel medio
    else:
        return f"{indent}{name}"          # Solo indentado para las tareas

# Creamos la columna que usaremos en el eje vertical
df_plot["Task_display"] = df_plot.apply(format_task_name, axis=1)

# -------------------- RENDERIZADO DEL GANTT --------------------
st.subheader("📈 Cronograma Escalonado")

# Filtramos solo las que tienen fechas para que no de error
df_plot_filtered = df_plot.dropna(subset=['Start', 'Finish'])

if not df_plot_filtered.empty:
    fig = px.timeline(
        df_plot_filtered, 
        x_start="Start", 
        x_end="Finish", 
        y="Task_display", 
        color="Status",
        # Esto es CLAVE: obliga a Plotly a mantener el orden de la tabla
        category_orders={"Task_display": df_plot["Task_display"].tolist()},
        color_discrete_map={
            "Completado": "#EF553B", # Rojo como en tu imagen
            "En curso": "#636EFA",   # Azul
            "Sin iniciar": "#AB63FA" # Morado/Rosa
        }
    )

    # Invertimos el eje Y para que la primera tarea salga arriba
    fig.update_yaxes(autorange="reversed")
    
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title=None,
        height=600,
        margin=dict(l=300), # Margen grande a la izquierda para que quepa el texto indentado
        legend_title_text="Estado"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay fechas definidas para mostrar el gráfico.")

# -------------------- EDITOR DE TABLA --------------------
st.markdown("---")
st.subheader("📝 Editor de Datos")
st.info("Puedes cambiar las fechas, niveles (0, 1, 2) o nombres aquí abajo y el gráfico se actualizará solo.")

# El editor de datos permite al usuario modificar la tabla directamente
edited_df = st.data_editor(
    st.session_state.df, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Level": st.column_config.NumberColumn("Nivel (0-2)", min_value=0, max_value=2, step=1),
        "Start": st.column_config.DateColumn("Inicio"),
        "Finish": st.column_config.DateColumn("Fin"),
        "Status": st.column_config.SelectboxColumn("Estado", options=["En curso", "Completado", "Sin iniciar"])
    }
)

# Guardamos los cambios
st.session_state.df = edited_df
