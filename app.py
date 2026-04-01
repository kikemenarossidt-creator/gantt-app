import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Gestión Planta Solar Pro")

# Estilo para que las tablas no corten el texto
st.markdown("<style>.stDataEditor {width: 100% !important;}</style>", unsafe_allow_html=True)

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

# --- LÓGICA DE CÁLCULO ---
def calcular_avances():
    pct_hitos = 0; pct_tareas = 0
    ws_hitos = conectar_hoja(client, "Hitos")
    if ws_hitos:
        v_h = ws_hitos.get_all_values()
        if len(v_h) > 1:
            df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
            df_h['val'] = pd.to_numeric(df_h['PORCENTAJE'].str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
            pagados = df_h[df_h['PAGADO'].str.upper() == 'TRUE']['val'].sum()
            total = df_h['val'].sum()
            if total > 0: pct_hitos = (pagados / total)
    ws_tareas = conectar_hoja(client, "Tareas")
    if ws_tareas:
        data_t = ws_tareas.get_all_records()
        if data_t:
            df_t = pd.DataFrame(data_t)
            if 'Progress' in df_t.columns:
                pct_tareas = pd.to_numeric(df_t['Progress'], errors='coerce').mean() / 100
    return pct_hitos, pct_tareas

# --- 1. CABECERA ---
st.title("☀️ Control Integral de Proyecto")
hitos_av, tareas_av = calcular_avances()
c_v1, c_v2 = st.columns(2)
with c_v1:
    st.write(f"**Payment Milestones: {hitos_av*100:.1f}%**")
    st.progress(min(hitos_av, 1.0))
with c_v2:
    st.write(f"**Avance Obra: {tareas_av*100:.1f}%**")
    st.progress(min(tareas_av, 1.0))

st.divider()

# --- 2. FICHA TÉCNICA (EXPANDER) ---
with st.expander("📋 FICHA TÉCNICA"):
    c1, c2, c3 = st.columns(3)
