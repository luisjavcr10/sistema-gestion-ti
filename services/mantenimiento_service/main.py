from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Mantenimiento Service")

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
class MantenimientoBase(BaseModel):
    equipo_id: str
    tipo: str # 'preventivo', 'correctivo'
    prioridad: str = "media"
    estado: str = "programado"
    fecha_programada: date
    fecha_realizacion: Optional[date] = None
    costo: Optional[float] = None
    descripcion: Optional[str] = None
    tecnico_responsable: Optional[str] = None
    notas_tecnicas: Optional[str] = None

class MantenimientoCreate(MantenimientoBase):
    pass

class MantenimientoUpdate(BaseModel):
    tipo: Optional[str] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    fecha_programada: Optional[date] = None
    fecha_realizacion: Optional[date] = None
    costo: Optional[float] = None
    descripcion: Optional[str] = None
    tecnico_responsable: Optional[str] = None
    notas_tecnicas: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/mantenimientos")
async def get_mantenimientos(
    estado: Optional[str] = None,
    tipo: Optional[str] = None,
    equipo_id: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None
):
    conn = await get_db_connection()
    try:
        query = """
            SELECT m.*, e.nombre as equipo_nombre, e.codigo_inventario 
            FROM mantenimientos m
            JOIN equipos e ON m.equipo_id = e.id
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        if estado:
            query += f" AND m.estado = ${param_idx}"
            params.append(estado)
            param_idx += 1
            
        if tipo:
            query += f" AND m.tipo = ${param_idx}"
            params.append(tipo)
            param_idx += 1
            
        if equipo_id:
            query += f" AND m.equipo_id = ${param_idx}"
            params.append(equipo_id)
            param_idx += 1
            
        if fecha_inicio:
            query += f" AND m.fecha_programada >= ${param_idx}"
            params.append(fecha_inicio)
            param_idx += 1
            
        if fecha_fin:
            query += f" AND m.fecha_programada <= ${param_idx}"
            params.append(fecha_fin)
            param_idx += 1
            
        query += " ORDER BY m.fecha_programada DESC"
            
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/mantenimientos/{id}")
async def get_mantenimiento(id: str):
    conn = await get_db_connection()
    try:
        mantenimiento = await conn.fetchrow("""
            SELECT m.*, e.nombre as equipo_nombre, e.codigo_inventario, 
                   c.nombre as categoria_nombre, u.nombre as ubicacion_nombre
            FROM mantenimientos m
            JOIN equipos e ON m.equipo_id = e.id
            LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
            LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
            WHERE m.id = $1
        """, id)
        
        if not mantenimiento:
            raise HTTPException(status_code=404, detail="Mantenimiento not found")
            
        return dict(mantenimiento)
    finally:
        await conn.close()

@app.post("/mantenimientos")
async def create_mantenimiento(mantenimiento: MantenimientoCreate):
    conn = await get_db_connection()
    try:
        query = """
            INSERT INTO mantenimientos (
                equipo_id, tipo, prioridad, estado, fecha_programada, 
                fecha_realizacion, costo, descripcion, tecnico_responsable, notas_tecnicas
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        """
        row = await conn.fetchrow(query, 
            mantenimiento.equipo_id, mantenimiento.tipo, mantenimiento.prioridad, 
            mantenimiento.estado, mantenimiento.fecha_programada, mantenimiento.fecha_realizacion,
            mantenimiento.costo, mantenimiento.descripcion, mantenimiento.tecnico_responsable,
            mantenimiento.notas_tecnicas
        )
        return {"id": row['id'], "message": "Mantenimiento created successfully"}
    finally:
        await conn.close()

@app.put("/mantenimientos/{id}")
async def update_mantenimiento(id: str, mantenimiento: MantenimientoUpdate):
    conn = await get_db_connection()
    try:
        fields = []
        params = []
        param_idx = 1
        
        update_data = mantenimiento.dict(exclude_unset=True)
        for key, value in update_data.items():
            fields.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1
            
        if not fields:
            return {"message": "No changes provided"}
            
        params.append(id)
        query = f"UPDATE mantenimientos SET {', '.join(fields)} WHERE id = ${param_idx}"
        
        result = await conn.execute(query, *params)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Mantenimiento not found")
            
        return {"message": "Mantenimiento updated successfully"}
    finally:
        await conn.close()

@app.get("/calendario")
async def get_calendario(mes: int = Query(..., ge=1, le=12), anio: int = Query(..., ge=2000)):
    conn = await get_db_connection()
    try:
        # Get start and end of month
        start_date = date(anio, mes, 1)
        if mes == 12:
            end_date = date(anio + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(anio, mes + 1, 1) - timedelta(days=1)
            
        query = """
            SELECT m.id, m.fecha_programada, m.tipo, m.estado, e.nombre as title
            FROM mantenimientos m
            JOIN equipos e ON m.equipo_id = e.id
            WHERE m.fecha_programada BETWEEN $1 AND $2
        """
        rows = await conn.fetch(query, start_date, end_date)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/proximos")
async def get_proximos(dias: int = 7):
    conn = await get_db_connection()
    try:
        today = date.today()
        limit_date = today + timedelta(days=dias)
        
        query = """
            SELECT m.*, e.nombre as equipo_nombre, e.codigo_inventario
            FROM mantenimientos m
            JOIN equipos e ON m.equipo_id = e.id
            WHERE m.fecha_programada BETWEEN $1 AND $2
            AND m.estado IN ('programado', 'en_proceso')
            ORDER BY m.fecha_programada ASC
        """
        rows = await conn.fetch(query, today, limit_date)
        return [dict(row) for row in rows]
    finally:
        await conn.close()
