import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(layout="wide", page_title="Gestión Planta Solar Pro")

# --- GOOGLE SHEETS ---
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

# --- FUNCIONES ---
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

def calcular_avances():
    pct_hitos, pct_tareas, pct_red = 0.0, 0.0, 0.0

    ws_hitos = conectar_hoja(client, "Hitos")
    if ws_hitos:
        v = ws_hitos.get_all_values()
        if len(v) > 1:
            df = pd.DataFrame(v[1:], columns=v[0])
            df['val'] = pd.to_numeric(df['PORCENTAJE'].astype(str).str.replace('%',''), errors='coerce').fillna(0)
            pag = df[df['PAGADO'].astype(str).str.upper()=='TRUE']['val'].sum()
            tot = df['val'].sum()
            if tot > 0:
                pct_hitos = pag / tot

    ws_t = conectar_hoja(client, "Tareas")
    if ws_t:
        data = ws_t.get_all_records()
        if data:
            df = pd.DataFrame(data)
            if 'Progress' in df.columns:
                pct_tareas = pd.to_numeric(df['Progress'], errors='coerce').fillna(0).mean()/100

    ws_r = conectar_hoja(client, "Red")
    if ws_r:
        v = ws_r.get_all_values()
        if len(v) > 1:
            df = pd.DataFrame(v[1:], columns=v[0])
            total = len(df)
            ok = len(df[df['ESTADO'].astype(str).str.upper()=='TRUE'])
            if total > 0:
                pct_red = ok/total

    return pct_hitos, pct_tareas, pct_red

# --- CABECERA ---
st.title("☀️ Control Integral de Proyecto")

hitos_av, tareas_av, red_av = calcular_avances()

c1, c2, c3 = st.columns(3)
c1.metric("Payment Milestones", f"{hitos_av*100:.1f}%")
c1.progress(hitos_av)
c2.metric("Avance Obra", f"{tareas_av*100:.1f}%")
c2.progress(tareas_av)
c3.metric("Red", f"{red_av*100:.1f}%")
c3.progress(red_av)

st.divider()

# --- FICHA ---
with st.expander("📋 Ficha Técnica"):
    st.text_input("Proyecto", "Planta Solar X")

# --- GANTT ---
st.header("📅 Cronograma")

ws_tareas = conectar_hoja(client, "Tareas")

if ws_tareas:
    data = ws_tareas.get_all_records()
    if data:
        df = pd.DataFrame(data)

        df['Start'] = df['Start'].apply(parse_fecha)
        df['End'] = df['End'].apply(parse_fecha)
        df['Level'] = pd.to_numeric(df['Level'], errors='coerce').fillna(0).astype(int)

        df = recalcular_fechas_jerarquia(df)

        if df['Start'].isna().any() or df['End'].isna().any():
            st.warning("Fechas inválidas detectadas")
            st.dataframe(df[df['Start'].isna() | df['End'].isna()])

        df_g = df.dropna(subset=['Start','End'])
        df_g = df_g[df_g['End'] >= df_g['Start']]

        if not df_g.empty:
            df_g['Display'] = df_g.apply(lambda x: " "*6*x['Level'] + str(x['Task']), axis=1)

            base = alt.Chart(df_g).encode(y=alt.Y('id:O', axis=None))

            text = base.mark_text(align='left').encode(text='Display:N')
            bars = base.mark_bar().encode(
                x='Start:T', x2='End:T',
                color=alt.Color('Level:N', legend=None)
            )

            st.altair_chart(alt.hconcat(text, bars), use_container_width=True)

        # EDITOR
        df_edit = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "Start": st.column_config.DateColumn(),
                "End": st.column_config.DateColumn()
            }
        )

        if st.button("💾 Guardar Tareas"):
            df_s = df_edit.copy()
            df_s['Start'] = pd.to_datetime(df_s['Start'], errors='coerce')
            df_s['End'] = pd.to_datetime(df_s['End'], errors='coerce')

            df_s['Start'] = df_s['Start'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "")
            df_s['End'] = df_s['End'].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "")

            ws_tareas.clear()
            ws_tareas.update([df_s.columns.tolist()] + df_s.fillna("").values.tolist())
            st.rerun()

st.divider()

# --- RED ---
st.header("🌐 Red")

ws_red = conectar_hoja(client, "Red")
if ws_red:
    v = ws_red.get_all_values()
    df = pd.DataFrame(v[1:], columns=v[0]) if len(v)>1 else pd.DataFrame(columns=["IP","ESTADO"])

    df['ESTADO'] = df['ESTADO'].astype(str).str.upper()=="TRUE"

    df_ed = st.data_editor(df, use_container_width=True)

    if st.button("Guardar Red"):
        df_ed['ESTADO'] = df_ed['ESTADO'].astype(str).upper()
        ws_red.clear()
        ws_red.update([df_ed.columns.tolist()] + df_ed.values.tolist())
        st.rerun()

st.divider()

# --- CREDENCIALES ---
st.header("🔑 Credenciales")

ws_c = conectar_hoja(client, "Credenciales")
if ws_c:
    v = ws_c.get_all_values()
    df = pd.DataFrame(v[1:], columns=v[0]) if len(v)>1 else pd.DataFrame(columns=["EMPRESA","USER","PASS"])

    df_ed = st.data_editor(df, use_container_width=True)

    if st.button("Guardar Credenciales"):
        ws_c.clear()
        ws_c.update([df_ed.columns.tolist()] + df_ed.fillna("").values.tolist())
        st.rerun()

st.divider()

# --- HITOS ---
st.header("💰 Hitos")

ws_h = conectar_hoja(client, "Hitos")
if ws_h:
    v = ws_h.get_all_values()
    df = pd.DataFrame(v[1:], columns=v[0]) if len(v)>1 else pd.DataFrame(columns=["HITO","PORCENTAJE","PAGADO"])

    df['PAGADO'] = df['PAGADO'].astype(str).str.upper()=="TRUE"

    df_ed = st.data_editor(df, use_container_width=True)

    if st.button("Guardar Hitos"):
        df_ed['PAGADO'] = df_ed['PAGADO'].astype(str).upper()
        ws_h.clear()
        ws_h.update([df_ed.columns.tolist()] + df_ed.values.tolist())
        st.rerun()

st.divider()

# --- REPUESTOS ---
st.header("📦 Repuestos")

ws_s = conectar_hoja(client, "Repuestos")
if ws_s:
    v = ws_s.get_all_values()
    df = pd.DataFrame(v[1:], columns=v[0]) if len(v)>1 else pd.DataFrame(columns=["DESC","UND"])

    df_ed = st.data_editor(df, use_container_width=True)

    if st.button("Guardar Repuestos"):
        ws_s.clear()
        ws_s.update([df_ed.columns.tolist()] + df_ed.values.tolist())
        st.rerun()
