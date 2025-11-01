#!/usr/bin/env bash

set -euo pipefail

REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$REPO/backend/backups/quizbank}"
LATEST="$BACKUP_DIR/latest.sql.gz"

if [ ! -f "$LATEST" ]; then
  echo "❌ No latest.sql.gz found at $LATEST"
  exit 1
fi

echo "🧨 Dropping and recreating quizbank database..."
docker exec -i quizbank_db psql -U postgres -c "DROP DATABASE IF EXISTS quizbank;"
docker exec -i quizbank_db psql -U postgres -c "CREATE DATABASE quizbank;"

echo "📥 Restoring DB from $LATEST ..."
gunzip -c "$LATEST" | docker exec -i quizbank_db psql -U postgres -d quizbank

echo "✅ Database restore complete."
