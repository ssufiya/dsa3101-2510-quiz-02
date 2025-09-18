from flask import Flask
from dotenv import load_dotenv
import os
import psycopg2

# Load variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

# Example route
@app.route("/")
def home():
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        cur.close()
        conn.close()
        return f"Connected to PostgreSQL! Version: {db_version[0]}"
    except Exception as e:
        return f"Connection failed: {e}"

if __name__ == "__main__":
    app.run(debug=True)
