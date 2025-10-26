"""
API routes for Questions - Updated for New DB Schema
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
from pathlib import Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil
import pandas as pd 
import io
import os
import zipfile
import csv
import tempfile
from datetime import datetime
import logging
import re
import unicodedata

# Setup logging once
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration (declared once)
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STORAGE_PNG_PATH = BACKEND_ROOT / "quizbank-db" / "storage" / "png"
UPLOADS_BASE_PATH = BACKEND_ROOT / "quizbank-db" / "uploads"

# Ensure directories exist
STORAGE_PNG_PATH.mkdir(parents=True, exist_ok=True)
UPLOADS_BASE_PATH.mkdir(parents=True, exist_ok=True)

# Create router once
router = APIRouter()

# Import DB connection
try:
    from app.db.connection import SessionLocal
except ImportError:
    logger.warning("Could not import SessionLocal - DB operations will fail")
    SessionLocal = None

# Filename parsing regex
FNAME_RE = re.compile(
    r"""
    ^
    (?P<course>[A-Za-z]{2,}\d{4})         # DSA1101 / ST2131 / IND5003
    (?:_Sem(?P<sem>\d))?                  # optional _Sem1
    (?:_(?P<acad>\d{4}))?                 # optional _2425
    _(?P<title>.+)                        # title can contain underscores
    _(?P<kind>context|contexts|questions) # file kind
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

_WS = re.compile(r"\s+", flags=re.UNICODE)

# Helper functions
def _clean_header(s: str) -> str:
    """Unicode normalize, lowercase, replace whitespace/dashes with underscores"""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\ufeff", "").replace("\u200b", "")
    s = s.lower()
    s = _WS.sub("_", s.strip())
    s = s.replace("-", "_")
    s = re.sub(r"_+", "_", s)
    return s

def normalise_keys(row: dict) -> dict:
    """Lower/underscore keys using unicode-aware normalization"""
    out = {}
    for k, v in row.items():
        if k is None:
            continue
        nk = _clean_header(str(k))
        out[nk] = v
        out[k] = v
    return out

def G(row: dict, *candidates, default: str = "") -> str:
    """Get value from row using multiple candidate keys"""
    n = normalise_keys(row)
    for key in candidates:
        if key in n and n[key] not in (None, ""):
            return str(n[key])
        ck = _clean_header(str(key))
        if ck in n and n[ck] not in (None, ""):
            return str(n[ck])
    return default

def read_csv_rows(path: Path) -> list[dict]:
    """Robust CSV reader"""
    b = path.read_bytes()
    try:
        s = b.decode("utf-8-sig")
    except UnicodeDecodeError:
        s = b.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(s)))

def parse_meta_from_filename(pathlike) -> Optional[Tuple[str, str, str, Optional[str], Optional[str]]]:
    """Return (course_code, assessment_type, kind, acadyear, semester)."""
    name = pathlike.name if hasattr(pathlike, "name") else str(pathlike)
    stem = name[:-4] if name.lower().endswith(".csv") else name

    m = FNAME_RE.match(stem)
    if not m:
        return None

    course = m.group("course").upper().strip()
    title = m.group("title").strip()
    kind = m.group("kind").lower()
    ay = m.group("acad") or None
    sem = m.group("sem") or None

    norm_kind = "contexts" if "context" in kind else "questions"
    return (course, title, norm_kind, ay, sem)

# Pydantic models for API #5
class QuestionPreview(BaseModel):
    question_number: Optional[int] = None
    sub_question_number: Optional[int] = None
    question_text: str
    question_type: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    option_e: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    points: Optional[float] = None
    difficulty: Optional[str] = None
    concepts: Optional[str] = None
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
    debug_info: Optional[Dict] = None

class ConfirmUploadRequest(BaseModel):
    upload_id: str

class ConfirmUploadResponse(BaseModel):
    success: bool
    message: str
    upload_id: str
    questions_inserted: int
    contexts_inserted: int
    attachments_copied: int

class CancelUploadRequest(BaseModel):
    upload_id: str

class CancelUploadResponse(BaseModel):
    success: bool
    message: str
    upload_id: str

# Temporary storage for pending uploads
pending_uploads: Dict[str, Dict] = {}

# Validation helpers
def validate_questions_data(rows: List[dict]) -> Tuple[bool, Optional[str]]:
    """Validate questions"""
    if not rows:
        return False, "No question rows found"
    
    for idx, r in enumerate(rows, 1):
        qtext = (G(r, "Question Text", "question_text") or "").strip()
        if not qtext:
            return False, f"Row {idx}: Missing Question Text"
        
        qnum = (G(r, "Question Number", "question_number") or "").strip()
        if qnum:
            try:
                int(qnum)
            except ValueError:
                return False, f"Row {idx}: Invalid Question Number '{qnum}'"
        
        sqnum = (G(r, "Sub-Question Number", "sub_question_number") or "").strip()
        if sqnum:
            try:
                int(sqnum)
            except ValueError:
                return False, f"Row {idx}: Invalid Sub-Question Number '{sqnum}'"
        
        pts_txt = (G(r, "Points", "points") or "").strip()
        if pts_txt:
            try:
                float(pts_txt)
            except ValueError:
                return False, f"Row {idx}: Invalid Points value '{pts_txt}'"
    
    return True, None

def validate_context_data(rows: List[dict]) -> Tuple[bool, Optional[str]]:
    """Validate contexts"""
    if not rows:
        return True, None
    
    for idx, r in enumerate(rows, 1):
        context_local_id = (G(r, "Context ID", "context_id", "contextid") or "").strip()
        context_text = (G(r, "Context Text", "context_text") or "").strip()
        
        if not context_local_id and not context_text:
            continue
        
        if bool(context_local_id) != bool(context_text):
            return False, f"Row {idx}: Context ID and Context Text must both be present or both be absent"
        
        if context_local_id:
            try:
                int(context_local_id)
            except ValueError:
                return False, f"Row {idx}: Context ID must be an integer, got '{context_local_id}'"
    
    return True, None

def find_attachment_matches(attachments: List[str], referenced_attachment: str) -> List[str]:
    """Find exact or partial matches for an attachment reference"""
    if not referenced_attachment:
        return []
    
    matches = []
    ref_lower = referenced_attachment.lower()
    ref_name = Path(referenced_attachment).stem.lower()
    
    for att in attachments:
        att_lower = att.lower()
        att_name = Path(att).stem.lower()
        
        if Path(att).name.lower() == Path(referenced_attachment).name.lower():
            matches.append(att)
        elif att_name == ref_name:
            matches.append(att)
    
    return matches


# ============================================================================
# API ENDPOINTS
# ============================================================================

# API #1: Filtered Questions Retrieval
@router.get("/")
async def get_questions(
    id: Optional[int] = Query(None, description="Filter by question ID"),
    subject: Optional[str] = Query(None, description="Filter by subject/course"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Low, Med, High)"),
    type: Optional[str] = Query(None, description="Filter by question type"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    topic: Optional[str] = Query(None, description="Filter by one or more topics"),
    match: Optional[str] = Query("all", description="Match mode: 'any' (OR) or 'all' (AND) across all filters"),
    fuzzy: Optional[bool] = Query(True, description="Enable fuzzy matching for topic keywords"),
    is_latest: Optional[bool] = Query(True, description="Only return latest versions"),
    db: Session = Depends(get_db)
):
    """
    GET /api/questions
    Returns all questions with flexible filtering.
    """
    try:
        query_str = """
            SELECT 
                q.question_id, 
                q.question_text, 
                q.question_type,
                c.course_code, 
                c.course_name, 
                a.assessment_type,
                a.assessment_acadyear,
                a.assessment_semester,
                q.difficulty, 
                q.concepts, 
                q.created_at, 
                q.version_number,
                q.previous_version_id,
                q.is_latest
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            WHERE 1=1
        """
        params = {}
        conditions = []

        if id is not None:
            conditions.append("q.question_id = :id")
            params["id"] = id

        if subject is not None:
            conditions.append("(c.course_code ILIKE :subject OR c.course_name ILIKE :subject)")
            params["subject"] = f"%{subject}%"

        if difficulty is not None:
            conditions.append("q.difficulty ILIKE :difficulty")
            params["difficulty"] = f"%{difficulty}%"

        if type is not None:
            conditions.append("q.question_type ILIKE :question_type")
            params["question_type"] = f"%{type}%"

        if semester is not None:
            conditions.append("(a.assessment_semester ILIKE :semester OR a.assessment_type ILIKE :semester)")
            params["semester"] = f"%{semester}%"

        if is_latest:
            conditions.append("q.is_latest = TRUE")

        if conditions:
            if match == "any":
                query_str += " AND (" + " OR ".join(conditions) + ")"
            else:
                query_str += " AND " + " AND ".join(conditions)

        base_results = db.execute(text(query_str), params).fetchall()

        if topic:
            topics = [t.strip().lower() for t in topic.split(",") if t.strip()]
            filtered_rows = []

            for row in base_results:
                question_topics = [t.strip().lower() for t in (row.concepts.split(",") if row.concepts else [])]

                topic_matches = []
                for user_topic in topics:
                    if fuzzy:
                        match_found = any(fuzz.partial_ratio(user_topic, qt) > 70 for qt in question_topics)
                    else:
                        match_found = any(user_topic in qt for qt in question_topics)
                    topic_matches.append(match_found)

                if (match == "all" and all(topic_matches)) or (match != "all" and any(topic_matches)):
                    filtered_rows.append(row)
        else:
            filtered_rows = base_results

        questions = []
        for row in filtered_rows:
            questions.append({
                "question_id": row.question_id,
                "question_text": row.question_text,
                "question_type": row.question_type,
                "course_code": row.course_code,
                "course_name": row.course_name,
                "assessment_type": row.assessment_type,
                "assessment_year": row.assessment_acadyear,
                "assessment_semester": row.assessment_semester,
                "difficulty": row.difficulty,
                "concepts": row.concepts.split(',') if row.concepts else [],
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "version_number": row.version_number,
                "previous_version_id": row.previous_version_id,
                "is_latest": row.is_latest
            })

        return {"success": True, "count": len(questions), "data": questions}

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
                a.assessment_acadyear,
                a.assessment_semester,
                ctx.context_text,
                ctx.context_local_id,
                STRING_AGG(DISTINCT qa.attachment_name, ', ') as question_attachments,
                STRING_AGG(DISTINCT ca.attachment_name, ', ') as context_attachments
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN contexts ctx ON q.context_id = ctx.context_id
            LEFT JOIN question_attachments qa ON q.question_id = qa.question_id
            LEFT JOIN context_attachments ca ON ctx.context_id = ca.context_id
            WHERE q.question_id = :id
            GROUP BY q.question_id, c.course_code, c.course_name, 
                     a.assessment_type, a.assessment_acadyear, a.assessment_semester,
                     ctx.context_text, ctx.context_local_id
        """)
    
        result = db.execute(query, {"id": id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        
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
            "assessment_year": row.assessment_acadyear,
            "assessment_semester": row.assessment_semester,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "version_number": row.version_number,
            "previous_version_id": row.previous_version_id
        }
        
        if row.question_type in ["MCQ", "MRQ"]:
            options = {}
            if row.option_a: options["A"] = row.option_a
            if row.option_b: options["B"] = row.option_b
            if row.option_c: options["C"] = row.option_c
            if row.option_d: options["D"] = row.option_d
            if row.option_e: options["E"] = row.option_e
            if options: response_data["options"] = options
        elif row.question_type == "T/F":
            response_data["options"] = {
                "A": row.option_a if row.option_a else "True",
                "B": row.option_b if row.option_b else "False"
            }
        
        if row.context_text or row.context_attachments:
            context = {}
            if row.context_text:
                context["text"] = row.context_text
                context["context_id"] = row.context_local_id
            
            if row.context_attachments:
                context_files = []
                for name in row.context_attachments.split(', '):
                    if name.strip():
                        context_files.append({"name": name.strip(), "url": f"/api/attachments/{name.strip()}"})
                if context_files:
                    context["attachments"] = context_files
            
            if context:
                response_data["context"] = context
        
        if row.question_attachments:
            question_files = []
            for name in row.question_attachments.split(', '):
                if name.strip():
                    question_files.append({"name": name.strip(), "url": f"/api/attachments/{name.strip()}"})
            if question_files:
                response_data["attachments"] = question_files
        
        return {"success": True, "data": response_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# API #3: Fetching ALL Versions
@router.get("/{id}/versions")
async def get_question_versions(id: int, db: Session = Depends(get_db)):
    """GET /api/questions/{id}/versions - Retrieve all related versions"""
    try:
        root_query = text("SELECT question_id, previous_version_id FROM questions WHERE question_id = :id")
        result = db.execute(root_query, {"id": id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Question not found")

        current_id = row.question_id
        root_id = current_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            parent_query = text("SELECT previous_version_id FROM questions WHERE question_id = :id")
            parent_result = db.execute(parent_query, {"id": current_id}).fetchone()
            
            if parent_result and parent_result.previous_version_id:
                root_id = parent_result.previous_version_id
                current_id = parent_result.previous_version_id
            else:
                root_id = current_id
                break

        versions_query = text("""
            WITH RECURSIVE version_tree AS (
                SELECT * FROM questions WHERE question_id = :root_id
                UNION ALL
                SELECT q.* FROM questions q
                INNER JOIN version_tree vt ON q.previous_version_id = vt.question_id
            )
            SELECT
                vt.question_id, vt.question_text, vt.question_type, vt.version_number,
                vt.previous_version_id, vt.is_latest, vt.difficulty, vt.concepts, vt.created_at,
                c.course_code, c.course_name, a.assessment_type, a.assessment_acadyear, a.assessment_semester
            FROM version_tree vt
            LEFT JOIN courses c ON vt.course_id = c.course_id
            LEFT JOIN assessments a ON vt.assessment_id = a.assessment_id
            ORDER BY vt.version_number ASC, vt.created_at ASC
        """)

        result = db.execute(versions_query, {"root_id": root_id})
        rows = result.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No versions found")

        versions = []
        for row in rows:
            versions.append({
                "question_id": row.question_id,
                "question_text": row.question_text or "",
                "question_type": row.question_type or "",
                "course_code": row.course_code or "",
                "course_name": row.course_name or "",
                "assessment_type": row.assessment_type or "",
                "assessment_year": row.assessment_acadyear or "",
                "assessment_semester": row.assessment_semester or "",
                "difficulty": row.difficulty or "",
                "concepts": row.concepts.split(',') if row.concepts else [],
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "version_number": row.version_number,
                "previous_version_id": row.previous_version_id,
                "is_latest": row.is_latest
            })

        return {"success": True, "root_id": root_id, "version_count": len(versions), "data": versions}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# API #4: Uploading new question version
@router.post("/edit", response_model=UploadPreviewResponse)
async def upload_edit(id: int, file: UploadFile = File(...)):
    """Step 1: Upload edited question CSV/ZIP and preview, using same logic as API 5."""
    upload_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    temp_dir = Path(tempfile.mkdtemp(prefix=f"edit_{upload_id}_"))

    try:
        file_path = temp_dir / file.filename
        with open(file_path, 'wb') as f:
            f.write(await file.read())

        questions_csv_path = None
        attachments = []
        attachment_paths = {}
        questions_data = []

        if file.filename.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            for csv_file in temp_dir.rglob("*.csv"):
                if "question" in csv_file.name.lower() and "__MACOSX" not in str(csv_file):
                    questions_csv_path = csv_file
                    break
            for f in temp_dir.rglob("*"):
                if f.is_file() and f.suffix.lower() != ".csv":
                    attachments.append(f.name)
                    attachment_paths[f.name] = str(f)
        elif file.filename.endswith(".csv"):
            questions_csv_path = file_path
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or ZIP")

        if not questions_csv_path or not questions_csv_path.exists():
            raise HTTPException(status_code=400, detail="Questions CSV not found in upload")

        # Read CSV rows
        questions_data = read_csv_rows(questions_csv_path)

        if len(questions_data) != 1:
            raise HTTPException(status_code=400, detail="Edit must contain exactly ONE question")

        # Convert fields for preview to avoid type errors (use same as API 5)
        questions_preview = []
        for q in questions_data:
            qnum_raw = (G(q, "Question Number", "question_number") or "").strip()
            sqnum_raw = (G(q, "Sub-Question Number", "sub_question_number") or "").strip()
            qnum = int(qnum_raw) if qnum_raw else None
            sqnum = int(sqnum_raw) if sqnum_raw else None

            pts_txt = (G(q, "Points", "points") or "").strip()
            pts = float(pts_txt) if pts_txt else None

            questions_preview.append(
                QuestionPreview(
                    question_number=qnum,
                    sub_question_number=sqnum,
                    question_text=(G(q, "Question Text", "question_text") or "").strip(),
                    question_type=(G(q, "Question Type", "question_type") or "").strip() or None,
                    option_a=(G(q, "Option A", "option_a") or None),
                    option_b=(G(q, "Option B", "option_b") or None),
                    option_c=(G(q, "Option C", "option_c") or None),
                    option_d=(G(q, "Option D", "option_d") or None),
                    option_e=(G(q, "Option E", "option_e") or None),
                    correct_answer=(G(q, "Correct Answer", "correct_answer") or None),
                    explanation=(G(q, "Explanation", "explanation") or None),
                    points=pts,
                    difficulty=(G(q, "Difficulty", "difficulty") or "").strip() or None,
                    concepts=(G(q, "Concepts", "concepts", "concept") or "").strip() or None,
                    attachment=(G(q, "Attachment", "attachment") or "").strip() or None,
                    context_id=(G(q, "Context ID", "context_id", "contextid") or "").strip() or None
                )
            )

        # Store upload data for confirm/delete
        pending_uploads[upload_id] = {
            "temp_dir": str(temp_dir),
            "questions_data": questions_data,
            "attachments": attachments,
            "attachment_paths": attachment_paths,
            "previous_question_id": id,
            "created_at": datetime.now().isoformat()
        }

        return UploadPreviewResponse(
            upload_id=upload_id,
            questions=questions_preview,
            contexts=[],  # no context edits here
            attachments=attachments,
            course_code=None,
            assessment_type=None,
            academic_year=None,
            semester=None,
            debug_info={"questions_count": len(questions_preview)}
        )

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")

@router.post("/confirm-edits", response_model=ConfirmUploadResponse)
def confirm_edit(request: ConfirmUploadRequest):
    """Step 2: Confirm edit and commit to DB using same safe pipeline as API 5."""
    upload_id = request.upload_id
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")

    upload_data = pending_uploads[upload_id]
    temp_dir = Path(upload_data['temp_dir'])
    session = SessionLocal()
    try:
        questions_data = upload_data['questions_data']
        prev_id = upload_data['previous_question_id']
        questions_inserted = 0
        attachments_copied = 0

        # Get existing question for versioning
        current_version = session.execute(
            text("SELECT version_number, course_id, assessment_id FROM questions WHERE question_id=:id"),
            {"id": prev_id}
        ).fetchone()

        if not current_version:
            raise HTTPException(status_code=404, detail=f"Original question ID {prev_id} not found")

        # Mark old version as not latest
        session.execute(
            text("UPDATE questions SET is_latest = FALSE WHERE question_id=:id"),
            {"id": prev_id}
        )

        for r in questions_data:
            qnum_raw = (G(r, "Question Number", "question_number") or "").strip()
            sqnum_raw = (G(r, "Sub-Question Number", "sub_question_number") or "").strip()
            qnum = int(qnum_raw) if qnum_raw else None
            sqnum = int(sqnum_raw) if sqnum_raw else None

            pts_txt = (G(r, "Points", "points") or "").strip()
            pts = float(pts_txt) if pts_txt else None

            res = session.execute(
                text("""
                    INSERT INTO questions (
                        assessment_id, course_id, context_id, question_number, sub_question_number,
                        question_text, question_type, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, explanation, points, difficulty, concepts,
                        version_number, previous_version_id, is_latest
                    ) VALUES (
                        :aid, :cid, NULL, :qnum, :sqnum, :qtxt, :qtype, :a, :b, :c, :d, :e,
                        :ans, :expl, :pts, :diff, :conc, :ver, :prev_id, TRUE
                    )
                    RETURNING question_id
                """),
                {
                    "aid": current_version.assessment_id,
                    "cid": current_version.course_id,
                    "qnum": qnum,
                    "sqnum": sqnum,
                    "qtxt": (G(r, "Question Text", "question_text") or "").strip(),
                    "qtype": (G(r, "Question Type", "question_type") or "").strip() or None,
                    "a": (G(r, "Option A", "option_a") or None),
                    "b": (G(r, "Option B", "option_b") or None),
                    "c": (G(r, "Option C", "option_c") or None),
                    "d": (G(r, "Option D", "option_d") or None),
                    "e": (G(r, "Option E", "option_e") or None),
                    "ans": (G(r, "Correct Answer", "correct_answer") or None),
                    "expl": (G(r, "Explanation", "explanation") or None),
                    "pts": pts,
                    "diff": (G(r, "Difficulty", "difficulty") or None),
                    "conc": (G(r, "Concepts", "concepts", "concept") or None),
                    "ver": current_version.version_number + 1,
                    "prev_id": prev_id
                }
            )
            new_qid = res.scalar()
            questions_inserted += 1

        session.commit()
        del pending_uploads[upload_id]
        shutil.rmtree(temp_dir, ignore_errors=True)

        return ConfirmUploadResponse(
            success=True,
            message=f"Successfully updated {questions_inserted} question(s)",
            upload_id=upload_id,
            questions_inserted=questions_inserted,
            contexts_inserted=0,
            attachments_copied=attachments_copied
        )

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Confirm failed: {str(e)}")
    finally:
        session.close()

@router.post("/delete-edits", response_model=CancelUploadResponse)
def delete_edit(request: CancelUploadRequest = Body(...)):
    """Step 3: Cancel pending edit upload."""
    upload_id = request.upload_id
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")
    upload_data = pending_uploads[upload_id]
    temp_dir = Path(upload_data['temp_dir'])
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    del pending_uploads[upload_id]
    return CancelUploadResponse(success=True, message="Edit upload cancelled", upload_id=upload_id)



# API #5: Upload (Preview)
@router.post("/upload", response_model=UploadPreviewResponse)
async def upload_assessment(file: UploadFile = File(...)):
    """Step 1: Upload CSV or ZIP, parse files, return preview."""
    upload_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    temp_dir = Path(tempfile.mkdtemp(prefix=f"upload_{upload_id}_"))
    
    logger.info(f"=== Starting upload {upload_id} ===")
    
    try:
        file_path = temp_dir / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        questions_data = []
        contexts_data = []
        attachments = []
        attachment_paths = {}
        questions_csv_path = None
        context_csv_path = None
        metadata = {}
        
        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            for csv_file in temp_dir.rglob('*.csv'):
                if '__MACOSX' in str(csv_file) or csv_file.name.startswith('.'):
                    continue
                
                meta = parse_meta_from_filename(csv_file.name)
                if meta:
                    course_code, assessment_type, kind, ay, sem = meta
                    if kind == "questions":
                        questions_csv_path = csv_file
                        metadata = {
                            'course_code': course_code,
                            'assessment_type': assessment_type,
                            'academic_year': f"20{ay[:2]}/20{ay[2:]}" if ay else None,
                            'semester': sem
                        }
                    elif kind == "contexts":
                        context_csv_path = csv_file
            
            for f in temp_dir.rglob('*'):
                if f.is_file() and not f.suffix.lower() == '.csv':
                    if '__MACOSX' not in str(f) and not f.name.startswith('.'):
                        attachments.append(f.name)
                        attachment_paths[f.name] = str(f)
        
        elif file.filename.endswith('.csv'):
            meta = parse_meta_from_filename(file.filename)
            if not meta:
                raise HTTPException(status_code=400, detail="Invalid CSV filename format")
            
            course_code, assessment_type, kind, ay, sem = meta
            if kind != "questions":
                raise HTTPException(status_code=400, detail="Single CSV file must be a questions file")
            
            questions_csv_path = file_path
            metadata = {
                'course_code': course_code,
                'assessment_type': assessment_type,
                'academic_year': f"20{ay[:2]}/20{ay[2:]}" if ay else None,
                'semester': sem
            }
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or ZIP")
        
        if not questions_csv_path or not questions_csv_path.exists():
            raise HTTPException(status_code=400, detail="questions.csv not found in upload")
        
        questions_data = read_csv_rows(questions_csv_path)
        is_valid, error_msg = validate_questions_data(questions_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid questions.csv: {error_msg}")
        
        if context_csv_path and context_csv_path.exists():
            contexts_data = read_csv_rows(context_csv_path)
            is_valid, error_msg = validate_context_data(contexts_data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid context.csv: {error_msg}")
        
        questions_preview = []
        for q in questions_data:
            qtext = (G(q, "Question Text", "question_text") or "").strip()
            if not qtext:
                continue
            
            qnum = (G(q, "Question Number", "question_number") or "").strip()
            sqnum = (G(q, "Sub-Question Number", "sub_question_number") or "").strip()
            pts_txt = (G(q, "Points", "points") or "").strip()
            
            questions_preview.append(QuestionPreview(
                question_number=int(qnum) if qnum else None,
                sub_question_number=int(sqnum) if sqnum else None,
                question_text=qtext,
                question_type=(G(q, "Question Type", "question_type") or "").strip() or None,
                option_a=(G(q, "Option A", "option_a") or None),
                option_b=(G(q, "Option B", "option_b") or None),
                option_c=(G(q, "Option C", "option_c") or None),
                option_d=(G(q, "Option D", "option_d") or None),
                option_e=(G(q, "Option E", "option_e") or None),
                correct_answer=(G(q, "Correct Answer", "correct_answer") or None),
                explanation=(G(q, "Explanation", "explanation") or None),
                points=float(pts_txt) if pts_txt else None,
                difficulty=(G(q, "Difficulty", "difficulty") or "").strip() or None,
                concepts=(G(q, "Concepts", "concepts", "concept") or "").strip() or None,
                attachment=(G(q, "Attachment", "attachment") or "").strip() or None,
                context_id=(G(q, "Context ID", "context_id", "contextid") or "").strip() or None
            ))
        
        contexts_preview = []
        for c in contexts_data:
            context_id = (G(c, "Context ID", "context_id", "contextid") or "").strip()
            context_text = (G(c, "Context Text", "context_text") or "").strip()
            if context_id and context_text:
                contexts_preview.append(ContextPreview(
                    context_id=context_id,
                    context_text=context_text,
                    attachment=(G(c, "Attachment", "attachment") or "").strip() or None
                ))
        
        pending_uploads[upload_id] = {
            'temp_dir': str(temp_dir),
            'questions_data': questions_data,
            'contexts_data': contexts_data,
            'attachments': attachments,
            'attachment_paths': attachment_paths,
            'metadata': metadata,
            'questions_csv_path': str(questions_csv_path),
            'context_csv_path': str(context_csv_path) if context_csv_path else None,
            'created_at': datetime.now().isoformat()
        }
        
        return UploadPreviewResponse(
            upload_id=upload_id,
            questions=questions_preview,
            contexts=contexts_preview,
            attachments=attachments,
            course_code=metadata.get('course_code'),
            assessment_type=metadata.get('assessment_type'),
            academic_year=metadata.get('academic_year'),
            semester=metadata.get('semester'),
            debug_info={'questions_count': len(questions_preview), 'contexts_count': len(contexts_preview)}
        )
    
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


# API #5: Confirm Upload
@router.post("/confirm-upload", response_model=ConfirmUploadResponse)
async def confirm_upload(request: ConfirmUploadRequest):
    """Step 2: Confirm upload and commit to database."""
    upload_id = request.upload_id
    
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")
    
    upload_data = pending_uploads[upload_id]
    temp_dir = Path(upload_data['temp_dir'])
    
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    session = SessionLocal()
    questions_inserted = 0
    contexts_inserted = 0
    attachments_copied = 0
    
    try:
        questions_data = upload_data['questions_data']
        contexts_data = upload_data['contexts_data']
        attachments = upload_data['attachments']
        attachment_paths = upload_data['attachment_paths']
        metadata = upload_data['metadata']
        
        course_code = metadata['course_code']
        assessment_type = metadata['assessment_type']
        ay = metadata.get('academic_year')
        sem = metadata.get('semester')
        
        course_id = session.execute(text("SELECT course_id FROM courses WHERE course_code = :code LIMIT 1"), {"code": course_code}).scalar()
        if not course_id:
            result = session.execute(text("INSERT INTO courses (course_code, course_name) VALUES (:code, :name) RETURNING course_id"), {"code": course_code, "name": course_code})
            course_id = result.scalar()
        
        assessment_id = session.execute(
            text("SELECT assessment_id FROM assessments WHERE course_id = :cid AND assessment_type = :at AND COALESCE(assessment_acadyear, '') = COALESCE(:ay, '') AND COALESCE(assessment_semester, '') = COALESCE(:sem, '') LIMIT 1"),
            {"cid": course_id, "at": assessment_type, "ay": ay, "sem": sem}
        ).scalar()
        
        if not assessment_id:
            result = session.execute(
                text("INSERT INTO assessments (course_id, assessment_type, assessment_acadyear, assessment_semester) VALUES (:cid, :at, :ay, :sem) RETURNING assessment_id"),
                {"cid": course_id, "at": assessment_type, "ay": ay, "sem": sem}
            )
            assessment_id = result.scalar()
        
        session.commit()
        
        context_id_map = {}
        for r in contexts_data:
            context_local_id = (G(r, "Context ID", "context_id", "contextid") or "").strip()
            context_text = (G(r, "Context Text", "context_text") or "").strip()
            if not context_local_id or not context_text:
                continue
            
            res = session.execute(
                text("INSERT INTO contexts (assessment_id, course_id, context_local_id, context_text) VALUES (:aid, :cid, :clid, :ctxt) ON CONFLICT (assessment_id, context_local_id) DO UPDATE SET context_text = EXCLUDED.context_text RETURNING context_id"),
                {"aid": assessment_id, "cid": course_id, "clid": context_local_id, "ctxt": context_text}
            )
            ctx_id = res.scalar()
            context_id_map[context_local_id] = ctx_id
            contexts_inserted += 1
        
        session.commit()
        
        for r in questions_data:
            qtext = (G(r, "Question Text", "question_text") or "").strip()
            if not qtext:
                continue
            
            ctx_local = (G(r, "Context ID", "context_id", "contextid") or "").strip()
            qnum = (G(r, "Question Number", "question_number") or "").strip() or None
            sqnum = (G(r, "Sub-Question Number", "sub_question_number") or "").strip() or None
            qtype = (G(r, "Question Type", "question_type") or "").strip() or None
            a = (G(r, "Option A", "option_a") or None)
            b = (G(r, "Option B", "option_b") or None)
            c = (G(r, "Option C", "option_c") or None)
            d = (G(r, "Option D", "option_d") or None)
            e = (G(r, "Option E", "option_e") or None)
            ans = (G(r, "Correct Answer", "correct_answer") or None)
            expl = (G(r, "Explanation", "explanation") or None)
            pts_txt = (G(r, "Points", "points") or "").strip()
            diff = (G(r, "Difficulty", "difficulty") or None)
            conc = (G(r, "Concepts", "concepts", "concept") or None)
            qatt = (G(r, "Attachment", "attachment") or "").strip()
            
            pts = float(pts_txt) if pts_txt else None
            ctx_id = context_id_map.get(ctx_local) if ctx_local else None
            
            res = session.execute(
                text("""
                    INSERT INTO questions (
                        assessment_id, course_id, context_id, question_number, sub_question_number,
                        question_text, question_type, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, explanation, points, difficulty, concepts, version_number, is_latest
                    ) VALUES (
                        :aid, :cid, :ctx, :qnum, :sqnum, :qtxt, :qtype, :a, :b, :c, :d, :e,
                        :ans, :expl, :pts, :diff, :conc, 1, TRUE
                    )
                    ON CONFLICT (course_id, assessment_id, question_text)
                    DO UPDATE SET question_type = EXCLUDED.question_type, option_a = EXCLUDED.option_a,
                        option_b = EXCLUDED.option_b, option_c = EXCLUDED.option_c, option_d = EXCLUDED.option_d,
                        option_e = EXCLUDED.option_e, correct_answer = EXCLUDED.correct_answer,
                        explanation = EXCLUDED.explanation, points = EXCLUDED.points,
                        difficulty = EXCLUDED.difficulty, concepts = EXCLUDED.concepts,
                        context_id = COALESCE(EXCLUDED.context_id, questions.context_id), is_latest = TRUE
                    RETURNING question_id
                """),
                {"aid": assessment_id, "cid": course_id, "ctx": ctx_id, "qnum": qnum, "sqnum": sqnum,
                 "qtxt": qtext, "qtype": qtype, "a": a, "b": b, "c": c, "d": d, "e": e,
                 "ans": ans, "expl": expl, "pts": pts, "diff": diff, "conc": conc}
            )
            qid = res.scalar()
            questions_inserted += 1
            
            if qid and qatt:
                session.execute(
                    text("INSERT INTO question_attachments (question_id, attachment_name, attachment_url) VALUES (:qid, :name, NULL) ON CONFLICT (question_id, attachment_name) DO NOTHING"),
                    {"qid": qid, "name": qatt}
                )
        
        session.commit()
        
        for att_name, att_path in attachment_paths.items():
            try:
                source = Path(att_path)
                if source.exists():
                    target_dir = STORAGE_PNG_PATH if att_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')) else STORAGE_PNG_PATH.parent / "other"
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target_dir / att_name)
                    attachments_copied += 1
            except Exception as e:
                logger.error(f"Failed to copy attachment {att_name}: {e}")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        del pending_uploads[upload_id]
        
        return ConfirmUploadResponse(
            success=True,
            message=f"Successfully uploaded {questions_inserted} questions",
            upload_id=upload_id,
            questions_inserted=questions_inserted,
            contexts_inserted=contexts_inserted,
            attachments_copied=attachments_copied
        )
    
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to confirm upload: {str(e)}")
    finally:
        session.close()


# API #5: Cancel Upload
@router.post("/cancel-upload", response_model=CancelUploadResponse)
def cancel_upload(request: CancelUploadRequest = Body(...)):
    """Step 3: Cancel a pending upload."""
    upload_id = request.upload_id
    
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")
    
    try:
        upload_data = pending_uploads[upload_id]
        temp_dir = Path(upload_data['temp_dir'])
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        del pending_uploads[upload_id]
        
        return CancelUploadResponse(success=True, message="Upload cancelled successfully", upload_id=upload_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel upload: {str(e)}")


# API #6: Version Diff
def highlight_changes(old_text: str, new_text: str) -> Dict[str, str]:
    """Generate inline highlighted HTML showing additions and deletions"""
    if old_text == new_text:
        return None
    
    similarity = SequenceMatcher(None, old_text, new_text).ratio()
    if similarity < 0.3:
        return {
            "previous": f'<span style="background-color: #ffc0c0; text-decoration: line-through;">{old_text}</span>' if old_text else "",
            "current": f'<span style="background-color: #c0ffc0; font-weight: bold;">{new_text}</span>' if new_text else "",
            "type": "complete_change"
        }
    
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
        
        if tag != 'equal' and i2 < len(old_words):
            old_html.append(' ')
        if tag != 'equal' and j2 < len(new_words):
            new_html.append(' ')
    
    return {"previous": ''.join(old_html), "current": ''.join(new_html), "type": "partial_change"}


@router.get("/{id}/diff/{version_id}")
async def get_question_diff(id: int, version_id: int, db: Session = Depends(get_db)):
    """Compare two versions of a question"""
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
        "explanation": "Explanation",
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


# API #7: Suggest Question Variants
@router.get("/{id}/suggestions")
async def get_question_suggestions(id: int, db: Session = Depends(get_db), top_n: int = Query(5)):
    """Suggest variant questions based on course, difficulty, type, and concepts"""
    try:
        ref_query = text("""
            SELECT q.question_id, q.question_text, q.question_type, q.difficulty, q.concepts, q.course_id, c.course_code
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            WHERE q.question_id = :id
        """)
        
        ref_result = db.execute(ref_query, {"id": id}).fetchone()
        if not ref_result:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Find all questions with same course, difficulty, and type (no restrictions)
        candidates_query = text("""
            SELECT q.question_id, q.question_text, q.question_type, q.difficulty, q.concepts, 
                   c.course_code, a.assessment_type, q.version_number, q.is_latest, q.previous_version_id
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            WHERE q.course_id = :course_id 
                AND q.difficulty = :difficulty 
                AND q.question_type = :qtype
                AND q.question_id != :id
        """)
        
        candidates = db.execute(candidates_query, {
            "course_id": ref_result.course_id,
            "difficulty": ref_result.difficulty,
            "qtype": ref_result.question_type,
            "id": id
        }).fetchall()
        
        if not candidates:
            return {
                "success": True,
                "question_id": id,
                "message": "No similar questions found",
                "suggested_variants": []
            }
        
        all_concepts = [ref_result.concepts or ""] + [c.concepts or "" for c in candidates]
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(all_concepts)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        suggestions = []
        for idx, candidate in enumerate(candidates):
            suggestions.append({
                "question_id": int(candidate.question_id),
                "question_text": candidate.question_text[:100] + "..." if len(candidate.question_text) > 100 else candidate.question_text,
                "course_code": candidate.course_code,
                "assessment_type": candidate.assessment_type,
                "difficulty": candidate.difficulty,
                "question_type": candidate.question_type,
                "concepts": candidate.concepts.split(',') if candidate.concepts else [],
                "version_number": candidate.version_number,
                "is_latest": candidate.is_latest,
                "previous_version_id": candidate.previous_version_id,
                "similarity_score": round(float(similarities[idx]), 3)
            })
        
        suggestions.sort(key=lambda x: x["similarity_score"], reverse=True)
        return {
            "success": True,
            "question_id": id,
            "reference_question": {
                "course_code": ref_result.course_code,
                "difficulty": ref_result.difficulty,
                "question_type": ref_result.question_type,
                "concepts": ref_result.concepts.split(',') if ref_result.concepts else []
            },
            "matching_criteria": {
                "same_course": True,
                "same_difficulty": True,
                "same_question_type": True,
                "concept_similarity": "TF-IDF cosine similarity",
                "note": "Includes all versions and related questions (no parent/child restrictions)"
            },
            "suggested_variants": suggestions[:top_n],
            "total_candidates": len(candidates)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
