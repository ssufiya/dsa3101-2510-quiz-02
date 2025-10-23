"""
update_questions.py
Used to append or update new data (questions, contexts, attachments)
after initial database initialization.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import shutil
import time
from pathlib import Path
from sqlalchemy import text
from app.db.connection import engine, SessionLocal
from app.utils.file_parser import parse_csv

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
BACKUP_SCRIPT = ROOT_DIR / "quizbank-db" / "scripts" / "backup_db.sh"
ATTACHMENT_DIR = DATA_DIR / "png_folder"  # where attachments are stored

# ------------------ Utility ------------------
def wait_for_db():
    for _ in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            time.sleep(1)
    return False


# ------------------ Context Updates ------------------
def update_contexts(session):
    print("🔁 Updating contexts...")
    for csv_file in sorted(DATA_DIR.glob("*_contexts.csv")):
        print(f"📄 Reading {csv_file.name}")
        with open(csv_file, "rb") as f:
            contexts = parse_csv(f.read())

        for c in contexts:
            session.execute(
                text("""
                    INSERT INTO contexts (context_global_id, context_local_id, context_text)
                    VALUES (:gid, :lid, :text)
                    ON CONFLICT (context_global_id)
                    DO UPDATE SET context_text = EXCLUDED.context_text;
                """),
                {
                    "gid": c.get("Global Context ID", ""),
                    "lid": c.get("Context ID", ""),
                    "text": c.get("Context Text", "")
                }
            )
        session.commit()
        print(f"✅ Updated from {csv_file.name}")


# ------------------ Question Updates ------------------
def update_questions(session):
    print("🔁 Updating questions from latest CSV files...")
    for csv_file in sorted(DATA_DIR.glob("*_questions.csv")):
        print(f"📄 Reading {csv_file.name}")
        with open(csv_file, "rb") as f:
            questions = parse_csv(f.read())

        for q in questions:
            if not q.get("Question Text"):
                continue
            session.execute(
                text("""
                    INSERT INTO questions (
                        course_id, assessment_id, context_id, question_text, question_type,
                        option_a, option_b, option_c, option_d, option_e,
                        correct_answer, explanation, points, difficulty, concepts
                    )
                    VALUES (
                        (SELECT course_id FROM courses WHERE course_code = :course LIMIT 1),
                        (SELECT assessment_id FROM assessments WHERE assessment_type = :assessment LIMIT 1),
                        (SELECT context_id FROM contexts WHERE context_global_id = :context LIMIT 1),
                        :text, :type, :a, :b, :c, :d, :e, :ans, :exp, :points, :diff, :concepts
                    )
                    ON CONFLICT (course_id, assessment_id, question_text)
                    DO UPDATE SET
                        correct_answer = EXCLUDED.correct_answer,
                        explanation = EXCLUDED.explanation,
                        difficulty = EXCLUDED.difficulty;
                """),
                {
                    "course": q.get("Course Code", ""),
                    "assessment": q.get("Assessment Type", ""),
                    "context": q.get("Global Context ID", ""),
                    "text": q.get("Question Text", ""),
                    "type": q.get("Question Type", ""),
                    "a": q.get("Option A", ""),
                    "b": q.get("Option B", ""),
                    "c": q.get("Option C", ""),
                    "d": q.get("Option D", ""),
                    "e": q.get("Option E", ""),
                    "ans": q.get("Correct Answer", ""),
                    "exp": q.get("Explanation", ""),
                    "points": q.get("Points", 1),
                    "diff": q.get("Difficulty", ""),
                    "concepts": q.get("Concepts", "")
                }
            )
        session.commit()
        print(f"✅ Updated from {csv_file.name}")


# ------------------ Attachment Updates ------------------
def update_attachments():
    print("🖼️ Updating attachments...")
    ATTACHMENT_DIR.mkdir(exist_ok=True)
    for file in DATA_DIR.glob("*.*"):
        if file.suffix.lower() in [".png", ".jpg", ".jpeg", ".pdf", ".r", ".csv"]:
            target = ATTACHMENT_DIR / file.name
            shutil.copy(file, target)
            print(f"✅ Copied {file.name} to {ATTACHMENT_DIR}/")
    print("✅ All attachments processed.\n")


# ------------------ Main ------------------
def main():
    print("\n==============================")
    print("🔄 Updating QuizBank DB")
    print("==============================\n")

    if not wait_for_db():
        sys.exit("❌ Database not reachable")

    session = SessionLocal()
    try:
        update_contexts(session)
        update_questions(session)
        update_attachments()
    except Exception as e:
        print(f"❌ Update failed: {e}")
        session.rollback()
    finally:
        session.close()

    print("🗄️ Creating backup after update...")
    os.system(f"bash {BACKUP_SCRIPT}")
    print("✅ Update completed and backed up.\n")

    # Cleanup CSV/XLSX after ingestion
    for f in DATA_DIR.glob("*.csv"):
        f.unlink()
    print("🧹 Cleaned up CSV files after processing.")


if __name__ == "__main__":
    main()
