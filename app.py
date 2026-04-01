import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE GOOGLE SHEETS ---
def conectar_google_sheets():
    # Usa los secrets de Streamlit para conectar
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Nota: Debes pegar tu JSON de credenciales en Streamlit Secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # Reemplaza con el nombre exacto de tu archivo
ID_HOJA = "TU_ID_AQUI" # Es el código largo entre /d/ y /edit
sheet = client.open_by_key(ID_HOJA).worksheet("Tareas")
    return sheet

st.set_page_config(layout="wide", page_title="Gantt Solar Sync")

# --- CABECERA (FICHA TÉCNICA) ---
st.title("☀️ Gestión de Proyecto Solar (Sync Sheets)")
with st.expander("📋 Ficha Técnica del Proyecto"):
    c1, c2, c3 = st.columns(3)
    nombre = c1.text_input("Proyecto", "Planta Atacama")
    mwp = c2.number_input("MWp", value=10.5)
    inversores = c3.text_input("Inversores", "Sungrow")
    # ... otros campos ...

# --- CARGA Y EDICIÓN DE DATOS ---
try:
    google_sheet = conectar_google_sheets()
    data = google_sheet.get_all_records()
    df = pd.DataFrame(data)

    st.subheader("📊 Cronograma Gantt")
    # Filtro de profundidad
    prof = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
    df_plot = df[df['Level'] <= prof].copy()
    df_plot['Display'] = df_plot.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)

    # Gráfica Altair
    chart_h = len(df_plot) * 30
    c_base = alt.Chart(df_plot).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
    text = c_base.mark_text(align='left').encode(text='Display:N').properties(width=300, height=chart_h)
    bars = c_base.mark_bar().encode(
        x='Start:T', x2='End:T',
        color='Level:N',
        tooltip=['Task', 'Empresa a Cargo', 'Start', 'End']
    ).properties(width=800, height=chart_h)
    
    st.altair_chart(alt.hconcat(text, bars))

    st.divider()
    st.subheader("📝 Editor de Datos (Sincronizado)")
    # La tabla permite editar TODO, incluida la columna Empresa
    df_editado = st.data_editor(df, hide_index=True, use_container_width=True)

    if st.button("💾 Guardar cambios en Google Sheets"):
        # Sobreescribe la hoja con los nuevos datos
        google_sheet.clear()
        google_sheet.update([df_editado.columns.values.tolist()] + df_editado.values.tolist())
        st.success("¡Datos actualizados en la nube!")
        st.rerun()

except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.info("Asegúrate de configurar st.secrets['gcp_service_account'] y que el nombre del archivo sea correcto.")
