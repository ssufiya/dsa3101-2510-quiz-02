#!/usr/bin/env bash
set -euo pipefail
REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

ASSETS_BACKUP_DIR="${ASSETS_BACKUP_DIR:-$REPO/backend/backups/assets}"
LATEST="$ASSETS_BACKUP_DIR/latest.tgz"

DEST_REL="backend/quizbank-db/storage/png"
DEST_DIR="$REPO/$DEST_REL"

if [ ! -f "$LATEST" ]; then
  echo "ℹ️ No assets tarball at $LATEST (skipping assets restore)."
  exit 0
fi

mkdir -p "$DEST_DIR"
echo "🖼  Restoring PNGs from $LATEST -> $DEST_REL"
# Merge into existing; remove DEST_DIR/* first if you want a clean slate:
# rm -rf "$DEST_DIR"/*

tar -xzf "$LATEST" -C "$REPO"
echo "✅ PNG restore complete."
