# Backend (FastAPI) - AI Agent Context

## Overview

FastAPI backend for the Parcel Feasibility Engine. Provides REST API for analyzing California housing development feasibility under state laws (SB 9, SB 35, AB 2011, Density Bonus).

**Technology**: Python 3.13, FastAPI 0.109.0, Pydantic v2, SQLModel, Uvicorn

## Directory Structure

```
app/
├── api/                    # API routers/endpoints
│   ├── analyze.py          # Main analysis endpoint
│   ├── rules.py            # State law information endpoints
│   ├── metadata.py         # Metadata endpoints
│   └── autocomplete.py     # Parcel autocomplete
├── core/                   # Core configuration
│   ├── config.py           # Settings (Pydantic Settings)
│   └── __init__.py
├── models/                 # Pydantic data models
│   ├── parcel.py           # Parcel data model
│   └── analysis.py         # Analysis request/response models
├── rules/                  # Zoning and state law logic
│   ├── base_zoning.py      # Base zoning calculations
│   ├── tiered_standards.py # FAR/height tier resolution
│   ├── overlays.py         # Overlay zone handling
│   ├── dcp_scenarios.py    # Downtown Community Plan
│   ├── bergamot_scenarios.py # Bergamot Area Plan
│   ├── proposed_validation.py # Proposed project validation
│   └── state_law/          # California housing laws
│       ├── sb9.py          # SB 9 lot splits/duplexes
│       ├── sb35.py         # SB 35 streamlining
│       ├── ab2011.py       # AB 2011 affordable corridors
│       └── density_bonus.py # Density Bonus Law
├── services/               # Business logic services
│   ├── arcgis_client.py    # ArcGIS REST API client
│   ├── rent_control_api.py # Santa Monica rent control
│   └── __init__.py
├── utils/                  # Utilities
│   ├── logging.py          # Structured logging setup
│   └── __init__.py
└── main.py                 # FastAPI app entry point
```

## Running the Backend

```bash
# From project root: /Users/Jordan_Ostwald/Parcel Feasibility Engine/

# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run with uvicorn (development mode with auto-reload)
./venv/bin/uvicorn app.main:app --reload --port 8000

# Or if venv is activated:
uvicorn app.main:app --reload --port 8000

# Production mode (no reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access points:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Configuration (app/core/config.py)

Uses **pydantic-settings** for environment-based configuration.

```python
from app.core.config import settings

# Access settings
settings.PROJECT_NAME
settings.ENABLE_SB9
settings.SANTA_MONICA_PARCEL_SERVICE_URL

# Check feature flags
settings.is_feature_enabled("ab2011")  # Returns bool
```

### Key Settings

```python
class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Santa Monica Parcel Feasibility Engine"
    VERSION: str = "1.0.0"

    # Feature Flags
    ENABLE_AB2011: bool = True
    ENABLE_SB35: bool = True
    ENABLE_DENSITY_BONUS: bool = True
    ENABLE_SB9: bool = True
    ENABLE_AB2097: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./parcel_feasibility.db"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # GIS Services
    SANTA_MONICA_PARCEL_SERVICE_URL: str = "https://gis.smgov.net/..."
    GIS_REQUEST_TIMEOUT: int = 30
    GIS_MAX_RETRIES: int = 3
```

### Environment Variables (.env)

```
ENVIRONMENT=development
LOG_LEVEL=INFO
LOG_FORMAT=json

DATABASE_URL=sqlite:///./parcel_feasibility.db
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

ENABLE_AB2011=true
ENABLE_SB35=true
ENABLE_DENSITY_BONUS=true
ENABLE_SB9=true
ENABLE_AB2097=true

SANTA_MONICA_PARCEL_SERVICE_URL=https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer
```

## Pydantic Models (v2)

### Model Patterns

All models use **Pydantic v2** syntax:

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ParcelBase(BaseModel):
    """Base parcel model."""

    # Required fields with descriptions
    apn: str = Field(..., description="Assessor's Parcel Number")
    lot_size_sqft: float = Field(..., gt=0, description="Lot size in square feet")

    # Optional fields
    year_built: Optional[int] = Field(None, description="Year built")

    # Validation constraints
    lot_coverage_pct: float = Field(..., ge=0, le=100, description="Lot coverage %")

    # Pattern validation
    development_tier: Optional[str] = Field(None, pattern=r'^[1-3]$')

    # Lists
    overlay_codes: Optional[List[str]] = Field(None, description="Overlay codes")
```

### Key Models

**ParcelBase** (`app/models/parcel.py`):
- Core parcel attributes (APN, address, lot size, zoning)
- Environmental flags (historic, coastal, flood, wetlands)
- Tier and overlay information
- AB 2011 specific fields (street_row_width)
- Protected housing flags (rent control, deed-restricted)

**DevelopmentScenario** (`app/models/analysis.py`):
- Scenario name and legal basis
- Max units, building sqft, height, stories
- Parking requirements
- Affordable units required
- Setbacks dict
- Lot coverage %
- Notes list (statute references, explanations)
- Concessions/waivers applied (for Density Bonus)

**AnalysisRequest** (`app/models/analysis.py`):
```python
class AnalysisRequest(BaseModel):
    parcel: Parcel
    proposed_project: Optional[ProposedProject] = None
    include_sb9: bool = True
    include_sb35: bool = True
    include_ab2011: bool = False
    include_density_bonus: bool = True
    target_affordability_pct: float = 15.0
```

**AnalysisResponse** (`app/models/analysis.py`):
```python
class AnalysisResponse(BaseModel):
    parcel_apn: str
    analysis_date: str
    base_scenario: DevelopmentScenario
    alternative_scenarios: List[DevelopmentScenario]
    recommended_scenario: str
    recommendation_reason: str
    applicable_laws: List[str]
    potential_incentives: List[str]
    warnings: Optional[List[str]] = None
    rent_control: Optional[RentControlData] = None
```

## API Endpoints (app/api/)

### Main Analysis Endpoint

```python
# app/api/analyze.py

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_parcel(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze a parcel for development feasibility.

    Returns base zoning scenario + alternative scenarios under:
    - SB 9 (if enabled and eligible)
    - SB 35 (if enabled and eligible)
    - AB 2011 (if enabled and eligible)
    - Density Bonus (if enabled)
    """
    # 1. Analyze base zoning
    base_scenario = analyze_base_zoning(request.parcel)

    # 2. Generate alternative scenarios
    scenarios = []

    if request.include_sb9 and settings.ENABLE_SB9:
        sb9_scenario = analyze_sb9(request.parcel)
        if sb9_scenario:
            scenarios.append(sb9_scenario)

    # ... SB 35, AB 2011, Density Bonus

    # 3. Select recommended scenario
    recommended = select_best_scenario(base_scenario, scenarios)

    # 4. Build response
    return AnalysisResponse(...)
```

### Endpoint Organization

- **analyze.py**: Main analysis logic (`POST /api/v1/analyze`)
- **rules.py**: State law information (`GET /api/v1/rules/{law_name}`)
- **metadata.py**: Metadata endpoints (`GET /api/v1/metadata`)
- **autocomplete.py**: APN autocomplete (`GET /autocomplete/parcels`)

### Router Registration

```python
# app/main.py

app.include_router(analyze.router, prefix=settings.API_V1_STR, tags=["Analysis"])
app.include_router(rules.router, prefix=settings.API_V1_STR, tags=["Rules"])
app.include_router(metadata.router, prefix=settings.API_V1_STR, tags=["Metadata"])
app.include_router(autocomplete.router)
```

## State Law Implementation (app/rules/state_law/)

### Pattern for Implementing a State Law

Each law is a separate module with analysis function:

```python
# app/rules/state_law/example_law.py

"""
Example State Law (Government Code Section 12345).

Description of the law and its provisions.

References:
- Gov. Code § 12345(a): Provision description
- Gov. Code § 12345(b): Another provision
"""

from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from typing import Optional

def analyze_example_law(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Analyze parcel under Example State Law.

    Args:
        parcel: Parcel to analyze

    Returns:
        DevelopmentScenario if eligible, None otherwise
    """
    # 1. Check eligibility
    if not is_eligible(parcel):
        return None

    # 2. Calculate standards
    max_units = calculate_units(parcel)
    max_height_ft = calculate_height(parcel)
    # ... other calculations

    # 3. Build notes with statute references
    notes = [
        f"Example State Law applied (Gov. Code § 12345)",
        f"Eligibility: {eligibility_reason}",
        f"Max units: {max_units} (§ 12345(a))",
        # ... more notes
    ]

    # 4. Return scenario
    return DevelopmentScenario(
        scenario_name="Example State Law",
        legal_basis="Gov. Code § 12345",
        max_units=max_units,
        max_building_sqft=calculate_sqft(parcel, max_units),
        max_height_ft=max_height_ft,
        max_stories=int(max_height_ft / 11),
        parking_spaces_required=calculate_parking(parcel, max_units),
        affordable_units_required=calculate_affordable(max_units),
        setbacks=calculate_setbacks(parcel),
        lot_coverage_pct=calculate_coverage(parcel),
        notes=notes
    )
```

### Statute References in Code

**ALWAYS** include statute references in:
1. **Module docstrings**: Full law overview with section citations
2. **Function docstrings**: Specific sections applicable
3. **Notes field**: Explain calculations with references
4. **Comments**: For complex logic tied to specific code sections

Example from `density_bonus.py`:

```python
"""
State Density Bonus Law (Government Code Section 65915).

References:
- Gov. Code § 65915(f): Density bonus percentages by income level
- Gov. Code § 65915(d)(1): Concessions and incentives (1-3)
- Gov. Code § 65915(p): Parking ratios by bedroom count
- AB 2097 (Gov. Code § 65915.1): Transit-oriented parking elimination
"""

notes = [
    f"State Density Bonus Law applied (Gov. Code § 65915)",
    f"Density bonus (§ 65915(f)): {bonus_pct}% = {bonus_units} additional units",
    f"Concessions granted (§ 65915(d)): {num_concessions}",
    f"Parking (§ 65915(p)): {parking_per_unit:.2f} spaces/unit",
]
```

## Logging (app/utils/logging.py)

### Setup

```python
from app.utils.logging import setup_logging, get_logger

# Initialize logging (done in main.py)
setup_logging()

# Get logger for module
logger = get_logger(__name__)
```

### Usage

```python
# Basic logging
logger.info("Processing parcel analysis")

# Structured logging with context
logger.info(
    "Analysis completed",
    extra={
        "apn": parcel.apn,
        "scenarios": len(scenarios),
        "duration_ms": duration * 1000
    }
)

# Error logging
try:
    result = process_parcel(parcel)
except Exception as e:
    logger.error(
        f"Analysis failed: {e}",
        extra={"apn": parcel.apn},
        exc_info=True
    )
    raise
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages (e.g., feature disabled)
- **ERROR**: Error messages with context
- **CRITICAL**: Critical failures

Configure via environment: `LOG_LEVEL=DEBUG`

## Testing Patterns

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_density_bonus.py -v

# Specific test class
pytest tests/test_density_bonus.py::TestDensityBonusPercentages -v

# Specific test
pytest tests/test_density_bonus.py::TestDensityBonusPercentages::test_bonus_percentages -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Coverage report opens in htmlcov/index.html
```

### Test Structure

```python
# tests/test_example.py

"""Tests for Example State Law."""
import pytest
from app.rules.state_law.example_law import analyze_example_law

class TestEligibility:
    """Tests for eligibility checks."""

    def test_eligible_parcel_returns_scenario(self, r1_parcel):
        """Test that eligible parcel returns scenario."""
        scenario = analyze_example_law(r1_parcel)
        assert scenario is not None
        assert scenario.max_units > 0

    def test_ineligible_parcel_returns_none(self, r1_parcel):
        """Test that ineligible parcel returns None."""
        r1_parcel.is_historic_property = True
        scenario = analyze_example_law(r1_parcel)
        assert scenario is None

    @pytest.mark.parametrize("lot_size,expected_units", [
        (5000, 2),
        (10000, 4),
        (15000, 6),
    ])
    def test_unit_calculation(self, r1_parcel, lot_size, expected_units):
        """Test unit calculation for various lot sizes."""
        r1_parcel.lot_size_sqft = lot_size
        scenario = analyze_example_law(r1_parcel)
        assert scenario.max_units == expected_units
```

### Fixtures

Use fixtures from `tests/conftest.py`:

```python
def test_density_bonus_on_r2(r2_parcel):
    """Test using r2_parcel fixture."""
    scenario = apply_density_bonus(base_scenario, r2_parcel)
    assert scenario.max_units > base_scenario.max_units
```

Available fixtures:
- `r1_parcel`: Single-family residential
- `r2_parcel`: Low-density multi-family
- `dcp_parcel`: Downtown Community Plan
- `coastal_parcel`: Coastal zone
- `historic_parcel`: Historic district
- `transit_adjacent_parcel`: Near transit
- `commercial_parcel`: Commercial zoning
- `small_r1_parcel`: Below minimums
- `large_r4_parcel`: High-density multi-family

## Common Patterns

### Calculating Parking

```python
def calculate_parking(parcel: ParcelBase, units: int) -> int:
    """Calculate parking spaces required."""

    # AB 2097 near-transit elimination
    if parcel.near_transit:
        return 0

    # Base ratio (from zoning)
    base_ratio = get_base_parking_ratio(parcel.zoning_code)

    # Apply bedroom-based caps (Density Bonus § 65915(p))
    if parcel.avg_bedrooms_per_unit:
        if parcel.avg_bedrooms_per_unit <= 1:
            bedroom_cap = 1.0
        elif parcel.avg_bedrooms_per_unit <= 3:
            bedroom_cap = 2.0
        else:
            bedroom_cap = 2.5
        ratio = min(base_ratio, bedroom_cap)
    else:
        ratio = base_ratio

    return int(units * ratio)
```

### Building Notes List

```python
notes = [
    f"State Law Applied (Gov. Code § 12345)",
    f"Eligibility: {reason}",
    f"Max units: {max_units}",
]

# Add conditional notes
if has_concessions:
    notes.append(f"Concessions: {num_concessions}")
    for i, concession in enumerate(concessions_applied, 1):
        notes.append(f"  {i}. {concession}")

# Add warnings
if has_warning:
    notes.append(f"⚠️ Warning: {warning_message}")

# Add references
notes.append("Reference: Full text at leginfo.legislature.ca.gov")
```

### Error Handling

```python
from fastapi import HTTPException

# Not found
if parcel is None:
    raise HTTPException(
        status_code=404,
        detail=f"Parcel with APN {apn} not found"
    )

# Validation error
if request.lot_size_sqft <= 0:
    raise HTTPException(
        status_code=422,
        detail="Lot size must be greater than zero"
    )

# Server error
try:
    result = complex_calculation()
except Exception as e:
    logger.error(f"Calculation failed: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Internal server error during analysis"
    )
```

## CORS Configuration

```python
# app/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r'https://frontend-[a-z0-9]+-jordan-ostwalds-projects\.vercel\.app',
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For development, ensure `.env` includes:
```
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## Deployment

### Railway

Configuration in `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Start command also in `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables (Railway)

Set in Railway dashboard:
- `ENVIRONMENT=production`
- `BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app"]`
- Feature flags (ENABLE_SB9, etc.)

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Health check with feature status."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "features": {
            "ab2011": settings.ENABLE_AB2011,
            "sb35": settings.ENABLE_SB35,
            # ...
        }
    }
```

## Key Implementation Details

### Optional Fields Pattern

```python
# Always use Optional[Type] for fields that may not exist
year_built: Optional[int] = Field(None, description="Year built")

# Check before using
if parcel.year_built and parcel.year_built < 1980:
    # Historic analysis
    pass

# Use getattr with default for dynamic access
near_transit = getattr(parcel, "near_transit", False)
```

### Concise Notes

Keep analysis notes concise and single-line when possible:

```python
# GOOD: Concise, clear
notes = [
    "SB 9 lot split: 1 lot → 2 lots (Gov. Code § 65852.21)",
    "Max units per lot: 2 (duplex allowed)",
    "Total potential: 4 units (2 lots × 2 units)"
]

# AVOID: Too verbose
notes = [
    "This parcel is eligible for an SB 9 lot split under Government Code Section 65852.21, which allows for the division of a single residential parcel into two separate parcels..."
]
```

## Related Documentation

- [Root CLAUDE.md](../CLAUDE.md) - Overall project context
- [Rules CLAUDE.md](rules/CLAUDE.md) - State law implementation details
- [Frontend CLAUDE.md](../frontend/CLAUDE.md) - Frontend integration
