#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
BACKEND="${BACKEND:-$REPO/backend}"
SCRIPTS="${SCRIPTS:-$BACKEND/quizbank-db/scripts}"
UPLOAD_ROOT="${1:?Usage: ingest_uploads.sh /abs/path/to/uploads/yyyymmdd}"

export BACKUP_DIR="${BACKUP_DIR:-$REPO/backend/backups/quizbank}"
export ASSETS_BACKUP_DIR="${ASSETS_BACKUP_DIR:-$REPO/backend/backups/assets}"

# ensure DB up & healthy
docker compose -f "$REPO/docker-compose.yml" up -d
echo "🔍 Waiting for Postgres container 'quizbank_db'..."
until docker inspect -f '{{.State.Health.Status}}' quizbank_db 2>/dev/null | grep -q healthy; do
  sleep 1
done

# restore first (so DB contains all previous data)
if [ -f "$BACKUP_DIR/latest.sql.gz" ]; then
  echo "♻️  Restoring DB from latest backup before ingest..."
  bash "$SCRIPTS/restore_db.sh"
fi

# ingest CSV + PNGs
export PYTHONPATH="$BACKEND:$PYTHONPATH"
python "$SCRIPTS/ingest_uploads.py" "$UPLOAD_ROOT"

# new backup after ingest
bash "$SCRIPTS/backup_db.sh"
