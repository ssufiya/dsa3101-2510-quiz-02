from flask import Flask, jsonify, request, send_from_directory
import os
import psycopg2
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
import uuid
import zipfile
import shutil
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://myuser:mypassword@db:5432/quiz_bank_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File storage configuration
UPLOAD_FOLDER = "uploads"
STORAGE_FOLDER = "storage/images"  # Where renamed images are stored
MASTER_CSV = "master_questions.csv"

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STORAGE_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ============================================
# DATABASE MODELS 
# ============================================

class Course(db.Model):
    """Stores course information"""
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True)
    course_name = db.Column(db.String(255))

class Users(db.Model):
    """Stores user/instructor information"""
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255))
    time_of_creation = db.Column(db.DateTime, default=db.func.current_timestamp())

class Upload(db.Model):
    """Tracks each CSV upload batch"""
    __tablename__ = 'upload'
    upload_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'))
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Attachment(db.Model):
    """Stores renamed image filenames linked to uploads"""
    __tablename__ = 'attachment'
    attachment_id = db.Column(db.Integer, primary_key=True)
    attachment_name = db.Column(db.String(255))  # The renamed filename (e.g., a3f5b2c1.png)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.upload_id'))

class Question(db.Model):
    """Main question table with all metadata"""
    __tablename__ = 'question'
    question_id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.upload_id'))
    attachment_id = db.Column(db.Integer, db.ForeignKey('attachment.attachment_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    
    # Question content
    question_text = db.Column(db.Text, nullable=False)
    question_number = db.Column(db.Integer)
    sub_question = db.Column(db.Integer)
    sub_sub_question = db.Column(db.Integer)
    question_type = db.Column(db.String(20))  # MCQ, T/F, SRQ
    
    # MCQ options
    option_a = db.Column(db.Text)
    option_b = db.Column(db.Text)
    option_c = db.Column(db.Text)
    option_d = db.Column(db.Text)
    
    # Answer and metadata
    answer = db.Column(db.Text)
    difficulty = db.Column(db.Integer)
    version = db.Column(db.Integer, default=1)
    concepts = db.Column(db.Text)  # Could be JSON array of tags

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_unique_filename(original_filename):
    """
    Generate a unique filename using UUID to prevent conflicts
    Preserves the file extension
    """
    extension = Path(original_filename).suffix  # e.g., '.png', '.jpg'
    unique_id = uuid.uuid4().hex  # Random unique identifier
    return f"{unique_id}{extension}"

def process_zip_upload(zip_file, course_code):
    """
    Extract ZIP file containing CSV + images
    Rename images and return mapping of old_name -> new_name
    """
    # Create temp directory for extraction
    temp_dir = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save and extract ZIP
    zip_path = os.path.join(temp_dir, zip_file.filename)
    zip_file.save(zip_path)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find CSV file
    csv_files = list(Path(temp_dir).rglob('*.csv'))
    if not csv_files:
        raise ValueError("No CSV file found in ZIP")
    csv_path = csv_files[0]
    
    # Find images directory
    images_dir = Path(temp_dir) / 'images'
    image_mapping = {}  # old_filename -> new_filename
    
    if images_dir.exists():
        # Create course-specific storage folder
        course_storage = os.path.join(STORAGE_FOLDER, course_code)
        os.makedirs(course_storage, exist_ok=True)
        
        # Process each image
        for image_file in images_dir.iterdir():
            if image_file.is_file():
                old_name = image_file.name
                new_name = generate_unique_filename(old_name)
                
                # Copy image to storage with new name
                new_path = os.path.join(course_storage, new_name)
                shutil.copy(str(image_file), new_path)
                
                image_mapping[old_name] = new_name
                print(f"Renamed: {old_name} -> {new_name}")
    
    return str(csv_path), image_mapping, temp_dir

def sync_questions_to_db(csv_path, upload_id, course_id, user_id, image_mapping):
    """
    Parse CSV and insert questions into database
    Links images using the renamed filenames from image_mapping
    """
    df = pd.read_csv(csv_path)
    print(f"Processing {len(df)} questions from CSV")
    
    added_count = 0
    
    for index, row in df.iterrows():
        # Get image reference if exists
        attachment_id = None
        if 'image_filename' in df.columns and pd.notna(row.get('image_filename')):
            old_image_name = str(row['image_filename']).strip()
            
            # Get renamed filename from mapping
            if old_image_name in image_mapping:
                new_image_name = image_mapping[old_image_name]
                
                # Create attachment record
                attachment = Attachment(
                    attachment_name=new_image_name,
                    upload_id=upload_id
                )
                db.session.add(attachment)
                db.session.flush()  # Get attachment_id before committing
                attachment_id = attachment.attachment_id
        
        # Create question record
        question = Question(
            upload_id=upload_id,
            attachment_id=attachment_id,
            course_id=course_id,
            user_id=user_id,
            question_text=str(row.get('question_text', '')),
            question_number=int(row['question_number']) if pd.notna(row.get('question_number')) else None,
            sub_question=int(row['sub_question']) if pd.notna(row.get('sub_question')) else None,
            question_type=str(row.get('question_type', '')),
            option_a=str(row.get('option_a', '')) if pd.notna(row.get('option_a')) else None,
            option_b=str(row.get('option_b', '')) if pd.notna(row.get('option_b')) else None,
            option_c=str(row.get('option_c', '')) if pd.notna(row.get('option_c')) else None,
            option_d=str(row.get('option_d', '')) if pd.notna(row.get('option_d')) else None,
            answer=str(row.get('answer', '')),
            difficulty=int(row['difficulty']) if pd.notna(row.get('difficulty')) else None,
            concepts=str(row.get('concepts', '')) if pd.notna(row.get('concepts')) else None
        )
        
        db.session.add(question)
        added_count += 1
    
    db.session.commit()
    print(f"✅ Added {added_count} questions to database")
    return added_count

# ============================================
# API ENDPOINTS
# ============================================

@app.route("/home")
def home():
    """Health check endpoint"""
    return jsonify({"message": "Flask server is running and connected to PostgreSQL!"})

@app.route("/upload", methods=["POST"])
def upload_questions():
    """
    Upload questions via ZIP file (containing CSV + images) or plain CSV
    
    Expected ZIP structure:
    - questions.csv
    - images/
      - diagram1.png
      - chart2.jpg
    
    CSV columns:
    - question_text (required)
    - question_number
    - sub_question  
    - question_type (MCQ, T/F, SRQ)
    - option_a, option_b, option_c, option_d (for MCQ)
    - answer
    - difficulty
    - concepts
    - image_filename (references image in images/ folder)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    # Get course_code and user_id from request
    course_code = request.form.get('course_code', 'DEFAULT')
    user_id = request.form.get('user_id', 1)  # Default to user 1 for now
    
    # Get or create course
    course = Course.query.filter_by(course_code=course_code).first()
    if not course:
        course = Course(course_code=course_code, course_name=f"Course {course_code}")
        db.session.add(course)
        db.session.commit()
    
    # Create upload record
    upload = Upload(
        filename=secure_filename(file.filename),
        course_id=course.course_id
    )
    db.session.add(upload)
    db.session.commit()
    upload_id = upload.upload_id
    
    try:
        if file.filename.endswith('.zip'):
            # Process ZIP with images
            csv_path, image_mapping, temp_dir = process_zip_upload(file, course_code)
            question_count = sync_questions_to_db(csv_path, upload_id, course.course_id, user_id, image_mapping)
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return jsonify({
                "message": "ZIP processed successfully",
                "upload_id": upload_id,
                "questions_added": question_count,
                "images_renamed": len(image_mapping)
            }), 200
            
        elif file.filename.endswith('.csv'):
            # Process plain CSV (no images)
            csv_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            file.save(csv_path)
            
            question_count = sync_questions_to_db(csv_path, upload_id, course.course_id, user_id, {})
            
            return jsonify({
                "message": "CSV processed successfully",
                "upload_id": upload_id,
                "questions_added": question_count
            }), 200
        else:
            return jsonify({"error": "Only .zip or .csv files accepted"}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/questions", methods=["GET"])
def get_questions():
    """
    Get questions with optional filters
    
    Query parameters:
    - course_code: Filter by course (e.g., DSA1101)
    - difficulty: Filter by difficulty level (1-5)
    - question_type: Filter by type (MCQ, T/F, SRQ)
    - concepts: Search in concepts field
    - limit: Max results (default 20)
    - offset: Pagination offset (default 0)
    """
    # Get query parameters
    course_code = request.args.get('course_code')
    difficulty = request.args.get('difficulty')
    question_type = request.args.get('question_type')
    concepts = request.args.get('concepts')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    # Build query
    query = Question.query
    
    # Apply filters
    if course_code:
        course = Course.query.filter_by(course_code=course_code).first()
        if course:
            query = query.filter(Question.course_id == course.course_id)
    
    if difficulty:
        query = query.filter(Question.difficulty == int(difficulty))
    
    if question_type:
        query = query.filter(Question.question_type == question_type)
    
    if concepts:
        query = query.filter(Question.concepts.ilike(f'%{concepts}%'))
    
    # Execute query with pagination
    total_count = query.count()
    results = query.limit(limit).offset(offset).all()
    
    # Format results
    questions_data = []
    for q in results:
        # Get attachment if exists
        image_url = None
        if q.attachment_id:
            attachment = Attachment.query.get(q.attachment_id)
            if attachment:
                course = Course.query.get(q.course_id)
                image_url = f"/images/{course.course_code}/{attachment.attachment_name}"
        
        questions_data.append({
            "question_id": q.question_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "answer": q.answer,
            "concepts": q.concepts,
            "image_url": image_url,
            "options": {
                "a": q.option_a,
                "b": q.option_b,
                "c": q.option_c,
                "d": q.option_d
            } if q.question_type == "MCQ" else None
        })
    
    return jsonify({
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "count": len(results),
        "questions": questions_data
    })

@app.route("/questions/<int:question_id>", methods=["GET"])
def get_question_detail(question_id):
    """Get detailed information for a specific question"""
    question = Question.query.get(question_id)
    
    if not question:
        return jsonify({"error": "Question not found"}), 404
    
    # Get related data
    course = Course.query.get(question.course_id) if question.course_id else None
    attachment = Attachment.query.get(question.attachment_id) if question.attachment_id else None
    
    image_url = None
    if attachment and course:
        image_url = f"/images/{course.course_code}/{attachment.attachment_name}"
    
    return jsonify({
        "question_id": question.question_id,
        "question_text": question.question_text,
        "question_number": question.question_number,
        "sub_question": question.sub_question,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "answer": question.answer,
        "concepts": question.concepts,
        "course_code": course.course_code if course else None,
        "image_url": image_url,
        "options": {
            "a": question.option_a,
            "b": question.option_b,
            "c": question.option_c,
            "d": question.option_d
        } if question.question_type == "MCQ" else None
    })

@app.route("/images/<course_code>/<filename>")
def serve_image(course_code, filename):
    """Serve uploaded images"""
    image_path = os.path.join(STORAGE_FOLDER, course_code)
    return send_from_directory(image_path, filename)

@app.route("/courses", methods=["GET"])
def get_courses():
    """Get list of all courses"""
    courses = Course.query.all()
    return jsonify({
        "courses": [
            {
                "course_id": c.course_id,
                "course_code": c.course_code,
                "course_name": c.course_name
            } for c in courses
        ]
    })

@app.route("/getdifficulty", methods=["GET"])
def get_difficulty():
    # Check if 'x' parameter exists
    difficulty_param = request.args.get('x')
    
    if difficulty_param is None:
        return jsonify({
            "error": "Missing 'x' parameter",
            "usage": "/getdifficulty?x=1"
        }), 400
    
    try:
        difficulty_level = int(difficulty_param)
    except ValueError:
        return jsonify({
            "error": "Parameter 'x' must be a number",
        }), 400
    
    # Optional: Validate difficulty range
    if difficulty_level < 1 or difficulty_level > 5:
        return jsonify({
            "error": "Difficulty must be between 1 and 5"
        }), 400
    
    questions = Question.query.filter_by(difficulty=difficulty_level).all()
    
    return jsonify({
        "difficulty": difficulty_level,
        "count": len(questions),
        "questions": [
            {
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "concepts": q.concepts 
            } for q in questions
        ]
    })

# ============================================
# INITIALIZATION
# ============================================

if __name__ == "__main__":
    # Tables are created and managed by teammate
    # This app only connects to existing tables
    print("✅ Connected to existing database tables")
    app.run(host="0.0.0.0", port=5000, debug=True)