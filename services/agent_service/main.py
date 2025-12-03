from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI(title="Agent Service")

# Database connection
async def get_db_connection():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )

async def create_notificacion(conn, tipo: str, mensaje: str, prioridad: str = "media", datos: dict = None):
    await conn.execute("""
        INSERT INTO notificaciones (tipo, mensaje, prioridad, datos_extra)
        VALUES ($1, $2, $3, $4)
    """, tipo, mensaje, prioridad, json.dumps(datos) if datos else None)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/check-maintenance")
async def check_maintenance():
    conn = await get_db_connection()
    try:
        today = date.today()
        
        # 1. Check upcoming maintenance (7 days)
        upcoming = await conn.fetch("""
            SELECT m.*, e.nombre as equipo 
            FROM mantenimientos m
            JOIN equipos e ON m.equipo_id = e.id
            WHERE m.fecha_programada BETWEEN $1 AND $2
            AND m.estado = 'programado'
        """, today, today + timedelta(days=7))
        
        for m in upcoming:
            days = (m['fecha_programada'] - today).days
            msg = f"Mantenimiento próximo para {m['equipo']} en {days} días."
            await create_notificacion(conn, 'mantenimiento', msg, 'media', {'mantenimiento_id': str(m['id'])})

        # 2. Check overdue maintenance
        overdue = await conn.fetch("""
            SELECT m.*, e.nombre as equipo 
            FROM mantenimientos m
            JOIN equipos e ON m.equipo_id = e.id
            WHERE m.fecha_programada < $1
            AND m.estado = 'programado'
        """, today)
        
        for m in overdue:
            msg = f"URGENTE: Mantenimiento vencido para {m['equipo']}."
            await create_notificacion(conn, 'mantenimiento', msg, 'alta', {'mantenimiento_id': str(m['id'])})
            
        return {"message": "Maintenance check completed", "upcoming": len(upcoming), "overdue": len(overdue)}
    finally:
        await conn.close()

@app.post("/check-obsolescence")
async def check_obsolescence():
    conn = await get_db_connection()
    try:
        # Check equipments older than useful life
        obsolete = await conn.fetch("""
            SELECT e.id, e.nombre, e.fecha_compra, c.vida_util_anios
            FROM equipos e
            JOIN categorias_equipos c ON e.categoria_id = c.id
            WHERE e.fecha_compra IS NOT NULL
            AND (e.fecha_compra + (c.vida_util_anios || ' years')::interval) < CURRENT_DATE
            AND e.estado != 'baja'
        """)
        
        for e in obsolete:
            msg = f"Obsolescencia: El equipo {e['nombre']} ha superado su vida útil."
            await create_notificacion(conn, 'obsolescencia', msg, 'media', {'equipo_id': str(e['id'])})
            
        return {"message": "Obsolescence check completed", "count": len(obsolete)}
    finally:
        await conn.close()

@app.post("/check-warranties")
async def check_warranties():
    conn = await get_db_connection()
    try:
        today = date.today()
        # Check warranties expiring in 60 days
        expiring = await conn.fetch("""
            SELECT e.id, e.nombre, e.fecha_garantia_fin
            FROM equipos e
            WHERE e.fecha_garantia_fin BETWEEN $1 AND $2
        """, today, today + timedelta(days=60))
        
        for e in expiring:
            days = (e['fecha_garantia_fin'] - today).days
            msg = f"Garantía por vencer: {e['nombre']} expira en {days} días."
            await create_notificacion(conn, 'garantia', msg, 'media', {'equipo_id': str(e['id'])})
            
        return {"message": "Warranty check completed", "count": len(expiring)}
    finally:
        await conn.close()

@app.post("/analyze-maintenance-costs")
async def analyze_maintenance_costs():
    conn = await get_db_connection()
    try:
        # Check equipments with high maintenance costs (> 50% of purchase cost)
        high_cost = await conn.fetch("""
            SELECT e.id, e.nombre, e.costo_compra, SUM(m.costo) as total_mantenimiento
            FROM equipos e
            JOIN mantenimientos m ON e.id = m.equipo_id
            WHERE e.costo_compra > 0
            GROUP BY e.id, e.nombre, e.costo_compra
            HAVING SUM(m.costo) > (e.costo_compra * 0.5)
        """)
        
        for e in high_cost:
            msg = f"Alto Costo: Mantenimiento de {e['nombre']} supera el 50% de su valor."
            await create_notificacion(conn, 'sistema', msg, 'alta', {'equipo_id': str(e['id'])})
            
        return {"message": "Cost analysis completed", "count": len(high_cost)}
    finally:
        await conn.close()

@app.get("/notificaciones")
async def get_notificaciones(leida: Optional[bool] = False):
    conn = await get_db_connection()
    try:
        query = "SELECT * FROM notificaciones WHERE 1=1"
        params = []
        if leida is not None:
            query += " AND leida = $1"
            params.append(leida)
            
        query += " ORDER BY fecha_creacion DESC LIMIT 50"
        
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.put("/notificaciones/{id}/marcar-leida")
async def marcar_leida(id: str):
    conn = await get_db_connection()
    try:
        await conn.execute("UPDATE notificaciones SET leida = TRUE WHERE id = $1", id)
        return {"message": "Notification marked as read"}
    finally:
        await conn.close()

@app.post("/run-all-agents")
async def run_all_agents(background_tasks: BackgroundTasks):
    background_tasks.add_task(check_maintenance)
    background_tasks.add_task(check_obsolescence)
    background_tasks.add_task(check_warranties)
    background_tasks.add_task(analyze_maintenance_costs)
    return {"message": "All agents started in background"}
