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

# --- 1. FICHA TÉCNICA ---
st.title("☀️ Control Integral de Proyecto")
with st.expander("📋 FICHA TÉCNICA DEL PROYECTO", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("📍 Ubicación y Contacto")
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Km 45, Ruta 5 Norte")
        st.text_area("Teléfonos de despacho", "+56 7 1263 5132\n+56 7 1263 5133", height=68)
    with c2:
        st.subheader("⚡ Datos Técnicos")
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.text_input("Inversores", "SUNGROW SG250HX")
        st.text_input("Paneles", "JINKO Solar 550W")
    with c3:
        st.subheader("🏢 Info CGE / Seguridad")
        st.text_input("Nombre proyecto para CGE", "Maule X")
        st.text_input("Nombre del alimentador", "DUAO 15 KV")
        st.text_input("Proveedor Seguridad", "Prosegur")

st.divider()

# --- 2. SECCIÓN TAREAS (DISEÑO ORIGINAL RECUPERADO) ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")
if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        
        # Gráfica Gantt con Sangrías
        prof = st.sidebar.slider("Detalle Gantt (Nivel)", 0, 2, 2)
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
            x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')), x2='End:T',
            color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
            tooltip=['Task', 'Empresa a Cargo']
        ).properties(width=750, height=h)
        st.altair_chart(alt.hconcat(text_layer, bars))
        
        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True)
        if st.button("💾 Sincronizar Cambios de Tabla"):
            df_save = df_t_edit.copy()
            df_save['Start'] = df_save['Start'].dt.strftime('%d/%m/%Y')
            df_save['End'] = df_save['End'].dt.strftime('%d/%m/%Y')
            ws_tareas.clear(); ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist()); st.rerun()

        col_add, col_del = st.columns(2)
        with col_add:
            with st.expander("➕ Añadir Nueva Tarea"):
                with st.form("f_add_task"):
                    nt = st.text_input("Nombre Tarea"); ne = st.text_input("Empresa"); nl = st.selectbox("Nivel", [0,1,2])
                    if st.form_submit_button("Añadir a la lista"):
                        ws_tareas.append_row([len(df_t), nt, nl, "", ne, datetime.now().strftime('%d/%m/%Y'), (datetime.now()+timedelta(5)).strftime('%d/%m/%Y')])
                        st.rerun()
        with col_del:
            with st.expander("🗑️ Eliminar Tarea"):
                t_b = st.selectbox("Tarea a eliminar", ["---"] + df_t['Task'].tolist())
                if st.button("Eliminar Definitivamente"):
                    df_f = df_t[df_t['Task'] != t_b].copy(); df_f['id'] = range(len(df_f))
                    ws_tareas.clear(); df_f['Start'] = df_f['Start'].dt.strftime('%d/%m/%Y'); df_f['End'] = df_f['End'].dt.strftime('%d/%m/%Y')
                    ws_tareas.update([df_f.columns.values.tolist()] + df_f.values.tolist()); st.rerun()

st.divider()

# --- 3. SECCIÓN RED (IPs) ---
st.header("🌐 Configuración de Red e IPs")
c_net1, c_net2 = st.columns(2)
with c_net1: st.text_input("Net mask:", value="255.255.255.0", key="nm_in")
with c_net2: st.text_input("Gateway:", value="192.168.30.1", key="gw_in")

ws_red = conectar_hoja(client, "Red")
if ws_red:
    v_r = ws_red.get_all_values()
    df_r = pd.DataFrame(v_r[1:], columns=v_r[0]) if len(v_r) > 1 else pd.DataFrame(columns=["PROVEEDOR","REFERENCIA","MARCA","USO","DIRECCION IP","ESTADO"])
    if 'ESTADO' in df_r.columns:
        df_r['ESTADO'] = df_r['ESTADO'].apply(lambda x: str(x).upper() == 'TRUE')
    
    df_r_ed = st.data_editor(df_r, hide_index=True, use_container_width=True, column_config={"ESTADO": st.column_config.CheckboxColumn("Comunicando")})
    
    if st.button("💾 Guardar Red"):
        df_r_ed['ESTADO'] = df_r_ed['ESTADO'].astype(str).upper()
        ws_red.clear(); ws_red.update([df_r_ed.columns.values.tolist()] + df_r_ed.values.tolist()); st.rerun()

    with st.expander("➕ Añadir Equipo a la Red"):
        with st.form("f_add_ip"):
            f1, f2, f3, f4 = st.columns(4)
            p, r, m, u = f1.text_input("Proveedor"), f2.text_input("Ref"), f3.text_input("Marca"), f4.text_input("Uso")
            ip_val = st.text_input("IP")
            if st.form_submit_button("Registrar IP"):
                ws_red.append_row([p, r, m, u, ip_val, "FALSE"]); st.rerun()

st.divider()

# --- 4. SECCIÓN CREDENCIALES ---
st.header("🔑 Credenciales de Planta")
ws_creds = conectar_hoja(client, "Credenciales")
if ws_creds:
    v_c = ws_creds.get_all_values()
    df_c = pd.DataFrame(v_c[1:], columns=v_c[0]) if len(v_c) > 1 else pd.DataFrame(columns=["EMPRESA","PLATAFORMA","USUARIO","CONTRASEÑA"])
    df_c_ed = st.data_editor(df_c, hide_index=True, use_container_width=True)
    if st.button("💾 Guardar Credenciales"):
        ws_creds.clear(); ws_creds.update([df_c_ed.columns.values.tolist()] + df_c_ed.values.tolist()); st.rerun()
    
    with st.expander("➕ Añadir Credencial"):
        with st.form("f_creds"):
            c1, c2 = st.columns(2)
            ce, cp, cu, cpw = c1.text_input("Empresa"), c2.text_input("Plataforma"), c1.text_input("Usuario"), c2.text_input("Contraseña")
            if st.form_submit_button("Registrar Credencial"):
                ws_creds.append_row([ce, cp, cu, cpw]); st.rerun()

st.divider()

# --- 5. SECCIÓN HITOS DE PAGO ---
st.header("💰 Hitos de Pago (Payment Milestones)")
ws_hitos = conectar_hoja(client, "Hitos")
if ws_hitos:
    try:
        v_h = ws_hitos.get_all_values()
        if len(v_h) > 1:
            df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
            if 'PAGADO' not in df_h.columns: df_h['PAGADO'] = "FALSE"
            df_h['PAGADO'] = df_h['PAGADO'].apply(lambda x: str(x).upper() == 'TRUE')
        else:
            df_h = pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])

        t1, t2 = st.tabs(["🚢 Offshore Payments", "🏗️ Onshore Payments"])
        
        # Configuración de columnas (incluimos el checkbox aquí)
        cfg = {
            "PAGADO": st.column_config.CheckboxColumn("Pagado"), 
            "PORCENTAJE": st.column_config.TextColumn("Cuota %")
        }

        with t1:
            df_off = df_h[df_h["TIPO"] == "Offshore"]
            # Añadimos hide_index=True para quitar la columna vacía del principio
            ed_off = st.data_editor(df_off, hide_index=True, use_container_width=True, key="ed_off", 
                                   column_order=("HITO", "PORCENTAJE", "PAGADO"), 
                                   column_config=cfg, num_rows="dynamic")
        with t2:
            df_on = df_h[df_h["TIPO"] == "Onshore"]
            # Añadimos hide_index=True aquí también
            ed_on = st.data_editor(df_on, hide_index=True, use_container_width=True, key="ed_on", 
                                  column_order=("HITO", "PORCENTAJE", "PAGADO"), 
                                  column_config=cfg, num_rows="dynamic")

        if st.button("💾 Guardar Hitos de Pago"):
            ed_off["TIPO"] = "Offshore"; ed_on["TIPO"] = "Onshore"
            df_final = pd.concat([ed_off, ed_on])
            df_final['PAGADO'] = df_final['PAGADO'].astype(str).upper()
            ws_hitos.clear(); ws_hitos.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("Hitos guardados correctamente"); st.rerun()
            
    except Exception as e:
        st.error(f"Error: {e}")
