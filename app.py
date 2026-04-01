import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN - DEBE SER EL PRIMER COMANDO
st.set_page_config(layout="wide", page_title="Gantt Jerárquico")

# -------------------- FECHA BASE --------------------
base_date = datetime(2026, 4, 1)

st.title("📊 Planificación de Obra - Plantilla Completa")

# -------------------- DATOS INICIALES --------------------
# He añadido fechas a todas las tareas para que el gráfico NO salga en blanco.
if "df" not in st.session_state or st.session_state.df is None:
    tasks = [
        # 1. INSTALACIÓN ELÉCTRICA
        {"Task": "1: Instalación eléctrica", "Level": 0, "Start": base_date, "Finish": base_date + timedelta(days=20), "Status": "En curso"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Start": base_date, "Finish": base_date + timedelta(days=10), "Status": "En curso"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Start": base_date, "Finish": base_date + timedelta(days=5), "Status": "En curso"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Start": base_date + timedelta(days=1), "Finish": base_date + timedelta(days=6), "Status": "Completado"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Start": base_date + timedelta(days=2), "Finish": base_date + timedelta(days=7), "Status": "Completado"},
        {"Task": "Alimentaciones CCTV", "Level": 2, "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=10), "Status": "En curso"},
        
        {"Task": "Puestas a Tierra", "Level": 1, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=18), "Status": "Sin iniciar"},
        {"Task": "Vallado", "Level": 2, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=14), "Status": "Sin iniciar"},
        {"Task": "Trackers", "Level": 2, "Start": base_date + timedelta(days=12), "Finish": base_date + timedelta(days=18), "Status": "Sin iniciar"},
        
        {"Task": "Pruebas", "Level": 1, "Start": base_date + timedelta(days=18), "Finish": base_date + timedelta(days=25), "Status": "Sin iniciar"},
        {"Task": "Pruebas de aislamiento CTs", "Level": 2, "Start": base_date + timedelta(days=18), "Finish": base_date + timedelta(days=22), "Status": "Sin iniciar"},

        # 2. COMUNICACIONES
        {"Task": "2: Comunicaciones", "Level": 0, "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=30), "Status": "Sin iniciar"},
        {"Task": "Tendido Cableado", "Level": 1, "Start": base_date + timedelta(days=5), "Finish": base_date + timedelta(days=15), "Status": "Sin iniciar"},
        {"Task": "Fusionado de Fibras", "Level": 1, "Start": base_date + timedelta(days=15), "Finish": base_date + timedelta(days=25), "Status": "Sin iniciar"},
        {"Task": "Configuración Red", "Level": 2, "Start": base_date + timedelta(days=20), "Finish": base_date + timedelta(days=30), "Status": "Sin iniciar"},

        # 3. SENSORES
        {"Task": "3: Sensores", "Level": 0, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=20), "Status": "Sin iniciar"},
        {"Task": "Instalación Sensores", "Level": 1, "Start": base_date + timedelta(days=10), "Finish": base_date + timedelta(days=20), "Status": "Sin iniciar"},

        # 5. CTs
        {"Task": "5: CTs", "Level": 0, "Start": base_date + timedelta(days=20), "Finish": base_date + timedelta(days=40), "Status": "Sin iniciar"},
        {"Task": "Equipamiento CT2", "Level": 1, "Start": base_date + timedelta(days=20), "Finish": base_date + timedelta(days=30), "Status": "Sin iniciar"},

        # 7. CCTV
        {"Task": "7: CCTV", "Level": 0, "Start": base_date + timedelta(days=25), "Finish": base_date + timedelta(days=45), "Status": "Sin iniciar"},
        {"Task": "Montaje Cámaras", "Level": 1, "Start": base_date + timedelta(days=25), "Finish": base_date + timedelta(days=35), "Status": "Sin iniciar"},
    ]
    st.session_state.df = pd.DataFrame(tasks)

# -------------------- PROCESAMIENTO DEL GRÁFICO --------------------
df_plot = st.session_state.df.copy()

# Aseguramos que las fechas sean tratadas correctamente por Python
df_plot["Start"] = pd.to_datetime(df_plot["Start"])
df_plot["Finish"] = pd.to_datetime(df_plot["Finish"])

# Función para crear el escalonado visual (Indentación)
def format_name(row):
    name = str(row["Task"])
    level = int(row["Level"])
    # Usamos espacios especiales (\u00A0) para que el navegador no los borre
    indent = "\u00A0" * (level * 10) 
    if level == 0:
        return f"<b>{name.upper()}</b>"
    return f"{indent}{name}"

df_plot["Task_display"] = df_plot.apply(format_name, axis=1)

# Filtramos tareas sin fecha para que no de error
df_final = df_plot.dropna(subset=["Start", "Finish"])

# -------------------- DIBUJAR GANTT --------------------
st.subheader("📈 Cronograma Visual")

if not df_final.empty:
    fig = px.timeline(
        df_final, 
        x_start="Start", 
        x_end="Finish", 
        y="Task_display", 
        color="Status",
        category_orders={"Task_display": df_plot["Task_display"].tolist()},
        color_discrete_map={
            "Completado": "#27AE60", # Verde
            "En curso": "#2980B9",   # Azul
            "Sin iniciar": "#E67E22" # Naranja
        }
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=800,
        margin=dict(l=300), # Espacio para las etiquetas indentadas
        xaxis_title="Fecha de ejecución",
        yaxis_title=None
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay fechas configuradas. Por favor, revisa la tabla de abajo.")

# -------------------- TABLA PARA EDITAR --------------------
st.markdown("---")
st.subheader("📝 Tabla de Datos (Edita aquí)")
st.info("Cualquier cambio que hagas en esta tabla actualizará el gráfico de arriba automáticamente.")

edited_df = st.data_editor(
    st.session_state.df, 
    num_rows="dynamic", 
    use_container_width=True,
    column_config={
        "Level": st.column_config.NumberColumn("Nivel (0, 1, 2)", min_value=0, max_value=2),
        "Start": st.column_config.DateColumn("Fecha Inicio"),
        "Finish": st.column_config.DateColumn("Fecha Fin"),
        "Status": st.column_config.SelectboxColumn("Estado", options=["Sin iniciar", "En curso", "Completado"])
    }
)

# Guardar cambios en el estado de la aplicación
if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df
    st.rerun()
