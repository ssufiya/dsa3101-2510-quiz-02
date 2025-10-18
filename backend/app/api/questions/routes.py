"""
API routes for Questions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text  # Add this for raw SQL
from app.db import get_db

router = APIRouter()

# API #1: Filtered Questions Retrieval
@router.get("/", response_model=QuestionListResponse)
async def get_questions(
    id: Optional[int] = Query(None, description="Filter by question ID"),
    subject: Optional[str] = Query(None, description="Filter by subject/course"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
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
    pass



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
        "concepts": row.concepts,
        "course_code": row.course_code,
        "course_name": row.course_name,
        "assessment_type": row.assessment_type,
        "created_at": row.created_at.isoformat() if row.created_at else None
    }
    
    # Add MCQ options if applicable
    if row.question_type == "MCQ":
        response_data["options"] = {
            "A": row.option_a,
            "B": row.option_b,
            "C": row.option_c,
            "D": row.option_d,
            "E": row.option_e
        }
    
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
    
    return response_data


        
        

# API #3: Fetching ALL Versions
@router.get("/{id}/versions", response_model=List[QuestionResponse])
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
    pass

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
    pass

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
    pass