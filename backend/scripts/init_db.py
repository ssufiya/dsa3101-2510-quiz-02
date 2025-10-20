"""
Database initialization script
Loads CSV files from backend/data/ folder into database
Uses existing app/db/connection.py and matches actual schema
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text
import csv
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from YOUR existing db/connection.py
from app.db.connection import engine, SessionLocal
from app.utils.file_parser import parse_csv
from app.utils.validation import validate_question_data


def auto_create_courses_and_assessments(session, data_dir):
    """
    Automatically create courses and assessments from question CSV files
    """
    print("  Extracting courses and assessments from question files...")
    
    courses_set = set()
    assessments_set = set()
    
    # Read all CSV files
    for csv_file in data_dir.glob('*.csv'):
        if csv_file.name in ['courses.csv', 'assessments.csv', 'Template.csv']:
            continue
            
        try:
            with open(csv_file, 'rb') as f:
                contents = f.read()
            questions_data = parse_csv(contents)
            
            for question in questions_data:
                if question.get('course_code') and question.get('course_name'):
                    courses_set.add((question['course_code'], question['course_name']))
                if question.get('assessment_type'):
                    assessments_set.add(question['assessment_type'])
        except Exception as e:
            print(f"  ⚠ Could not read {csv_file.name}: {e}")
    
    # Insert unique courses
    for course_code, course_name in sorted(courses_set):
        result = session.execute(
            text("SELECT course_id FROM courses WHERE course_code = :code"),
            {"code": course_code}
        )
        if not result.fetchone():
            session.execute(
                text("INSERT INTO courses (course_code, course_name) VALUES (:code, :name)"),
                {"code": course_code, "name": course_name}
            )
    session.commit()
    print(f"  ✓ Auto-created {len(courses_set)} courses")
    
    # Insert unique assessments
    for assessment_type in sorted(assessments_set):
        result = session.execute(
            text("SELECT assessment_id FROM assessments WHERE assessment_type = :type"),
            {"type": assessment_type}
        )
        if not result.fetchone():
            session.execute(
                text("INSERT INTO assessments (assessment_type) VALUES (:type)"),
                {"type": assessment_type}
            )
    session.commit()
    print(f"  ✓ Auto-created {len(assessments_set)} assessments\n")


def wait_for_db():
    """Wait for database to be ready"""
    print("Waiting for database connection...")
    max_retries = 30
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ Database connected\n")
            return True
        except Exception as e:
            if i == max_retries - 1:
                print(f"✗ Failed to connect to database: {e}")
                return False
            time.sleep(1)
    return False


def load_courses(session, csv_path):
    """Load courses from CSV"""
    print(f"Loading courses from {csv_path}...")
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            # Check if course already exists
            result = session.execute(
                text("SELECT course_id FROM courses WHERE course_code = :code"),
                {"code": row['course_code']}
            )
            if result.fetchone():
                print(f"  Course {row['course_code']} already exists, skipping...")
                continue
            
            # Insert course
            session.execute(
                text("""
                    INSERT INTO courses (course_code, course_name)
                    VALUES (:code, :name)
                """),
                {"code": row['course_code'], "name": row['course_name']}
            )
            count += 1
        
        session.commit()
        print(f"  ✓ Loaded {count} courses")


def load_assessments(session, csv_path):
    """Load assessments from CSV"""
    print(f"Loading assessments from {csv_path}...")
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            # Check if assessment already exists
            result = session.execute(
                text("SELECT assessment_id FROM assessments WHERE assessment_type = :type"),
                {"type": row['assessment_type']}
            )
            if result.fetchone():
                print(f"  Assessment {row['assessment_type']} already exists, skipping...")
                continue
            
            # Insert assessment
            session.execute(
                text("""
                    INSERT INTO assessments (assessment_type)
                    VALUES (:type)
                """),
                {"type": row['assessment_type']}
            )
            count += 1
        
        session.commit()
        print(f"  ✓ Loaded {count} assessments")


def load_questions(session, csv_path):
    """Load questions from CSV - matching YOUR actual schema"""
    print(f"Loading questions from {csv_path}...")
    
    with open(csv_path, 'rb') as f:
        contents = f.read()
    
    questions_data = parse_csv(contents)
    count = 0
    errors = 0
    
    for idx, question in enumerate(questions_data, 1):
        try:
            # Validate
            validation_errors = validate_question_data(question)
            if validation_errors:
                print(f"  ✗ Row {idx}: Validation errors: {validation_errors}")
                errors += 1
                continue
            
            # Get course_id
            result = session.execute(
                text("SELECT course_id FROM courses WHERE course_code = :code OR course_name = :name LIMIT 1"),
                {"code": question.get('course_code'), "name": question.get('course_name')}
            )
            course_row = result.fetchone()
            if not course_row:
                print(f"  ✗ Row {idx}: Course not found: {question.get('course_code')}")
                errors += 1
                continue
            course_id = course_row[0]
            
            # Get assessment_id
            result = session.execute(
                text("SELECT assessment_id FROM assessments WHERE assessment_type = :type LIMIT 1"),
                {"type": question.get('assessment_type')}
            )
            assessment_row = result.fetchone()
            if not assessment_row:
                print(f"  ✗ Row {idx}: Assessment not found: {question.get('assessment_type')}")
                errors += 1
                continue
            assessment_id = assessment_row[0]
            
            # Build insert query matching YOUR schema
            fields = [
                "question_text",        # Required
                "difficulty",           # Required
                "concepts",             # Required
                "course_id",            # Required FK
                "assessment_id",        # Required FK
                "version_number",       # Default 1
                "created_by"            # Can be NULL
            ]
            values = [
                ":question_text",
                ":difficulty",
                ":concepts",
                ":course_id",
                ":assessment_id",
                "1",                    # version_number always 1 for new questions
                ":created_by"
            ]
            
            params = {
                "question_text": question.get("question_text"),
                "difficulty": question.get("difficulty"),
                "concepts": question.get("concepts"),
                "course_id": course_id,
                "assessment_id": assessment_id,
                "created_by": question.get("created_by", 1)  # Default user_id = 1
            }
            
            # Add optional fields (only if provided)
            if question.get("correct_answer"):
                fields.append("correct_answer")
                values.append(":correct_answer")
                params["correct_answer"] = question.get("correct_answer")
            
            if question.get("option_a"):
                fields.append("option_a")
                values.append(":option_a")
                params["option_a"] = question.get("option_a")
            
            if question.get("option_b"):
                fields.append("option_b")
                values.append(":option_b")
                params["option_b"] = question.get("option_b")
            
            if question.get("option_c"):
                fields.append("option_c")
                values.append(":option_c")
                params["option_c"] = question.get("option_c")
            
            if question.get("option_d"):
                fields.append("option_d")
                values.append(":option_d")
                params["option_d"] = question.get("option_d")
            
            if question.get("option_e"):
                fields.append("option_e")
                values.append(":option_e")
                params["option_e"] = question.get("option_e")
            
            # Note: context_id and attachment_id would need separate handling
            # For now, they'll be NULL
            
            # Insert question
            query = f"""
                INSERT INTO questions ({', '.join(fields)})
                VALUES ({', '.join(values)})
            """
            session.execute(text(query), params)
            count += 1
            
        except Exception as e:
            print(f"  ✗ Row {idx}: Error - {str(e)}")
            errors += 1
    
    
    session.commit()
    


def main():
    """Main initialization function"""
    print("\n" + "="*50)
    print("Database Initialization")
    print("="*50 + "\n")
    
    # Convert XLSX files to CSV first
    data_dir = Path(__file__).parent.parent / 'data'
    if data_dir.exists():
        from scripts.xlsx_to_csv import convert_xlsx_to_csv
        convert_xlsx_to_csv()
    
    # Wait for database to be ready
    if not wait_for_db():
        sys.exit(1)
    
    # Create session using YOUR existing SessionLocal
    session = SessionLocal()
    
    try:
        # Check if schema is initialized
        try:
            result = session.execute(text("SELECT COUNT(*) FROM courses"))
            print("✓ Database schema already initialized\n")
        except Exception:
            print("⚠ Database schema not found. Make sure SQL files in quizbank-db/db-init/ ran correctly.\n")
            session.rollback()
        
        # Define data directory
        if not data_dir.exists():
            print(f"✗ Data directory not found: {data_dir}")
            print("Please create backend/data/ folder with CSV files")
            return
        
        # Load data in order
        print("Loading data files...\n")
        
        # Check if courses already exist (from 02_seed_courses.sql)
        result = session.execute(text("SELECT COUNT(*) FROM courses"))
        existing_courses = result.fetchone()[0]
        
        if existing_courses > 0:
            print(f"✓ Found {existing_courses} existing courses (from seed file)\n")
        else:
            # Load courses.csv if exists, or auto-create
            courses_file = data_dir / 'courses.csv'
            if courses_file.exists():
                load_courses(session, courses_file)
            else:
                print(f"⚠ Warning: {courses_file} not found")
                print("  Creating courses from question files...")
                auto_create_courses_and_assessments(session, data_dir)
        
        # Load assessments
        result = session.execute(text("SELECT COUNT(*) FROM assessments"))
        existing_assessments = result.fetchone()[0]
        
        if existing_assessments > 0:
            print(f"✓ Found {existing_assessments} existing assessments\n")
        else:
            assessments_file = data_dir / 'assessments.csv'
            if assessments_file.exists():
                load_assessments(session, assessments_file)
            else:
                print(f"⚠ Warning: {assessments_file} not found")
                print("  Creating assessments from question files...")
                if existing_courses == 0:  # Only auto-create if we haven't done it above
                    auto_create_courses_and_assessments(session, data_dir)
        
        # Load ALL CSV files as question files (except courses, assessments, Template)
        all_csv_files = sorted(data_dir.glob('*.csv'))
        question_files = [f for f in all_csv_files if f.name not in ['courses.csv', 'assessments.csv', 'Template.csv']]
        
        if question_files:
            print(f"Found {len(question_files)} question file(s) to load:\n")
            for qfile in question_files:
                load_questions(session, qfile)
        else:
            print(f"⚠ Warning: No question files found in {data_dir}")
        
        print("\n" + "="*50)
        print("✓ Database initialization complete!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
