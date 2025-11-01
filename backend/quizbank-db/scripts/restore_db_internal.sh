#!/usr/bin/env bash
# restore_db_internal.sh - runs INSIDE the container
set -euo pipefail

REPO="${REPO_ROOT:-/app}"
BACKUP_DIR="$REPO/backend/backups/quizbank"
LATEST="$BACKUP_DIR/latest.sql.gz"

if [ ! -e "$LATEST" ]; then
  echo "❌ No latest.sql.gz found at $LATEST"
  exit 1
fi

echo "🧨 Dropping schema public..."
psql -h db -U postgres -d quizbank -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "📥 Restoring DB from $LATEST ..."
gunzip -c "$LATEST" | psql -h db -U postgres -d quizbank

echo "✅ DB restore complete."