import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Gestión Planta Solar Pro")

def obtener_cliente_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error en Credenciales: {e}")
        return None

def conectar_hoja(client, nombre_pestaña):
    ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
    try:
        return client.open_by_key(ID_HOJA).worksheet(nombre_pestaña)
    except:
        return None

# --- INICIALIZACIÓN ---
client = obtener_cliente_gspread()

# 1. FICHA TÉCNICA (CABECERA)
st.title("☀️ Control Integral de Proyecto")
with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte")
        st.text_input("URL Maps", "http://google.com/...")
    with c2:
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.number_input("Potencia Nominal (MWn)", value=9.0)
        st.text_input("Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Paneles", "JINKO Solar 550W")
        st.text_input("Trackers", "NextTracker 1P")
        st.text_input("Proveedor Seguridad", "Prosegur")

# 2. SECCIÓN TAREAS (CRONOGRAMA)
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")

if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        
        # --- GRÁFICA GANTT ---
        prof = st.sidebar.slider("Detalle Gantt", 0, 2, 2)
        df_p = df_t[df_t['Level'] <= prof].copy()
        df_p['Display'] = df_p.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)
        
        h = max(len(df_p) * 25, 200)
        base = alt.Chart(df_p).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
        
        text_layer = alt.layer(
            base.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold', fontSize=13),
            base.transform_filter(alt.datum.Level == 1).mark_text(align='left', fontSize=12),
            base.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
        ).encode(text='Display:N').properties(width=350, height=h)
        
        bars = base.mark_bar(cornerRadius=3).encode(
            x='Start:T', x2='End:T',
            color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
            tooltip=['Task', 'Empresa a Cargo']
        ).properties(width=750, height=h)
        
        st.altair_chart(alt.hconcat(text_layer, bars))
        
        # --- EDITOR TAREAS ---
        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True)
        
        if st.button("💾 Sincronizar Cambios de Tabla"):
            df_save = df_t_edit.copy()
            df_save['Start'] = df_save['Start'].dt.strftime('%d/%m/%Y')
            df_save['End'] = df_save['End'].dt.strftime('%d/%m/%Y')
            ws_tareas.clear()
            ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist())
            st.success("¡Tareas actualizadas!")
            st.rerun()

        # --- AÑADIR Y ELIMINAR TAREAS ---
        col_add, col_del = st.columns(2)
        with col_add:
            with st.expander("➕ Añadir Nueva Tarea"):
                with st.form("form_add_task"):
                    nt = st.text_input("Nombre de la Tarea")
                    ne = st.text_input("Empresa a Cargo")
                    nl = st.selectbox("Nivel", [0, 1, 2])
                    np = st.selectbox("Padre", [None] + df_t[df_t['Level'] < nl]['Task'].tolist())
                    if st.form_submit_button("Añadir a la lista"):
                        nueva_fila = [len(df_t), nt, nl, np if np else "", ne, 
                                     datetime.now().strftime('%d/%m/%Y'), 
                                     (datetime.now() + timedelta(days=5)).strftime('%d/%m/%Y')]
                        ws_tareas.append_row(nueva_fila)
                        st.rerun()
        with col_del:
            with st.expander("🗑️ Eliminar Tarea"):
                t_borrar = st.selectbox("Selecciona tarea para eliminar", ["---"] + df_t['Task'].tolist())
                if st.button("Eliminar Definitivamente"):
                    if t_borrar != "---":
                        df_final = df_t[df_t['Task'] != t_borrar].copy()
                        df_final['id'] = range(len(df_final))
                        ws_tareas.clear()
                        df_final['Start'] = df_final['Start'].dt.strftime('%d/%m/%Y')
                        df_final['End'] = df_final['End'].dt.strftime('%d/%m/%Y')
                        ws_tareas.update([df_final.columns.values.tolist()] + df_final.values.tolist())
                        st.rerun()

st.divider()

# 3. SECCIÓN RED (IPs)
st.header("🌐 Configuración de Red e IPs")

c_net1, c_net2 = st.columns(2)
with c_net1: st.text_input("Net mask:", value="255.255.255.0", key="mask_input")
with c_net2: st.text_input("Gateway:", value="192.168.30.1", key="gw_input")

ws_red = conectar_hoja(client, "Red")

if ws_red:
    try:
        # Cargamos datos y manejamos posibles celdas vacías
        vals_r = ws_red.get_all_values()
        if len(vals_r) > 0:
            # Usamos la primera fila como cabecera
            df_r = pd.DataFrame(vals_r[1:], columns=vals_r[0])
            # Convertimos la columna ESTADO a booleano para el checkbox
            df_r['ESTADO'] = df_r['ESTADO'].apply(lambda x: str(x).upper() == 'TRUE')
        else:
            df_r = pd.DataFrame(columns=["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"])

        # Editor de Red
        df_r_edit = st.data_editor(
            df_r,
            hide_index=True,
            use_container_width=True,
            column_config={
                "ESTADO": st.column_config.CheckboxColumn("Comunicando", default=False),
                "DIRECCION IP": st.column_config.TextColumn("Dirección IP", required=True)
            }
        )
        
        if st.button("💾 Guardar Estado de Red"):
            ws_red.clear()
            # Aseguramos que los booleanos se guarden como texto 'TRUE'/'FALSE' para Sheets
            ws_red.update([df_r_edit.columns.values.tolist()] + df_r_edit.values.tolist())
            st.success("Red actualizada")
            st.rerun()

    except Exception as e:
        st.error(f"Error al cargar red: {e}")

    # Formulario para añadir IP
    with st.expander("➕ Añadir Equipo a la Red"):
        with st.form("form_add_ip"):
            f1, f2, f3, f4 = st.columns(4)
            r_prov = f1.text_input("Proveedor")
            r_ref = f2.text_input("Referencia")
            r_marca = f3.text_input("Marca")
            r_uso = f4.text_input("Uso/Equipo")
            r_ip = st.text_input("IP (Obligatoria)")
            if st.form_submit_button("Añadir a Red"):
                if r_ip:
                    # Si la hoja está totalmente vacía, ponemos cabeceras
                    if not ws_red.get_all_values():
                        ws_red.append_row(["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"])
                    ws_red.append_row([r_prov, r_ref, r_marca, r_uso, r_ip, "FALSE"])
                    st.rerun()
                else:
                    st.warning("Debes introducir al menos la Dirección IP.")
