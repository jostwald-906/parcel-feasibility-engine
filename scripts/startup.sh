#!/bin/bash
# Startup script for Railway deployment
# Runs database migrations and starts the application

set -e

echo "Starting Parcel Feasibility Engine..."

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head || {
    echo "Migration failed, checking if tables already exist..."
    # If migrations fail due to existing tables, stamp the current revision
    alembic stamp head
    echo "Database stamped with current revision"
}

echo "Migrations complete!"

# Start uvicorn server
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
