import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Jerárquico Profesional")

# ---------- 1. BASE DE DATOS COMPLETA (TODAS LAS TAREAS) ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    # Definición exhaustiva de la estructura jerárquica
    tasks_data = [
        # 1: INSTALACIÓN ELÉCTRICA
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Eléctrico BT"},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Vallado Eléctrico", "Level": 2, "Parent": "Puestas a Tierra"},
        {"Task": "Pruebas Eléctricas", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA"},
        {"Task": "Pruebas Aislamiento", "Level": 2, "Parent": "Pruebas Eléctricas"},

        # 2: COMUNICACIONES
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None},
        {"Task": "Tendido Cableado Datos", "Level": 1, "Parent": "2: COMUNICACIONES"},
        {"Task": "Configuración Router", "Level": 2, "Parent": "Tendido Cableado Datos"},
        {"Task": "Antena / FO", "Level": 2, "Parent": "Tendido Cableado Datos"},

        # 3: SENSORES
        {"Task": "3: SENSORES", "Level": 0, "Parent": None},
        {"Task": "Instalación Equipos", "Level": 1, "Parent": "3: SENSORES"},
        {"Task": "Soportes Piranómetros", "Level": 2, "Parent": "Instalación Equipos"},
        {"Task": "Sensores Temp", "Level": 2, "Parent": "Instalación Equipos"},

        # 4: MONTAJE ESTRUCTURAS
        {"Task": "4: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None},
        {"Task": "Hincado", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS"},
        {"Task": "Montaje Perfiles", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS"},
        {"Task": "Montaje Módulos", "Level": 2, "Parent": "Montaje Perfiles"},

        # 5: TRACKERS Y TSM
        {"Task": "5: TRACKERS Y TSM", "Level": 0, "Parent": None},
        {"Task": "Instalación TSM", "Level": 1, "Parent": "5: TRACKERS Y TSM"},
        {"Task": "Comisionado Tracker", "Level": 1, "Parent": "5: TRACKERS Y TSM"},

        # 6: CTs
        {"Task": "6: CTs", "Level": 0, "Parent": None},
        {"Task": "Instalación Celdas", "Level": 1, "Parent": "6: CTs"},
        {"Task": "Conexionado MT/BT", "Level": 1, "Parent": "6: CTs"},

        # 7: CCTV
        {"Task": "7: CCTV", "Level": 0, "Parent": None},
        {"Task": "Montaje Cámaras", "Level": 1, "Parent": "7: CCTV"},
        {"Task": "Configuración NVR", "Level": 1, "Parent": "7: CCTV"},

        # 8: SEGURIDAD
        {"Task": "8: SEGURIDAD", "Level": 0, "Parent": None},
        {"Task": "Cercado Perimetral", "Level": 1, "Parent": "8: SEGURIDAD"},
        {"Task": "Sistemas Alarma", "Level": 1, "Parent": "8: SEGURIDAD"},

        # 9: ENTRONQUE
        {"Task": "9: ENTRONQUE", "Level": 0, "Parent": None},
        {"Task": "Montaje Reconectador", "Level": 1, "Parent": "9: ENTRONQUE"},
        {"Task": "Medidor Energía", "Level": 1, "Parent": "9: ENTRONQUE"},

        # 10: PEM (CONEXIONADO)
        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None},
        {"Task": "Protocolos Pruebas", "Level": 1, "Parent": "10: PEM (CONEXIONADO)"},
        {"Task": "Energización", "Level": 1, "Parent": "10: PEM (CONEXIONADO)"},

        # 11: PERMISOS
        {"Task": "11: PERMISOS", "Level": 0, "Parent": None},
        {"Task": "Tramitación SEC", "Level": 1, "Parent": "11: PERMISOS"},
        {"Task": "Recepción Municipal", "Level": 1, "Parent": "11: PERMISOS"},

        # 12: SERVICIOS
        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None},
        {"Task": "Limpieza Módulos", "Level": 1, "Parent": "12: SERVICIOS"},
        {"Task": "Entrega Obra", "Level": 1, "Parent": "12: SERVICIOS"}
    ]
    
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i,
            "Task": t["Task"],
            "Level": t["Level"],
            "Parent": t["Parent"],
            "Start": base + timedelta(days=i*2),
            "End": base + timedelta(days=i*2 + 4)
        })
    st.session_state.df = pd.DataFrame(rows)

# ---------- 2. FUNCIÓN DE CÁLCULO DE FECHAS ----------
def update_hierarchical_dates(df):
    df = df.copy()
    # Asegurar formato datetime
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

    # Procesar desde la raíz (Nivel 0)
    for root in df[df['Level'] == 0]['Task']:
        compute_dates(root)

    # Actualizar el DataFrame con los resultados
    for task, (start, end) in calculated.items():
        df.loc[df['Task'] == task, 'Start'] = start
        df.loc[df['Task'] == task, 'End'] = end
    return df

# ---------- 3. PROCESAMIENTO Y FILTRADO ----------
# Recalcular fechas antes de mostrar
st.session_state.df = update_hierarchical_dates(st.session_state.df)

st.sidebar.header("Configuración de Vista")
profundidad = st.sidebar.slider("Nivel de detalle (0: Resumen, 2: Todo)", 0, 2, 2)

df_chart = st.session_state.df.copy()
df_chart = df_chart[df_chart['Level'] <= profundidad].copy()
# Sangría visual para el diagrama
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

# ---------- 4. GRÁFICO ALTAIR ----------
h = len(df_chart) * 25
col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

base_text = alt.Chart(df_chart).encode(
    text='Display_Task:N',
    **col_config
).properties(width=350, height=h)

text_layer = alt.layer(
    base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold', fontSize=13),
    base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left', fontSize=12),
    base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
)

bars = alt.Chart(df_chart).mark_bar(cornerRadius=3).encode(
    x=alt.X('Start:T', title="Cronograma", axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
    tooltip=['Task', 'Start', 'End'],
    **col_config
).properties(width=700, height=h)

st.altair_chart(alt.hconcat(text_layer, bars, spacing=5).configure_view(stroke=None))

# ---------- 5. EDITOR MAESTRO ----------
st.divider()
st.subheader("📝 Panel de Control y Edición")
st.info("💡 Edita las fechas de las tareas de Nivel 2 o 1 para que los grupos superiores se ajusten automáticamente.")

# Editor de datos
edited_df = st.data_editor(
    st.session_state.df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Start": st.column_config.DateColumn("Inicio"),
        "End": st.column_config.DateColumn("Fin"),
        "Level": st.column_config.NumberColumn("Nivel", disabled=True),
        "id": None # Ocultar ID
    }
)

if not edited_df.equals(st.session_state.df):
    st.session_state.df = update_hierarchical_dates(edited_df)
    st.rerun()

# ---------- 6. AÑADIR TAREAS DINÁMICAMENTE ----------
with st.expander("➕ Crear Nueva Sub-Tarea"):
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Nombre del ítem")
        new_level = st.radio("Nivel jerárquico", [0, 1, 2], horizontal=True)
    with col2:
        parents = [None] + st.session_state.df[st.session_state.df['Level'] < new_level]['Task'].tolist()
        new_parent = st.selectbox("Asignar a Padre", parents)
        
    c_date1, c_date2 = st.columns(2)
    new_start = c_date1.date_input("Inicia", datetime.today())
    new_end = c_date2.date_input("Termina", datetime.today() + timedelta(days=5))

    if st.button("Guardar e Integrar"):
        new_id = st.session_state.df['id'].max() + 1
        new_row = pd.DataFrame([{
            "id": new_id,
            "Task": new_name,
            "Level": new_level,
            "Parent": new_parent,
            "Start": pd.to_datetime(new_start),
            "End": pd.to_datetime(new_end)
        }])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df = update_hierarchical_dates(st.session_state.df)
        st.success("Estructura actualizada.")
        st.rerun()
