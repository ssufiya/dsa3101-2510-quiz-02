#!/usr/bin/env bash
# bootstrap_db.sh
# End-to-end bootstrap for QuizBank DB:
# - Start containers
# - Restore from a *non-empty* backup if requested
# - Otherwise seed from CSV/XLSX via init_db.py
# - Take a fresh backup after a successful seed
# Env knobs:
#   RESTORE_IF_BACKUP=1  -> restore if latest.sql.gz exists AND has data
#   SEED_FORCE=1         -> force seeder to run even if sentinel exists
#   SEED_SKIP_XLSX=1     -> skip XLSX->CSV conversion step inside seeder

set -euo pipefail

# --- Paths ---
REPO="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BACKEND="$REPO/backend"
QDB="$BACKEND/quizbank-db"
SCRIPTS="$QDB/scripts"
DBINIT="$QDB/db-init"
DATA_DIR="$DBINIT/data"
PNG_BUCKET="$QDB/storage/png"
BACKUP_DIR="${BACKUP_DIR:-$REPO/backend/backups/quizbank}"
ASSETS_BACKUP_DIR="${ASSETS_BACKUP_DIR:-$REPO/backend/backups/assets}"
COMPOSE="$REPO/docker-compose.yml"

mkdir -p "$BACKUP_DIR" "$PNG_BUCKET"

echo "Repo:         $REPO"
echo "Backend:      $BACKEND"
echo "DB init dir:  $DBINIT"
echo "Data dir:     $DATA_DIR"
echo "PNG bucket:   $PNG_BUCKET"
echo "Backups dir:  $BACKUP_DIR"
echo

# --- Start services ---
docker compose -f "$COMPOSE" up -d
echo "🔍 Waiting for Postgres container 'quizbank_db'..."
until docker inspect -f '{{.State.Health.Status}}' quizbank_db 2>/dev/null | grep -q healthy; do
  sleep 1
done
echo "✅ DB container healthy."

LATEST_DUMP="$BACKUP_DIR/latest.sql.gz"

# --- Helper: check if a dump actually contains data rows for any core table ---
backup_has_data() {
  local dump="${1:-$LATEST_DUMP}"
  [ -s "$dump" ] || return 1
  # Look for any COPY block for core tables that has at least one data row
  # (COPY header ... rows ... \.)
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

if [ "$RESTORE_IF_BACKUP" = "1" ] && backup_has_data "$LATEST_DUMP"; then
  echo "📦 Backup found & non-empty — restoring…"
  bash "$SCRIPTS/restore_db.sh"
  RAN_ACTION="restore"
  
  echo "🗂 Restoring assets snapshot…"
  bash "$SCRIPTS/restore_assets.sh" || echo "⚠️ restore_assets.sh failed (continuing)"
  RAN_ACTION="restore"

else
  if [ "$RESTORE_IF_BACKUP" = "1" ] && [ -f "$LATEST_DUMP" ]; then
    echo "⚠️  latest.sql.gz exists but appears EMPTY. Seeding instead."
  else
    echo "🧪 No backup restore requested (or missing dump). Seeding instead."
  fi

  # Run the Python seeder; allow overrides via env vars passed through
  SEED_FORCE="${SEED_FORCE:-1}"
  SEED_SKIP_XLSX="${SEED_SKIP_XLSX:-1}"

  echo "📥 Seeding DB via init_db.py (SEED_FORCE=$SEED_FORCE, SEED_SKIP_XLSX=$SEED_SKIP_XLSX)…"
  SEED_FORCE="$SEED_FORCE" SEED_SKIP_XLSX="$SEED_SKIP_XLSX" \
    python3 "$SCRIPTS/init_db.py"
  RAN_ACTION="seed"

  echo "💾 Creating immediate backup after seed…"
  bash "$SCRIPTS/backup_db.sh"

  echo "🗂 Backing up assets after seed…"
  bash "$SCRIPTS/backup_assets.sh" || echo "⚠️ backup_assets.sh failed (continuing)"
  
fi

# --- Sanity check: counts from core tables ---
echo "🔎 Sanity-checking table counts…"
docker exec -it quizbank_db psql -U postgres -d quizbank -c \
"SELECT
  (SELECT count(*) FROM courses)               AS courses,
  (SELECT count(*) FROM assessments)           AS assessments,
  (SELECT count(*) FROM contexts)              AS contexts,
  (SELECT count(*) FROM questions)             AS questions,
  (SELECT count(*) FROM context_attachments)   AS ctx_atts,
  (SELECT count(*) FROM question_attachments)  AS q_atts;"

echo
echo "✅ bootstrap_db.sh finished via: $RAN_ACTION"
echo "   (Tip) To force restore next time: RESTORE_IF_BACKUP=1 $0"
echo "   (Tip) To force seeding even if sentinel exists: SEED_FORCE=1 $0"
