# Environment Variables Reference

Complete reference for all environment variables used in the Santa Monica Parcel Feasibility Engine.

## Table of Contents

1. [Backend Variables](#backend-variables)
2. [Frontend Variables](#frontend-variables)
3. [Feature Flags](#feature-flags)
4. [GIS Configuration](#gis-configuration)
5. [Security Settings](#security-settings)
6. [Environment-Specific Settings](#environment-specific-settings)

## Backend Variables

### Core API Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `API_V1_PREFIX` | string | `/api/v1` | API version prefix | No |
| `PROJECT_NAME` | string | `Santa Monica Parcel Feasibility Engine` | Application name | No |
| `VERSION` | string | `1.0.0` | Application version | No |
| `ENVIRONMENT` | string | `development` | Environment name (development/staging/production) | No |
| `DEBUG` | boolean | `false` | Enable debug mode | No |

### Database Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `DATABASE_URL` | string | `sqlite:///./parcel_feasibility.db` | PostgreSQL connection string | Yes |

**Format:** `postgresql://user:password@host:port/database`

**Example:**
```bash
DATABASE_URL=postgresql://parcels:parcels_dev@localhost:5432/parcels_feasibility
```

### CORS Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `BACKEND_CORS_ORIGINS` | list | `["http://localhost:3000", "http://localhost:8000"]` | Allowed CORS origins (comma-separated) | No |

**Example:**
```bash
BACKEND_CORS_ORIGINS=http://localhost:3000,https://parcels.smgov.net
```

### Logging Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) | No |
| `LOG_FORMAT` | string | `json` | Log format (json/text) | No |
| `API_DEBUG_MODE` | boolean | `false` | Enable API debug mode with decision logging | No |

## Frontend Variables

All frontend environment variables must be prefixed with `NEXT_PUBLIC_` to be accessible in the browser.

### API Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `NEXT_PUBLIC_API_BASE_URL` | string | `http://localhost:8000` | Backend API URL | Yes |
| `NEXT_PUBLIC_API_V1_PREFIX` | string | `/api/v1` | API version prefix | No |

### Application Settings

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `NEXT_PUBLIC_APP_NAME` | string | `Santa Monica Parcel Feasibility Engine` | Application name | No |
| `NEXT_PUBLIC_APP_VERSION` | string | `1.0.0` | Application version | No |
| `NEXT_PUBLIC_DEBUG_MODE` | boolean | `false` | Enable frontend debug mode | No |

### Map Configuration

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `NEXT_PUBLIC_MAPBOX_TOKEN` | string | - | Mapbox access token (optional) | No |
| `NEXT_PUBLIC_DEFAULT_MAP_CENTER_LAT` | number | `34.0195` | Default map center latitude | No |
| `NEXT_PUBLIC_DEFAULT_MAP_CENTER_LNG` | number | `-118.4912` | Default map center longitude | No |
| `NEXT_PUBLIC_DEFAULT_MAP_ZOOM` | number | `12` | Default map zoom level | No |

### Analytics

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | string | - | Google Analytics measurement ID | No |
| `NEXT_PUBLIC_ANALYTICS_ENABLED` | boolean | `false` | Enable analytics tracking | No |

## Feature Flags

Control which state housing laws are enabled for analysis:

| Variable | Type | Default | Description | State Law |
|----------|------|---------|-------------|-----------|
| `ENABLE_AB2011` | boolean | `true` | Enable AB 2011 office conversion analysis | AB 2011 (2022) |
| `ENABLE_SB35` | boolean | `true` | Enable SB 35 streamlining analysis | SB 35 (2017) |
| `ENABLE_DENSITY_BONUS` | boolean | `true` | Enable density bonus calculations | Gov Code §65915 |
| `ENABLE_SB9` | boolean | `true` | Enable SB 9 lot split analysis | SB 9 (2021) |
| `ENABLE_AB2097` | boolean | `true` | Enable AB 2097 parking reduction | AB 2097 (2022) |

**Frontend Feature Flags:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NEXT_PUBLIC_ENABLE_3D_VISUALIZATION` | boolean | `false` | Enable 3D building visualization |
| `NEXT_PUBLIC_ENABLE_NARRATIVE_EXPORT` | boolean | `false` | Enable narrative text export |
| `NEXT_PUBLIC_ENABLE_PDF_REPORTS` | boolean | `false` | Enable PDF report generation |

## GIS Configuration

### Backend GIS Services

| Variable | Type | Default | Description | Required |
|----------|------|---------|-------------|----------|
| `SANTA_MONICA_PARCEL_SERVICE_URL` | string | - | Santa Monica parcel GIS service URL | Yes |
| `SANTA_MONICA_ZONING_SERVICE_URL` | string | - | Santa Monica zoning GIS service URL | Yes |
| `SANTA_MONICA_OVERLAY_SERVICE_URL` | string | - | Santa Monica overlay GIS service URL | Yes |
| `SANTA_MONICA_TRANSIT_SERVICE_URL` | string | - | Santa Monica transit GIS service URL | Yes |
| `SCAG_REGIONAL_SERVICE_URL` | string | - | SCAG regional GIS service URL | No |
| `METRO_TRANSIT_SERVICE_URL` | string | - | Metro transit GIS service URL | No |

**Example:**
```bash
SANTA_MONICA_PARCEL_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer
SANTA_MONICA_ZONING_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/Planning/Zoning/MapServer
```

### GIS Request Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GIS_REQUEST_TIMEOUT` | integer | `30` | GIS request timeout in seconds |
| `GIS_MAX_RETRIES` | integer | `3` | Maximum retry attempts for GIS requests |
| `GIS_CACHE_TTL` | integer | `3600` | GIS data cache TTL in seconds |

### Frontend GIS Services

| Variable | Type | Description |
|----------|------|-------------|
| `NEXT_PUBLIC_SANTA_MONICA_PARCEL_SERVICE_URL` | string | Parcel service for client-side mapping |
| `NEXT_PUBLIC_SANTA_MONICA_ZONING_SERVICE_URL` | string | Zoning service for client-side mapping |
| `NEXT_PUBLIC_SANTA_MONICA_OVERLAY_SERVICE_URL` | string | Overlay service for client-side mapping |
| `NEXT_PUBLIC_SANTA_MONICA_TRANSIT_SERVICE_URL` | string | Transit service for client-side mapping |

## Security Settings

### Authentication & Authorization

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_KEY_ENABLED` | boolean | `false` | Enable API key authentication |
| `API_KEY` | string | - | API key for authentication (if enabled) |

### Rate Limiting

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RATE_LIMIT_ENABLED` | boolean | `false` | Enable rate limiting |
| `RATE_LIMIT_PER_MINUTE` | integer | `60` | Maximum requests per minute |

### External Services

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GEOCODING_API_KEY` | string | - | Geocoding service API key (optional) |
| `GEOCODING_PROVIDER` | string | `google` | Geocoding provider (google/mapbox/etc.) |
| `OPENAI_API_KEY` | string | - | OpenAI API key for narrative generation (optional) |
| `NARRATIVE_MODEL` | string | `gpt-4` | LLM model for narrative generation |
| `ENABLE_NARRATIVE_GENERATION` | boolean | `false` | Enable AI narrative generation |

## Analysis Defaults

Configuration for default analysis parameters:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEFAULT_PARKING_SPACE_SIZE` | float | `320.0` | Default parking space size in sq ft |
| `DEFAULT_UNIT_SIZE` | float | `1000.0` | Default unit size in sq ft |
| `MIN_OPEN_SPACE_PER_UNIT` | float | `100.0` | Minimum open space per unit in sq ft |

## Environment-Specific Settings

### Development

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text
API_DEBUG_MODE=true
DATABASE_URL=postgresql://parcels:parcels_dev@localhost:5432/parcels_feasibility
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
API_DEBUG_MODE=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/parcels
BACKEND_CORS_ORIGINS=https://staging.parcels.smgov.net
RATE_LIMIT_ENABLED=true
```

### Production

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
LOG_FORMAT=json
API_DEBUG_MODE=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/parcels
BACKEND_CORS_ORIGINS=https://parcels.smgov.net
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=120
API_KEY_ENABLED=true
```

## Validation & Best Practices

### Required Variables Checklist

**Minimal Backend Setup:**
- [ ] `DATABASE_URL`
- [ ] `SANTA_MONICA_PARCEL_SERVICE_URL`
- [ ] `SANTA_MONICA_ZONING_SERVICE_URL`

**Minimal Frontend Setup:**
- [ ] `NEXT_PUBLIC_API_BASE_URL`

### Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use different credentials** for each environment
3. **Rotate API keys** regularly
4. **Use secrets management** for production (AWS Secrets Manager, etc.)
5. **Validate URLs** before use
6. **Enable rate limiting** in production
7. **Use HTTPS** for all production URLs

### Configuration Validation

The application validates configuration on startup. Check logs for:

```json
{
  "level": "INFO",
  "message": "Configuration loaded successfully",
  "environment": "production",
  "features_enabled": {
    "sb9": true,
    "sb35": true,
    "ab2011": true
  }
}
```

### Troubleshooting

**Common Issues:**

1. **Database connection failed**
   - Verify `DATABASE_URL` format
   - Check database is running
   - Verify credentials

2. **GIS service timeout**
   - Check `GIS_REQUEST_TIMEOUT` value
   - Verify GIS service URLs are accessible
   - Check network connectivity

3. **CORS errors in browser**
   - Verify `BACKEND_CORS_ORIGINS` includes frontend URL
   - Check frontend `NEXT_PUBLIC_API_BASE_URL` is correct

4. **Feature not working**
   - Check corresponding `ENABLE_*` flag is `true`
   - Verify both backend and frontend flags if applicable

## Example Configurations

### Local Development (Docker Compose)

```bash
# .env
DATABASE_URL=postgresql://parcels:parcels_dev@postgres:5432/parcels_feasibility
SANTA_MONICA_PARCEL_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer
SANTA_MONICA_ZONING_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/Planning/Zoning/MapServer
SANTA_MONICA_OVERLAY_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/Planning/Overlays/MapServer
SANTA_MONICA_TRANSIT_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/Transportation/Transit/MapServer
ENABLE_AB2011=true
ENABLE_SB35=true
ENABLE_SB9=true
ENABLE_DENSITY_BONUS=true
ENABLE_AB2097=true
LOG_LEVEL=DEBUG
```

```bash
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_V1_PREFIX=/api/v1
NEXT_PUBLIC_DEBUG_MODE=true
```

### Production (Kubernetes)

Use ConfigMaps and Secrets:

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: parcel-engine-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  ENABLE_AB2011: "true"
  # ... other non-sensitive config

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: parcel-engine-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://..."
  API_KEY: "secret-key"
```

## Support

For configuration issues:
1. Check [docs/DEPLOYMENT.md](DEPLOYMENT.md)
2. Verify against `.env.example` and `frontend/.env.local.example`
3. Review application logs for validation errors
4. Contact: planning@santamonica.gov
