import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Gestión Planta Solar")

def obtener_cliente_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except: return None

def conectar_hoja(client, nombre_pestaña):
    ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
    try: return client.open_by_key(ID_HOJA).worksheet(nombre_pestaña)
    except: return None

client = obtener_cliente_gspread()

# --- CÁLCULO DE AVANCES ---
def calcular_avances():
    h, t = 0, 0
    ws_h = conectar_hoja(client, "Hitos")
    if ws_h:
        data = ws_h.get_all_records()
        if data:
            df = pd.DataFrame(data)
            df['PORCENTAJE'] = pd.to_numeric(df['PORCENTAJE'].astype(str).str.replace('%','').str.replace(',','.'), errors='coerce').fillna(0)
            pagados = df[df['PAGADO'].astype(str).upper() == 'TRUE']['PORCENTAJE'].sum()
            total = df['PORCENTAJE'].sum()
            h = (pagados / total) if total > 0 else 0
    ws_t = conectar_hoja(client, "Tareas")
    if ws_t:
        data = ws_t.get_all_records()
        if data:
            df = pd.DataFrame(data)
            t = pd.to_numeric(df['Progress'], errors='coerce').mean() / 100 if 'Progress' in df.columns else 0
    return h, t

# --- UI ---
st.title("☀️ Control de Proyecto Solar")
av_h, av_t = calcular_avances()
c1, c2 = st.columns(2)
c1.metric("Hitos de Pago", f"{av_h*100:.1f}%")
c1.progress(min(av_h, 1.0))
c2.metric("Avance Obra", f"{av_t*100:.1f}%")
c2.progress(min(av_t, 1.0))

st.divider()

# --- SECCIÓN TAREAS ---
st.header("📅 Cronograma")
ws_t = conectar_hoja(client, "Tareas")
if ws_t:
    df_t = pd.DataFrame(ws_t.get_all_records())
    # Editor de tareas (Añadir/Eliminar activado)
    df_t_ed = st.data_editor(df_t, hide_index=True, use_container_width=True, num_rows="dynamic", key="editor_tareas")
    if st.button("💾 Guardar Tareas"):
        ws_t.clear()
        ws_t.update([df_t_ed.columns.values.tolist()] + df_t_ed.values.tolist())
        st.rerun()

st.divider()

# --- SECCIÓN RED Y CREDENCIALES ---
col_a, col_b = st.columns(2)
with col_a:
    st.header("🌐 Red e IPs")
    ws_r = conectar_hoja(client, "Red")
    if ws_r:
        df_r = pd.DataFrame(ws_r.get_all_records())
        df_r_ed = st.data_editor(df_r, hide_index=True, use_container_width=True, num_rows="dynamic", key="editor_red")
        if st.button("💾 Guardar Red"):
            ws_r.clear(); ws_r.update([df_r_ed.columns.values.tolist()] + df_r_ed.values.tolist()); st.rerun()

with col_b:
    st.header("🔑 Credenciales")
    ws_c = conectar_hoja(client, "Credenciales")
    if ws_c:
        df_c = pd.DataFrame(ws_c.get_all_records())
        df_c_ed = st.data_editor(df_c, hide_index=True, use_container_width=True, num_rows="dynamic", key="editor_creds")
        if st.button("💾 Guardar Credenciales"):
            ws_c.clear(); ws_c.update([df_c_ed.columns.values.tolist()] + df_c_ed.values.tolist()); st.rerun()

st.divider()

# --- SECCIÓN HITOS ---
st.header("💰 Hitos de Pago")
ws_h = conectar_hoja(client, "Hitos")
if ws_h:
    df_h = pd.DataFrame(ws_h.get_all_records())
    df_h_ed = st.data_editor(df_h, hide_index=True, use_container_width=True, num_rows="dynamic", key="editor_hitos")
    if st.button("💾 Guardar Hitos"):
        ws_h.clear(); ws_h.update([df_h_ed.columns.values.tolist()] + df_h_ed.values.tolist()); st.rerun()

st.divider()

# --- SECCIÓN SPARE PARTS (REPUESTOS) ---
st.header("📦 Spare Parts (Repuestos)")
ws_s = conectar_hoja(client, "Repuestos")
if ws_s:
    # Obtener datos
    v_s = ws_s.get_all_values()
    if len(v_s) > 1:
        df_s = pd.DataFrame(v_s[1:], columns=v_s[0])
        # Convertir RECIBIDO a booleano para el checkbox de la tabla
        df_s['RECIBIDO'] = df_s['RECIBIDO'].astype(str).upper() == 'TRUE'
    else:
        df_s = pd.DataFrame(columns=["CATEGORIA", "DESCRIPCION", "UNIDADES", "RECIBIDO"])

    # Configuración de columnas para que SE VEA TODO
    config_s = {
        "CATEGORIA": st.column_config.SelectboxColumn("Categoría", options=["PANELS", "LV/MV COMPONENTS", "INVERTERS", "STRUCTURE", "SECURITY", "MONITORING", "OTROS"], width="medium"),
        "DESCRIPCION": st.column_config.TextColumn("Descripción", width="large", required=True),
        "UNIDADES": st.column_config.NumberColumn("Cant.", min_value=0),
        "RECIBIDO": st.column_config.CheckboxColumn("OK")
    }

    # Tabla dinámica (Añadir/Eliminar/Editar)
    df_s_ed = st.data_editor(df_s, hide_index=True, use_container_width=True, num_rows="dynamic", column_config=config_s, key="editor_repuestos")

    if st.button("💾 Guardar Inventario"):
        # Limpiar y convertir antes de subir
        df_final = df_s_ed.dropna(subset=["DESCRIPCION"])
        df_final['RECIBIDO'] = df_final['RECIBIDO'].astype(str).upper()
        ws_s.clear()
        ws_s.update([df_final.columns.values.tolist()] + df_final.values.tolist())
        st.success("Inventario guardado")
        st.rerun()
