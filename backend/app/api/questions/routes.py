"""
API routes for Questions
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text 
from typing import Optional, List
from rapidfuzz import fuzz
from difflib import HtmlDiff, unified_diff
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.db import get_db
from app.utils.file_parser import parse_csv, parse_csv_for_version
from app.utils.validation import validate_question_data
from pathlib import Path
import shutil
import subprocess
import pandas as pd 
import io


router = APIRouter()

# API #1: Filtered Questions Retrieval
@router.get("/")
async def get_questions(
    id: Optional[int] = Query(None, description="Filter by question ID"),
    subject: Optional[str] = Query(None, description="Filter by subject/course"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    topic: Optional[str] = Query(None, description="Filter by one or more topics"),
    match: Optional[str] = Query("any", description="Match mode for multi-topic filtering: 'any' (OR) or 'all' (AND)"),
    fuzzy: Optional[bool] = Query(True, description="Enable fuzzy matching for topic keywords"),
    is_latest: Optional[bool] = Query(True, description="Only return latest versions"),
    db: Session = Depends(get_db)
):
    """
    GET /api/questions
    
    Returns all questions with optional filters:
    - id: Filter by question ID
    - subject: Filter by course/subject
    - difficulty: Filter by difficulty level
    - topic: One or more topics (supports fuzzy match)
    
    Used in: QuestionLibrary, AssessmentPreview/QuestionCart, QuestionDetails
    """
    # TODO: Implement filtering logic
    # Return question with corresponding tags (course, semester, difficulty, etc.)
    try:
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

        # --- Filter: question ID ---
        if id is not None:
            query_str += " AND q.question_id = :id"
            params["id"] = id

        # --- Filter: subject / course ---
        if subject is not None:
            query_str += " AND (c.course_code ILIKE :subject OR c.course_name ILIKE :subject)"
            params["subject"] = f"%{subject}%"

        # --- Filter: difficulty ---
        if difficulty is not None:
            query_str += " AND q.difficulty = :difficulty"
            params["difficulty"] = difficulty

        # --- Filter: semester ---
        if semester is not None:
            query_str += " AND a.assessment_type ILIKE :semester"
            params["semester"] = f"%{semester}%"
            
        # --- Filter: only latest versions ---
        if is_latest:
            query_str += " AND q.is_latest = TRUE"

        # --- Execute base query first ---
        base_results = db.execute(text(query_str), params).fetchall()
        
        # --- Handle topics (with optional fuzzy match) ---
        if topic:
            topics = [t.strip().lower() for t in topic.split(",") if t.strip()]
            filtered_rows = []

            for row in base_results:
                question_topics = [t.strip().lower() for t in (row.concepts.split(",") if row.concepts else [])]

                # Fuzzy or exact matching logic
                matches = []
                for user_topic in topics:
                    if fuzzy:
                        # Compare with threshold 70/100 (threshold can be adjusted)
                        match_found = any(fuzz.partial_ratio(user_topic, qt) > 70 for qt in question_topics)
                    else:
                        match_found = any(user_topic in qt for qt in question_topics)
                    matches.append(match_found)

                # Apply match mode: 'all' or 'any'
                if (match == "all" and all(matches)) or (match != "all" and any(matches)):
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
    Returns full question content
    """
    try: 
        query = text("""
            SELECT 
                q.*,
                c.course_code,
                c.course_name,
                a.assessment_type,
                ctx.context_text,
                STRING_AGG(att.attachment_name, ', ') as attachment_names
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN contexts ctx ON q.context_id = ctx.context_id
            LEFT JOIN attachments att ON q.question_id = att.question_id
            WHERE q.question_id = :id
            GROUP BY q.question_id, c.course_code, c.course_name, a.assessment_type, ctx.context_text
        """)
    
        result = db.execute(query, {"id": id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Build response
        response_data = {
            "question_id": row.question_id,
            "question_text": row.question_text,
            "question_type": row.question_type,
            "difficulty": row.difficulty,
            "correct_answer": row.correct_answer,
            "concepts": row.concepts.split(',') if row.concepts else [],
            "course_code": row.course_code,
            "course_name": row.course_name,
            "assessment_type": row.assessment_type,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "version_number": row.version_number,
            "previous_version_id": row.previous_version_id
        }
        
        # Add MCQ options if applicable
        if row.question_type == "MCQ":
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

        elif row.question_type == "True/False":
            response_data["options"] = {
                "True": "True",
                "False": "False"
            }
        
        # Add context if exists
        if row.context_text:
            response_data["context"] = {
                "context_text": row.context_text
            }
        
        # Add attachments if exist
        if row.attachment_names:
            attachments = row.attachment_names.split(', ')
            response_data["uploaded_files"] = [
                {
                    "attachment_name": name,
                    "attachment_url": f"/api/attachments/{name}"
                }
                for name in attachments
            ]
        
        # Add tags
        response_data["tags"] = {
            "course": row.course_code,
            "assessment": row.assessment_type,
            "difficulty": row.difficulty,
            "concepts": row.concepts.split(',') if row.concepts else []
        }
        
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



# API #4: Uploading a NEW Question Version
@router.post("/{id}/editversion")
async def upload_new_version(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    POST /api/question/{id}/editversion
    
    When users edit, we reupload a csv file (of edited question content).
    This API should:
    - Increment version_number by 1 (using latest version_number where is_latest = TRUE)
    - Assign a new question_id
    - Ensure correct previouse_version_id
    - Change is_latest boolean
    
    A new row is created for every version, past versions are preserved.
    
    Used in: QuestionEdit
    """
    # TODO: Implement version creation
    try: 
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        contents = await file.read()
        question_data = parse_csv_for_version(contents)

        validation_errors = validate_question_data(question_data)
        if validation_errors:
            raise HTTPException(status_code=400, detail={"errors": validation_errors})
        
        current_query = text("""
            SELECT previouse_version_id, version_number, is_latest, course_id, assessment_id
            FROM questions
            WHERE question_id = "id
        """)

        result = db.execute(current_query, {"id": id})
        current = result.fetchone()

        if not current:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Lookup course_id
        course_lookup = text("""
            SELECT course_id FROM courses 
            WHERE course_code = :course_code
        """)
        course_result = db.execute(course_lookup, {"course_code": question_data.get("course_code")})
        course_row = course_result.fetchone()
        course_id = course_row.course_id if course_row else current.course_id

        # Lookup assessment_id
        assessment_lookup = text("""
            SELECT assessment_id FROM assessments 
            WHERE assessment_type = :assessment_type
        """)
        assessment_result = db.execute(assessment_lookup, {"assessment_type": question_data.get("assessment_type")})
        assessment_row = assessment_result.fetchone()
        assessment_id = assessment_row.assessment_id if assessment_row else current.assessment_id
        
        previouse_version_id = current.previouse_version_id if current.previouse_version_id else id
        new_version_number = current.version_number + 1

        update_query = text("""
            INSERT INTO questions (..., previous_version_id) 
            VALUES (..., :old_question_id)
        """)
        db.execute(update_query, {"id": id})

        insert_fields = [
            "question_text", "question_type", "difficulty", "concepts", "course_id", "assessment_id", "version_number", "previous_version_id", "is_latest"
        ]
        insert_values = [
            ":question_text", ":question_type", ":difficulty", ":concepts", ":course_id", ":assessment_id", ":version_number", ":previous_version_id", "TRUE"
        ]

        params = {
            "question_text": question_data.get("question_text"),
            "question_type": question_data.get("question_type", current.question_type),
            "difficulty": question_data.get("difficulty"),
            "concepts": question_data.get("concepts"),
            "course_id": course_id,
            "assessment_id": assessment_id,
            "version_number": new_version_number,
            "previous_version_id": previous_version_id
        }

        if question_data.get("correct_answer"):
            insert_fields.append("correct_answer")
            insert_values.append(":correct_answer")
            params["correct_answer"] = question_data.get("correct_answer")

        if question_data.get("option_a"):
            insert_fields.append("option_a")
            insert_values.append(":option_a")
            params["option_a"] = question_data.get("option_a")

        if question_data.get("option_b"):
            insert_fields.append("option_b")
            insert_values.append(":option_b")
            params["option_b"] = question_data.get("option_b")

        if question_data.get("option_c"):
            insert_fields.append("option_c")
            insert_values.append(":option_c")
            params["option_c"] = question_data.get("option_c")

        if question_data.get("option_d"):
            insert_fields.append("option_d")
            insert_values.append(":option_d")
            params["option_d"] = question_data.get("option_d")

        if question_data.get("option_e"):
            insert_fields.append("option_e")
            insert_values.append(":option_e")
            params["option_e"] = question_data.get("option_e")

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
            "new_question_id": new_id,
            "version_number": new_version_number,
            "previous_version_id": previous_version_id
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# API #5: Uploading a NEW Quiz/Question

def validate_question_data(question: dict):
    """Check required fields; returns list of error strings"""
    errors = []
    if not question.get("question_text"):
        errors.append("Missing required field; question_text")
    if not question.get("difficulty"):
        errors.append("Missing required field; difficulty")
    if not question.get("concepts"):
        errors.append("Missing required field; concepts")
    return errors


def parse_csv(csv_bytes: bytes):
    """Parse CSV bytes into list of dicts"""
    df = pd.read_csv(io.BytesIO(csv_bytes))
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    return df.to_dict(orient="records")

@router.post("/upload")
async def upload_new_questions(
    file: UploadFile = File(...),
    user_id: int = None,  # optional
    db: Session = Depends(get_db)
):
    try:
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        contents = await file.read()

        # ===== STEP 0: PARSE COURSE CODE FROM FILENAME =====
        filename = Path(file.filename).name
        course_code = filename.split("_")[0]

        result = db.execute(
            text("SELECT course_id, course_name FROM courses WHERE course_code = :code LIMIT 1"),
            {"code": course_code}
        )
        course_row = result.fetchone()
        if not course_row:
            raise HTTPException(status_code=400, detail=f"Course code '{course_code}' not found in database")
        course_id, course_name = course_row

        # ===== STEP 1: READ CSV =====
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

        # ===== STEP 2: SAVE CSV TO DATA FOLDER =====
        data_dir = Path(__file__).parent.parent.parent.parent / "quizbank-db" / "db-init" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        dest_file_path = data_dir / file.filename
        if dest_file_path.exists():
            raise HTTPException(status_code=400, detail=f"File {file.filename} already exists")
        with open(dest_file_path, "wb") as f:
            f.write(contents)

        # ===== STEP 3: INSERT QUESTIONS =====
        inserted_count = 0
        errors = []

        for idx, question in enumerate(questions_data, 1):
            try:
                # Validate
                validation_errors = validate_question_data(question)
                if validation_errors:
                    errors.append({
                        "row": idx,
                        "question": question.get("question_text", "N/A")[:50],
                        "error": validation_errors
                    })
                    continue

                # Determine created_by safely
                created_by_id = None
                if user_id:
                    res = db.execute(text("SELECT user_id FROM users WHERE user_id = :uid"), {"uid": user_id})
                    if res.fetchone():
                        created_by_id = user_id

                # Build insert query
                fields = ["question_text", "difficulty", "concepts", "course_id", "version_number"]
                values = [":question_text", ":difficulty", ":concepts", ":course_id", "1"]
                params = {
                    "question_text": question.get("question_text"),
                    "difficulty": question.get("difficulty"),
                    "concepts": question.get("concepts"),
                    "course_id": course_id
                }

                if created_by_id:
                    fields.append("created_by")
                    values.append(":created_by")
                    params["created_by"] = created_by_id

                for field in ["correct_answer", "option_a", "option_b", "option_c", "option_d", "option_e",
                              "explanation", "points", "question_number", "sub_question_number", "question_type", "context"]:
                    if question.get(field) is not None:
                        fields.append(field)
                        values.append(f":{field}")
                        params[field] = question.get(field)

                query = f"INSERT INTO questions ({', '.join(fields)}) VALUES ({', '.join(values)})"
                db.execute(text(query), params)
                inserted_count += 1

            except Exception as e:
                errors.append({
                    "row": idx,
                    "question": question.get("question_text", "N/A")[:50],
                    "error": str(e)
                })
                continue

        if inserted_count > 0:
            db.commit()
            return {
                "success": True,
                "message": f"File saved and {inserted_count} questions loaded successfully",
                "file_path": str(dest_file_path),
                "questions_loaded": inserted_count,
                "error_count": len(errors),
                "errors": errors if errors else None
            }
        else:
            db.rollback()
            return {
                "success": False,
                "message": "File saved but no questions were loaded. Check errors for details.",
                "file_path": str(dest_file_path),
                "questions_loaded": 0,
                "error_count": len(errors),
                "errors": errors
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload questions: {str(e)}")

# API #6: Version Diff
@router.get("/{id}/diff/{version_id}")
async def get_question_diff(id: int, version_id: int, db: Session = Depends(get_db)):
    """
    Compare two versions of a question (like Git diff).

    GET /api/questions/{id}/diff/{version_id}
    - id: latest or current question ID
    - version_id: ID of the question version to compare against
    """
    # Fetch both versions
    query = text("SELECT * FROM questions WHERE question_id IN (:id, :version_id)")
    result = db.execute(query, {"id": id, "version_id": version_id}).fetchall()
    
    if len(result) < 2:
        raise HTTPException(status_code=404, detail="One or both question versions not found")

    current = dict(result[0]._mapping)
    previous = dict(result[1]._mapping)

    fields_to_compare = [
        "question_text", "option_a", "option_b", "option_c", "option_d", "option_e",
        "correct_answer", "difficulty", "concepts"
    ]

    differences = {}
    for field in fields_to_compare:
        old = str(previous.get(field) or "")
        new = str(current.get(field) or "")
        if old != new:
            diff = "\n".join(unified_diff(
                old.splitlines(),
                new.splitlines(),
                fromfile="Previous",
                tofile="Current",
                lineterm=""
            ))
            differences[field] = diff

    if not differences:
        return {"success": True, "message": "No differences found — identical versions"}

    return {
        "success": True,
        "question_id": id,
        "compared_to": version_id,
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


