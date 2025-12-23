import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

if not os.path.exists(db_path):
    print(f"File not found: {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM market_product")
        count = cursor.fetchone()[0]
        print(f"Products in {db_path}: {count}")
        conn.close()
    except Exception as e:
        print(f"Error checking {db_path}: {e}")
