import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN
st.set_page_config(layout="wide", page_title="Gantt Obra Maestro Completo")

st.title("📊 Planificación de Obra - Listado Detallado 1-12")

# 2. BASE DE DATOS INTEGRAL (SIN RESÚMENES)
if "df" not in st.session_state:
    base = datetime(2026, 4, 1)
    
    # Lista exhaustiva basada en tu mensaje
    raw_tasks = [
        # 1: INSTALACIÓN ELÉCTRICA
        ("1: Instalación eléctrica", 0),
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
        ("2: Comunicaciones", 0),
        ("Tendido Cableado", 1),
        ("CT1", 2), ("CT2", 2), ("Piranómetros", 2), ("Sensores Temperatura", 2),
        ("Estación Meteorológica", 2), ("TSMs", 2), ("Cuadro Monit CT2", 2),
        ("Cuadro Seguridad CT2", 2), ("Rack", 2), ("Cuadro Monit SC", 2),
        ("Cuadro Seguridad SC", 2), ("Cuadro Sensores SC", 2),
        ("Instalación Equipos", 1),
        ("Cuadro Monit CT2", 2), ("Cuadro Seguridad CT2", 2), ("Cuadro Monit SC", 2),
        ("Cuadro Seguridad SC", 2), ("Cuadro Sensores SC", 2),
        ("Comprobación", 1),
        ("Comunicaciones CT", 2), ("Comunicaciones CCTV", 2), ("Comunicaciones TSM", 2),
        ("Comunicaciones Sensores", 2), ("VPNs", 2),
        ("Internet", 1),
        ("Router Medidor Entronque", 2), ("Antena / FO Entronque", 2), ("Servicio Entronque", 2),
        ("Antena SC", 2), ("Router SC", 2), ("Servicio SC", 2), ("Firewall SC", 2),
        ("Preconfiguración Firewall SC", 2), ("Comisionado Firewall SC", 2),

        # 3: SENSORES
        ("3: Sensores", 0),
        ("Instalación Equipos", 1),
        ("Soportes Piranómetros", 2), ("Instalación Piranómetros", 2),
        ("Instalación Sensores Temperatura", 2), ("Instalación Celdas L/S", 2),
        ("Soportes Estación Meteo", 2), ("Instalación Estación Meteo", 2),
        ("Sensores Spare Bodega", 2),
        ("Comisionado", 1),
        ("Comisionado Contrata", 2), ("Credenciales Plataforma", 2), ("Documentación comisionado", 2),

        # 5: TRACKERS Y TSM
        ("5: Trackers y TSM", 0),
        ("TSM", 1),
        ("Sensores TSM", 2), ("Cuadros TSM", 2), ("Comisionado TSM Contrata", 2),
        ("TSC", 1),
        ("TSC Completas", 2), ("Antenas TSC", 2),
        ("Comisionado Tracker", 1),
        ("Instalación WS", 2), ("Credenciales WS", 2), ("Trackers en Seguimiento", 2),
        ("TSCs Operativas", 2), ("Documentación comisionado", 2),

        # 6: CTS
        ("6: CTs", 0),
        ("Preparación PEM CT", 1),
        ("Botellas y Parayos (CKTSA)", 2), ("Fusibles Bodega", 2), ("Kits Aisladores", 2),
        ("Cuadro SSAA", 2), ("Trafo MT", 2), ("Trafo SA", 2), ("Configuración Inversores", 2),
        ("Pletinas Inversores", 2), ("Tierras", 2), ("Filtro", 2), ("Pruebas", 2),
        ("Comisionado", 1),
        ("Monitorización Plataforma", 2), ("Banco Pértiga", 2), ("Pegatinas 5RO", 2),
        ("Pruebas PR", 2), ("Documentación comisionado", 2),

        # 7: CCTV
        ("7: CCTV", 0),
        ("Instalación Equipos", 1),
        ("Cámaras", 2), ("Teclados", 2), ("WS", 2),
        ("Comisionado", 1),
        ("Acceso Plataforma", 2), ("Credenciales", 2), ("Documentación comisionado", 2), ("Pruebas Walk Test", 2),

        # 8: SEGURIDAD
        ("8: Seguridad", 0),
        ("Guardias", 1),

        # 9: ENTRONQUE
        ("9: Entronque", 0),
        ("Reconectador", 1),
        ("Instalación", 2), ("Ajustes Protecciones", 2), ("Acceso Plataforma Remoto", 2), ("Printout", 2),
        ("Comisionado Reconectador", 1),
        ("Documentación Ajustes Protecciones", 2),
        ("Medidor", 1),
        ("Instalación", 2), ("Acceso Plataforma Remoto", 2),
        ("Empalme Línea", 1),
        ("Protocolo ECM", 2),
        ("Señalética", 1),
        ("Peligro Generador Conectado", 2),

        # 10: PEM (CONEXIONADO)
        ("10: PEM (Conexionado)", 0),
        ("CT", 1), ("Medidor", 1), ("Reco", 1), ("Permisos", 1),

        # 11: PERMISOS
        ("11: Permisos", 0),
        ("SEC", 1),
        ("TE1", 2), ("TE7", 2), ("Señalética", 2),
        ("CEN", 1),
        ("Documentación Empalme Línea", 2),
        ("SEREMI", 1),
        ("Señalética", 2), ("RESPEL", 2), ("RESNOPEL", 2), ("Aseos", 2),
        ("Otros", 1),
        ("Planos", 2),

        # 12: SERVICIOS
        ("12: Servicios", 0),
        ("Limpieza Módulos", 1),
        ("Desbroce", 1)
    ]

    formatted = []
    start_dt = base
    for i, (name, level) in enumerate(raw_tasks):
        formatted.append({
            "Task": name,
            "Level": level,
            "Start": start_dt + timedelta(days=i),
            "Finish": start_dt + timedelta(days=i+3)
        })
    st.session_state.df = pd.DataFrame(formatted)

# 3. PROCESAMIENTO
df_plot = st.session_state.df.copy()
df_plot['unique_id'] = range(len(df_plot))

def get_label(row):
    return "\u00A0" * (int(row["Level"]) * 8) + str(row["Task"])

df_plot["Task_display"] = df_plot.apply(get_label, axis=1)

# 4. GRÁFICO (Altura dinámica para evitar amontonamiento)
h_per_task = 25
dynamic_height = len(df_plot) * h_per_task + 200

fig = px.timeline(
    df_plot, 
    x_start="Start", 
    x_end="Finish", 
    y="unique_id",
    color="Level",
    color_continuous_scale="Turbo"
)

fig.update_yaxes(
    tickmode='array',
    tickvals=df_plot['unique_id'],
    ticktext=df_plot['Task_display'],
    autorange="reversed",
    title=None,
    fixedrange=True
)

fig.update_layout(
    height=dynamic_height,
    margin=dict(l=450, r=20, t=50, b=50),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# 5. EDITOR
st.subheader("📝 Tabla de Datos Completa")
st.session_state.df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
