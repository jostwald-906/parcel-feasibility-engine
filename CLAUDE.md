# Parcel Feasibility Engine - AI Agent Context

## Project Overview

California housing development feasibility analysis platform for analyzing residential development opportunities under state housing laws (SB 9, SB 35, AB 2011, Density Bonus). This is a **monorepo** containing both the FastAPI backend (`/app`) and Next.js frontend (`/frontend`) in a single codebase.

**Purpose**: Help developers, planners, and policymakers understand what can be built on parcels in Santa Monica (and other California cities) under various state housing laws.

**GitHub**: https://github.com/jostwald-906/parcel-feasibility-engine

## Technology Stack

### Backend
- **Python 3.13** with FastAPI 0.109.0
- **Uvicorn** 0.27.0 (ASGI server)
- **Pydantic v2** (2.10.6) for data validation and settings
- **SQLModel** 0.0.14 for database ORM
- **GeoAlchemy2** 0.14.3 + Shapely 2.0.6 for spatial data
- **Testing**: pytest 7.4.4, pytest-cov 4.1.0
- **Code Quality**: black 24.1.1, ruff 0.1.14, mypy 1.8.0

### Frontend
- **Next.js 15.5.4** with App Router
- **TypeScript 5**
- **Turbopack** (enabled in dev and build)
- **React 19.1.0** + React DOM 19.1.0
- **Tailwind CSS v4** with @tailwindcss/postcss
- **React-Leaflet 5.0.0** + Leaflet 1.9.4 for maps
- **Axios 1.12.2** for API calls
- **Lucide React** 0.544.0 for icons
- **Testing**: Jest 29.7.0, Testing Library

### Deployment
- **Backend**: Railway (auto-deploy on push to main)
- **Frontend**: Vercel (manual deployment)
- **Docker**: Dockerfile available for containerized deployment
- **Error Monitoring**: Sentry for production error tracking

## Project Structure

```
/Users/Jordan_Ostwald/Parcel Feasibility Engine/
├── app/                          # FastAPI backend
│   ├── api/                      # API endpoints (routers)
│   ├── core/                     # Configuration, logging
│   ├── models/                   # Pydantic models
│   ├── rules/                    # Zoning + state law implementations
│   │   └── state_law/            # SB 9, SB 35, AB 2011, Density Bonus
│   ├── services/                 # Business logic, GIS clients
│   ├── utils/                    # Helper utilities
│   └── main.py                   # FastAPI app entry point
├── frontend/                     # Next.js frontend
│   ├── app/                      # Next.js App Router pages
│   ├── components/               # React components
│   ├── lib/                      # Client utilities, types, API client
│   ├── public/                   # Static assets
│   └── package.json
├── tests/                        # Backend pytest tests
├── data/                         # Data files, caches
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── railway.json                  # Railway deployment config
└── README.md                     # Project documentation
```

## Development Setup

### Prerequisites
- Python 3.13
- Node.js 18+
- pip and npm

### Backend Setup

```bash
# From project root: /Users/Jordan_Ostwald/Parcel Feasibility Engine/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (from within venv)
./venv/bin/uvicorn app.main:app --reload --port 8000

# Alternative (if venv activated):
uvicorn app.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server with Turbopack
npm run dev
```

Frontend runs at: http://localhost:3000

### Environment Variables

**Backend** (create `.env` in project root):
```
ENVIRONMENT=development
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./parcel_feasibility.db
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Feature flags
ENABLE_AB2011=true
ENABLE_SB35=true
ENABLE_DENSITY_BONUS=true
ENABLE_SB9=true
ENABLE_AB2097=true

# GIS Services (Santa Monica defaults in config.py)
SANTA_MONICA_PARCEL_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer
```

**Frontend** (create `.env.local` in frontend/):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Commands

### Backend

```bash
# Run backend server (from project root)
./venv/bin/uvicorn app.main:app --reload --port 8000

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_density_bonus.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Format code
black app/ tests/

# Lint
ruff app/ tests/

# Type check
mypy app/
```

### Frontend

```bash
# From frontend/ directory

# Run dev server
npm run dev

# Build for production
npm run build

# Run production build locally
npm start

# Lint
npm run lint

# Type check
npm run type-check

# Run tests
npm test

# Run tests in watch mode
npm test:watch

# Coverage
npm test:coverage
```

## Key Patterns and Conventions

### Backend Patterns

1. **Pydantic Models (v2)**
   - All models use Pydantic v2 BaseModel or SQLModel
   - Use Field(...) for required fields with descriptions
   - Use Optional[Type] for optional fields
   - Field validation with gt=0, ge=0, le=100, pattern=r'...'
   - Example: `app/models/parcel.py`

2. **API Structure**
   - Routers in `app/api/` with clear endpoint organization
   - Use tags for OpenAPI grouping
   - Prefix all routes with `/api/v1`
   - Return Pydantic models for consistent responses
   - Example: `app/api/analyze.py`

3. **Configuration**
   - Settings in `app/core/config.py` using pydantic-settings
   - Feature flags for all state laws
   - Environment-based configuration via .env
   - Access via `from app.core.config import settings`

4. **Logging**
   - Structured logging via `app/utils/logging.py`
   - Use `get_logger(__name__)` in each module
   - Include context in extra={} dict
   - Example: `logger.info("Message", extra={"apn": parcel.apn})`

5. **Testing**
   - Fixtures in `tests/conftest.py` (r1_parcel, r2_parcel, etc.)
   - Parametrized tests with @pytest.mark.parametrize
   - Clear test class organization (Test*, test_*)
   - Docstrings on all test functions

### Frontend Patterns

1. **Component Organization**
   - Use 'use client' directive for client components
   - TypeScript interfaces in `lib/types.ts`
   - Shared utilities in `lib/` directory
   - Tailwind CSS for all styling

2. **Form Inputs**
   - **IMPORTANT**: All text inputs MUST use `text-gray-900` className
   - This ensures text is visible (not white on white)
   - Example: `className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900"`

3. **TypeScript Types**
   - All API types mirror backend Pydantic models
   - Optional fields use `?` syntax
   - Snake_case from backend → camelCase in frontend where appropriate
   - Example: `lib/types.ts`

4. **GIS Data Conventions**
   - Field names are lowercase: `usetype`, `usedescription`, `usecode`
   - Use optional types (?) for fields that may not exist
   - Always include useType, useDescription alongside useCode
   - Example from ParcelForm: `use_type`, `use_description`, `use_code`

5. **Map Components**
   - Z-index for Leaflet overlays: `z-[1000]` to appear above map tiles
   - Use React-Leaflet hooks for map interactions
   - Dynamic imports for Leaflet (client-side only)
   - Example: `components/ParcelMap.tsx`

## Legal Framework (California Housing Laws)

### SB 9 (2021) - Gov. Code § 65852.21
- Urban lot splits: divide 1 lot into 2
- Duplex development: up to 2 units per lot
- Combined: up to 4 units total (2 lots × 2 units)
- **Exclusions**: Historic properties, rent-controlled units
- **Implementation**: `app/rules/state_law/sb9.py`

### SB 35 (2017) - Gov. Code § 65913.4
- Streamlined ministerial approval (no discretionary review)
- **Affordability**: 10% in high-performing cities, 50% elsewhere
- **Labor**: Prevailing wage (10+ units), skilled & trained (75+ units)
- **Site exclusions**: Historic, wetlands, very high fire, coastal high hazard
- **Implementation**: `app/rules/state_law/sb35.py`

### AB 2011 (2022) - Gov. Code § 65913.5
- 100% affordable housing on commercial/parking sites
- **Density minimums**: 30-80 units/acre by corridor tier
- **Height minimums**: 35-65 feet by corridor tier
- **Labor**: Prevailing wage + skilled & trained workforce
- **Exclusions**: Historic, protected housing, environmental constraints
- **Implementation**: `app/rules/state_law/ab2011.py`

### Density Bonus Law - Gov. Code § 65915
- **Density bonuses**: 20-80% based on affordability %
- **Concessions**: 1-4 based on affordability (height, parking, setbacks, FAR)
- **Waivers**: Unlimited (must prove standard prevents construction)
- **Parking caps**: § 65915(p) bedroom-based + income-based limits
- **AB 2097 integration**: Near-transit parking elimination (§ 65915.1)
- **Implementation**: `app/rules/state_law/density_bonus.py`

### AB 2097 (2022) - Gov. Code § 65915.1
- Eliminates parking minimums within ½ mile of major transit
- Applies to all housing laws (SB 35, AB 2011, Density Bonus)
- **Implementation**: Integrated into parking calculations

## Common Tasks

### Adding a New State Law

1. Create new file in `app/rules/state_law/`
2. Implement analysis function returning DevelopmentScenario
3. Add statute references in docstring
4. Add feature flag to `app/core/config.py`
5. Register in analysis router `app/api/analyze.py`
6. Write tests in `tests/test_<law_name>.py`
7. Update frontend types in `frontend/lib/types.ts`

### Adding a New Zoning Code

1. Update `frontend/lib/constants/zoning-codes.ts`
2. Add to appropriate category (residential, commercial, mixed-use)
3. Implement standards in `app/rules/base_zoning.py`
4. Add test fixtures if needed in `tests/conftest.py`

### Debugging GIS Integration

1. Check GIS service URLs in config.py
2. Test endpoints directly in browser
3. Verify field name mappings (lowercase: usetype, usedescription)
4. Use browser DevTools Network tab for API calls
5. Check CORS configuration in app/main.py

### Running Integration Tests

```bash
# Backend: Test specific law
pytest tests/test_density_bonus.py -v

# Backend: Test GIS integration (requires network)
pytest tests/test_gis_integration.py -v -s

# Frontend: Component tests
cd frontend && npm test
```

## Error Monitoring (Sentry)

### Overview

Production error monitoring is configured via Sentry with environment-based filtering. Only production errors are sent to Sentry; development, staging, and test errors are filtered out.

**Sentry Projects**:
- Backend: https://sentry.io/organizations/d3ai/issues/?project=4510146633072640
- Frontend: https://sentry.io/organizations/d3ai/issues/?project=4510151500496896

### Environment-Based Filtering

All Sentry configurations use `beforeSend` hooks to filter events based on environment:

**Backend** ([app/main.py:47](app/main.py#L47)):
```python
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
    before_send=lambda event, hint: event if settings.ENVIRONMENT == "production" else None,
)
```

**Frontend Client** ([frontend/instrumentation-client.ts:34-44](frontend/instrumentation-client.ts#L34-L44)):
```typescript
Sentry.init({
  beforeSend(event, hint) {
    const environment = process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV;
    if (environment !== 'production') {
      console.log('[Sentry Dev] Error captured locally (not sent):', event.exception?.values?.[0]?.type);
      return null;
    }
    return event;
  },
});
```

**Frontend Server** ([frontend/sentry.server.config.ts:26-32](frontend/sentry.server.config.ts#L26-L32)):
```typescript
Sentry.init({
  beforeSend(event, hint) {
    if (SENTRY_ENVIRONMENT !== 'production') {
      console.log('[Sentry Server Dev] Event captured locally (not sent)');
      return null;
    }
    return event;
  },
});
```

### Environment Strategy

| Environment | Backend Filter | Frontend Filter | Sent to Sentry? |
|-------------|---------------|-----------------|-----------------|
| Local dev   | `ENVIRONMENT=development` | `NEXT_PUBLIC_SENTRY_ENVIRONMENT=development` | ❌ No (logged locally) |
| GitHub Actions | `ENVIRONMENT=test` | `NEXT_PUBLIC_SENTRY_ENVIRONMENT=test` | ❌ No |
| Staging     | `ENVIRONMENT=staging` | `NEXT_PUBLIC_SENTRY_ENVIRONMENT=staging` | ❌ No |
| Production  | `ENVIRONMENT=production` | `NEXT_PUBLIC_SENTRY_ENVIRONMENT=production` | ✅ Yes |

### Local Development Configuration

**Backend** (`.env` in project root):
```bash
SENTRY_DSN=https://e2d8a4e6cf15c114a1de078a757fad6e@o4510146612101120.ingest.us.sentry.io/4510146633072640
SENTRY_ENABLED=true
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_ENVIRONMENT=development  # Filters out events
```

**Frontend** (`.env.local` in frontend/):
```bash
NEXT_PUBLIC_SENTRY_DSN=https://6afbe26ee5c14d5a0416ebb6a5658aa3@o4510146612101120.ingest.us.sentry.io/4510151500496896
SENTRY_ORG=d3ai
SENTRY_PROJECT=parcel-feasibility-frontend
NEXT_PUBLIC_SENTRY_ENVIRONMENT=development  # Filters out events
```

### Production Configuration

Set these environment variables once on deployment platforms:

**Railway (Backend)**:
- `ENVIRONMENT=production` (enables Sentry)
- `SENTRY_DSN` (same as development DSN)
- `SENTRY_ENABLED=true`
- `SENTRY_TRACES_SAMPLE_RATE=0.1`

**Vercel (Frontend)**:
- `NEXT_PUBLIC_SENTRY_ENVIRONMENT=production` (enables Sentry)
- `NEXT_PUBLIC_SENTRY_DSN` (same as development DSN)
- `SENTRY_ORG=d3ai`
- `SENTRY_PROJECT=parcel-feasibility-frontend`

### Testing Sentry

**Backend Test Endpoint**:
```bash
curl http://localhost:8000/sentry-debug
# Or visit http://localhost:8000/sentry-debug in browser
```

**Frontend Test Page**:
```
http://localhost:3000/sentry-test-simple
```

In development, errors are logged to console but NOT sent to Sentry. In production, errors are automatically sent to Sentry.

### File Structure

```
# Backend
app/main.py                     # Sentry initialization with production filter

# Frontend
frontend/instrumentation.ts            # Instrumentation hook loader
frontend/instrumentation-client.ts     # Client-side Sentry config
frontend/sentry.server.config.ts       # Server-side Sentry config
frontend/sentry.edge.config.ts         # Edge runtime Sentry config
frontend/app/sentry-test-simple/       # Test page
```

### Key Configuration Details

1. **Session Replay**: 10% sample rate, 100% on errors, with privacy masking
2. **Performance Monitoring**: 10% traces sample rate
3. **No Manual Intervention**: Environment variables set once, persist across deployments
4. **Privacy**: PII sending disabled (`send_default_pii=False`)
5. **Stack Traces**: Attached to all errors (`attach_stacktrace=True`)

### Common Issues

**Issue**: Rate limiting (429 errors) during testing
**Solution**: Wait 30 minutes for rate limit to reset. Use production filter to prevent excessive test events.

**Issue**: Events not appearing in Sentry dashboard
**Solution**: Check `ENVIRONMENT` or `NEXT_PUBLIC_SENTRY_ENVIRONMENT` is set to `production`

**Issue**: Frontend Sentry not initializing
**Solution**: Verify `instrumentation-client.ts` exists (not `sentry.client.config.ts`). Next.js requires specific instrumentation filenames.

### Reference Documentation

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive deployment workflow and [SENTRY_SETUP_COMPLETE.md](SENTRY_SETUP_COMPLETE.md) for setup summary.

## Deployment

### Backend (Railway)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy (auto-deploys from git push to main)
railway up

# View logs
railway logs
```

Configuration in `railway.json`. Uses `Procfile` for start command.

### Frontend (Vercel)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from frontend/ directory
cd frontend && vercel

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_URL=<your-railway-backend-url>
```

Configuration in `frontend/vercel.json`.

### Docker

```bash
# Build image
docker build -t parcel-feasibility-engine .

# Run container
docker run -p 8000:8000 parcel-feasibility-engine
```

## Critical Implementation Details

### Notes in Analysis Results

- Keep notes concise (single-line items when possible)
- Always include statute references (e.g., "Gov. Code § 65915(f)")
- Document concessions/waivers in detail
- Explain parking calculations clearly

### Data Validation

- Use Pydantic Field validators with clear descriptions
- Validate ranges: gt=0 (greater than), ge=0 (greater or equal)
- Pattern validation for codes: `pattern=r'^[1-3]$'`
- Optional fields must use Optional[Type]

### Error Handling

- FastAPI raises HTTPException with clear detail messages
- Frontend displays errors in AlertCircle components
- Log all errors with structured context
- Return 404 for not found, 500 for server errors

## Common Issues and Solutions

### Issue: White text in form inputs
**Solution**: Add `text-gray-900` class to all input elements

### Issue: Map overlays hidden behind tiles
**Solution**: Use `z-[1000]` or higher z-index for custom overlays

### Issue: GIS field not found
**Solution**: Check field name is lowercase (usetype not UseType)

### Issue: CORS errors in development
**Solution**: Verify BACKEND_CORS_ORIGINS includes http://localhost:3000

### Issue: Tests failing with fixture not found
**Solution**: Check conftest.py is in tests/ directory and pytest discovers it

## Related Documentation

- [Backend CLAUDE.md](app/CLAUDE.md) - FastAPI patterns, Pydantic models
- [Frontend CLAUDE.md](frontend/CLAUDE.md) - Next.js patterns, TypeScript
- [Rules CLAUDE.md](app/rules/CLAUDE.md) - Housing law implementation
- [Components CLAUDE.md](frontend/components/CLAUDE.md) - React patterns
- [Tests CLAUDE.md](tests/CLAUDE.md) - Testing patterns

## Maintaining CLAUDE.md Files

**IMPORTANT**: These CLAUDE.md files are living documentation that should be updated whenever significant changes are made to the codebase.

### When to Update CLAUDE.md

Update the relevant CLAUDE.md file(s) when:

1. **Adding new features or patterns**
   - New state law implementation
   - New UI component pattern
   - New API endpoint structure
   - New testing pattern

2. **Fixing critical bugs or issues**
   - Solutions to common problems
   - Important gotchas discovered
   - Critical implementation details

3. **Changing development workflows**
   - New build processes
   - Updated deployment procedures
   - New testing approaches
   - Changed environment variables

4. **Updating dependencies**
   - Major version upgrades
   - Breaking changes
   - New package integrations

### Pre-Commit Checklist for Major Changes

Before committing significant features or changes:

```bash
# 1. Review what changed
git status
git diff

# 2. Identify which CLAUDE.md files should be updated:
#    - Root CLAUDE.md: Project-level changes, new dependencies, deployment
#    - app/CLAUDE.md: Backend patterns, new models, API changes
#    - app/rules/CLAUDE.md: New laws, statute references, legal patterns
#    - frontend/CLAUDE.md: Frontend patterns, new libraries, type changes
#    - frontend/components/CLAUDE.md: New components, UI patterns
#    - tests/CLAUDE.md: New testing patterns, fixtures, approaches

# 3. Update relevant CLAUDE.md file(s) with:
#    - What was added/changed
#    - Why it was done this way
#    - Example code snippets
#    - Common pitfalls to avoid
#    - Commands or patterns to follow

# 4. Commit changes including CLAUDE.md updates
git add <changed-files> <updated-CLAUDE.md-files>
git commit -m "feat: Add feature X

- Implementation details
- Updated CLAUDE.md with new patterns"
```

### What to Document

**Good additions to CLAUDE.md:**
- ✅ New patterns that should be followed consistently
- ✅ Solutions to tricky problems
- ✅ Critical implementation details
- ✅ Common mistakes and how to avoid them
- ✅ New commands or workflows
- ✅ Integration patterns between systems

**Don't clutter CLAUDE.md with:**
- ❌ Temporary workarounds (unless they're critical)
- ❌ Obvious or self-explanatory code
- ❌ Implementation details better suited for code comments
- ❌ Extremely specific edge cases

### Example: Recent Updates

Here's what should have been added for recent work:

**frontend/components/CLAUDE.md** (text-gray-900 pattern):
```markdown
### Form Input Text Color (CRITICAL)

All text inputs MUST use `text-gray-900` to ensure text is visible:

// ❌ BAD - text will be invisible (white on white)
<input className="w-full px-3 py-2 border border-gray-300 rounded-lg" />

// ✅ GOOD - text is visible (dark gray)
<input className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900" />

This applies to ALL inputs: text, number, select, textarea.
```

**app/rules/CLAUDE.md** (density bonus notes):
```markdown
### Notes Formatting

Keep notes concise - single line when possible:

// ❌ BAD - creates multiple bullet points
notes.append("")
notes.append("Note: Waivers are tracked separately.")
notes.append("Waivers are unlimited but require...")

// ✅ GOOD - single concise bullet
notes.append("Note: Waivers (§ 65915(e)) are tracked separately. Waivers are unlimited but require demonstrating that a standard physically precludes construction.")
```

### Automated Reminder

Consider adding this git hook (`.git/hooks/pre-commit`):

```bash
#!/bin/bash
echo ""
echo "📝 Reminder: If this is a significant change, update relevant CLAUDE.md files!"
echo ""
echo "   CLAUDE.md files to consider:"
echo "   - Root: /CLAUDE.md"
echo "   - Backend: /app/CLAUDE.md"
echo "   - Rules: /app/rules/CLAUDE.md"
echo "   - Frontend: /frontend/CLAUDE.md"
echo "   - Components: /frontend/components/CLAUDE.md"
echo "   - Tests: /tests/CLAUDE.md"
echo ""
```

## Getting Help

- API Documentation: http://localhost:8000/docs
- API Health Check: http://localhost:8000/health
- GitHub Issues: https://github.com/jostwald-906/parcel-feasibility-engine/issues
- California Law References:
  - SB 9: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=65852.21
  - Density Bonus: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=65915
