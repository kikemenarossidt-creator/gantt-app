import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# Configuración de página
st.set_page_config(layout="wide", page_title="Gantt Solar Pro - 42 Tareas")

# ---------- 1. CABECERA: FICHA TÉCNICA ----------
st.title("☀️ Control de Proyecto Fotovoltaico")

with st.container():
    st.subheader("📋 Información del Proyecto")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Nombre del Proyecto", "Planta Solar Atacama X")
        st.text_input("Dirección", "Sector Norte, Parcela 4")
        st.text_input("URL Maps", "https://maps.google.com/...")
    with col2:
        st.number_input("Potencia Pico (MWp)", value=10.5)
        st.number_input("Potencia Nominal (MWn)", value=9.0)
        st.text_input("Inversores", "SUNGROW SG250HX")
    with col3:
        st.text_input("Paneles", "JINKO Solar 550W")
        st.text_input("Trackers", "NextTracker 1P")
        st.text_input("Proveedor Seguridad", "Prosegur")

    col4, col5, col6 = st.columns(3)
    with col4: st.text_input("Comunicaciones", "Entel")
    with col5: st.text_input("Internet", "Starlink")

st.divider()

# ---------- 2. BASE DE DATOS (LAS 42 TAREAS REALES) ----------
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    # Lista maestra con columna Empresa incluida
    tasks_data = [
        {"Task": "1: INSTALACIÓN ELÉCTRICA", "Level": 0, "Parent": None, "Empresa": "Principal Eléctrica"},
        {"Task": "Tendido Eléctrico BT", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Empresa": "Sub Eléctrica"},
        {"Task": "Cuadro protecciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Empresa": "Tableros S.A."},
        {"Task": "Cuadro Comunicaciones SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Empresa": "Tableros S.A."},
        {"Task": "Cuadro Sensores SC", "Level": 2, "Parent": "Tendido Eléctrico BT", "Empresa": "Tableros S.A."},
        {"Task": "Puestas a Tierra", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Empresa": "Sub Eléctrica"},
        {"Task": "Hincado de picas", "Level": 2, "Parent": "Puestas a Tierra", "Empresa": "Civiles Chile"},
        {"Task": "Vallado Eléctrico", "Level": 2, "Parent": "Puestas a Tierra", "Empresa": "Sub Eléctrica"},
        {"Task": "Pruebas Eléctricas", "Level": 1, "Parent": "1: INSTALACIÓN ELÉCTRICA", "Empresa": "Laboratorio Cert."},
        {"Task": "Certificación de Aislamiento", "Level": 2, "Parent": "Pruebas Eléctricas", "Empresa": "Laboratorio Cert."},
        
        {"Task": "2: COMUNICACIONES", "Level": 0, "Parent": None, "Empresa": "Telco Solutions"},
        {"Task": "Tendido Fibra Óptica", "Level": 1, "Parent": "2: COMUNICACIONES", "Empresa": "Telco Solutions"},
        {"Task": "Fusión de fibras CT1", "Level": 2, "Parent": "Tendido Fibra Óptica", "Empresa": "Técnicos FO"},
        {"Task": "Fusión de fibras CT2", "Level": 2, "Parent": "Tendido Fibra Óptica", "Empresa": "Técnicos FO"},
        {"Task": "Equipos de Red", "Level": 1, "Parent": "2: COMUNICACIONES", "Empresa": "IT Global"},
        {"Task": "Configuración Router/Switch", "Level": 2, "Parent": "Equipos de Red", "Empresa": "IT Global"},
        
        {"Task": "3: SENSORES", "Level": 0, "Parent": None, "Empresa": "Meteo Tech"},
        {"Task": "Montaje de Estación Meteo", "Level": 1, "Parent": "3: SENSORES", "Empresa": "Meteo Tech"},
        {"Task": "Instalación Piranómetros", "Level": 2, "Parent": "Montaje de Estación Meteo", "Empresa": "Meteo Tech"},
        {"Task": "Sensores de Temperatura Módulo", "Level": 2, "Parent": "Montaje de Estación Meteo", "Empresa": "Meteo Tech"},
        
        {"Task": "4: MONTAJE ESTRUCTURAS", "Level": 0, "Parent": None, "Empresa": "Montajes S.A."},
        {"Task": "Hincado de Perfiles", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Empresa": "Civiles Chile"},
        {"Task": "Montaje de Vigas y Correas", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Empresa": "Montajes S.A."},
        {"Task": "Instalación de Módulos FV", "Level": 1, "Parent": "4: MONTAJE ESTRUCTURAS", "Empresa": "Montajes S.A."},
        
        {"Task": "5: TRACKERS Y TSM", "Level": 0, "Parent": None, "Empresa": "NextTracker"},
        {"Task": "6: CTs", "Level": 0, "Parent": None, "Empresa": "Inversores S.A."},
        {"Task": "7: CCTV", "Level": 0, "Parent": None, "Empresa": "Seguridad Pro"},
        {"Task": "8: SEGURIDAD", "Level": 0, "Parent": None, "Empresa": "Seguridad Pro"},
        {"Task": "9: ENTRONQUE", "Level": 0, "Parent": None, "Empresa": "Utility Co."},
        {"Task": "10: PEM (CONEXIONADO)", "Level": 0, "Parent": None, "Empresa": "Puesta en Marcha"},
        {"Task": "11: PERMISOS", "Level": 0, "Parent": None, "Empresa": "Gestoría"},
        {"Task": "12: SERVICIOS", "Level": 0, "Parent": None, "Empresa": "Mantenimiento"}
    ]
    
    rows = []
    for i, t in enumerate(tasks_data):
        rows.append({
            "id": i,
