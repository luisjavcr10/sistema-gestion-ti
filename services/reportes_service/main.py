from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
import pandas as pd
from datetime import date, datetime
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import uuid

load_dotenv()

app = FastAPI(title="Reportes Service")

# Database connection
async def get_db_connection():
    return await asyncpg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/dashboard")
async def get_dashboard():
    conn = await get_db_connection()
    try:
        total_equipos = await conn.fetchval("SELECT COUNT(*) FROM equipos")
        equipos_mantenimiento = await conn.fetchval("SELECT COUNT(*) FROM equipos WHERE estado = 'mantenimiento'")
        mantenimientos_pendientes = await conn.fetchval("SELECT COUNT(*) FROM mantenimientos WHERE estado IN ('programado', 'en_proceso')")
        costo_total_mes = await conn.fetchval("""
            SELECT COALESCE(SUM(costo), 0) FROM mantenimientos 
            WHERE fecha_realizacion >= date_trunc('month', CURRENT_DATE)
        """)
        
        return {
            "total_equipos": total_equipos,
            "equipos_mantenimiento": equipos_mantenimiento,
            "mantenimientos_pendientes": mantenimientos_pendientes,
            "costo_mantenimiento_mes": float(costo_total_mes)
        }
    finally:
        await conn.close()

@app.get("/equipos-por-ubicacion")
async def get_equipos_por_ubicacion():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT u.nombre, COUNT(e.id) as cantidad
            FROM ubicaciones u
            LEFT JOIN equipos e ON u.id = e.ubicacion_actual_id
            GROUP BY u.nombre
            ORDER BY cantidad DESC
        """)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/equipos-por-estado")
async def get_equipos_por_estado():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT estado, COUNT(*) as cantidad
            FROM equipos
            GROUP BY estado
        """)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/equipos-por-categoria")
async def get_equipos_por_categoria():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT c.nombre, COUNT(e.id) as cantidad, COALESCE(SUM(e.costo_compra), 0) as valor_total
            FROM categorias_equipos c
            LEFT JOIN equipos e ON c.id = e.categoria_id
            GROUP BY c.nombre
        """)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/equipos-antiguedad")
async def get_equipos_antiguedad():
    conn = await get_db_connection()
    try:
        # Group by years since purchase
        rows = await conn.fetch("""
            SELECT 
                CASE 
                    WHEN fecha_compra IS NULL THEN 'Desconocido'
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, fecha_compra)) < 1 THEN 'Menos de 1 año'
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, fecha_compra)) BETWEEN 1 AND 3 THEN '1-3 años'
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, fecha_compra)) BETWEEN 3 AND 5 THEN '3-5 años'
                    ELSE 'Más de 5 años'
                END as rango,
                COUNT(*) as cantidad
            FROM equipos
            GROUP BY rango
        """)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/costos-mantenimiento")
async def get_costos_mantenimiento(anio: int = 2023):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT 
                TO_CHAR(fecha_realizacion, 'Month') as mes,
                DATE_PART('month', fecha_realizacion) as mes_num,
                tipo,
                SUM(costo) as total
            FROM mantenimientos
            WHERE fecha_realizacion IS NOT NULL 
            AND DATE_PART('year', fecha_realizacion) = $1
            GROUP BY mes, mes_num, tipo
            ORDER BY mes_num
        """, float(anio))
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/mantenimientos-por-prioridad")
async def get_mantenimientos_por_prioridad():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT prioridad, COUNT(*) as cantidad
            FROM mantenimientos
            WHERE estado IN ('programado', 'en_proceso')
            GROUP BY prioridad
        """)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@app.get("/equipos-garantia")
async def get_equipos_garantia():
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT 
                CASE 
                    WHEN fecha_garantia_fin >= CURRENT_DATE THEN 'En Garantía'
                    ELSE 'Fuera de Garantía'
                END as estado_garantia,
                COUNT(*) as cantidad
            FROM equipos
            WHERE fecha_garantia_fin IS NOT NULL
            GROUP BY estado_garantia
        """)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

# Export Endpoints

class ExportRequest(BaseModel):
    tipo_reporte: str # 'inventario', 'mantenimientos', 'proveedores'
    filtros: Optional[dict] = {}

def generate_excel(data: List[dict], filename: str):
    df = pd.DataFrame(data)
    filepath = f"/app/reportes/{filename}"
    df.to_excel(filepath, index=False)
    return filepath

def generate_pdf(data: List[dict], title: str, filename: str):
    filepath = f"/app/reportes/{filename}"
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    if not data:
        elements.append(Paragraph("No hay datos para mostrar", styles['Normal']))
    else:
        # Convert data to list of lists for Table
        headers = list(data[0].keys())
        table_data = [headers]
        for item in data:
            row = [str(item.get(h, '')) for h in headers]
            table_data.append(row)
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        
    doc.build(elements)
    return filepath

@app.post("/export/excel")
async def export_excel(request: ExportRequest):
    conn = await get_db_connection()
    try:
        data = []
        filename = f"{request.tipo_reporte}_{uuid.uuid4()}.xlsx"
        
        if request.tipo_reporte == 'inventario':
            rows = await conn.fetch("""
                SELECT e.codigo_inventario, e.nombre, e.marca, e.modelo, 
                       c.nombre as categoria, u.nombre as ubicacion, e.estado
                FROM equipos e
                LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
                LEFT JOIN ubicaciones u ON e.ubicacion_actual_id = u.id
            """)
            data = [dict(row) for row in rows]
            
        elif request.tipo_reporte == 'mantenimientos':
            rows = await conn.fetch("""
                SELECT m.fecha_programada, e.nombre as equipo, m.tipo, m.estado, m.costo
                FROM mantenimientos m
                JOIN equipos e ON m.equipo_id = e.id
            """)
            data = [dict(row) for row in rows]
            
        # Add other report types as needed
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found for report")
            
        filepath = generate_excel(data, filename)
        return FileResponse(filepath, filename=filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    finally:
        await conn.close()

@app.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    conn = await get_db_connection()
    try:
        data = []
        filename = f"{request.tipo_reporte}_{uuid.uuid4()}.pdf"
        title = ""
        
        if request.tipo_reporte == 'inventario':
            title = "Reporte de Inventario de Equipos"
            rows = await conn.fetch("""
                SELECT e.codigo_inventario, e.nombre, c.nombre as categoria, e.estado
                FROM equipos e
                LEFT JOIN categorias_equipos c ON e.categoria_id = c.id
                LIMIT 100 -- Limit for PDF readability
            """)
            data = [dict(row) for row in rows]
            
        elif request.tipo_reporte == 'mantenimientos':
            title = "Reporte de Mantenimientos"
            rows = await conn.fetch("""
                SELECT m.fecha_programada, e.nombre as equipo, m.tipo, m.estado
                FROM mantenimientos m
                JOIN equipos e ON m.equipo_id = e.id
                LIMIT 100
            """)
            data = [dict(row) for row in rows]
            
        if not data:
            raise HTTPException(status_code=404, detail="No data found for report")
            
        filepath = generate_pdf(data, title, filename)
        return FileResponse(filepath, filename=filename, media_type='application/pdf')
        
    finally:
        await conn.close()
