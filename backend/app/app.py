"""
API routes for Questions - Updated with Enhanced Upload & Attachment Support
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
from fastapi.responses import JSONResponse, FileResponse
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
import subprocess
import mimetypes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_ROOT = Path(__file__).resolve().parent.parent
ATT_STORAGE_PATH = BACKEND_ROOT / "quizbank-db" / "attachment_storage"
BACKUP_DIR = BACKEND_ROOT / "backups" / "quizbank"

# Database configuration
DB_CONTAINER_NAME = "quizbank_db" 
DB_NAME = "quizbank"
DB_USER = "postgres"

# Ensure directories exist
ATT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Create router
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

# Supported attachment extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.md'}
DATA_EXTENSIONS = {'.r', '.rmd', '.py', '.ipynb', '.json', '.xml', '.csv', '.xlsx'}
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.gz'}
OTHER_EXTENSIONS = {'.html', '.css', '.js', '.tex'}


def get_storage_path_for_file(filename: str) -> Path:
    return STORAGE_PATH


def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
    return Path(filename).suffix.lower() in image_extensions


def get_mime_type(filename: str) -> str:
    """Get MIME type for file"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    
    # Fallback for common types
    ext = Path(filename).suffix.lower()
    mime_map = {
        '.r': 'text/plain',
        '.rmd': 'text/plain',
        '.py': 'text/x-python',
        '.ipynb': 'application/x-ipynb+json',
        '.md': 'text/markdown',
        '.tex': 'application/x-latex'
    }
    return mime_map.get(ext, 'application/octet-stream')

def trigger_backup():
    """Trigger database backup after successful ingestion"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"backup_{timestamp}.sql.gz"
        
        logger.info(f"🔄 Creating database backup: {backup_file}")
        
        # Run pg_dump directly (we're already in a container that can reach the DB)
        result = subprocess.run(
            [
                "pg_dump",
                "-h", "quizbank_db",
                "-U", "postgres",
                "-d", "quizbank",
                "--no-password"
            ],
            capture_output=True,
            check=True,
            env={**os.environ, "PGPASSWORD": "postgres"}
        )
        
        # Compress the output
        import gzip
        with gzip.open(backup_file, 'wb') as f:
            f.write(result.stdout)
        
        # Create/update symlink to latest backup
        latest_link = BACKUP_DIR / "latest.sql.gz"
        
        # Remove existing symlink or file (more robust approach)
        try:
            if latest_link.is_symlink():
                latest_link.unlink()
            elif latest_link.exists():
                latest_link.unlink()
        except Exception as e:
            logger.warning(f"⚠️ Could not remove old symlink: {e}")
        
        # Create new symlink using relative path
        try:
            latest_link.symlink_to(backup_file.name)
            logger.info(f"🔗 Latest backup linked: latest.sql.gz -> {backup_file.name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not create symlink: {e}, copying file instead")
            # Fallback: just copy the file if symlink fails
            shutil.copy2(backup_file, latest_link)
            logger.info(f"📋 Latest backup copied to: latest.sql.gz")
        
        logger.info(f"✅ Database backup created: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Backup failed (pg_dump error): {e.stderr.decode() if e.stderr else 'Unknown error'}")
        return False
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False

def get_latest_backup() -> Optional[Path]:
    """Find the most recent backup file"""
    try:
        # Check for symlink first
        latest_link = BACKUP_DIR / "latest.sql.gz"
        if latest_link.exists():
            return latest_link
        
        # Fallback to finding newest file
        backups = sorted(BACKUP_DIR.glob("backup_*.sql.gz"), reverse=True)
        return backups[0] if backups else None
    except Exception as e:
        logger.error(f"❌ Failed to find latest backup: {e}")
        return None

def restore_from_backup(backup_file: Path) -> bool:
    """Restore database from backup file"""
    try:
        logger.info(f"🔄 Restoring database from: {backup_file}")
        
        # Read and decompress backup
        import gzip
        with gzip.open(backup_file, 'rb') as f:
            backup_sql = f.read().decode('utf-8')
        
        # Drop and recreate database
        subprocess.run(
            [
                "psql",
                "-h", DB_CONTAINER_NAME,
                "-U", DB_USER,
                "-c", "DROP DATABASE IF EXISTS quizbank;"
            ],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PGPASSWORD": "postgres"}
        )
        
        subprocess.run(
            [
                "psql",
                "-h", DB_CONTAINER_NAME,
                "-U", DB_USER,
                "-c", "CREATE DATABASE quizbank;"
            ],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PGPASSWORD": "postgres"}
        )
        
        # Restore data
        result = subprocess.run(
            [
                "psql",
                "-h", DB_CONTAINER_NAME,
                "-U", DB_USER,
                "-d", DB_NAME
            ],
            input=backup_sql,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PGPASSWORD": "postgres"}
        )
        
        logger.info(f"✅ Database restored from: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Restore failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        return False

def copy_attachments_to_storage(attachment_paths: Dict[str, str]) -> int:
    """Copy attachments from temp directory to persistent storage. Keeps images and R files."""
    copied_count = 0
    skip_exts = {'.csv', '.zip'}
    
    for att_name, att_path in attachment_paths.items():
        try:
            source = Path(att_path)
            if not source.exists():
                logger.warning(f"⚠️ Attachment not found: {att_name}")
                continue
            
            # Get file extension
            file_ext = source.suffix.lower()
            
            # Keep images and R files, skip others (CSV, ZIP, etc.)
            if file_ext in skip_exts:
                logger.info(f"⏭️ Skipping CSV/ZIP file: {att_name} ({file_ext})")
                continue
            
            # All files go to attachment_storage
            target_path = ATT_STORAGE_PATH / att_name
            shutil.copy2(source, target_path)
            logger.info(f"✅ Copied attachment: {att_name} → {target_path}")
            copied_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to copy attachment {att_name}: {e}")
    
    return copied_count


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


def check_for_duplicates(session, assessment_id: int, questions_data: list) -> tuple[bool, list]:
    """
    Check if any questions already exist in the database.
    
    Returns:
        (has_duplicates: bool, duplicate_list: list of dicts with duplicate info)
    """
    duplicates = []
    
    for idx, q in enumerate(questions_data):
        qtext = (G(q, "Question Text", "question_text") or "").strip()
        if not qtext:
            continue
            
        # Check if this question already exists
        existing = session.execute(
            text("""
                SELECT question_id, question_text, version_number 
                FROM questions 
                WHERE assessment_id = :aid 
                  AND question_text = :qtxt
                LIMIT 1
            """),
            {"aid": assessment_id, "qtxt": qtext}
        ).fetchone()

        if existing:
            qnum = (G(q, "Question Number", "question_number") or "").strip()
            duplicates.append({
                "row_number": idx + 1,
                "question_number": qnum if qnum else "N/A",
                "question_text": qtext[:100] + "..." if len(qtext) > 100 else qtext,
                "existing_question_id": existing.question_id,
                "existing_version": existing.version_number
            })
    
    return len(duplicates) > 0, duplicates


# Pydantic models
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

class AttachmentInfo(BaseModel):
    name: str
    type: str  # 'image', 'document', 'data', 'other'
    size: Optional[int] = None

class UploadPreviewResponse(BaseModel):
    upload_id: str
    questions: List[QuestionPreview]
    contexts: List[ContextPreview]
    attachments: List[AttachmentInfo]
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
    backup_created: bool

class CancelUploadRequest(BaseModel):
    upload_id: str

class CancelUploadResponse(BaseModel):
    success: bool
    message: str
    upload_id: str

# Temporary storage for pending uploads
pending_uploads: Dict[str, Dict] = {}

# Validation helpers
def validate_questions_data(rows: List[dict], is_edit: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate questions - for edits, exactly 1 row required"""
    if not rows:
        return False, "No question rows found"
    
    if is_edit and len(rows) != 1:
        return False, f"Edit must contain exactly 1 question, found {len(rows)}"
    
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

def categorize_attachment(filename: str, file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Categorize attachment and return metadata"""
    ext = Path(filename).suffix.lower()
    
    # Determine type
    if ext in IMAGE_EXTENSIONS:
        att_type = 'image'
    elif ext in DOCUMENT_EXTENSIONS:
        att_type = 'document'
    elif ext in DATA_EXTENSIONS:
        att_type = 'data'
    else:
        att_type = 'other'
    
    result = {
        'name': filename,
        'type': att_type,
        'extension': ext,
        'mime_type': get_mime_type(filename)
    }
    
    # Get file size if path provided
    if file_path and file_path.exists():
        result['size'] = file_path.stat().st_size
    
    return result

def extract_attachments_from_zip(temp_dir: Path, zip_path: Path) -> Tuple[List[str], Dict[str, str], List[AttachmentInfo]]:
    """Extract and categorize attachments from ZIP"""
    attachments = []
    attachment_paths = {}
    attachment_info = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    for f in temp_dir.rglob('*'):
        # Skip CSV files, ZIP files, and hidden/system files
        if f.is_file() and f.suffix.lower() not in {'.csv', '.zip'}:
            if '__MACOSX' not in str(f) and not f.name.startswith('.'):
                attachments.append(f.name)
                attachment_paths[f.name] = str(f)
                
                # Categorize attachment
                att_info = categorize_attachment(f.name, f)
                attachment_info.append(AttachmentInfo(**att_info))
                
                logger.info(f"📎 Found {att_info['type']} attachment: {f.name} ({att_info.get('size', 0)} bytes)")
    
    return attachments, attachment_paths, attachment_info


# ============================================================================
# API ENDPOINTS
# ============================================================================

# API #1: Filtered Questions Retrieval (unchanged)
@router.get("/")
async def get_questions(
    id: Optional[str] = Query(None, description="Filter by question ID"),
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
    """GET /api/questions - Returns all questions with flexible filtering"""
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
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN courses c ON a.course_id = c.course_id
            WHERE 1=1
        """
        params = {}
        conditions = []

        # ID filtering
        if id is not None:
            ids = [i.strip() for i in id.split(",") if i.strip()]
            if len(ids) == 1:
                conditions.append("q.question_id = :id")
                params["id"] = ids[0]
            else:
                subconds = []
                for i, val in enumerate(ids):
                    key = f"id_{i}"
                    subconds.append(f"q.question_id = :{key}")
                    params[key] = val
                conditions.append("(" + " OR ".join(subconds) + ")")

        # Subject filtering
        if subject is not None:
            subjects = [s.strip() for s in subject.split(",") if s.strip()]
            if len(subjects) == 1:
                conditions.append("(c.course_code ILIKE :subject OR c.course_name ILIKE :subject)")
                params["subject"] = f"%{subjects[0]}%"
            else:
                subconds = []
                for i, s in enumerate(subjects):
                    key = f"subject_{i}"
                    subconds.append(f"(c.course_code ILIKE :{key} OR c.course_name ILIKE :{key})")
                    params[key] = f"%{s}%"
                conditions.append("(" + " OR ".join(subconds) + ")")

        # Difficulty filtering
        if difficulty is not None:
            difficulties = [d.strip() for d in difficulty.split(",") if d.strip()]
            if len(difficulties) == 1:
                conditions.append("q.difficulty ILIKE :difficulty")
                params["difficulty"] = f"%{difficulties[0]}%"
            else:
                subconds = []
                for i, d in enumerate(difficulties):
                    key = f"difficulty_{i}"
                    subconds.append(f"q.difficulty ILIKE :{key}")
                    params[key] = f"%{d}%"
                conditions.append("(" + " OR ".join(subconds) + ")")

        if type is not None:
            types = [t.strip() for t in type.split(",") if t.strip()]
            if len(types) == 1:
                conditions.append("q.question_type ILIKE :question_type")
                params["question_type"] = f"%{types[0]}%"
            else:
                subconds = []
                for i, t in enumerate(types):
                    key = f"type_{i}"
                    subconds.append(f"q.question_type ILIKE :{key}")
                    params[key] = f"%{t}%"
                conditions.append("(" + " OR ".join(subconds) + ")")

        if semester is not None:
            semesters = [s.strip() for s in semester.split(",") if s.strip()]
            if len(semesters) == 1:
                conditions.append("(a.assessment_semester ILIKE :semester OR a.assessment_type ILIKE :semester)")
                params["semester"] = f"%{semesters[0]}%"
            else:
                subconds = []
                for i, s in enumerate(semesters):
                    key = f"semester_{i}"
                    subconds.append(f"(a.assessment_semester ILIKE :{key} OR a.assessment_type ILIKE :{key})")
                    params[key] = f"%{s}%"
                conditions.append("(" + " OR ".join(subconds) + ")")

        if is_latest and match == "all":
            conditions.append("q.is_latest = TRUE")

        if conditions:
            if match == "any" and len(conditions) > 1:
                query_str += " AND (" + " OR ".join(conditions) + ")"
            else:
                query_str += " AND " + " AND ".join(conditions)

        base_results = db.execute(text(query_str), params).fetchall()

        # Apply topic-based filtering
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

        if is_latest and match == "any":
            filtered_rows = [row for row in filtered_rows if row.is_latest]

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

# API #2: More Questions Details with Enhanced Attachment Info
from fastapi import Request, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

@router.get("/{id}")
async def get_question_by_id(id: int, request: Request, db: Session = Depends(get_db)):
    """GET /api/questions/:id - Returns full question with enhanced attachment metadata"""
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
                STRING_AGG(DISTINCT qa.attachment_name, ', ') AS question_attachments,
                STRING_AGG(DISTINCT ca.attachment_name, ', ') AS context_attachments
            FROM questions q
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN courses c ON a.course_id = c.course_id
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
            "previous_version_id": row.previous_version_id,
        }

        # Add options for question types
        if row.question_type in ["MCQ", "MRQ"]:
            options = {}
            for key in ["A", "B", "C", "D", "E"]:
                opt_value = getattr(row, f"option_{key.lower()}", None)
                if opt_value:
                    options[key] = opt_value
            if options:
                response_data["options"] = options

        elif row.question_type == "T/F":
            response_data["options"] = {
                "A": row.option_a or "True",
                "B": row.option_b or "False"
            }

        # === Context attachments ===
        if row.context_text or row.context_attachments:
            context = {}
            if row.context_text:
                context["text"] = row.context_text
                context["context_id"] = row.context_local_id

            if row.context_attachments:
                context_files = []
                for name in row.context_attachments.split(', '):
                    name = name.strip()
                    if not name:
                        continue
                    att_info = categorize_attachment(name)
                    context_files.append({
                        "name": name,
                        "url": request.url_for("get_attachment", filename=name),
                        "type": att_info["type"],
                        "mime_type": att_info["mime_type"],
                        "is_image": att_info["type"] == "image"
                    })
                if context_files:
                    context["attachments"] = context_files

            response_data["context"] = context

        # === Question attachments ===
        if row.question_attachments:
            question_files = []
            for name in row.question_attachments.split(', '):
                name = name.strip()
                if not name:
                    continue
                att_info = categorize_attachment(name)
                url = ATT_STORAGE_PATH/name
                question_files.append({
                    "name": name,
                    "url": request.url_for("get_attachment", filename=name),
                    "type": att_info["type"],
                    "mime_type": att_info["mime_type"],
                    "is_image": att_info["type"] == "image"
                })
            if question_files:
                response_data["attachments"] = question_files

        return {"success": True, "data": response_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# API for serving attachments
@router.get("/attachments/{filename}")
async def get_attachment(filename: str):
    """Serve attachment files with proper MIME types"""
    try:
        # First look in storage
        file_path = ATT_STORAGE_PATH / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Attachment '{filename}' not found")

        # Detect MIME type
        mime_type = get_mime_type(filename)

        # Return as inline for images, as download for others
        content_disposition = (
            f"inline; filename={filename}"
            if is_image_file(filename)
            else f"attachment; filename={filename}"
        )

        return FileResponse(
            path=file_path,
            media_type=mime_type,
            headers={"Content-Disposition": content_disposition},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving attachment: {str(e)}")

# API #3: Fetching ALL Versions (unchanged)
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
            LEFT JOIN assessments a ON vt.assessment_id = a.assessment_id
            LEFT JOIN courses c ON a.course_id = c.course_id
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


# ============================================================================
# API #4: Edit Upload
# ============================================================================

@router.post("/edit", response_model=UploadPreviewResponse)
async def edit_upload(id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    API #4: Upload a new version of a question.
    Step 1: Upload CSV/ZIP, extract metadata from existing question, return preview.
    """
    upload_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    temp_dir = Path(tempfile.mkdtemp(prefix=f"edit_{upload_id}_"))
    
    logger.info(f"=== Starting edit upload {upload_id} for question {id} ===")

    try:
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

        questions_csv_path = None
        context_csv_path = None
        attachments = []
        attachment_paths = {}
        attachment_info = []
        questions_data = []
        contexts_data = []

        # --- Handle ZIP files ---
        if file.filename.endswith(".zip"):
            logger.info(f"📦 Processing ZIP file: {file.filename}")
            attachments, attachment_paths, attachment_info = extract_attachments_from_zip(temp_dir, file_path)

            # Find CSVs inside ZIP
            for csv_file in temp_dir.rglob("*.csv"):
                name_lower = csv_file.name.lower()

                # Skip hidden/macOS files
                if "__macosx" in str(csv_file).lower() or csv_file.name.startswith("."):
                    continue

                # Context CSV detection
                if "context" in name_lower and "question" not in name_lower:
                    context_csv_path = csv_file
                    logger.info(f"✅ Found context CSV: {csv_file.name}")
                    continue

                # Questions CSV detection
                if "question" in name_lower:
                    questions_csv_path = csv_file
                    logger.info(f"✅ Found questions CSV: {csv_file.name}")
                    continue

            if not questions_csv_path:
                raise HTTPException(status_code=400, detail="No question CSV found in ZIP")

        # --- Handle single CSV uploads ---
        elif file.filename.endswith(".csv"):
            questions_csv_path = file_path
        else:
            raise HTTPException(status_code=400, detail="Only .zip or .csv files are supported")

        # --- Read questions CSV ---
        questions_data = read_csv_rows(questions_csv_path)
        logger.info(f"📊 Read {len(questions_data)} rows from questions CSV")

        # Enforce exactly 1 question for API #4
        if len(questions_data) != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Questions CSV must contain exactly 1 question, found {len(questions_data)}"
            )

        # --- Read context CSV if exists ---
        if context_csv_path and context_csv_path.exists():
            contexts_data = read_csv_rows(context_csv_path)
            logger.info(f"📘 Read {len(contexts_data)} rows from context CSV")

        # --- Extract contexts from questions CSV if no separate context CSV ---
        elif not context_csv_path:
            logger.info("📝 No separate context CSV found, extracting from questions CSV")
            contexts_data = []
            seen_contexts = set()
            for q in questions_data:
                ctx_id = (G(q, "Context ID", "context_id", "contextid") or "").strip()
                ctx_text = (G(q, "Context Text", "context_text") or "").strip()
                ctx_att = (G(q, "Context Attachment", "context_attachment") or "").strip()

                if ctx_id and ctx_text and ctx_id not in seen_contexts:
                    contexts_data.append({
                        "Context ID": ctx_id,
                        "Context Text": ctx_text,
                        "Attachment": ctx_att
                    })
                    seen_contexts.add(ctx_id)
                    logger.info(f"📄 Extracted context {ctx_id} from questions CSV")

        # --- Build question previews ---
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

        # --- Build context previews ---
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

        # --- Get metadata from existing question ---
        logger.info(f"📋 Extracting metadata from question ID {id}")
        existing_q = db.execute(
            text("""
                SELECT c.course_code, a.assessment_type, a.assessment_acadyear, a.assessment_semester
                FROM questions q
                JOIN assessments a ON q.assessment_id = a.assessment_id
                JOIN courses c ON a.course_id = c.course_id
                WHERE q.question_id = :qid
            """),
            {"qid": id}
        ).fetchone()
        
        if not existing_q:
            raise HTTPException(status_code=404, detail=f"Question {id} not found")
        
        metadata = {
            'course_code': existing_q.course_code,
            'assessment_type': existing_q.assessment_type,
            'academic_year': existing_q.assessment_acadyear,
            'semester': existing_q.assessment_semester
        }

        # --- Save pending upload ---
        pending_uploads[upload_id] = {
            "temp_dir": str(temp_dir),
            "questions_data": questions_data,
            "contexts_data": contexts_data,
            "attachments": attachments,
            "attachment_paths": attachment_paths,
            "previous_question_id": id,
            "metadata": metadata,
            "original_file_path": str(file_path),
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"✅ Edit upload preview created: {upload_id} with {len(questions_preview)} questions, {len(contexts_preview)} contexts, {len(attachment_info)} attachments")

        return UploadPreviewResponse(
            upload_id=upload_id,
            questions=questions_preview,
            contexts=contexts_preview,
            attachments=attachment_info,
            course_code=metadata['course_code'],
            assessment_type=metadata['assessment_type'],
            academic_year=metadata['academic_year'],
            semester=metadata['semester'],
            debug_info={
                "questions_count": len(questions_preview),
                "contexts_count": len(contexts_preview),
                "attachments_count": len(attachment_info)
            }
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


# ============================================================================
# API #4: Confirm Edit
# ============================================================================

@router.post("/confirm-edits", response_model=ConfirmUploadResponse)
def confirm_edit(request: ConfirmUploadRequest, db: Session = Depends(get_db)):
    """
    Step 2: Confirm edit and commit to DB:
    1. Get metadata and check for duplicates
    2. Insert new question version
    3. Move attachments to storage bucket
    4. Run fresh backup
    5. Clean up temp files
    """
    upload_id = request.upload_id
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")

    upload_data = pending_uploads[upload_id]
    temp_dir = Path(upload_data['temp_dir'])
    
    session = db
    questions_inserted = 0
    attachments_copied = 0
    backup_created = False
    
    try:
        # STEP 1: Get metadata
        logger.info("📊 Step 1: Getting course and assessment info...")
        questions_data = upload_data['questions_data']
        metadata = upload_data['metadata']
        attachment_paths = upload_data['attachment_paths']
        
        course_code = metadata['course_code']
        assessment_type = metadata['assessment_type']
        ay = metadata.get('academic_year')
        sem = metadata.get('semester')
        
        # Get course_id
        course_id = session.execute(
            text("SELECT course_id FROM courses WHERE course_code = :code LIMIT 1"),
            {"code": course_code}
        ).scalar()
        
        if not course_id:
            raise HTTPException(status_code=404, detail=f"Course {course_code} not found")
        
        # Get assessment_id
        assessment_id = session.execute(
            text("SELECT assessment_id FROM assessments WHERE course_id = :cid AND assessment_type = :at AND COALESCE(assessment_acadyear, '') = COALESCE(:ay, '') AND COALESCE(assessment_semester, '') = COALESCE(:sem, '') LIMIT 1"),
            {"cid": course_id, "at": assessment_type, "ay": ay or '', "sem": sem or ''}
        ).scalar()
        
        if not assessment_id:
            raise HTTPException(status_code=404, detail=f"Assessment not found for {course_code} {assessment_type}")
        
        # STEP 2: Check for duplicates
        logger.info("🔍 Step 2: Checking for duplicate questions...")
        has_duplicates, duplicate_list = check_for_duplicates(session, assessment_id, questions_data)
        
        if has_duplicates:
            error_msg = f"Found {len(duplicate_list)} duplicate question(s):"
            for dup in duplicate_list:
                error_msg += f"\n  • Row {dup['row_number']} (Q{dup['question_number']}): '{dup['question_text']}' already exists as question ID {dup['existing_question_id']} (v{dup['existing_version']})"
            
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Duplicate questions found",
                    "message": error_msg,
                    "duplicates": duplicate_list
                }
            )
        
        logger.info("📝 Step 2.5: Processing contexts...")
        contexts_data = upload_data.get('contexts_data', [])
        context_id_map = {}

        for r in contexts_data:
            context_local_id = (G(r, "Context ID", "context_id", "contextid") or "").strip()
            context_text = (G(r, "Context Text", "context_text") or "").strip()
            if not context_local_id or not context_text:
                continue
            
            res = session.execute(
                text("INSERT INTO contexts (assessment_id, context_local_id, context_text) VALUES (:aid, :clid, :ctxt) ON CONFLICT (assessment_id, context_local_id) DO UPDATE SET context_text = EXCLUDED.context_text RETURNING context_id"),
                {"aid": assessment_id, "clid": context_local_id, "ctxt": context_text}
            )
            ctx_id = res.scalar()
            context_id_map[context_local_id] = ctx_id
            
            # Handle context attachments
            catt = (G(r, "Attachment", "attachment") or "").strip()
            if ctx_id and catt:
                session.execute(
                    text("INSERT INTO context_attachments (context_id, attachment_name, attachment_url) VALUES (:cid, :name, NULL) ON CONFLICT (context_id, attachment_name) DO NOTHING"),
                    {"cid": ctx_id, "name": catt}
                )

        session.commit()
        logger.info(f"✅ Processed {len(context_id_map)} context(s)")

        
        # STEP 3: Process question edit (insert new version)
        logger.info("✏️ Step 3: Processing question edit...")
        
        for r in questions_data:
            qtext = (G(r, "Question Text", "question_text") or "").strip()
            if not qtext:
                continue
            
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
            prev_id = upload_data.get('previous_question_id')
            
            # Get the latest version number for this question lineage
            if prev_id:
                max_ver = session.execute(
                    text("SELECT MAX(version_number) FROM questions WHERE question_id = :pid OR previous_version_id = :pid"),
                    {"pid": prev_id}
                ).scalar() or 1
                new_ver = max_ver + 1
            else:
                new_ver = 1
            
            # Insert new version
            res = session.execute(
                text("""
                    INSERT INTO questions (
                        assessment_id, context_id, question_number, sub_question_number,
                        question_text, question_type, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, explanation, points, difficulty, concepts,
                        version_number, previous_version_id, is_latest
                    ) VALUES (
                        :aid, NULL, :qnum, :sqnum, :qtxt, :qtype, :a, :b, :c, :d, :e,
                        :ans, :expl, :pts, :diff, :conc, :ver, :prev_id, TRUE
                    )
                    RETURNING question_id
                """),
                {"aid": assessment_id, "qnum": qnum, "sqnum": sqnum,
                 "qtxt": qtext, "qtype": qtype, "a": a, "b": b, "c": c, "d": d, "e": e,
                 "ans": ans, "expl": expl, "pts": pts, "diff": diff, "conc": conc,
                 "ver": new_ver, "prev_id": prev_id}
            )
            qid = res.scalar()
            questions_inserted += 1
            
            # Mark previous version as not latest
            if prev_id:
                session.execute(
                    text("UPDATE questions SET is_latest = FALSE WHERE question_id = :pid"),
                    {"pid": prev_id}
                )
            
            # Handle question attachments
            if qid and qatt:
                session.execute(
                    text("INSERT INTO question_attachments (question_id, attachment_name, attachment_url) VALUES (:qid, :name, NULL) ON CONFLICT (question_id, attachment_name) DO NOTHING"),
                    {"qid": qid, "name": qatt}
                )
        
        session.commit()
        logger.info(f"✅ Inserted {questions_inserted} question(s)")
        
        # STEP 4: Move attachments to storage bucket
        logger.info("📎 Step 4: Moving attachments to storage bucket...")
        attachments_copied = copy_attachments_to_storage(attachment_paths)
        
        # STEP 5: Run fresh backup
        logger.info("💾 Step 5: Creating fresh backup...")
        backup_created = trigger_backup()
        
        # STEP 6: Clean up batch folder
        logger.info("🧹 Step 6: Cleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        del pending_uploads[upload_id]
        
        logger.info(f"✅ Edit confirmation complete for upload {upload_id}")
        
        return ConfirmUploadResponse(
            success=True,
            message=f"Successfully edited {questions_inserted} question(s)",
            upload_id=upload_id,
            questions_inserted=questions_inserted,
            contexts_inserted=0,
            attachments_copied=attachments_copied,
            backup_created=backup_created
        )
    
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Confirm edit failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Confirm failed: {str(e)}")


# API #4 - delete edits
@router.post("/delete-edits", response_model=CancelUploadResponse)
def delete_edit(request: CancelUploadRequest = Body(...)):
    """Step 3: Cancel pending edit upload"""
    upload_id = request.upload_id
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")
    upload_data = pending_uploads[upload_id]
    temp_dir = Path(upload_data['temp_dir'])
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    del pending_uploads[upload_id]
    return CancelUploadResponse(success=True, message="Edit upload cancelled", upload_id=upload_id)


# API #5: Upload Assessment - ENHANCED WITH BETTER ATTACHMENT HANDLING
@router.post("/upload", response_model=UploadPreviewResponse)
async def upload_assessment(file: UploadFile = File(...)):
    """Step 1: Upload CSV or ZIP, parse files, return preview with attachment metadata"""
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
        attachment_info = []
        questions_csv_path = None
        context_csv_path = None
        metadata = {}
        
        # Handle ZIP files
        if file.filename.endswith('.zip'):
            logger.info(f"📦 Processing ZIP file: {file.filename}")
            attachments, attachment_paths, attachment_info = extract_attachments_from_zip(temp_dir, file_path)
            
            # Find CSVs - look for both questions and contexts
            for csv_file in temp_dir.rglob('*.csv'):
                if '__MACOSX' in str(csv_file) or csv_file.name.startswith('.'):
                    continue
                
                csv_name_lower = csv_file.name.lower()
                logger.info(f"📄 Found CSV in ZIP: {csv_file.name}")
                
                # Check if it's a contexts file
                if 'context' in csv_name_lower and 'question' not in csv_name_lower:
                    context_csv_path = csv_file
                    logger.info(f"✅ Identified as contexts file: {csv_file.name}")
                    continue
                
                # Check if it's a questions file or try to parse metadata
                if 'question' in csv_name_lower:
                    questions_csv_path = csv_file
                    logger.info(f"✅ Identified as questions file: {csv_file.name}")
                    
                    # Try to extract metadata from filename
                    meta = parse_meta_from_filename(csv_file.name)
                    if meta:
                        course_code, assessment_type, kind, ay, sem = meta
                        metadata = {
                            'course_code': course_code,
                            'assessment_type': assessment_type,
                            'academic_year': f"20{ay[:2]}/20{ay[2:]}" if ay else None,
                            'semester': sem
                        }
                        logger.info(f"📊 Extracted metadata from filename: {metadata}")
                    continue
                
                # If no clear indicator, try to parse as questions file
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
                        logger.info(f"✅ Parsed as questions file from pattern: {csv_file.name}")
                    elif kind == "contexts":
                        context_csv_path = csv_file
                        logger.info(f"✅ Parsed as contexts file from pattern: {csv_file.name}")
            
            # If we still don't have a questions file, look for any CSV that might be questions
            if not questions_csv_path:
                for csv_file in temp_dir.rglob('*.csv'):
                    if '__MACOSX' not in str(csv_file) and not csv_file.name.startswith('.'):
                        if csv_file != context_csv_path:  # Not the contexts file
                            questions_csv_path = csv_file
                            logger.info(f"⚠️ Using {csv_file.name} as questions file (fallback)")
                            break
        
        # Handle CSV files
        elif file.filename.endswith('.csv'):
            logger.info(f"📄 Processing CSV file: {file.filename}")
            meta = parse_meta_from_filename(file.filename)
            if meta:
                course_code, assessment_type, kind, ay, sem = meta
                if kind != "questions":
                    raise HTTPException(status_code=400, detail="Single CSV file must be a questions file")
                
                metadata = {
                    'course_code': course_code,
                    'assessment_type': assessment_type,
                    'academic_year': f"20{ay[:2]}/20{ay[2:]}" if ay else None,
                    'semester': sem
                }
            else:
                # If filename doesn't match pattern, try to extract from CSV content
                logger.warning(f"⚠️ Filename doesn't match expected pattern, will extract metadata from CSV content")
                metadata = {
                    'course_code': None,
                    'assessment_type': None,
                    'academic_year': None,
                    'semester': None
                }
            
            questions_csv_path = file_path
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or ZIP")
        
        if not questions_csv_path or not questions_csv_path.exists():
            raise HTTPException(status_code=400, detail="questions.csv not found in upload")
        
        logger.info(f"📋 Using questions CSV: {questions_csv_path.name}")
        if context_csv_path:
            logger.info(f"📋 Using contexts CSV: {context_csv_path.name}")
        else:
            logger.info(f"📋 No separate contexts CSV found, will extract from questions CSV")
        
        # Read and validate questions
        questions_data = read_csv_rows(questions_csv_path)
        logger.info(f"📊 Read {len(questions_data)} rows from questions CSV")
        
        is_valid, error_msg = validate_questions_data(questions_data, is_edit=False)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid questions.csv: {error_msg}")
        
        # Extract metadata from CSV content if not already set from filename
        if not metadata.get('course_code') and questions_data:
            # Try to extract from first row
            first_row = questions_data[0]
            course = (G(first_row, "Course", "Course Code", "course_code") or "").strip()
            assessment = (G(first_row, "Assessment", "Assessment Type", "assessment_type") or "").strip()
            year = (G(first_row, "Academic Year", "Year", "academic_year") or "").strip()
            sem = (G(first_row, "Semester", "semester") or "").strip()
            
            if course:
                metadata['course_code'] = course
            if assessment:
                metadata['assessment_type'] = assessment
            if year:
                metadata['academic_year'] = year
            if sem:
                metadata['semester'] = sem
            
            logger.info(f"📊 Extracted metadata from CSV: {metadata}")
        
        # Read and validate contexts
        if context_csv_path and context_csv_path.exists():
            contexts_data = read_csv_rows(context_csv_path)
            is_valid, error_msg = validate_context_data(contexts_data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid context.csv: {error_msg}")
        else:
            # Extract contexts from questions CSV if no separate contexts file
            logger.info("📝 No separate contexts.csv found, extracting contexts from questions.csv")
            contexts_data = []
            seen_contexts = set()
            
            for q in questions_data:
                ctx_id = (G(q, "Context ID", "context_id", "contextid") or "").strip()
                ctx_text = (G(q, "Context Text", "context_text") or "").strip()
                ctx_att = (G(q, "Context Attachment", "context_attachment") or "").strip()
                
                if ctx_id and ctx_text and ctx_id not in seen_contexts:
                    contexts_data.append({
                        "Context ID": ctx_id,
                        "Context Text": ctx_text,
                        "Attachment": ctx_att
                    })
                    seen_contexts.add(ctx_id)
                    logger.info(f"📄 Extracted context {ctx_id} from questions.csv")
        
        # Build preview
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
            'original_file_path': str(file_path),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Upload preview created: {upload_id} with {len(questions_preview)} questions, {len(contexts_preview)} contexts, {len(attachment_info)} attachments")
        
        return UploadPreviewResponse(
            upload_id=upload_id,
            questions=questions_preview,
            contexts=contexts_preview,
            attachments=attachment_info,
            course_code=metadata.get('course_code'),
            assessment_type=metadata.get('assessment_type'),
            academic_year=metadata.get('academic_year'),
            semester=metadata.get('semester'),
            debug_info={
                'questions_count': len(questions_preview),
                'contexts_count': len(contexts_preview),
                'attachments_count': len(attachment_info)
            }
        )
    
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


# ============================================================================
# API #5: Confirm Upload
# ============================================================================

@router.post("/confirm-upload", response_model=ConfirmUploadResponse)
async def confirm_upload(request: ConfirmUploadRequest, db: Session = Depends(get_db)):
    """
    Step 2: Confirm upload and commit to database:
    1. Parse CSVs and check for duplicates
    2. Insert data
    3. Move attachments to storage bucket
    4. Run fresh backup
    5. Clean up batch folder
    """
    upload_id = request.upload_id
    
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail=f"Upload {upload_id} not found")
    
    upload_data = pending_uploads[upload_id]
    temp_dir = Path(upload_data['temp_dir'])

    
    session = db
    questions_inserted = 0
    contexts_inserted = 0
    attachments_copied = 0
    backup_created = False
    
    try:        
        # STEP 1: Parse data and get course/assessment
        logger.info("📊 Step 2: Parsing CSVs and getting course/assessment...")
        questions_data = upload_data['questions_data']
        contexts_data = upload_data['contexts_data']
        attachments = upload_data['attachments']
        attachment_paths = upload_data['attachment_paths']
        metadata = upload_data['metadata']
        
        course_code = metadata['course_code']
        assessment_type = metadata['assessment_type']
        ay = metadata.get('academic_year')
        sem = metadata.get('semester')
        
        # Get or create course
        course_id = session.execute(
            text("SELECT course_id FROM courses WHERE course_code = :code LIMIT 1"),
            {"code": course_code}
        ).scalar()
        
        if not course_id:
            result = session.execute(
                text("INSERT INTO courses (course_code, course_name) VALUES (:code, :name) RETURNING course_id"),
                {"code": course_code, "name": course_code}
            )
            course_id = result.scalar()
        
        # Get or create assessment
        assessment_id = session.execute(
            text("SELECT assessment_id FROM assessments WHERE course_id = :cid AND assessment_type = :at AND COALESCE(assessment_acadyear, '') = COALESCE(:ay, '') AND COALESCE(assessment_semester, '') = COALESCE(:sem, '') LIMIT 1"),
            {"cid": course_id, "at": assessment_type, "ay": ay, "sem": sem}
        ).scalar()

        if not assessment_id:
            logger.info(f"📝 Creating new assessment: {assessment_type} for {course_code}")
            result = session.execute(
                text("INSERT INTO assessments (course_id, assessment_type, assessment_acadyear, assessment_semester) VALUES (:cid, :at, :ay, :sem) RETURNING assessment_id"),
                {"cid": course_id, "at": assessment_type, "ay": ay, "sem": sem}
            )
            assessment_id = result.scalar()
            logger.info(f"✅ Created assessment_id: {assessment_id}")

        session.commit()
                
        # STEP 2: Check for duplicate questions
        logger.info("🔍 Step 3: Checking for duplicate questions...")
        has_duplicates, duplicate_list = check_for_duplicates(session, assessment_id, questions_data)        
        if has_duplicates:
            error_msg = f"Found {len(duplicate_list)} duplicate question(s):"
            for dup in duplicate_list:
                error_msg += f"\n  • Row {dup['row_number']} (Q{dup['question_number']}): '{dup['question_text']}' already exists as question ID {dup['existing_question_id']} (v{dup['existing_version']})"
            
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Duplicate questions found",
                    "message": error_msg,
                    "duplicates": duplicate_list
                }
            )
        
        # STEP 3: Insert contexts
        logger.info("📝 Step 4: Inserting contexts...")
        context_id_map = {}
        for r in contexts_data:
            context_local_id = (G(r, "Context ID", "context_id", "contextid") or "").strip()
            context_text = (G(r, "Context Text", "context_text") or "").strip()
            if not context_local_id or not context_text:
                continue
            
            res = session.execute(
                text("INSERT INTO contexts (assessment_id, context_local_id, context_text) VALUES (:aid, :clid, :ctxt) ON CONFLICT (assessment_id, context_local_id) DO UPDATE SET context_text = EXCLUDED.context_text RETURNING context_id"),
                {"aid": assessment_id, "clid": context_local_id, "ctxt": context_text}
            )
            ctx_id = res.scalar()
            context_id_map[context_local_id] = ctx_id
            contexts_inserted += 1
            
            # Handle context attachments
            catt = (G(r, "Attachment", "attachment") or "").strip()
            if ctx_id and catt:
                session.execute(
                    text("INSERT INTO context_attachments (context_id, attachment_name, attachment_url) VALUES (:cid, :name, NULL) ON CONFLICT (context_id, attachment_name) DO NOTHING"),
                    {"cid": ctx_id, "name": catt}
                )
        
        session.commit()
        logger.info(f"✅ Inserted {contexts_inserted} context(s)")
        
        # STEP 4: Insert questions
        logger.info("📝 Step 5: Inserting questions...")
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
                        assessment_id, context_id, question_number, sub_question_number,
                        question_text, question_type, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, explanation, points, difficulty, concepts, version_number, is_latest
                    ) VALUES (
                        :aid, :ctx, :qnum, :sqnum, :qtxt, :qtype, :a, :b, :c, :d, :e,
                        :ans, :expl, :pts, :diff, :conc, 1, TRUE
                    )
                    RETURNING question_id
                """),
                {"aid": assessment_id, "ctx": ctx_id, "qnum": qnum, "sqnum": sqnum,
                 "qtxt": qtext, "qtype": qtype, "a": a, "b": b, "c": c, "d": d, "e": e,
                 "ans": ans, "expl": expl, "pts": pts, "diff": diff, "conc": conc}
            )
            qid = res.scalar()
            questions_inserted += 1
            
            # Handle question attachments
            if qid and qatt:
                session.execute(
                    text("INSERT INTO question_attachments (question_id, attachment_name, attachment_url) VALUES (:qid, :name, NULL) ON CONFLICT (question_id, attachment_name) DO NOTHING"),
                    {"qid": qid, "name": qatt}
                )
        
        session.commit()
        logger.info(f"✅ Inserted {questions_inserted} question(s)")
        
        # STEP 5: Move attachments to storage bucket
        logger.info("📎 Step 6: Moving attachments to storage bucket...")
        attachments_copied = copy_attachments_to_storage(attachment_paths)
        
        # STEP 6: Run fresh backup
        logger.info("💾 Step 7: Creating fresh backup...")
        backup_created = trigger_backup()
        
        # STEP 7: Clean up batch folder
        logger.info("🧹 Step 8: Cleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        del pending_uploads[upload_id]
        
        logger.info(f"✅ Upload confirmation complete for upload {upload_id}")
        
        return ConfirmUploadResponse(
            success=True,
            message=f"Successfully uploaded {questions_inserted} questions and {contexts_inserted} contexts",
            upload_id=upload_id,
            questions_inserted=questions_inserted,
            contexts_inserted=contexts_inserted,
            attachments_copied=attachments_copied,
            backup_created=backup_created
        )
    
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Confirm upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm upload: {str(e)}")
        

# API #5: Cancel Upload
@router.post("/cancel-upload", response_model=CancelUploadResponse)
def cancel_upload(request: CancelUploadRequest = Body(...)):
    """Step 3: Cancel a pending upload"""
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
            SELECT q.question_id, q.question_text, q.question_type, q.difficulty, q.concepts, a.course_id, c.course_code
            FROM questions q
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN courses c ON a.course_id = c.course_id
            WHERE q.question_id = :id
        """)
        
        ref_result = db.execute(ref_query, {"id": id}).fetchone()
        if not ref_result:
            raise HTTPException(status_code=404, detail="Question not found")
        
        candidates_query = text("""
            SELECT q.question_id, q.question_text, q.question_type, q.difficulty, q.concepts, 
                   c.course_code, a.assessment_type, q.version_number, q.is_latest, q.previous_version_id
            FROM questions q
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN courses c ON a.course_id = c.course_id
            WHERE a.course_id = :course_id 
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
                "note": "Includes all versions and related questions"
            },
            "suggested_variants": suggestions[:top_n],
            "total_candidates": len(candidates)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
