"""
API routes for Questions
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from sqlalchemy.orm import Session
from sqlalchemy import text 
from typing import Optional, List, Dict, Any, Tuple
from rapidfuzz import fuzz
from difflib import HtmlDiff, unified_diff, SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.db import get_db
from app.utils.file_parser import parse_csv, parse_csv_for_version
from app.utils.validation import validate_question_data
from pathlib import Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
import psycopg2
import shutil
import subprocess
import pandas as pd 
import io
import os
import zipfile
import csv
import tempfile
from datetime import datetime


router = APIRouter()

# API #1: Filtered Questions Retrieval
@router.get("/")
async def get_questions(
    id: Optional[int] = Query(None, description="Filter by question ID"),
    subject: Optional[str] = Query(None, description="Filter by subject/course"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    type: Optional[str] = Query(None, description="Filter by question type"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    topic: Optional[str] = Query(None, description="Filter by one or more topics"),
    match: Optional[str] = Query("all", description="Match mode: 'any' (OR) or 'all' (AND) across all filters"),
    fuzzy: Optional[bool] = Query(True, description="Enable fuzzy matching for topic keywords"),
    is_latest: Optional[bool] = Query(None, description="Only return latest versions"), ## changed from True to None
    db: Session = Depends(get_db)
):
    """
    GET /api/questions
    Returns all questions with flexible filtering.

    Example:
    - ?difficulty=low&subject=dsa1101&match=all → Intersection (AND)
    - ?difficulty=low&subject=dsa1101&match=any → Union (OR)
    - ?topic=regression,data manipulation&match=any → Any topic (OR fuzzy match)
    """

    try:
        # Base query and parameter dict
        query_str = """
            SELECT 
                q.question_id, 
                q.question_text, 
                q.question_type,
                c.course_code, 
                c.course_name, 
                a.assessment_type, 
                q.difficulty, 
                q.concepts, 
                q.created_at, 
                q.version_number,
                q.original_id,
                q.is_latest
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            WHERE 1=1
        """
        params = {}
        conditions = []

        # --- ID Filter ---
        if id is not None:
            conditions.append("q.question_id = :id")
            params["id"] = id

        # --- Subject / Course Filter ---
        if subject is not None:
            conditions.append("(c.course_code ILIKE :subject OR c.course_name ILIKE :subject)")
            params["subject"] = f"%{subject}%"

        # --- Difficulty Filter ---
        if difficulty is not None:
            conditions.append("q.difficulty = :difficulty")
            params["difficulty"] = difficulty

        # --- Question Type Filter ---
        if type is not None:
            conditions.append("q.question_type =:question_type")
            params["question_type"] = type

        # --- Semester Filter ---
        if semester is not None:
            conditions.append("a.assessment_type ILIKE :semester")
            params["semester"] = f"%{semester}%"

        # --- Latest Version Filter ---

        if is_latest is True:
            conditions.append("q.is_latest = TRUE")
        elif is_latest is False:
            conditions.append("q.is_latest = FALSE")


        # --- Combine Conditions: AND vs OR ---
        if conditions:
            if match == "any":
                query_str += " AND (" + " OR ".join(conditions) + ")"
            else:
                query_str += " AND " + " AND ".join(conditions)

        # --- Execute base query first ---
        base_results = db.execute(text(query_str), params).fetchall()

        # --- Handle Topics (with optional fuzzy match) ---
        if topic:
            topics = [t.strip().lower() for t in topic.split(",") if t.strip()]
            filtered_rows = []

            for row in base_results:
                question_topics = [t.strip().lower() for t in (row.concepts.split(",") if row.concepts else [])]

                topic_matches = []
                for user_topic in topics:
                    if fuzzy:
                        # Fuzzy partial ratio threshold = 70
                        match_found = any(fuzz.partial_ratio(user_topic, qt) > 70 for qt in question_topics)
                    else:
                        match_found = any(user_topic in qt for qt in question_topics)
                    topic_matches.append(match_found)

                # Apply topic match logic
                if (match == "all" and all(topic_matches)) or (match != "all" and any(topic_matches)):
                    filtered_rows.append(row)
        else:
            filtered_rows = base_results

        # --- Format output ---
        questions = []
        for row in filtered_rows:
            questions.append({
                "question_id": row.question_id,
                "question_text": row.question_text,
                "question_type": row.question_type,
                "course_code": row.course_code,
                "course_name": row.course_name,
                "assessment_type": row.assessment_type,
                "difficulty": row.difficulty,
                "concepts": row.concepts.split(',') if row.concepts else [],
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "version_number": row.version_number,
                "original_id": row.original_id,
                "is_latest": row.is_latest
            })

        return {
            "success": True,
            "count": len(questions),
            "data": questions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# API #2: More Question Details
@router.get("/{id}")
async def get_question_by_id(id: int, db: Session = Depends(get_db)):
    """
    GET /api/questions/:id
    Returns full question content with context and attachments
    """
    try: 
        query = text("""
            SELECT 
                q.*,
                c.course_code,
                c.course_name,
                a.assessment_type,
                ctx.context_text,
                ctx.context_attachment,
                STRING_AGG(DISTINCT att_q.attachment_name, ', ') as question_attachments,
                STRING_AGG(DISTINCT att_ctx.attachment_name, ', ') as context_attachments
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN contexts ctx ON q.context_id = ctx.context_id
            LEFT JOIN attachments att_q ON q.question_id = att_q.question_id
            LEFT JOIN attachments att_ctx ON ctx.context_id = att_ctx.context_id
            WHERE q.question_id = :id
            GROUP BY q.question_id, c.course_code, c.course_name, a.assessment_type, 
                     ctx.context_text, ctx.context_attachment
        """)
    
        result = db.execute(query, {"id": id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Build clean response
        response_data = {
            "question_id": row.question_id,
            "question_number": row.question_number,
            "sub_question_number": row.sub_question_number,
            "question_text": row.question_text,
            "question_type": row.question_type,
            "difficulty": row.difficulty,
            "correct_answer": row.correct_answer,
            "explanation": row.explanation,
            "points": float(row.points) if row.points else 1.0,
            "concepts": row.concepts.split(',') if row.concepts else [],
            "course_code": row.course_code,
            "course_name": row.course_name,
            "assessment_type": row.assessment_type,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "version_number": row.version_number,
            "previous_version_id": row.previous_version_id
        }
        
        # Add options based on question type
        if row.question_type in ["MCQ", "MRQ"]:
            options = {}
            if row.option_a:
                options["A"] = row.option_a
            if row.option_b:
                options["B"] = row.option_b
            if row.option_c:
                options["C"] = row.option_c
            if row.option_d:
                options["D"] = row.option_d
            if row.option_e:
                options["E"] = row.option_e
            if options:
                response_data["options"] = options
        
        elif row.question_type == "T/F":
            response_data["options"] = {
                "A": row.option_a if row.option_a else "True",
                "B": row.option_b if row.option_b else "False"
            }
        
        # Add context (shared across multiple questions)
        if row.context_text or row.context_attachment or row.context_attachments:
            context = {}
            
            if row.context_text:
                context["text"] = row.context_text
            
            # Context attachments (images/files for the context)
            context_files = []
            
            # From context_attachment column
            if row.context_attachment:
                context_files.append({
                    "name": row.context_attachment,
                    "url": f"/api/attachments/{row.context_attachment}"
                })
            
            if context_files:
                context["attachments"] = context_files
            
            if context:
                response_data["context"] = context
        
        # Add question-specific attachments

        if row.question_attachments:
            question_files = []
            for name in row.question_attachments.split(', '):
                if name.strip():
                    question_files.append({
                        "name": name.strip(),
                        "url": f"/api/attachments/{name.strip()}"
                    })
            if question_files:
                response_data["attachments"] = question_files
        
        return {
            "success": True,
            "data": response_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# API #3: Fetching ALL Versions
@router.get("/{id}/versions")
async def get_question_versions(id: int, db: Session = Depends(get_db)):
    """
    GET /api/questions/{id}/versions

    Retrieve all related versions of the selected question — including:
    - The original (root) question
    - All descendant versions (direct + indirect)
    - Any sibling/branched versions derived from the same parent

    Returns:
    - question_id, question_text, version_number, previous_version_id, is_latest
    - course_code, course_name, assessment_type, difficulty, concepts
    - created_at (ISO format)
    
    Used in: QuestionDetails
    """

    try:
        # Find the "root" question (the start of the version chain)
        root_query = text("""
            SELECT question_id, previous_version_id
            FROM questions
            WHERE question_id = :id
        """)
        result = db.execute(root_query, {"id": id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Question not found")

        root_id = row.previous_version_id if row.previous_version_id else row.question_id

        # Recursive CTE to fetch *all versions* in the lineage
        versions_query = text("""
            WITH RECURSIVE version_tree AS (
                SELECT * FROM questions WHERE question_id = :root_id
                UNION ALL
                SELECT q.*
                FROM questions q
                INNER JOIN version_tree vt ON q.previous_version_id = vt.question_id
            )
            SELECT
                vt.question_id,
                vt.question_text,
                vt.question_type,
                vt.version_number,
                vt.previous_version_id,
                vt.is_latest,
                vt.difficulty,
                vt.concepts,
                vt.created_at,
                c.course_code,
                c.course_name,
                a.assessment_type
            FROM version_tree vt
            LEFT JOIN courses c ON vt.course_id = c.course_id
            LEFT JOIN assessments a ON vt.assessment_id = a.assessment_id
            ORDER BY vt.version_number ASC, vt.created_at ASC
        """)

        result = db.execute(versions_query, {"root_id": root_id})
        rows = result.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No versions found")

        # Format the response
        versions = []
        for row in rows:
            versions.append({
                "question_id": row.question_id,
                "question_text": row.question_text or "",
                "question_type": row.question_type or "",
                "course_code": row.course_code or "",
                "course_name": row.course_name or "",
                "assessment_type": row.assessment_type or "",
                "difficulty": row.difficulty or "",
                "concepts": row.concepts.split(',') if row.concepts else [],
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "version_number": row.version_number,
                "previous_version_id": row.previous_version_id,
                "is_latest": row.is_latest
            })

        return {
            "success": True,
            "root_id": root_id,
            "version_count": len(versions),
            "data": versions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# API #4: Uploading new question version
@router.post("/{id}/editversion")
async def upload_new_version(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    POST /api/questions/{id}/editversion

    Upload a new CSV file containing edited question data to create a new version.
    - Increments version_number
    - Links to previous version via previous_version_id
    - Marks old version's is_latest = FALSE
    - Creates a new row for each question (preserving history)
    """
    try:
        # ===== STEP 0: Validate file =====
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        contents = await file.read()

        # ===== STEP 1: Find the parent question =====
        current_query = text("""
            SELECT question_id, course_id, assessment_id, version_number, is_latest
            FROM questions
            WHERE question_id = :id
        """)
        result = db.execute(current_query, {"id": id})
        current = result.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail=f"Parent question (ID={id}) not found")

        # ===== STEP 2: Parse CSV =====
        df = None
        for enc in ['utf-8', 'latin1', 'iso-8859-1', 'windows-1252', 'cp1252']:
            try:
                df = pd.read_csv(io.BytesIO(contents), encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise HTTPException(status_code=400, detail="Unable to decode CSV file")

        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        questions_data = df.to_dict(orient="records")

        if len(questions_data) != 1:
            raise HTTPException(status_code=400, detail="Edit version file must contain exactly ONE question")

        question_data = questions_data[0]

        # ===== STEP 3: Validate data =====
        validation_errors = validate_question_data(question_data)
        if validation_errors:
            raise HTTPException(status_code=400, detail={"errors": validation_errors})

        # ===== STEP 4: Lookup course and assessment =====
        # (Reuse parent if not provided)
        course_id = current.course_id
        assessment_id = current.assessment_id

        if question_data.get("course_code"):
            course_result = db.execute(
                text("SELECT course_id FROM courses WHERE course_code = :code"),
                {"code": question_data.get("course_code")}
            ).fetchone()
            if course_result:
                course_id = course_result.course_id

        if question_data.get("assessment_type"):
            assess_result = db.execute(
                text("SELECT assessment_id FROM assessments WHERE assessment_type = :atype"),
                {"atype": question_data.get("assessment_type")}
            ).fetchone()
            if assess_result:
                assessment_id = assess_result.assessment_id

        # ===== STEP 5: Save CSV file to /quizbank-db/db-init/data =====
        data_dir = Path(__file__).parent.parent.parent.parent / "quizbank-db" / "db-init" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Rename file to include version info for traceability
        versioned_filename = f"question_{id}_v{current.version_number + 1}_{file.filename}"
        dest_file_path = data_dir / versioned_filename

        if dest_file_path.exists():
            raise HTTPException(status_code=400, detail=f"File {versioned_filename} already exists")

        with open(dest_file_path, "wb") as f:
            f.write(contents)

        # ===== STEP 6: Update parent is_latest to FALSE =====
        db.execute(
            text("UPDATE questions SET is_latest = FALSE WHERE question_id = :id"),
            {"id": id}
        )

        # ===== STEP 7: Prepare insert query for new version =====
        insert_fields = [
            "question_text", "difficulty", "concepts",
            "course_id", "assessment_id",
            "version_number", "previous_version_id", "is_latest"
        ]
        insert_values = [
            ":question_text", ":difficulty", ":concepts",
            ":course_id", ":assessment_id",
            ":version_number", ":previous_version_id", "TRUE"
        ]
        params = {
            "question_text": question_data.get("question_text"),
            "difficulty": question_data.get("difficulty"),
            "concepts": question_data.get("concepts"),
            "course_id": course_id,
            "assessment_id": assessment_id,
            "version_number": current.version_number + 1,
            "previous_version_id": id
        }

        # Optional fields (same pattern as API #5)
        for field in [
            "correct_answer", "option_a", "option_b", "option_c", "option_d", "option_e",
            "explanation", "points", "question_number", "sub_question_number", "question_type", "context"
        ]:
            if question_data.get(field) is not None:
                insert_fields.append(field)
                insert_values.append(f":{field}")
                params[field] = question_data.get(field)

        insert_query = text(f"""
            INSERT INTO questions ({', '.join(insert_fields)})
            VALUES ({', '.join(insert_values)})
            RETURNING question_id
        """)

        result = db.execute(insert_query, params)
        new_id = result.fetchone()[0]

        db.commit()

        return {
            "success": True,
            "message": "New version created successfully",
            "previous_question_id": id,
            "new_question_id": new_id,
            "new_version_number": current.version_number + 1
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



# API #5: Uploading a NEW Quiz/Question
# Configuration
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STORAGE_PNG_PATH = BACKEND_ROOT / "quizbank-db" / "storage" / "png"
UPLOADS_BASE_PATH = BACKEND_ROOT / "quizbank-db" / "uploads"
INGEST_SCRIPT = BACKEND_ROOT / "quizbank-db" / "scripts" / "ingest_uploads.sh"

# Ensure directories exist
STORAGE_PNG_PATH.mkdir(parents=True, exist_ok=True)
UPLOADS_BASE_PATH.mkdir(parents=True, exist_ok=True)

# Database connection helper
def get_db_connection():
    """Get database connection - adjust credentials as needed"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "quizbank"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

# Pydantic models
class QuestionPreview(BaseModel):
    question_number: Optional[int]
    sub_question_number: Optional[int]
    question_text: str
    question_type: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    option_e: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    points: Optional[float] = None
    difficulty: str
    concepts: str
    attachment: Optional[str] = None
    context_id: Optional[str] = None

class ContextPreview(BaseModel):
    context_id: str
    context_text: str
    attachment: Optional[str] = None

class UploadPreviewResponse(BaseModel):
    upload_id: str
    questions: List[QuestionPreview]
    contexts: List[ContextPreview]
    attachments: List[str]
    course_code: Optional[str] = None
    assessment_type: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None

class ConfirmUploadRequest(BaseModel):
    upload_id: str
    course_code: str
    assessment_type: str
    academic_year: Optional[str] = None
    semester: Optional[str] = None

# Temporary storage for pending uploads
pending_uploads: Dict[str, Dict] = {}

def parse_csv_to_dict(csv_path: Path) -> List[Dict]:
    """Parse CSV file and return list of dictionaries"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def validate_questions_csv(questions: List[Dict]) -> Tuple[bool, Optional[str]]:
    """Validate questions CSV data"""
    required_fields = ['Question Text', 'Question Type', 'Difficulty', 'Concepts']
    
    for idx, q in enumerate(questions, 1):
        for field in required_fields:
            if field not in q or not q[field].strip():
                return False, f"Row {idx}: Missing required field '{field}'"
        
        # If Question Number is present, it must be valid
        if 'Question Number' in q and q['Question Number'].strip():
            try:
                int(q['Question Number'])
            except ValueError:
                return False, f"Row {idx}: Invalid Question Number"
    
    return True, None

def validate_context_csv(contexts: List[Dict]) -> Tuple[bool, Optional[str]]:
    """Validate context CSV data"""
    for idx, ctx in enumerate(contexts, 1):
        context_id = ctx.get('Context ID', '').strip()
        context_text = ctx.get('Context Text', '').strip()
        
        # If Context ID is present, Context Text must be present and vice versa
        if bool(context_id) != bool(context_text):
            return False, f"Row {idx}: Context ID and Context Text must both be present or both be absent"
        
        if context_id:
            try:
                int(context_id)
            except ValueError:
                return False, f"Row {idx}: Context ID must be an integer"
    
    return True, None

def extract_metadata_from_filename(filename: str) -> Dict[str, Optional[str]]:
    """Extract course code, assessment type, etc. from filename"""
    # Example: DSA1101_Sem1_2425_Midterm_questions.csv
    parts = filename.replace('.csv', '').split('_')
    
    metadata = {
        'course_code': None,
        'assessment_type': None,
        'academic_year': None,
        'semester': None
    }
    
    if len(parts) >= 1:
        metadata['course_code'] = parts[0]
    
    # Look for semester pattern
    for part in parts:
        if part.lower().startswith('sem'):
            metadata['semester'] = part
    
    # Look for academic year (e.g., 2425)
    for part in parts:
        if part.isdigit() and len(part) == 4:
            metadata['academic_year'] = f"20{part[:2]}/20{part[2:]}"
    
    # Assessment type is usually the part before 'questions' or 'context'
    for i, part in enumerate(parts):
        if part.lower() in ['questions', 'context']:
            if i > 0:
                metadata['assessment_type'] = parts[i-1]
            break
    
    return metadata

@router.post("/upload", response_model=UploadPreviewResponse)
async def upload_assessment(file: UploadFile = File(...)):
    """
    Step 1-3: Upload CSV or ZIP, parse files, return preview
    """
    upload_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Save uploaded file
        file_path = temp_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        questions_data = []
        contexts_data = []
        attachments = []
        questions_csv_path = None
        context_csv_path = None
        metadata = {}
        
        # Handle ZIP file
        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find CSV files
            for csv_file in temp_dir.rglob('*.csv'):
                if 'questions' in csv_file.name.lower():
                    questions_csv_path = csv_file
                    metadata = extract_metadata_from_filename(csv_file.name)
                elif 'context' in csv_file.name.lower():
                    context_csv_path = csv_file
            
            # Find attachments
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.pdf', '*.r', '*.R']:
                attachments.extend([f.name for f in temp_dir.rglob(ext)])
        
        # Handle single CSV file
        elif file.filename.endswith('.csv'):
            if 'questions' not in file.filename.lower():
                raise HTTPException(
                    status_code=400, 
                    detail="Single CSV file must be questions.csv"
                )
            questions_csv_path = file_path
            metadata = extract_metadata_from_filename(file.filename)
        else:
            raise HTTPException(
                status_code=400,
                detail="File must be CSV or ZIP"
            )
        
        # Validate questions CSV exists
        if not questions_csv_path or not questions_csv_path.exists():
            raise HTTPException(
                status_code=400,
                detail="questions.csv not found in upload"
            )
        
        # Parse questions CSV
        questions_data = parse_csv_to_dict(questions_csv_path)
        is_valid, error_msg = validate_questions_csv(questions_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid questions.csv: {error_msg}")
        
        # Parse context CSV if exists
        if context_csv_path and context_csv_path.exists():
            contexts_data = parse_csv_to_dict(context_csv_path)
            is_valid, error_msg = validate_context_csv(contexts_data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid context.csv: {error_msg}")
        
        # Convert to preview models
        questions_preview = [
            QuestionPreview(
                question_number=int(q.get('Question Number', 0)) if q.get('Question Number', '').strip() else None,
                sub_question_number=int(q.get('Sub-Question Number', 0)) if q.get('Sub-Question Number', '').strip() else None,
                question_text=q['Question Text'],
                question_type=q['Question Type'],
                option_a=q.get('Option A') or None,
                option_b=q.get('Option B') or None,
                option_c=q.get('Option C') or None,
                option_d=q.get('Option D') or None,
                option_e=q.get('Option E') or None,
                correct_answer=q.get('Correct Answer') or None,
                explanation=q.get('Explanation') or None,
                points=float(q['Points']) if q.get('Points', '').strip() else None,
                difficulty=q['Difficulty'],
                concepts=q['Concepts'],
                attachment=q.get('Attachment') or None,
                context_id=q.get('Context ID') or None
            )
            for q in questions_data
        ]
        
        contexts_preview = [
            ContextPreview(
                context_id=c['Context ID'],
                context_text=c['Context Text'],
                attachment=c.get('Attachment') or None
            )
            for c in contexts_data
            if c.get('Context ID', '').strip()
        ]
        
        # Store in temporary cache
        pending_uploads[upload_id] = {
            'temp_dir': str(temp_dir),
            'questions_data': questions_data,
            'contexts_data': contexts_data,
            'attachments': attachments,
            'metadata': metadata
        }
        
        return UploadPreviewResponse(
            upload_id=upload_id,
            questions=questions_preview,
            contexts=contexts_preview,
            attachments=attachments,
            course_code=metadata.get('course_code'),
            assessment_type=metadata.get('assessment_type'),
            academic_year=metadata.get('academic_year'),
            semester=metadata.get('semester')
        )
    
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm-upload")
async def confirm_upload(request: ConfirmUploadRequest):
    """
    Step 4-9: Process confirmed upload, map data, store in DB, backup
    """
    if request.upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail="Upload not found or expired")
    
    upload_data = pending_uploads[request.upload_id]
    temp_dir = Path(upload_data['temp_dir'])
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get or create course
        cur.execute(
            "SELECT course_id FROM courses WHERE course_code = %s",
            (request.course_code,)
        )
        course_result = cur.fetchone()
        
        if course_result:
            course_id = course_result['course_id']
        else:
            cur.execute(
                "INSERT INTO courses (course_code, course_name) VALUES (%s, %s) RETURNING course_id",
                (request.course_code, request.course_code)  # Use course_code as name if not provided
            )
            course_id = cur.fetchone()['course_id']
        
        # Create assessment
        cur.execute(
            """
            INSERT INTO assessments (course_id, assessment_type, assessment_acadyear, assessment_semester)
            VALUES (%s, %s, %s, %s)
            RETURNING assessment_id
            """,
            (course_id, request.assessment_type, request.academic_year, request.semester)
        )
        assessment_id = cur.fetchone()['assessment_id']
        
        # Map contexts
        context_map = {}  # Maps local context_id to DB context_id
        
        for ctx in upload_data['contexts_data']:
            context_local_id = ctx.get('Context ID', '').strip()
            if not context_local_id:
                continue
            
            cur.execute(
                """
                INSERT INTO contexts (assessment_id, course_id, context_local_id, context_text)
                VALUES (%s, %s, %s, %s)
                RETURNING context_id
                """,
                (assessment_id, course_id, context_local_id, ctx['Context Text'])
            )
            db_context_id = cur.fetchone()['context_id']
            context_map[context_local_id] = db_context_id
            
            # Handle context attachments
            attachment_str = ctx.get('Attachment', '').strip()
            if attachment_str:
                attachment_names = [a.strip() for a in attachment_str.split(',')]
                for att_name in attachment_names:
                    cur.execute(
                        """
                        INSERT INTO context_attachments (context_id, attachment_name, attachment_url)
                        VALUES (%s, %s, %s)
                        """,
                        (db_context_id, att_name, f"/storage/png/{att_name}")
                    )
        
        # Insert questions
        for q in upload_data['questions_data']:
            context_local_id = q.get('Context ID', '').strip()
            db_context_id = context_map.get(context_local_id) if context_local_id else None
            
            cur.execute(
                """
                INSERT INTO questions (
                    assessment_id, course_id, context_id, question_number, sub_question_number,
                    question_text, question_type, option_a, option_b, option_c, option_d, option_e,
                    correct_answer, explanation, points, difficulty, concepts
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING question_id
                """,
                (
                    assessment_id, course_id, db_context_id,
                    int(q['Question Number']) if q.get('Question Number', '').strip() else None,
                    int(q['Sub-Question Number']) if q.get('Sub-Question Number', '').strip() else None,
                    q['Question Text'], q['Question Type'],
                    q.get('Option A') or None, q.get('Option B') or None,
                    q.get('Option C') or None, q.get('Option D') or None, q.get('Option E') or None,
                    q.get('Correct Answer') or None, q.get('Explanation') or None,
                    float(q['Points']) if q.get('Points', '').strip() else None,
                    q['Difficulty'], q['Concepts']
                )
            )
            question_id = cur.fetchone()['question_id']
            
            # Handle question attachments
            attachment_str = q.get('Attachment', '').strip()
            if attachment_str:
                attachment_names = [a.strip() for a in attachment_str.split(',')]
                for att_name in attachment_names:
                    cur.execute(
                        """
                        INSERT INTO question_attachments (question_id, attachment_name, attachment_url)
                        VALUES (%s, %s, %s)
                        """,
                        (question_id, att_name, f"/storage/png/{att_name}")
                    )
        
        conn.commit()
        
        # Copy attachments to storage
        for attachment in upload_data['attachments']:
            for src_file in temp_dir.rglob(attachment):
                dest_file = STORAGE_PNG_PATH / attachment
                shutil.copy2(src_file, dest_file)
                break
        
        # Create dated upload folder for ingest script
        dated_folder = UPLOADS_BASE_PATH / datetime.now().strftime("%Y-%m-%d_%H%M%S")
        dated_folder.mkdir(parents=True, exist_ok=True)
        
        # Copy CSV files to dated folder
        for csv_file in temp_dir.rglob('*.csv'):
            shutil.copy2(csv_file, dated_folder / csv_file.name)
        
        # Copy attachments to dated folder
        if upload_data['attachments']:
            images_dir = dated_folder / "images"
            images_dir.mkdir(exist_ok=True)
            for attachment in upload_data['attachments']:
                for src_file in temp_dir.rglob(attachment):
                    shutil.copy2(src_file, images_dir / attachment)
                    break
        
        # Run backup via ingest script if it exists
        if INGEST_SCRIPT.exists():
            try:
                subprocess.run(
                    [str(INGEST_SCRIPT), str(dated_folder)],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Warning: Backup script failed: {e.stderr}")
        
        # Cleanup
        cur.close()
        conn.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
        del pending_uploads[request.upload_id]
        
        return JSONResponse(content={
            "message": "Upload successful",
            "assessment_id": assessment_id,
            "course_id": course_id
        })
    
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cancel-upload/{upload_id}")
async def cancel_upload(upload_id: str):
    """Cancel a pending upload and cleanup temporary files"""
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    upload_data = pending_uploads[upload_id]
    temp_dir = Path(upload_data['temp_dir'])
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    del pending_uploads[upload_id]
    
    return JSONResponse(content={"message": "Upload cancelled"})

# API #6: Version Diff 
def highlight_changes(old_text: str, new_text: str) -> Dict[str, str]:
    """Generate inline highlighted HTML showing additions and deletions"""
    if old_text == new_text:
        return None
    
    # If texts are too different (less than 30% similarity), show them separately without char-by-char diff
    similarity = SequenceMatcher(None, old_text, new_text).ratio()
    
    if similarity < 0.3:  # Less than 30% similar - show full replacement
        return {
            "previous": f'<span style="background-color: #ffc0c0; text-decoration: line-through;">{old_text}</span>' if old_text else "",
            "current": f'<span style="background-color: #c0ffc0; font-weight: bold;">{new_text}</span>' if new_text else "",
            "type": "complete_change"
        }
    
    # For similar texts, do word-level diff instead of character-level
    old_words = old_text.split()
    new_words = new_text.split()
    
    s = SequenceMatcher(None, old_words, new_words)
    old_html = []
    new_html = []
    
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        old_chunk = ' '.join(old_words[i1:i2])
        new_chunk = ' '.join(new_words[j1:j2])
        
        if tag == 'equal':
            old_html.append(old_chunk)
            new_html.append(new_chunk)
        elif tag == 'delete':
            old_html.append(f'<span style="background-color: #ffc0c0; text-decoration: line-through;">{old_chunk}</span>')
        elif tag == 'insert':
            new_html.append(f'<span style="background-color: #c0ffc0; font-weight: bold;">{new_chunk}</span>')
        elif tag == 'replace':
            old_html.append(f'<span style="background-color: #ffc0c0; text-decoration: line-through;">{old_chunk}</span>')
            new_html.append(f'<span style="background-color: #c0ffc0; font-weight: bold;">{new_chunk}</span>')
        
        # Add space between words
        if tag != 'equal' and i2 < len(old_words):
            old_html.append(' ')
        if tag != 'equal' and j2 < len(new_words):
            new_html.append(' ')
    
    return {
        "previous": ''.join(old_html),
        "current": ''.join(new_html),
        "type": "partial_change"
    }


# Update your API endpoint
@router.get("/{id}/diff/{version_id}")
async def get_question_diff(id: int, version_id: int, db: Session = Depends(get_db)):
    """
    Compare two versions of a question and return user-friendly colored differences.
    """
    
    # Fetch both versions
    query = text("SELECT * FROM questions WHERE question_id IN (:id, :version_id)")
    result = db.execute(query, {"id": id, "version_id": version_id}).fetchall()
    
    if len(result) < 2:
        raise HTTPException(status_code=404, detail="One or both question versions not found")

    current = dict(result[0]._mapping)
    previous = dict(result[1]._mapping)
    
    if current["version_number"] < previous["version_number"]:
        current, previous = previous, current

    fields_to_compare = {
        "question_text": "Question Text",
        "option_a": "Option A",
        "option_b": "Option B",
        "option_c": "Option C",
        "option_d": "Option D",
        "option_e": "Option E",
        "correct_answer": "Correct Answer",
        "difficulty": "Difficulty",
        "concepts": "Concepts"
    }

    differences = []

    for field, label in fields_to_compare.items():
        old_val = str(previous.get(field) or "")
        new_val = str(current.get(field) or "")
        
        if old_val != new_val:
            diff = highlight_changes(old_val, new_val)
            if diff:
                differences.append({
                    "field": label,
                    "field_key": field,
                    "previous": diff["previous"],
                    "current": diff["current"],
                    "change_type": diff.get("type", "partial_change")
                })

    return {
        "success": True,
        "question_id": id,
        "version_number": current.get("version_number"),
        "compared_to": version_id,
        "compared_version": previous.get("version_number"),
        "differences": differences
    }


# API #7: Suggest Question Variants by semantic similarity
@router.get("/{id}/suggestions")
async def get_question_suggestions(id: int, db: Session = Depends(get_db), top_n: int = 5):
    """
    Suggest variant questions based on semantic similarity (TF-IDF).

    GET /api/questions/{id}/suggestions
    """
    # Fetch all questions
    result = db.execute(text("SELECT question_id, question_text, concepts FROM questions"))
    questions = result.fetchall()

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found in database")

    # Build lists
    ids = [q.question_id for q in questions]
    texts = [
        (q.question_text or "") + " " + (q.concepts or "")
        for q in questions
    ]

    if id not in ids:
        raise HTTPException(status_code=404, detail="Question not found")

    idx = ids.index(id)

    # Compute TF-IDF similarity
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(texts)
    similarities = cosine_similarity(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()

    # Get top N most similar (excluding itself)
    similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
    suggestions = [
        {"question_id": int(ids[i]), "similarity": round(float(similarities[i]), 3)}
        for i in similar_indices
    ]

    return {
        "success": True,
        "question_id": id,
        "suggested_variants": suggestions
    }



