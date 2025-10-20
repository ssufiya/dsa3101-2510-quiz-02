#!/bin/bash
set -e

echo "🔄 Waiting for database..."

# Wait for database with timeout
MAX_RETRIES=30
RETRY_COUNT=0

until pg_isready -h db -p 5432 -U postgres 2>/dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  RETRY_COUNT=$((RETRY_COUNT+1))
  echo "⏳ Database is unavailable - attempt $RETRY_COUNT/$MAX_RETRIES"
  sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "❌ Could not connect to database after $MAX_RETRIES attempts"
  echo "⚠️  Starting API anyway (database might come up later)..."
else
  echo "✅ Database is ready!"
fi

# Run init script if it exists
if [ -f "scripts/init_db.py" ]; then
    echo "🔧 Running database initialization..."
    python scripts/init_db.py || echo "⚠️  Init script failed, continuing..."
fi

echo "🚀 Starting FastAPI application..."
exec "$@"