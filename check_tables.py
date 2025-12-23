import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for table in tables:
        print(table[0])
    conn.close()
except Exception as e:
    print(f"Error: {e}")
