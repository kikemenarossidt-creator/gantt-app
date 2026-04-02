import streamlit as st
import pandas as pd
import altair as alt
import gspread
from google.oauth2.service_account import Credentials

# Configuración de página
st.set_page_config(page_title="Control de Proyecto", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# 🔑 CONEXIÓN Y FUNCIONES BASE
# ─────────────────────────────────────────────────────────────────────────────

def conectar_google_sheets():
    """Establece la conexión con la API de Google Sheets."""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["spreadsheet_id"])

def leer_hoja(nombre_hoja, columnas_esperadas):
    """Lee una pestaña y asegura que tenga las columnas mínimas."""
    try:
        sh = conectar_google_sheets()
        ws = sh.worksheet(nombre_hoja)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            df = pd.DataFrame(columns=columnas_esperadas)
        
        # Limpieza de nombres de columnas (quitar espacios en blanco)
        df.columns = [c.strip() for c in df.columns]
        return ws, df
    except Exception as e:
        st.error(f"Error leyendo '{nombre_hoja}': {e}")
        return None, pd.DataFrame(columns=columnas_esperadas)

def guardar_en_sheet(ws, df, date_cols=None, bool_cols=None):
    """Guarda el DataFrame de vuelta a la hoja de cálculo."""
    if ws is None: return
    
    df_save = df.copy()
    # Convertir fechas a string para Google Sheets
    if date_cols:
        for col in date_cols:
            if col in df_save.columns:
                df_save[col] = df_save[col].dt.strftime('%d/%m/%Y').replace('NaT', '')
    
    # Convertir booleanos a string
    if bool_cols:
        for col in bool_cols:
            if col in df_save.columns:
                df_save[col] = df_save[col].astype(str).str.upper()

    ws.clear()
    ws.update([df_save.columns.values.tolist()] + df_save.values.tolist())

# ─────────────────────────────────────────────────────────────────────────────
# 📦 CARGA DE DATOS CENTRALIZADA (TTL de 10 min para evitar error 429)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner="Sincronizando con Google Sheets...")
def cargar_todo():
    """Carga todas las hojas en una sola llamada masiva."""
    _, df_h = leer_hoja("Hitos", ["TIPO", "HITO", "PORCENTAJE", "PAGADO"])
    _, df_t = leer_hoja("Tareas", ["id", "Task", "Level", "Progress", "Empresa a Cargo", "Start", "End"])
    _, df_r = leer_hoja("Red", ["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"])
    _, df_c = leer_hoja("Credenciales", ["EMPRESA", "PLATAFORMA", "USUARIO", "CONTRASEÑA"])
    _, df_s = leer_hoja("Repuestos", ["CATEGORIA", "DESCRIPCION", "UNIDADES"])
    return df_h, df_t, df_r, df_c, df_s

# ═══════════════════════════════════════════════
# APLICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════

# Botón lateral para forzar refresco
if st.sidebar.button("🔄 Refrescar Datos"):
    st.cache_data.clear()
    st.rerun()

# Cargar DataFrames iniciales
df_h_raw, df_t_raw, df_r_raw, df_c_raw, df_s_raw = cargar_todo()

st.title("☀️ Control Integral de Proyecto")

# --- DASHBOARD DE AVANCES ---
col1, col2, col3 = st.columns(3)

with col1:
    h_val = pd.to_numeric(df_h_raw["PORCENTAJE"].astype(str).str.replace("%",""), errors="coerce").fillna(0)
    h_pag = df_h_raw["PAGADO"].astype(str).str.upper() == "TRUE"
    h_prog = float(h_val[h_pag].sum() / h_val.sum()) if h_val.sum() > 0 else 0.0
    st.metric("Hitos de Pago", f"{h_prog*100:.1f}%")
    st.progress(min(max(h_prog, 0.0), 1.0))

with col2:
    t_prog = pd.to_numeric(df_t_raw["Progress"], errors="coerce").fillna(0).mean() / 100
    st.metric("Avance Obra (Gantt)", f"{t_prog*100:.1f}%")
    st.progress(min(max(t_prog, 0.0), 1.0))

with col3:
    r_total = len(df_r_raw)
    r_on = (df_r_raw["ESTADO"].astype(str).str.upper() == "TRUE").sum()
    r_prog = float(r_on / r_total) if r_total > 0 else 0.0
    st.metric("Equipos Online", f"{r_prog*100:.1f}%")
    st.progress(min(max(r_prog, 0.0), 1.0))

st.divider()

# ─────────────────────────────────────────────
# 📅 SECCIÓN 1: CRONOGRAMA (GANTT)
# ─────────────────────────────────────────────
st.header("📅 Cronograma de Obra")

df_t = df_t_raw.copy()
if not df_t.empty:
    # Preparar fechas y niveles
    df_t["Start"] = pd.to_datetime(df_t["Start"], dayfirst=True, errors="coerce")
    df_t["End"] = pd.to_datetime(df_t["End"], dayfirst=True, errors="coerce")
    df_t["Level"] = pd.to_numeric(df_t["Level"], errors="coerce").fillna(0).astype(int)
    
    # Gráfica Gantt
    df_gantt = df_t.dropna(subset=["Start", "End"])
    df_gantt = df_gantt[df_gantt["End"] >= df_gantt["Start"]]

    if not df_gantt.empty:
        prof = st.sidebar.slider("Detalle Gantt (Nivel)", 0, 2, 2)
        df_p = df_gantt[df_gantt["Level"] <= prof].copy()
        df_p["Display"] = df_p.apply(lambda x: " " * 6 * int(x["Level"]) + str(x["Task"]), axis=1)
        df_p = df_p.reset_index(drop=True)
        df_p["idx"] = df_p.index

        h_chart = max(len(df_p) * 30, 150)
        base = alt.Chart(df_p).encode(y=alt.Y("idx:O", axis=None, sort="ascending"))
        
        text = base.mark_text(align="left", fontSize=13).encode(text="Display:N").properties(width=300, height=h_chart)
        bars = base.mark_bar(cornerRadius=3).encode(
            x=alt.X("Start:T", title="Fecha"), x2="End:T",
            color=alt.Color("Level:N", scale=alt.Scale(range=["#1a5276", "#3498db", "#aed6f1"]), legend=None),
            tooltip=["Task", "Empresa a Cargo", "Progress"]
        ).properties(width=800, height=h_chart)
        
        st.altair_chart(alt.hconcat(text, bars), use_container_width=True)
    else:
        st.info("💡 Introduce tareas con fechas válidas para activar la visualización.")

    # Editor de Tareas Dinámico
    st.subheader("📝 Gestión de Tareas")
    df_t_edit = st.data_editor(
        df_t, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "id": st.column_config.Column(disabled=True),
            "Level": st.column_config.SelectboxColumn("Nivel", options=[0, 1, 2]),
            "Progress": st.column_config.NumberColumn("Progreso %", min_value=0, max_value=100),
            "Start": st.column_config.DateColumn("Inicio", format="DD/MM/YYYY"),
            "End": st.column_config.DateColumn("Fin", format="DD/MM/YYYY")
        }
    )
    if st.button("💾 Guardar Cambios en Cronograma"):
        ws = conectar_google_sheets().worksheet("Tareas")
        df_t_edit["id"] = range(len(df_t_edit))
        guardar_en_sheet(ws, df_t_edit, date_cols=["Start", "End"])
        st.cache_data.clear()
        st.success("¡Tareas actualizadas!")
        st.rerun()

st.divider()

# ─────────────────────────────────────────────
# 🌐 SECCIÓN 2: RED E IPs
# ─────────────────────────────────────────────
st.header("🌐 Configuración de Red")
df_r = df_r_raw.copy()
if "ESTADO" in df_r.columns:
    df_r["ESTADO"] = df_r["ESTADO"].astype(str).str.upper() == "TRUE"

df_r_ed = st.data_editor(df_r, num_rows="dynamic", use_container_width=True, hide_index=True,
                         column_config={"ESTADO": st.column_config.CheckboxColumn("Online")})

if st.button("💾 Guardar Configuración de Red"):
    ws = conectar_google_sheets().worksheet("Red")
    guardar_en_sheet(ws, df_r_ed, bool_cols=["ESTADO"])
    st.cache_data.clear()
    st.success("Red actualizada.")
    st.rerun()

st.divider()

# ─────────────────────────────────────────────
# 💰 SECCIÓN 3: HITOS DE PAGO
# ─────────────────────────────────────────────
st.header("💰 Hitos de Pago")
df_h = df_h_raw.copy()
if "PAGADO" in df_h.columns:
    df_h["PAGADO"] = df_h["PAGADO"].astype(str).str.upper() == "TRUE"

t1, t2 = st.tabs(["🚢 Offshore", "🏗️ Onshore"])
with t1:
    ed_off = st.data_editor(df_h[df_h["TIPO"] == "Offshore"], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_off")
with t2:
    ed_on = st.data_editor(df_h[df_h["TIPO"] == "Onshore"], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_on")

if st.button("💾 Guardar Hitos de Pago"):
    ws = conectar_google_sheets().worksheet("Hitos")
    df_final_h = pd.concat([ed_off, ed_on])
    guardar_en_sheet(ws, df_final_h, bool_cols=["PAGADO"])
    st.cache_data.clear()
    st.success("Hitos guardados.")
    st.rerun()

st.divider()

# ─────────────────────────────────────────────
# 📦 SECCIÓN 4: REPUESTOS Y CREDENCIALES
# ─────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.header("📦 Repuestos")
    df_s_ed = st.data_editor(df_s_raw, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Guardar Repuestos"):
        ws = conectar_google_sheets().worksheet("Repuestos")
        guardar_en_sheet(ws, df_s_ed)
        st.cache_data.clear()
        st.rerun()

with col_b:
    st.header("🔑 Credenciales")
    df_c_ed = st.data_editor(df_c_raw, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Guardar Credenciales"):
        ws = conectar_google_sheets().worksheet("Credenciales")
        guardar_en_sheet(ws, df_c_ed)
        st.cache_data.clear()
        st.rerun()
