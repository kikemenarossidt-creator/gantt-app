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

# --- 🔧 FIX FUNCIONES ---
def parse_fecha(x):
    try:
        if pd.isna(x) or x == "":
            return pd.NaT
        return pd.to_datetime(x, dayfirst=True)
    except:
        return pd.NaT

def recalcular_fechas_jerarquia(df):
    df = df.sort_values("id").copy()

    for i in reversed(range(len(df))):
        nivel = df.iloc[i]['Level']
        hijos = []
        j = i + 1

        while j < len(df) and df.iloc[j]['Level'] > nivel:
            if df.iloc[j]['Level'] == nivel + 1:
                hijos.append(df.iloc[j])
            j += 1

        if hijos:
            hijos_df = pd.DataFrame(hijos)

            ini = pd.to_datetime(hijos_df['Start'], errors='coerce')
            fin = pd.to_datetime(hijos_df['End'], errors='coerce')

            if ini.notna().any():
                df.at[df.index[i], 'Start'] = ini.min()

            if fin.notna().any():
                df.at[df.index[i], 'End'] = fin.max()

    return df

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

# --- 2. FICHA TÉCNICA ---
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

# --- 3. CRONOGRAMA (FIX APLICADO) ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")

if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)

        df_t['Start'] = df_t['Start'].apply(parse_fecha)
        df_t['End'] = df_t['End'].apply(parse_fecha)
        df_t['Level'] = pd.to_numeric(df_t['Level'], errors='coerce').fillna(0).astype(int)

        df_t = recalcular_fechas_jerarquia(df_t)

        df_gantt = df_t.dropna(subset=['Start', 'End']).copy()
        df_gantt = df_gantt[df_gantt['End'] >= df_gantt['Start']]

        if not df_gantt.empty:
            prof = st.sidebar.slider("Detalle Gantt (Nivel)", 0, 2, 2)
            df_p = df_gantt[df_gantt['Level'] <= prof].copy()
            df_p['Display'] = df_p.apply(lambda x: "\xa0" * 6 * x['Level'] + str(x['Task']), axis=1)

            h = max(len(df_p) * 25, 200)
            base = alt.Chart(df_p).encode(y=alt.Y('id:O', axis=None, sort='ascending'))

            text_layer = alt.layer(
                base.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold', fontSize=13),
                base.transform_filter(alt.datum.Level == 1).mark_text(align='left', fontSize=12),
                base.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
            ).encode(text='Display:N').properties(width=350, height=h)

            bars = base.mark_bar(cornerRadius=3).encode(
                x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
                x2='End:T',
                color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
                tooltip=['Task', 'Empresa a Cargo']
            ).properties(width=750, height=h)

            st.altair_chart(alt.hconcat(text_layer, bars))

        # --- EDITOR ---
        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True, key="edit_t",
                                   column_config={
                                       "Start": st.column_config.DateColumn("Start"),
                                       "End": st.column_config.DateColumn("End")
                                   })

        if st.button("💾 Sincronizar Tareas"):
            try:
                df_save = df_t_edit.copy()

                df_save['Start'] = pd.to_datetime(df_save['Start'], errors='coerce')
                df_save['End'] = pd.to_datetime(df_save['End'], errors='coerce')

                df_save['Start'] = df_save['Start'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "")
                df_save['End'] = df_save['End'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "")

                df_save = df_save.fillna("")

                ws_tareas.clear()
                ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist())

                st.success("¡Datos guardados con éxito!")
                st.rerun()

            except Exception as e:
                st.error(f"Error fatal al intentar guardar en Google Sheets: {e}")

        # --- AÑADIR / BORRAR ---
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("➕ Añadir Tarea"):
                with st.form("f_t"):
                    nt = st.text_input("Tarea"); ne = st.text_input("Empresa"); nl = st.selectbox("Nivel", [0,1,2])
                    if st.form_submit_button("Agregar"):
                        ws_tareas.append_row([len(df_t), nt, nl, 0, ne, datetime.now().strftime('%d/%m/%Y'), (datetime.now()+timedelta(5)).strftime('%d/%m/%Y')]); st.rerun()
        with c2:
            with st.expander("🗑️ Eliminar Tarea"):
                t_b = st.selectbox("Tarea", ["---"] + df_t['Task'].tolist())
                if st.button("Confirmar Borrado") and t_b != "---":
                    df_f = df_t[df_t['Task'] != t_b].copy(); df_f['id'] = range(len(df_f))
                    ws_tareas.clear(); df_f['Start'] = pd.to_datetime(df_f['Start']).dt.strftime('%d/%m/%Y'); df_f['End'] = pd.to_datetime(df_f['End']).dt.strftime('%d/%m/%Y')
                    ws_tareas.update([df_f.columns.values.tolist()] + df_f.fillna("").values.tolist()); st.rerun()

# --- 4. RED ---
st.header("🌐 Configuración de Red e IPs")
ws_red = conectar_hoja(client, "Red")
if ws_red:
    v_r = ws_red.get_all_values()
    df_r = pd.DataFrame(v_r[1:], columns=v_r[0]) if len(v_r) > 1 else pd.DataFrame(columns=["PROVEEDOR","REFERENCIA","MARCA","USO","DIRECCION IP","ESTADO"])
    if 'ESTADO' in df_r.columns: df_r['ESTADO'] = df_r['ESTADO'].astype(str).str.upper() == 'TRUE'
    df_r_ed = st.data_editor(df_r, hide_index=True, use_container_width=True, key="edit_r", column_config={"ESTADO": st.column_config.CheckboxColumn("Comunicando")})
    if st.button("💾 Guardar Red"):
        df_r_ed['ESTADO'] = df_r_ed['ESTADO'].astype(str).upper()
        ws_red.clear(); ws_red.update([df_r_ed.columns.values.tolist()] + df_r_ed.fillna("").values.tolist()); st.rerun()
    with st.expander("➕ Añadir IP"):
        with st.form("f_ip"):
            f1, f2, f3, f4, f5 = st.columns(5)
            p = f1.text_input("Prov"); r = f2.text_input("Ref"); m = f3.text_input("Marca"); u = f4.text_input("Uso"); ip = f5.text_input("IP")
            if st.form_submit_button("Añadir"): ws_red.append_row([p, r, m, u, ip, "FALSE"]); st.rerun()

st.divider()

# --- 5. CREDENCIALES ---
st.header("🔑 Credenciales")
ws_creds = conectar_hoja(client, "Credenciales")
if ws_creds:
    v_c = ws_creds.get_all_values()
    df_c = pd.DataFrame(v_c[1:], columns=v_c[0]) if len(v_c) > 1 else pd.DataFrame(columns=["EMPRESA","PLATAFORMA","USUARIO","CONTRASEÑA"])
    df_c_ed = st.data_editor(df_c, hide_index=True, use_container_width=True, key="edit_c")
    if st.button("💾 Guardar Credenciales"):
        ws_creds.clear(); ws_creds.update([df_c_ed.columns.values.tolist()] + df_c_ed.fillna("").values.tolist()); st.rerun()
    with st.expander("➕ Añadir Credencial"):
        with st.form("f_c"):
            c1, c2, c3, c4 = st.columns(4)
            ce = c1.text_input("Empresa"); cp = c2.text_input("Plat"); cu = c3.text_input("User"); cpw = c4.text_input("Pass")
            if st.form_submit_button("Añadir"): ws_creds.append_row([ce, cp, cu, cpw]); st.rerun()

st.divider()

# --- 6. HITOS ---
st.header("💰 Hitos de Pago (Payment Milestones)")
ws_hitos = conectar_hoja(client, "Hitos")
if ws_hitos:
    v_h = ws_hitos.get_all_values()
    if len(v_h) > 1:
        df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
        df_h['PAGADO'] = df_h['PAGADO'].astype(str).str.upper() == 'TRUE'
    else: df_h = pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])

    df_h_ed = st.data_editor(df_h, hide_index=True, use_container_width=True)
    if st.button("💾 Guardar Hitos"):
        df_h_ed['PAGADO'] = df_h_ed['PAGADO'].astype(str).upper()
        ws_hitos.clear(); ws_hitos.update([df_h_ed.columns.values.tolist()] + df_h_ed.fillna("").values.tolist()); st.rerun()

st.divider()

# --- 7. REPUESTOS ---
st.header("📦 Spare Parts Inventory (Repuestos)")
ws_spare = conectar_hoja(client, "Repuestos")
if ws_spare:
    v_s = ws_spare.get_all_values()
    df_s = pd.DataFrame(v_s[1:], columns=v_s[0]) if len(v_s) > 1 else pd.DataFrame(columns=["CATEGORIA", "DESCRIPCION", "UNIDADES"])

    df_s_ed = st.data_editor(df_s, hide_index=True, use_container_width=True)

    if st.button("💾 Guardar Inventario"):
        ws_spare.clear(); ws_spare.update([df_s_ed.columns.values.tolist()] + df_s_ed.fillna("").values.tolist()); st.rerun()
