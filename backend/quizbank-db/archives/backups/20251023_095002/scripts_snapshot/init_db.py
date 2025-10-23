"""
init_db.py  — Idempotent database initialization for QuizBank

- Applies 01_schema.sql
- Best-effort XLSX→CSV (non-fatal; set QB_SKIP_XLSX=1 to skip)
- Seeds courses, assessments, contexts, questions from CSV
- Runs ONCE only (uses system_meta.sentinel)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

from sqlalchemy import text

# ── Path shims so "import app..." works no matter where this script is run ─────
SCRIPT_DIR = Path(__file__).resolve().parent                   # .../backend/quizbank-db/scripts
BACKEND_DIR = SCRIPT_DIR.parent.parent                         # .../backend
REPO_ROOT = BACKEND_DIR.parent                                 # repo root

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Your existing infra
from app.db.connection import engine, SessionLocal
from app.utils.file_parser import parse_csv
try:
    from app.utils.validation import validate_question_data  # optional
except Exception:
    def validate_question_data(_row):  # fallback no-op
        return []

# ── Locations ─────────────────────────────────────────────────────────────────
DATA_DIRS = [
    BACKEND_DIR / "data",                                   # original source
    BACKEND_DIR / "quizbank-db" / "db-init" / "data",       # converter output
]
DB_INIT_DIR = BACKEND_DIR / "quizbank-db" / "db-init"

# ── Helpers ───────────────────────────────────────────────────────────────────
def wait_for_db(timeout: int = 30) -> bool:
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


def apply_sql_file(session, sql_path: Path) -> None:
    if not sql_path.exists():
        print(f"ℹ️  {sql_path.name} not found — skipping.")
        return
    print(f"🧱 Applying SQL: {sql_path.name}")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    session.execute(text(sql))
    session.commit()
    print(f"✅ Applied: {sql_path.name}\n")


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
        text("SELECT 1 FROM system_meta WHERE key = 'seeded_by_python' LIMIT 1")
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
    """
    Best effort XLSX→CSV. If pandas/NumPy stack is broken, we continue.
    Set QB_SKIP_XLSX=1 to skip conversion entirely (useful on CI or broken local envs).
    """
    if os.environ.get("QB_SKIP_XLSX") == "1":
        print("ℹ️  Skipping XLSX→CSV because QB_SKIP_XLSX=1\n")
        return

    try:
        try:
            # when run via `python -m`
            from .xlsx_to_csv import convert_xlsx_to_csv  # type: ignore
        except Exception:
            # when run via file path
            sys.path.insert(0, str(SCRIPT_DIR))
            from xlsx_to_csv import convert_xlsx_to_csv  # type: ignore

        print("🧾 Converting XLSX → CSV...")
        convert_xlsx_to_csv()
        print("✅ XLSX conversion complete.\n")
    except Exception as e:
        # DO NOT raise — continue with any CSVs we already have
        print("⚠️ XLSX→CSV conversion failed; proceeding with existing CSVs.")
        print(f"   Reason: {e}\n")


def find_first_caseinsensitive(*names: str) -> Optional[Path]:
    """
    Look for any of `names` (case-insensitive-ish) across all DATA_DIRS.
    Returns a Path or None.
    """
    candidates = set()
    for n in names:
        candidates.add(n)
        if n:
            candidates.add(n[0].upper() + n[1:])

    for root in DATA_DIRS:
        for n in candidates:
            p = root / n
            if p.exists():
                return p
    return None


# ── Seed helpers ──────────────────────────────────────────────────────────────
def load_courses_csv(session, csv_path: Path):
    import csv
    print(f"📥 Loading courses from {csv_path.name}")
    cnt = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            code = (r.get("course_code") or r.get("Course Code") or "").strip()
            name = (r.get("course_name") or r.get("Course Name") or code).strip()
            if not code:
                continue
            session.execute(
                text("""INSERT INTO courses(course_code, course_name)
                        VALUES (:code, :name)
                        ON CONFLICT (course_code)
                        DO UPDATE SET course_name = EXCLUDED.course_name"""),
                {"code": code, "name": name}
            )
            cnt += 1
    session.commit()
    print(f"  ✅ Upserted {cnt} course rows")


def load_assessments_csv(session, csv_path: Path):
    import csv
    print(f"📥 Loading assessments from {csv_path.name}")
    cnt = 0
    with open(csv_path, "r", encoding="utf-8") as f:
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
                cnt += 1
    session.commit()
    print(f"  ✅ Upserted {cnt} assessment rows")

import re
from sqlalchemy import text

def _norm_keys(row: dict) -> dict:
    def n(k: str) -> str:
        return (
            k.replace("\ufeff","").strip().lower()
             .replace(" ", "_").replace("-", "_")
        )
    return {n(k): v for k, v in row.items()}

_filename_pat_full   = re.compile(
    r'^(?P<code>[A-Za-z]+\d+)_(?P<sem>Sem\d+)_?(?P<year>\d{4,})?_(?P<title>[^_]+)_(?P<kind>context|questions)\.csv$',
    re.IGNORECASE
)
_filename_pat_simple = re.compile(
    r'^(?P<code>[A-Za-z]+\d+)_(?P<title>[^_]+)_(?P<kind>context|questions)\.csv$',
    re.IGNORECASE
)

def _parse_filename_meta(name: str) -> dict:
    m = _filename_pat_full.match(name) or _filename_pat_simple.match(name)
    if not m:
        return {}
    d = m.groupdict()
    # assessment_type from title (normalize some common ones)
    title = d.get("title","")
    atype = title
    # e.g. Quiz3, Midterm, Final, Questions
    if re.match(r'(?i)^quiz\d+$', title):
        atype = title.title()         # Quiz3
    elif title.lower() in {"midterm","final","questions"}:
        atype = title.title()
    d["assessment_type"] = atype
    return d

def auto_create_courses_and_assessments(session):
    """
    Derive courses & assessments from *_questions.csv (and any other CSVs) across DATA_DIRS.
    Uses both row headers and filename tokens so your two naming schemes work.
    """
    print("🔎 Auto-deriving courses & assessments from CSVs...")
    courses_set = set()       # {(course_code, course_name)}
    assessments_set = set()   # {(course_code, assessment_type, acadyear, semester)}

    for root in DATA_DIRS:
        for csv_path in sorted(root.glob("*.csv")):
            name_low = csv_path.name.lower()
            # ignore known “list” files; we want question-derived info
            if name_low in {"courses.csv", "assessments.csv", "template.csv"}:
                continue

            # pull hints from filename
            meta = _parse_filename_meta(csv_path.name)
            file_code = (meta.get("code") or "").strip()
            file_at   = (meta.get("assessment_type") or "").strip()
            file_year = (meta.get("year") or "") or None
            file_sem  = (meta.get("sem") or "") or None
            if file_sem:
                m = re.search(r'(\d+)', file_sem)
                file_sem = m.group(1) if m else file_sem  # “Sem1” → “1”

            try:
                with open(csv_path, "rb") as f:
                    rows = parse_csv(f.read())
                rows = [_norm_keys(r) for r in rows]
            except Exception as e:
                print(f"  ⚠ Skipping {csv_path.name}: {e}")
                continue

            for r in rows:
                # prefer row values; else fall back to filename tokens
                cc = (r.get("course_code") or file_code or "").strip()
                cn = (r.get("course_name") or cc).strip()
                at = (r.get("assessment_type") or file_at or "").strip()
                ay = (r.get("assessment_acadyear") or file_year or None)
                se = (r.get("assessment_semester") or file_sem or None)

                if cc:
                    courses_set.add((cc, cn or cc))
                if cc and at:
                    assessments_set.add((cc, at, ay, se))

    # upsert courses
    for code, name in sorted(courses_set):
        session.execute(
            text("""INSERT INTO courses(course_code, course_name)
                    VALUES (:code, :name)
                    ON CONFLICT (course_code)
                    DO UPDATE SET course_name = EXCLUDED.course_name"""),
            {"code": code, "name": name}
        )
    session.commit()

    # upsert assessments (needs course_id)
    for code, atype, ay, se in sorted(assessments_set):
        cid = session.execute(
            text("SELECT course_id FROM courses WHERE course_code=:c LIMIT 1"),
            {"c": code}
        ).scalar()
        if cid:
            session.execute(
                text("""INSERT INTO assessments(course_id, assessment_type, assessment_acadyear, assessment_semester)
                        VALUES (:cid, :atype, :ay, :se)
                        ON CONFLICT (course_id, assessment_type, assessment_acadyear, assessment_semester)
                        DO NOTHING"""),
                {"cid": cid, "atype": atype, "ay": ay, "se": se}
            )
    session.commit()

    # ✅ put your debug prints HERE (inside the function, after sets exist)
    print(f"  [DEBUG] derived courses_set sample (≤5): {list(sorted(courses_set))[:5]}")
    print(f"  [DEBUG] derived assessments_set sample (≤5): {list(sorted(assessments_set))[:5]}")
    print(f"  ✅ Ensured {len(courses_set)} courses; {len(assessments_set)} assessments\n")


def load_contexts_from_csvs(session):
    """
    Load contexts from both singular and plural patterns, across both data roots.
    Accepts headers:
      - Course Code / course_code
      - Assessment Type / assessment_type
      - Context ID / context_local_id
      - Context Text / context_text
    """
    print("📥 Loading contexts from *_context(s).csv")
    patterns = ["*_contexts.csv", "*_context.csv"]
    processed = 0
    upserted = 0

    for root in DATA_DIRS:
        for pat in patterns:
            for csv_path in sorted(root.glob(pat)):
                with open(csv_path, "rb") as f:
                    rows = parse_csv(f.read())

                for r in rows:
                    code = (r.get("Course Code") or r.get("course_code") or "").strip()
                    at   = (r.get("Assessment Type") or r.get("assessment_type") or "").strip()
                    clid = (r.get("Context ID") or r.get("context_local_id") or "").strip()
                    ctxt = (r.get("Context Text") or r.get("context_text") or "").strip()
                    processed += 1
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

                    res = session.execute(
                        text("""INSERT INTO contexts(assessment_id, course_id, context_local_id, context_text)
                                VALUES (:aid, :cid, :clid, :ctxt)
                                ON CONFLICT (assessment_id, context_local_id)
                                DO UPDATE SET context_text = EXCLUDED.context_text
                                RETURNING context_id"""),
                        {"aid": aid, "cid": cid, "clid": clid, "ctxt": ctxt}
                    )
                    if res.scalar():
                        upserted += 1

    session.commit()
    print(f"  ✅ Context rows seen: {processed}, upserted: {upserted}")


def load_questions_from_csvs(session):
    """
    Load questions from *_questions.csv across both data roots.
    Accepts common headers with case variations.
    """
    print("📥 Loading questions from *_questions.csv")
    processed = 0
    upserted = 0

    def G(row, *keys, default=""):
        for k in keys:
            v = row.get(k)
            if v is not None:
                return v
        return default

    for root in DATA_DIRS:
        for csv_path in sorted(root.glob("*_questions.csv")):
            with open(csv_path, "rb") as f:
                rows = parse_csv(f.read())

            for q in rows:
                processed += 1
                cc  = G(q, "Course Code", "course_code").strip()
                at  = G(q, "Assessment Type", "assessment_type").strip()
                cl  = G(q, "Context ID", "context_local_id").strip()
                qtx = G(q, "Question Text", "question_text").strip()
                if not cc or not at or not qtx:
                    continue

                errs = (validate_question_data(q) or [])
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

                res = session.execute(
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
                        RETURNING question_id
                    """),
                    {
                        "aid": aid, "cid": cid, "ctx": ctx_id,
                        "qtx": qtx,
                        "qtype": G(q, "Question Type","question_type"),
                        "a": G(q, "Option A","option_a"),
                        "b": G(q, "Option B","option_b"),
                        "c": G(q, "Option C","option_c"),
                        "d": G(q, "Option D","option_d"),
                        "e": G(q, "Option E","option_e"),
                        "ans": G(q, "Correct Answer","correct_answer"),
                        "exp": G(q, "Explanation","explanation"),
                        "pts": (G(q, "Points","points") or None),
                        "diff": G(q, "Difficulty","difficulty"),
                        "concepts": G(q, "Concepts","concepts"),
                        "vnum": (G(q, "Version Number","version_number") or None),
                    }
                )
                if res.scalar():
                    upserted += 1

    session.commit()
    print(f"  ✅ Question rows seen: {processed}, upserted: {upserted}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n==============================")
    print("📦 Initializing QuizBank DB")
    print("==============================\n")

    # 0) Best-effort XLSX→CSV (non-fatal)
    try_convert_xlsx_to_csv()

    # 1) Wait DB
    if not wait_for_db():
        sys.exit(1)

    session = SessionLocal()
    try:
        # 2) Apply base schema (idempotent)
        apply_sql_file(session, DB_INIT_DIR / "01_schema.sql")

        # 3) Idempotency guard
        if already_seeded(session):
            print("ℹ️ Database already initialized by Python seeder — skipping.\n")
            return

        # Baseline counts (sentinel gating)
        c_before   = session.execute(text("SELECT COUNT(*) FROM courses")).scalar()     or 0
        a_before   = session.execute(text("SELECT COUNT(*) FROM assessments")).scalar() or 0
        ctx_before = session.execute(text("SELECT COUNT(*) FROM contexts")).scalar()    or 0
        q_before   = session.execute(text("SELECT COUNT(*) FROM questions")).scalar()   or 0

        # 4) Explicit CSVs if present (in either root)
        courses_csv     = find_first_caseinsensitive("courses.csv")
        assessments_csv = find_first_caseinsensitive("assessments.csv")

        if courses_csv:
            load_courses_csv(session, courses_csv)
        if assessments_csv:
            load_assessments_csv(session, assessments_csv)

        # 5) Fallback auto-derive if still empty
        c_count = session.execute(text("SELECT COUNT(*) FROM courses")).scalar() or 0
        a_count = session.execute(text("SELECT COUNT(*) FROM assessments")).scalar() or 0
        if c_count == 0 or a_count == 0:
            auto_create_courses_and_assessments(session)

        # 6) Contexts + Questions
        load_contexts_from_csvs(session)
        load_questions_from_csvs(session)

        # 7) Only write sentinel if rows landed
        c_after   = session.execute(text("SELECT COUNT(*) FROM courses")).scalar()     or 0
        a_after   = session.execute(text("SELECT COUNT(*) FROM assessments")).scalar() or 0
        ctx_after = session.execute(text("SELECT COUNT(*) FROM contexts")).scalar()    or 0
        q_after   = session.execute(text("SELECT COUNT(*) FROM questions")).scalar()   or 0

        inserted_any = (c_after > c_before) or (a_after > a_before) or (ctx_after > ctx_before) or (q_after > q_before)
        if inserted_any:
            mark_seeded(session)
            print("✅ Seeding complete (sentinel written).")
        else:
            print("⚠️ No rows loaded — sentinel not written so we can try again next run.")

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
