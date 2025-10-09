from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Example Models (tables)
class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Course(db.Model):
    __tablename__ = "courses"
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)

@app.route("/")
def home():
    return "Flask is running ✅"

@app.route("/users")
def get_users():
    users = User.query.limit(10).all()
    data = [{"user_id": u.user_id, "username": u.username, "role": u.role} for u in users]
    return jsonify({"status": "success", "data": data})

@app.route("/courses")
def get_courses():
    courses = Course.query.limit(10).all()
    data = [{"course_id": c.course_id, "course_code": c.course_code, "course_name": c.course_name} for c in courses]
    return jsonify({"status": "success", "data": data})

@app.route("/insert-sample")
def insert_sample():
    # Insert sample data if not exists
    if not User.query.filter_by(username="alice").first():
        db.session.add(User(username="alice", password_hash="pw1", role="instructor"))
    if not User.query.filter_by(username="bob").first():
        db.session.add(User(username="bob", password_hash="pw2", role="student"))
    if not Course.query.filter_by(course_code="CS101").first():
        db.session.add(Course(course_code="CS101", course_name="Intro to CS"))
    if not Course.query.filter_by(course_code="DSA3101").first():
        db.session.add(Course(course_code="DSA3101", course_name="Data Structures"))
    db.session.commit()
    return jsonify({"status": "success", "message": "Sample data inserted"})

if __name__ == "__main__":
    app.run(debug=True)
