# Guía de Despliegue

## Prerrequisitos

- Docker Desktop instalado
- Git
- Cuenta en Supabase (o PostgreSQL local)

## Pasos de Instalación

1. **Clonar el repositorio**

   ```bash
   git clone <repo-url>
   cd sistema-gestion-ti
   ```

2. **Configurar Variables de Entorno**

   - Copiar `.env.example` (o usar el creado) a `.env`
   - Editar `.env` con las credenciales de la base de datos.

3. **Iniciar Servicios**

   ```bash
   docker-compose up --build -d
   ```

4. **Inicializar Base de Datos**

   - Asegurarse que los contenedores estén corriendo.
   - Ejecutar el script de inicialización (requiere python local o ejecutar dentro del contenedor):

   ```bash
   # Opción A: Local (si tiene python y dependencias)
   pip install -r scripts/requirements.txt
   python scripts/init_db.py

   # Opción B: Manual
   # Conectarse a la BD y ejecutar database/schema.sql
   ```

5. **Verificar Despliegue**
   - Frontend: http://localhost:8501
   - API Gateway Docs: http://localhost:8000/docs

## Solución de Problemas

- **Error de conexión a BD**: Verificar credenciales en `.env` y que el puerto 5432 no esté ocupado.
- **Servicios no inician**: Revisar logs con `docker-compose logs -f`.
