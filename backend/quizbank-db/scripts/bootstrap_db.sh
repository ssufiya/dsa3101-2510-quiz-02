#!/usr/bin/env bash
# bootstrap_db.sh
# End-to-end bootstrap for QuizBank DB

set -euo pipefail

# --- Paths (fixed for Docker) ---
REPO="${REPO_ROOT:-/app}"
BACKEND="$REPO"
QDB="$BACKEND/quizbank-db"
SCRIPTS="$QDB/scripts"
DBINIT="$QDB/db-init"
DATA_DIR="$DBINIT/data"
PNG_BUCKET="$QDB/storage/png"
BACKUP_DIR="${BACKUP_DIR:-/app/backups/quizbank}"
ASSETS_BACKUP_DIR="${ASSETS_BACKUP_DIR:-/app/backups/assets}"
SCHEMA_FILE="$DBINIT/01_schema.sql"

mkdir -p "$BACKUP_DIR" "$PNG_BUCKET"

echo "Repo:         $REPO"
echo "Backend:      $BACKEND"
echo "DB init dir:  $DBINIT"
echo "Schema file:  $SCHEMA_FILE"
echo "Backups dir:  $BACKUP_DIR"
echo

# --- Wait for database ---
echo "🔍 Waiting for Postgres to be ready..."
until pg_isready -h db -U postgres > /dev/null 2>&1; do
  sleep 1
done
echo "✅ DB is ready."

# --- Check if DB already has data (skip restore/seed) ---
FORCE_RESTORE="${FORCE_RESTORE:-0}"    # Allow manual override

if [ "$FORCE_RESTORE" = "1" ]; then
  echo "⚠️  FORCE_RESTORE=1 set — will ignore existing data and continue restore/seed."
else
  echo "🔎 Checking if DB has user data..."
  HAS_ROWS=$(psql -h db -U postgres -d quizbank -tAc "SELECT count(*) FROM questions;" 2>/dev/null || echo 0)
  if [ "$HAS_ROWS" -gt 0 ]; then
    echo "📦 Existing data detected ($HAS_ROWS questions) — skipping restore/seed."
    echo "   (Tip) To force full restore next time: FORCE_RESTORE=1 docker compose up"
    exit 0
  else
    echo "📭 No user data found — continuing to restore or seed."
  fi
fi


# --- CRITICAL: Initialize schema if tables don't exist ---
echo "🔧 Checking if schema exists..."
TABLE_EXISTS=$(psql -h db -U postgres -d quizbank -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'courses');")

if [ "$TABLE_EXISTS" = "f" ]; then
  echo "📋 Schema not found - initializing from $SCHEMA_FILE..."
  if [ -f "$SCHEMA_FILE" ]; then
    psql -h db -U postgres -d quizbank -f "$SCHEMA_FILE" > /dev/null 2>&1
    echo "✅ Schema initialized successfully"
  else
    echo "❌ Schema file not found: $SCHEMA_FILE"
    exit 1
  fi
else
  echo "✅ Schema already exists"
fi

LATEST_DUMP="$BACKUP_DIR/latest.sql.gz"

# --- Helper: check if a dump actually contains data ---
backup_has_data() {
  local dump="${1:-$LATEST_DUMP}"
  [ -s "$dump" ] || return 1
  
  if zcat "$dump" 2>/dev/null | awk '
      /^COPY (courses|assessments|contexts|questions|context_attachments|question_attachments) / { in=1; rows=0; next }
      in && /^\\\./ { if (rows>0) { print "ok"; exit 0 } else { in=0; next } }
      in { rows++ }
    ' | grep -q ok; then
    return 0
  fi
  return 1
}

# --- Decision: restore or seed ---
RESTORE_IF_BACKUP="${RESTORE_IF_BACKUP:-0}"

if [ "$RESTORE_IF_BACKUP" = "1" ] && [ -s "$LATEST_DUMP" ]; then
  echo "📦 Backup found & non-empty — restoring…"

  echo "🧨 Dropping and recreating quizbank database to ensure clean restore..."
  psql -h db -U postgres -c "DROP DATABASE IF EXISTS quizbank;"
  psql -h db -U postgres -c "CREATE DATABASE quizbank;"

  echo "🧩 Restoring from $LATEST_DUMP ..."
  zcat "$LATEST_DUMP" | psql -h db -U postgres -d quizbank
  echo "✅ Database restore completed."

  echo "🗂 Restoring assets snapshot…"
  bash "$SCRIPTS/restore_assets.sh" || echo "⚠️ restore_assets.sh failed (continuing)"
  RAN_ACTION="restore"
else
  if [ "$RESTORE_IF_BACKUP" = "1" ] && [ -f "$LATEST_DUMP" ]; then
    echo "⚠️  latest.sql.gz exists but appears EMPTY. Seeding instead."
  else
    echo "🧪 No backup restore requested (or missing dump). Seeding instead."
  fi
  
  # Run the Python seeder
  SEED_FORCE="${SEED_FORCE:-1}"
  SEED_SKIP_XLSX="${SEED_SKIP_XLSX:-1}"
  
  echo "📥 Seeding DB via init_db.py (SEED_FORCE=$SEED_FORCE, SEED_SKIP_XLSX=$SEED_SKIP_XLSX)…"
  
  if [ -f "$SCRIPTS/init_db.py" ]; then
    SEED_FORCE="$SEED_FORCE" SEED_SKIP_XLSX="$SEED_SKIP_XLSX" \
      python3 "$SCRIPTS/init_db.py" || echo "⚠️ Seeding failed (continuing)"
  else
    echo "⚠️ init_db.py not found, skipping seeding"
  fi
  
  RAN_ACTION="seed"
  
  echo "💾 Creating immediate backup after seed…"
  bash "$SCRIPTS/backup_db.sh" || echo "⚠️ Backup failed (continuing)"
  
  echo "🗂 Backing up assets after seed…"
  bash "$SCRIPTS/backup_assets.sh" || echo "⚠️ backup_assets.sh failed (continuing)"
fi

# --- Sanity check: counts from core tables ---
echo "🔎 Sanity-checking table counts…"
psql -h db -U postgres -d quizbank -c \
  "SELECT
    (SELECT count(*) FROM courses)               AS courses,
    (SELECT count(*) FROM assessments)           AS assessments,
    (SELECT count(*) FROM contexts)              AS contexts,
    (SELECT count(*) FROM questions)             AS questions,
    (SELECT count(*) FROM context_attachments)   AS ctx_atts,
    (SELECT count(*) FROM question_attachments)  AS q_atts;"

echo
echo "✅ bootstrap_db.sh finished via: $RAN_ACTION"
echo "   (Tip) To force restore next time: RESTORE_IF_BACKUP=1"
echo "   (Tip) To force seeding even if sentinel exists: SEED_FORCE=1"