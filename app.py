import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Gestión Planta Solar Pro")

# Estilo para asegurar que las tablas ocupen todo el ancho
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

# --- LÓGICA DE CÁLCULO PARA EL VISOR ---
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

# --- 1. CABECERA Y VISOR ---
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

# --- 2. FICHA TÉCNICA ---
with st.expander("📋 FICHA TÉCNICA", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Proyecto", "Planta Solar Atacama X")
        st.text_area("Despacho", "+56 7 1263 5132", height=68)
    with c2:
        st.number_input("MWp", value=10.5)
        st.text_input("Inversores", "SUNGROW")
    with c3:
        st.text_input("CGE", "Maule X")
        st.text_input("Seguridad", "Prosegur")

# --- 3. CRONOGRAMA (TAREAS) ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")
if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        
        df_chart = df_t.dropna(subset=['Start', 'End']).copy()
        if not df_chart.empty:
            chart = alt.Chart(df_chart).mark_bar(cornerRadius=3).encode(
                x=alt.X('Start:T', title="Fecha Inicio"), x2='End:T', y=alt.Y('Task:N', sort=None, title="Tarea"),
                color=alt.Color('Level:N', legend=None), tooltip=['Task', 'Progress']
            ).properties(height=350).interactive()
            st.altair_chart(chart, use_container_width=True)
        
        st.subheader("📝 Gestión de Tareas")
        df_t_ed = st.data_editor(df_t, hide_index=True, use_container_width=True, num_rows="dynamic",
                                 column_config={
                                     "Task": st.column_config.TextColumn("Tarea", width="large", required=True),
                                     "Progress": st.column_config.NumberColumn("%", min_value=0, max_value=100)
                                 })
        if st.button("💾 Guardar Tareas"):
            df_save = df_t_ed.copy()
            df_save['Start'] = df_save['Start'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")
            df_save['End'] = df_save['End'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")
            ws_tareas.clear(); ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist()); st.rerun()

st.divider()

# --- 4. RED E IPs ---
st.header("🌐 Configuración de Red")
ws_red = conectar_hoja(client, "Red")
if ws_red:
    v_r = ws_red.get_all_values()
    df_r = pd.DataFrame(v_r[1:], columns=v_r[0]) if len(v_r) > 1 else pd.DataFrame(columns=["PROVEEDOR","MARCA","USO","IP","ESTADO"])
    df_r['ESTADO'] = df_r['ESTADO'].astype(str).str.upper() == 'TRUE'
    df_r_ed = st.data_editor(df_r, hide_index=True, use_container_width=True, num_rows="dynamic", 
                             column_config={
                                 "USO": st.column_config.TextColumn("Uso/Destino", width="large"),
                                 "ESTADO": st.column_config.CheckboxColumn("OK")
                             })
    if st.button("💾 Guardar Red"):
        df_r_ed['ESTADO'] = df_r_ed['ESTADO'].astype(str).upper()
        ws_red.clear(); ws_red.update([df_r_ed.columns.values.tolist()] + df_r_ed.values.tolist()); st.rerun()

st.divider()

# --- 5. CREDENCIALES ---
st.header("🔑 Credenciales")
ws_creds = conectar_hoja(client, "Credenciales")
if ws_creds:
    v_c = ws_creds.get_all_values()
    df_c = pd.DataFrame(v_c[1:], columns=v_c[0]) if len(v_c) > 1 else pd.DataFrame(columns=["EMPRESA","PLATAFORMA","USUARIO","CONTRASEÑA"])
    df_c_ed = st.data_editor(df_c, hide_index=True, use_container_width=True, num_rows="dynamic",
                             column_config={"PLATAFORMA": st.column_config.TextColumn("Plataforma", width="medium")})
    if st.button("💾 Guardar Credenciales"):
        ws_creds.clear(); ws_creds.update([df_c_ed.columns.values.tolist()] + df_c_ed.values.tolist()); st.rerun()

st.divider()

# --- 6. PAYMENT MILESTONES (HITOS) ---
st.header("💰 Payment Milestones")
ws_hitos = conectar_hoja(client, "Hitos")
if ws_hitos:
    v_h = ws_hitos.get_all_values()
    df_h = pd.DataFrame(v_h[1:], columns=v_h[0]) if len(v_h) > 1 else pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])
    df_h['PAGADO'] = df_h['PAGADO'].astype(str).str.upper() == 'TRUE'
    
    t1, t2 = st.tabs(["🚢 Offshore", "🏗️ Onshore"])
    conf_h = {
        "PAGADO": st.column_config.CheckboxColumn("Pagado"),
        "HITO": st.column_config.TextColumn("Hito de Pago", width="large"),
        "PORCENTAJE": st.column_config.TextColumn("Cuota %", width="small")
    }
    with t1:
        df_off = df_h[df_h["TIPO"] == "Offshore"].copy()
        ed_off = st.data_editor(df_off, hide_index=True, use_container_width=True, num_rows="dynamic", key="ed_h_off", column_config=conf_h, column_order=("HITO", "PORCENTAJE", "PAGADO"))
    with t2:
        df_on = df_h[df_h["TIPO"] == "Onshore"].copy()
        ed_on = st.data_editor(df_on, hide_index=True, use_container_width=True, num_rows="dynamic", key="ed_h_on", column_config=conf_h, column_order=("HITO", "PORCENTAJE", "PAGADO"))
    
    if st.button("💾 Guardar Hitos"):
        df_final = pd.concat([ed_off, ed_on])
        df_final['PAGADO'] = df_final['PAGADO'].astype(str).upper()
        ws_hitos.clear(); ws_hitos.update([df_final.columns.values.tolist()] + df_final.values.tolist()); st.rerun()

st.divider()

# --- 7. SPARE PARTS INVENTORY (REPUESTOS) ---
st.header("📦 Spare Parts Inventory (Repuestos)")
ws_spare = conectar_hoja(client, "Repuestos")
if ws_spare:
    try:
        v_s = ws_spare.get_all_values()
        if len(v_s) > 1:
            df_s = pd.DataFrame(v_s[1:], columns=v_s[0])
            if 'RECIBIDO' not in df_s.columns: df_s['RECIBIDO'] = "FALSE"
            df_s['RECIBIDO'] = df_s['RECIBIDO'].astype(str).str.upper() == 'TRUE'
        else:
            df_s = pd.DataFrame(columns=["CATEGORIA", "DESCRIPCION", "UNIDADES", "RECIBIDO"])

        st.info("💡 Usa el '+' al final de la tabla para añadir. Selecciona filas y pulsa 'Supr' para eliminar.")

        config_spare = {
            "CATEGORIA": st.column_config.SelectboxColumn("Categoría", options=["PANELS", "LV/MV COMPONENTS", "INVERTERS", "STRUCTURE", "SECURITY", "MONITORING", "OTROS"], width="medium"),
            "DESCRIPCION": st.column_config.TextColumn("Descripción", width="large", required=True),
            "UNIDADES": st.column_config.NumberColumn("Cant.", min_value=0, default=1),
            "RECIBIDO": st.column_config.CheckboxColumn("OK")
        }

        df_s_ed = st.data_editor(df_s, hide_index=True, use_container_width=True, num_rows="dynamic", column_config=config_spare, key="ed_spare_final")

        if st.button("💾 Guardar Inventario"):
            df_final_s = df_s_ed.dropna(subset=["DESCRIPCION"]) # Evita guardar filas vacías
            df_final_s['RECIBIDO'] = df_final_s['RECIBIDO'].astype(str).upper()
            ws_spare.clear(); ws_spare.update([df_final_s.columns.values.tolist()] + df_final_s.values.tolist()); st.rerun()

    except Exception as e:
        st.error(f"Error en Spare Parts: {e}")
