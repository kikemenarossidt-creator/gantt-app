import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(layout="wide", page_title="Gantt Solar Pro")

def conectar_google_sheets():
    # Configuración de permisos
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Extraer credenciales de los Secrets de Streamlit
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Usamos el ID que me pasaste
        ID_HOJA = "1n63OLrzPg27ekpipyW_XF-kXfpg4F-yEkRc0gKynrys"
        
        # Abrimos el archivo y seleccionamos la primera pestaña
        sheet_file = client.open_by_key(ID_HOJA)
        return sheet_file.get_worksheet(0)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

st.title("☀️ Gestión de Proyecto Solar (Sincronizado)")

# --- CARGAR DATOS ---
ws = conectar_google_sheets()

if ws:
    try:
        data = ws.get_all_records()
        if not data:
            st.warning("La hoja está vacía. Asegúrate de pegar la tabla de 42 tareas en el Excel.")
        else:
            df = pd.DataFrame(data)

            # 1. Limpieza y Formato de Fechas
            df['Start'] = pd.to_datetime(df['Start'], dayfirst=True, errors='coerce')
            df['End'] = pd.to_datetime(df['End'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Start', 'End']) # Quitamos filas mal formadas

            # 2. Visualización Gantt
            st.subheader("📊 Cronograma de Obra")
            profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)
            
            df_plot = df[df['Level'] <= profundidad].sort_values('id')
            # Sangría visual para la jerarquía
            df_plot['Display_Task'] = df_plot.apply(lambda x: "\xa0" * 6 * int(x['Level']) + str(x['Task']), axis=1)

            chart_height = max(len(df_plot) * 30, 200)
            
            # Gráfico de barras (Gantt)
            c_base = alt.Chart(df_plot).encode(y=alt.Y('id:O', axis=None, sort='ascending'))
            
            text_col = c_base.mark_text(align='left', fontSize=12).encode(
                text='Display_Task:N'
            ).properties(width=350, height=chart_height)
            
            bars_col = c_base.mark_bar(cornerRadius=3).encode(
                x=alt.X('Start:T', title='Fecha'),
                x2='End:T',
                color=alt.Color('Level:N', scale=alt.Scale(range=['#1a5276', '#3498db', '#aed6f1']), legend=None),
                tooltip=['Task', 'Empresa a Cargo', 'Start', 'End']
            ).properties(width=800, height=chart_height)

            st.altair_chart(alt.hconcat(text_col, bars_col), use_container_width=True)

            # 3. Editor de Datos
            st.divider()
            st.subheader("📝 Editor Maestro")
            st.info("Puedes editar nombres, fechas y empresas directamente aquí abajo:")
            
            df_editado = st.data_editor(
                df, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "Start": st.column_config.DateColumn("Inicio"),
                    "End": st.column_config.DateColumn("Fin"),
                }
            )

            # 4. Botón de Guardado
            if st.button("💾 Guardar cambios en Google Sheets"):
                with st.spinner("Actualizando nube..."):
                    # Convertir fechas de vuelta a texto para Google Sheets
                    df_save = df_editado.copy()
                    df_save['Start'] = df_save['Start'].dt.strftime('%d/%m/%Y')
                    df_save['End'] = df_save['End'].dt.strftime('%d/%m/%Y')
                    
                    ws.clear()
                    ws.update([df_save.columns.values.tolist()] + df_save.values.tolist())
                    st.success("¡Datos guardados correctamente!")
                    st.rerun()

    except Exception as e:
        st.error(f"Ocurrió un error al procesar los datos: {e}")
