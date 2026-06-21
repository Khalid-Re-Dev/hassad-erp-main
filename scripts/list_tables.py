import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="hassad_local",
    user="postgres",
    password="admin"
)
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [t[0] for t in cur.fetchall()]
print(f"\nFound {len(tables)} tables:")
for t in tables:
    print(f"  - {t}")
conn.close()
