import sqlite3
import os

db_path = r"c:\Users\ElBarto\Desktop\OverPlay\Backend\historial.db"
print("Checking database path:", db_path)
print("File exists:", os.path.exists(db_path))

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

for table in tables:
    print(f"\n--- Schema for {table} ---")
    cursor.execute(f"PRAGMA table_info({table});")
    for col in cursor.fetchall():
        print(dict(col))
    
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")
    
    if count > 0:
        cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
        print("Sample data:")
        for row in cursor.fetchall():
            print(dict(row))

conn.close()
