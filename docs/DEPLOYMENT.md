# Deployment Guide

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Production Deployment](#production-deployment)
3. [Monitoring & Observability](#monitoring--observability)
4. [Health Checks](#health-checks)
5. [Performance Optimization](#performance-optimization)
6. [Security Considerations](#security-considerations)

## Environment Configuration

### Required Environment Variables

The application requires the following environment variables for production deployment. Copy `.env.example` to `.env` and configure:

#### Core Settings

```bash
# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=Santa Monica Parcel Feasibility Engine
VERSION=1.0.0

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### Database

```bash
# PostgreSQL with PostGIS
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

#### Feature Flags

```bash
# Enable/disable state housing law analysis
ENABLE_AB2011=true
ENABLE_SB35=true
ENABLE_DENSITY_BONUS=true
ENABLE_SB9=true
ENABLE_AB2097=true
```

#### GIS Services

```bash
# Santa Monica GIS endpoints
SANTA_MONICA_PARCEL_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer
SANTA_MONICA_ZONING_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/Planning/Zoning/MapServer
SANTA_MONICA_OVERLAY_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/Planning/Overlays/MapServer
SANTA_MONICA_TRANSIT_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/Transportation/Transit/MapServer

# GIS Configuration
GIS_REQUEST_TIMEOUT=30
GIS_MAX_RETRIES=3
GIS_CACHE_TTL=3600
```

#### Security

```bash
# CORS Configuration
BACKEND_CORS_ORIGINS=https://parcels.smgov.net,https://planning.smgov.net

# API Security (optional)
API_KEY_ENABLED=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### Frontend Environment Variables

Create `frontend/.env.local` for production:

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://api.parcels.smgov.net
NEXT_PUBLIC_API_V1_PREFIX=/api/v1

# GIS Services
NEXT_PUBLIC_SANTA_MONICA_PARCEL_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer
# ... other GIS URLs

# Feature Flags
NEXT_PUBLIC_ENABLE_3D_VISUALIZATION=false
NEXT_PUBLIC_ENABLE_NARRATIVE_EXPORT=true
NEXT_PUBLIC_ENABLE_PDF_REPORTS=true

# Analytics
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_ANALYTICS_ENABLED=true
```

## Production Deployment

### Docker Deployment

#### Backend

```dockerfile
# Dockerfile (already exists)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

#### Frontend

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.4
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  backend:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_BASE_URL=${API_BASE_URL}
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  postgres_data:
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: parcel-feasibility-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: parcel-feasibility-api
  template:
    metadata:
      labels:
        app: parcel-feasibility-api
    spec:
      containers:
      - name: api
        image: parcels/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: ENVIRONMENT
          value: "production"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Monitoring & Observability

### Logging

The application uses structured JSON logging in production:

```python
# Configured via LOG_FORMAT=json
{
  "timestamp": "2025-10-06T12:00:00Z",
  "level": "INFO",
  "logger": "app.api.analyze",
  "message": "Request completed",
  "method": "POST",
  "path": "/api/v1/analyze",
  "status_code": 200,
  "duration_ms": 45.2
}
```

#### Log Aggregation

**Option 1: ELK Stack**
```yaml
# docker-compose.logging.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

**Option 2: Cloud Logging**
- Google Cloud Logging
- AWS CloudWatch
- Azure Monitor

### Metrics & Monitoring

#### Prometheus + Grafana

```yaml
# Add to docker-compose
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

#### Key Metrics to Monitor

- **API Metrics:**
  - Request rate (requests/second)
  - Response time (p50, p95, p99)
  - Error rate (4xx, 5xx)
  - Active connections

- **Business Metrics:**
  - Analysis requests by law type (SB9, AB2011, etc.)
  - Average scenarios per parcel
  - Feature flag usage

- **Infrastructure Metrics:**
  - CPU usage
  - Memory usage
  - Database connections
  - GIS service latency

### Error Tracking

**Sentry Integration:**

```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)
```

## Health Checks

### Endpoint: `/health`

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "features": {
    "ab2011": true,
    "sb35": true,
    "density_bonus": true,
    "sb9": true,
    "ab2097": true
  },
  "services": {
    "gis_services_configured": true,
    "narrative_generation": false,
    "database": "configured"
  }
}
```

### Load Balancer Health Checks

Configure health check:
- **Path:** `/health`
- **Expected Status:** 200
- **Interval:** 30 seconds
- **Timeout:** 5 seconds
- **Unhealthy threshold:** 2 consecutive failures

## Performance Optimization

### Backend Optimization

1. **Database Connection Pooling**
```python
# app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

2. **Caching Strategy**
```python
# Redis caching for GIS data
import redis
from functools import lru_cache

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=6379,
    decode_responses=True
)

@lru_cache(maxsize=1000)
def get_parcel_data(apn: str):
    # Cache parcel lookups
    pass
```

3. **Async GIS Requests**
```python
import asyncio
import httpx

async def fetch_gis_data(parcel_id: str):
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(
            client.get(f"{settings.PARCEL_URL}/{parcel_id}"),
            client.get(f"{settings.ZONING_URL}/{parcel_id}"),
            client.get(f"{settings.OVERLAY_URL}/{parcel_id}")
        )
    return responses
```

### Frontend Optimization

1. **Static Generation**
```typescript
// next.config.ts
export default {
  output: 'standalone',
  poweredByHeader: false,
  compress: true,
}
```

2. **Image Optimization**
```typescript
import Image from 'next/image'

<Image
  src="/parcel-map.png"
  width={800}
  height={600}
  loading="lazy"
/>
```

3. **Code Splitting**
```typescript
import dynamic from 'next/dynamic'

const ParcelMap = dynamic(() => import('@/components/ParcelMap'), {
  loading: () => <p>Loading map...</p>,
  ssr: false
})
```

## Security Considerations

### SSL/TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name parcels.smgov.net;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Rate Limiting

```python
# app/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/analyze")
@limiter.limit("60/minute")
async def analyze_parcel(request: Request, ...):
    pass
```

### Security Headers

```python
# app/main.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Environment Secrets

**Use secret management:**

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name parcel-engine/database-url \
  --secret-string "postgresql://..."

# Kubernetes Secrets
kubectl create secret generic db-credentials \
  --from-literal=url='postgresql://...'

# Docker Secrets
echo "postgresql://..." | docker secret create db_url -
```

## Backup & Recovery

### Database Backups

```bash
# Automated backup script
#!/bin/bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
aws s3 cp backup_*.sql s3://parcels-backups/
```

### Disaster Recovery

1. **Database replication** - PostgreSQL streaming replication
2. **Multi-region deployment** - Deploy to multiple availability zones
3. **Backup retention** - 30-day retention policy
4. **Recovery testing** - Quarterly DR drills

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Health checks configured
- [ ] Logging aggregation setup
- [ ] Monitoring dashboards created
- [ ] Backup strategy implemented
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] CORS origins whitelisted
- [ ] Error tracking enabled
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on operations

## Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Docker Production Guide](https://docs.docker.com/config/containers/resource_constraints/)
