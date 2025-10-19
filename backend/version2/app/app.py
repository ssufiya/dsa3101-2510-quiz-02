from flask import Flask, jsonify, request, send_from_directory
import os
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from pathlib import Path
import zipfile
import shutil

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://myuser:mypassword@db:5432/quiz_bank_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File storage configuration
UPLOAD_FOLDER = "uploads"
STORAGE_FOLDER = "storage/attachments"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STORAGE_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ============================================
# DATABASE MODELS
# ============================================

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(225), nullable=False)
    role = db.Column(db.String(25), default='instructor')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(10), unique=True, nullable=False)
    course_name = db.Column(db.String(255), nullable=False)

class Assessment(db.Model):
    __tablename__ = 'assessments'
    assessment_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    assessment_type = db.Column(db.String(50))
    assessment_acadyear = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))

class Context(db.Model):
    __tablename__ = 'contexts'
    context_id = db.Column(db.Integer, primary_key=True)
    context_text = db.Column(db.Text)
    context_attachment = db.Column(db.String(500))

class Attachment(db.Model):
    __tablename__ = 'attachments'
    attachment_id = db.Column(db.Integer, primary_key=True)
    attachment_name = db.Column(db.String(255))
    attachment_type = db.Column(db.String(50))
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.context_id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'))

class Question(db.Model):
    __tablename__ = 'questions'
    question_id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.assessment_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    context_id = db.Column(db.Integer, db.ForeignKey('contexts.context_id'))
    attachment_id = db.Column(db.Integer, db.ForeignKey('attachments.attachment_id'))
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50))
    option_a = db.Column(db.Text)
    option_b = db.Column(db.Text)
    option_c = db.Column(db.Text)
    option_d = db.Column(db.Text)
    option_e = db.Column(db.Text)
    correct_answer = db.Column(db.String(10))
    difficulty = db.Column(db.String(20))
    concepts = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    version_number = db.Column(db.Integer, default=1)
    previous_version_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'))

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_unique_filename(original_filename):
    """Generate a unique filename using UUID"""
    extension = Path(original_filename).suffix
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{extension}"

def process_zip_with_images(zip_file, user_id):
    """
    Extract ZIP file containing CSV + images
    Returns: (csv_path, image_mapping, temp_dir)
    """
    # Create temp directory for extraction
    temp_dir = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save and extract ZIP
    zip_path = os.path.join(temp_dir, secure_filename(zip_file.filename))
    zip_file.save(zip_path)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Find CSV file
    csv_files = list(Path(temp_dir).rglob('*.csv'))
    if not csv_files:
        raise ValueError("No CSV file found in ZIP")
    csv_path = str(csv_files[0])
    
    # Find images directory
    images_dir = Path(temp_dir) / 'images'
    image_mapping = {}  # old_filename -> new_filename
    
    if images_dir.exists():
        # Process each image
        for image_file in images_dir.iterdir():
            if image_file.is_file() and image_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']:
                old_name = image_file.name
                new_name = generate_unique_filename(old_name)
                
                # Copy image to storage
                new_path = os.path.join(STORAGE_FOLDER, new_name)
                shutil.copy(str(image_file), new_path)
                
                image_mapping[old_name] = new_name
                print(f"✅ Image renamed: {old_name} -> {new_name}")
    
    return csv_path, image_mapping, temp_dir

# ============================================
# API ENDPOINTS
# ============================================

@app.route("/")
def home():
    """Health check endpoint"""
    return jsonify({"message": "Quiz Bank API is running!"})

# ============================================
# UPLOAD ENDPOINT - CSV/ZIP to Database
# ============================================

@app.route("/upload", methods=["POST"])
def upload_csv():
    """
    Upload questions from CSV or ZIP file
    
    For ZIP files, expected structure:
    - questions.csv
    - images/
      - diagram1.png
      - chart2.jpg
    
    CSV columns:
    - question_text (required)
    - question_type (MCQ, T/F, Essay, etc.)
    - option_a, option_b, option_c, option_d, option_e (for MCQ)
    - correct_answer (e.g., 'A', 'B', 'C', 'D', 'E')
    - difficulty (Easy, Medium, Hard)
    - concepts (comma-separated tags)
    - course_code (e.g., DSA1101)
    - assessment_type (optional: Quiz, Exam, Practice)
    - assessment_acadyear (optional: 2023/2024)
    - image_filename (optional: references image in images/ folder)
    
    Form data:
    - file: CSV or ZIP file
    - user_id: ID of instructor uploading (default: 1)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    user_id = request.form.get('user_id', 1)
    
    try:
        csv_path = None
        image_mapping = {}
        temp_dir = None
        
        # Handle ZIP files with images
        if file.filename.endswith('.zip'):
            csv_path, image_mapping, temp_dir = process_zip_with_images(file, user_id)
            print(f"📦 Processing ZIP file with {len(image_mapping)} images")
        
        # Handle plain CSV files
        elif file.filename.endswith('.csv'):
            csv_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            file.save(csv_path)
            print("📄 Processing CSV file")
        
        else:
            return jsonify({"error": "Only .csv or .zip files are accepted"}), 400
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_columns = ['question_text']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return jsonify({"error": f"Missing required columns: {missing}"}), 400
        
        added_count = 0
        images_attached = 0
        
        for _, row in df.iterrows():
            # Get or create course
            course = None
            if 'course_code' in df.columns and pd.notna(row.get('course_code')):
                course_code = str(row['course_code']).strip()
                course = Course.query.filter_by(course_code=course_code).first()
                
                if not course:
                    course = Course(
                        course_code=course_code,
                        course_name=f"Course {course_code}"
                    )
                    db.session.add(course)
                    db.session.flush()
            
            # Create or get assessment if specified
            assessment = None
            if course and 'assessment_type' in df.columns and pd.notna(row.get('assessment_type')):
                assessment_type = str(row['assessment_type']).strip()
                assessment_acadyear = str(row.get('assessment_acadyear', '')).strip() if pd.notna(row.get('assessment_acadyear')) else None
                
                query = Assessment.query.filter_by(
                    course_id=course.course_id,
                    assessment_type=assessment_type
                )
                if assessment_acadyear:
                    query = query.filter_by(assessment_acadyear=assessment_acadyear)
                
                assessment = query.first()
                
                if not assessment:
                    assessment = Assessment(
                        course_id=course.course_id,
                        assessment_type=assessment_type,
                        assessment_acadyear=assessment_acadyear,
                        created_by=user_id
                    )
                    db.session.add(assessment)
                    db.session.flush()
            
            # Handle image attachment
            attachment_id = None
            if 'image_filename' in df.columns and pd.notna(row.get('image_filename')):
                old_image_name = str(row['image_filename']).strip()
                
                # Check if image was uploaded in ZIP
                if old_image_name in image_mapping:
                    new_image_name = image_mapping[old_image_name]
                    
                    # Create attachment record
                    attachment = Attachment(
                        attachment_name=new_image_name,
                        attachment_type=Path(new_image_name).suffix[1:],  # e.g., 'png', 'jpg'
                    )
                    db.session.add(attachment)
                    db.session.flush()
                    attachment_id = attachment.attachment_id
                    images_attached += 1
                else:
                    print(f"⚠️  Warning: Image '{old_image_name}' referenced but not found in ZIP")
            
            # Create question
            question = Question(
                question_text=str(row['question_text']),
                question_type=str(row.get('question_type', '')).strip() if pd.notna(row.get('question_type')) else None,
                option_a=str(row.get('option_a', '')).strip() if pd.notna(row.get('option_a')) else None,
                option_b=str(row.get('option_b', '')).strip() if pd.notna(row.get('option_b')) else None,
                option_c=str(row.get('option_c', '')).strip() if pd.notna(row.get('option_c')) else None,
                option_d=str(row.get('option_d', '')).strip() if pd.notna(row.get('option_d')) else None,
                option_e=str(row.get('option_e', '')).strip() if pd.notna(row.get('option_e')) else None,
                correct_answer=str(row.get('correct_answer', '')).strip() if pd.notna(row.get('correct_answer')) else None,
                difficulty=str(row.get('difficulty', '')).strip() if pd.notna(row.get('difficulty')) else None,
                concepts=str(row.get('concepts', '')).strip() if pd.notna(row.get('concepts')) else None,
                course_id=course.course_id if course else None,
                assessment_id=assessment.assessment_id if assessment else None,
                attachment_id=attachment_id,
                created_by=user_id
            )
            
            db.session.add(question)
            
            # Update attachment with question_id if attachment exists
            if attachment_id:
                db.session.flush()  # Get question_id
                attachment = Attachment.query.get(attachment_id)
                attachment.question_id = question.question_id
            
            added_count += 1
        
        db.session.commit()
        
        # Cleanup temp directory if ZIP was used
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        response_data = {
            "message": "File uploaded successfully",
            "questions_added": added_count
        }
        
        if images_attached > 0:
            response_data["images_attached"] = images_attached
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": str(e)}), 500

# ============================================
# BROWSE QUESTIONS - "Shopping" for Questions
# ============================================

@app.route("/questions", methods=["GET"])
def get_questions():
    """
    Browse/search questions with filters
    
    Query parameters:
    - course_code: Filter by course (e.g., DSA1101)
    - difficulty: Filter by difficulty (Easy, Medium, Hard)
    - question_type: Filter by type (MCQ, T/F, Essay, etc.)
    - concepts: Search in concepts field (partial match)
    - assessment_type: Filter by assessment type
    - limit: Max results (default 20)
    - offset: Pagination offset (default 0)
    """
    course_code = request.args.get('course_code')
    difficulty = request.args.get('difficulty')
    question_type = request.args.get('question_type')
    concepts = request.args.get('concepts')
    assessment_type = request.args.get('assessment_type')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    # Build query
    query = Question.query
    
    # Filter by course
    if course_code:
        course = Course.query.filter_by(course_code=course_code).first()
        if course:
            query = query.filter(Question.course_id == course.course_id)
    
    # Filter by difficulty
    if difficulty:
        query = query.filter(Question.difficulty.ilike(f'%{difficulty}%'))
    
    # Filter by question type
    if question_type:
        query = query.filter(Question.question_type == question_type)
    
    # Filter by concepts (partial match)
    if concepts:
        query = query.filter(Question.concepts.ilike(f'%{concepts}%'))
    
    # Filter by assessment type
    if assessment_type:
        query = query.join(Assessment).filter(Assessment.assessment_type == assessment_type)
    
    # Execute query
    total_count = query.count()
    results = query.limit(limit).offset(offset).all()
    
    # Format response
    questions_data = []
    for q in results:
        # Get course info
        course = Course.query.get(q.course_id) if q.course_id else None
        
        # Get assessment info
        assessment = Assessment.query.get(q.assessment_id) if q.assessment_id else None
        
        # Get attachment info
        attachment = Attachment.query.get(q.attachment_id) if q.attachment_id else None
        
        question_dict = {
            "question_id": q.question_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "concepts": q.concepts,
            "correct_answer": q.correct_answer,
            "course_code": course.course_code if course else None,
            "assessment_type": assessment.assessment_type if assessment else None,
            "created_at": q.created_at.isoformat() if q.created_at else None
        }
        
        # Add MCQ options if applicable
        if q.question_type == "MCQ":
            question_dict["options"] = {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
                "E": q.option_e
            }
        
        # Add attachment URL if exists
        if attachment:
            question_dict["attachment_url"] = f"/attachments/{attachment.attachment_name}"
            question_dict["attachment_type"] = attachment.attachment_type
        
        questions_data.append(question_dict)
    
    return jsonify({
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "count": len(results),
        "questions": questions_data
    })

# ============================================
# GET QUESTIONS BY DIFFICULTY
# ============================================

@app.route("/questions/difficulty/<difficulty_level>", methods=["GET"])
def get_questions_by_difficulty(difficulty_level):
    """
    Get questions by difficulty level
    
    Path parameter:
    - difficulty_level: Easy, Medium, or Hard
    
    Query parameters:
    - course_code: Optional course filter
    - question_type: Optional type filter
    """
    course_code = request.args.get('course_code')
    question_type = request.args.get('question_type')
    
    query = Question.query.filter(Question.difficulty.ilike(f'%{difficulty_level}%'))
    
    if course_code:
        course = Course.query.filter_by(course_code=course_code).first()
        if course:
            query = query.filter(Question.course_id == course.course_id)
    
    if question_type:
        query = query.filter(Question.question_type == question_type)
    
    questions = query.all()
    
    return jsonify({
        "difficulty": difficulty_level,
        "count": len(questions),
        "questions": [
            {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "question_type": q.question_type,
                "concepts": q.concepts
            } for q in questions
        ]
    })

# ============================================
# GET QUESTIONS BY CONCEPT
# ============================================

@app.route("/questions/concept/<concept_name>", methods=["GET"])
def get_questions_by_concept(concept_name):
    """
    Browse questions by concept/tag
    
    Example: /questions/concept/probability
    """
    questions = Question.query.filter(
        Question.concepts.ilike(f'%{concept_name}%')
    ).all()
    
    return jsonify({
        "concept": concept_name,
        "count": len(questions),
        "questions": [
            {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "difficulty": q.difficulty,
                "question_type": q.question_type,
                "concepts": q.concepts
            } for q in questions
        ]
    })

# ============================================
# GET QUESTION DETAIL
# ============================================

@app.route("/questions/<int:question_id>", methods=["GET"])
def get_question_detail(question_id):
    """Get detailed information for a specific question"""
    question = Question.query.get(question_id)
    
    if not question:
        return jsonify({"error": "Question not found"}), 404
    
    # Get related data
    course = Course.query.get(question.course_id) if question.course_id else None
    assessment = Assessment.query.get(question.assessment_id) if question.assessment_id else None
    context = Context.query.get(question.context_id) if question.context_id else None
    attachment = Attachment.query.get(question.attachment_id) if question.attachment_id else None
    
    response_data = {
        "question_id": question.question_id,
        "question_text": question.question_text,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "correct_answer": question.correct_answer,
        "concepts": question.concepts,
        "course_code": course.course_code if course else None,
        "course_name": course.course_name if course else None,
        "assessment_type": assessment.assessment_type if assessment else None,
        "assessment_acadyear": assessment.assessment_acadyear if assessment else None,
        "version_number": question.version_number,
        "created_at": question.created_at.isoformat() if question.created_at else None
    }
    
    # Add MCQ options if applicable
    if question.question_type == "MCQ":
        response_data["options"] = {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d,
            "E": question.option_e
        }
    
    # Add context if exists
    if context:
        response_data["context"] = {
            "context_text": context.context_text,
            "context_attachment": context.context_attachment
        }
    
    # Add attachment if exists
    if attachment:
        response_data["attachment"] = {
            "attachment_name": attachment.attachment_name,
            "attachment_type": attachment.attachment_type,
            "attachment_url": f"/attachments/{attachment.attachment_name}"
        }
    
    return jsonify(response_data)

# ============================================
# GET ALL COURSES
# ============================================

@app.route("/courses", methods=["GET"])
def get_courses():
    """Get list of all courses with question counts"""
    courses = Course.query.all()
    
    courses_data = []
    for course in courses:
        question_count = Question.query.filter_by(course_id=course.course_id).count()
        courses_data.append({
            "course_id": course.course_id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "question_count": question_count
        })
    
    return jsonify({
        "courses": courses_data
    })

# ============================================
# GET ALL ASSESSMENTS
# ============================================

@app.route("/assessments", methods=["GET"])
def get_assessments():
    """Get list of all assessments"""
    course_code = request.args.get('course_code')
    
    query = Assessment.query
    
    if course_code:
        course = Course.query.filter_by(course_code=course_code).first()
        if course:
            query = query.filter(Assessment.course_id == course.course_id)
    
    assessments = query.all()
    
    assessments_data = []
    for assessment in assessments:
        course = Course.query.get(assessment.course_id) if assessment.course_id else None
        question_count = Question.query.filter_by(assessment_id=assessment.assessment_id).count()
        
        assessments_data.append({
            "assessment_id": assessment.assessment_id,
            "assessment_type": assessment.assessment_type,
            "assessment_acadyear": assessment.assessment_acadyear,
            "course_code": course.course_code if course else None,
            "question_count": question_count,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None
        })
    
    return jsonify({
        "assessments": assessments_data
    })

# ============================================
# SERVE ATTACHMENTS
# ============================================

@app.route("/attachments/<filename>")
def serve_attachment(filename):
    """Serve uploaded attachment files (images)"""
    return send_from_directory(STORAGE_FOLDER, filename)

# ============================================
# STATISTICS ENDPOINTS
# ============================================

@app.route("/stats", methods=["GET"])
def get_statistics():
    """Get overall statistics about the question bank"""
    total_questions = Question.query.count()
    total_courses = Course.query.count()
    total_assessments = Assessment.query.count()
    total_attachments = Attachment.query.count()
    
    # Count by difficulty
    difficulty_counts = {}
    for difficulty in ['Easy', 'Medium', 'Hard']:
        count = Question.query.filter(Question.difficulty.ilike(f'%{difficulty}%')).count()
        difficulty_counts[difficulty] = count
    
    # Count by question type
    question_types = db.session.query(
        Question.question_type,
        db.func.count(Question.question_id)
    ).group_by(Question.question_type).all()
    
    type_counts = {qt[0]: qt[1] for qt in question_types if qt[0]}
    
    return jsonify({
        "total_questions": total_questions,
        "total_courses": total_courses,
        "total_assessments": total_assessments,
        "total_attachments": total_attachments,
        "by_difficulty": difficulty_counts,
        "by_question_type": type_counts
    })

if __name__ == "__main__":
    print("✅ Quiz Bank API starting...")
    app.run(host="0.0.0.0", port=5000, debug=True)