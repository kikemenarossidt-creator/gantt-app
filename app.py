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

    

    # Cálculo de Hitos

    ws_hitos = conectar_hoja(client, "Hitos")

    if ws_hitos:

        v_h = ws_hitos.get_all_values()

        if len(v_h) > 1:

            df_h = pd.DataFrame(v_h[1:], columns=v_h[0])

            df_h['val'] = df_h['PORCENTAJE'].str.replace('%', '').str.replace(',', '.').astype(float)

            pagados = df_h[df_h['PAGADO'].str.upper() == 'TRUE']['val'].sum()

            total = df_h['val'].sum()

            if total > 0: pct_hitos = (pagados / total)

            

    # Cálculo de Tareas

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


# --- 3. CRONOGRAMA (GANTT) ---
ws_tareas = conectar_hoja(client, "Tareas")

if ws_tareas:
    data_t = ws_tareas.get_all_records()
    if data_t:
        df_t = pd.DataFrame(data_t)

        # 1. Selector de nivel (ENCIMA del título)
        prof = st.radio(
            "🔍 Nivel de detalle del Cronograma:",
            options=[0, 1, 2],
            format_func=lambda x: ["Básico (Hitos)", "Intermedio", "Detallado (Todo)"][x],
            horizontal=True,
            key="selector_gantt_final"
        )

        st.header("📅 Cronograma de Obra")

        # --- LIMPIEZA INICIAL ---
        df_t['Level'] = pd.to_numeric(df_t['Level'], errors='coerce').fillna(0).astype(int)
        df_t['Start'] = pd.to_datetime(df_t['Start'], dayfirst=True, errors='coerce')
        df_t['End'] = pd.to_datetime(df_t['End'], dayfirst=True, errors='coerce')

        # Guardar copia original para la tabla/editor
        df_t_original = df_t.copy()

        # --- CÁLCULO AUTOMÁTICO DE FECHAS (Jerarquía Nivel 2 -> 1 -> 0) ---
        # Esto se calcula UNA vez sobre todo el dataframe
        df_calc = df_t.copy()

        # Creamos identificadores para saber a qué padre pertenece cada fila
        df_calc['L0_idx'] = pd.Series(df_calc.index, index=df_calc.index).where(df_calc['Level'] == 0).ffill()
        df_calc['L1_idx'] = pd.Series(df_calc.index, index=df_calc.index).where(df_calc['Level'] == 1).ffill()

        # 1. Calcular fechas del Nivel 1 en base a sus hijos Nivel 2
        l2_tasks = df_calc[df_calc['Level'] == 2]
        if not l2_tasks.empty:
            l1_start = l2_tasks.groupby('L1_idx')['Start'].min()
            l1_end = l2_tasks.groupby('L1_idx')['End'].max()
            for idx in l1_start.index:
                if pd.notna(idx):
                    df_calc.loc[idx, 'Start'] = l1_start[idx]
                    df_calc.loc[idx, 'End'] = l1_end[idx]

        # 2. Calcular fechas del Nivel 0 en base a todas las tareas por debajo de él
        children = df_calc[df_calc['Level'] > 0]
        if not children.empty:
            l0_start = children.groupby('L0_idx')['Start'].min()
            l0_end = children.groupby('L0_idx')['End'].max()
            for idx in l0_start.index:
                if pd.notna(idx):
                    df_calc.loc[idx, 'Start'] = l0_start[idx]
                    df_calc.loc[idx, 'End'] = l0_end[idx]

        # --- ELIMINAR SOLO PARA LA GRÁFICA LAS FILAS SIN FECHAS ---
        df_plot = df_calc.dropna(subset=['Start', 'End']).copy()

        # --- FILTRO SOLO VISUAL ---
        df_p = df_plot[df_plot['Level'] <= prof].copy()

        if not df_p.empty:
            # CLAVE: usar el índice original estable, no regenerarlo con range(len(df_p))
            df_p['plot_id'] = df_p.index.astype(str)

            # Formateo visual
            df_p['Display'] = df_p.apply(
                lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']),
                axis=1
            )

            h_dinamica = max(len(df_p) * 30, 150)

            # Mantener orden original de arriba hacia abajo
            orden_y = [str(i) for i in reversed(df_p.index.tolist())]

            # --- GRÁFICO ALTAIR ---
            base = alt.Chart(df_p).encode(
                y=alt.Y('plot_id:O', axis=None, sort=orden_y)
            )

            text_layer = alt.layer(
                base.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold', fontSize=13),
                base.transform_filter(alt.datum.Level == 1).mark_text(align='left', fontSize=12),
                base.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='gray')
            ).encode(
                text='Display:N'
            ).properties(width=350, height=h_dinamica)

            bars = base.mark_bar(cornerRadius=3).encode(
                x=alt.X('Start:T', axis=alt.Axis(format='%d/%m', title='Cronograma')),
                x2='End:T',
                color=alt.Color(
                    'Level:N',
                    scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip('Task:N', title='Tarea'),
                    alt.Tooltip('Start:T', title='Inicio', format='%d/%m/%Y'),
                    alt.Tooltip('End:T', title='Fin', format='%d/%m/%Y'),
                    alt.Tooltip('Empresa a Cargo:N', title='Responsable')
                ]
            ).properties(width=750, height=h_dinamica)

            st.altair_chart(
                alt.hconcat(text_layer, bars).resolve_scale(y='shared'),
                use_container_width=False
            )
        else:
            st.info("No hay tareas con fechas asignadas o subtareas configuradas para mostrar la gráfica.")

        # --- GESTIÓN DE TAREAS (DATA EDITOR) ---
        st.subheader("📝 Gestión de Tareas")

        df_t_show = df_t_original.copy()
        df_t_show['Start'] = pd.to_datetime(df_t_show['Start'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_t_show['End'] = pd.to_datetime(df_t_show['End'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_t_show['Start'] = df_t_show['Start'].fillna('')
        df_t_show['End'] = df_t_show['End'].fillna('')

        cols_to_drop = [c for c in ['L0_idx', 'L1_idx', 'plot_id', 'Display'] if c in df_t_show.columns]
        df_t_show = df_t_show.drop(columns=cols_to_drop)

        df_t_edit = st.data_editor(df_t_show, hide_index=True, use_container_width=True)

        if st.button("💾 Sincronizar Tareas"):
            ws_tareas.clear()
            ws_tareas.update([df_t_edit.columns.values.tolist()] + df_t_edit.values.tolist())
            st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            with st.expander("➕ Añadir Tarea"):
                with st.form("f_t"):
                    nt = st.text_input("Tarea")
                    ne = st.text_input("Empresa")
                    nl = st.selectbox("Nivel", [0, 1, 2])
                    if st.form_submit_button("Agregar"):
                        ws_tareas.append_row([len(df_t_original), nt, nl, 0, ne, "", ""])
                        st.rerun()

        with c2:
            with st.expander("🗑️ Eliminar Tarea"):
                t_b = st.selectbox("Tarea", ["---"] + df_t_original['Task'].tolist())
                if st.button("Confirmar Borrado"):
                    df_f = df_t_original[df_t_original['Task'] != t_b].copy()
                    df_f['id'] = range(len(df_f))
                    df_f['Start'] = pd.to_datetime(df_f['Start'], errors='coerce').dt.strftime('%d/%m/%Y')
                    df_f['End'] = pd.to_datetime(df_f['End'], errors='coerce').dt.strftime('%d/%m/%Y')
                    df_f['Start'] = df_f['Start'].fillna('')
                    df_f['End'] = df_f['End'].fillna('')

                    cols_to_drop_f = [c for c in ['L0_idx', 'L1_idx', 'plot_id', 'Display'] if c in df_f.columns]
                    df_f = df_f.drop(columns=cols_to_drop_f)

                    ws_tareas.clear()
                    ws_tareas.update([df_f.columns.values.tolist()] + df_f.values.tolist())
                    st.rerun()
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

    df_c_ed = st.data_editor(df_c, hide_index=True, use_container_width=True)

    if st.button("💾 Guardar Credenciales"):

        ws_creds.clear(); ws_creds.update([df_c_ed.columns.values.tolist()] + df_c_ed.values.tolist()); st.rerun()

    with st.expander("➕ Añadir Credencial"):

        with st.form("f_c"):

            c1, c2, c3, c4 = st.columns(4)

            ce = c1.text_input("Empresa"); cp = c2.text_input("Plat"); cu = c3.text_input("User"); cpw = c4.text_input("Pass")

            if st.form_submit_button("Añadir"): ws_creds.append_row([ce, cp, cu, cpw]); st.rerun()



st.divider()



# --- 6. HITOS DE PAGO ---

st.header("💰 Hitos de Pago (Payment Milestones)")

ws_hitos = conectar_hoja(client, "Hitos")

if ws_hitos:

    v_h = ws_hitos.get_all_values()

    if len(v_h) > 1:

        df_h = pd.DataFrame(v_h[1:], columns=v_h[0])

        df_h['PAGADO'] = df_h['PAGADO'].astype(str).str.upper() == 'TRUE'

    else: df_h = pd.DataFrame(columns=["TIPO", "HITO", "PORCENTAJE", "PAGADO"])



    t1, t2 = st.tabs(["🚢 Offshore", "🏗️ Onshore"])

    cfg_h = {"PAGADO": st.column_config.CheckboxColumn("Pagado"), "PORCENTAJE": st.column_config.TextColumn("Cuota %")}

    with t1:

        df_off = df_h[df_h["TIPO"] == "Offshore"].copy()

        ed_off = st.data_editor(df_off, hide_index=True, use_container_width=True, key="ed_off", column_order=("HITO", "PORCENTAJE", "PAGADO"), column_config=cfg_h)

    with t2:

        df_on = df_h[df_h["TIPO"] == "Onshore"].copy()

        ed_on = st.data_editor(df_on, hide_index=True, use_container_width=True, key="ed_on", column_order=("HITO", "PORCENTAJE", "PAGADO"), column_config=cfg_h)



    if st.button("💾 Guardar Hitos"):

        ed_off["TIPO"] = "Offshore"; ed_on["TIPO"] = "Onshore"; df_final = pd.concat([ed_off, ed_on])

        df_final['PAGADO'] = df_final['PAGADO'].astype(str).str.upper()

        ws_hitos.clear(); ws_hitos.update([df_final.columns.values.tolist()] + df_final.values.tolist()); st.rerun()

    with st.expander("➕ Añadir Hito"):

        with st.form("f_h"):

            c1, c2, c3 = st.columns(3)

            ht = c1.selectbox("Tipo", ["Offshore", "Onshore"]); hn = c2.text_input("Hito"); hp = c3.text_input("%")

            if st.form_submit_button("Añadir"): ws_hitos.append_row([ht, hn, hp, "FALSE"]); st.rerun()



st.divider()



# --- 7. SPARE PARTS (REPUESTOS) ---

st.header("📦 Spare Parts Inventory (Repuestos)")

ws_spare = conectar_hoja(client, "Repuestos")

if ws_spare:

    v_s = ws_spare.get_all_values()

    df_s = pd.DataFrame(v_s[1:], columns=v_s[0]) if len(v_s) > 1 else pd.DataFrame(columns=["CATEGORIA", "DESCRIPCION", "UNIDADES"])

    

    search = st.text_input("🔍 Buscar repuesto...", "")

    df_show = df_s[df_s['DESCRIPCION'].str.contains(search, case=False)] if search else df_s

    

    df_s_ed = st.data_editor(df_show, hide_index=True, use_container_width=True, key="ed_spare")

    

    if st.button("💾 Guardar Inventario"):

        if search: df_s.update(df_s_ed); df_to_save = df_s

        else: df_to_save = df_s_ed

        ws_spare.clear(); ws_spare.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist()); st.rerun()



    with st.expander("➕ Registrar Nuevo Repuesto"):

        with st.form("f_s"):

            c1, c2, c3 = st.columns([2, 3, 1])

            cat = c1.selectbox("Cat", ["PANELS", "LV/MV COMPONENTS", "INVERTERS", "STRUCTURE", "SECURITY", "MONITORING", "OTROS"])

            ds = c2.text_input("Descripción"); un = c3.number_input("Und", min_value=1, value=1)

            if st.form_submit_button("Añadir"): ws_spare.append_row([cat, ds, str(un)]); st.rerun()
