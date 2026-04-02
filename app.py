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

# --- FUNCIONES SEGURAS ---
def parse_fecha(x):
    try:
        if pd.isna(x) or x == "":
            return pd.NaT
        return pd.to_datetime(x, dayfirst=True)
    except:
        return pd.NaT

# --- CABECERA ---
st.title("☀️ Control Integral de Proyecto")

# --- CRONOGRAMA (GANTT ROBUSTO) ---
st.header("📅 Cronograma de Obra")

ws_tareas = conectar_hoja(client, "Tareas")

if ws_tareas:
    data_t = ws_tareas.get_all_records()

    if data_t:
        df_t = pd.DataFrame(data_t)

        # --- PARSEO ROBUSTO ---
        df_t['Start'] = df_t['Start'].apply(parse_fecha)
        df_t['End'] = df_t['End'].apply(parse_fecha)
        df_t['Level'] = pd.to_numeric(df_t['Level'], errors='coerce').fillna(0).astype(int)

        # --- DEBUG ---
        if df_t['Start'].isna().any() or df_t['End'].isna().any():
            st.warning("⚠️ Hay fechas inválidas. Revisa estas filas:")
            st.dataframe(df_t[df_t['Start'].isna() | df_t['End'].isna()])

        # --- FILTRO GANTT ---
        df_gantt = df_t.dropna(subset=['Start', 'End']).copy()
        df_gantt = df_gantt[df_gantt['End'] >= df_gantt['Start']]

        if df_gantt.empty:
            st.error("❌ No hay tareas válidas para mostrar (fechas incorrectas).")
        else:
            prof = st.sidebar.slider("Detalle Gantt (Nivel)", 0, 2, 2)

            df_p = df_gantt[df_gantt['Level'] <= prof].copy()

            df_p['Display'] = df_p.apply(
                lambda x: " " * 6 * x['Level'] + str(x['Task']),
                axis=1
            )

            h = max(len(df_p) * 25, 200)

            base = alt.Chart(df_p).encode(
                y=alt.Y('id:O', axis=None, sort='ascending')
            )

            text_layer = alt.layer(
                base.transform_filter(alt.datum.Level == 0)
                    .mark_text(align='left', fontWeight='bold', fontSize=13),

                base.transform_filter(alt.datum.Level == 1)
                    .mark_text(align='left', fontSize=12),

                base.transform_filter(alt.datum.Level == 2)
                    .mark_text(align='left', fontStyle='italic', color='gray')
            ).encode(
                text='Display:N'
            ).properties(width=350, height=h)

            bars = base.mark_bar(cornerRadius=3).encode(
                x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
                x2='End:T',
                color=alt.Color(
                    'Level:N',
                    scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']),
                    legend=None
                ),
                tooltip=['Task', 'Empresa a Cargo']
            ).properties(width=750, height=h)

            st.altair_chart(alt.hconcat(text_layer, bars), use_container_width=True)

        # --- EDITOR ---
        st.subheader("📝 Gestión de Tareas")

        df_t_edit = st.data_editor(
            df_t,
            hide_index=True,
            use_container_width=True,
            key="edit_t",
            column_config={
                "Start": st.column_config.DateColumn("Start"),
                "End": st.column_config.DateColumn("End")
            }
        )

        # --- GUARDAR ---
        if st.button("💾 Sincronizar Tareas"):
            try:
                df_save = df_t_edit.copy()

                df_save['Start'] = pd.to_datetime(df_save['Start'], errors='coerce')
                df_save['End'] = pd.to_datetime(df_save['End'], errors='coerce')

                df_save['Start'] = df_save['Start'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
                )
                df_save['End'] = df_save['End'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
                )

                df_save = df_save.fillna("")

                ws_tareas.clear()
                ws_tareas.update([df_save.columns.values.tolist()] + df_save.values.tolist())

                st.success("¡Datos guardados con éxito!")
                st.rerun()

            except Exception as e:
                st.error(f"Error al guardar: {e}")

        # --- AÑADIR ---
        with st.expander("➕ Añadir Tarea"):
            with st.form("f_t"):
                nt = st.text_input("Tarea")
                ne = st.text_input("Empresa")
                nl = st.selectbox("Nivel", [0, 1, 2])

                if st.form_submit_button("Agregar"):
                    ws_tareas.append_row([
                        len(df_t),
                        nt,
                        nl,
                        0,
                        ne,
                        datetime.now().strftime('%d/%m/%Y'),
                        (datetime.now() + timedelta(days=5)).strftime('%d/%m/%Y')
                    ])
                    st.rerun()

        # --- BORRAR ---
        with st.expander("🗑️ Eliminar Tarea"):
            t_b = st.selectbox("Tarea", ["---"] + df_t['Task'].tolist())

            if st.button("Confirmar Borrado") and t_b != "---":
                df_f = df_t[df_t['Task'] != t_b].copy()
                df_f['id'] = range(len(df_f))

                df_f['Start'] = df_f['Start'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
                )
                df_f['End'] = df_f['End'].apply(
                    lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ""
                )

                ws_tareas.clear()
                ws_tareas.update([df_f.columns.values.tolist()] + df_f.fillna("").values.tolist())

                st.rerun()
