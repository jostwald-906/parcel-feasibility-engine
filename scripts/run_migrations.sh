#!/bin/bash
# Run database migrations on Railway
# Usage: railway run bash scripts/run_migrations.sh

set -e

echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations completed successfully!"
