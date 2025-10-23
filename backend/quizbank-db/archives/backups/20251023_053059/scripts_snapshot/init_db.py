"""
init_db.py
Initializes the QuizBank PostgreSQL database:
- Converts XLSX files in backend/data → CSVs in db-init/data
- Seeds courses, assessments, contexts, questions
- Runs only once at first startup
"""
import os
import sys
import time
from pathlib import Path
from sqlalchemy import text
from app.db.connection import engine, SessionLocal
from .xlsx_to_csv import convert_xlsx_to_csv

# === Paths ===
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

DATA_XLSX = ROOT_DIR / "data"
DATA_CSV = ROOT_DIR / "quizbank-db" / "db-init" / "data"
BACKUP_SCRIPT = ROOT_DIR / "quizbank-db" / "scripts" / "backup_db.sh"
RESTORE_SCRIPT = ROOT_DIR / "quizbank-db" / "scripts" / "restore_db.sh"

# === Utility ===
def wait_for_db():
    print("Waiting for database connection...")
    for _ in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connected\n")
            return True
        except Exception:
            time.sleep(1)
    print("❌ Database not responding")
    return False


def load_seed_files(session):
    """Executes all seed SQL scripts in db-init in order"""
    seed_dir = ROOT_DIR / "quizbank-db" / "db-init"
    seed_files = sorted(seed_dir.glob("0*_*.sql"))

    for file in seed_files:
        print(f"⚙️ Running seed file: {file.name}")
        with open(file, "r") as f:
            sql = f.read()
        session.execute(text(sql))
        session.commit()
    print("✅ All seed SQL files executed.\n")


def main():
    print("\n==============================")
    print("📦 Initializing QuizBank DB")
    print("==============================\n")

    if not wait_for_db():
        sys.exit(1)

    # === Step 1: Convert XLSX → CSV ===
    print("🧾 Converting Excel sheets to CSV...")
    convert_xlsx_to_csv()
    print("✅ Conversion complete.\n")

    # === Step 2: Seed database ===
    session = SessionLocal()
    try:
        load_seed_files(session)
    except Exception as e:
        print(f"⚠️ Failed to seed database: {e}")
    finally:
        session.close()

    # === Step 3: Backup ===
    print("🗄️  Creating initial backup...")
    exit_code = os.system(f"bash {BACKUP_SCRIPT}")
    if exit_code == 0:
        print("✅ Initialization complete with backup.\n")
    else:
        print("⚠️ Backup script failed.\n")


if __name__ == "__main__":
    main()
