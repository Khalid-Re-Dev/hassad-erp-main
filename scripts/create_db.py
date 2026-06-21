"""Create hassad_local database if it doesn't exist."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create hassad_local database."""
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
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'hassad_local'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE hassad_local")
            print("✅ Database 'hassad_local' created successfully")
        else:
            print("ℹ️  Database 'hassad_local' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    exit(0 if success else 1)
