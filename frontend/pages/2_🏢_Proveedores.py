import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.set_page_config(page_title="Gestión de Proveedores", page_icon="🏢", layout="wide")

st.title("🏢 Gestión de Proveedores")

tab1, tab2, tab3 = st.tabs(["📋 Lista de Proveedores", "➕ Nuevo Proveedor", "📜 Contratos"])

def get_proveedores(activo=None):
    params = {}
    if activo is not None:
        params['activo'] = activo
    try:
        return requests.get(f"{API_URL}/api/proveedores/proveedores", params=params).json()
    except:
        return []

with tab1:
    st.subheader("Directorio de Proveedores")
    
    activo_filter = st.checkbox("Mostrar solo activos", value=True)
    proveedores = get_proveedores(activo=True if activo_filter else None)
    
    if proveedores:
        df = pd.DataFrame(proveedores)
        st.dataframe(
            df[['nombre', 'ruc', 'contacto_nombre', 'contacto_email', 'contacto_telefono', 'activo']],
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        st.subheader("Detalle de Proveedor")
        selected_prov = st.selectbox("Seleccionar Proveedor", df['nombre'].tolist())
        
        if selected_prov:
            prov_id = df[df['nombre'] == selected_prov].iloc[0]['id']
            try:
                detail = requests.get(f"{API_URL}/api/proveedores/proveedores/{prov_id}").json()
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**RUC:** {detail['ruc']}")
                    st.write(f"**Dirección:** {detail['direccion']}")
                    st.write(f"**Estado:** {'Activo' if detail['activo'] else 'Inactivo'}")
                with c2:
                    st.write(f"**Contacto:** {detail['contacto_nombre']}")
                    st.write(f"**Email:** {detail['contacto_email']}")
                    st.write(f"**Teléfono:** {detail['contacto_telefono']}")
                    
                st.metric("Total Equipos Suministrados", detail['estadisticas']['total_equipos'])
                
                st.write("**Contratos Asociados**")
                if detail['contratos']:
                    st.dataframe(pd.DataFrame(detail['contratos']))
                else:
                    st.info("No tiene contratos registrados")
            except:
                st.error("Error al cargar detalle")
    else:
        st.info("No hay proveedores registrados")

with tab2:
    st.subheader("Registrar Nuevo Proveedor")
    with st.form("new_prov_form"):
        nombre = st.text_input("Razón Social *")
        ruc = st.text_input("RUC *")
        direccion = st.text_area("Dirección")
        
        st.markdown("---")
        st.write("Datos de Contacto")
        c1, c2, c3 = st.columns(3)
        with c1: contact_name = st.text_input("Nombre Contacto")
        with c2: contact_email = st.text_input("Email")
        with c3: contact_phone = st.text_input("Teléfono")
        
        submitted = st.form_submit_button("Guardar Proveedor")
        
        if submitted:
            if not nombre or not ruc:
                st.error("Nombre y RUC son obligatorios")
            else:
                data = {
                    "nombre": nombre,
                    "ruc": ruc,
                    "direccion": direccion,
                    "contacto_nombre": contact_name,
                    "contacto_email": contact_email,
                    "contacto_telefono": contact_phone,
                    "activo": True
                }
                try:
                    resp = requests.post(f"{API_URL}/api/proveedores/proveedores", json=data)
                    if resp.status_code == 200:
                        st.success("Proveedor registrado")
                    else:
                        st.error(f"Error: {resp.text}")
                except:
                    st.error("Error de conexión")

with tab3:
    st.subheader("Gestión de Contratos")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.write("Listado de Contratos")
        try:
            contratos = requests.get(f"{API_URL}/api/proveedores/contratos").json()
            if contratos:
                df_c = pd.DataFrame(contratos)
                st.dataframe(df_c[['numero_contrato', 'proveedor_nombre', 'tipo', 'fecha_inicio', 'fecha_fin', 'estado']], use_container_width=True)
            else:
                st.info("No hay contratos")
        except:
            st.error("Error al cargar contratos")
            
    with c2:
        st.write("Nuevo Contrato")
        with st.form("new_contract"):
            all_provs = get_proveedores()
            p_id = st.selectbox("Proveedor", options=[p['id'] for p in all_provs], format_func=lambda x: next((p['nombre'] for p in all_provs if p['id'] == x), x))
            num = st.text_input("N° Contrato")
            tipo = st.selectbox("Tipo", ["compra", "mantenimiento", "arrendamiento"])
            f_ini = st.date_input("Inicio")
            f_fin = st.date_input("Fin")
            monto = st.number_input("Monto Total", min_value=0.0)
            
            if st.form_submit_button("Registrar Contrato"):
                data = {
                    "proveedor_id": p_id,
                    "numero_contrato": num,
                    "tipo": tipo,
                    "fecha_inicio": str(f_ini),
                    "fecha_fin": str(f_fin),
                    "monto_total": monto
                }
                try:
                    requests.post(f"{API_URL}/api/proveedores/contratos", json=data)
                    st.success("Contrato registrado")
                    st.rerun()
                except:
                    st.error("Error al guardar")
