import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Sin Espacios")

# 1. BASE DE DATOS TOTAL (TODAS LAS TAREAS 1-12)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    tasks_data = [
        ("1: INSTALACIÓN ELÉCTRICA", 0), 
        ("Tendido Eléctrico BT", 1), 
        ("Cuadro protecciones SC", 2), ("Cuadro Comunicaciones SC", 2), ("Cuadro Sensores SC", 2),
        ("Cuadro Comunicaciones CT2", 2), ("Cuadro Sensores CT2", 2), ("Alimentaciones CCTV", 2),
        ("Alimentaciones TSM", 2), ("Alimentaciones Cuadros Monitorización", 2),
        ("Alimentaciones Cuadros Seguridad", 2), ("Alimentación Rack", 2),
        ("Alimentación Alumbrado y Secundarios", 2), 
        ("Puestas a Tierra", 1),
        ("Vallado", 2), ("TSMs", 2), ("Box TSM", 2), ("CCTV", 2), ("Vallado CT", 2),
        ("Bodega", 2), ("Trackers", 2), ("String Box", 2), 
        ("Pruebas", 1),
        ("Pruebas de aislamiento CT - Entronque", 2), ("Pruebas de aislamiento CTs", 2),
        ("Pruebas de aislamiento BT", 2), ("Polaridades CT", 2), ("Termografías", 2),
        ("Curvas IV", 2), ("Continuidad de Tierras", 2), ("Arc Flash", 2),
        
        ("2: COMUNICACIONES", 0), 
        ("Tendido Cableado", 1), ("CT1", 2), ("CT2", 2), ("Piranómetros", 2), 
        ("Sensores Temperatura", 2), ("Estación Meteorológica", 2), ("TSMs", 2),
        ("Cuadro Monit CT2", 2), ("Cuadro Seguridad CT2", 2), ("Rack", 2),
        ("Internet", 1), ("Router Medidor Entronque", 2), ("Antena / FO Entronque", 2), ("Servicio", 2),
        
        ("3: SENSORES", 0), 
        ("Instalación Equipos", 1), 
        ("Soportes Piranómetros", 2), ("Sensores Temperatura", 2), ("Piranómetros", 2),
        ("Cableado y Conexionado", 2), ("Configuración Datalogger", 2),
        
        ("4: MONTAJE ESTRUCTURAS", 0),
        ("Hincado", 1), ("Montaje Perfiles", 1), ("Montaje Módulos", 1),
        
        ("5: TRACKERS Y TSM", 0), 
        ("Instalación TSM", 1), ("Instalación TSC", 1), ("Comunicación Zigbee", 1),
        ("Comisionado Tracker", 1), ("Pruebas de Movimiento", 1),
        
        ("6: CTs", 0), 
        ("Instalación Celdas", 1), ("Instalación Transformador", 1),
        ("Conexionado MT", 1), ("Conexionado BT", 1),
        ("Preparación PEM CT", 1), ("Comisionado y Pruebas", 1),
        
        ("7: CCTV", 0), 
        ("Instalación Postes", 1), ("Montaje Cámaras", 1), ("Grabadores y Configuración", 1),
        ("Instalación Equipos", 1), ("Comisionado Sistema", 1),
        
        ("8: SEGURIDAD", 0), 
        ("Cercado Perimetral", 1), ("Puertas de Acceso", 1),
        ("Guardias y Vigilancia", 1), ("Sistemas de Alarma", 1),
        
        ("9: ENTRONQUE", 0), 
        ("Montaje Estructura MT", 1), ("Reconectador", 1), ("Medidor de Energía", 1), 
        ("Empalme Línea Existente", 1), ("Pruebas de Protección", 1),
        
        ("10: PEM (CONEXIONADO)", 0), 
        ("Verificación CT", 1), ("Verificación Medidor", 1), ("Verificación Reco", 1),
        ("Protocolos de Pruebas", 1), ("Energización", 1),
        
        ("11: PERMISOS", 0), 
        ("Tramitación SEC (TE1/TE7)", 1), ("Declaración CEN", 1), 
        ("Inspección SEREMI", 1), ("Recepción Municipal", 1),
        
        ("12: SERVICIOS", 0), 
        ("Limpieza de Módulos", 1), ("Desbroce y Control Vegetal", 1),
        ("Retirada de Escombros", 1), ("Entrega de Obra", 1)
    ]
    
    rows = []
    for i, (name, level) in enumerate(tasks_data):
        rows.append({
            "id": i,
            "Task": name,
            "Level": level,
            "Start": base + timedelta(days=i*2),
            "End": base + timedelta(days=i*2 + 4),
        })
    st.session_state.df = pd.DataFrame(rows)

# --- LÓGICA DE FECHAS DEPENDIENTES ---
def update_hierarchical_dates(df):
    df = df.copy()
    for level in [1, 0]:
        for i in range(len(df)):
            if df.loc[i, 'Level'] == level:
                children_start, children_end = [], []
                for j in range(i + 1, len(df)):
                    if df.loc[j, 'Level'] > level:
                        children_start.append(df.loc[j, 'Start'])
                        children_end.append(df.loc[j, 'End'])
                    else:
                        break
                
                if children_start and children_end:
                    df.loc[i, 'Start'] = min(children_start)
                    df.loc[i, 'End'] = max(children_end)
    return df

df_final = update_hierarchical_dates(st.session_state.df)

# --- CONTROL RETRÁCTIL ---
st.sidebar.header("Vista de Diagrama")
profundidad = st.sidebar.slider("Nivel de detalle", 0, 2, 2)

# Filtrado para gráfica
df_chart = df_final[df_final['Level'] <= profundidad].copy()

# EL SECRETO: Añadimos espacios (sangría) directamente al texto según el nivel
# Usamos \xa0 (espacio duro) para que HTML/Altair no lo borre. (6 espacios por nivel)
df_chart['Display_Task'] = df_chart.apply(lambda x: "\xa0" * 6 * int(x['Level']) + x['Task'], axis=1)

h = len(df_chart) * 22

# --- GRÁFICO ALTAIR (UNA SOLA COLUMNA DE TEXTO) ---
# Usamos una sola columna (width=280) y superponemos las capas para darles formato (negrita, cursiva)
base_text = alt.Chart(df_chart).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='Display_Task:N'
).properties(width=280, height=h)

# Capa Nivel 0 (Negrita)
c0 = base_text.transform_filter(alt.datum.Level == 0).mark_text(align='left', fontWeight='bold')
# Capa Nivel 1 (Normal)
c1 = base_text.transform_filter(alt.datum.Level == 1).mark_text(align='left')
# Capa Nivel 2 (Cursiva y Gris)
c2 = base_text.transform_filter(alt.datum.Level == 2).mark_text(align='left', fontStyle='italic', color='#555')

# Unimos las 3 capas de texto en una sola columna maestra
text_column = alt.layer(c0, c1, c2)

# Barras del Gantt
bars = alt.Chart(df_chart).mark_bar(cornerRadius=1).encode(
    x=alt.X('Start:T', axis=alt.Axis(format='%d/%m')),
    x2='End:T',
    y=alt.Y('id:O', axis=None, sort='ascending'),
    color=alt.Color('Level:N', scale=alt.Scale(range=['#004e92', '#00a1ff', '#b3e0ff']), legend=None)
).properties(width=650, height=h)

# Concatenamos la columna ÚNICA de texto con las barras
gantt = alt.hconcat(text_column, bars, spacing=0).configure_view(stroke=None)

st.altair_chart(gantt, use_container_width=False)

# --- EDITOR MAESTRO ---
st.divider()
st.subheader("📝 Editor de Tareas")
st.session_state.df = st.data_editor(st.session_state.df, hide_index=True, use_container_width=True)
