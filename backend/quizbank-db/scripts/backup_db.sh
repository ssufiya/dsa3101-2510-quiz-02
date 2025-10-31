#!/usr/bin/env bash
set -euo pipefail

# Determine backup directory
REPO="${REPO:-/app}"
BACKUP_DIR="${BACKUP_DIR:-$REPO/backups/quizbank}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/backup_${STAMP}.sql.gz"

echo "💾 Creating DB backup: $OUT"

# Detect environment: inside vs outside Docker
if command -v pg_dump > /dev/null 2>&1; then
  # Inside container (pg_dump available)
  pg_dump -h db -U postgres -d quizbank | gzip > "$OUT"
else
  # Running on host (fallback)
  docker exec -i quizbank_db pg_dump -U postgres -d quizbank | gzip > "$OUT"
fi

ln -sfn "$(basename "$OUT")" "$BACKUP_DIR/latest.sql.gz"
echo "✅ DB backup ready: $OUT"
