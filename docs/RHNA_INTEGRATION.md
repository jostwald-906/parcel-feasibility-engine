# RHNA Data Integration

## Overview

The Parcel Feasibility Engine now integrates official California HCD (Housing and Community Development) RHNA (Regional Housing Needs Allocation) data to determine SB35 affordability requirements.

**What replaced:** Hardcoded city lists in `app/rules/state_law/sb35.py` that assumed certain cities required 10% vs 50% affordable housing.

**What's new:** Official HCD SB35 Determination Dataset with actual RHNA performance data for all 539 California jurisdictions.

## Key Features

### 1. Official HCD Data

- **Data Source:** California HCD SB35 Determination Dataset
- **URL:** https://data.ca.gov/dataset/sb-35-data
- **Coverage:** All 539 California jurisdictions (cities and counties)
- **Updated:** Automatically downloadable (biweekly HCD updates)

### 2. Accurate Affordability Determinations

The service provides three possible determinations:

- **0% (Exempt):** Jurisdiction met RHNA targets - SB35 does not apply
- **10% Affordable:** Jurisdiction met >50% of above-moderate RHNA
- **50% Affordable:** Jurisdiction did NOT meet >50% of above-moderate RHNA

### 3. Real Data Examples

From current HCD data (as of October 2025):

```
Santa Monica:
  - Affordability: 0% (EXEMPT)
  - Above-moderate RHNA progress: 328.4%
  - Status: Exempt from SB35 streamlining

San Francisco:
  - Affordability: 50%
  - Above-moderate RHNA progress: 118.4%
  - Status: Subject to SB35 with 50% affordable requirement

Los Angeles:
  - Affordability: 50%
  - Above-moderate RHNA progress: 362.6%
  - Status: Subject to SB35 with 50% affordable requirement
  - Note: Despite high above-moderate progress, did not meet lower-income targets

Adelanto:
  - Affordability: 10%
  - Above-moderate RHNA progress: 11.3%
  - Status: Subject to SB35 with 10% affordable requirement
```

## Architecture

### Components

1. **RHNADataService** (`app/services/rhna_service.py`)
   - Loads CSV data on initialization
   - Provides jurisdiction lookup with fallback logic
   - Caches data for performance

2. **HCD Data File** (`data/sb35_determinations.csv`)
   - 539 jurisdictions
   - Official HCD determinations (10% vs 50%)
   - Above-moderate RHNA progress percentages
   - Planning period and APR metadata

3. **Update Script** (`scripts/update_rhna_data.py`)
   - Downloads latest data from data.ca.gov
   - Validates CSV structure
   - Creates backup before updating
   - Can be scheduled via cron

4. **SB35 Integration** (`app/rules/state_law/sb35.py`)
   - `get_affordability_requirement()` uses RHNA service
   - `_check_rhna_status()` uses RHNA service
   - No more hardcoded city lists

## Usage

### In Code

```python
from app.services.rhna_service import rhna_service

# Get affordability requirement for a jurisdiction
result = rhna_service.get_sb35_affordability(
    jurisdiction="Los Angeles",
    county="Los Angeles"  # Optional, helps with disambiguation
)

print(f"Affordability: {result['percentage']}%")
print(f"Exempt: {result['is_exempt']}")
print(f"Above-moderate progress: {result['above_moderate_progress']}%")
print(f"Income levels: {result['income_levels']}")
print(f"Data source: {result['source']}")

# Notes include detailed requirements and disclaimers
for note in result['notes']:
    print(note)
```

### With Parcel Analysis

```python
from app.rules.state_law.sb35 import get_affordability_requirement
from app.models.parcel import ParcelBase

parcel = ParcelBase(
    apn="123-456-789",
    address="123 Main St",
    city="Santa Monica",
    county="Los Angeles",
    state="CA",
    zip_code="90401",
    lot_size_sqft=10000,
    zoning_code="R3"
)

affordability = get_affordability_requirement(parcel)
# Returns official HCD determination for Santa Monica
```

### Summary Statistics

```python
from app.services.rhna_service import rhna_service

stats = rhna_service.get_summary_stats()

print(f"Total jurisdictions: {stats['total_jurisdictions']}")
print(f"Exempt (met targets): {stats['exempt_count']}")
print(f"Require 10%: {stats['requires_10_pct_count']}")
print(f"Require 50%: {stats['requires_50_pct_count']}")
```

Current stats:
- Total jurisdictions: 539
- Exempt: 38 (7%)
- Require 10%: 263 (49%)
- Require 50%: 238 (44%)

### List Jurisdictions

```python
# List all jurisdictions
jurisdictions = rhna_service.list_jurisdictions()

# Filter by county
la_jurisdictions = rhna_service.list_jurisdictions(county="Los Angeles")

for juris in la_jurisdictions:
    print(f"{juris['jurisdiction']}: {juris['affordability_pct']}%")
```

## Data Updates

### Manual Update

```bash
# Download latest HCD data
python scripts/update_rhna_data.py
```

### Automated Update (Cron)

Add to crontab for weekly updates (Sundays at 2am):

```bash
0 2 * * 0 cd /path/to/project && /path/to/venv/bin/python scripts/update_rhna_data.py >> logs/rhna_update.log 2>&1
```

### What the Script Does

1. Checks for updates via CKAN API
2. Downloads latest CSV from data.ca.gov
3. Validates data structure and content
4. Backs up existing data before replacing
5. Saves update metadata
6. Reloads service with new data

## Fallback Behavior

If no HCD data is available for a jurisdiction:

1. **Known high-performers** (SF, San Jose, Sacramento) → 10% (estimated)
2. **All others** → 50% (conservative default)
3. **Warning notes** indicate the determination is estimated
4. **Disclaimer** reminds user to verify with planning department

Example fallback response:
```python
{
    'percentage': 50.0,
    'income_levels': ['Very Low Income', 'Lower Income'],
    'source': 'Estimated (no official HCD data)',
    'notes': [
        'WARNING: Estimated 50% (conservative default - no HCD data available)',
        'CRITICAL: No official RHNA data found for this jurisdiction',
        'YOU MUST verify actual RHNA performance with local planning department',
        ...
    ]
}
```

## Data File Format

The CSV file (`data/sb35_determinations.csv`) contains:

### Key Columns

- `County`: County name
- `Jurisdiction`: City/county name
- `10%`: "Yes" if 10% affordability applies
- `50%`: "Yes" if 50% affordability applies
- `Exempt`: "Yes" if jurisdiction is exempt (met RHNA targets)
- `Above MOD % Complete`: Percentage of above-moderate RHNA achieved
- `Planning Period Progress`: Overall RHNA progress percentage
- `Last APR`: Date of last Annual Progress Report

### Example Rows

```csv
County,Jurisdiction,10%,50%,Exempt,Above MOD % Complete,Last APR,...
LOS ANGELES,SANTA MONICA,No,No,Yes,328.4%,2021,...
SAN FRANCISCO,SAN FRANCISCO,No,Yes,No,118.4%,2021,...
SAN BERNARDINO,ADELANTO,Yes,No,No,11.3%,2021,...
```

## Testing

Comprehensive test suite in `tests/test_rhna_service.py`:

```bash
# Run RHNA service tests
pytest tests/test_rhna_service.py -v

# Results: 21 tests, all passing
# - Service initialization
# - Data loading and validation
# - Jurisdiction lookups (exact and partial match)
# - Case-insensitive matching
# - Exempt/10%/50% determinations
# - Summary statistics
# - Integration with SB35 code
# - Edge cases and error handling
```

## Important Notes

### 1. Always Verify with Planning Department

The service includes disclaimers in all responses:

> "IMPORTANT: Always verify current RHNA status with local planning department"
> "HCD determination data may not reflect most recent Annual Progress Reports"

### 2. Data Staleness

- HCD updates data biweekly
- Some jurisdictions submit APRs late
- Current cycle data may not include most recent permits
- Recommendation: Update data weekly via cron

### 3. Exempt Jurisdictions

If a jurisdiction is exempt (met RHNA targets):
- `percentage` = 0.0
- `is_exempt` = True
- SB35 streamlining does NOT apply
- Project must go through standard discretionary review

### 4. Above-Moderate Paradox

Some jurisdictions (like Los Angeles) show very high above-moderate progress (362%) but still require 50% affordable. This occurs when:
- They exceeded above-moderate RHNA targets
- BUT failed to meet lower-income (Very Low + Low) RHNA targets
- SB35 requires meeting BOTH thresholds to qualify for exemption

### 5. Bay Area Special Rule

The service does NOT currently implement the Bay Area 20% requirement (vs 10% statewide). This should be added in future updates.

## API Response Format

```python
{
    'percentage': 50.0,  # 0.0, 10.0, or 50.0
    'income_levels': ['Very Low Income', 'Lower Income'],
    'source': 'HCD SB35 Determination Dataset',
    'last_updated': '2021',  # Date of last APR
    'notes': [
        'AFFORDABILITY REQUIREMENT: 50% affordable units required',
        'Income targeting: Mix of Very Low Income (≤50% AMI) and Lower Income (≤80% AMI)',
        'Above-moderate RHNA progress: 118.4%',
        'Jurisdiction did NOT meet >50% of above-moderate RHNA target',
        'Income mix requirements:',
        '  - If jurisdiction met ≤10% of above-moderate: 50% Very Low + 50% Lower',
        '  - If >10% but ≤50%: Mix varies by RHNA category shortfall',
        'Planning period: 100.0%',
        'Last Annual Progress Report (APR): 2021',
        '',
        'Data source: California HCD SB35 Determination Dataset',
        'URL: https://data.ca.gov/dataset/sb-35-data',
        'Data loaded: 2025-10-06',
        '',
        'IMPORTANT: Always verify current RHNA status with local planning department',
        'HCD determination data may not reflect most recent Annual Progress Reports'
    ],
    'is_exempt': False,
    'above_moderate_progress': 118.4,
    'jurisdiction': 'SAN FRANCISCO',
    'county': 'SAN FRANCISCO'
}
```

## Future Enhancements

### Short-term
1. Implement Bay Area 20% requirement exception
2. Add API endpoint for jurisdiction lookup
3. Create admin dashboard showing RHNA data version
4. Add email alerts for data update failures

### Medium-term
1. Download and integrate APR Table A2 data (building permits by income level)
2. Calculate real-time RHNA progress percentages
3. Historical tracking of jurisdiction status changes
4. Compare multiple RHNA cycles (5th, 6th, etc.)

### Long-term
1. Regional COG API integration (SANDAG, SCAG, ABAG)
2. Real-time RHNA progress updates
3. Predictive modeling of future RHNA status
4. Integration with HCD SMAP Dashboard

## Resources

### HCD Official Resources
- **Statutory Determinations:** https://www.hcd.ca.gov/planning-and-community-development/statutory-determinations
- **SMAP Dashboard:** https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process-dashboard
- **RHNA Portal:** https://www.hcd.ca.gov/planning-and-community-development/regional-housing-needs-allocation

### Data Sources
- **California Open Data:** https://data.ca.gov/
- **RHNA Progress Report:** https://data.ca.gov/dataset/rhna-progress-report
- **SB35 Determination Data:** https://data.ca.gov/dataset/sb-35-data

### Legal References
- **Gov. Code § 65913.4:** SB35 Streamlined Ministerial Approval
- **Health & Safety Code § 50093:** Income Limit Definitions

### Related Documentation
- `docs/RHNA_API_RESEARCH.md` - Research on RHNA data sources
- `app/services/rhna_service.py` - Service implementation
- `scripts/update_rhna_data.py` - Automated update script
- `tests/test_rhna_service.py` - Test suite

## Support

For questions about RHNA data:
- HCD APR Team: APR@hcd.ca.gov
- HCD Connect Support: HCDConnectHPD@hcd.ca.gov

For questions about this integration:
- See implementation in `app/services/rhna_service.py`
- Run tests: `pytest tests/test_rhna_service.py -v`
- Review research: `docs/RHNA_API_RESEARCH.md`

---

**Last Updated:** October 6, 2025
**Data Version:** HCD SB35 Determination Dataset (539 jurisdictions)
**Implementation:** Complete - Replaces hardcoded SB35 logic
