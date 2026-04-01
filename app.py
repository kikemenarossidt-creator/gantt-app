import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Gantt Obra - Lista Completa 1-12")

# 1. BASE DE DATOS TOTAL (RECUPERANDO TODAS LAS TAREAS SUPRIMIDAS)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    # LISTA MAESTRA SIN RECORTES
    tasks_data = [
        # 1: INSTALACIÓN ELÉCTRICA
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
        
        # 2: COMUNICACIONES
        ("2: COMUNICACIONES", 0), 
        ("Tendido Cableado", 1), ("CT1", 2), ("CT2", 2), ("Piranómetros", 2), 
        ("Sensores Temperatura", 2), ("Estación Meteorológica", 2), ("TSMs", 2),
        ("Cuadro Monit CT2", 2), ("Cuadro Seguridad CT2", 2), ("Rack", 2),
        ("Internet", 1), ("Router Medidor Entronque", 2), ("Antena / FO Entronque", 2), ("Servicio", 2),
        
        # 3: SENSORES
        ("3: SENSORES", 0), 
        ("Instalación Equipos", 1), 
        ("Soportes Piranómetros", 2), ("Sensores Temperatura", 2), ("Piranómetros", 2),
        ("Cableado y Conexionado", 2), ("Configuración Datalogger", 2),
        
        # 4: MONTAJE ESTRUCTURAS (Añadido)
        ("4: MONTAJE ESTRUCTURAS", 0),
        ("Hincado", 1), ("Montaje Perfiles", 1), ("Montaje Módulos", 1),
        
        # 5: TRACKERS Y TSM
        ("5: TRACKERS Y TSM", 0), 
        ("Instalación TSM", 1), ("Instalación TSC", 1), ("Comunicación Zigbee", 1),
        ("Comisionado Tracker", 1), ("Pruebas de Movimiento", 1),
        
        # 6: CTs (Centros de Transformación)
        ("6: CTs", 0), 
        ("Instalación Celdas", 1), ("Instalación Transformador", 1),
        ("Conexionado MT", 1), ("Conexionado BT", 1),
        ("Preparación PEM CT", 1), ("Comisionado y Pruebas", 1),
        
        # 7: CCTV
        ("7: CCTV", 0), 
        ("Instalación Postes", 1), ("Montaje Cámaras", 1), ("Grabadores y Configuración", 1),
        ("Instalación Equipos", 1), ("Comisionado Sistema", 1),
        
        # 8: SEGURIDAD
        ("8: SEGURIDAD", 0), 
        ("Cercado Perimetral", 1), ("Puertas de Acceso", 1),
        ("Guardias y Vigilancia", 1), ("Sistemas de Alarma", 1),
        
        # 9: ENTRONQUE
        ("9: ENTRONQUE", 0), 
        ("Montaje Estructura MT", 1), ("Reconectador", 1), ("Medidor de Energía", 1), 
        ("Empalme Línea Existente", 1), ("Pruebas de Protección", 1),
        
        # 10: PEM (PUESTA EN MARCHA)
        ("10: PEM (CONEXIONADO)", 0), 
        ("Verificación CT", 1), ("Verificación Medidor", 1), ("Verificación Reco", 1),
        ("Protocolos de Pruebas", 1), ("Energización", 1),
        
        # 11: PERMISOS Y RECEPCIONES
        ("11: PERMISOS", 0), 
        ("Tramitación SEC (TE1/TE7)", 1), ("Declaración CEN", 1), 
        ("Inspección SEREMI", 1), ("Recepción Municipal", 1),
        
        # 12: SERVICIOS Y CIERRE
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
            "Start": base + timedelta(days=i),
            "End": base + timedelta(days=i+2),
        })
    st.session_state.df = pd.DataFrame(rows)

# 2. PROCESAMIENTO DE COLUMNAS PARA EL GANTT
df = st.session_state.df.copy()
df['L0'] = df.apply(lambda x: x['Task'] if x['Level'] == 0 else "", axis=1)
df['L1'] = df.apply(lambda x: x['Task'] if x['Level'] == 1 else "", axis=1)
df['L2'] = df.apply(lambda x: x['Task'] if x['Level'] == 2 else "", axis=1)

# 3. CONFIGURACIÓN VISUAL
h = len(df) * 20  # Altura proporcional al número total de tareas

# Columna Nivel 0: Títulos de Sección
col0 = alt.Chart(df).mark_text(align='left', fontWeight='bold', size=11).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L0:N'
).properties(width=160, height=h)

# Columna Nivel 1: Tareas Principales
col1 = alt.Chart(df).mark_text(align='left', dx=10, size=10).encode(
    y=alt.Y('id:O', axis=None, sort='ascending'),
    text='L1:N'
).properties(width=160, height=h)

# Columna Nivel 2: Sub-tareas Detalladas
col2 = alt.Chart(df).mark_text(align='left', dx=20, fontStyle='italic', size=10, color='#444').encode(
    y=alt.Y
