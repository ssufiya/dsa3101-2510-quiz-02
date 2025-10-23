#!/bin/bash
set -euo pipefail

CONTAINER="quizbank_db"
DB_NAME="quizbank"

# --- Resolve paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_ROOT="${QB_DIR}/backups"
LIVE_DATA_DIR="${QB_DIR}/../data"
LIVE_SCRIPTS_DIR="${QB_DIR}/scripts_snapshot"

ARG="${1:-}"   # optional argument for timestamp or path

# --- Helper: locate correct backup file ---
resolve_backup_file() {
  local input="$1"
  if [[ -z "$input" ]]; then
    find "${BACKUP_ROOT}" -type f -name "*.sql" -print0 2>/dev/null \
      | xargs -0 ls -t 2>/dev/null | head -n 1 || true
    return
  fi

  if [[ -d "$input" ]]; then
    ls -t "$input"/*.sql 2>/dev/null | head -n 1 || true; return
  fi
  if [[ -d "${BACKUP_ROOT}/${input}" ]]; then
    ls -t "${BACKUP_ROOT}/${input}"/*.sql 2>/dev/null | head -n 1 || true; return
  fi
  if [[ -f "$input" ]]; then echo "$input"; return; fi
  if [[ -f "${BACKUP_ROOT}/${input}" ]]; then echo "${BACKUP_ROOT}/${input}"; return; fi
}

BACKUP_PATH="$(resolve_backup_file "${ARG}")"

if [[ -z "${BACKUP_PATH}" ]]; then
  echo "❌ Could not locate a backup .sql file."
  exit 1
fi

BACKUP_DIR="$(dirname "${BACKUP_PATH}")"

echo "🧰 Restoring '${DB_NAME}' on container '${CONTAINER}' from:"
echo "   ${BACKUP_PATH}"

# --- Step 1: Restore SQL dump ---
docker exec -i "${CONTAINER}" psql -U postgres -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" >/dev/null

docker exec -i "${CONTAINER}" psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker exec -i "${CONTAINER}" psql -U postgres -d postgres -c "CREATE DATABASE ${DB_NAME};"

cat "${BACKUP_PATH}" | docker exec -i "${CONTAINER}" psql -U postgres -d "${DB_NAME}"

echo "✅ Database restored successfully."

# --- Step 2: Restore data assets (attachments) ---
if [[ -d "${BACKUP_DIR}/data_assets" ]]; then
  echo "📦 Restoring attachments..."
  mkdir -p "${LIVE_DATA_DIR}"
  cp -r "${BACKUP_DIR}/data_assets/"* "${LIVE_DATA_DIR}/" || true
  echo "✅ Restored attachments → ${LIVE_DATA_DIR}/"
else
  echo "⚠️ No attachments found in backup."
fi

# --- Step 3: Restore scripts snapshot (optional) ---
if [[ -d "${BACKUP_DIR}/scripts_snapshot" ]]; then
  echo "📜 Restoring script snapshot..."
  mkdir -p "${LIVE_SCRIPTS_DIR}"
  cp -r "${BACKUP_DIR}/scripts_snapshot/"* "${LIVE_SCRIPTS_DIR}/" || true
  echo "✅ Restored scripts snapshot → ${LIVE_SCRIPTS_DIR}/"
else
  echo "⚠️ No script snapshot found in backup."
fi

echo "🎉 FULL RESTORE COMPLETE."
