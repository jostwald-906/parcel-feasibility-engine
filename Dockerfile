FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create cache directory
RUN mkdir -p .cache/rent_control

# Make startup script executable
RUN chmod +x scripts/startup.sh

# Expose port (Railway will set $PORT dynamically)
EXPOSE 8000

# Run startup script
CMD ["bash", "scripts/startup.sh"]
