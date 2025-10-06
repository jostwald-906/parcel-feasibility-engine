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
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Create cache directory
RUN mkdir -p .cache/rent_control

# Expose port (Railway will set $PORT dynamically)
EXPOSE 8000

# Run via start.sh script which handles PORT environment variable
CMD ["./start.sh"]
