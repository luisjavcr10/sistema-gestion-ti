import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def init_db():
    # Get database connection details
    # Note: Supabase provides a direct postgres connection string or individual params.
    # We'll construct the connection string from the params in .env
    
    db_host = os.getenv("POSTGRES_HOST")
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_pass = os.getenv("POSTGRES_PASSWORD")
    db_port = os.getenv("POSTGRES_PORT")

    if not all([db_host, db_name, db_user, db_pass, db_port]):
        print("Error: Missing database configuration in .env")
        return

    try:
        print(f"Connecting to database {db_name} at {db_host}...")
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            port=db_port
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), '../database/schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        print("Executing schema.sql...")
        cur.execute(schema_sql)
        
        print("Schema executed successfully.")

        # Verify tables
        tables = [
            'usuarios', 'categorias_equipos', 'proveedores', 'ubicaciones', 
            'equipos', 'movimientos_equipos', 'contratos', 'mantenimientos', 
            'notificaciones'
        ]
        
        print("\nVerifying tables:")
        for table in tables:
            cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
            exists = cur.fetchone()[0]
            status = "✅ Created" if exists else "❌ Missing"
            
            # Count records if exists
            count_str = ""
            if exists:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                count_str = f"({count} records)"
            
            print(f"- {table}: {status} {count_str}")

        cur.close()
        conn.close()
        print("\nDatabase initialization completed successfully!")

    except Exception as e:
        print(f"\nError initializing database: {e}")

if __name__ == "__main__":
    init_db()
