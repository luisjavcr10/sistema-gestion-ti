from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncpg
import os
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Equipos Service")

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
class EquipoBase(BaseModel):
    codigo_inventario: str
    nombre: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    categoria_id: str
    proveedor_id: Optional[str] = None
    ubicacion_actual_id: Optional[str] = None
    estado: str = "disponible"
    fecha_compra: Optional[date] = None
    fecha_garantia_fin: Optional[date] = None
    costo_compra: Optional[float] = None
    especificaciones: Optional[Dict[str, Any]] = None

class EquipoCreate(EquipoBase):
    pass

class EquipoUpdate(BaseModel):
    nombre: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    categoria_id: Optional[str] = None
    proveedor_id: Optional[str] = None
    ubicacion_actual_id: Optional[str] = None
    estado: Optional[str] = None
    fecha_compra: Optional[date] = None
    fecha_garantia_fin: Optional[date] = None
    costo_compra: Optional[float] = None
    especificaciones: Optional[Dict[str, Any]] = None

class MovimientoCreate(BaseModel):
    equipo_id: str
    ubicacion_destino_id: str
    usuario_id: str
    motivo: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/equipos")
async def get_equipos(
    categoria_id: Optional[str] = None,
    estado: Optional[str] = None,
    ubicacion_id: Optional[str] = None
):
    conn = await get_db_connection()
    try:
        query = """
            SELECT e.*, c.nombre as categoria_nombre, u.nombre as ubicacion_nombre 
            FROM equipos e
            LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
            LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        if categoria_id:
            query += f" AND e.categoria_id = ${param_idx}"
            params.append(categoria_id)
            param_idx += 1
            
        if estado:
            query += f" AND e.estado = ${param_idx}"
            params.append(estado)
            param_idx += 1
            
        if ubicacion_id:
            query += f" AND e.ubicacion_actual_id = ${param_idx}"
            params.append(ubicacion_id)
            param_idx += 1
            
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/equipos/{id}")
async def get_equipo(id: str):
    conn = await get_db_connection()
    try:
        # Get basic info
        equipo = await conn.fetchrow("""
            SELECT e.*, c.nombre as categoria_nombre, u.nombre as ubicacion_nombre, p.nombre as proveedor_nombre
            FROM equipos e
            LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
            LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
            LEFT JOIN proveedores p ON e.proveedor_id = p.id
            WHERE e.id = $1
        """, id)
        
        if not equipo:
            raise HTTPException(status_code=404, detail="Equipo not found")
            
        # Get history
        historial = await conn.fetch("""
            SELECT m.*, u_orig.nombre as origen, u_dest.nombre as destino, us.nombre as usuario
            FROM movimientos_equipos m
            LEFT JOIN ubicaciones u_orig ON m.ubicacion_origen_id = u_orig.id
            LEFT JOIN ubicaciones u_dest ON m.ubicacion_destino_id = u_dest.id
            LEFT JOIN usuarios us ON m.usuario_id = us.id
            WHERE m.equipo_id = $1
            ORDER BY m.fecha_movimiento DESC
        """, id)
        
        result = dict(equipo)
        result['historial'] = [dict(h) for h in historial]
        return result
    finally:
        await conn.close()

@app.post("/equipos")
async def create_equipo(equipo: EquipoCreate):
    conn = await get_db_connection()
    try:
        # Check if code exists
        exists = await conn.fetchval("SELECT 1 FROM equipos WHERE codigo_inventario = $1", equipo.codigo_inventario)
        if exists:
            raise HTTPException(status_code=400, detail="Codigo inventario already exists")

        query = """
            INSERT INTO equipos (
                codigo_inventario, nombre, marca, modelo, numero_serie, 
                categoria_id, proveedor_id, ubicacion_actual_id, estado, 
                fecha_compra, fecha_garantia_fin, costo_compra, especificaciones
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
        """
        row = await conn.fetchrow(query, 
            equipo.codigo_inventario, equipo.nombre, equipo.marca, equipo.modelo, equipo.numero_serie,
            equipo.categoria_id, equipo.proveedor_id, equipo.ubicacion_actual_id, equipo.estado,
            equipo.fecha_compra, equipo.fecha_garantia_fin, equipo.costo_compra, equipo.especificaciones
        )
        return {"id": row['id'], "message": "Equipo created successfully"}
    finally:
        await conn.close()

@app.put("/equipos/{id}")
async def update_equipo(id: str, equipo: EquipoUpdate):
    conn = await get_db_connection()
    try:
        # Build dynamic update query
        fields = []
        params = []
        param_idx = 1
        
        update_data = equipo.dict(exclude_unset=True)
        for key, value in update_data.items():
            fields.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1
            
        if not fields:
            return {"message": "No changes provided"}
            
        params.append(id)
        query = f"UPDATE equipos SET {', '.join(fields)} WHERE id = ${param_idx}"
        
        result = await conn.execute(query, *params)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Equipo not found")
            
        return {"message": "Equipo updated successfully"}
    finally:
        await conn.close()

@app.delete("/equipos/{id}")
async def delete_equipo(id: str):
    conn = await get_db_connection()
    try:
        result = await conn.execute("DELETE FROM equipos WHERE id = $1", id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Equipo not found")
        return {"message": "Equipo deleted successfully"}
    finally:
        await conn.close()

@app.get("/categorias")
async def get_categorias():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM categorias_equipos")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/ubicaciones")
async def get_ubicaciones():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT * FROM ubicaciones WHERE activo = TRUE")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.post("/movimientos")
async def create_movimiento(movimiento: MovimientoCreate):
    conn = await get_db_connection()
    try:
        async with conn.transaction():
            # Get current location
            current_loc = await conn.fetchval("SELECT ubicacion_actual_id FROM equipos WHERE id = $1", movimiento.equipo_id)
            
            if not current_loc:
                raise HTTPException(status_code=404, detail="Equipo not found")

            # Insert movement
            await conn.execute("""
                INSERT INTO movimientos_equipos (
                    equipo_id, ubicacion_origen_id, ubicacion_destino_id, 
                    usuario_id, motivo
                ) VALUES ($1, $2, $3, $4, $5)
            """, movimiento.equipo_id, current_loc, movimiento.ubicacion_destino_id, 
               movimiento.usuario_id, movimiento.motivo)
            
            # Update equipment location
            await conn.execute("""
                UPDATE equipos SET ubicacion_actual_id = $1 WHERE id = $2
            """, movimiento.ubicacion_destino_id, movimiento.equipo_id)
            
        return {"message": "Movimiento registered successfully"}
    finally:
        await conn.close()
