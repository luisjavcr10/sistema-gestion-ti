import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.set_page_config(page_title="Gestión de Equipos", page_icon="📦", layout="wide")

st.title("📦 Gestión de Equipos")

# Helper functions
def get_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/api/equipos/{endpoint}")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def post_data(endpoint, data):
    try:
        response = requests.post(f"{API_URL}/api/equipos/{endpoint}", json=data)
        return response
    except Exception as e:
        return None

# Load common data
categorias = get_data("categorias")
ubicaciones = get_data("ubicaciones")
proveedores = requests.get(f"{API_URL}/api/proveedores/proveedores").json() if requests.get(f"{API_URL}/api/proveedores/proveedores").status_code == 200 else []

tab1, tab2, tab3 = st.tabs(["📋 Lista de Equipos", "➕ Nuevo Equipo", "📈 Estadísticas"])

with tab1:
    st.subheader("Inventario de Equipos")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cat_filter = st.selectbox("Categoría", ["Todas"] + [c['nombre'] for c in categorias])
    with col2:
        estado_filter = st.selectbox("Estado", ["Todos", "disponible", "en_uso", "mantenimiento", "baja", "reparacion"])
    with col3:
        ubic_filter = st.selectbox("Ubicación", ["Todas"] + [u['nombre'] for u in ubicaciones])
    with col4:
        st.write("") # Spacer
        if st.button("🔄 Actualizar"):
            st.rerun()

    # Build query params
    params = {}
    if cat_filter != "Todas":
        cat_id = next((c['id'] for c in categorias if c['nombre'] == cat_filter), None)
        if cat_id: params['categoria_id'] = cat_id
    if estado_filter != "Todos":
        params['estado'] = estado_filter
    if ubic_filter != "Todas":
        ubic_id = next((u['id'] for u in ubicaciones if u['nombre'] == ubic_filter), None)
        if ubic_id: params['ubicacion_id'] = ubic_id

    # Fetch filtered data
    try:
        response = requests.get(f"{API_URL}/api/equipos/equipos", params=params)
        equipos = response.json() if response.status_code == 200 else []
    except:
        equipos = []
        st.error("Error al conectar con el servidor")

    if equipos:
        df = pd.DataFrame(equipos)
        
        # Display table
        st.dataframe(
            df[['codigo_inventario', 'nombre', 'marca', 'modelo', 'estado', 'categoria_nombre', 'ubicacion_nombre']],
            use_container_width=True,
            hide_index=True
        )
        
        # Detail view
        st.divider()
        st.subheader("Detalle de Equipo")
        selected_code = st.selectbox("Seleccionar Equipo para ver detalles", df['codigo_inventario'].tolist())
        
        if selected_code:
            selected_id = df[df['codigo_inventario'] == selected_code].iloc[0]['id']
            try:
                detail_resp = requests.get(f"{API_URL}/api/equipos/equipos/{selected_id}")
                if detail_resp.status_code == 200:
                    detail = detail_resp.json()
                    
                    d_col1, d_col2, d_col3 = st.columns(3)
                    with d_col1:
                        st.info(f"**Información General**")
                        st.write(f"**Código:** {detail['codigo_inventario']}")
                        st.write(f"**Nombre:** {detail['nombre']}")
                        st.write(f"**Marca/Modelo:** {detail['marca']} {detail['modelo']}")
                        st.write(f"**Serie:** {detail['numero_serie']}")
                    
                    with d_col2:
                        st.warning(f"**Estado y Ubicación**")
                        st.write(f"**Estado:** {detail['estado']}")
                        st.write(f"**Ubicación:** {detail['ubicacion_nombre']}")
                        st.write(f"**Categoría:** {detail['categoria_nombre']}")
                        st.write(f"**Proveedor:** {detail.get('proveedor_nombre', 'N/A')}")

                    with d_col3:
                        st.success(f"**Fechas y Costos**")
                        st.write(f"**Compra:** {detail['fecha_compra']}")
                        st.write(f"**Garantía Fin:** {detail['fecha_garantia_fin']}")
                        st.write(f"**Costo:** S/ {detail['costo_compra']}")
                    
                    # History
                    st.write("**Historial de Movimientos**")
                    if detail.get('historial'):
                        hist_df = pd.DataFrame(detail['historial'])
                        st.dataframe(hist_df[['fecha_movimiento', 'origen', 'destino', 'usuario', 'motivo']], hide_index=True)
                    else:
                        st.write("Sin movimientos registrados.")
                        
            except:
                st.error("Error al cargar detalles")
    else:
        st.info("No se encontraron equipos con los filtros seleccionados.")

with tab2:
    st.subheader("Registrar Nuevo Equipo")
    
    with st.form("new_equipo_form"):
        c1, c2 = st.columns(2)
        
        with c1:
            codigo = st.text_input("Código Inventario *")
            nombre = st.text_input("Nombre *")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            serie = st.text_input("Número de Serie")
            
        with c2:
            cat_id = st.selectbox("Categoría *", options=[c['id'] for c in categorias], format_func=lambda x: next((c['nombre'] for c in categorias if c['id'] == x), x))
            prov_id = st.selectbox("Proveedor", options=[p['id'] for p in proveedores], format_func=lambda x: next((p['nombre'] for p in proveedores if p['id'] == x), x))
            ubic_id = st.selectbox("Ubicación Inicial", options=[u['id'] for u in ubicaciones], format_func=lambda x: next((u['nombre'] for u in ubicaciones if u['id'] == x), x))
            estado = st.selectbox("Estado", ["disponible", "en_uso", "mantenimiento"])
            
        c3, c4 = st.columns(2)
        with c3:
            fecha_compra = st.date_input("Fecha Compra")
            costo = st.number_input("Costo Compra", min_value=0.0)
        with c4:
            fecha_garantia = st.date_input("Fin Garantía")
            
        submitted = st.form_submit_button("Guardar Equipo")
        
        if submitted:
            if not codigo or not nombre:
                st.error("Código y Nombre son obligatorios")
            else:
                data = {
                    "codigo_inventario": codigo,
                    "nombre": nombre,
                    "marca": marca,
                    "modelo": modelo,
                    "numero_serie": serie,
                    "categoria_id": cat_id,
                    "proveedor_id": prov_id,
                    "ubicacion_actual_id": ubic_id,
                    "estado": estado,
                    "fecha_compra": str(fecha_compra),
                    "fecha_garantia_fin": str(fecha_garantia),
                    "costo_compra": costo
                }
                resp = post_data("equipos", data)
                if resp and resp.status_code == 200:
                    st.success("Equipo registrado exitosamente")
                else:
                    st.error(f"Error al registrar: {resp.text if resp else 'Unknown error'}")

with tab3:
    st.subheader("Estadísticas de Equipos")
    
    if equipos:
        df_stats = pd.DataFrame(equipos)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            fig_estado = px.pie(df_stats, names='estado', title='Equipos por Estado')
            st.plotly_chart(fig_estado, use_container_width=True)
            
        with col_g2:
            fig_cat = px.bar(df_stats, x='categoria_nombre', title='Equipos por Categoría')
            st.plotly_chart(fig_cat, use_container_width=True)
            
        st.metric("Valor Total Inventario", f"S/ {df_stats['costo_compra'].sum():,.2f}")
