import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from datetime import date, datetime

API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
if not API_URL.startswith("http"):
    API_URL = f"http://{API_URL}"

st.set_page_config(page_title="Gestión de Mantenimiento", page_icon="🔧", layout="wide")

st.title("🔧 Gestión de Mantenimiento")

tab1, tab2, tab3 = st.tabs(["📅 Programados", "➕ Nuevo Mantenimiento", "📜 Historial"])

def get_equipos():
    try:
        return requests.get(f"{API_URL}/api/equipos/equipos").json()
    except:
        return []

with tab1:
    st.subheader("Mantenimientos Programados")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # Calendar View (Simplified as list for now, or use a calendar component if available, but standard streamlit doesn't have a full calendar widget)
        # We'll use a table sorted by date
        try:
            proximos = requests.get(f"{API_URL}/api/mantenimientos/proximos?dias=30").json()
            if proximos:
                df = pd.DataFrame(proximos)
                st.dataframe(
                    df[['fecha_programada', 'equipo_nombre', 'tipo', 'prioridad', 'estado']],
                    use_container_width=True,
                    hide_index=True
                )
                
                st.divider()
                st.write("Acciones")
                selected_maint = st.selectbox("Seleccionar Mantenimiento para gestionar", 
                                            options=df['id'].tolist(), 
                                            format_func=lambda x: f"{df[df['id']==x].iloc[0]['fecha_programada']} - {df[df['id']==x].iloc[0]['equipo_nombre']}")
                
                if selected_maint:
                    with st.form("complete_maint"):
                        st.write("Registrar Realización")
                        c1, c2 = st.columns(2)
                        with c1:
                            f_real = st.date_input("Fecha Realización")
                            costo = st.number_input("Costo Real", min_value=0.0)
                        with c2:
                            tecnico = st.text_input("Técnico Responsable")
                            notas = st.text_area("Notas Técnicas")
                            
                        if st.form_submit_button("Marcar como Realizado"):
                            data = {
                                "estado": "completado",
                                "fecha_realizacion": str(f_real),
                                "costo": costo,
                                "tecnico_responsable": tecnico,
                                "notas_tecnicas": notas
                            }
                            requests.put(f"{API_URL}/api/mantenimientos/mantenimientos/{selected_maint}", json=data)
                            st.success("Mantenimiento completado")
                            st.rerun()
            else:
                st.info("No hay mantenimientos programados para los próximos 30 días")
        except:
            st.error("Error al cargar mantenimientos")

with tab2:
    st.subheader("Programar Mantenimiento")
    
    with st.form("new_maint"):
        equipos = get_equipos()
        e_id = st.selectbox("Equipo", options=[e['id'] for e in equipos], format_func=lambda x: next((f"{e['codigo_inventario']} - {e['nombre']}" for e in equipos if e['id'] == x), x))
        
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.selectbox("Tipo", ["preventivo", "correctivo"])
            prioridad = st.selectbox("Prioridad", ["baja", "media", "alta", "critica"])
        with c2:
            fecha = st.date_input("Fecha Programada")
            desc = st.text_area("Descripción")
            
        if st.form_submit_button("Programar"):
            data = {
                "equipo_id": e_id,
                "tipo": tipo,
                "prioridad": prioridad,
                "estado": "programado",
                "fecha_programada": str(fecha),
                "descripcion": desc
            }
            try:
                requests.post(f"{API_URL}/api/mantenimientos/mantenimientos", json=data)
                st.success("Mantenimiento programado")
            except:
                st.error("Error al programar")

with tab3:
    st.subheader("Historial de Mantenimientos")
    
    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_start = st.date_input("Desde", value=date(date.today().year, 1, 1))
    with col_f2:
        f_end = st.date_input("Hasta", value=date.today())
        
    params = {
        "fecha_inicio": str(f_start),
        "fecha_fin": str(f_end)
    }
    
    try:
        historial = requests.get(f"{API_URL}/api/mantenimientos/mantenimientos", params=params).json()
        if historial:
            df_h = pd.DataFrame(historial)
            st.dataframe(df_h, use_container_width=True, hide_index=True)
            
            # Cost chart
            if 'costo' in df_h.columns and not df_h['costo'].isnull().all():
                df_h['fecha_realizacion'] = pd.to_datetime(df_h['fecha_realizacion'])
                df_cost = df_h.groupby(df_h['fecha_realizacion'].dt.to_period("M"))['costo'].sum().reset_index()
                df_cost['fecha_realizacion'] = df_cost['fecha_realizacion'].astype(str)
                
                fig = px.bar(df_cost, x='fecha_realizacion', y='costo', title="Costos Mensuales")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontraron registros en el rango seleccionado")
    except:
        st.error("Error al cargar historial")
