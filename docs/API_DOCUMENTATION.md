# Documentación de API

## Equipos Service

Base URL: `/api/equipos`

| Método | Endpoint        | Descripción                   |
| ------ | --------------- | ----------------------------- |
| GET    | `/equipos`      | Lista equipos con filtros     |
| GET    | `/equipos/{id}` | Detalle de equipo e historial |
| POST   | `/equipos`      | Crear nuevo equipo            |
| PUT    | `/equipos/{id}` | Actualizar equipo             |
| GET    | `/categorias`   | Listar categorías             |
| POST   | `/movimientos`  | Registrar movimiento          |

## Proveedores Service

Base URL: `/api/proveedores`

| Método | Endpoint       | Descripción        |
| ------ | -------------- | ------------------ |
| GET    | `/proveedores` | Lista proveedores  |
| POST   | `/proveedores` | Crear proveedor    |
| GET    | `/contratos`   | Listar contratos   |
| POST   | `/contratos`   | Registrar contrato |

## Mantenimiento Service

Base URL: `/api/mantenimientos`

| Método | Endpoint          | Descripción                      |
| ------ | ----------------- | -------------------------------- |
| GET    | `/mantenimientos` | Historial y programación         |
| POST   | `/mantenimientos` | Programar mantenimiento          |
| GET    | `/proximos`       | Mantenimientos próximos (7 días) |

## Reportes Service

Base URL: `/api/reportes`

| Método | Endpoint        | Descripción            |
| ------ | --------------- | ---------------------- |
| GET    | `/dashboard`    | KPIs principales       |
| POST   | `/export/pdf`   | Exportar reporte PDF   |
| POST   | `/export/excel` | Exportar reporte Excel |

## Agent Service

Base URL: `/api/agents`

| Método | Endpoint          | Descripción                |
| ------ | ----------------- | -------------------------- |
| POST   | `/run-all-agents` | Ejecutar todos los agentes |
| GET    | `/notificaciones` | Listar alertas             |
