from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Proveedores Service")

# Database connection
async def get_db_connection():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )

# Models
class ProveedorBase(BaseModel):
    nombre: str
    ruc: str
    contacto_nombre: Optional[str] = None
    contacto_email: Optional[str] = None
    contacto_telefono: Optional[str] = None
    direccion: Optional[str] = None
    activo: bool = True

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    ruc: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_email: Optional[str] = None
    contacto_telefono: Optional[str] = None
    direccion: Optional[str] = None
    activo: Optional[bool] = None

class ContratoBase(BaseModel):
    proveedor_id: str
    numero_contrato: Optional[str] = None
    tipo: Optional[str] = None
    fecha_inicio: date
    fecha_fin: date
    monto_total: Optional[float] = None
    archivo_url: Optional[str] = None
    estado: str = "vigente"

class ContratoCreate(ContratoBase):
    pass

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/proveedores")
async def get_proveedores(activo: Optional[bool] = None):
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM proveedores WHERE 1=1"
        params = []
        if activo is not None:
            query += " AND activo = $1"
            params.append(activo)
            
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/proveedores/{id}")
async def get_proveedor(id: str):
    conn = await get_db_connection()
    try:
        proveedor = await conn.fetchrow("SELECT * FROM proveedores WHERE id = $1", id)
        if not proveedor:
            raise HTTPException(status_code=404, detail="Proveedor not found")
            
        # Get contracts
        contratos = await conn.fetch("SELECT * FROM contratos WHERE proveedor_id = $1", id)
        
        # Get stats (e.g., number of equipments)
        equipos_count = await conn.fetchval("SELECT COUNT(*) FROM equipos WHERE proveedor_id = $1", id)
        
        result = dict(proveedor)
        result['contratos'] = [dict(c) for c in contratos]
        result['estadisticas'] = {'total_equipos': equipos_count}
        return result
    finally:
        await conn.close()

@app.post("/proveedores")
async def create_proveedor(proveedor: ProveedorCreate):
    conn = await get_db_connection()
    try:
        # Validate RUC
        exists = await conn.fetchval("SELECT 1 FROM proveedores WHERE ruc = $1", proveedor.ruc)
        if exists:
            raise HTTPException(status_code=400, detail="RUC already exists")

        query = """
            INSERT INTO proveedores (
                nombre, ruc, contacto_nombre, contacto_email, contacto_telefono, direccion, activo
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        row = await conn.fetchrow(query, 
            proveedor.nombre, proveedor.ruc, proveedor.contacto_nombre, 
            proveedor.contacto_email, proveedor.contacto_telefono, 
            proveedor.direccion, proveedor.activo
        )
        return {"id": row['id'], "message": "Proveedor created successfully"}
    finally:
        await conn.close()

@app.put("/proveedores/{id}")
async def update_proveedor(id: str, proveedor: ProveedorUpdate):
    conn = await get_db_connection()
    try:
        fields = []
        params = []
        param_idx = 1
        
        update_data = proveedor.dict(exclude_unset=True)
        for key, value in update_data.items():
            fields.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1
            
        if not fields:
            return {"message": "No changes provided"}
            
        params.append(id)
        query = f"UPDATE proveedores SET {', '.join(fields)} WHERE id = ${param_idx}"
        
        result = await conn.execute(query, *params)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Proveedor not found")
            
        return {"message": "Proveedor updated successfully"}
    finally:
        await conn.close()

@app.get("/contratos")
async def get_contratos(proveedor_id: Optional[str] = None):
    conn = await get_db_connection()
    try:
        query = """
            SELECT c.*, p.nombre as proveedor_nombre 
            FROM contratos c
            JOIN proveedores p ON c.proveedor_id = p.id
            WHERE 1=1
        """
        params = []
        if proveedor_id:
            query += " AND c.proveedor_id = $1"
            params.append(proveedor_id)
            
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.post("/contratos")
async def create_contrato(contrato: ContratoCreate):
    conn = await get_db_connection()
    try:
        # Calculate state based on dates
        today = date.today()
        estado = "vigente"
        if contrato.fecha_fin < today:
            estado = "vencido"
        elif contrato.fecha_inicio > today:
            estado = "pendiente"

        query = """
            INSERT INTO contratos (
                proveedor_id, numero_contrato, tipo, fecha_inicio, fecha_fin, 
                monto_total, archivo_url, estado
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        row = await conn.fetchrow(query, 
            contrato.proveedor_id, contrato.numero_contrato, contrato.tipo,
            contrato.fecha_inicio, contrato.fecha_fin, contrato.monto_total,
            contrato.archivo_url, estado
        )
        return {"id": row['id'], "message": "Contrato created successfully"}
    finally:
        await conn.close()
