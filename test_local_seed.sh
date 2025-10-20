#!/bin/bash
# ============================================================
# test_local_seed.sh
# Purpose: Dry-run your SQL seed scripts locally without Docker
# ============================================================

DB_NAME="quizbank_test"
SCHEMA="backend/quizbank-db/db-init/01_schema.sql"
SEED1="backend/quizbank-db/db-init/03_seed_contexts.sql"
SEED2="backend/quizbank-db/db-init/04_seed_questions.sql"

echo "🧩 Checking local PostgreSQL setup..."
if ! command -v psql &> /dev/null; then
    echo "❌ psql not found. Please install PostgreSQL locally first (brew install postgresql)."
    exit 1
fi

echo "🧹 Dropping old test database (if any)..."
psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "🆕 Creating new test database..."
psql -U postgres -c "CREATE DATABASE $DB_NAME;"

# Make temporary copies of seed files with local paths
TMP_SEED1="${SEED1%.sql}_local.sql"
TMP_SEED2="${SEED2%.sql}_local.sql"
cp "$SEED1" "$TMP_SEED1"
cp "$SEED2" "$TMP_SEED2"

# Replace Docker COPY paths with local ones for testing
echo "🔧 Adjusting COPY paths for local test..."
sed -i '' 's|/docker-entrypoint-initdb.d/data/|backend/quizbank-db/db-init/data/|g' "$TMP_SEED1"
sed -i '' 's|/docker-entrypoint-initdb.d/data/|backend/quizbank-db/db-init/data/|g' "$TMP_SEED2"

echo "🏗️ Running schema..."
psql -U postgres -d "$DB_NAME" -f "$SCHEMA"

echo "📦 Loading seed data (contexts)..."
psql -U postgres -d "$DB_NAME" -f "$TMP_SEED1"

echo "📦 Loading seed data (questions)..."
psql -U postgres -d "$DB_NAME" -f "$TMP_SEED2"

echo "🔍 Checking table counts..."
psql -U postgres -d "$DB_NAME" -c "
\\dt;
SELECT 'contexts' AS table, COUNT(*) AS rows FROM contexts
UNION ALL
SELECT 'questions', COUNT(*) FROM questions
UNION ALL
SELECT 'attachments', COUNT(*) FROM attachments
UNION ALL
SELECT 'concepts', COUNT(*) FROM concepts;
"

echo "✅ Test completed!"
echo "🧾 To inspect data manually, run: psql -U postgres -d $DB_NAME"
echo "🧹 To clean up, run: psql -U postgres -c 'DROP DATABASE $DB_NAME;'"

# Cleanup temporary local files
rm "$TMP_SEED1" "$TMP_SEED2"
echo "🧽 Cleaned temporary SQL files."

