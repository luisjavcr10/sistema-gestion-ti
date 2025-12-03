import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import altair as alt

API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
if not API_URL.startswith("http"):
    API_URL = f"http://{API_URL}"

st.set_page_config(page_title="Reportes y Análisis", page_icon="📊", layout="wide")

st.title("📊 Reportes y Análisis")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "📊 Gráficos Detallados", "📥 Exportar", "🧠 Análisis Avanzado"])

def get_data(endpoint):
    try:
        return requests.get(f"{API_URL}/api/reportes/{endpoint}").json()
    except:
        return []

with tab1:
    st.subheader("KPIs Principales")
    
    dash_data = get_data("dashboard")
    if dash_data:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Equipos", dash_data['total_equipos'])
        c2.metric("En Mantenimiento", dash_data['equipos_mantenimiento'])
        c3.metric("Pendientes", dash_data['mantenimientos_pendientes'])
        c4.metric("Costo Mes", f"S/ {dash_data['costo_mantenimiento_mes']:,.2f}")
    
    st.divider()
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write("Equipos por Estado")
        data_estado = get_data("equipos-por-estado")
        if data_estado:
            fig = px.pie(data_estado, values='cantidad', names='estado', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
    with col_d2:
        st.write("Equipos por Ubicación")
        data_ubic = get_data("equipos-por-ubicacion")
        if data_ubic:
            fig = px.bar(data_ubic, x='nombre', y='cantidad')
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Visualización de Datos")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.write("Costos de Mantenimiento por Mes")
        data_costos = get_data("costos-mantenimiento")
        if data_costos:
            df_costos = pd.DataFrame(data_costos)
            fig = px.line(df_costos, x='mes', y='total', color='tipo', markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g2:
        st.write("Antigüedad de Equipos")
        data_antig = get_data("equipos-antiguedad")
        if data_antig:
            fig = px.bar(data_antig, x='rango', y='cantidad')
            st.plotly_chart(fig, use_container_width=True)
            
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        st.write("Mantenimientos por Prioridad")
        data_prio = get_data("mantenimientos-por-prioridad")
        if data_prio:
            fig = px.bar(data_prio, x='prioridad', y='cantidad', color='prioridad')
            st.plotly_chart(fig, use_container_width=True)
            
    with col_g4:
        st.write("Estado de Garantías")
        data_garantia = get_data("equipos-garantia")
        if data_garantia:
            fig = px.pie(data_garantia, values='cantidad', names='estado_garantia')
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Exportar Reportes")
    
    report_type = st.selectbox("Tipo de Reporte", ["inventario", "mantenimientos"])
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📄 Exportar a PDF"):
            with st.spinner("Generando PDF..."):
                try:
                    resp = requests.post(f"{API_URL}/api/reportes/export/pdf", json={"tipo_reporte": report_type})
                    if resp.status_code == 200:
                        st.download_button(
                            label="Descargar PDF",
                            data=resp.content,
                            file_name=f"reporte_{report_type}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Error al generar PDF")
                except:
                    st.error("Error de conexión")
                    
    with c2:
        if st.button("📊 Exportar a Excel"):
            with st.spinner("Generando Excel..."):
                try:
                    resp = requests.post(f"{API_URL}/api/reportes/export/excel", json={"tipo_reporte": report_type})
                    if resp.status_code == 200:
                        st.download_button(
                            label="Descargar Excel",
                            data=resp.content,
                            file_name=f"reporte_{report_type}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("Error al generar Excel")
                except:
                    st.error("Error de conexión")

with tab4:
    st.subheader("Análisis Avanzado")
    
    st.write("Valor del Inventario por Categoría")
    data_cat = get_data("equipos-por-categoria")
    if data_cat:
        df_cat = pd.DataFrame(data_cat)
        
        chart = alt.Chart(df_cat).mark_bar().encode(
            x='nombre',
            y='valor_total',
            tooltip=['nombre', 'cantidad', 'valor_total']
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
    st.divider()
    
    st.write("Eficiencia de Mantenimiento (Simulado)")
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = 85,
        title = {'text': "Eficiencia Global"},
        gauge = {'axis': {'range': [None, 100]},
                 'bar': {'color': "darkblue"},
                 'steps' : [
                     {'range': [0, 50], 'color': "lightgray"},
                     {'range': [50, 80], 'color': "gray"}],
                 'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}}))

    st.plotly_chart(fig)
