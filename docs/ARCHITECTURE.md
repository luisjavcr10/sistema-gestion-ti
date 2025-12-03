# Arquitectura del Sistema

## Diagrama de Arquitectura General

```mermaid
graph TD
    User[Usuario] -->|HTTP/HTTPS| Frontend[Frontend Streamlit]
    Frontend -->|REST API| Gateway[API Gateway]

    subgraph "Microservicios"
        Gateway -->|/api/equipos| Equipos[Equipos Service]
        Gateway -->|/api/proveedores| Proveedores[Proveedores Service]
        Gateway -->|/api/mantenimientos| Mantenimiento[Mantenimiento Service]
        Gateway -->|/api/reportes| Reportes[Reportes Service]
        Gateway -->|/api/agents| Agents[Agent Service]
    end

    subgraph "Persistencia"
        Equipos --> DB[(PostgreSQL)]
        Proveedores --> DB
        Mantenimiento --> DB
        Reportes --> DB
        Agents --> DB
    end
```

## Diagrama de Flujo de Datos

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant G as API Gateway
    participant S as Servicio
    participant D as Base de Datos

    U->>F: Solicita información
    F->>G: Request HTTP
    G->>S: Enruta Request
    S->>D: Consulta SQL
    D-->>S: Retorna Datos
    S-->>G: Response JSON
    G-->>F: Response JSON
    F-->>U: Renderiza UI
```

## Diagrama Entidad-Relación (Simplificado)

```mermaid
erDiagram
    EQUIPOS ||--o{ MOVIMIENTOS : tiene
    EQUIPOS ||--o{ MANTENIMIENTOS : recibe
    CATEGORIAS ||--o{ EQUIPOS : clasifica
    PROVEEDORES ||--o{ EQUIPOS : suministra
    PROVEEDORES ||--o{ CONTRATOS : firma
    UBICACIONES ||--o{ EQUIPOS : aloja
    UBICACIONES ||--o{ MOVIMIENTOS : origen/destino
```

## Componentes

1. **Frontend (Streamlit)**: Interfaz de usuario interactiva para gestión y visualización.
2. **API Gateway (FastAPI)**: Punto de entrada único, maneja enrutamiento y CORS.
3. **Equipos Service**: Microservicio core para inventario y trazabilidad.
4. **Proveedores Service**: Gestión de terceros y contratos.
5. **Mantenimiento Service**: Lógica de negocio para programación de tareas técnicas.
6. **Reportes Service**: Generación de dashboards y exportables.
7. **Agent Service**: Procesos en segundo plano para monitoreo proactivo.
8. **PostgreSQL**: Base de datos relacional centralizada.
