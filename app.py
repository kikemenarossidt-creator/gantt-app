import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Gantt Solar Sync")

def conectar_google_sheets():
    # Definimos el alcance
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Cargamos credenciales desde los Secrets de Streamlit
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # CAMBIA ESTO por el nombre exacto de tu Excel o su ID
    # Ejemplo con nombre: client.open("Nombre Del Archivo").sheet1
    # Ejemplo con ID (más seguro):
    ID_HOJA = "TU_ID_DE_GOOGLE_SHEETS_AQUI" 
    sheet = client.open_by_key(ID_HOJA).worksheet("Tareas")
    return sheet

# --- CABECERA ---
st.title("☀️ Gestión de Proyecto Solar (Sync Sheets)")

with st.expander("📋 Ficha Técnica del Proyecto", expanded=False):
    c1, c2, c3 = st.columns(3)
    c1.text_input("Proyecto", "Planta Atacama")
    c2.number_input("MWp", value=10.5)
    c3.text_input("Inversores", "Sungrow")

# --- LÓGICA PRINCIPAL ---
try:
    google_sheet = conectar_google_sheets()
    lista_datos = google_sheet.get_all_records()
    df = pd.DataFrame(lista_datos)

    if not df.empty:
        # Convertir fechas a formato datetime para que Altair no falle
        df['Start'] = pd.to_datetime(df['Start'], dayfirst=True)
        df['End'] = pd.to_datetime(df['End'], dayfirst=True)

        # Gráfica
        st.subheader("📊 Cronograma Gantt")
        prof = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
        df_plot = df[df['Level'] <= prof].copy()
        df_plot['Display'] = df_plot.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)

        chart_h = max(len(df_plot) * 30, 150)
        c_base = alt.Chart(df_plot).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
        text = c_base.mark_text(align='left').encode(text='Display:N').properties(width=300, height=chart_h)
        bars = c_base.mark_bar().encode(
            x=alt.X('Start:T', title="Fecha"), 
            x2='End:T',
            color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
            tooltip=['Task', 'Empresa a Cargo', 'Start', 'End']
        ).properties(width=800, height=chart_h)
        
        st.altair_chart(alt.hconcat(text, bars))

        st.divider()
        st.subheader("📝 Editor de Datos")
        df_editado = st.data_editor(df, hide_index=True, use_container_width=True)

        if st.button("💾 Guardar cambios en Google Sheets"):
            # Convertimos fechas a string para guardar de vuelta
            df_guardar = df_editado.copy()
            df_guardar['Start'] = df_guardar['Start'].dt.strftime('%d/%m/%Y')
            df_guardar['End'] = df_guardar['End'].dt.strftime('%d/%m/%Y')
            
            google_sheet.clear()
            google_sheet.update([df_guardar.columns.values.tolist()] + df_guardar.values.tolist())
            st.success("¡Sincronizado con éxito!")
            st.rerun()
    else:
        st.info("La hoja está vacía. Añade datos en Google Sheets.")

except Exception as e:
    st.error(f"Error: {e}")
