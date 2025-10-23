#!/usr/bin/env python3
import csv, io, os, re, sys, textwrap
from pathlib import Path
from collections import Counter, defaultdict
import psycopg2

# --- CONFIG ---
REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "quizbank-db/db-init/data"
MASTER_COURSES = DATA_DIR / "updated_nus_dsa_courses.csv"

# replace the PG dict section with this:
import os
PG = dict(
    host=os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "localhost")),   # use quizbank_db inside containers
    port=int(os.getenv("PGPORT", os.getenv("POSTGRES_PORT", "5432"))),
    dbname=os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "quizbank")),
    user=os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres")),
    password=os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "")),
)


# --- Filename regex (same as init_db) ---
FNAME_RE = re.compile(r"""
^
(?P<course>[A-Za-z]{2,}\d{4})
(?:_Sem(?P<sem>\d))?
(?:_(?P<acad>\d{4}))?
_(?P<title>.+)
_(?P<kind>context|contexts|questions)
$
""", re.IGNORECASE | re.VERBOSE)

def parse_meta(name):
    stem = name[:-4] if name.lower().endswith(".csv") else name
    m = FNAME_RE.match(stem)
    if not m: return None
    course = m.group("course").upper()
    title  = m.group("title").strip()
    kind   = "contexts" if "context" in m.group("kind").lower() else "questions"
    ay     = m.group("acad") or None
    sem    = m.group("sem") or None
    return (course, title, kind, ay, sem)

def read_csv_rows(p: Path):
    b = p.read_bytes()
    try:
        s = b.decode("utf-8-sig")
    except UnicodeDecodeError:
        s = b.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(s)))

def norm(v): return (v or "").strip()

def main():
    if not DATA_DIR.exists():
        print(f"ERROR: data dir not found: {DATA_DIR}")
        sys.exit(1)

    # ---------- EXPECTED FROM FILES ----------
    files = sorted(list(DATA_DIR.glob("*_context*.csv")) + list(DATA_DIR.glob("*_questions*.csv")))
    expected_assess = set()
    expected_questions = Counter()
    expected_contexts = Counter()
    expected_q_atts = Counter()
    expected_c_atts = Counter()
    dup_q_by_assessment = defaultdict(lambda: defaultdict(int))  # (course,atype,ay,sem)[qtext] -> count

    for p in files:
        meta = parse_meta(p.name)
        if not meta:
            # e.g. template files
            continue
        course, atype, kind, ay, sem = meta
        key = (course, atype, ay or "", sem or "")
        expected_assess.add(key)

        rows = read_csv_rows(p)
        if kind == "questions":
            qt_nonempty = 0
            for r in rows:
                qtxt = norm(r.get("Question Text") or r.get("question_text"))
                if qtxt:
                    qt_nonempty += 1
                    expected_questions[key] += 1
                    dup_q_by_assessment[key][qtxt] += 1
                    att = norm(r.get("Attachment") or r.get("attachment"))
                    if att:
                        expected_q_atts[key] += 1
            # (optional) print quick visibility
            # print(f"[CSV] {p.name}: non_empty_question_text={qt_nonempty}")
        else:
            for r in rows:
                ctxt = norm(r.get("Context Text") or r.get("context_text"))
                if ctxt:
                    expected_contexts[key] += 1
                    att = norm(r.get("Attachment") or r.get("attachment"))
                    if att:
                        expected_c_atts[key] += 1

    # duplicates in CSV that would collapse under (course,atype,ay,sem, question_text)
    collapsed = {k: sum(c-1 for c in d.values() if c>1) for k,d in dup_q_by_assessment.items()}

    # ---------- ACTUAL FROM DB ----------
    conn = psycopg2.connect(**PG)
    cur = conn.cursor()

    cur.execute("SELECT course_id, course_code FROM courses")
    code_by_id = {cid:code for cid,code in cur.fetchall()}
    id_by_code = {v:k for k,v in code_by_id.items()}

    cur.execute("""SELECT course_id, assessment_type, COALESCE(assessment_acadyear,''), COALESCE(assessment_semester,''), assessment_id
                   FROM assessments""")
    assess_rows = cur.fetchall()
    assess_set_db = set((code_by_id[cid], at, ay, sem) for (cid, at, ay, sem, aid) in assess_rows if cid in code_by_id)
    aid_by_key = {(code_by_id[cid], at, ay, sem): aid for (cid, at, ay, sem, aid) in assess_rows if cid in code_by_id}

    # contexts count per assessment
    cur.execute("SELECT assessment_id, COUNT(*) FROM contexts GROUP BY 1")
    ctx_db_counts = dict(cur.fetchall())

    # questions count per assessment
    cur.execute("SELECT assessment_id, COUNT(*) FROM questions GROUP BY 1")
    q_db_counts = dict(cur.fetchall())

    # attachments
    cur.execute("""SELECT c.assessment_id, COUNT(*) 
                   FROM context_attachments ca
                   JOIN contexts c ON c.context_id=ca.context_id
                   GROUP BY 1""")
    c_att_db = dict(cur.fetchall())

    cur.execute("""SELECT q.assessment_id, COUNT(*)
                   FROM question_attachments qa
                   JOIN questions q ON q.question_id=qa.question_id
                   GROUP BY 1""")
    q_att_db = dict(cur.fetchall())

    # ---------- REPORT ----------

    print("\n=== A) Courses: master vs DB ===")
    if MASTER_COURSES.exists():
        rows = read_csv_rows(MASTER_COURSES)
        master_codes = { (norm(r.get("course_code") or r.get("Course Code") or r.get("Course_Code"))).upper()
                         for r in rows if norm(r.get("course_code") or r.get("Course Code") or r.get("Course_Code")) }
        db_codes = set(id_by_code.keys())
        missing_in_db = sorted(master_codes - db_codes)
        extra_in_db   = sorted(db_codes - master_codes)
        print(f"Master={len(master_codes)}  DB={len(db_codes)}")
        if missing_in_db: print("  Missing in DB:", missing_in_db)
        if extra_in_db:   print("  Extra in DB:", extra_in_db)
    else:
        print(f"(no master file at {MASTER_COURSES})")

    print("\n=== B) Assessments: expected-from-files vs DB ===")
    only_in_files = sorted(expected_assess - assess_set_db)
    only_in_db    = sorted(assess_set_db - expected_assess)
    print(f"Expected(from files)={len(expected_assess)}  DB={len(assess_set_db)}")
    if only_in_files:
        print("  Missing assessments in DB:")
        for k in only_in_files: print("   -", k)
    if only_in_db:
        print("  Assessments present in DB but not in files:")
        for k in only_in_db: print("   -", k)

    print("\n=== C) Contexts per assessment (CSV non-empty text vs DB) ===")
    ctx_misses = []
    for k, expected in expected_contexts.items():
        aid = aid_by_key.get(k)
        actual = ctx_db_counts.get(aid, 0) if aid else 0
        if actual != expected:
            ctx_misses.append((k, expected, actual))
    print(f"Mismatches: {len(ctx_misses)}")
    for k, exp, act in ctx_misses[:20]:
        print(f"  {k}: expected={exp}, db={act}")

    print("\n=== D) Questions per assessment (CSV non-empty text vs DB) ===")
    q_misses = []
    for k, expected in expected_questions.items():
        aid = aid_by_key.get(k)
        actual = q_db_counts.get(aid, 0) if aid else 0
        if actual != expected:
            q_misses.append((k, expected, actual, collapsed.get(k,0)))
    print(f"Mismatches: {len(q_misses)}   (4th col = duplicates collapsed)")
    for k, exp, act, col in q_misses[:20]:
        print(f"  {k}: expected={exp}, db={act}, collapsed_by_unique={col}")

    print("\n=== E) Attachments (CSV non-empty vs DB inserted) ===")
    # Context atts
    c_att_miss = []
    for k, expected in expected_c_atts.items():
        aid = aid_by_key.get(k)
        actual = c_att_db.get(aid, 0) if aid else 0
        if actual != expected:
            c_att_miss.append((k, expected, actual))
    print(f"Context-attachments mismatches: {len(c_att_miss)}")
    for k, exp, act in c_att_miss[:20]:
        print(f"  {k}: expected={exp}, db={act}")

    # Question atts
    q_att_miss = []
    for k, expected in expected_q_atts.items():
        aid = aid_by_key.get(k)
        actual = q_att_db.get(aid, 0) if aid else 0
        if actual != expected:
            q_att_miss.append((k, expected, actual))
    print(f"Question-attachments mismatches: {len(q_att_miss)}")
    for k, exp, act in q_att_miss[:20]:
        print(f"  {k}: expected={exp}, db={act}")

    # Optional: show top duplicate question texts per assessment
    print("\n=== F) Top duplicate question_texts per assessment (that would collapse) ===")
    for k, d in dup_q_by_assessment.items():
        dups = [(t,c) for t,c in d.items() if c>1]
        if dups:
            dups.sort(key=lambda x: -x[1])
            print(" ", k, "=>", sum(c-1 for _,c in dups), "rows collapsed")
            for t,c in dups[:3]:
                t_short = t.replace("\n"," ")[:100]
                print(f"     x{c}: {t_short!r}")
    print("\nDone.")
if __name__ == "__main__":
    main()
