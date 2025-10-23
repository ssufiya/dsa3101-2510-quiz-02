"""
Load questions from master CSV file into database
Handles courses, assessments, and questions from one CSV
"""
import pandas as pd
import os
import time
from pathlib import Path
from app import app, db, Question, Course, Assessment, User

def wait_for_db():
    """Wait for database to be ready"""
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                db.engine.connect()
                print("✅ Database connection established")
                return True
        except Exception as e:
            retry_count += 1
            print(f"⏳ Waiting for database... ({retry_count}/{max_retries})")
            time.sleep(2)
    
    print("❌ Could not connect to database")
    return False

def load_master_csv(csv_path):
    """
    Load questions from master CSV that contains all info
    
    Expected CSV columns (flexible - handles missing columns):
    - question_text (required)
    - question_type (MCQ, T/F, Essay, etc.)
    - option_a, option_b, option_c, option_d, option_e
    - correct_answer
    - difficulty (Easy, Medium, Hard)
    - concepts (comma-separated)
    - course_code (e.g., DSA1101)
    - course_name (optional)
    - assessment_type (Quiz, Exam, etc.)
    - assessment_acadyear (2023/2024)
    """
    print(f"📂 Loading {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    print(f"   Found {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")
    
    # Validate required column
    if 'question_text' not in df.columns:
        raise ValueError("CSV must have 'question_text' column")
    
    added_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Get or create course
            course = None
            if 'course_code' in df.columns and pd.notna(row.get('course_code')):
                course_code = str(row['course_code']).strip()
                course = Course.query.filter_by(course_code=course_code).first()
                
                if not course:
                    # Get course name from CSV or generate default
                    course_name = str(row.get('course_name', f'Course {course_code}')).strip() if pd.notna(row.get('course_name')) else f'Course {course_code}'
                    
                    course = Course(
                        course_code=course_code,
                        course_name=course_name
                    )
                    db.session.add(course)
                    db.session.flush()
                    print(f"   ✨ Created course: {course_code}")
            
            # Get or create assessment
            assessment = None
            if course and 'assessment_type' in df.columns and pd.notna(row.get('assessment_type')):
                assessment_type = str(row['assessment_type']).strip()
                assessment_acadyear = str(row.get('assessment_acadyear', '')).strip() if pd.notna(row.get('assessment_acadyear')) else None
                
                # Try to find existing assessment
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
                        created_by=1
                    )
                    db.session.add(assessment)
                    db.session.flush()
                    print(f"   ✨ Created assessment: {assessment_type} for {course_code}")
            
            # Create question
            question = Question(
                assessment_id=assessment.assessment_id if assessment else None,
                course_id=course.course_id if course else None,
                context_id=None,  # Add if you have context data
                attachment_id=None,  # Add if you have attachments
                question_text=str(row['question_text']).strip(),
                question_type=str(row.get('question_type', '')).strip() if pd.notna(row.get('question_type')) else None,
                option_a=str(row.get('option_a', '')).strip() if pd.notna(row.get('option_a')) else None,
                option_b=str(row.get('option_b', '')).strip() if pd.notna(row.get('option_b')) else None,
                option_c=str(row.get('option_c', '')).strip() if pd.notna(row.get('option_c')) else None,
                option_d=str(row.get('option_d', '')).strip() if pd.notna(row.get('option_d')) else None,
                option_e=str(row.get('option_e', '')).strip() if pd.notna(row.get('option_e')) else None,
                correct_answer=str(row.get('correct_answer', '')).strip() if pd.notna(row.get('correct_answer')) else None,
                difficulty=str(row.get('difficulty', '')).strip() if pd.notna(row.get('difficulty')) else None,
                concepts=str(row.get('concepts', '')).strip() if pd.notna(row.get('concepts')) else None,
                created_by=1,
                version_number=1,
                previous_version_id=None
            )
            
            db.session.add(question)
            added_count += 1
            
            # Commit in batches of 100 for better performance
            if added_count % 100 == 0:
                db.session.commit()
                print(f"   💾 Committed {added_count} questions...")
                
        except Exception as e:
            print(f"   ⚠️  Error on row {idx + 2}: {str(e)}")
            continue
    
    # Final commit
    db.session.commit()
    return added_count

def load_sample_data():
    """Load sample data from CSV files"""
    
    if not wait_for_db():
        return
    
    with app.app_context():
        try:
            # Check if data already loaded
            existing_count = Question.query.count()
            if existing_count > 0:
                print(f"✅ Database already has {existing_count} questions, skipping sample data load")
                return
            
            # Create default user
            default_user = User.query.filter_by(user_id=1).first()
            if not default_user:
                default_user = User(
                    user_id=1,
                    username='admin',
                    password_hash='placeholder_hash'
                )
                db.session.add(default_user)
                db.session.commit()
                print("✅ Created default admin user")
            
            # Find data folder
            data_dir = Path('data')
            if not data_dir.exists():
                print(f"⚠️  No data folder found, skipping sample data load")
                return
            
            # Load all CSV files
            csv_files = list(data_dir.glob('*.csv'))
            
            if not csv_files:
                print(f"⚠️  No CSV files found in data/ folder")
                return
            
            print(f"📁 Found {len(csv_files)} CSV file(s)")
            
            total_added = 0
            
            for csv_file in sorted(csv_files):
                print(f"\n{'='*60}")
                count = load_master_csv(csv_file)
                total_added += count
                print(f"✅ Loaded {count} questions from {csv_file.name}")
            
            print(f"\n{'='*60}")
            print(f"🎉 Successfully loaded {total_added} total questions!")
            print(f"📊 Summary:")
            print(f"   Courses: {Course.query.count()}")
            print(f"   Assessments: {Assessment.query.count()}")
            print(f"   Questions: {Question.query.count()}")
            
        except Exception as e:
            print(f"❌ Error loading sample data: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    load_sample_data()