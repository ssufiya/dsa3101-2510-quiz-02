#!/usr/bin/env bash
set -euo pipefail
REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$REPO/backend/backups/quizbank}"
LATEST="$BACKUP_DIR/latest.sql.gz"

if [ ! -f "$LATEST" ]; then
  echo "❌ No latest.sql.gz found at $LATEST"
  exit 1
fi

echo "🧨 Dropping schema public..."
docker exec -i quizbank_db psql -U postgres -d quizbank -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "📥 Restoring DB from $LATEST ..."
gunzip -c "$LATEST" | docker exec -i quizbank_db psql -U postgres -d quizbank

echo "✅ DB restore complete."
