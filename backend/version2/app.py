from flask import Flask, jsonify, request
import os
import psycopg2
import pandas as pd
from psycopg2.extras import execute_values
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://myuser:mypassword@db:5432/quiz_bank_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = "uploads"
MASTER_CSV = "master_questions.csv"

db = SQLAlchemy(app)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String)
    difficulty = db.Column(db.Integer)
    topic = db.Column(db.String)




def sync_csv_to_db(csv_path="master_questions.csv"):
    """Sync CSV data to database"""
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        
        # Debug output
        print(f"Reading CSV: {csv_path}")
        print(f"Columns found: {df.columns.tolist()}")
        print(f"Number of rows: {len(df)}")
        
        if df.empty:
            print("CSV is empty!")
            return
        
        # Get existing questions to avoid duplicates
        existing_questions = {q.question_text for q in Question.query.all()}
        
        added_count = 0
        for index, row in df.iterrows():
            question_text = row.get("question_text")
            
            # Skip if question already exists
            if question_text in existing_questions:
                print(f"Skipping duplicate: {question_text}")
                continue
            
            # Skip if missing data
            if pd.isna(question_text) or question_text == "":
                print(f"Skipping row {index}: missing question_text")
                continue
            
            # Convert difficulty to int
            try:
                diff = int(str(row.get("difficulty")).strip()) if pd.notna(row.get("difficulty")) else None
            except (ValueError, TypeError):
                print(f"Warning: Invalid difficulty for '{question_text}', setting to None")
                diff = None
            
            print(f"Adding: '{question_text}' | difficulty={diff} | topic={row.get('topic')}")
            
            q = Question(
                question_text=str(question_text),
                difficulty=diff,
                topic=str(row.get("topic")) if pd.notna(row.get("topic")) else None
            )
            db.session.add(q)
            existing_questions.add(question_text)
            added_count += 1
        
        db.session.commit()
        print(f"✅ Synced {added_count} new questions to database.")
    else:
        print(f"❌ CSV file not found: {csv_path}")




@app.route("/home")
def home():
    return jsonify({"message": "Flask server is running and connected to Postgresql!"})


@app.route("/upload", methods =["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.endswith(".csv"):
        return jsonify({"error":"Only CSV files are allowed"}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print(f"Saved upload: {filepath}")

    new_data = pd.read_csv(filepath)
    if os.path.exists(MASTER_CSV):
        all_data = pd.read_csv(MASTER_CSV)
        combined = pd.concat([all_data, new_data], ignore_index=True)
    else:
        combined = new_data
    combined.to_csv(MASTER_CSV, index = False)
    print("Master csv updated.")

    sync_csv_to_db(MASTER_CSV)

    return jsonify({"message": "File uploaded and database updated successfully."})




@app.route("/getdifficulty", methods=["GET"])
def get_difficulty():
    difficulty_level = int(request.args.get('x'))

    if difficulty_level is None:
        return jsonify({
            "error": "Missing 'x' parameter",
            "usage": "/getdifficulty?x=1"
        }), 400
    
    try:
        difficulty_level=int(difficulty_level)
    except ValueError:
        return jsonify({
            "error": "Parameter 'x' must be a number",
        }), 400
    
    questions = Question.query.filter_by(difficulty=difficulty_level).all()
    return jsonify({
        "difficulty": difficulty_level,
        "count": len(questions),
        "questions":[
            {
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "topic": q.topic
            } for q in questions
        ]
    })




@app.route("/getquestions", methods=["GET"])
def get_questions():
    difficulty= request.args.get("difficulty")
    topic = request.args.get("topic")

    query = Question.query

    if difficulty is not None:
        try:
            difficulty = int(difficulty)
            query = query.filter(Question.difficulty == difficulty)
        except ValueError:
            return jsonify({"error": "difficulty must be an integer"}), 400
    if topic is not None: 
        query = query.filter(Question.topic.ilike(f"%{topic}%"))

    results = query.all()
    return jsonify({
        "count": len(results),
        "questions": [
            {
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "topic": q.topic
            } for q in results
        ]
    })





if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        sync_csv_to_db()
    app.run(host="0.0.0.0", port=5000, debug = True)


