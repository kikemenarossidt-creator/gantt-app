import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gestión Solar con Google Sheets")

# ---------- 1. CONFIGURACIÓN DE CONEXIÓN ----------
# Se espera que en .streamlit/secrets.toml estén las credenciales
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer datos
def load_data():
    try:
        # Reemplaza 'URL_DE_TU_HOJA' o usa la configurada en secrets
        return conn.read(worksheet="Tareas", ttl=0)
    except:
        return None

# ---------- 2. FICHA TÉCNICA DEL PROYECTO ----------
st.title("☀️ Control de Proyecto con Sincronización")

with st.expander("📋 FICHA TÉCNICA", expanded=False):
    col1, col2, col3 = st.columns(3)
    # Estos datos también podrían guardarse en otra pestaña de Sheets
    with col1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección URL", "https://maps.google.com/...")
    with col2:
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.text_input("Inversores", "SUNGROW SG250HX")
    with col3:
        st.text_input("Proveedor Internet", "Starlink Business")

# ---------- 3. CARGA DE DATOS (GOOGLE SHEETS O INICIAL) ----------
df = load_data()

if df is None or df.empty:
    st.warning("No se encontraron datos en Google Sheets. Cargando base predeterminada...")
    # Si la hoja está vacía, creamos la estructura de 42 tareas
    base_date = datetime(2026, 4, 1)
    tasks_data = [
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None, "Empresa": "Contratista A"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Empresa": "Contratista A"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Empresa": "Tableros X"},
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None, "Empresa": "Telco Solutions"},
        {"Task": "Tendido Fibra Óptica", "Level": 1, "Parent": "2: COMUNICACIONES", "Empresa": "Telco Solutions"},
        # ... Aquí irían las 42 tareas. 
    ]
    df = pd.DataFrame(tasks_data)
    df['id'] = range(len(df))
    df['Start'] = base_date
    df['End'] = base_date + timedelta(days=5)

# ---------- 4. LÓGICA DE JERARQUÍA ----------
def update_hierarchical_dates(df_input):
    temp_df = df_input.copy()
    temp_df['Start'] = pd.to_datetime(temp_df['Start'])
    temp_df['End'] = pd.to_datetime(temp_df['End'])
    
    # Lógica simplificada de fechas para evitar bucles
    for _ in range(3): # Repetir para asegurar que suban los niveles
        for idx, row in temp_df.iterrows():
            if row['Level'] < 2:
                children = temp_df[temp_df['Parent'] == row['Task']]
                if not children.empty:
                    temp_df.at[idx, 'Start'] = children['Start'].min()
                    temp_df.at[idx, 'End'] = children['End'].max()
    return temp_df

# ---------- 5. VISUALIZACIÓN GANTT ----------
df = update_hierarchical_dates(df)
profundidad = st.sidebar.slider("Ver niveles", 0, 2, 2)
df_chart = df[df['Level'] <= profundidad].sort_values('id')
df_chart['Display'] = df_chart.apply(lambda x: " " * 6 * int(x['Level']) + str(x['Task']), axis=1)

chart_h = len(df_chart) * 30
base_alt = alt.Chart(df_chart).encode(y=alt.Y('id:O', axis=None, sort='ascending'))

text = base_alt.mark_text(align='left', fontSize=12).encode(text='Display:N').properties(width=300, height=chart_h)
bars = base_alt.mark_bar(cornerRadius=3).encode(
    x=alt.X('Start:T', title='Fecha'), x2='End:T',
    color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
    tooltip=['Task', 'Empresa', 'Start', 'End']
).properties(width=800, height=chart_h)

st.altair_chart(alt.hconcat(text, bars), use_container_width=True)

# ---------- 6. EDITOR Y GUARDADO EN GOOGLE SHEETS ----------
st.subheader("📝 Editor de Tareas (Se guarda en la Nube)")
# IMPORTANTE: Aquí está la columna Empresa
edited_df = st.data_editor(
    df, 
    hide_index=True, 
    use_container_width=True,
    column_order=("id", "Task", "Level", "Parent", "Empresa", "Start", "End")
)

if st.button("💾 Guardar cambios en Google Sheets"):
    conn.update(worksheet="Tareas", data=edited_df)
    st.success("¡Datos sincronizados con Google Sheets!")
    st.rerun()

# ---------- 7. AÑADIR TAREA (CON COLUMNA EMPRESA) ----------
with st.expander("➕ Añadir Nueva Tarea"):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_t = st.text_input("Nombre de la Tarea")
        new_e = st.text_input("Empresa a Cargo") # <--- AQUÍ ESTÁ
    with col_b:
        new_l = st.selectbox("Nivel", [0, 1, 2])
        parents = [None] + df[df['Level'] < new_l]['Task'].tolist()
        new_p = st.selectbox("Padre", parents)
    with col_c:
        new_start = st.date_input("Inicio", datetime.now())
        
    if st.button("Añadir a la lista"):
        new_row = pd.DataFrame([{
            "id": len(df), "Task": new_t, "Level": new_l, 
            "Parent": new_p, "Empresa": new_e, # <--- SE INCLUYE
            "Start": pd.to_datetime(new_start), 
            "End": pd.to_datetime(new_start) + timedelta(days=2)
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(worksheet="Tareas", data=updated_df)
        st.rerun()
