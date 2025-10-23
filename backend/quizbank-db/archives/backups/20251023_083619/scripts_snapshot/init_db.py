"""
Idempotent database initialization
- Applies schema from db-init/01_schema.sql
- Reads CSV/XLSX from backend/data
- Seeds courses, assessments, contexts, questions (matching your schema)
- Runs ONCE only (uses system_meta.sentinel)
"""

from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from sqlalchemy import text

# ── Path shims so "import app..." works no matter where this script is run ─────
SCRIPT_DIR = Path(__file__).resolve().parent               # .../backend/quizbank-db/scripts
BACKEND_DIR = SCRIPT_DIR.parent.parent                      # .../backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Your existing infrastructure
from app.db.connection import engine, SessionLocal
from app.utils.file_parser import parse_csv
from app.utils.validation import validate_question_data

# Locations
DATA_DIR = BACKEND_DIR / "data"
DB_INIT_DIR = BACKEND_DIR / "quizbank-db" / "db-init"

# ── Helpers ───────────────────────────────────────────────────────────────────
def wait_for_db(timeout=30) -> bool:
    print("⏳ Waiting for database connection...")
    for _ in range(timeout):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connected.\n")
            return True
        except Exception:
            time.sleep(1)
    print("❌ Database not responding.")
    return False

def run_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    print(f"🧱 Applying SQL: {path.name}")
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)
    print(f"✅ Applied: {path.name}\n")

def ensure_system_meta(session) -> None:
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS system_meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """))
    session.commit()

def already_seeded(session) -> bool:
    ensure_system_meta(session)
    row = session.execute(
        text("SELECT value FROM system_meta WHERE key = 'seeded_by_python' LIMIT 1")
    ).fetchone()
    return row is not None

def mark_seeded(session) -> None:
    session.execute(
        text("""
            INSERT INTO system_meta(key, value)
            VALUES ('seeded_by_python', NOW()::text)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """)
    )
    session.commit()

def try_convert_xlsx_to_csv() -> None:
    """If xlsx_to_csv.py exists, run convert_xlsx_to_csv() to produce CSVs into backend/data."""
    try:
        try:
            from .xlsx_to_csv import convert_xlsx_to_csv  # when run as module
        except Exception:
            sys.path.insert(0, str(SCRIPT_DIR))           # when run as a file
            from xlsx_to_csv import convert_xlsx_to_csv
        print("🧾 Converting XLSX → CSV...")
        convert_xlsx_to_csv()
        print("✅ XLSX conversion complete.\n")
    except Exception as e:
        print(f"ℹ️ XLSX→CSV converter not available or failed: {e}\n")

# ── Loaders (Python-based seeding logic) ──────────────────────────────────────
def auto_create_courses_and_assessments(session, data_dir: Path):
    print("🔎 Auto-deriving courses & assessments from question CSVs...")
    courses_set = set()
    assessments_set = set()

    for csv_path in sorted(data_dir.glob("*.csv")):
        if csv_path.name.lower() in {"courses.csv", "assessments.csv", "template.csv"}:
            continue
        try:
            with open(csv_path, "rb") as f:
                rows = parse_csv(f.read())
            for q in rows:
                cc = (q.get("course_code") or q.get("Course Code") or "").strip()
                cn = (q.get("course_name") or q.get("Course Name") or cc).strip()
                at = (q.get("assessment_type") or q.get("Assessment Type") or "").strip()
                if cc:
                    courses_set.add((cc, cn or cc))
                if at:
                    assessments_set.add((cc, at))
        except Exception as e:
            print(f"  ⚠ Skipping {csv_path.name}: {e}")

    # Courses
    for code, name in sorted(courses_set):
        session.execute(
            text("""INSERT INTO courses(course_code, course_name)
                    VALUES (:code, :name)
                    ON CONFLICT (course_code) DO UPDATE SET course_name = EXCLUDED.course_name"""),
            {"code": code, "name": name or code}
        )
    session.commit()
    print(f"  ✅ Ensured {len(courses_set)} courses")

    # Assessments
    for code, atype in sorted(assessments_set):
        course_id = session.execute(
            text("SELECT course_id FROM courses WHERE course_code=:c LIMIT 1"),
            {"c": code}
        ).scalar()
        if course_id:
            session.execute(
                text("""INSERT INTO assessments(course_id, assessment_type)
                        VALUES (:cid, :atype)
                        ON CONFLICT (course_id, assessment_type, assessment_acadyear, assessment_semester)
                        DO NOTHING"""),
                {"cid": course_id, "atype": atype}
            )
    session.commit()
    print(f"  ✅ Ensured {len(assessments_set)} assessments\n")

def load_courses_csv(session, csv_path: Path):
    import csv
    print(f"📥 Loading courses from {csv_path.name}")
    with open(csv_path, "r") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            code = (r.get("course_code") or r.get("Course Code") or "").strip()
            name = (r.get("course_name") or r.get("Course Name") or code).strip()
            if not code:
                continue
            session.execute(
                text("""INSERT INTO courses(course_code, course_name)
                        VALUES (:code, :name)
                        ON CONFLICT (course_code) DO UPDATE SET course_name = EXCLUDED.course_name"""),
                {"code": code, "name": name}
            )
    session.commit()

def load_assessments_csv(session, csv_path: Path):
    import csv
    print(f"📥 Loading assessments from {csv_path.name}")
    with open(csv_path, "r") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            code = (r.get("course_code") or r.get("Course Code") or "").strip()
            at   = (r.get("assessment_type") or r.get("Assessment Type") or "").strip()
            if not code or not at:
                continue
            cid = session.execute(
                text("SELECT course_id FROM courses WHERE course_code=:c LIMIT 1"),
                {"c": code}
            ).scalar()
            if cid:
                session.execute(
                    text("""INSERT INTO assessments(course_id, assessment_type, assessment_acadyear, assessment_semester)
                            VALUES (:cid, :at, NULL, NULL)
                            ON CONFLICT (course_id, assessment_type, assessment_acadyear, assessment_semester)
                            DO NOTHING"""),
                    {"cid": cid, "at": at}
                )
    session.commit()

def load_contexts_from_csvs(session, data_dir: Path):
    print("📥 Loading contexts from *_contexts.csv")
    for csv_path in sorted(data_dir.glob("*_contexts.csv")):
        with open(csv_path, "rb") as f:
            rows = parse_csv(f.read())
        for r in rows:
            code = (r.get("Course Code") or r.get("course_code") or "").strip()
            at   = (r.get("Assessment Type") or r.get("assessment_type") or "").strip()
            clid = (r.get("Context ID") or r.get("context_local_id") or "").strip()
            ctxt = (r.get("Context Text") or r.get("context_text") or "").strip()
            if not code or not at or not clid:
                continue
            cid = session.execute(
                text("SELECT course_id FROM courses WHERE course_code=:c LIMIT 1"),
                {"c": code}
            ).scalar()
            aid = session.execute(
                text("""SELECT a.assessment_id
                        FROM assessments a
                        JOIN courses c ON c.course_id=a.course_id
                        WHERE c.course_code=:c AND a.assessment_type=:t
                        LIMIT 1"""),
                {"c": code, "t": at}
            ).scalar()
            if not cid or not aid:
                continue
            session.execute(
                text("""INSERT INTO contexts(assessment_id, course_id, context_local_id, context_text)
                        VALUES (:aid, :cid, :clid, :ctxt)
                        ON CONFLICT (assessment_id, context_local_id)
                        DO UPDATE SET context_text = EXCLUDED.context_text"""),
                {"aid": aid, "cid": cid, "clid": clid, "ctxt": ctxt}
            )
    session.commit()

def load_questions_from_csvs(session, data_dir: Path):
    print("📥 Loading questions from *_questions.csv")
    for csv_path in sorted(data_dir.glob("*_questions.csv")):
        with open(csv_path, "rb") as f:
            rows = parse_csv(f.read())
        for idx, q in enumerate(rows, 1):
            # normalize headers
            def G(*keys, default=""):
                for k in keys:
                    v = q.get(k)
                    if v is not None:
                        return v
                return default
            cc  = G("Course Code", "course_code").strip()
            at  = G("Assessment Type", "assessment_type").strip()
            cl  = G("Context ID", "context_local_id").strip()
            qtx = G("Question Text", "question_text").strip()
            if not cc or not at or not qtx:
                continue

            # validate (your helper)
            errs = validate_question_data(q) or []
            if errs:
                continue

            cid = session.execute(
                text("SELECT course_id FROM courses WHERE course_code=:c LIMIT 1"),
                {"c": cc}
            ).scalar()
            aid = session.execute(
                text("""SELECT a.assessment_id
                        FROM assessments a JOIN courses c ON c.course_id=a.course_id
                        WHERE c.course_code=:c AND a.assessment_type=:t
                        LIMIT 1"""),
                {"c": cc, "t": at}
            ).scalar()
            ctx_id = None
            if cl:
                ctx_id = session.execute(
                    text("""SELECT ctx.context_id
                            FROM contexts ctx
                            JOIN assessments a ON a.assessment_id=ctx.assessment_id
                            JOIN courses c ON c.course_id=ctx.course_id
                            WHERE c.course_code=:c AND a.assessment_type=:t AND ctx.context_local_id=:clid
                            LIMIT 1"""),
                    {"c": cc, "t": at, "clid": cl}
                ).scalar()

            session.execute(
                text("""
                    INSERT INTO questions (
                      assessment_id, course_id, context_id,
                      question_text, question_type,
                      option_a, option_b, option_c, option_d, option_e,
                      correct_answer, explanation, points, difficulty, concepts,
                      version_number, is_latest
                    )
                    VALUES (
                      :aid, :cid, :ctx,
                      :qtx, :qtype,
                      :a, :b, :c, :d, :e,
                      :ans, :exp, :pts, :diff, :concepts,
                      COALESCE(:vnum, 1), TRUE
                    )
                    ON CONFLICT (course_id, assessment_id, question_text)
                    DO UPDATE SET
                      question_type  = EXCLUDED.question_type,
                      option_a       = EXCLUDED.option_a,
                      option_b       = EXCLUDED.option_b,
                      option_c       = EXCLUDED.option_c,
                      option_d       = EXCLUDED.option_d,
                      option_e       = EXCLUDED.option_e,
                      correct_answer = EXCLUDED.correct_answer,
                      explanation    = EXCLUDED.explanation,
                      points         = EXCLUDED.points,
                      difficulty     = EXCLUDED.difficulty,
                      concepts       = EXCLUDED.concepts,
                      context_id     = EXCLUDED.context_id,
                      version_number = EXCLUDED.version_number,
                      is_latest      = TRUE
                """),
                {
                    "aid": aid, "cid": cid, "ctx": ctx_id,
                    "qtx": qtx,
                    "qtype": G("Question Type","question_type"),
                    "a": G("Option A","option_a"),
                    "b": G("Option B","option_b"),
                    "c": G("Option C","option_c"),
                    "d": G("Option D","option_d"),
                    "e": G("Option E","option_e"),
                    "ans": G("Correct Answer","correct_answer"),
                    "exp": G("Explanation","explanation"),
                    "pts": (G("Points","points") or None),
                    "diff": G("Difficulty","difficulty"),
                    "concepts": G("Concepts","concepts"),
                    "vnum": (G("Version Number","version_number") or None),
                }
            )
    session.commit()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n==============================")
    print("📦 Initializing QuizBank DB")
    print("==============================\n")

    # 0) Convert XLSX→CSV if converter available
    try_convert_xlsx_to_csv()

    # 1) Wait DB
    if not wait_for_db():
        sys.exit(1)

    # 2) Apply schema (01) once (safe to re-run thanks to IF NOT EXISTS)
    schema_sql = DB_INIT_DIR / "01_schema.sql"
    if schema_sql.exists():
        run_sql_file(schema_sql)
    else:
        print(f"⚠️ {schema_sql} not found; assuming schema already present.\n")

    session = SessionLocal()
    try:
        # 3) Idempotency guard
        if already_seeded(session):
            print("ℹ️ Database already initialized by Python seeder — skipping.\n")
            return

        # 4) Seed courses & assessments (CSV if present, else auto from question files)
        courses_csv = DATA_DIR / "courses.csv"
        assessments_csv = DATA_DIR / "assessments.csv"
        if courses_csv.exists():
            load_courses_csv(session, courses_csv)
        if assessments_csv.exists():
            load_assessments_csv(session, assessments_csv)

        # Fallback auto-derive when CSVs are missing or incomplete
        c_count = session.execute(text("SELECT COUNT(*) FROM courses")).scalar() or 0
        a_count = session.execute(text("SELECT COUNT(*) FROM assessments")).scalar() or 0
        if c_count == 0 or a_count == 0:
            auto_create_courses_and_assessments(session, DATA_DIR)

        # 5) Seed contexts and questions from *_contexts.csv / *_questions.csv
        load_contexts_from_csvs(session, DATA_DIR)
        load_questions_from_csvs(session, DATA_DIR)

        # 6) Mark seeded (sentinel)
        mark_seeded(session)
        print("✅ Seeding complete (sentinel written).")

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
