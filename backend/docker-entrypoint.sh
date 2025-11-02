#!/bin/bash
set -e

echo "=================================="
echo "Starting Backend Container"
echo "=================================="

# Wait for database to be ready
echo "Waiting for database..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "  Database is unavailable - sleeping"
  sleep 2
done
echo "✓ Database is ready"

# Run bootstrap (includes init, restore, sanitization, etc.)
if [ -f /app/quizbank-db/scripts/bootstrap_db.sh ]; then
  echo "Running bootstrap script..."
  chmod +x /app/quizbank-db/scripts/*.sh
  /app/quizbank-db/scripts/bootstrap_db.sh || echo "Bootstrap failed, continuing..."
else
  echo "Bootstrap script not found, running init_db.py manually..."
  python /app/quizbank-db/scripts/init_db.py
fi

# Start the application
echo "Starting FastAPI..."
exec "$@"

