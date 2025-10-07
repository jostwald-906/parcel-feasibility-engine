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
│   ├── timeline_estimator.py # Entitlement timeline estimation
│   ├── comprehensive_analysis.py # Comprehensive scenario analysis
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

## Entitlement Timeline Estimation (app/services/timeline_estimator.py)

### Overview

The timeline estimator provides approval timeline estimates for different development pathways, helping developers understand "How long will this take?" - the #1 question for financing decisions.

**Key Features**:
- Ministerial vs. discretionary pathway detection
- Statutory deadline compliance (SB 9: 60 days, SB 35: 90 days, ADU: 60 days)
- Step-by-step timeline breakdown with required submittals
- Color-coded visualization (Green: ministerial/fast, Yellow: administrative/medium, Red: discretionary/slow)

### Timeline Models

```python
from app.services.timeline_estimator import (
    estimate_timeline,
    EntitlementTimeline,
    TimelineStep,
)

class TimelineStep(BaseModel):
    step_name: str                    # e.g., "Application Submittal"
    days_min: int                     # Minimum days for this step
    days_max: int                     # Maximum days for this step
    description: str                  # What happens in this step
    required_submittals: List[str]    # Required documents

class EntitlementTimeline(BaseModel):
    pathway_type: str                 # "Ministerial", "Administrative", "Discretionary"
    total_days_min: int               # Total minimum days
    total_days_max: int               # Total maximum days
    steps: List[TimelineStep]         # Timeline steps in order
    statutory_deadline: Optional[int] # Statutory deadline (if applicable)
    notes: List[str]                  # Important notes
```

### Usage

```python
from app.services.timeline_estimator import estimate_timeline

# Estimate timeline for a scenario
timeline = estimate_timeline(
    scenario_name="SB 9 Lot Split",
    legal_basis="SB 9 (Gov. Code § 65852.21)",
    max_units=4,
    parcel=parcel  # Optional
)

# Check pathway type
if timeline.pathway_type == "Ministerial":
    print(f"Fast-track approval: {timeline.total_days_min}-{timeline.total_days_max} days")
    if timeline.statutory_deadline:
        print(f"Statutory deadline: {timeline.statutory_deadline} days")

# Iterate through steps
for step in timeline.steps:
    print(f"{step.step_name}: {step.days_min}-{step.days_max} days")
    print(f"Description: {step.description}")
    if step.required_submittals:
        print(f"Required: {', '.join(step.required_submittals)}")
```

### Pathway Detection

```python
from app.services.timeline_estimator import detect_pathway_type

# Automatically detect pathway from legal basis
pathway = detect_pathway_type("SB 9 (Gov. Code § 65852.21)")
# Returns: "Ministerial"

pathway = detect_pathway_type("Conditional Use Permit")
# Returns: "Discretionary"

# Ministerial keywords: sb 9, sb 35, ab 2011, adu, jadu, ministerial, by-right
# Administrative keywords: administrative, arp, director approval
# Default: Discretionary
```

### Timeline Ranges by Pathway

**Ministerial** (State-mandated by-right approval):
- SB 9: 36-60 days (statutory deadline: 60 days)
- SB 35: 52-81 days (statutory deadline: 90 days)
- ADU/JADU: 36-60 days (statutory deadline: 60 days)
- AB 2011: 87-156 days (no statutory deadline, but ministerial)
- No public hearing required
- Must meet objective standards

**Administrative** (Staff-level approval):
- 109-193 days (~3.5-6.5 months)
- No public hearing required
- Subject to 15-day appeal period
- May require design review

**Discretionary** (Public hearing required):
- Small projects (<10 units): 268-516 days (~9-17 months)
- Large projects (≥10 units): 298-606 days (~10-20 months)
- Requires CEQA review
- Planning Commission and/or City Council hearing
- Community input and design revisions

### Integration with Comprehensive Analysis

Timeline estimation is automatically integrated into `comprehensive_analysis.py`:

```python
from app.services.comprehensive_analysis import generate_comprehensive_scenarios

# Generate scenarios with timeline estimates
results = generate_comprehensive_scenarios(
    parcel=parcel,
    include_sb35=True,
    include_ab2011=True,
    include_density_bonus=True,
    include_timeline=True  # Enable timeline estimation (default)
)

# Each scenario will have estimated_timeline field
for scenario in results['scenarios']:
    if scenario.estimated_timeline:
        timeline = scenario.estimated_timeline
        print(f"{scenario.scenario_name}: {timeline['total_days_min']}-{timeline['total_days_max']} days")
        print(f"Pathway: {timeline['pathway_type']}")
```

### Adding Timeline to DevelopmentScenario

```python
from app.models.analysis import DevelopmentScenario

# Timeline is optional on DevelopmentScenario
scenario = DevelopmentScenario(
    scenario_name="SB 9 Lot Split",
    legal_basis="SB 9 (Gov. Code § 65852.21)",
    max_units=4,
    # ... other fields
    estimated_timeline={
        "pathway_type": "Ministerial",
        "total_days_min": 36,
        "total_days_max": 60,
        "statutory_deadline": 60,
        # ... timeline details
    }
)
```

### Timeline Notes Structure

Each timeline includes notes explaining key requirements:

```python
# SB 9 timeline notes
[
    "SB 9 requires ministerial approval within 60 days (Gov. Code § 65852.21(k))",
    "No public hearing or CEQA review required",
    "Must meet all objective design standards",
    "Timeline may be extended if application is incomplete"
]

# Discretionary timeline notes
[
    "Discretionary approval requires public hearing(s)",
    "CEQA environmental review typically required",
    "Timeline includes Planning Commission and may include City Council",
    "Large or controversial projects may take longer",
    "Community input and design revisions can extend timeline",
    "Estimated total: 9-17 months"
]
```

### Testing

See `tests/test_timeline_estimator.py` for comprehensive test coverage:

```python
def test_sb9_timeline_within_60_days():
    """SB 9 timeline should be within statutory 60-day deadline."""
    timeline = estimate_timeline(
        scenario_name="SB 9 Lot Split",
        legal_basis="SB 9 (Gov. Code § 65852.21)",
        max_units=4,
    )

    assert timeline.total_days_min <= 60
    assert timeline.total_days_max <= 60
    assert timeline.statutory_deadline == 60
    assert timeline.pathway_type == "Ministerial"
```

## AMI Calculator (app/services/ami_calculator.py)

### Overview

The AMI (Area Median Income) Calculator provides accurate affordable rent and sales price calculations based on official HCD/HUD income limits data. This is critical for statutory compliance with density bonus law, AB 2011, and other affordable housing programs.

**Key Features**:
- HCD 2025 income limits for all California counties
- Automatic affordable rent calculation (30% of income standard)
- Affordable sales price calculation (mortgage affordability)
- Pydantic models for type safety
- API endpoints for frontend integration

**Data Source**: HCD 2025 State Income Limits (Effective April 23, 2025)
- URL: https://www.hcd.ca.gov/grants-and-funding/income-limits
- Updated: Annually (April)
- Coverage: All California counties, household sizes 1-8, AMI percentages 30%-120%

### Income Categories

```python
# Standard AMI percentages used in California housing programs
AMI_CATEGORIES = {
    30: "Extremely Low Income (ELI)",    # 30% AMI
    50: "Very Low Income (VLI)",         # 50% AMI
    60: "Low Income",                     # 60% AMI
    80: "Low Income",                     # 80% AMI
    100: "Median Income",                 # 100% AMI
    120: "Moderate Income",               # 120% AMI
}
```

### Usage

```python
from app.services.ami_calculator import get_ami_calculator, AMICalculator

# Get singleton instance
calculator = get_ami_calculator()

# Income limit lookup
income_limit = calculator.get_income_limit(
    county="Los Angeles",
    ami_pct=50.0,  # 50% AMI (Very Low Income)
    household_size=2
)
# Returns: 42640.0 (annual income limit in dollars)

# Affordable rent calculation
rent = calculator.calculate_max_rent(
    county="Los Angeles",
    ami_pct=50.0,
    bedrooms=2,
    utility_allowance=150.0  # Monthly utility allowance
)
# Returns AffordableRent model:
# {
#     "county": "Los Angeles",
#     "ami_pct": 50.0,
#     "bedrooms": 2,
#     "household_size": 4,  # Auto-calculated from bedrooms
#     "income_limit": 53300.0,
#     "max_rent_with_utilities": 1332.5,
#     "max_rent_no_utilities": 1182.5,
#     "utility_allowance": 150.0
# }

# Affordable sales price calculation
price = calculator.calculate_max_sales_price(
    county="Los Angeles",
    ami_pct=80.0,
    household_size=4,
    interest_rate_pct=6.5,       # Default assumptions
    loan_term_years=30,
    down_payment_pct=10.0,
    property_tax_rate_pct=1.25,  # CA typical
    insurance_rate_pct=0.5,
    hoa_monthly=0.0
)
# Returns AffordableSalesPrice model:
# {
#     "county": "Los Angeles",
#     "ami_pct": 80.0,
#     "household_size": 4,
#     "income_limit": 85280.0,
#     "max_sales_price": 298000.0,
#     "assumptions": { ... }
# }
```

### Pydantic Models

```python
from app.services.ami_calculator import (
    AMILookup,
    AffordableRent,
    AffordableSalesPrice
)

class AMILookup(BaseModel):
    """Income limit lookup result."""
    county: str
    ami_pct: float
    household_size: int
    income_limit: float

class AffordableRent(BaseModel):
    """Affordable rent calculation result."""
    county: str
    ami_pct: float
    bedrooms: int
    household_size: int  # Auto-calculated: bedrooms + 2 (HUD standard)
    income_limit: float
    max_rent_with_utilities: float
    max_rent_no_utilities: float
    utility_allowance: float = 150.0

class AffordableSalesPrice(BaseModel):
    """Affordable sales price calculation result."""
    county: str
    ami_pct: float
    household_size: int
    income_limit: float
    max_sales_price: float
    assumptions: Dict[str, float]  # Mortgage parameters
```

### API Endpoints

```python
# GET /api/v1/ami/income-limit
# Get income limit for county/AMI%/household size
GET /api/v1/ami/income-limit?county=Los Angeles&ami_pct=50&household_size=2

# GET /api/v1/ami/rent
# Calculate maximum affordable rent
GET /api/v1/ami/rent?county=Los Angeles&ami_pct=50&bedrooms=2&utility_allowance=150

# GET /api/v1/ami/sales-price
# Calculate maximum affordable sales price
GET /api/v1/ami/sales-price?county=Los Angeles&ami_pct=80&household_size=4

# GET /api/v1/ami/counties
# Get list of available counties
GET /api/v1/ami/counties

# GET /api/v1/ami/percentages
# Get list of available AMI percentages with labels
GET /api/v1/ami/percentages
```

### Integration with Density Bonus Law

```python
from app.services.ami_calculator import get_ami_calculator

# Example: Calculate affordable rent for density bonus units
calculator = get_ami_calculator()

# For 50% AMI (Very Low Income) density bonus units
rent_50_ami = calculator.calculate_max_rent(
    county=parcel.county,
    ami_pct=50.0,
    bedrooms=2  # 2-bedroom unit
)

# Add to scenario notes
notes.append(
    f"Affordable units (50% AMI): Max rent ${rent_50_ami.max_rent_no_utilities:.0f}/month"
)
notes.append(
    f"Income limit: ${rent_50_ami.income_limit:,.0f}/year "
    f"({rent_50_ami.household_size}-person household)"
)
```

### Integration with AB 2011

```python
from app.services.ami_calculator import get_ami_calculator

# Example: Calculate affordable rent for AB 2011 corridor housing
calculator = get_ami_calculator()

# For 80% AMI (Low Income) mixed-income track
rent_80_ami = calculator.calculate_max_rent(
    county=parcel.county,
    ami_pct=80.0,
    bedrooms=1  # 1-bedroom unit
)

notes.append(
    f"Affordable units (80% AMI): Max rent ${rent_80_ami.max_rent_no_utilities:.0f}/month"
)
```

### Household Size Calculation

```python
# HUD occupancy standard: bedrooms + 1.5 persons, rounded up
def calculate_household_size(bedrooms: int) -> int:
    """
    Calculate household size from bedrooms.

    Formula: bedrooms + 1.5, rounded up
    - Studio (0BR) → 2 persons
    - 1BR → 3 persons
    - 2BR → 4 persons
    - 3BR → 5 persons
    - 4BR → 6 persons

    Capped at 8 persons (maximum in HCD data).
    """
    household_size = bedrooms + 2  # bedrooms + 1.5, rounded up
    return min(household_size, 8)  # Cap at 8
```

### Formulas

**Affordable Rent** (30% of income standard):
```python
# Annual income limit × 30% ÷ 12 months = Max monthly housing cost
max_rent_with_utilities = (income_limit * 0.30) / 12

# Subtract utility allowance for contract rent
max_rent_no_utilities = max_rent_with_utilities - utility_allowance
```

**Affordable Sales Price** (PITI affordability):
```python
# PITI = Principal + Interest + Taxes + Insurance
# Max monthly housing cost = (income_limit * 0.30) / 12
# Monthly PITI + HOA ≤ Max monthly housing cost
# Solve for maximum sales price

# Loan amount = Sales Price × (1 - down_payment_pct/100)
# Monthly mortgage payment = Loan × mortgage_factor
# Monthly taxes = Sales Price × (property_tax_rate/12)
# Monthly insurance = Sales Price × (insurance_rate/12)

# Combined factor approach:
combined_factor = (
    loan_to_value * mortgage_factor +
    (property_tax_rate + insurance_rate) / 12
)

max_sales_price = (max_monthly_housing - hoa_monthly) / combined_factor
```

### Data Import

```bash
# Import HCD income limits data (run annually when HCD updates)
python scripts/import_ami_limits.py

# Output: /data/ami_limits_2025.csv
# Format: county, household_size, ami_pct, income_limit
```

### Testing

```python
# tests/test_ami_calculator.py

def test_los_angeles_50_ami_2_person():
    """Test Los Angeles 50% AMI for 2-person household matches HCD data."""
    calculator = AMICalculator()
    income_limit = calculator.get_income_limit("Los Angeles", 50, 2)

    # From HCD 2025: LA County 50% AMI, 2-person = $42,640
    assert income_limit == 42640

def test_rent_calculation_uses_30_percent_standard():
    """Test that rent calculation uses 30% of income standard."""
    calculator = AMICalculator()
    rent = calculator.calculate_max_rent("Los Angeles", 50, 2)

    # Annual rent should be 30% of income
    annual_rent = rent.max_rent_with_utilities * 12
    expected_annual_rent = rent.income_limit * 0.30

    assert annual_rent == pytest.approx(expected_annual_rent, abs=0.5)
```

### Available Counties (2025)

```python
# Coverage: 16 major California counties
COUNTIES = [
    "Alameda",
    "Fresno",
    "Kern",
    "Los Angeles",
    "Orange",
    "Riverside",
    "Sacramento",
    "San Bernardino",
    "San Diego",
    "San Francisco",
    "San Joaquin",
    "San Mateo",
    "Santa Barbara",
    "Santa Clara",
    "Stanislaus",
    "Ventura",
]

# To add more counties: Update scripts/import_ami_limits.py
```

### References

- Gov. Code § 50053: Very low income definition
- Gov. Code § 50052.5: Lower income definition
- HCD Income Limits: https://www.hcd.ca.gov/grants-and-funding/income-limits
- HUD Fair Market Rent methodology

### Coverage

Test coverage: 98% (37 tests, all passing)

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
