import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Gantt Solar Pro - Sync")

# --- CONEXIÓN A GOOGLE SHEETS ---
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
        sheet_file = client.open_by_key(ID_HOJA)
        return sheet_file.get_worksheet(0)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

ws = conectar_google_sheets()

# --- 1. INFORMACIÓN DEL PROYECTO (CABECERA) ---
st.title("☀️ Control de Proyecto Fotovoltaico")

with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte, Chile")
        st.text_input("Dirección Url", "https://maps.google.com/...")
    with c2:
        st.number_input("Potencia Pico (MWp)", value=10.5, step=0.1)
        st.number_input("Potencia Nominal (MWn)", value=9.0, step=0.1)
        st.text_input("Marca / Modelo Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Marca / Modelo Paneles", "JINKO Solar 550W")
        st.text_input("Marca / Configuracion Trackers", "NextTracker 1P")
        st.text_input("Proveedor Seguridad", "Prosegur")
    
    c4, c5, c6 = st.columns(3)
    with c4: st.text_input("Proveedor Comunicaciones", "Entel Empresas")
    with c5: st.text_input("Proveedor Internet", "Starlink Business")

st.divider()

# --- 2. CARGA Y PROCESAMIENTO DE DATOS ---
if ws:
    data = ws.get_all_records()
    if not data:
        st.warning("La hoja está vacía. Asegúrate de tener los encabezados: id, Task, Level, Parent, Empresa a Cargo, Start, End")
        st.stop()
    
    df = pd.DataFrame(data)
    df['Start'] = pd.to_datetime(df['Start'], dayfirst=True, errors='coerce')
    df['End'] = pd.to_datetime(df['End'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Task']).sort_values('id')

    # --- 3. GRÁFICA GANTT CON JERARQUÍA VISUAL ---
    st.subheader("📊 Cronograma Gantt")
    profundidad = st.sidebar.slider("Nivel de detalle visual", 0, 2, 2)
    df_chart = df[df['Level'] <= profundidad].copy()
    
    # Sangría para la tabla visual
    df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)

    chart_h = max(len(df_chart) * 30, 200)
    col_config = {"y": alt.Y('id:O', axis=None, sort='ascending')}

    # Capas de texto (Negrita para nivel 0, normal para 1, itálica para 2)
    base_text = alt.Chart(df_chart).encode(text='Display_Task:N', **col_config).properties(width=350, height=chart_h)
    
    text_layer = alt.layer(
        base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold', fontSize=13),
        base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left', fontSize=12),
        base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
    )

    # Barras de colores por nivel
    bars = alt.Chart(df_chart).mark_bar(cornerRadius=3).encode(
        x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
        x2='End:T',
        color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
        tooltip=['Task', 'Empresa a Cargo', 'Start', 'End'],
        **col_config
    ).properties(width=800, height=chart_h)

    st.altair_chart(alt.hconcat(text_layer, bars, spacing=5).configure_view(stroke=None))

    # --- 4. TABLA EDITOR ---
    st.subheader("📝 Gestión de Tareas")
    df_edited = st.data_editor(df, hide_index=True, use_container_width=True)

    if st.button("💾 Sincronizar Cambios en Google Sheets"):
        df_save = df_edited.copy()
        df_save['Start'] = df_save['Start'].dt.strftime('%d/%m/%Y')
        df_save['End'] = df_save['End'].dt.strftime('%d/%m/%Y')
        ws.clear()
        ws.update([df_save.columns.values.tolist()] + df_save.values.tolist())
        st.success("¡Datos actualizados en la nube!")
        st.rerun()

    # --- 5. AÑADIR Y ELIMINAR TAREAS ---
    st.divider()
    col_add, col_del = st.columns(2)

    with col_add:
        with st.expander("➕ Añadir Nueva Tarea"):
            n_name = st.text_input("Nombre de la tarea")
            n_emp = st.text_input("Empresa a Cargo")
            n_level = st.selectbox("Nivel", [0, 1, 2])
            n_parent = st.selectbox("Grupo Padre", [None] + df[df['Level'] < n_level]['Task'].tolist())
            
            if st.button("Insertar Tarea"):
                new_row = pd.DataFrame([{
                    "id": len(df), 
                    "Task": n_name, 
                    "Level": n_level, 
                    "Parent": n_parent, 
                    "Empresa a Cargo": n_emp,
                    "Start": datetime.now().strftime('%d/%m/%Y'),
                    "End": (datetime.now() + timedelta(days=5)).strftime('%d/%m/%Y')
                }])
                df_total = pd.concat([df, new_row], ignore_index=True)
                ws.clear()
                # Volvemos a formatear fechas para que Sheets no se queje
                df_total['Start'] = pd.to_datetime(df_total['Start']).dt.strftime('%d/%m/%Y')
                df_total['End'] = pd.to_datetime(df_total['End']).dt.strftime('%d/%m/%Y')
                ws.update([df_total.columns.values.tolist()] + df_total.values.tolist())
                st.rerun()

    with col_del:
        with st.expander("🗑️ Eliminar Tarea"):
            t_to_del = st.selectbox("Seleccionar tarea para borrar", ["---"] + df['Task'].tolist())
            if st.button("Confirmar Borrado"):
                if t_to_del != "---":
                    df_final = df[df['Task'] != t_to_del].copy()
                    df_final['id'] = range(len(df_final)) # Re-indexar
                    ws.clear()
                    df_final['Start'] = df_final['Start'].dt.strftime('%d/%m/%Y')
                    df_final['End'] = df_final['End'].dt.strftime('%d/%m/%Y')
                    ws.update([df_final.columns.values.tolist()] + df_final.values.tolist())
                    st.rerun()
