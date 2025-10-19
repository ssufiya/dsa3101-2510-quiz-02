# ============================================================
# Dockerfile for quizbank-api
# ============================================================

# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional but helps with psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Expose Flask port
EXPOSE 5000

# Start your app (same as docker-compose command)
CMD ["bash", "-c", "python load_sample_data.py && python app.py"]
