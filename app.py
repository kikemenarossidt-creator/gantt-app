import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Gestión Planta Solar Pro")

ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"

# ─────────────────────────────────────────────
# CONEXIÓN A GOOGLE SHEETS
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def obtener_cliente_gspread():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de autenticación con Google: {e}")
        return None

def conectar_hoja(nombre_pestaña: str):
    """Devuelve el worksheet o None si falla."""
    c = obtener_cliente_gspread()
    if c is None:
        return None
    try:
        return c.open_by_key(ID_HOJA).worksheet(nombre_pestaña)
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Pestaña '{nombre_pestaña}' no encontrada.")
        return None
    except Exception as e:
        st.warning(f"No se pudo conectar a '{nombre_pestaña}': {e}")
        return None

# ─────────────────────────────────────────────
# UTILIDADES DE LIMPIEZA Y GUARDADO
# ─────────────────────────────────────────────
def normalizar_bool(valor) -> str:
    """Convierte cualquier representación booleana a 'TRUE'/'FALSE'."""
    try:
        if pd.isna(valor):
            return "FALSE"
    except Exception:
        pass
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    return "TRUE" if str(valor).strip().upper() in ("TRUE", "1", "SI", "S", "YES", "Y") else "FALSE"

def limpiar_df_para_sheet(df: pd.DataFrame, date_cols=None, bool_cols=None) -> list:
    """
    Devuelve lista de listas lista para escribir en gspread.
    Convierte fechas, bools y limpia nulos de forma segura.
    """
    date_cols = set(date_cols or [])
    bool_cols = set(bool_cols or [])
    out = df.copy()

    for col in out.columns:
        if col in date_cols:
            out[col] = pd.to_datetime(out[col], errors="coerce", dayfirst=True).dt.strftime("%d/%m/%Y").fillna("")
        elif col in bool_cols:
            out[col] = out[col].apply(normalizar_bool)

    # Convertir todo a string y asegurar que no queden textos de nulos
    out = out.fillna("")
    out = out.astype(str).replace({"nan": "", "NaT": "", "None": "", "NaN": "", "<NA>": ""})

    header = out.columns.tolist()
    rows = out.values.tolist()
    return [header] + rows

def guardar_en_sheet(ws, df: pd.DataFrame, date_cols=None, bool_cols=None):
    """Escribe el DataFrame completo en el worksheet asegurando compatibilidad con gspread."""
    if ws is None:
        raise ValueError("Worksheet no disponible.")
    
    values = limpiar_df_para_sheet(df, date_cols=date_cols, bool_cols=bool_cols)
    n_rows = max(len(values), 1)
    n_cols = max(len(values[0]), 1) if values else 1
    
    ws.clear()
    ws.resize(rows=n_rows, cols=n_cols)
    
    # Manejo de compatibilidad para diferentes versiones de gspread
    try:
        ws.update(range_name="A1", values=values)
    except TypeError:
        try:
            ws.update("A1", values)
        except Exception:
            ws.update(values, "A1")

def leer_hoja(nombre_pestaña: str, columnas_default: list) -> tuple:
    """Devuelve (ws, df). Si la hoja no existe o está vacía devuelve (None, df_vacío)."""
    ws = conectar_hoja(nombre_pestaña)
    if ws is None:
        return None, pd.DataFrame(columns=columnas_default)
    try:
        values = ws.get_all_values()
    except Exception as e:
        st.warning(f"Error leyendo '{nombre_pestaña}': {e}")
        return ws, pd.DataFrame(columns=columnas_default)

    if len(values) < 2:
        return ws, pd.DataFrame(columns=columnas_default if not values else values[0])

    df = pd.DataFrame(values[1:], columns=values[0])
    return ws, df

# ─────────────────────────────────────────────
# CÁLCULO DE AVANCES
# ─────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def calcular_avances():
    pct_hitos = pct_tareas = pct_red = 0.0

    # Hitos
    _, df_h = leer_hoja("Hitos", ["TIPO", "HITO", "PORCENTAJE", "PAGADO"])
    if not df_h.empty and {"PORCENTAJE", "PAGADO"}.issubset(df_h.columns):
        df_h["_val"] = pd.to_numeric(
            df_h["PORCENTAJE"].str.replace("%", "", regex=False).str.replace(",", ".", regex=False),
            errors="coerce",
        ).fillna(0)
        total = df_h["_val"].sum()
        pagados = df_h[df_h["PAGADO"].astype(str).str.upper() == "TRUE"]["_val"].sum()
        if total > 0:
            pct_hitos = float(pagados / total)

    # Tareas
    _, df_t = leer_hoja("Tareas", ["id", "Task", "Level", "Progress", "Empresa a Cargo", "Start", "End"])
    if not df_t.empty and "Progress" in df_t.columns:
        pct_tareas = float(pd.to_numeric(df_t["Progress"], errors="coerce").fillna(0).mean() / 100)

    # Red
    _, df_r = leer_hoja("Red", ["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"])
    if not df_r.empty and "ESTADO" in df_r.columns:
        total_ips = len(df_r)
        online = (df_r["ESTADO"].astype(str).str.upper() == "TRUE").sum()
        if total_ips > 0:
            pct_red = float(online / total_ips)

    return pct_hitos, pct_tareas, pct_red

# ═══════════════════════════════════════════════
# INICIO DE LA APP
# ═══════════════════════════════════════════════
st.title("☀️ Control Integral de Proyecto")

hitos_av, tareas_av, red_av = calcular_avances()

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.write(f"**Payment Milestones: {hitos_av*100:.1f}%**")
    st.progress(float(min(max(hitos_av, 0.0), 1.0)))
with col_v2:
    st.write(f"**Avance Obra: {tareas_av*100:.1f}%**")
    st.progress(float(min(max(tareas_av, 0.0), 1.0)))
with col_v3:
    st.write(f"**Configuración Red: {red_av*100:.1f}%**")
    st.progress(float(min(max(red_av, 0.0), 1.0)))

st.divider()

# ─────────────────────────────────────────────
# FICHA TÉCNICA
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# CRONOGRAMA / GANTT
# ─────────────────────────────────────────────
st.header("📅 Cronograma de Obra")

COLS_TAREAS = ["id", "Task", "Level", "Progress", "Empresa a Cargo", "Start", "End"]
ws_tareas, df_t = leer_hoja("Tareas", COLS_TAREAS)

if not df_t.empty:
    df_t["Start"] = pd.to_datetime(df_t["Start"], dayfirst=True, errors="coerce")
    df_t["End"] = pd.to_datetime(df_t["End"], dayfirst=True, errors="coerce")
    df_t["Level"] = pd.to_numeric(df_t["Level"], errors="coerce").fillna(0).astype(int)
    df_t["Progress"] = pd.to_numeric(df_t["Progress"], errors="coerce").fillna(0)

    df_gantt = df_t.dropna(subset=["Start", "End"])
    df_gantt = df_gantt[df_gantt["End"] >= df_gantt["Start"]].copy()

    if not df_gantt.empty:
        prof = st.sidebar.slider("Detalle Gantt (Nivel)", 0, 2, 2)
        df_p = df_gantt[df_gantt["Level"] <= prof].copy()
        df_p["Display"] = df_p.apply(lambda x: "\xa0" * 6 * int(x["Level"]) + str(x["Task"]), axis=1)
        df_p = df_p.reset_index(drop=True)
        df_p["id"] = df_p.index

        try:
            h = max(len(df_p) * 25, 200)
            base = alt.Chart(df_p).encode(y=alt.Y("id:O", axis=None, sort="ascending"))
            text_layer = alt.layer(
                base.transform_filter(alt.datum.Level == 0).mark_text(align="left", fontWeight="bold", fontSize=13),
                base.transform_filter(alt.datum.Level == 1).mark_text(align="left", fontSize=12),
                base.transform_filter(alt.datum.Level == 2).mark_text(align="left", fontStyle="italic", color="gray"),
            ).encode(text="Display:N").properties(width=350, height=h)

            bars = base.mark_bar(cornerRadius=3).encode(
                x=alt.X("Start:T", axis=alt.Axis(format="%d/%m")),
                x2="End:T",
                color=alt.Color("Level:N", scale=alt.Scale(range=["#1a5276", "#3498db", "#aed6f1"]), legend=None),
                tooltip=["Task", "Empresa a Cargo", "Progress"],
            ).properties(width=750, height=h)

            st.altair_chart(alt.hconcat(text_layer, bars))
        except Exception as e:
            st.error(f"Error al renderizar Gantt: {e}")

    # ── Editor de tareas ──
    st.subheader("📝 Gestión de Tareas")
    df_t_edit = st.data_editor(
        df_t,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="edit_t",
        column_config={
            "id": st.column_config.Column(disabled=True),
            "Start": st.column_config.DateColumn("Start", format="DD/MM/YYYY"),
            "End": st.column_config.DateColumn("End", format="DD/MM/YYYY"),
            "Progress": st.column_config.NumberColumn("Progress", min_value=0, max_value=100),
            "Level": st.column_config.NumberColumn("Level", min_value=0, max_value=2),
        },
    )

    if st.button("💾 Sincronizar Tareas"):
        if ws_tareas is None:
            st.error("No hay conexión con la hoja de Tareas.")
        else:
            try:
                # Recalcular IDs en caso de filas borradas/añadidas
                df_t_edit = df_t_edit.reset_index(drop=True)
                df_t_edit["id"] = df_t_edit.index
                guardar_en_sheet(ws_tareas, df_t_edit, date_cols=["Start", "End"])
                st.cache_data.clear()
                st.success("✅ Tareas guardadas correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar Tareas: {type(e).__name__} — {e}")

    c1, c2 = st.columns(2)
    with c1:
        with st.expander("➕ Añadir Tarea Rápida"):
            with st.form("f_t", clear_on_submit=True):
                nt = st.text_input("Tarea")
                ne = st.text_input("Empresa a Cargo")
                nl = st.selectbox("Nivel", [0, 1, 2])
                np_ = st.number_input("Progreso (%)", 0, 100, 0)
                ns = st.date_input("Inicio", datetime.today())
                nend = st.date_input("Fin", datetime.today() + timedelta(days=5))
                if st.form_submit_button("Agregar") and nt:
                    if ws_tareas is None:
                        st.error("Sin conexión.")
                    else:
                        try:
                            nuevo_id = len(df_t)
                            ws_tareas.append_row([
                                str(nuevo_id), nt, str(nl), str(np_), ne,
                                ns.strftime("%d/%m/%Y"), nend.strftime("%d/%m/%Y"),
                            ])
                            st.cache_data.clear()
                            st.success("Tarea añadida.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo añadir: {type(e).__name__} — {e}")

    with c2:
        with st.expander("🗑️ Eliminar Tarea"):
            opciones_tareas = df_t["Task"].dropna().tolist()
            t_b = st.selectbox("Tarea a eliminar", ["---"] + opciones_tareas)
            if st.button("Confirmar Borrado") and t_b != "---":
                if ws_tareas is None:
                    st.error("Sin conexión.")
                else:
                    try:
                        df_f = df_t[df_t["Task"] != t_b].copy().reset_index(drop=True)
                        df_f["id"] = df_f.index
                        guardar_en_sheet(ws_tareas, df_f, date_cols=["Start", "End"])
                        st.cache_data.clear()
                        st.success(f"Tarea '{t_b}' eliminada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo borrar: {type(e).__name__} — {e}")

elif ws_tareas is not None:
    st.info("La hoja 'Tareas' está vacía.")

st.divider()

# ─────────────────────────────────────────────
# RED E IPs
# ─────────────────────────────────────────────
st.header("🌐 Configuración de Red e IPs")

COLS_RED = ["PROVEEDOR", "REFERENCIA", "MARCA", "USO", "DIRECCION IP", "ESTADO"]
ws_red, df_r = leer_hoja("Red", COLS_RED)

if "ESTADO" in df_r.columns:
    df_r["ESTADO"] = df_r["ESTADO"].astype(str).str.upper() == "TRUE"

df_r_ed = st.data_editor(
    df_r,
    hide_index=True,
    num_rows="dynamic",
    use_container_width=True,
    key="edit_r",
    column_config={"ESTADO": st.column_config.CheckboxColumn("Comunicando")},
)

if st.button("💾 Guardar Red"):
    if ws_red is None:
        st.error("Sin conexión con la hoja Red.")
    else:
        try:
            df_save = df_r_ed.copy()
            guardar_en_sheet(ws_red, df_save, bool_cols=["ESTADO"])
            st.cache_data.clear()
            st.success("✅ Red guardada.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar Red: {type(e).__name__} — {e}")

with st.expander("➕ Añadir IP"):
    with st.form("f_ip", clear_on_submit=True):
        f1, f2, f3, f4, f5 = st.columns(5)
        p = f1.text_input("Proveedor")
        r = f2.text_input("Referencia")
        m = f3.text_input("Marca")
        u = f4.text_input("Uso")
        ip = f5.text_input("IP")
        if st.form_submit_button("Añadir") and ip:
            if ws_red is None:
                st.error("Sin conexión.")
            else:
                try:
                    ws_red.append_row([p, r, m, u, ip, "FALSE"])
                    st.cache_data.clear()
                    st.success("IP añadida.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir: {type(e).__name__} — {e}")

st.divider()

# ─────────────────────────────────────────────
# CREDENCIALES
# ─────────────────────────────────────────────
st.header("🔑 Credenciales")

COLS_CREDS = ["EMPRESA", "PLATAFORMA", "USUARIO", "CONTRASEÑA"]
ws_creds, df_c = leer_hoja("Credenciales", COLS_CREDS)

df_c_ed = st.data_editor(
    df_c,
    hide_index=True,
    num_rows="dynamic",
    use_container_width=True,
    key="edit_c",
    column_config={
        "CONTRASEÑA": st.column_config.TextColumn("CONTRASEÑA", help="Visible sólo en esta app")
    },
)

if st.button("💾 Guardar Credenciales"):
    if ws_creds is None:
        st.error("Sin conexión con la hoja Credenciales.")
    else:
        try:
            guardar_en_sheet(ws_creds, df_c_ed)
            st.success("✅ Credenciales guardadas.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {type(e).__name__} — {e}")

with st.expander("➕ Añadir Credencial"):
    with st.form("f_c", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        ce = c1.text_input("Empresa")
        cp = c2.text_input("Plataforma")
        cu = c3.text_input("Usuario")
        cpw = c4.text_input("Contraseña", type="password")
        if st.form_submit_button("Añadir") and ce:
            if ws_creds is None:
                st.error("Sin conexión.")
            else:
                try:
                    ws_creds.append_row([ce, cp, cu, cpw])
                    st.success("Credencial añadida.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir: {type(e).__name__} — {e}")

st.divider()

# ─────────────────────────────────────────────
# HITOS DE PAGO
# ─────────────────────────────────────────────
st.header("💰 Hitos de Pago (Payment Milestones)")

COLS_HITOS = ["TIPO", "HITO", "PORCENTAJE", "PAGADO"]
ws_hitos, df_h = leer_hoja("Hitos", COLS_HITOS)

if "PAGADO" in df_h.columns:
    df_h["PAGADO"] = df_h["PAGADO"].astype(str).str.upper() == "TRUE"

cfg_h = {
    "PAGADO": st.column_config.CheckboxColumn("Pagado"),
    "PORCENTAJE": st.column_config.TextColumn("Cuota %"),
}

t1, t2 = st.tabs(["🚢 Offshore", "🏗️ Onshore"])

with t1:
    df_off = df_h[df_h["TIPO"] == "Offshore"].copy() if not df_h.empty else pd.DataFrame(columns=COLS_HITOS)
    ed_off = st.data_editor(
        df_off,
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="ed_off",
        column_order=["HITO", "PORCENTAJE", "PAGADO"],
        column_config=cfg_h,
    )

with t2:
    df_on = df_h[df_h["TIPO"] == "Onshore"].copy() if not df_h.empty else pd.DataFrame(columns=COLS_HITOS)
    ed_on = st.data_editor(
        df_on,
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="ed_on",
        column_order=["HITO", "PORCENTAJE", "PAGADO"],
        column_config=cfg_h,
    )

if st.button("💾 Guardar Hitos"):
    if ws_hitos is None:
        st.error("Sin conexión con la hoja Hitos.")
    else:
        try:
            df_off_save = ed_off.copy()
            df_on_save = ed_on.copy()
            df_off_save["TIPO"] = "Offshore"
            df_on_save["TIPO"] = "Onshore"
            
            # Concatenar y asegurar el orden de las columnas originales
            df_final = pd.concat([df_off_save, df_on_save], ignore_index=True)[COLS_HITOS]
            
            guardar_en_sheet(ws_hitos, df_final, bool_cols=["PAGADO"])
            st.cache_data.clear()
            st.success("✅ Hitos guardados.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar Hitos: {type(e).__name__} — {e}")

with st.expander("➕ Añadir Hito"):
    with st.form("f_h", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ht = c1.selectbox("Tipo", ["Offshore", "Onshore"])
        hn = c2.text_input("Descripción del Hito")
        hp = c3.text_input("Porcentaje (%)")
        if st.form_submit_button("Añadir") and hn:
            if ws_hitos is None:
                st.error("Sin conexión.")
            else:
                try:
                    ws_hitos.append_row([ht, hn, hp, "FALSE"])
                    st.cache_data.clear()
                    st.success("Hito añadido.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir: {type(e).__name__} — {e}")

st.divider()

# ─────────────────────────────────────────────
# SPARE PARTS / REPUESTOS
# ─────────────────────────────────────────────
st.header("📦 Spare Parts Inventory (Repuestos)")

COLS_SPARE = ["CATEGORIA", "DESCRIPCION", "UNIDADES"]
ws_spare, df_s = leer_hoja("Repuestos", COLS_SPARE)

search = st.text_input("🔍 Buscar repuesto...", "")

if search and not df_s.empty:
    mask = df_s["DESCRIPCION"].astype(str).str.contains(search, case=False, na=False)
    df_show = df_s[mask].copy()
else:
    df_show = df_s.copy()

df_s_ed = st.data_editor(
    df_show,
    hide_index=True,
    num_rows="dynamic",
    use_container_width=True,
    key="ed_spare",
    column_config={
        "UNIDADES": st.column_config.NumberColumn("Unidades", min_value=0),
    },
)

if st.button("💾 Guardar Inventario"):
    if ws_spare is None:
        st.error("Sin conexión con la hoja Repuestos.")
    else:
        try:
            if search and not df_s.empty:
                # Actualizar los valores en el dataframe original usando su índice para evitar sobrescribir mal
                df_s.loc[df_s_ed.index, df_s_ed.columns] = df_s_ed
                df_to_save = df_s
            else:
                df_to_save = df_s_ed
            guardar_en_sheet(ws_spare, df_to_save)
            st.cache_data.clear()
            st.success("✅ Inventario guardado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar inventario: {type(e).__name__} — {e}")

with st.expander("➕ Registrar Nuevo Repuesto"):
    with st.form("f_s", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 3, 1])
        cat = c1.selectbox(
            "Categoría",
            ["PANELS", "LV/MV COMPONENTS", "INVERTERS", "STRUCTURE",
             "SECURITY", "MONITORING", "OTROS"],
        )
        ds = c2.text_input("Descripción")
        un = c3.number_input("Unidades", min_value=1, value=1)
        if st.form_submit_button("Añadir") and ds:
            if ws_spare is None:
                st.error("Sin conexión.")
            else:
                try:
                    ws_spare.append_row([cat, ds, str(int(un))])
                    st.cache_data.clear()
                    st.success("Repuesto añadido.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo añadir: {type(e).__name__} — {e}")
