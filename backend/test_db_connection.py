from utils.db import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM courses;")
    count = cur.fetchone()[0]
    print(f"✅ Connection successful! There are {count} courses in the database.")
    cur.close()
    conn.close()
except Exception as e:
    print("❌ Database test failed:", e)
