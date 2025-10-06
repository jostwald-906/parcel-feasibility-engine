# Installation Guide

## Option 1: Docker (Recommended)

The easiest way to run the project with all dependencies:

```bash
# Start all services (PostgreSQL + API)
make docker-up

# Run tests inside Docker container
docker-compose exec api pytest -q

# Stop services
make docker-down
```

## Option 2: Local Development

### Prerequisites

1. **Python 3.11+**
2. **PostgreSQL 14+ with PostGIS extension**
3. **System libraries**:
   - macOS: `brew install postgresql@14 gdal`
   - Linux: `sudo apt-get install postgresql-14 postgresql-14-postgis-3 libgdal-dev`

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb parcels_feasibility
psql parcels_feasibility -c "CREATE EXTENSION postgis;"

# Run migrations
alembic upgrade head

# Run tests
pytest -q

# Start development server
uvicorn app.main:app --reload
```

## Common Issues

### Issue: `psycopg2-binary` won't compile

**Solution**: Install PostgreSQL development headers:
- macOS: `brew install postgresql@14`
- Linux: `sudo apt-get install libpq-dev`

### Issue: `shapely` won't compile

**Solution**: Install GDAL:
- macOS: `brew install gdal`
- Linux: `sudo apt-get install libgdal-dev`

### Issue: Python 3.13 compatibility

**Solution**: Use Python 3.11 or 3.12:
```bash
# Install Python 3.11
brew install python@3.11

# Create venv with specific version
python3.11 -m venv venv
```

## Verifying Installation

```bash
# Check Python version
python --version  # Should be 3.11 or 3.12

# Check installed packages
pip list | grep -E "fastapi|sqlmodel|pytest"

# Run health check
curl http://localhost:8000/health
```

## Development Workflow

```bash
# Format code
make format

# Run linters
make lint

# Run tests with coverage
make test

# Clean build artifacts
make clean
```
