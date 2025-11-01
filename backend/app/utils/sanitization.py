"""
Sanitization Layer
------------------
Performs pre-insertion validation and duplicate detection for question uploads.
Can be imported by:
 - /upload API
 - /editversion API
 - update_script.py (batch uploads after init)

Handles:
- Non-ASCII cleanup
- Required field validation
- Hash generation
- Within-file duplicate detection
- Cross-database duplicate detection (scoped by course + assessment)
- Row-level error reporting
"""

import re
import hashlib
import unicodedata
import pandas as pd
from sqlalchemy import text
from typing import List, Dict, Tuple


# ===============================
# Text Cleaning and Normalization
# ===============================

def clean_non_ascii(text: str) -> str:
    """
    Clean invalid or invisible non-ASCII characters 
    but preserve meaningful math symbols and Unicode letters.
    """
    if not isinstance(text, str):
        return ""
    
    # Normalize to NFC form (standard Unicode)
    text = unicodedata.normalize("NFC", text)
    
    # Remove control and invisible characters (except space)
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]", "", text)
    
    # Replace non-breaking spaces with normal spaces
    text = text.replace("\u00A0", " ")

    # Encode/decode to ensure valid UTF-8
    text = text.encode("utf-8", "ignore").decode("utf-8")

    return text.strip()


def normalize_text(text: str) -> str:
    """Normalize text safely for statistical content and hashing."""
    if not isinstance(text, str):
        return ""
    text = clean_non_ascii(text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ===============================
# Hash Generation
# ===============================

def generate_question_hash(question_text: str) -> str:
    """Generate SHA-256 hash of normalized question text."""
    normalized = normalize_text(question_text)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ===============================
# Field Validation
# ===============================

REQUIRED_FIELDS = ["question_text", "question_type", "difficulty", "concepts"]

def validate_required_fields(row: dict) -> List[str]:
    """Ensure all required fields are present and not empty."""
    errors = []
    for field in REQUIRED_FIELDS:
        if not row.get(field) or str(row.get(field)).strip() == "":
            errors.append(f"Missing required field: {field}")
    return errors


# ===============================
# Core Sanitization
# ===============================

def sanitize_dataframe(df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
    """
    Perform sanitization and within-file duplicate checks.
    Returns:
        (clean_rows, errors)
    """
    clean_rows = []
    errors = []
    seen_hashes = set()

    for idx, row in df.iterrows():
        row_num = idx + 1
        record = row.to_dict()
        row_errors = validate_required_fields(record)

        # Clean and hash question_text
        question_text = record.get("question_text", "")
        question_text = clean_non_ascii(question_text)
        record["question_text"] = question_text
        record["question_hash"] = generate_question_hash(question_text)

        if not record["question_hash"]:
            row_errors.append("Unable to generate hash (empty question text)")

        # Within-file duplicate check
        if record["question_hash"] in seen_hashes:
            row_errors.append("Duplicate question found within same upload file")
        else:
            seen_hashes.add(record["question_hash"])

        if row_errors:
            errors.append({
                "row": row_num,
                "question_text": question_text[:80],
                "errors": row_errors
            })
        else:
            clean_rows.append(record)

    return clean_rows, errors


# ===============================
# Cross-DB Duplicate Check
# ===============================

def check_db_duplicates(
    clean_rows: List[Dict],
    db,
    course_code: str,
    assessment_semester: str,
    assessment_acadyear: str,
    assessment_type: str
) -> Tuple[List[Dict], List[Dict]]:
    """
    Compare uploaded question hashes with DB to detect duplicates 
    in the same course + assessment scope.
    Returns:
        (rows_to_insert, duplicate_rows)
    """
    if not clean_rows:
        return [], []

    hashes = [r["question_hash"] for r in clean_rows]
    params = {
        "hashes": tuple(hashes),
        "course_code": course_code,
        "assessment_semester": assessment_semester,
        "assessment_acadyear": assessment_acadyear,
        "assessment_type": assessment_type,
    }

    query = text("""
        SELECT q.question_hash
        FROM questions q
        JOIN assessments a ON q.assessment_id = a.assessment_id
        JOIN courses c ON a.course_id = c.course_id
        WHERE c.course_code = :course_code
        AND a.assessment_semester = :assessment_semester
        AND a.assessment_acadyear = :assessment_acadyear
        AND a.assessment_type = :assessment_type
        AND q.question_hash IN :hashes
    """)


    result = db.execute(query, params).fetchall()
    existing_hashes = {r.question_hash for r in result}

    rows_to_insert = []
    duplicate_rows = []

    for row in clean_rows:
        if row["question_hash"] in existing_hashes:
            duplicate_rows.append({
                "question_text": row["question_text"][:80],
                "reason": (
                    "Duplicate question already exists "
                    "in this course and assessment scope"
                ),
            })
        else:
            rows_to_insert.append(row)

    return rows_to_insert, duplicate_rows


# ===============================
# Full Sanitization Pipeline
# ===============================

def run_sanitization_pipeline(
    df: pd.DataFrame,
    db,
    course_code: str,
    assessment_semester: str,
    assessment_acadyear: str,
    assessment_type: str
) -> Dict:
    """
    Run full sanitization pipeline before insertion.
    Returns structured report:
    {
        "clean_count": ...,
        "duplicates_count": ...,
        "error_count": ...,
        "clean_rows": [...],
        "duplicates": [...],
        "errors": [...]
    }
    """
    clean_rows, errors = sanitize_dataframe(df)
    rows_to_insert, duplicates = check_db_duplicates(
        clean_rows,
        db,
        course_code,
        assessment_semester,
        assessment_acadyear,
        assessment_type,
    )

    report = {
        "clean_count": len(rows_to_insert),
        "duplicates_count": len(duplicates),
        "error_count": len(errors),
        "clean_rows": rows_to_insert,
        "duplicates": duplicates,
        "errors": errors,
    }

    return report
