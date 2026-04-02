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
    except:
        return None

def conectar_hoja(client, nombre_pestaña):
    ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
    try:
        return client.open_by_key(ID_HOJA).worksheet(nombre_pestaña)
    except:
        return None

client = obtener_cliente_gspread()

# --- UTILIDADES SEGURAS PARA GUARDAR ---
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

def limpiar_df_para_sheet(df, date_cols=None, bool_cols=None):
    """
    Convierte el DataFrame a valores seguros para gspread:
    - fechas -> dd/mm/YYYY
    - booleanos -> TRUE/FALSE
    - vacíos/NaN -> ""
    - tipos raros -> texto simple
    """
    date_cols = set(date_cols or [])
    bool_cols = set(bool_cols or [])

    out = df.copy()

    for col in out.columns:
        if col in date_cols:
            out[col] = pd.to_datetime(out[col], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y")
        elif col in bool_cols:
            out[col] = out[col].apply(normalizar_bool)

    # Sustituye NaN/NaT por vacío y deja valores simples
    out = out.where(pd.notna(out), "")
    out = out.applymap(lambda x: "" if x is None else x)

    return out

def guardar_df_en_worksheet(ws, df, date_cols=None, bool_cols=None):
    """
    Limpia y escribe un DataFrame entero en una worksheet sin crashear por tipos.
    """
    if ws is None:
        raise ValueError("Worksheet no disponible")

    df_ok = limpiar_df_para_sheet(df, date_cols=date_cols, bool_cols=bool_cols)

    # Asegurar valores completamente serializables para gspread
    valores = [df_ok.columns.astype(str).tolist()]
    if not df_ok.empty:
        valores += df_ok.astype(object).values.tolist()

    ws.clear()
    ws.update(valores)

# --- LÓGICA DE CÁLCULO SEGURA ---
def calcular_avances():
    pct_hitos, pct_tareas, pct_red = 0.0, 0.0, 0.0
    
    # Hitos
    ws_hitos = conectar_hoja(client, "Hitos")
    if ws_hitos:
        v_h = ws_hitos.get_all_values()
        if len(v_h) > 1:
            df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
            if 'PORCENTAJE' in df_h.columns and 'PAGADO' in df_h.columns:
                df_h['val'] = pd.to_numeric(df_h['PORCENTAJE'].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
                pagados = df_h[df_h['PAGADO'].astype(str).str.upper() == 'TRUE']['val'].sum()
                total = df_h['val'].sum()
                if total > 0:
                    pct_hitos = float(pagados / total)
            
    # Tareas
    ws_tareas = conectar_hoja(client, "Tareas")
    if ws_tareas:
        data_t = ws_tareas.get_all_records()
        if data_t:
            df_t = pd.DataFrame(data_t)
            if 'Progress' in df_t.columns:
                pct_tareas = float(pd.to_numeric(df_t['Progress'], errors='coerce').fillna(0).mean() / 100)

    # Red
    ws_red = conectar_hoja(client, "Red")
    if ws_red:
        v_r = ws_red.get_all_values()
        if len(v_r) > 1:
            df_r = pd.DataFrame(v_r[1:], columns=v_r[0])
            if 'ESTADO' in df_r.columns:
                total_ips = len(df_r)
                online = len(df_r[df_r['ESTADO'].astype(str).str.upper() == 'TRUE'])
                if total_ips > 0:
                    pct_red = float(online / total_ips)
                
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

# --- 3. CRONOGRAMA (GANTT SEGURO) ---
st.header("📅 Cronograma de Obra")
ws_tareas = conectar_hoja(client, "Tareas")
if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')
        df_t['Level'] = pd.to_numeric(df_t['Level'], errors='coerce').fillna(0).astype(int)

        df_gantt = df_t.dropna(subset=['Start', 'End']).copy()
        df_gantt = df_gantt[df_gantt['End'] >= df_gantt['Start']]

        if not df_gantt.empty:
            prof = st.sidebar.slider("Detalle Gantt (Nivel)", 0, 2, 2)
            df_p = df_gantt[df_gantt['Level'] <= prof].copy()
            df_p['Display'] = df_p.apply(lambda x: "\xa0" * 6 * x['Level'] + str(x['Task']), axis=1)
            
            try:
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
            except:
                st.error("Error visual. Revisa las fechas en la tabla.")
        
        st.subheader("📝 Gestión de Tareas")
        df_t_edit = st.data_editor(
            df_t,
            hide_index=True,
            use_container_width=True,
            key="edit_t",
            column_config={
                "Start": st.column_config.DateColumn("Start", format="DD/MM/YYYY"),
                "End": st.column_config.DateColumn("End", format="DD/MM/YYYY")
            }
        )
        
        if st.button("💾 Sincronizar Tareas"):
            try:
                df_save = df_t_edit.copy()
                df_save['Start'] = pd.to_datetime(df_save['Start'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
                df_save['End'] = pd.to_datetime(df_save['End'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
                df_save = df_save.fillna("")

                guardar_df_en_worksheet(ws_tareas, df_save, date_cols=['Start', 'End'])
                st.success("¡Datos guardados con éxito!")
                st.rerun()
            except Exception as e:
                st.error(f"Error fatal al intentar guardar en Google Sheets: {e}")

        c1, c2 = st.columns(2)
        with c1:
            with st.expander("➕ Añadir Tarea"):
                with st.form("f_t"):
                    nt = st.text_input("Tarea")
                    ne = st.text_input("Empresa")
                    nl = st.selectbox("Nivel", [0, 1, 2])
                    if st.form_submit_button("Agregar"):
                        try:
                            nueva_fila = [
                                len(df_t),
                                nt,
                                nl,
                                0,
                                ne,
                                datetime.now().strftime('%d/%m/%Y'),
                                (datetime.now() + timedelta(days=5)).strftime('%d/%m/%Y')
                            ]
                            ws_tareas.append_row(nueva_fila)
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo añadir la tarea: {e}")
        with c2:
            with st.expander("🗑️ Eliminar Tarea"):
                t_b = st.selectbox("Tarea", ["---"] + df_t['Task'].tolist())
                if st.button("Confirmar Borrado") and t_b != "---":
                    try:
                        df_f = df_t[df_t['Task'] != t_b].copy()
                        df_f['id'] = range(len(df_f))
                        df_f['Start'] = pd.to_datetime(df_f['Start'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
                        df_f['End'] = pd.to_datetime(df_f['End'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
                        df_f = df_f.fillna("")
                        guardar_df_en_worksheet(ws_tareas, df_f, date_cols=['Start', 'End'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo borrar la tarea: {e}")

st.divider()

# --- 4. RED E IPs ---
st.header("🌐 Configuración de Red e IPs")
ws_red = conectar_hoja(client, "Red")
if ws_red:
    v_r = ws_red.get_all_values()
    df_r = pd.DataFrame(v_r[1:], columns=v_r[0]) if len(v_r) > 1 else pd.DataFrame(columns=["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"])
    if 'ESTADO' in df_r.columns:
        df_r['ESTADO'] = df_r['ESTADO'].astype(str).str.upper() == 'TRUE'

    df_r_ed = st.data_editor(
        df_r,
        hide_index=True,
        use_container_width=True,
        key="edit_r",
        column_config={"ESTADO": st.column_config.CheckboxColumn("Comunicando")}
    )
    
    if st.button("💾 Guardar Red"):
        try:
            df_r_ed = df_r_ed.copy()
            # Corregido: era .astype(str).upper() y eso rompe
            df_r_ed['ESTADO'] = df_r_ed['ESTADO'].apply(normalizar_bool)
            guardar_df_en_worksheet(ws_red, df_r_ed, bool_cols=['ESTADO'])
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo guardar la red: {e}")

    with st.expander("➕ Añadir IP"):
        with st.form("f_ip"):
            f1, f2, f3, f4, f5 = st.columns(5)
            p = f1.text_input("Prov")
            r = f2.text_input("Ref")
            m = f3.text_input("Marca")
            u = f4.text_input("Uso")
            ip = f5.text_input("IP")
            if st.form_submit_button("Añadir"):
                try:
                    ws_red.append_row([p, r, m, u, ip, "FALSE"])
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir la IP: {e}")

st.divider()

# --- 5. CREDENCIALES ---
st.header("🔑 Credenciales")
ws_creds = conectar_hoja(client, "Credenciales")
if ws_creds:
    v_c = ws_creds.get_all_values()
    df_c = pd.DataFrame(v_c[1:], columns=v_c[0]) if len(v_c) > 1 else pd.DataFrame(columns=["EMPRESA", "PLATAFORMA", "USUARIO", "CONTRASEÑA"])
    df_c_ed = st.data_editor(df_c, hide_index=True, use_container_width=True, key="edit_c")
    if st.button("💾 Guardar Credenciales"):
        try:
            guardar_df_en_worksheet(ws_creds, df_c_ed)
            st.rerun()
        except Exception as e:
            st.error(f"No se pudieron guardar las credenciales: {e}")
    with st.expander("➕ Añadir Credencial"):
        with st.form("f_c"):
            c1, c2, c3, c4 = st.columns(4)
            ce = c1.text_input("Empresa")
            cp = c2.text_input("Plat")
            cu = c3.text_input("User")
            cpw = c4.text_input("Pass")
            if st.form_submit_button("Añadir"):
                try:
                    ws_creds.append_row([ce, cp, cu, cpw])
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir la credencial: {e}")

st.divider()

# --- 6. HITOS DE PAGO ---
st.header("💰 Hitos de Pago (Payment Milestones)")
ws_hitos = conectar_hoja(client, "Hitos")
if ws_hitos:
    v_h = ws_hitos.get_all_values()
    if len(v_h) > 1:
        df_h = pd.DataFrame(v_h[1:], columns=v_h[0])
        df_h['PAGADO'] = df_h['PAGADO'].astype(str).str.upper() == 'TRUE'
    else:
        df_h = pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])

    t1, t2 = st.tabs(["🚢 Offshore", "🏗️ Onshore"])
    cfg_h = {
        "PAGADO": st.column_config.CheckboxColumn("Pagado"),
        "PORCENTAJE": st.column_config.TextColumn("Cuota %")
    }
    with t1:
        df_off = df_h[df_h["TIPO"] == "Offshore"].copy()
        ed_off = st.data_editor(
            df_off,
            hide_index=True,
            use_container_width=True,
            key="ed_off",
            column_order=("HITO", "PORCENTAJE", "PAGADO"),
            column_config=cfg_h
        )
    with t2:
        df_on = df_h[df_h["TIPO"] == "Onshore"].copy()
        ed_on = st.data_editor(
            df_on,
            hide_index=True,
            use_container_width=True,
            key="ed_on",
            column_order=("HITO", "PORCENTAJE", "PAGADO"),
            column_config=cfg_h
        )

    if st.button("💾 Guardar Hitos"):
        try:
            ed_off = ed_off.copy()
            ed_on = ed_on.copy()
            ed_off["TIPO"] = "Offshore"
            ed_on["TIPO"] = "Onshore"
            df_final = pd.concat([ed_off, ed_on], ignore_index=True)

            df_final['PAGADO'] = df_final['PAGADO'].apply(normalizar_bool)
            df_final = df_final.fillna("")

            guardar_df_en_worksheet(ws_hitos, df_final, bool_cols=['PAGADO'])
            st.rerun()
        except Exception as e:
            st.error(f"No se pudieron guardar los hitos: {e}")

    with st.expander("➕ Añadir Hito"):
        with st.form("f_h"):
            c1, c2, c3 = st.columns(3)
            ht = c1.selectbox("Tipo", ["Offshore", "Onshore"])
            hn = c2.text_input("Hito")
            hp = c3.text_input("%")
            if st.form_submit_button("Añadir"):
                try:
                    ws_hitos.append_row([ht, hn, hp, "FALSE"])
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir el hito: {e}")

st.divider()

# --- 7. SPARE PARTS (REPUESTOS) ---
st.header("📦 Spare Parts Inventory (Repuestos)")
ws_spare = conectar_hoja(client, "Repuestos")
if ws_spare:
    v_s = ws_spare.get_all_values()
    df_s = pd.DataFrame(v_s[1:], columns=v_s[0]) if len(v_s) > 1 else pd.DataFrame(columns=["CATEGORIA", "DESCRIPCION", "UNIDADES"])
    
    search = st.text_input("🔍 Buscar repuesto...", "")
    if search:
        df_show = df_s[df_s['DESCRIPCION'].astype(str).str.contains(search, case=False, na=False)]
    else:
        df_show = df_s
    
    df_s_ed = st.data_editor(df_show, hide_index=True, use_container_width=True, key="ed_spare")
    
    if st.button("💾 Guardar Inventario"):
        try:
            if search:
                # Mantiene tu lógica original, pero evita fallos por vacíos/tipos
                df_s.update(df_s_ed)
                df_to_save = df_s
            else:
                df_to_save = df_s_ed

            guardar_df_en_worksheet(ws_spare, df_to_save)
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo guardar el inventario: {e}")

    with st.expander("➕ Registrar Nuevo Repuesto"):
        with st.form("f_s"):
            c1, c2, c3 = st.columns([2, 3, 1])
            cat = c1.selectbox("Cat", ["PANELS", "LV/MV COMPONENTS", "INVERTERS", "STRUCTURE", "SECURITY", "MONITORING", "OTROS"])
            ds = c2.text_input("Descripción")
            un = c3.number_input("Und", min_value=1, value=1)
            if st.form_submit_button("Añadir"):
                try:
                    ws_spare.append_row([cat, ds, str(un)])
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir el repuesto: {e}")
