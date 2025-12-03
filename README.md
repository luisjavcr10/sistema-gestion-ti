# Sistema de Gestión de Equipos de TI

Este proyecto es una aplicación web para la gestión integral de equipos de TI en una universidad pública.

## Estructura del Proyecto

El sistema está construido con una arquitectura de microservicios:

- **Frontend**: Streamlit
- **API Gateway**: FastAPI
- **Microservicios**:
  - `equipos_service`: Gestión de inventario y movimientos.
  - `proveedores_service`: Gestión de proveedores y contratos.
  - `mantenimiento_service`: Programación y seguimiento de mantenimientos.
  - `reportes_service`: Generación de reportes y dashboard.
  - `agent_service`: Agentes inteligentes para monitoreo y alertas.
- **Base de Datos**: PostgreSQL (Supabase)

## Configuración Inicial

1.  Clonar el repositorio.
2.  Copiar `.env.example` a `.env` y configurar las credenciales de Supabase.
3.  Ejecutar `docker-compose up --build` para iniciar todos los servicios.

## Documentación

La documentación detallada se encuentra en el directorio `docs/`.
