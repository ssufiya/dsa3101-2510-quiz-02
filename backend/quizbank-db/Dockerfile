# Start from official Postgres image
FROM postgres:15

# Set environment
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=quizbank

# Copy initialization SQL scripts
COPY db-init/ /docker-entrypoint-initdb.d/

# Copy backup and restore scripts (optional utilities)
COPY scripts/ /scripts/
RUN chmod +x /scripts/*.sh

# Install utilities for backup (optional)
RUN apt-get update && apt-get install -y python3 python3-pip cron vim \
    && pip install sqlalchemy pandas openpyxl psycopg2-binary \
    && apt-get clean

# Optional: add cron job for daily backups
# (uncomment if you want automatic backups)
# RUN echo "0 3 * * * root /scripts/auto_backup.sh" >> /etc/crontab

WORKDIR /scripts
CMD ["postgres"]
