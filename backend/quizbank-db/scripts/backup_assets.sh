#!/usr/bin/env bash
set -euo pipefail
REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

PNG_DIR_REL="backend/quizbank-db/storage/png"
PNG_DIR="$REPO/$PNG_DIR_REL"

ASSETS_BACKUP_DIR="${ASSETS_BACKUP_DIR:-$REPO/backend/backups/assets}"
mkdir -p "$ASSETS_BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$ASSETS_BACKUP_DIR/png_${STAMP}.tgz"

if [ ! -d "$PNG_DIR" ]; then
  echo "ℹ️ No PNG dir at $PNG_DIR_REL (skipping assets backup)."
  exit 0
fi

echo "🖼  Creating PNG backup: $OUT"
tar -czf "$OUT" -C "$REPO" "$PNG_DIR_REL"

ln -sfn "$(basename "$OUT")" "$ASSETS_BACKUP_DIR/latest.tgz"
echo "✅ PNG backup ready: $OUT"
