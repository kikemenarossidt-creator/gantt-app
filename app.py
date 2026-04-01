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

# 1. FICHA TÉCNICA
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

# 2. SECCIÓN TAREAS
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
        
        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(df_t, hide_index=True, use_container_width=True)
        if st.button("💾 Sincronizar Tareas"):
            df_save = df_t_edit.copy()
            df_save['Start'] = df_save['Start'].dt.strftime('%d/%m/%Y')
            df_save['End'] = df_save['End'].dt.strftime('%d/%m/%Y')
            ws_tareas.clear()
            ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist())
            st.rerun()

        c_add, c_del = st.columns(2)
        with c_add:
            with st.expander("➕ Añadir Tarea"):
                with st.form("f_add_t"):
                    nt = st.text_input("Tarea"); ne = st.text_input("Empresa"); nl = st.selectbox("Nivel", [0,1,2])
                    if st.form_submit_button("Añadir"):
                        ws_tareas.append_row([len(df_t), nt, nl, "", ne, datetime.now().strftime('%d/%m/%Y'), (datetime.now()+timedelta(5)).strftime('%d/%m/%Y')])
                        st.rerun()
        with c_del:
            with st.expander("🗑️ Eliminar Tarea"):
                t_b = st.selectbox("Tarea a borrar", ["---"] + df_t['Task'].tolist())
                if st.button("Eliminar"):
                    df_f = df_t[df_t['Task'] != t_b].copy()
                    df_f['id'] = range(len(df_f))
                    ws_tareas.clear()
                    df_f['Start'] = df_f['Start'].dt.strftime('%d/%m/%Y'); df_f['End'] = df_f['End'].dt.strftime('%d/%m/%Y')
                    ws_tareas.update([df_f.columns.values.tolist()] + df_f.values.tolist())
                    st.rerun()

st.divider()

# 3. SECCIÓN RED (IPs) - AQUÍ ESTABA EL FALLO
st.header("🌐 Configuración de Red e IPs")

c_net1, c_net2 = st.columns(2)
with c_net1: st.text_input("Net mask:", value="255.255.255.0", key="m_in")
with c_net2: st.text_input("Gateway:", value="192.168.30.1", key="g_in")

ws_red = conectar_hoja(client, "Red")

if ws_red:
    try:
        # Leemos todo como texto puro para evitar errores de formato
        vals_r = ws_red.get_all_values()
        
        if len(vals_r) > 0:
            df_r = pd.DataFrame(vals_r[1:], columns=vals_r[0])
            # Convertimos ESTADO a Booleano real para el checkbox de Streamlit
            df_r['ESTADO'] = df_r['ESTADO'].apply(lambda x: str(x).strip().upper() == 'TRUE')
        else:
            df_r = pd.DataFrame(columns=["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"])

        df_r_edit = st.data_editor(
            df_r,
            hide_index=True,
            use_container_width=True,
            column_config={
                "ESTADO": st.column_config.CheckboxColumn("Comunicando"),
                "DIRECCION IP": st.column_config.TextColumn("IP", required=True)
            }
        )
        
        if st.button("💾 Guardar Red"):
            # CONVERSIÓN CRÍTICA: Todo a String antes de enviar a Google
            df_to_save = df_r_edit.copy()
            df_to_save['ESTADO'] = df_to_save['ESTADO'].astype(str).str.upper()
            
            ws_red.clear()
            # Enviamos encabezados + datos convertidos a lista de listas
            datos_finales = [df_to_save.columns.values.tolist()] + df_to_save.values.tolist()
            ws_red.update(datos_finales)
            st.success("Red actualizada")
            st.rerun()

    except Exception as e:
        st.error(f"Error en sección Red: {e}")

    with st.expander("➕ Añadir Equipo"):
        with st.form("f_add_ip"):
            f1, f2, f3, f4 = st.columns(4)
            p, r, m, u = f1.text_input("Proveedor"), f2.text_input("Ref"), f3.text_input("Marca"), f4.text_input("Uso")
            ip = st.text_input("IP")
            if st.form_submit_button("Añadir"):
                if ip:
                    ws_red.append_row([p, r, m, u, ip, "FALSE"])
                    st.rerun()
