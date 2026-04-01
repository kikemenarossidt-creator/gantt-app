import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Gantt & Red Solar Pro")

# --- CONEXIÓN A GOOGLE SHEETS ---
def conectar_ws(nombre_pestaña):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
        sheet_file = client.open_by_key(ID_HOJA)
        return sheet_file.worksheet(nombre_pestaña)
    except Exception as e:
        st.error(f"Error conectando a {nombre_pestaña}: {e}")
        return None

# --- 1. FICHA TÉCNICA DEL PROYECTO ---
st.title("☀️ Gestión Integral Planta Solar")

with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte, Chile")
    with c2:
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.text_input("Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Paneles", "JINKO Solar 550W")
        st.text_input("Trackers", "NextTracker 1P")

# --- 2. SECCIÓN CRONOGRAMA (Pestaña Tareas) ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_ws("Tareas")

if ws_tareas:
    df_tareas = pd.DataFrame(ws_tareas.get_all_records())
    df_tareas['Start'] = pd.to_datetime(df_tareas['Start'], dayfirst=True, errors='coerce')
    df_tareas['End'] = pd.to_datetime(df_tareas['End'], dayfirst=True, errors='coerce')
    
    # Gráfica Gantt
    profundidad = st.sidebar.slider("Nivel Detalle Gantt", 0, 2, 2)
    df_plot = df_tareas[df_tareas['Level'] <= profundidad].copy()
    df_plot['Display'] = df_plot.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)
    
    chart_h = max(len(df_plot) * 25, 150)
    base = alt.Chart(df_plot).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
    text = base.mark_text(align='left').encode(text='Display:N').properties(width=300, height=chart_h)
    bars = base.mark_bar().encode(
        x='Start:T', x2='End:T',
        color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
        tooltip=['Task', 'Empresa a Cargo']
    ).properties(width=800, height=chart_h)
    st.altair_chart(alt.hconcat(text, bars))

    if st.checkbox("Editar Tareas"):
        df_t_edit = st.data_editor(df_tareas, hide_index=True, use_container_width=True)
        if st.button("💾 Guardar Tareas"):
            df_t_edit['Start'] = df_t_edit['Start'].dt.strftime('%d/%m/%Y')
            df_t_edit['End'] = df_t_edit['End'].dt.strftime('%d/%m/%Y')
            ws_tareas.clear()
            ws_tareas.update([df_t_edit.columns.values.tolist()] + df_t_edit.values.tolist())
            st.rerun()

st.divider()

# --- 3. SECCIÓN RED Y COMUNICACIONES (Pestaña Red) ---
st.header("🌐 Configuración de Red e IPs")

# Inputs de red general (Segunda imagen)
c_net1, c_net2 = st.columns(2)
with c_net1:
    st.text_input("Net mask:", "255.255.255.0")
with c_net2:
    st.text_input("Gateway:", "192.168.30.1")

ws_red = conectar_ws("Red")

if ws_red:
    df_red = pd.DataFrame(ws_red.get_all_records())
    
    if df_red.empty:
        st.info("La pestaña 'Red' está vacía. Por favor, añade las columnas: PROVEEDOR, REFERENCIA, MARCA, USO, DIRECCION IP, ESTADO")
    else:
        # Editor de la tabla de IPs
        # El checkbox se mapea automáticamente a la columna ESTADO si es booleana
        df_red_edit = st.data_editor(
            df_red, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "ESTADO": st.column_config.CheckboxColumn(
                    "Comunicando",
                    help="Marcar si el equipo responde a PING",
                    default=False,
                ),
                "DIRECCION IP": st.column_config.TextColumn(
                    "Dirección IP",
                    validate=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
                )
            }
        )

        if st.button("💾 Sincronizar Estado de Red"):
            ws_red.clear()
            ws_red.update([df_red_edit.columns.values.tolist()] + df_red_edit.values.tolist())
            st.success("Configuración de red actualizada en Google Sheets")
            st.rerun()

# --- 4. AÑADIR ELEMENTO DE RED ---
with st.expander("➕ Añadir Nuevo Equipo a la Red"):
    f1, f2, f3, f4 = st.columns(4)
    with f1: n_prov = st.text_input("Proveedor")
    with f2: n_marca = st.text_input("Marca")
    with f3: n_uso = st.text_input("Uso/Equipo")
    with f4: n_ip = st.text_input("IP")
    
    if st.button("Insertar en Red"):
        nueva_ip = [[n_prov, "", n_marca, n_uso, n_ip, False]]
        ws_red.append_row(nueva_ip[0])
        st.rerun()
