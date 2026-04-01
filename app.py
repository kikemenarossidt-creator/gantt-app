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

# --- LÓGICA DE CÁLCULO PARA EL VISOR ---
def calcular_avances():
    pct_hitos = 0
    pct_tareas = 0
    ws_hitos = conectar_hoja(client, "Hitos")
    if ws_hitos:
        v_h = ws_hitos.get_all_values()
        if len(v_h) > 1:
            df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
            df_h['val'] = df_h['PORCENTAJE'].str.replace('%', '').str.replace(',', '.').astype(float)
            pagados = df_h[df_h['PAGADO'].str.upper() == 'TRUE']['val'].sum()
            total = df_h['val'].sum()
            if total > 0: pct_hitos = (pagados / total)
    ws_tareas = conectar_hoja(client, "Tareas")
    if ws_tareas:
        data_t = ws_tareas.get_all_records()
        if data_t:
            df_t = pd.DataFrame(data_t)
            if 'Progress' in df_t.columns:
                df_t['Progress'] = pd.to_numeric(df_t['Progress'], errors='coerce').fillna(0)
                pct_tareas = df_t['Progress'].mean() / 100
    return pct_hitos, pct_tareas

# --- 1. CABECERA Y VISOR DE AVANCE ---
st.title("☀️ Control Integral de Proyecto")
hitos_av, tareas_av = calcular_avances()
col_v1, col_v2 = st.columns(2)
with col_v1:
    st.write(f"**Payment Milestones: {hitos_av*100:.1f}%**")
    st.progress(min(hitos_av, 1.0))
with col_v2:
    st.write(f"**Avance Obra: {tareas_av*100:.1f}%**")
    st.progress(min(tareas_av, 1.0))

st.divider()

# --- 2. FICHA TÉCNICA ---
with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("📍 Ubicación y Contacto")
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_area("Teléfonos de despacho", "+56 7 1263 5132\n+56 7 1263 5133", height=68)
    with c2:
        st.subheader("⚡ Datos Técnicos")
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.text_input("Inversores", "SUNGROW SG250HX")
    with c3:
        st.subheader("🏢 Info CGE / Seguridad")
        st.text_input("Nombre proyecto para CGE", "Maule X")
        st.text_input("Proveedor Seguridad", "Prosegur")

# --- 3. CRONOGRAMA ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")
if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        prof = st.sidebar.slider("Detalle Gantt (Nivel)", 0, 2, 2)
        df_p = df_t[df_t['Level'] <= prof].copy()
        df_p['Display'] = df_p.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)
        h = max(len(df_p) * 25, 200)
        base = alt.Chart(df_p).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
        text_layer = alt.layer(
            base.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold'),
            base.transform_filter(alt.datum.Level == 1).mark_text(align='left'),
            base.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic')
        ).encode(text='Display:N').properties(width=350, height=h)
        bars = base.mark_bar(cornerRadius=3).encode(
            x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')), x2='End:T',
            color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
            tooltip=['Task']
        ).properties(width=750, height=h)
        st.altair_chart(alt.hconcat(text_layer, bars))
        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True)
        if st.button("💾 Sincronizar Tareas"):
            df_save = df_t_edit.copy()
            df_save['Start'] = df_save['Start'].dt.strftime('%d/%m/%Y')
            df_save['End'] = df_save['End'].dt.strftime('%d/%m/%Y')
            ws_tareas.clear(); ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist()); st.rerun()

st.divider()

# --- 4. RED E IPs ---
st.header("🌐 Configuración de Red e IPs")
ws_red = conectar_hoja(client, "Red")
if ws_red:
    v_r = ws_red.get_all_values()
    df_r = pd.DataFrame(v_r[1:], columns=v_r[0]) if len(v_r) > 1 else pd.DataFrame(columns=["PROVEEDOR","REFERENCIA","MARCA","USO","DIRECCION IP","ESTADO"])
    if 'ESTADO' in df_r.columns: df_r['ESTADO'] = df_r['ESTADO'].apply(lambda x: str(x).upper() == 'TRUE')
    df_r_ed = st.data_editor(df_r, hide_index=True, use_container_width=True, column_config={"ESTADO": st.column_config.CheckboxColumn("Comunicando")})
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
    df_c_ed = st.data_editor(df_c, hide_index=True, use_container_width=True)
    if st.button("💾 Guardar Credenciales"):
        ws_creds.clear(); ws_creds.update([df_c_ed.columns.values.tolist()] + df_c_ed.values.tolist()); st.rerun()

st.divider()

# --- 6. HITOS DE PAGO ---
st.header("💰 Hitos de Pago")
ws_hitos = conectar_hoja(client, "Hitos")
if ws_hitos:
    v_h = ws_hitos.get_all_values()
    df_h = pd.DataFrame(v_h[1:], columns=v_h[0]) if len(v_h) > 1 else pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])
    df_h['PAGADO'] = df_h['PAGADO'].astype(str).str.upper() == 'TRUE'
    t1, t2 = st.tabs(["🚢 Offshore", "🏗️ Onshore"])
    cfg_h = {"PAGADO": st.column_config.CheckboxColumn("Pagado")}
    with t1:
        df_off = df_h[df_h["TIPO"] == "Offshore"].copy()
        ed_off = st.data_editor(df_off, hide_index=True, use_container_width=True, key="ed_off", column_config=cfg_h)
    with t2:
        df_on = df_h[df_h["TIPO"] == "Onshore"].copy()
        ed_on = st.data_editor(df_on, hide_index=True, use_container_width=True, key="ed_on", column_config=cfg_h)
    if st.button("💾 Guardar Hitos"):
        df_final = pd.concat([ed_off, ed_on])
        df_final['PAGADO'] = df_final['PAGADO'].astype(str).str.upper()
        ws_hitos.clear(); ws_hitos.update([df_final.columns.values.tolist()] + df_final.values.tolist()); st.rerun()

st.divider()

# --- 7. SPARE PARTS (MODO DINÁMICO: AÑADIR/ELIMINAR) ---
st.header("📦 Spare Parts Inventory (Repuestos)")
ws_spare = conectar_hoja(client, "Repuestos")
if ws_spare:
    v_s = ws_spare.get_all_values()
    if len(v_s) > 1:
        df_s = pd.DataFrame(v_s[1:], columns=v_s[0])
        # Aseguramos columna RECIBIDO si no existe
        if 'RECIBIDO' not in df_s.columns: df_s['RECIBIDO'] = "FALSE"
        df_s['RECIBIDO'] = df_s['RECIBIDO'].astype(str).str.upper() == 'TRUE'
    else:
        df_s = pd.DataFrame(columns=["CATEGORIA", "DESCRIPCION", "UNIDADES", "RECIBIDO"])

    # Aquí habilitamos añadir/eliminar con num_rows="dynamic"
    df_s_ed = st.data_editor(
        df_s, 
        hide_index=True, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={"RECIBIDO": st.column_config.CheckboxColumn("OK")},
        key="ed_spare_dynamic"
    )
    
    if st.button("💾 Guardar Inventario"):
        # Limpiar filas vacías y convertir booleano para Google Sheets
        df_to_save = df_s_ed.dropna(subset=["DESCRIPCION"])
        df_to_save['RECIBIDO'] = df_to_save['RECIBIDO'].astype(str).upper()
        ws_spare.clear()
        ws_spare.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        st.success("Inventario guardado")
        st.rerun()
