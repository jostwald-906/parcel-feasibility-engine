# Parcel Feasibility Engine

California housing development feasibility analysis platform for analyzing residential development opportunities under state housing laws (SB 9, SB 35, AB 2011, Density Bonus).

## Overview

This application analyzes California residential parcels to determine feasibility for housing development under various state streamlining laws. It integrates multiple data sources including GIS services, rent control databases, RHNA performance metrics, and environmental constraints.

## Architecture

- **Backend**: FastAPI (Python 3.13) with Uvicorn
- **Frontend**: Next.js 15.5.4 with TypeScript and Turbopack
- **APIs**: Santa Monica GIS, California rent control, environmental data
- **Validation**: Pydantic v2 models with strict type checking

## Features

- **SB 9 Analysis**: Lot splits and duplex conversions
- **SB 35 Analysis**: Streamlined ministerial approval (10-50% affordable housing)
- **AB 2011 Analysis**: 100% affordable housing projects on commercial/parking sites
- **Density Bonus**: State density bonus calculations with tiered standards
- **Environmental Checks**: Historic resources, wetlands, fire hazard zones, coastal zones
- **Rent Control Integration**: Santa Monica rent control database lookup with caching

## Local Development

### Prerequisites

- Python 3.13
- Node.js 18+
- pip and npm

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000

## Deployment

### Backend (Railway)

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Create project: `railway init`
4. Deploy: `railway up`

Configuration is in [railway.json](railway.json). The backend uses the Procfile for the start command.

### Frontend (Vercel)

1. Install Vercel CLI: `npm install -g vercel`
2. Deploy: `cd frontend && vercel`
3. Set environment variable: `NEXT_PUBLIC_API_URL` to your Railway backend URL

Configuration is in [frontend/vercel.json](frontend/vercel.json).

### Docker

```bash
# Build image
docker build -t parcel-feasibility-engine .

# Run container
docker run -p 8000:8000 parcel-feasibility-engine
```

## Environment Variables

### Backend
- `PORT`: Server port (default: 8000)
- `ENVIRONMENT`: production/development

### Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run backend tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Project Structure

```
├── app/
│   ├── api/          # API endpoints
│   ├── models/       # Pydantic models
│   ├── services/     # Business logic
│   └── main.py       # FastAPI application
├── frontend/
│   ├── app/          # Next.js app directory
│   ├── components/   # React components
│   └── lib/          # Utilities
├── data/             # Data files and caches
├── tests/            # Backend tests
├── Dockerfile        # Docker configuration
├── railway.json      # Railway deployment config
└── requirements.txt  # Python dependencies
```

## Legal Framework

- **SB 9 (2021)**: Gov. Code § 65852.21 - Urban lot splits and duplex development
- **SB 35 (2017)**: Gov. Code § 65913.4 - Streamlined approval for affordable housing
- **AB 2011 (2022)**: Gov. Code § 65913.5 - 100% affordable on commercial sites
- **Density Bonus Law**: Gov. Code § 65915 - Density increases for affordable housing

## License

Proprietary - All rights reserved
