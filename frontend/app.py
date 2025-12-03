import streamlit as st
import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Config
st.set_page_config(
    page_title="Sistema Gestión TI",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
if not API_URL.startswith("http"):
    API_URL = f"http://{API_URL}"

# Helper functions
def get_dashboard_data():
    try:
        response = requests.get(f"{API_URL}/api/reportes/dashboard")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_notificaciones():
    try:
        response = requests.get(f"{API_URL}/api/agents/notificaciones?leida=false")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def run_agents():
    try:
        requests.post(f"{API_URL}/api/agents/run-all-agents")
        st.toast("Agentes ejecutándose en segundo plano", icon="🤖")
    except:
        st.error("Error al ejecutar agentes")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=LOGO+TI", use_column_width=True)
    st.title("Gestión TI")
    st.write(f"Usuario: Admin")
    
    st.divider()
    
    st.subheader("🤖 Agentes Inteligentes")
    if st.button("Ejecutar Análisis Completo"):
        run_agents()
        
    st.divider()
    
    st.subheader("🔔 Notificaciones")
    notificaciones = get_notificaciones()
    if not notificaciones:
        st.info("No hay nuevas notificaciones")
    else:
        for notif in notificaciones[:5]:
            if isinstance(notif, dict):
                icon = "🔴" if notif.get('prioridad') == 'alta' else "🔵"
                st.warning(f"{icon} {notif.get('mensaje', '')}")

# Main Content
st.title("🖥️ Sistema de Gestión de Activos TI")
st.markdown("Bienvenido al panel de control principal.")

# Dashboard
data = get_dashboard_data()

if data:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Equipos", data['total_equipos'])
    with col2:
        st.metric("En Mantenimiento", data['equipos_mantenimiento'], delta_color="inverse")
    with col3:
        st.metric("Mantenimientos Pendientes", data['mantenimientos_pendientes'])
    with col4:
        st.metric("Costo Mantenimiento (Mes)", f"S/ {data['costo_mantenimiento_mes']:,.2f}")
else:
    st.error("No se pudo conectar con el servicio de reportes")

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["Resumen", "Estadísticas Rápidas", "Acerca de"])

with tab1:
    st.subheader("Resumen del Sistema")
    st.write("Este sistema permite la gestión integral de activos de TI, incluyendo inventario, mantenimiento, proveedores y reportes.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("""
        **Módulos Disponibles:**
        - 📦 **Equipos**: Gestión de inventario y movimientos.
        - 🏢 **Proveedores**: Gestión de contratos y proveedores.
        - 🔧 **Mantenimiento**: Programación y seguimiento.
        - 📊 **Reportes**: Análisis y exportación de datos.
        """)
    with col_b:
        st.success("""
        **Estado del Sistema:**
        - Base de Datos: Conectada
        - API Gateway: Activo
        - Agentes: En espera
        """)

with tab2:
    st.subheader("Vista Rápida")
    # Here we could add some mini charts if needed, but for now just placeholder
    st.write("Seleccione el módulo de Reportes para ver estadísticas detalladas.")

with tab3:
    st.write("Sistema de Gestión de TI v1.0")
    st.write("Desarrollado para Examen de Laboratorio Unidad III")

# Footer
st.divider()
st.caption("© 2023 Universidad Pública - Departamento de TI")
