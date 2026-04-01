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
        st.error(f"Error en Credenciales GCP: {e}")
        return None

def conectar_hoja(client, nombre_pestaña):
    ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
    try:
        return client.open_by_key(ID_HOJA).worksheet(nombre_pestaña)
    except:
        return None

client = obtener_cliente_gspread()

# --- 1. FICHA TÉCNICA ---
st.title("☀️ Control Integral de Proyecto")
with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte")
    with c2:
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.text_input("Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Paneles", "JINKO Solar 550W")
        st.text_input("Proveedor Seguridad", "Prosegur")

# --- 2. SECCIÓN TAREAS ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")
if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        
        prof = st.sidebar.slider("Detalle Gantt", 0, 2, 2)
        df_p = df_t[df_t['Level'] <= prof].copy()
        df_p['Display'] = df_p.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)
        
        h = max(len(df_p) * 25, 200)
        base = alt.Chart(df_p).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
        text_l = alt.layer(
            base.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold'),
            base.transform_filter(alt.datum.Level == 1).mark_text(align='left'),
            base.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
        ).encode(text='Display:N').properties(width=350, height=h)
        bars = base.mark_bar().encode(x='Start:T', x2='End:T', color='Level:N').properties(width=750, height=h)
        st.altair_chart(alt.hconcat(text_l, bars))
        
        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True)
        if st.button("💾 Sincronizar Tareas"):
            df_save = df_t_edit.copy()
            df_save['Start'] = df_save['Start'].dt.strftime('%d/%m/%Y')
            df_save['End'] = df_save['End'].dt.strftime('%d/%m/%Y')
            ws_tareas.clear()
            ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist())
            st.rerun()

st.divider()

# --- 3. SECCIÓN RED (IPs) ---
st.header("🌐 Configuración de Red e IPs")
ws_red = conectar_hoja(client, "Red")
if ws_red:
    vals_r = ws_red.get_all_values()
    if len(vals_r) > 0:
        df_r = pd.DataFrame(vals_r[1:], columns=vals_r[0])
        df_r['ESTADO'] = df_r['ESTADO'].apply(lambda x: str(x).strip().upper() == 'TRUE')
    else:
        df_r = pd.DataFrame(columns=["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"])

    df_r_edit = st.data_editor(df_r, hide_index=True, use_container_width=True, column_config={"ESTADO": st.column_config.CheckboxColumn("Comunicando")})
    if st.button("💾 Guardar Red"):
        df_to_save = df_r_edit.copy()
        df_to_save['ESTADO'] = df_to_save['ESTADO'].astype(str).upper()
        ws_red.clear()
        ws_red.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        st.rerun()

st.divider()

# --- 4. SECCIÓN CREDENCIALES (NUEVA) ---
st.header("🔑 Credenciales de Planta")
ws_creds = conectar_hoja(client, "Credenciales")

if ws_creds:
    try:
        vals_c = ws_creds.get_all_values()
        if len(vals_c) > 0:
            df_c = pd.DataFrame(vals_c[1:], columns=vals_c[0])
        else:
            df_c = pd.DataFrame(columns=["EMPRESA", "PLATAFORMA", "USUARIO", "CONTRASEÑA"])

        # Editor de credenciales (permite editar directamente la tabla)
        df_c_edit = st.data_editor(
            df_c,
            hide_index=True,
            use_container_width=True,
            column_config={
                "CONTRASEÑA": st.column_config.TextColumn("Contraseña", help="Credenciales de acceso")
            }
        )

        if st.button("💾 Guardar Credenciales"):
            ws_creds.clear()
            ws_creds.update([df_c_edit.columns.values.tolist()] + df_c_edit.values.tolist())
            st.success("Credenciales actualizadas")
            st.rerun()

    except Exception as e:
        st.error(f"Error en Credenciales: {e}")

    # Formulario para añadir nuevas credenciales
    with st.expander("➕ Añadir Nueva Credencial"):
        with st.form("form_creds"):
            c1, c2 = st.columns(2)
            new_emp = c1.text_input("Empresa")
            new_plat = c2.text_input("Plataforma")
            new_user = c1.text_input("Usuario")
            new_pass = c2.text_input("Contraseña")
            
            if st.form_submit_button("Registrar Credencial"):
                if new_emp and new_plat:
                    # Verificar si la hoja está vacía para poner encabezados
                    if not ws_creds.get_all_values():
                        ws_creds.append_row(["EMPRESA", "PLATAFORMA", "USUARIO", "CONTRASEÑA"])
                    
                    ws_creds.append_row([new_emp, new_plat, new_user, new_pass])
                    st.success("Credencial añadida correctamente")
                    st.rerun()
                else:
                    st.warning("Empresa y Plataforma son campos obligatorios.")
