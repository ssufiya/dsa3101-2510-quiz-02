#!/usr/bin/env bash
set -euo pipefail
REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$REPO/backend/backups/quizbank}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/quizbank_${STAMP}.sql.gz"

echo "💾 Creating DB backup: $OUT"
docker exec -i quizbank_db pg_dump -U postgres -d quizbank | gzip > "$OUT"

ln -sfn "$(basename "$OUT")" "$BACKUP_DIR/latest.sql.gz"
echo "✅ DB backup ready: $OUT"

