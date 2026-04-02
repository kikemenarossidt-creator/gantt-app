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

# --- CABECERA ---
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

# --- FICHA TÉCNICA ---
with st.expander("📋 FICHA TÉCNICA", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input("Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte")
    with c2:
        st.number_input("MWp", value=10.5)
        st.text_input("Inversores", "SUNGROW SG250HX")
    with c3:
        st.text_input("Alimentador", "DUAO 15 KV")
        st.text_input("Seguridad", "Prosegur")

# --- CRONOGRAMA ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")
if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        # Forzamos conversión a fecha para el gráfico
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        df_t['Level'] = pd.to_numeric(df_t['Level'], errors='coerce').fillna(0).astype(int)

        df_gantt = df_t.dropna(subset=['Start', 'End']).copy()
        df_gantt = df_gantt[df_gantt['End'] >= df_gantt['Start']]

        if not df_gantt.empty:
            prof = st.sidebar.slider("Nivel Detalle", 0, 2, 2)
            df_p = df_gantt[df_gantt['Level'] <= prof].copy()
            df_p['Display'] = df_p.apply(lambda x: "\xa0" * 6 * x['Level'] + str(x['Task']), axis=1)
            try:
                h = max(len(df_p) * 25, 200)
                base = alt.Chart(df_p).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
                text = base.mark_text(align='left').encode(text='Display:N').properties(width=300, height=h)
                bars = base.mark_bar().encode(
                    x=alt.X('Start:T'), x2='End:T',
                    color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None)
                ).properties(width=700, height=h)
                st.altair_chart(text | bars)
            except: st.error("Error visual en Gantt.")

        # EDITOR DE TABLA
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True, key="edit_t",
                                   column_config={
                                       "Start": st.column_config.DateColumn("Start", format="DD/MM/YYYY"),
                                       "End": st.column_config.DateColumn("End", format="DD/MM/YYYY")
                                   })
        
        if st.button("💾 Sincronizar Tareas"):
            try:
                df_save = df_t_edit.copy()
                # LIMPIEZA EXTREMA: Forzamos a string DD/MM/YYYY antes de subir
                df_save['Start'] = pd.to_datetime(df_save['Start']).dt.strftime('%d/%m/%Y').fillna("")
                df_save['End'] = pd.to_datetime(df_save['End']).dt.strftime('%d/%m/%Y').fillna("")
                
                # Convertimos todo a string para evitar errores de JSON con Google
                df_save = df_save.astype(str).replace('NaT', '').replace('nan', '')
                
                ws_tareas.clear()
                ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist())
                st.success("Guardado en 2025/2026 OK")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- RED ---
st.header("🌐 Red e IPs")
ws_red = conectar_hoja(client, "Red")
if ws_red:
    v_r = ws_red.get_all_values()
    df_r = pd.DataFrame(v_r[1:], columns=v_r[0]) if len(v_r) > 1 else pd.DataFrame(columns=["PROVEEDOR","REFERENCIA","MARCA","USO","DIRECCION IP","ESTADO"])
    if 'ESTADO' in df_r.columns: df_r['ESTADO'] = df_r['ESTADO'].astype(str).str.upper() == 'TRUE'
    df_r_ed = st.data_editor(df_r, hide_index=True, key="edit_r", column_config={"ESTADO": st.column_config.CheckboxColumn("Online")})
    if st.button("💾 Guardar Red"):
        df_r_ed['ESTADO'] = df_r_ed['ESTADO'].astype(str).upper()
        ws_red.clear(); ws_red.update([df_r_ed.columns.values.tolist()] + df_r_ed.astype(str).values.tolist()); st.rerun()

# --- CREDENCIALES ---
st.header("🔑 Credenciales")
ws_creds = conectar_hoja(client, "Credenciales")
if ws_creds:
    v_c = ws_creds.get_all_values()
    df_c = pd.DataFrame(v_c[1:], columns=v_c[0]) if len(v_c) > 1 else pd.DataFrame(columns=["EMPRESA","PLATAFORMA","USUARIO","CONTRASEÑA"])
    df_c_ed = st.data_editor(df_c, hide_index=True, key="edit_c")
    if st.button("💾 Guardar Credenciales"):
        ws_creds.clear(); ws_creds.update([df_c_ed.columns.values.tolist()] + df_c_ed.astype(str).values.tolist()); st.rerun()

# --- HITOS ---
st.header("💰 Hitos de Pago")
ws_hitos = conectar_hoja(client, "Hitos")
if ws_hitos:
    v_h = ws_hitos.get_all_values()
    df_h = pd.DataFrame(v_h[1:], columns=v_h[0]) if len(v_h) > 1 else pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])
    df_h['PAGADO'] = df_h['PAGADO'].astype(str).str.upper() == 'TRUE'
    df_h_ed = st.data_editor(df_h, hide_index=True, key="edit_h", column_config={"PAGADO": st.column_config.CheckboxColumn("Pagado")})
    if st.button("💾 Guardar Hitos"):
        df_h_ed['PAGADO'] = df_h_ed['PAGADO'].astype(str).upper()
        ws_hitos.clear(); ws_hitos.update([df_h_ed.columns.values.tolist()] + df_h_ed.astype(str).values.tolist()); st.rerun()

# --- REPUESTOS ---
st.header("📦 Repuestos")
ws_spare = conectar_hoja(client, "Repuestos")
if ws_spare:
    v_s = ws_spare.get_all_values()
    df_s = pd.DataFrame(v_s[1:], columns=v_s[0]) if len(v_s) > 1 else pd.DataFrame(columns=["CATEGORIA", "DESCRIPCION", "UNIDADES"])
    df_s_ed = st.data_editor(df_s, hide_index=True, key="edit_s")
    if st.button("💾 Guardar Repuestos"):
        ws_spare.clear(); ws_spare.update([df_s_ed.columns.values.tolist()] + df_s_ed.astype(str).values.tolist()); st.rerun()
