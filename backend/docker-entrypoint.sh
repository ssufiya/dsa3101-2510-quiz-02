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

# Run database initialization
echo ""
echo "Running database initialization..."
python /app/quizbank-db/scripts/init_db.py

# Start the application
echo ""
echo "Starting FastAPI application..."
exec "$@"

