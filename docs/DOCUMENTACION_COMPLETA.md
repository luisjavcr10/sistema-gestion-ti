# DOCUMENTACIÓN DEL SISTEMA DE GESTIÓN DE TI

## 1. CÓMO INICIAR EL PROYECTO

### Prerrequisitos

- Docker Desktop instalado y ejecutándose.
- Git instalado.

### Pasos de Instalación

1.  **Clonar el repositorio:**
    Descargue el código fuente a su máquina local.

2.  **Configurar Variables de Entorno:**
    Asegúrese de tener el archivo `.env` en la raíz del proyecto con las credenciales de base de datos correctas.

3.  **Iniciar los Servicios:**
    Abra una terminal en la carpeta del proyecto y ejecute:

    ```bash
    docker-compose up --build -d
    ```

    Esto descargará las imágenes necesarias e iniciará los 7 contenedores del sistema (Base de datos, 5 microservicios, API Gateway y Frontend).

4.  **Inicializar la Base de Datos (Solo la primera vez):**
    Para crear las tablas y datos de prueba, ejecute el siguiente comando (asegúrese de que los contenedores estén corriendo):

    ```bash
    cat database/schema.sql | docker-compose exec -T postgres psql -U postgres -d postgres
    ```

5.  **Acceder a la Aplicación:**
    - **Frontend (Usuario):** Abra su navegador en `http://localhost:8501`
    - **Documentación API (Swagger):** `http://localhost:8000/docs`

---

## 2. ESTRUCTURA DEL PROYECTO

El sistema sigue una arquitectura de microservicios organizada de la siguiente manera:

```text
sistema-gestion-ti/
├── database/                   # Scripts de Base de Datos
│   └── schema.sql              # Definición de tablas y datos semilla
├── docs/                       # Documentación del proyecto
├── frontend/                   # Aplicación de Usuario (Streamlit)
│   ├── pages/                  # Páginas del sistema (Equipos, Proveedores, etc.)
│   ├── app.py                  # Página principal (Dashboard)
│   └── Dockerfile              # Configuración de despliegue frontend
├── scripts/                    # Scripts de utilidad (Backup, Restore, Health Check)
├── services/                   # Backend (Microservicios)
│   ├── agent_service/          # Agentes inteligentes en segundo plano
│   ├── api_gateway/            # Puerta de enlace principal
│   ├── equipos_service/        # Gestión de inventario
│   ├── mantenimiento_service/  # Gestión de mantenimientos
│   ├── proveedores_service/    # Gestión de proveedores y contratos
│   └── reportes_service/       # Analítica y generación de reportes
├── .env                        # Variables de entorno (Credenciales)
├── docker-compose.yml          # Orquestación de contenedores
└── render.yaml                 # Configuración para despliegue en la nube
```

---

## 3. API ENDPOINTS

A continuación se listan todos los puntos de acceso disponibles en el sistema a través del API Gateway.

### 📦 Servicio de Equipos

| Método | Endpoint                    | Descripción                                     |
| ------ | --------------------------- | ----------------------------------------------- |
| GET    | `/api/equipos/equipos`      | Listar todos los equipos (filtros disponibles). |
| POST   | `/api/equipos/equipos`      | Registrar un nuevo equipo.                      |
| GET    | `/api/equipos/equipos/{id}` | Obtener detalle e historial de un equipo.       |
| PUT    | `/api/equipos/equipos/{id}` | Actualizar datos de un equipo.                  |
| DELETE | `/api/equipos/equipos/{id}` | Eliminar un equipo.                             |
| GET    | `/api/equipos/categorias`   | Listar categorías de equipos.                   |
| GET    | `/api/equipos/ubicaciones`  | Listar ubicaciones disponibles.                 |
| POST   | `/api/equipos/movimientos`  | Registrar traslado de equipo.                   |

### 🏢 Servicio de Proveedores

| Método | Endpoint                       | Descripción                |
| ------ | ------------------------------ | -------------------------- |
| GET    | `/api/proveedores/proveedores` | Listar proveedores.        |
| POST   | `/api/proveedores/proveedores` | Registrar nuevo proveedor. |
| GET    | `/api/proveedores/contratos`   | Listar contratos vigentes. |
| POST   | `/api/proveedores/contratos`   | Registrar nuevo contrato.  |

### 🔧 Servicio de Mantenimiento

| Método | Endpoint                             | Descripción                                     |
| ------ | ------------------------------------ | ----------------------------------------------- |
| GET    | `/api/mantenimientos/mantenimientos` | Historial de mantenimientos.                    |
| POST   | `/api/mantenimientos/mantenimientos` | Programar nuevo mantenimiento.                  |
| GET    | `/api/mantenimientos/proximos`       | Listar mantenimientos para los próximos 7 días. |
| GET    | `/api/mantenimientos/calendario`     | Datos para vista de calendario.                 |

### 📊 Servicio de Reportes

| Método | Endpoint                              | Descripción                    |
| ------ | ------------------------------------- | ------------------------------ |
| GET    | `/api/reportes/dashboard`             | KPIs principales del sistema.  |
| GET    | `/api/reportes/equipos-por-estado`    | Estadísticas de estado.        |
| GET    | `/api/reportes/equipos-por-ubicacion` | Distribución geográfica.       |
| GET    | `/api/reportes/costos-mantenimiento`  | Evolución de costos mensuales. |
| POST   | `/api/reportes/export/pdf`            | Generar reporte en PDF.        |
| POST   | `/api/reportes/export/excel`          | Generar reporte en Excel.      |

### 🤖 Servicio de Agentes (Inteligencia)

| Método | Endpoint                                       | Descripción                             |
| ------ | ---------------------------------------------- | --------------------------------------- |
| POST   | `/api/agents/run-all-agents`                   | Ejecutar análisis completo del sistema. |
| GET    | `/api/agents/notificaciones`                   | Obtener alertas generadas.              |
| PUT    | `/api/agents/notificaciones/{id}/marcar-leida` | Marcar alerta como leída.               |

---

## 4. CONFIGURACIÓN AVANZADA

### Puertos del Sistema

El sistema utiliza los siguientes puertos para sus servicios:

| Servicio                  | Puerto Interno | Puerto Externo (Host)          |
| ------------------------- | -------------- | ------------------------------ |
| **Frontend**              | 8501           | 8501                           |
| **API Gateway**           | 8000           | 8000                           |
| **Equipos Service**       | 8001           | 8001                           |
| **Proveedores Service**   | 8002           | 8002                           |
| **Mantenimiento Service** | 8003           | 8003                           |
| **Reportes Service**      | 8004           | 8004                           |
| **Agent Service**         | 8005           | 8005                           |
| **Base de Datos**         | 5432           | 5432 (o 5433 si hay conflicto) |

### Variables de Entorno (.env)

Estas son las variables clave para la configuración del despliegue:

| Variable            | Descripción                              | Ejemplo                        |
| ------------------- | ---------------------------------------- | ------------------------------ |
| `POSTGRES_HOST`     | Dirección del servidor de Base de Datos. | `localhost` o `db.supabase.co` |
| `POSTGRES_PORT`     | Puerto de conexión a BD.                 | `5432`                         |
| `POSTGRES_DB`       | Nombre de la base de datos.              | `postgres`                     |
| `POSTGRES_USER`     | Usuario de la base de datos.             | `postgres`                     |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos.          | `*****`                        |
| `API_GATEWAY_URL`   | URL del Gateway para el Frontend.        | `http://api-gateway:8000`      |
