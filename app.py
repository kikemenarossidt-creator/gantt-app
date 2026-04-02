import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Gestión Planta Solar Pro")

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

# --- UTIL ---
def normalizar_bool(valor):
    try:
        if pd.isna(valor):
            return "FALSE"
    except:
        pass
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    s = str(valor).strip().upper()
    return "TRUE" if s in ("TRUE", "1", "SI", "S", "YES", "Y") else "FALSE"

# 🔥 FUNCIÓN CORREGIDA (CLAVE)
def guardar_df_en_worksheet(ws, df, date_cols=None, bool_cols=None):
    if ws is None:
        raise ValueError("Worksheet no disponible")

    date_cols = set(date_cols or [])
    bool_cols = set(bool_cols or [])

    df_ok = df.copy()

    for col in df_ok.columns:
        if col in date_cols:
            df_ok[col] = pd.to_datetime(df_ok[col], errors="coerce", dayfirst=True)\
                           .dt.strftime("%d/%m/%Y")
        elif col in bool_cols:
            df_ok[col] = df_ok[col].apply(normalizar_bool)

    # 🔥 evitar TODOS los errores de gspread
    df_ok = df_ok.astype(str).replace("nan", "")

    values = [df_ok.columns.tolist()] + df_ok.values.tolist()

    ws.clear()
    ws.resize(rows=len(values), cols=len(values[0]))
    ws.update(values)

# --- LÓGICA DE CÁLCULO SEGURA ---
def calcular_avances():
    pct_hitos, pct_tareas, pct_red = 0.0, 0.0, 0.0
    
    ws_hitos = conectar_hoja(client, "Hitos")
    if ws_hitos:
        v_h = ws_hitos.get_all_values()
        if len(v_h) > 1:
            df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
            if 'PORCENTAJE' in df_h.columns and 'PAGADO' in df_h.columns:
                df_h['val'] = pd.to_numeric(df_h['PORCENTAJE'].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
                pagados = df_h[df_h['PAGADO'].astype(str).str.upper() == 'TRUE']['val'].sum()
                total = df_h['val'].sum()
                if total > 0: pct_hitos = float(pagados / total)
            
    ws_tareas = conectar_hoja(client, "Tareas")
    if ws_tareas:
        data_t = ws_tareas.get_all_records()
        if data_t:
            df_t = pd.DataFrame(data_t)
            if 'Progress' in df_t.columns:
                pct_tareas = float(pd.to_numeric(df_t['Progress'], errors='coerce').fillna(0).mean() / 100)

    ws_red = conectar_hoja(client, "Red")
    if ws_red:
        v_r = ws_red.get_all_values()
        if len(v_r) > 1:
            df_r = pd.DataFrame(v_r[1:], columns=v_r[0])
            if 'ESTADO' in df_r.columns:
                total_ips = len(df_r)
                online = len(df_r[df_r['ESTADO'].astype(str).str.upper() == 'TRUE'])
                if total_ips > 0: pct_red = float(online / total_ips)
                
    return pct_hitos, pct_tareas, pct_red

# --- 1. CABECERA ---
st.title("☀️ Control Integral de Proyecto")

hitos_av, tareas_av, red_av = calcular_avances()

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.write(f"**Payment Milestones: {hitos_av*100:.1f}%**")
    st.progress(min(max(hitos_av, 0.0), 1.0))
with col_v2:
    st.write(f"**Avance Obra: {tareas_av*100:.1f}%**")
    st.progress(min(max(tareas_av, 0.0), 1.0))
with col_v3:
    st.write(f"**Configuración Red: {red_av*100:.1f}%**")
    st.progress(min(max(red_av, 0.0), 1.0))

st.divider()

# --- 3. CRONOGRAMA ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")
if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)

        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True, key="edit_t")
        
        if st.button("💾 Sincronizar Tareas"):
            try:
                guardar_df_en_worksheet(ws_tareas, df_t_edit, date_cols=['Start','End'])
                st.success("¡Datos guardados con éxito!")
                st.rerun()
            except Exception as e:
                st.error(f"Error fatal: {type(e).__name__} - {e}")

# --- 4. RED ---
st.header("🌐 Configuración de Red e IPs")
ws_red = conectar_hoja(client, "Red")
if ws_red:
    v_r = ws_red.get_all_values()
    df_r = pd.DataFrame(v_r[1:], columns=v_r[0]) if len(v_r) > 1 else pd.DataFrame()

    df_r_ed = st.data_editor(df_r, hide_index=True, use_container_width=True, key="edit_r")
    
    if st.button("💾 Guardar Red"):
        try:
            # 🔥 FIX REAL
            df_r_ed['ESTADO'] = df_r_ed['ESTADO'].apply(normalizar_bool)
            guardar_df_en_worksheet(ws_red, df_r_ed, bool_cols=['ESTADO'])
            st.rerun()
        except Exception as e:
            st.error(f"Error: {type(e).__name__} - {e}")
