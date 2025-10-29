#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
ASSETS_BACKUP_DIR="${ASSETS_BACKUP_DIR:-$REPO/backend/backups/assets}"

# Tarball to use
ASSETS_SRC="${ASSETS_SRC:-$ASSETS_BACKUP_DIR/latest.tgz}"

# Storage root (where assets should live in the repo)
STORAGE_DIR_REL="${STORAGE_DIR_REL:-backend/quizbank-db/storage}"
STORAGE_DIR="$REPO/$STORAGE_DIR_REL"

# Clean restore toggle
CLEAN_RESTORE="${CLEAN_RESTORE:-0}"

if [ ! -f "$ASSETS_SRC" ]; then
  echo "ℹ️ No assets tarball at $ASSETS_SRC (skipping assets restore)."
  exit 0
fi

mkdir -p "$STORAGE_DIR"

if [ "$CLEAN_RESTORE" = "1" ]; then
  echo "🧹 CLEAN_RESTORE=1: removing current contents of $STORAGE_DIR_REL"
  rm -rf "$STORAGE_DIR"/*
fi

echo "🗂  Restoring assets from: $ASSETS_SRC -> $STORAGE_DIR_REL"
# Because the tar has paths relative to storage/, we extract *into* storage/
tar -xzf "$ASSETS_SRC" -C "$STORAGE_DIR"

echo "✅ Assets restore complete."
