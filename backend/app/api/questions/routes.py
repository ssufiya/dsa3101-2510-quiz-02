"""
API routes for Questions
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text  # Add this for raw SQL
from typing import Optional, List
from app.db import get_db
from app.utils.file_parser import parse_csv, parse_csv_for_version
from app.utils.validation import validate_question_data

router = APIRouter()

# API #1: Filtered Questions Retrieval
@router.get("/")
async def get_questions(
    id: Optional[int] = Query(None, description="Filter by question ID"),
    subject: Optional[str] = Query(None, description="Filter by subject/course"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    semester: Optional[str] = Query(None, description="Filter by semester"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    is_latest: Optional[bool] = Query(True, description="Only return latest versions"),
    db: Session = Depends(get_db)
):
    """
    GET /api/questions
    
    Returns all questions with optional filters:
    - id: Filter by question ID
    - subject: Filter by course/subject
    - difficulty: Filter by difficulty level
    
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

        if id is not None:
            query_str += " AND q.question_id = :id"
            params["id"] = id

        if subject is not None:
            query_str += " AND (c.course_code ILIKE :subject OR c.course_name ILIKE :subject)"
            params["subject"] = f"%{subject}%"

        if difficulty is not None:
            query_str += " AND q.difficulty = :difficulty"
            params["difficulty"] = difficulty

        if semester is not None:
            query_str += " AND a.assessment_type ILIKE :semester"
            params["semester"] = f"%{semester}%"
        
        if topic is not None:
            query_str += " AND q.concepts ILIKE :topic"
            params["topic"] = f"%{topic}%"

        if is_latest:
            query_str += " AND q.is_latest = TRUE"

        query_str += " ORDER BY q.created_at DESC"

        result = db.execute(text(query_str), params)
        rows = result.fetchall()

        questions = []
        for row in rows:
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
    
    Returns full question content:
    - context
    - question
    - answer options
    - correct answer
    - uploaded files/images
    - all corresponding tags
    
    Used in: QuestionDetails, QuestionEdit
    """
    # Query the database for the question
    try: 
        query = text("""
            SELECT 
                q.*,
                c.course_code,
                c.course_name,
                a.assessment_type,
                ctx.context_text,
                att.attachment_name
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a ON q.assessment_id = a.assessment_id
            LEFT JOIN contexts ctx ON q.context_id = ctx.context_id
            LEFT JOIN attachments att ON q.attachment_id = att.attachment_id
            WHERE q.question_id = :id
        """)
    
        # Execute the query
        result = db.execute(query, {"id": id})
        row = result.fetchone()
        
        # Check if question exists
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Build response
        response_data = {
            "question_id": row.question_id,
            "question_text": row.question_text,
            "question_type": row.question_type,
            "difficulty": row.difficulty,
            "correct_answer": row.correct_answer,
            "concepts": row.concepts.spilt(',') if row.concepts else [],
            "course_code": row.course_code,
            "course_name": row.course_name,
            "assessment_type": row.assessment_type,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "version_number": row.version_number,
            "original_id": row.original_id,
            "is_latest": row.is_latest
        }

        if hasattr(row, 'correct_answer') and row.correct_answer:
            response_data["correct_answer"] = row.correct_answer
        
        # Add MCQ options if applicable
        if row.question_type == "MCQ":
            options = {}
            if hasattr(row, 'option_a') and row.option_a:
                options["A"] = row.option_a
            if hasattr(row, 'option_b') and row.option_b:
                options["B"] = row.option_b
            if hasattr(row, 'option_c') and row.option_c:
                options["C"] = row.option_c
            if hasattr(row, 'option_d') and row.option_d:
                options["D"] = row.option_d
            if hasattr(row, 'option_e') and row.option_e:
                options["E"] = row.option_e
            if options:
                response_data["options"] = options

        elif row.question_type == "True/False":
            response_data["options"] = {
            "True": "True",
            "False": "False"}
        
        # Add context if exists
        if row.context_text:
            response_data["context"] = {
                "context_text": row.context_text
            }
        
        # Add attachment if exists
        if row.attachment_name:
            response_data["uploaded_files"] = {
                "attachment_name": row.attachment_name,
                "attachment_url": f"/api/attachments/{row.attachment_name}"
            }
        
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
    GET /api/question/{id}/versions
    
    Retrieve all versions of the selected question.
    Example: For qns_id = 1, fetch all questions with original_id = 1
    
    Returns:
    - content (same detail level as API 1)
    - original_id
    - version_number
    - is_latest
    
    Used in: QuestionDetails
    """
    # TODO: Implement version fetching
    # Query: SELECT * FROM questions WHERE original_id = :id OR question_id = :id
    try:
        check_query = text("""
            SELECT question_type, original_id, question_id
            FROM questions
            WHERE question_id = :id
        """)

        result = db.execute(check_query, {"id": id})
        row = result.fetchone()

        if not row: 
            raise HTTPException(status_code=404, detail="question not found")
        
        original_id = row.original_id if row.original_id else row.question_id

        versions_query = text("""
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
                q.is_latest)
            FROM questions q
            LEFT JOIN courses c ON q.course_id = c.course_id
            LEFT JOIN assessments a on q.assessment_id = a.assessment_id
            WHERE q.original_id = :original_id OR (q.question_id = original_id AND q.original_id is NULL)
            ORDER BY q.version_number ASC
        """)

        result = db.execute(versions_query, {"original_id": original_id})
        rows = result.fetchall()

        versions = []
        for row in rows:
            versions.append({
                "question_id": row.question_id,
                "question_text": row.question_text,
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
            "original_id": original_id,
            "count": len(versions),
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
    - Ensure correct original_id
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
            SELECT original_id, version_number, is_latest, course_id, assessment_id
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
        
        original_id = current.original_id if current.original_id else id
        new_version_number = current.version_number + 1

        update_query = text("""
            UPDATE questions
            SET is_latest = FALSE
            WHERE question_id = :id
        """)
        db.execute(update_query, {"id": id})

        insert_fields = [
            "question_text", "question_type", "difficulty", "concepts", "course_id", "assessment_id", "version_number", "original_id", "is_latest"
        ]
        insert_values = [
            ":question_text", ":question_type", ":difficulty", ":concepts", ":course_id", ":assessment_id", ":version_number", ":original_id", "TRUE"
        ]

        params = {
            "question_text": question_data.get("question_text"),
            "question_type": question_data.get("question_type", current.question_type),
            "difficulty": question_data.get("difficulty"),
            "concepts": question_data.get("concepts"),
            "course_id": course_id,
            "assessment_id": assessment_id,
            "version_number": new_version_number,
            "original_id": original_id
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
            "original_id": original_id
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# API #5: Uploading a NEW Quiz/Question
@router.post("/upload")
async def upload_new_questions(
    file: UploadFile = File(...),
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    POST /api/questions/upload
    
    Add new questions into database.
    Should tag: version_number = 1, original_id = NULL, is_latest = TRUE
    
    Used in: QuestionUpload
    """
    # TODO: Implement new question upload
    # Set version_number = 1, original_id = NULL, is_latest = TRUE
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        contents = await file.read()
        questions_data = parse_csv(contents)

        if not questions_data:
            raise HTTPException(status_code=400, detail="No valid questions found in CSV")
        
        inserted_ids = []
        errors = []

        for idx, question in enumerate(questions_data):
            try: 
                validation_errors = validate_question_data(question)
                if validation_errors:
                    errors.append({
                        "row": idx + 1,
                        "errors": validation_errors
                    })
                    continue

                insert_fields = [
                    "question_text", "question_type", "difficulty",
                    "concepts", "course_id", "assessment_id",
                    "version_number", "original_id", "is_latest", "user_id"
                ]
                insert_values = [
                    ":question_text"," :question_type", ":difficulty",
                    ":concepts", ":course_id", ":assessment_id",
                    "1", "NULL", "TRUE", ":user_id"
                ]
                params = {
                    "question_text": question.get("question_text"),
                    "question_type": question.get("question_type"),
                    "difficulty": question.get("difficulty"),
                    "concepts": question.get("concepts"),
                    "course_id": question.get("course_id"),
                    "assessment_id": question.get("assessment_id"),
                    "user_id": user_id
                }

                result = db.execute(insert_query, {
                    "question_text": question.get("question"),
                    "question_type": question.get("question_type", "MCQ"),
                    "difficulty": question.get("difficulty"),
                    "option_a": question.get("option_a"),
                    "option_b": question.get("option_b"),
                    "option_c": question.get("option_c"),
                    "option_d": question.get("option_d"),
                    "option_e": question.get("option_e"),
                    "concepts": question.get("concepts"),
                    "course_id": question.get("course_id, 1"), # need to add lookup logic
                    "assessment_id": question.get("assessment_id", 1),
                    "user_id": user_id
                })


                if question.get("correct_answer"):
                    insert_fields.append("correct_answer")
                    insert_values.append(":correct_answer")
                    params["correct_answer"] = question.get("correct_answer")

                if question.get("option_a"):
                    insert_fields.append("option_a")
                    insert_values.append(":option_a")
                    params["option_a"] = question.get("option_a")

                if question.get("option_b"):
                    insert_fields.append("option_b")
                    insert_values.append(":option_b")
                    params["option_b"] = question.get("option_b")

                if question.get("option_c"):
                    insert_fields.append("option_c")
                    insert_values.append(":option_c")
                    params["option_c"] = question.get("option_c")

                if question.get("option_d"):
                    insert_fields.append("option_d")
                    insert_values.append(":option_d")
                    params["option_d"] = question.get("option_d")

                if question.get("option_e"):
                    insert_fields.append("option_e")
                    insert_values.append(":option_e")
                    params["option_e"] = question.get("option_e")

                insert_query = text(f"""
                    INSERT INTO questions ({', '.join(insert_fields)})
                    VALUES ({', '.join(insert_values)})
                    RETURNING question_id
                """)

                result = db.execute(insert_query, params)
                new_id = result.fetchone()[0]
                inserted_ids.append(new_id)

            except Exception as e:
                errors.append({
                    "row": idx + 1,
                    "error": str(e)
                })
            
        if inserted_ids:
            db.commit()
        else: 
            db.rollback()

        return {
            "success": len(inserted_ids) > 0,
            "message": f"Successfully uploaded {len(inserted_ids)} questions",
            "inserted_count": len(inserted_ids),
            "inserted_ids": inserted_ids,
            "errors": errors if errors else None
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")