#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=============================================="
echo "🚀 QuizBank Database End-to-End Test Pipeline"
echo "=============================================="
echo ""

# --- Configuration ------------------------------------------------------------
CONTAINER="quizbank_db"          # Must match docker-compose container name
INIT_SCRIPT="${SCRIPT_DIR}/init_db.py"
UPDATE_SCRIPT="${SCRIPT_DIR}/update_questions.py"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup_db.sh"
RESTORE_SCRIPT="${SCRIPT_DIR}/restore_db.sh"

# --- Helper -------------------------------------------------------------------
wait_for_container() {
  echo "🔍 Waiting for Postgres container '${CONTAINER}'..."
  for i in {1..30}; do
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
      echo "✅ Container running."
      return
    fi
    sleep 1
  done
  echo "❌ Container not found. Run 'docker compose up -d' first."
  exit 1
}

# --- Step 1: Start DB ---------------------------------------------------------
echo "🧱 Starting Docker services..."
docker compose up -d
wait_for_container

# --- Step 2: Initialize database ----------------------------------------------
echo ""
echo "🔎 Checking if database is already initialised..."

# Check if a known table (e.g., 'courses') exists inside the quizbank DB
if docker exec "${CONTAINER}" psql -U postgres -d quizbank -tAc \
   "SELECT to_regclass('public.courses');" | grep -q "courses"; then
  echo "✅ Database already initialised — skipping seeding."
else
  echo "⚙️ Running initial database seeding..."
  python -m quizbank-db.scripts.init_db
  echo "💾 Creating baseline backup after first initialisation..."
  bash "${BACKUP_SCRIPT}"
fi

# --- Step 3: Check that tables are populated ----------------------------------
echo ""
echo "🔍 Checking populated table counts..."
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "\dt"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS courses FROM courses;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS assessments FROM assessments;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS contexts FROM contexts;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS questions FROM questions;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS attachments FROM attachments;"


# --- Step 4: Backup -----------------------------------------------------------
echo ""
echo "💾 Creating a backup..."
bash "${BACKUP_SCRIPT}"
