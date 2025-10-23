#!/bin/bash
set -euo pipefail

# === CONFIG ===
CONTAINER="quizbank_db"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${ROOT_DIR}/quizbank-db/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEST="${BACKUP_DIR}/${TIMESTAMP}"
mkdir -p "${DEST}"

echo ""
echo "=============================================="
echo "💾 FULL SYSTEM BACKUP - ${TIMESTAMP}"
echo "=============================================="

# --- Step 1: Dump PostgreSQL DB ---
echo "📦 Dumping database..."
docker exec "${CONTAINER}" pg_dump -U postgres -d quizbank > "${DEST}/quizbank_${TIMESTAMP}.sql"
echo "✅ Database dump created: ${DEST}/quizbank_${TIMESTAMP}.sql"

# --- Step 2: Copy data assets (attachments only) ---
echo ""
echo "📁 Copying attachments..."

if [ -d "${ROOT_DIR}/data" ]; then
  mkdir -p "${DEST}/data_assets"
  echo "📁 Copying attachments (PNG, JPG, PDF, R, etc.)..."
  find "${ROOT_DIR}/data" -maxdepth 1 -type f \( \
    -iname "*.png" -o \
    -iname "*.jpg" -o \
    -iname "*.jpeg" -o \
    -iname "*.pdf" -o \
    -iname "*.r" -o \
    -iname "*.py" \
    -iname "*.csv" \
  \) -exec cp {} "${DEST}/data_assets/" \;
  echo "✅ Copied attachments to ${DEST}/data_assets"
else
  echo "⚠️ No data folder found at ${ROOT_DIR}/data"
fi


# --- Step 3: Copy scripts (for reproducibility) ---
echo ""
echo "📜 Copying key scripts for snapshot..."

mkdir -p "${DEST}/scripts_snapshot"

rsync -av --exclude='__pycache__' --exclude='*.pyc' \
  "${ROOT_DIR}/quizbank-db/scripts/" "${DEST}/scripts_snapshot/" > /dev/null

echo "✅ Script snapshot created at ${DEST}/scripts_snapshot"

# --- Step 4: Finish up ---
echo ""
echo "🎉 Backup complete: ${DEST}"
du -sh "${DEST}" | awk '{print "📦 Total size:", $1}'
echo "=============================================="
echo "✅ Backup finished successfully!"
echo "=============================================="
