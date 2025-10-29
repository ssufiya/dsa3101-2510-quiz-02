#!/usr/bin/env bash
set -euo pipefail

# Repo root
REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Default asset roots (relative to REPO). You now only use storage/
ASSET_ROOTS_REL_DEFAULT=("backend/quizbank-db/storage")
IFS=' ' read -r -a ASSET_ROOTS_REL <<< "${ASSET_ROOTS_REL:-${ASSET_ROOTS_REL_DEFAULT[*]}}"

ASSETS_BACKUP_DIR="${ASSETS_BACKUP_DIR:-$REPO/backend/backups/assets}"
mkdir -p "$ASSETS_BACKUP_DIR"

# Pair with DB stamp if provided
STAMP="${ASSETS_STAMP:-$(date +%Y%m%d_%H%M%S)}"
OUT="$ASSETS_BACKUP_DIR/assets_${STAMP}.tgz"
MANIFEST="$ASSETS_BACKUP_DIR/assets_${STAMP}.manifest.txt"

# Build list of existing roots (should be just the storage/ root)
TO_ARCHIVE=()
for rel in "${ASSET_ROOTS_REL[@]}"; do
  [ -d "$REPO/$rel" ] && TO_ARCHIVE+=("$rel")
done

if [ "${#TO_ARCHIVE[@]}" -eq 0 ]; then
  echo "ℹ️ No asset roots found. Searched: ${ASSET_ROOTS_REL[*]} (skipping assets backup)."
  exit 0
fi

echo "🗂  Creating assets backup: $OUT"
printf "📄 Included paths (relative to each root):\n" > "$MANIFEST"

# Archive each root separately, changing into it so paths are *short* in the tar
# This preserves directory structure *under* storage/ (e.g., png/, contexts/, etc.)
TMP_TAR="$OUT.tmp"
: > "$TMP_TAR"

for rel in "${TO_ARCHIVE[@]}"; do
  printf "  - %s\n" "$rel" >> "$MANIFEST"

  # Create or append to the tar. The first root uses 'czf', subsequent use 'rf'.
  if [ ! -s "$TMP_TAR" ]; then
    tar \
      --exclude='**/.DS_Store' \
      --exclude='**/__pycache__' \
      -czf "$TMP_TAR" -C "$REPO/$rel" .
  else
    # append files from another root (rare in your case, but supported)
    tar \
      --exclude='**/.DS_Store' \
      --exclude='**/__pycache__' \
      -rf "$TMP_TAR" -C "$REPO/$rel" .
  fi

  # Record a manifest of files (relative to each root)
  (cd "$REPO/$rel" && find . -type f -print0 | xargs -0 ls -l >> "$MANIFEST" || true)
done

# Recompress if we appended (tar rf creates an uncompressed tar; normalize to .tgz)
if file "$TMP_TAR" | grep -qi 'gzip compressed'; then
  mv "$TMP_TAR" "$OUT"
else
  gzip -c "$TMP_TAR" > "$OUT"
  rm -f "$TMP_TAR"
fi

ln -sfn "$(basename "$OUT")" "$ASSETS_BACKUP_DIR/latest.tgz"
ln -sfn "$(basename "$MANIFEST")" "$ASSETS_BACKUP_DIR/latest.manifest.txt"

echo "✅ Assets backup ready: $OUT"
