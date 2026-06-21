"""Drop and recreate hassad_local database."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_database():
    """Drop and recreate hassad_local database."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="admin",
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Terminate existing connections
        cursor.execute("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'hassad_local'
            AND pid <> pg_backend_pid()
        """)
        
        # Drop database
        cursor.execute("DROP DATABASE IF EXISTS hassad_local")
        print("✅ Dropped existing 'hassad_local' database")
        
        # Create database
        cursor.execute("CREATE DATABASE hassad_local")
        print("✅ Created fresh 'hassad_local' database")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    exit(0 if success else 1)
