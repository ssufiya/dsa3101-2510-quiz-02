from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

# Helper function to get a DB connection
def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route("/")
def home():
    return "Flask is running ✅"

@app.route("/test-db")
def test_db():
    """Insert sample user and return first 5 users"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Insert sample user
                cur.execute("""
                    INSERT INTO users (username, password_hash, role)
                    VALUES ('testuser', 'hashed_password', 'instructor')
                    ON CONFLICT (username) DO NOTHING;
                """)

                # Fetch first 5 users
                cur.execute("SELECT user_id, username, role FROM users LIMIT 5;")
                rows = cur.fetchall()

        return jsonify({"status": "success", "data": rows})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/users")
def get_users():
    """Return first 10 users"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, username, role FROM users LIMIT 10;")
                rows = cur.fetchall()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/courses")
def get_courses():
    """Return first 10 courses"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT course_id, course_code, course_name FROM courses LIMIT 10;")
                rows = cur.fetchall()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/tables")
def list_tables():
    """List all tables in the current database"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema='public';
                """)
                tables = [row['table_name'] for row in cur.fetchall()]
        return jsonify({"status": "success", "tables": tables})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/insert-sample")
def insert_sample_data():
    """Insert sample users and courses for testing"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Sample users
                cur.execute("""
                    INSERT INTO users (username, password_hash, role)
                    VALUES
                    ('alice', 'pw1', 'instructor'),
                    ('bob', 'pw2', 'student')
                    ON CONFLICT (username) DO NOTHING;
                """)

                # Sample courses
                cur.execute("""
                    INSERT INTO courses (course_code, course_name)
                    VALUES
                    ('CS101', 'Intro to CS'),
                    ('DSA3101', 'Data Structures')
                    ON CONFLICT (course_code) DO NOTHING;
                """)

        return jsonify({"status": "success", "message": "Sample data inserted"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
