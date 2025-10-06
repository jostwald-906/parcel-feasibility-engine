#!/bin/bash
set -e

echo "Starting Parcel Feasibility Engine..."
echo "PORT: ${PORT:-8000}"
echo "ENVIRONMENT: ${ENVIRONMENT:-development}"

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
