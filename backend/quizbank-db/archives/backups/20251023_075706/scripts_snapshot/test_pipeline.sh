#!/bin/bash
set -euo pipefail

# === Paths (resolve from repo root) ===========================================
# This file lives at backend/quizbank-db/scripts/test_pipeline.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="${SCRIPT_DIR}"
QB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"              # backend/quizbank-db
BACKEND_DIR="$(cd "${QB_DIR}/.." && pwd)"             # backend
REPO_ROOT="$(cd "${BACKEND_DIR}/.." && pwd)"          # repo root: dsa3101-2510-quiz-02

# after REPO_ROOT/BACKEND_DIR are computed
export PYTHONPATH="${BACKEND_DIR}:${PYTHONPATH:-}"
echo "PYTHONPATH set to: ${PYTHONPATH}"

# === Config ===================================================================
COMPOSE_FILE="${REPO_ROOT}/docker-compose.yml"        # use root compose
CONTAINER="quizbank_db"

INIT_SCRIPT="${SCRIPTS_DIR}/init_db.py"
UPDATE_SCRIPT="${SCRIPTS_DIR}/update_questions.py"
BACKUP_SCRIPT="${SCRIPTS_DIR}/backup_db.sh"
RESTORE_SCRIPT="${SCRIPTS_DIR}/restore_db.sh"

echo ""
echo "=============================================="
echo "🚀 QuizBank Database End-to-End Test Pipeline"
echo "=============================================="
echo "Repo root:      ${REPO_ROOT}"
echo "Backend dir:    ${BACKEND_DIR}"
echo "Scripts dir:    ${SCRIPTS_DIR}"
echo ""

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

# --- Step 1: Start DB (explicit compose file at repo root) --------------------
echo "🧱 Starting Docker services (root compose)..."
docker compose -f "${COMPOSE_FILE}" up -d
wait_for_container

# --- Step 2: Initialize database ---------------------------------------------
echo ""
echo "🔎 Checking if database is already initialised..."

# Recommended: switch to sentinel check once you add system_meta
# If you already added it, uncomment this block and comment the courses check.
# if docker exec "${CONTAINER}" psql -U postgres -d quizbank -tAc \
#    "SELECT 1 FROM system_meta WHERE key='seeded_by_python' LIMIT 1;" | grep -q 1; then

# Temporary: table-exists check
if docker exec "${CONTAINER}" psql -U postgres -d quizbank -tAc \
   "SELECT to_regclass('public.courses');" | grep -q "courses"; then
  echo "✅ Database already initialised — skipping seeding."
else
  echo "⚙️ Running initial database seeding..."
  # IMPORTANT: call by path (avoid -m quizbank-db); init_db.py must add backend to sys.path
  python "${INIT_SCRIPT}"
  echo "💾 Creating baseline backup after first initialisation..."
  bash "${BACKUP_SCRIPT}"
fi

# --- Step 3: Check that tables are populated ---------------------------------
echo ""
echo "🔍 Checking populated table counts..."
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "\dt"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS courses FROM courses;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS assessments FROM assessments;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS contexts FROM contexts;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS questions FROM questions;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS context_attachments FROM context_attachments;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS question_attachments FROM question_attachments;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c \
"SELECT (SELECT COUNT(*) FROM context_attachments) + (SELECT COUNT(*) FROM question_attachments) AS attachments_total;"

# --- Step 4: Backup -----------------------------------------------------------
echo ""
echo "💾 Creating a backup..."
bash "${BACKUP_SCRIPT}"

# --- Step 5: Simulate an update ----------------------------------------------
echo ""
echo "🧩 Running update script..."
python "${UPDATE_SCRIPT}"

echo ""
echo "🔍 Re-checking table counts after update..."
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS questions_after_update FROM questions;"

# --- Step 6: Restore from latest backup --------------------------------------
echo ""
echo "♻️  Restoring from latest backup..."
bash "${RESTORE_SCRIPT}"

echo ""
echo "✅ Re-checking data after restore..."
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS courses FROM courses;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS assessments FROM assessments;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS contexts FROM contexts;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS questions FROM questions;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS context_attachments FROM context_attachments;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c "SELECT COUNT(*) AS question_attachments FROM question_attachments;"
docker exec -it "${CONTAINER}" psql -U postgres -d quizbank -c \
"SELECT (SELECT COUNT(*) FROM context_attachments) + (SELECT COUNT(*) FROM question_attachments) AS attachments_total;"


echo ""
echo "🎉 END-TO-END TEST COMPLETED SUCCESSFULLY!"
