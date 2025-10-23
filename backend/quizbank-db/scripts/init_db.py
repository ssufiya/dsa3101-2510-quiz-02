"""
Idempotent DB initialization for QuizBank

What this script does (in order):
  1) (Optional) Convert backend/data/*.xlsx -> backend/quizbank-db/db-init/data/*.csv
  2) Ensure DB is reachable
  3) Ensure schema (apply 01_schema.sql once; guard self-FKs; dedupe; add coalesced unique index for assessments)
  4) If seeding is allowed (no sentinel OR SEED_FORCE=1):
        4a) Seed COURSES from canonical CSV: db-init/data/updated_nus_dsa_courses.csv
        4b) Infer & upsert ASSESSMENTS by scanning *_context*.csv and *_questions.csv file names
        4c) Load CONTEXTS (+ context_attachments) from *_context*.csv
        4d) Load QUESTIONS (+ question_attachments) from *_questions.csv
        4e) Write sentinel in system_meta so subsequent runs skip seeding
  5) Print final row counts

Supported filename patterns (case-insensitive):
  - Course_SemX_YYYY_Title_{context|questions}.csv
      e.g. DSA1101_Sem1_2425_Quiz3_context.csv
  - Course_Title_{context|questions}.csv
      e.g. ST2131_Questions_context.csv

Expected CSV headers (case-insensitive):
  Contexts:  Context ID | Context Text | Attachment
  Questions: Context ID | Question Number | Sub-Question Number | Question Text | Question Type
             Option A | Option B | Option C | Option D | Option E
             Correct Answer | Explanation | Points | Difficulty | Concepts | Attachment

Environment flags:
  - SEED_FORCE=1     -> run full seeding even if sentinel exists
  - SEED_SKIP_XLSX=1 -> skip XLSX->CSV conversion step
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable, Optional, Tuple

from sqlalchemy import text

# ── Path bootstrapping so `import app...` works from repo root or subfolders ──
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent  # .../backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Project modules
from app.db.connection import engine, SessionLocal
from app.utils.file_parser import parse_csv  # robust CSV bytes -> list[dict]

# ── Constants & Paths ─────────────────────────────────────────────────────────
DB_INIT_DIR = SCRIPT_DIR.parent / "db-init"               # .../quizbank-db/db-init
DATA_DIR = DB_INIT_DIR / "data"                           # CSVs land here
COURSES_MASTER = DATA_DIR / "updated_nus_dsa_courses.csv" # canonical course list

# Max lengths per schema (guards to avoid DataErrors)
MAX_CORRECT_ANSWER = 64
MAX_EXPLANATION    = 4096
MAX_QTYPE          = 64
MAX_DIFFICULTY     = 32
MAX_CONCEPTS       = 1024

# ── Env helpers ───────────────────────────────────────────────────────────────
import csv, io

def read_csv_rows(path: Path) -> list[dict]:
    """Robust CSV reader for seeding: UTF-8-SIG decode + csv.DictReader."""
    b = path.read_bytes()
    try:
        s = b.decode("utf-8-sig")          # strip BOM if present
    except UnicodeDecodeError:
        s = b.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(s)))

def _env_flag(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y"}

def is_seed_forced() -> bool:
    return _env_flag("SEED_FORCE", False)

def skip_xlsx() -> bool:
    return _env_flag("SEED_SKIP_XLSX", False)

# ── DB helpers ────────────────────────────────────────────────────────────────
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

def apply_sql_file(session, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    session.execute(text(sql))
    session.commit()

def table_exists(session, name: str) -> bool:
    return session.execute(
        text("SELECT to_regclass(:r)"), {"r": f"public.{name}"}
    ).scalar() is not None

def constraint_exists(session, table: str, conname: str) -> bool:
    return session.execute(text("""
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = :t AND c.conname = :c
        LIMIT 1
    """), {"t": table, "c": conname}).scalar() is not None

def dedupe_assessments(session) -> int:
    """
    Remove duplicate assessment rows that collide on
    (course_id, assessment_type, COALESCE(ay,''), COALESCE(sem,'')),
    keeping the lowest assessment_id. Returns number of rows deleted.
    """
    deleted = session.execute(text("""
        WITH dups AS (
          SELECT
            course_id,
            assessment_type,
            COALESCE(assessment_acadyear, '') AS ay,
            COALESCE(assessment_semester, '') AS sem,
            MIN(assessment_id) AS keep_id,
            COUNT(*) AS cnt
          FROM assessments
          GROUP BY course_id, assessment_type,
                   COALESCE(assessment_acadyear, ''), COALESCE(assessment_semester, '')
          HAVING COUNT(*) > 1
        ),
        to_delete AS (
          SELECT a.assessment_id
          FROM assessments a
          JOIN dups d
            ON a.course_id = d.course_id
           AND a.assessment_type = d.assessment_type
           AND COALESCE(a.assessment_acadyear, '') = d.ay
           AND COALESCE(a.assessment_semester, '') = d.sem
          WHERE a.assessment_id <> d.keep_id
        )
        DELETE FROM assessments a
        USING to_delete td
        WHERE a.assessment_id = td.assessment_id
        RETURNING a.assessment_id
    """)).fetchall()
    session.commit()
    return len(deleted)

def ensure_assessment_unique_index(session) -> None:
    """Force uniqueness of (course, type, AY, SEM) even when AY/SEM are NULL."""
    session.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_assessment_coalesced
        ON assessments (
          course_id,
          assessment_type,
          COALESCE(assessment_acadyear, ''),
          COALESCE(assessment_semester, '')
        )
    """))
    session.commit()

def ensure_schema(session) -> None:
    """Apply 01_schema.sql if core tables missing; guard constraints; dedupe; add coalesced unique index."""
    need_schema = not table_exists(session, "courses") or not table_exists(session, "questions")
    if need_schema:
        print("🧱 Applying SQL: 01_schema.sql")
        apply_sql_file(session, DB_INIT_DIR / "01_schema.sql")
        print("✅ Applied: 01_schema.sql")

    # Guard self-referential constraints (if 01 was partially applied earlier)
    if not constraint_exists(session, "questions", "fk_questions_previous"):
        session.execute(text("""
            ALTER TABLE questions
              ADD CONSTRAINT fk_questions_previous
              FOREIGN KEY (previous_version_id)
              REFERENCES questions(question_id)
              ON DELETE SET NULL
              DEFERRABLE INITIALLY DEFERRED
        """))
    if not constraint_exists(session, "questions", "fk_questions_original"):
        session.execute(text("""
            ALTER TABLE questions
              ADD CONSTRAINT fk_questions_original
              FOREIGN KEY (original_id)
              REFERENCES questions(question_id)
              ON DELETE SET NULL
              DEFERRABLE INITIALLY DEFERRED
        """))
    if not constraint_exists(session, "questions", "chk_prev_not_self"):
        session.execute(text("""
            ALTER TABLE questions
              ADD CONSTRAINT chk_prev_not_self
              CHECK (previous_version_id IS NULL OR previous_version_id <> question_id)
        """))
    if not constraint_exists(session, "questions", "chk_orig_not_self"):
        session.execute(text("""
            ALTER TABLE questions
              ADD CONSTRAINT chk_orig_not_self
              CHECK (original_id IS NULL OR original_id <> question_id)
        """))
    session.commit()

    removed = dedupe_assessments(session)
    if removed:
        print(f"🧹 Removed {removed} duplicate assessment rows before indexing.")

    ensure_assessment_unique_index(session)

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
        text("SELECT value FROM system_meta WHERE key='seeded_by_python' LIMIT 1")
    ).fetchone()
    return row is not None

def mark_seeded(session) -> None:
    session.execute(text("""
        INSERT INTO system_meta(key, value)
        VALUES ('seeded_by_python', NOW()::text)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """))
    session.commit()

def safe_count(session, table_name: str) -> int:
    try:
        return int(session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0)
    except Exception:
        return 0

# ── Optional XLSX → CSV converter ─────────────────────────────────────────────
def try_convert_xlsx_to_csv() -> None:
    """
    Optional: converts XLSX from backend/data -> CSVs into db-init/data.
    Will proceed even if pandas/numexpr/numpy are not available.
    """
    if skip_xlsx():
        print("⏭  Skipping XLSX→CSV (SEED_SKIP_XLSX=1).")
        return
    try:
        try:
            # when invoked as module
            from .xlsx_to_csv import convert_xlsx_to_csv  # type: ignore
        except Exception:
            # when invoked by path
            sys.path.insert(0, str(SCRIPT_DIR))
            from xlsx_to_csv import convert_xlsx_to_csv  # type: ignore
        print("🧾 Converting XLSX → CSV...")
        convert_xlsx_to_csv()
        print("✅ XLSX conversion complete.\n")
    except Exception as e:
        print(f"ℹ️ XLSX→CSV converter not available or failed: {e}\n")

# ── Filenames → metadata parsing ──────────────────────────────────────────────
FNAME_RE = re.compile(
    r"""
    ^
    (?P<course>[A-Za-z]{2,}\d{4})         # DSA1101 / ST2131 / IND5003
    (?:_Sem(?P<sem>\d))?                  # optional _Sem1
    (?:_(?P<acad>\d{4}))?                 # optional _2425
    _(?P<title>.+)                        # title can contain underscores
    _(?P<kind>context|contexts|questions) # file kind
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

def parse_meta_from_filename(pathlike) -> Optional[Tuple[str, str, str, Optional[str], Optional[str]]]:
    """
    Return (course_code, assessment_type, kind, acadyear, semester).
      - course_code: 'DSA1101'
      - assessment_type: 'Quiz3' | 'Midterm' | 'Final' | 'Questions' | 'Regression' | ...
      - kind: 'contexts' or 'questions'
      - acadyear: '2425' if present else None
      - semester: '1'|'2' if present else None
    """
    name = pathlike.name if hasattr(pathlike, "name") else str(pathlike)
    stem = name[:-4] if name.lower().endswith(".csv") else name

    m = FNAME_RE.match(stem)
    if not m:
        return None

    course = m.group("course").upper().strip()
    title  = m.group("title").strip()
    kind   = m.group("kind").lower()
    ay     = m.group("acad") or None
    sem    = m.group("sem") or None

    norm_kind = "contexts" if "context" in kind else "questions"
    return (course, title, norm_kind, ay, sem)

# ── CSV helpers ───────────────────────────────────────────────────────────────
import re, unicodedata

_WS = re.compile(r"\s+", flags=re.UNICODE)

def _clean_header(s: str) -> str:
    # Unicode normalize
    s = unicodedata.normalize("NFKC", s)
    # Remove common invisible troublemakers
    s = s.replace("\ufeff", "").replace("\u200b", "")
    # Lowercase
    s = s.lower()
    # Replace any unicode whitespace with underscores
    s = _WS.sub("_", s.strip())
    # Replace dashes with underscores
    s = s.replace("-", "_")
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    return s

def normalise_keys(row: dict) -> dict:
    """Lower/underscore keys using unicode-aware normalization; keep originals too."""
    out = {}
    for k, v in row.items():
        if k is None:
            continue
        nk = _clean_header(str(k))
        out[nk] = v
        out[k] = v  # keep original for safety
    return out

def G(row: dict, *candidates, default: str = "") -> str:
    n = normalise_keys(row)
    for key in candidates:
        if key in n and n[key] not in (None, ""):
            return str(n[key])
        ck = _clean_header(str(key))
        if ck in n and n[ck] not in (None, ""):
            return str(n[ck])
    return default

# ── Seed courses from canonical CSV ───────────────────────────────────────────
def load_courses_from_master_csv(session, master_csv: Path) -> int:
    """
    Upsert courses from a canonical CSV so course list is authoritative.
    CSV headers expected (case-insensitive): course_code, course_name
    """
    if not master_csv.exists():
        print(f"ℹ️ Courses master CSV not found: {master_csv} (skipping)")
        return 0

    print(f"📚 Seeding courses from: {master_csv}")
    rows = parse_csv(master_csv.read_bytes())
    upserts = 0

    for r in rows:
        code = (G(r, "course_code", "Course Code", "Course_Code") or "").upper().strip()
        name = (G(r, "course_name", "Course Name", "Course_Name") or "").strip() or code
        if not code:
            continue

        session.execute(text("""
            INSERT INTO courses(course_code, course_name)
            VALUES (:code, :name)
            ON CONFLICT (course_code)
            DO UPDATE SET course_name = EXCLUDED.course_name
        """), {"code": code, "name": name})
        upserts += 1

    session.commit()
    print(f"✅ Courses upserted from master: {upserts}")
    return upserts

# ── Build assessments by scanning file names ──────────────────────────────────
def create_assessments_from_filenames(session, data_dir: Path) -> None:
    """
    Scan *_context*.csv and *_questions*.csv, infer (course_code, assessment_type, [acadyear], [semester]),
    ensure the course exists, and insert assessments idempotently.
    """
    files = []
    files.extend(sorted(Path(data_dir).glob("*_context*.csv")))
    files.extend(sorted(Path(data_dir).glob("*_questions*.csv")))

    seen = set()  # avoid double-inserting same (course_id, type, ay, sem) during one run
    created = 0

    for p in files:
        meta = parse_meta_from_filename(p.name)
        if not meta:
            # e.g. Template_Questions_*.csv
            continue

        course_code, assessment_type, _kind, ay, sem = meta

        # look up course_id
        course_id = session.execute(
            text("SELECT course_id FROM courses WHERE course_code = :code LIMIT 1"),
            {"code": course_code},
        ).scalar()
        if not course_id:
            # course not seeded yet
            continue

        sig = (course_id, assessment_type or "", ay or "", sem or "")
        if sig in seen:
            continue
        seen.add(sig)

        session.execute(
            text("""
                INSERT INTO assessments (
                course_id, assessment_type, assessment_acadyear, assessment_semester
                )
                SELECT :course_id, :atype, :ay, :sem
                WHERE NOT EXISTS (
                SELECT 1
                FROM assessments a
                WHERE a.course_id = :course_id
                    AND a.assessment_type = :atype
                    AND COALESCE(a.assessment_acadyear, '') = COALESCE(:ay,  '')
                    AND COALESCE(a.assessment_semester, '') = COALESCE(:sem, '')
                )
            """),
            {"course_id": course_id, "atype": assessment_type, "ay": ay, "sem": sem},
        )

        created += 1

    session.commit()
    print(f"🧱 Assessments inferred & upserted (this run): {created}")

# ── Loaders: contexts & questions (with attachment debug) ─────────────────────
def _normalize_dirs(data_dirs: Iterable[Path] | Path | str):
    if isinstance(data_dirs, (str, Path)):
        return [Path(data_dirs)]
    try:
        return [Path(p) for p in data_dirs]
    except TypeError:
        return [Path(data_dirs)]

def ensure_assessment_id(session, course_code: str, assessment_type: str,
                         ay: Optional[str] = None, sem: Optional[str] = None):
    """Return (course_id, assessment_id) for (course_code, assessment_type, AY, SEM)."""
    course_id = session.execute(
        text("SELECT course_id FROM courses WHERE course_code = :c LIMIT 1"),
        {"c": course_code},
    ).scalar()

    if not course_id:
        return (None, None)

    assessment_id = session.execute(
        text("""
            SELECT a.assessment_id
            FROM assessments a
            WHERE a.course_id = :cid
              AND a.assessment_type = :at
              AND COALESCE(a.assessment_acadyear, '') = COALESCE(:ay, '')
              AND COALESCE(a.assessment_semester, '') = COALESCE(:sem, '')
            ORDER BY a.assessment_id
            LIMIT 1
        """),
        {"cid": course_id, "at": assessment_type, "ay": ay, "sem": sem},
    ).scalar()

    return (course_id, assessment_id)

def load_contexts_from_csvs(session, data_dirs) -> tuple[int, int]:
    """
    Upsert contexts from *_context(s).csv with headers:
      - Context ID | Context Text | Attachment (optional)
    Uses course/assessment inferred from filename.
    """
    data_dirs = _normalize_dirs(data_dirs)

    total_upserts = total_atts = 0
    files = []
    for base in data_dirs:
        files.extend(sorted(Path(base).glob("*_context*.csv")))
    print(f"📥 Loading contexts from {len(files)} files")

    for csv_path in files:
        meta = parse_meta_from_filename(csv_path.name)
        if not meta:
            print(f"  ⚠️  Skip (name unmatched): {csv_path.name}")
            continue
        course_code, assessment_type, _kind, ay, sem = meta
        course_id, assessment_id = ensure_assessment_id(session, course_code, assessment_type, ay, sem)

        if not (course_id and assessment_id):
            print(f"  ⚠️  No assessment for {course_code}/{assessment_type}; file={csv_path.name}")
            continue

        rows = read_csv_rows(csv_path)

        hdrs = list(rows[0].keys()) if rows else []
        print(f"  [DEBUG] headers={hdrs}")
        if rows:
            print("  [DEBUG] first context row (raw):",
                {k: rows[0].get(k) for k in ("Context ID","Context Text","Attachment")})


        saw_ctx_atts = wrote_ctx_atts = 0
        file_upserts = 0

        # quick visibility
        non_empty_context_text = sum(1 for r in rows if (G(r, "Context Text", "context_text") or "").strip())
        print(f"  [DEBUG] {csv_path.name}: rows={len(rows)}, non_empty_context_text={non_empty_context_text}")

        for r in rows:
            context_local_id = (G(r, "Context ID", "context_id", "contextid") or "").strip()
            context_text     = (G(r, "Context Text", "context_text") or "").strip()
            attachment_name  = (G(r, "Attachment", "attachment") or "").strip()

            if attachment_name:
                saw_ctx_atts += 1
            if not context_local_id or not context_text:
                continue

            # upsert context
            res = session.execute(
                text("""
                  INSERT INTO contexts (assessment_id, course_id, context_local_id, context_text)
                  VALUES (:aid, :cid, :clid, :ctxt)
                  ON CONFLICT (assessment_id, context_local_id)
                  DO UPDATE SET context_text = EXCLUDED.context_text
                  RETURNING context_id
                """),
                {"aid": assessment_id, "cid": course_id,
                 "clid": context_local_id, "ctxt": context_text}
            )
            ctx_id = res.scalar()
            file_upserts += 1

            if ctx_id and attachment_name:
                session.execute(
                    text("""
                      INSERT INTO context_attachments (context_id, attachment_name, attachment_url)
                      VALUES (:ctx, :name, NULL)
                      ON CONFLICT (context_id, attachment_name) DO NOTHING
                    """),
                    {"ctx": ctx_id, "name": attachment_name}
                )
                wrote_ctx_atts += 1

        session.commit()

        # sample attachments
        sample = []
        if saw_ctx_atts:
            for r in rows:
                v = (G(r, "Attachment", "attachment") or "").strip()
                if v:
                    sample.append(v)
                if len(sample) >= 5:
                    break

        total_upserts += file_upserts
        total_atts += wrote_ctx_atts
        print(f"  ✅ {csv_path.name}: contexts+= {file_upserts} (cum={total_upserts}), "
              f"ctx_atts saw={saw_ctx_atts}, wrote={wrote_ctx_atts}, sample={sample}")

    print(f"✅ Contexts upserted: {total_upserts}, context attachments: {total_atts}")
    return total_upserts, total_atts

def _truncate(s: Optional[str], maxlen: int) -> Optional[str]:
    if s is None:
        return None
    s = str(s)
    if len(s) <= maxlen:
        return s
    return s[: maxlen - 3] + "..."

def load_questions_from_csvs(session, data_dirs) -> tuple[int, int]:
    """
    Upsert questions from *_questions.csv with headers:
      Context ID | Question Number | Sub-Question Number | Question Text | Question Type
      Option A..E | Correct Answer | Explanation | Points | Difficulty | Concepts | Attachment
    Context ID is optional; we’ll link to a context if found.
    """
    data_dirs = _normalize_dirs(data_dirs)

    total_upserts = total_qatts = 0
    files = []
    for base in data_dirs:
        files.extend(sorted(Path(base).glob("*_questions.csv")))
    print(f"📥 Loading questions from {len(files)} files")

    for csv_path in files:
        meta = parse_meta_from_filename(csv_path.name)
        if not meta:
            print(f"  ⚠️  Skip (name unmatched): {csv_path.name}")
            continue
        course_code, assessment_type, _kind, ay, sem = meta
        course_id, assessment_id = ensure_assessment_id(session, course_code, assessment_type, ay, sem)

        if not (course_id and assessment_id):
            print(f"  ⚠️  No assessment for {course_code}/{assessment_type}; file={csv_path.name}")
            continue

        rows = read_csv_rows(csv_path)

        hdrs = list(rows[0].keys()) if rows else []
        print(f"  [DEBUG] headers={hdrs}")
        for i, r in enumerate(rows[:2]):
            raw_qt = r.get("Question Text")
            g_qt   = (G(r, "Question Text", "question_text") or "").strip()
            print(f"  [DEBUG] row{i+1} raw_qt_len={0 if raw_qt is None else len(raw_qt)} "
                f"g_qt_len={len(g_qt)} match={raw_qt and raw_qt.strip()==g_qt}")


        # quick visibility
        non_empty_question_text = sum(1 for r in rows if (G(r, "Question Text", "question_text") or "").strip())
        print(f"  [DEBUG] {csv_path.name}: rows={len(rows)}, non_empty_question_text={non_empty_question_text}")

        saw_q_atts = wrote_q_atts = 0
        file_upserts = 0

        for r in rows:
            # Required
            qtext = (G(r, "Question Text", "question_text") or "").strip()
            if not qtext:
                continue

            # Optional
            ctx_local = (G(r, "Context ID", "context_id", "contextid") or "").strip()
            qnum      = (G(r, "Question Number", "question_number") or "").strip() or None
            subqnum   = (G(r, "Sub-Question Number", "sub_question_number") or "").strip() or None
            qtype     = _truncate(((G(r, "Question Type", "question_type") or "").strip() or None), MAX_QTYPE)
            a = (G(r, "Option A", "option_a") or None)
            b = (G(r, "Option B", "option_b") or None)
            c = (G(r, "Option C", "option_c") or None)
            d = (G(r, "Option D", "option_d") or None)
            e = (G(r, "Option E", "option_e") or None)
            ans_raw = (G(r, "Correct Answer", "correct_answer") or None)
            expl    = (G(r, "Explanation", "explanation") or None)
            pts_txt = (G(r, "Points", "points") or "").strip()
            diff    = _truncate((G(r, "Difficulty", "difficulty") or None), MAX_DIFFICULTY)
            conc    = _truncate((G(r, "Concepts", "concepts") or None), MAX_CONCEPTS)
            qatt    = (G(r, "Attachment", "attachment") or "").strip()

            # Points normalization -> numeric or None
            pts = None
            if pts_txt:
                try:
                    pts = float(pts_txt)
                except Exception:
                    pts = None

            # Correct answer length guard
            ans = ans_raw
            if ans is not None and len(ans) > MAX_CORRECT_ANSWER:
                # spill into explanation, leave short marker as answer
                spill = f"[Answer moved here]\n{ans}"
                if expl:
                    expl = (expl + "\n\n" + spill)
                else:
                    expl = spill
                expl = _truncate(expl, MAX_EXPLANATION)
                ans = "See explanation"
            # Explanation length guard
            if expl is not None:
                expl = _truncate(expl, MAX_EXPLANATION)

            if qatt:
                saw_q_atts += 1

            # map context if present
            ctx_id = None
            if ctx_local:
                ctx_id = session.execute(
                    text("""
                      SELECT ctx.context_id
                      FROM contexts ctx
                      WHERE ctx.assessment_id=:aid AND ctx.context_local_id=:clid
                      ORDER BY ctx.context_id LIMIT 1
                    """),
                    {"aid": assessment_id, "clid": ctx_local}
                ).scalar()

            # upsert by natural key
            res = session.execute(
                text("""
                  INSERT INTO questions (
                    assessment_id, course_id, context_id,
                    question_number, sub_question_number,
                    question_text, question_type,
                    option_a, option_b, option_c, option_d, option_e,
                    correct_answer, explanation, points, difficulty, concepts,
                    version_number, is_latest
                  )
                  VALUES (
                    :aid, :cid, :ctx,
                    :qnum, :sqnum,
                    :qtxt, :qtype,
                    :a, :b, :c, :d, :e,
                    :ans, :expl, :pts, :diff, :conc,
                    1, TRUE
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
                    context_id     = COALESCE(EXCLUDED.context_id, questions.context_id),
                    is_latest      = TRUE
                  RETURNING question_id
                """),
                {
                    "aid": assessment_id, "cid": course_id, "ctx": ctx_id,
                    "qnum": qnum, "sqnum": subqnum,
                    "qtxt": qtext, "qtype": qtype,
                    "a": a, "b": b, "c": c, "d": d, "e": e,
                    "ans": ans, "expl": expl, "pts": pts, "diff": diff, "conc": conc
                }
            )
            qid = res.scalar()
            file_upserts += 1

            if qid and qatt:
                session.execute(
                    text("""
                      INSERT INTO question_attachments (question_id, attachment_name, attachment_url)
                      VALUES (:qid, :name, NULL)
                      ON CONFLICT (question_id, attachment_name) DO NOTHING
                    """),
                    {"qid": qid, "name": qatt}
                )
                wrote_q_atts += 1

        session.commit()

        # sample attachments
        sample = []
        if saw_q_atts:
            for r in rows:
                v = (G(r, "Attachment", "attachment") or "").strip()
                if v:
                    sample.append(v)
                if len(sample) >= 5:
                    break

        total_upserts += file_upserts
        total_qatts += wrote_q_atts
        print(f"  ✅ {csv_path.name}: q+= {file_upserts} (cum={total_upserts}), "
              f"q_atts saw={saw_q_atts}, wrote={wrote_q_atts}, sample={sample}")

    print(f"✅ Questions upserted: {total_upserts}, question attachments: {total_qatts}")
    return total_upserts, total_qatts

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n==============================")
    print("📦 Initializing QuizBank DB")
    print("==============================\n")

    # 0) Try to create CSVs (optional)
    try_convert_xlsx_to_csv()

    # 1) DB ready?
    if not wait_for_db():
        sys.exit(1)

    session = SessionLocal()
    try:
        # 2) Ensure schema & constraints & unique index
        ensure_schema(session)

        # 3) Decide whether to seed
        seeded = already_seeded(session)
        if seeded and not is_seed_forced():
            print("ℹ️ Database already initialized by Python seeder — skipping ALL data load.\n")
        else:
            # 4) Seed from canonical + payload (all seeding happens together)
            print(f"📂 Looking for CSVs in: {DATA_DIR}")
            if not DATA_DIR.exists():
                print("❌ CSV data directory not found. Aborting seeding.")
                sys.exit(1)

            # 4a) Courses (authoritative)
            load_courses_from_master_csv(session, COURSES_MASTER)

            # 4b) Quick payload presence warning
            payload_count = (
                len(list(Path(DATA_DIR).glob("*_context*.csv"))) +
                len(list(Path(DATA_DIR).glob("*_questions*.csv")))
            )
            if payload_count == 0:
                print(f"⚠️ No *_context.csv / *_questions.csv files found in {DATA_DIR}. Nothing to seed into contexts/questions.")

            # 4c) Infer assessments from filenames (idempotent)
            create_assessments_from_filenames(session, DATA_DIR)

            # 4d) Load contexts & questions
            load_contexts_from_csvs(session, DATA_DIR)
            load_questions_from_csvs(session, DATA_DIR)

            # 4e) Sentinel
            mark_seeded(session)
            print("✅ Seeding complete (sentinel written).")

        # 5) Final counts
        counts = {
            "courses":              safe_count(session, "courses"),
            "assessments":          safe_count(session, "assessments"),
            "contexts":             safe_count(session, "contexts"),
            "questions":            safe_count(session, "questions"),
            "context_attachments":  safe_count(session, "context_attachments"),
            "question_attachments": safe_count(session, "question_attachments"),
        }
        print("\n📊 Final counts:")
        for k, v in counts.items():
            print(f"  - {k}: {v}")
        print()

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
