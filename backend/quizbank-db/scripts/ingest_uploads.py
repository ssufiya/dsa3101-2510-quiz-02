#!/usr/bin/env python3
"""
Ingest new CSV + PNG uploads after initial seeding.

- CSVs: parsed with init_db loaders (idempotent upserts)
- PNGs: moved/renamed into storage/png and URL set on *_attachments
- After success: uploaded CSVs are deleted
"""

from __future__ import annotations
import shutil, sys, io, csv
from pathlib import Path
from typing import Optional

# path bootstrap
HERE = Path(__file__).resolve().parent
QDB = HERE.parent
BACKEND = QDB.parent
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from sqlalchemy import text
from app.db.connection import SessionLocal
from app.utils.file_parser import parse_csv

# reuse functions from init_db.py
from quizbank_db.scripts.init_db import (
    parse_meta_from_filename,
    _normalize_dirs,
    load_contexts_from_csvs,
    load_questions_from_csvs,
    ensure_assessment_id,
)

PNG_BUCKET = QDB / "storage" / "png"

def safe_stem(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in s)

def rename_for_assessment(course: str, atype: str, kind: str, local_id: Optional[str], original: Path) -> str:
    """
    e.g. DSA1101-Quiz3-context-1-screenshot.png
         ST2131-Questions-question-15-figureA.png
    """
    base = original.stem
    ext = original.suffix.lower()
    local = f"{local_id}" if local_id else "NA"
    return f"{course}-{atype}-{kind}-{local}-{safe_stem(base)}{ext}"

def move_and_link_pngs(session, upload_png_dir: Path):
    PNG_BUCKET.mkdir(parents=True, exist_ok=True)
    n_linked_ctx = n_linked_q = 0

    for src in sorted(upload_png_dir.glob("*")):
        if not src.is_file():
            continue
        if src.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue

        # try to find a matching attachment row by attachment_name (file name as provided)
        name = src.name

        # context attachments
        ctx_rows = session.execute(text("""
            SELECT ca.context_id, a.assessment_type, c.course_id, crs.course_code, ctx.context_local_id
            FROM context_attachments ca
            JOIN contexts ctx ON ctx.context_id = ca.context_id
            JOIN assessments a ON a.assessment_id = ctx.assessment_id
            JOIN courses crs ON crs.course_id = ctx.course_id
            WHERE ca.attachment_name = :name
            ORDER BY ca.context_id
        """), {"name": name}).fetchall()

        if ctx_rows:
            # move once using first mapping (could be many, but usually one)
            course_code = ctx_rows[0].course_code
            atype = ctx_rows[0].assessment_type
            local_id = str(ctx_rows[0].context_local_id)
            dst_name = rename_for_assessment(course_code, atype, "context", local_id, src)
            dst = PNG_BUCKET / dst_name
            if not dst.exists():
                shutil.copy2(src, dst)
            # set URL on all rows that referenced this name
            for r in ctx_rows:
                session.execute(text("""
                    UPDATE context_attachments
                    SET attachment_url = :url
                    WHERE context_id = :ctx AND attachment_name = :name
                """), {"url": f"/static/png/{dst.name}", "ctx": r.context_id, "name": name})
                n_linked_ctx += 1
            continue

        # question attachments
        q_rows = session.execute(text("""
            SELECT qa.question_id, a.assessment_type, q.course_id, crs.course_code,
                   COALESCE(q.question_number::text,'') AS qn,
                   COALESCE(q.sub_question_number::text,'') AS sq
            FROM question_attachments qa
            JOIN questions q ON q.question_id = qa.question_id
            JOIN assessments a ON a.assessment_id = q.assessment_id
            JOIN courses crs ON crs.course_id = q.course_id
            WHERE qa.attachment_name = :name
            ORDER BY qa.question_id
        """), {"name": name}).fetchall()

        if q_rows:
            course_code = q_rows[0].course_code
            atype = q_rows[0].assessment_type
            local_id = "-".join(filter(None, [q_rows[0].qn, q_rows[0].sq])) or "NA"
            dst_name = rename_for_assessment(course_code, atype, "question", local_id, src)
            dst = PNG_BUCKET / dst_name
            if not dst.exists():
                shutil.copy2(src, dst)
            for r in q_rows:
                session.execute(text("""
                    UPDATE question_attachments
                    SET attachment_url = :url
                    WHERE question_id = :qid AND attachment_name = :name
                """), {"url": f"/static/png/{dst.name}", "qid": r.question_id, "name": name})
                n_linked_q += 1
            continue

        # if no matches, still copy into bucket with a neutral name so it’s available
        dst = PNG_BUCKET / src.name
        if not dst.exists():
            shutil.copy2(src, dst)

    session.commit()
    print(f"🖇  Linked context attachments: {n_linked_ctx}, question attachments: {n_linked_q}")
    return n_linked_ctx, n_linked_q

def ingest_upload_root(upload_root: Path):
    csv_dir = upload_root / "csv"
    png_dir = upload_root / "png"

    if not csv_dir.exists() and not png_dir.exists():
        print(f"❌ Nothing to ingest in {upload_root}")
        return

    s = SessionLocal()
    try:
        if csv_dir.exists():
            print(f"📥 Loading CSVs from: {csv_dir}")
            load_contexts_from_csvs(s, csv_dir)
            load_questions_from_csvs(s, csv_dir)
        if png_dir.exists():
            print(f"🖼  Processing PNGs from: {png_dir}")
            move_and_link_pngs(s, png_dir)

        # after success, delete CSVs as requested
        if csv_dir.exists():
            for f in csv_dir.glob("*.csv"):
                f.unlink(missing_ok=True)
        print("✅ Upload ingest complete.")
    finally:
        s.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: ingest_uploads.py /absolute/path/to/uploads/yyyymmdd")
        sys.exit(2)
    root = Path(sys.argv[1]).resolve()
    ingest_upload_root(root)

if __name__ == "__main__":
    main()
