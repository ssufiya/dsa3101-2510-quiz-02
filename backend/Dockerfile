FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for database operations, backup/restore, and file processing
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    bash \
    gzip \
    tar \
    curl \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p \
    /app/quizbank-db/storage/png \
    /app/quizbank-db/storage/other \
    /app/quizbank-db/uploads \
    /app/uploads \
    /app/backups/quizbank \
    /app/backups/assets \
    /app/scripts \
    /app/quizbank-db/scripts \
    /app/quizbank-db/db-init/data

# Create .gitkeep files to preserve empty directories
RUN touch /app/quizbank-db/storage/png/.gitkeep \
    && touch /app/quizbank-db/uploads/.gitkeep \
    && touch /app/backups/quizbank/.gitkeep \
    && touch /app/backups/assets/.gitkeep

# Make all scripts in the scripts directory executable
RUN find /app/quizbank-db/scripts -type f -name "*.sh" -exec chmod +x {} \; || true
RUN find /app/quizbank-db/scripts -type f -name "*.py" -exec chmod +x {} \; || true
RUN find /app/scripts -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# Set proper permissions for working directories
RUN chmod -R 755 /app/quizbank-db/storage \
    && chmod -R 755 /app/quizbank-db/uploads \
    && chmod -R 755 /app/backups

# Expose port
EXPOSE 5000
