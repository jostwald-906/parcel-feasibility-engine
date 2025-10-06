# California HCD RHNA Data API Research
## Integration Planning for SB35 Affordability Determination

**Research Date:** October 6, 2025
**Purpose:** Identify APIs and data sources for determining SB35 affordability requirements based on jurisdiction RHNA performance
**Current Status:** Code uses hardcoded assumptions (see `app/rules/state_law/sb35.py` lines 184, 244, 481-519)

---

## Executive Summary

California HCD does **not** provide a public REST API for RHNA data. However, multiple data sources are available for integration:

1. **California Open Data Portal** - Biweekly updated CSV datasets with RHNA progress by jurisdiction
2. **HCD SMAP Dashboard** - Daily updated SB35 determination data (10% vs 50% affordability)
3. **Regional COG Data Portals** - ABAG, SCAG, SANDAG, SACOG with regional-specific data
4. **CKAN API** - Limited programmatic access to metadata and resource URLs on data.ca.gov

**Recommended Approach:** Download and cache CSV datasets, with periodic refresh strategy.

---

## Background: SB35 Affordability Requirements

Per Gov. Code § 65913.4(a)(5), affordability requirements depend on jurisdiction RHNA performance:

- **10% affordable** (Lower Income ≤80% AMI): If jurisdiction met >50% of **above-moderate** RHNA
- **50% affordable** (mix of Very Low ≤50% AMI and Lower Income): If jurisdiction met ≤50% of above-moderate RHNA

**Bay Area Exception:** Projects in ABAG counties require 20% affordable (for households <120% AMI) instead of 10%.

HCD publishes official SB35 determinations showing which jurisdictions are subject to streamlining and their required affordability levels.

---

## Data Sources

### 1. California HCD - RHNA Progress Report Dataset

**Primary Source:** https://data.ca.gov/dataset/rhna-progress-report

#### Available Data Files

| File | URL | Coverage |
|------|-----|----------|
| 5th Cycle RHNA Progress | https://data.ca.gov/dataset/ff082e96-72f7-4443-9747-8b8dadc15671/resource/cff0bc49-dd85-43a1-b1d5-1cfa7cf1ae22/download/rhna_progress_5.csv | 2013-2021 |
| 6th Cycle RHNA Progress | https://data.ca.gov/dataset/ff082e96-72f7-4443-9747-8b8dadc15671/resource/1e80a9cf-724c-432d-8374-e9708a6a92dc/download/rhna_progress_6.csv | 2021-2029 |
| Data Dictionary (5th) | Available as DOCX | Field definitions |
| Data Dictionary (6th) | Available as DOCX | Field definitions |

#### Dataset Details

- **Update Frequency:** Biweekly
- **Data Format:** CSV
- **Geographic Coverage:** All California jurisdictions (cities and counties)
- **Granularity:** City & County level
- **Temporal Coverage:** 2013 - Current
- **Income Categories:** Very Low, Low, Moderate, Above Moderate
- **Data Source:** Self-reported by jurisdictions via Annual Progress Reports (APR)

#### Data Structure

Shows sum of units reported on APR Tables:
- Table A and A3 (2013-2017)
- Table A2 (2018 onwards) - "Annual Building Activity Report Summary - New Construction"

Each row represents:
- Jurisdiction name
- Year
- Income level (Very Low, Low, Moderate, Above Moderate)
- RHNA allocation (target)
- Building permits issued (actual)
- Progress percentage

#### Limitations

- **No API:** Must download CSV files directly
- **Self-reported:** HCD does not independently verify data
- **Database Transition:** HCD is transitioning to new database system (late Q1 2025)
- **Not Real-time:** Data lags behind actual permit issuance

---

### 2. HCD SB35 Streamlining (SMAP) Determination Dataset

**Primary Source:** https://data.ca.gov/dataset/sb-35-data
**Dashboard:** https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process-dashboard

#### Available Data Files

| File | Description |
|------|-------------|
| SB 35 Determination Data | CSV with jurisdiction affordability requirements |
| 5th Cycle Raw Data | Historical RHNA data |
| 6th Cycle Raw Data | Current cycle RHNA data |
| Assigned 5th/6th Cycle RHNA | Allocation targets by jurisdiction |
| Data Dictionary | DOCX with field definitions |

#### Dataset Details

- **Update Frequency:** Annual (Dashboard: Daily starting 6/30/2025)
- **Data Format:** CSV
- **Coverage:** Statewide
- **Temporal Coverage:** 2013-2021 (historical data)
- **Direct Affordability Mapping:** Shows which jurisdictions require 10% vs 50% affordable

#### SMAP Dashboard Features

Dashboard provides:
1. **Determination Summary:** List of jurisdictions by SMAP status
   - Not subject to SMAP
   - Subject to SMAP with 10% affordability
   - Subject to SMAP with 50% affordability
2. **Infographic:** Visual summary of jurisdiction status
3. **Determination Methodology:** PDF explaining calculation

#### Key Value

This is the **most direct source** for SB35 affordability determination. HCD has already calculated whether each jurisdiction meets the 50% threshold for above-moderate RHNA.

#### Limitations

- **Annual updates:** Determination data updated once per year
- **No API:** Dashboard data must be scraped or CSV downloaded
- **Historical only:** Dataset temporal coverage ends 2021 (may be updated)

---

### 3. HCD Annual Progress Report (APR) Dataset

**Primary Source:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year

#### Available Data Tables

| Table | Description |
|-------|-------------|
| Table A2 | Annual Building Activity - New Construction (permits, completions) |
| Table A | Housing Development Applications |
| Table A3 | (Legacy) Merged with A2 in 2018+ |
| Table C | Sites Inventory |
| Table D | Financial Resources |
| Table E | Commercial Development |
| Table F | Assisted Housing |
| Table F2 | Assisted Housing Units at Risk |
| Table G | Extremely Low Income Housing |
| Table H | Housing Element Implementation |
| Table I | Land Inventory |
| Table K | General Information |

#### Dataset Details

- **Update Frequency:** Annual (submissions throughout fiscal year, finalized June 30)
- **Data Format:** CSV (each table separate)
- **Coverage:** Statewide by jurisdiction
- **Data Range:** 2018-2022 (available now, ongoing)
- **Contact:** APR@hcd.ca.gov

#### Key Tables for RHNA Progress

**Table A2** - Most important for SB35 determination:
- Building permits issued by income level
- Comparison to RHNA allocation
- Tracks progress toward Very Low, Low, Moderate, Above Moderate targets

#### Calculating RHNA Progress from APR Data

```
RHNA Progress % = (Cumulative Permits Issued / RHNA Allocation) × 100

Above Moderate Progress = (Above Moderate Permits / Above Moderate RHNA) × 100

SB35 Affordability = 10% if Above Moderate Progress > 50%
                     50% if Above Moderate Progress ≤ 50%
```

#### Limitations

- **Complex structure:** Multiple related tables
- **Requires calculation:** Must compute percentages from raw permit data
- **Annual lag:** Previous year data not complete until June 30
- **No API:** CSV download only

---

### 4. California Open Data Portal CKAN API

**API Base URL:** https://data.ca.gov/api/3/action/

#### Available Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| package_show | Get dataset metadata | https://data.ca.gov/api/3/action/package_show?id=rhna-progress-report |
| package_search | Search datasets | https://data.ca.gov/api/3/action/package_search?q=rhna |
| resource_show | Get resource info | https://data.ca.gov/api/3/action/resource_show?id={resource_id} |
| package_list | List all datasets | https://data.ca.gov/api/3/action/package_list |

#### Example API Call

```bash
# Get RHNA Progress Report metadata
curl "https://data.ca.gov/api/3/action/package_show?id=rhna-progress-report"

# Response includes:
# - Dataset description
# - Resource URLs (CSV download links)
# - Last updated timestamp
# - Data dictionaries
```

#### API Response Structure

```json
{
  "success": true,
  "result": {
    "id": "ff082e96-72f7-4443-9747-8b8dadc15671",
    "name": "rhna-progress-report",
    "title": "RHNA Progress Report",
    "resources": [
      {
        "id": "cff0bc49-dd85-43a1-b1d5-1cfa7cf1ae22",
        "name": "5th Cycle RHNA Progress Report",
        "url": "https://data.ca.gov/.../rhna_progress_5.csv",
        "format": "CSV",
        "last_modified": "2024-..."
      }
    ]
  }
}
```

#### Limitations

- **Metadata only:** API provides URLs, not actual data
- **No data query:** Cannot filter or query CSV data via API
- **1000 record limit:** Pagination required for large result sets
- **Not guaranteed:** HCD discourages building systems that rely on API always being available
- **CKAN documentation:** https://docs.ckan.org/en/2.9/api/

---

### 5. Regional COG Data Sources

#### ABAG (Association of Bay Area Governments)

**Coverage:** 9 Bay Area counties (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma)

| Resource | URL | Details |
|----------|-----|---------|
| Housing & Land Use Viewer | https://housing.abag.ca.gov/ | Interactive map (SSL cert issue with API) |
| Data Tools | https://abag.ca.gov/tools-resources/data-tools | Open data initiative with API access |
| Housing Needs Data Packets | https://abag.ca.gov/technical-assistance/abag-housing-needs-data-packets | PDF and Excel downloads by jurisdiction |
| RHNA Maps | https://abag.ca.gov/rhna-maps | Visual RHNA allocation maps |

**6th Cycle Allocation:** 441,176 housing units (2023-2031)

**Data Access:**
- Excel files with underlying data tables
- HESS Tool account for jurisdictions (Housing Element Site Selection)
- Open data API (documentation not readily available)

**Bay Area Special Rule:** 20% affordable requirement (vs 10% statewide) for above-moderate shortfall

#### SCAG (Southern California Association of Governments)

**Coverage:** 6 counties, 197 jurisdictions (Imperial, Los Angeles, Orange, Riverside, San Bernardino, Ventura)

| Resource | URL | Details |
|----------|-----|---------|
| Regional Data Platform | https://hub.scag.ca.gov/ | Consolidated parcel and housing data |
| GIS Open Data Portal | https://gisdata-scag.opendata.arcgis.com/ | ArcGIS REST services |
| RHNA Information | https://scag.ca.gov/rhna | Policy and allocation information |
| Local Data Exchange (LDX) | via hub.scag.ca.gov | Jurisdictions can edit data via browser |
| HELPR Tool | https://maps.scag.ca.gov/helpr/ | Housing Element Parcel Tool |

**6th Cycle Allocation:** 1,341,827 housing units (Oct 2021 - Oct 2029)

**Data Features:**
- 5.1 million parcels with zoning, land use, density data
- SoCal Atlas web application
- ArcGIS REST API services (need to search portal for specific RHNA layers)
- Complete reports and raw format available

**Data Access:**
- Free to all users
- ArcGIS REST API endpoints available (must search portal)
- Download options: Shapefile, GeoJSON, CSV
- Contact: scaggisadmin@scag.ca.gov

#### SANDAG (San Diego Association of Governments)

**Coverage:** San Diego County

| Resource | URL | Details |
|----------|-----|---------|
| RHNA Progress Dashboard | https://opendata.sandag.org/stories/s/RHNA-Progress-Dashboard-2023/8utc-zau5/ | Interactive dashboard |
| 5th & 6th Cycle Dataset | https://opendata.sandag.org/dataset/5th-and-6th-Cycle-RHNA-Progress-by-Jurisdiction-20/as8h-a2a4 | Direct data access |
| Open Data Portal | https://opendata.sandag.org/ | All housing datasets |
| Data Surfer API | https://datasurfer.sandag.org/api | Census, population, housing API |

**Data Features:**
- RHNA Progress by jurisdiction
- Excel and PDF export
- Socrata-based open data platform
- API access via Socrata SODA API

**Data Access:**
- Socrata API endpoints (dataset-specific)
- CSV, JSON, XML export options
- Real-time or near real-time updates

#### SACOG (Sacramento Area Council of Governments)

**Coverage:** Sacramento region (6 counties)

| Resource | URL | Details |
|----------|-----|---------|
| Open Data Portal | https://data.sacog.org/ | Public platform for data |
| Housing Data & Resources | https://www.sacog.org/planning/land-use/housing/housing-data-resources | RHNA information |
| ArcGIS Portal | https://sb743-sacog.opendata.arcgis.com/ | GIS data services |

**Data Access:**
- Open data platform (emphasis on information-based decision making)
- ArcGIS REST services
- Download formats: CSV, KML, GeoJSON, Shapefile

#### AMBAG (Association of Monterey Bay Area Governments)

**Coverage:** Monterey and Santa Cruz counties

| Resource | URL | Details |
|----------|-----|---------|
| Regional Housing Planning | https://www.ambag.org/plans/regional-housing-planning | RHNA plan documents |
| RHNA Element Cycles | https://www.ambag.org/plans/regional-housing-needs-allocation-element-cycles | Historical data |

**6th Cycle:** Final plan adopted October 12, 2022 (2023-2031)

**Data Access:**
- PDF reports with allocation tables
- Excel files available
- No apparent API or open data portal

---

## RHNA Progress Calculation Methodology

### HCD Official Methodology

**Source:** SB 35 Determination Methodology (https://www.hcd.ca.gov/community-development/accountability-enforcement/docs/sb35determinationmethodology10012020.pdf)

#### Key Concepts

1. **Pro-rata Share:** Expected percentage of RHNA met at each point in the cycle
   - First half of cycle: 50% minimum expected
   - End of cycle (8 years): 100% required

2. **Income Categories:**
   - **Very Low Income:** ≤50% AMI
   - **Lower Income:** >50% and ≤80% AMI
   - **Moderate Income:** >80% and ≤120% AMI
   - **Above Moderate:** >120% AMI

3. **SB35 Thresholds:**
   - **Above Moderate Shortfall:** Triggers 10% affordability requirement (20% in Bay Area)
   - **Lower Income Shortfall:** Triggers 50% affordability requirement

#### Calculation Formula

```python
# For each jurisdiction and income category:

permits_issued = sum(building_permits_by_year)
rhna_allocation = total_allocation_for_cycle
years_elapsed = current_year - cycle_start_year
cycle_length = 8  # or 5 for older cycles

# Pro-rata expected progress
expected_progress_pct = (years_elapsed / cycle_length) * 100

# Actual progress
actual_progress_pct = (permits_issued / rhna_allocation) * 100

# Determine streamlining requirement
if actual_progress_pct < expected_progress_pct:
    subject_to_streamlining = True

# Determine affordability requirement
above_mod_progress_pct = (above_mod_permits / above_mod_rhna) * 100

if above_mod_progress_pct > 50:
    affordability_requirement = 0.10  # 10% affordable
elif above_mod_progress_pct <= 50:
    affordability_requirement = 0.50  # 50% affordable
```

#### Data Sources for Calculation

1. **RHNA Allocation:** From "Assigned 5th/6th Cycle RHNA" dataset
2. **Building Permits:** From APR Table A2 or RHNA Progress Report
3. **Cycle Dates:**
   - 5th Cycle: 2013-2021
   - 6th Cycle: 2021-2029
4. **Income Mix (for 50% requirement):**
   - If ≤10% of above-moderate met: 50% at Very Low + 50% at Lower Income
   - If >10% but ≤50%: Mix varies by RHNA category shortfall

---

## Integration Approach Recommendations

### Option 1: Download & Cache (RECOMMENDED)

**Approach:** Periodically download HCD CSV files and cache locally

**Pros:**
- Simple implementation
- No API rate limits
- Fast lookups
- Works offline
- Official HCD determinations available

**Cons:**
- Data staleness (biweekly updates)
- Requires storage
- Manual refresh process

**Implementation:**
```python
import pandas as pd
from datetime import datetime, timedelta
import requests

class RHNADataService:
    """Service for managing RHNA progress data."""

    RHNA_5TH_CYCLE_URL = "https://data.ca.gov/dataset/ff082e96-72f7-4443-9747-8b8dadc15671/resource/cff0bc49-dd85-43a1-b1d5-1cfa7cf1ae22/download/rhna_progress_5.csv"
    RHNA_6TH_CYCLE_URL = "https://data.ca.gov/dataset/ff082e96-72f7-4443-9747-8b8dadc15671/resource/1e80a9cf-724c-432d-8374-e9708a6a92dc/download/rhna_progress_6.csv"
    SB35_DETERMINATION_URL = "https://data.ca.gov/dataset/sb-35-data"  # Navigate to get actual CSV URL

    CACHE_DURATION = timedelta(days=7)  # Refresh weekly

    def __init__(self, cache_dir="./data/rhna_cache"):
        self.cache_dir = cache_dir
        self.data = None
        self.last_updated = None

    def get_affordability_requirement(self, jurisdiction: str, year: int = None) -> dict:
        """
        Get SB35 affordability requirement for a jurisdiction.

        Args:
            jurisdiction: City or county name
            year: Year to check (defaults to current year)

        Returns:
            {
                'percentage': float,  # 10.0 or 50.0
                'reason': str,  # Explanation
                'above_moderate_progress': float,  # Percentage
                'last_updated': datetime
            }
        """
        # Ensure data is fresh
        self._ensure_fresh_data()

        # Look up jurisdiction
        juris_data = self._lookup_jurisdiction(jurisdiction, year)

        if not juris_data:
            return {
                'percentage': 50.0,  # Conservative default
                'reason': f'No data found for {jurisdiction}. Defaulting to 50% (conservative)',
                'above_moderate_progress': None,
                'last_updated': self.last_updated
            }

        # Calculate above moderate progress
        above_mod_permits = juris_data['above_moderate_permits']
        above_mod_rhna = juris_data['above_moderate_rhna']

        if above_mod_rhna == 0:
            progress_pct = 0.0
        else:
            progress_pct = (above_mod_permits / above_mod_rhna) * 100

        # Determine requirement
        if progress_pct > 50:
            pct = 10.0
            reason = f'{jurisdiction} met {progress_pct:.1f}% of above-moderate RHNA (>50%)'
        else:
            pct = 50.0
            reason = f'{jurisdiction} met {progress_pct:.1f}% of above-moderate RHNA (≤50%)'

        # Check for Bay Area exception
        bay_area_counties = [
            'Alameda', 'Contra Costa', 'Marin', 'Napa',
            'San Francisco', 'San Mateo', 'Santa Clara', 'Solano', 'Sonoma'
        ]

        if any(county in jurisdiction for county in bay_area_counties) and pct == 10.0:
            pct = 20.0
            reason += ' (Bay Area: 20% requirement)'

        return {
            'percentage': pct,
            'reason': reason,
            'above_moderate_progress': progress_pct,
            'last_updated': self.last_updated
        }

    def _ensure_fresh_data(self):
        """Download data if cache is stale."""
        if self.data is None or self._is_cache_stale():
            self._download_data()

    def _is_cache_stale(self) -> bool:
        """Check if cached data is older than CACHE_DURATION."""
        if self.last_updated is None:
            return True
        return datetime.now() - self.last_updated > self.CACHE_DURATION

    def _download_data(self):
        """Download RHNA data from HCD."""
        # Download 6th cycle data (current)
        df_6th = pd.read_csv(self.RHNA_6TH_CYCLE_URL)

        # Process and store
        self.data = df_6th
        self.last_updated = datetime.now()

        # Save to cache
        cache_path = f"{self.cache_dir}/rhna_6th_cycle.csv"
        df_6th.to_csv(cache_path, index=False)

    def _lookup_jurisdiction(self, jurisdiction: str, year: int = None) -> dict:
        """Look up jurisdiction data in cached dataset."""
        # Implementation depends on actual CSV structure
        # This is a placeholder
        pass
```

**Recommended Refresh Strategy:**
- Weekly automated download (cron job)
- On-demand refresh via admin API
- Cache validation on startup
- Fallback to previous cache if download fails

---

### Option 2: Use HCD SB35 Determination Dataset Directly

**Approach:** Download official SB35 determination CSV which already has 10% vs 50% calculated

**Pros:**
- HCD's official determination (authoritative)
- No calculation required
- Already categorized by affordability requirement
- Most legally defensible

**Cons:**
- Annual updates only
- May lag current year data
- Still requires CSV download (no API)

**Implementation:**
```python
def load_sb35_determinations() -> pd.DataFrame:
    """
    Load HCD's official SB35 streamlining determinations.

    Returns:
        DataFrame with columns:
        - jurisdiction
        - affordability_requirement (10 or 50)
        - above_moderate_progress
        - determination_year
    """
    # Download from https://data.ca.gov/dataset/sb-35-data
    # Parse CSV
    # Return as DataFrame
    pass

def get_affordability_from_determination(jurisdiction: str,
                                        determinations: pd.DataFrame) -> float:
    """
    Look up affordability requirement from HCD determinations.

    Returns 10.0 or 50.0 (percentage)
    """
    match = determinations[
        determinations['jurisdiction'].str.contains(jurisdiction, case=False)
    ]

    if len(match) == 0:
        # Not found - default to 50% (conservative)
        return 50.0

    return float(match.iloc[0]['affordability_requirement'])
```

---

### Option 3: CKAN API for Metadata + CSV Download

**Approach:** Use CKAN API to check for updates, then download CSV

**Pros:**
- Can detect when new data is available
- Automated update checking
- Gets latest resource URLs

**Cons:**
- More complex than direct download
- API not guaranteed to be stable
- Still requires CSV parsing

**Implementation:**
```python
import requests

def check_for_updates(last_updated: datetime) -> bool:
    """
    Check if RHNA dataset has been updated since last download.

    Returns True if new data available.
    """
    api_url = "https://data.ca.gov/api/3/action/package_show"
    params = {"id": "rhna-progress-report"}

    response = requests.get(api_url, params=params)
    data = response.json()

    if not data['success']:
        return False

    # Check last_modified of resources
    for resource in data['result']['resources']:
        if 'last_modified' in resource:
            resource_date = datetime.fromisoformat(resource['last_modified'])
            if resource_date > last_updated:
                return True

    return False

def get_latest_csv_url() -> str:
    """Get URL for latest 6th cycle RHNA progress CSV."""
    api_url = "https://data.ca.gov/api/3/action/package_show"
    params = {"id": "rhna-progress-report"}

    response = requests.get(api_url, params=params)
    data = response.json()

    for resource in data['result']['resources']:
        if '6th Cycle' in resource.get('name', ''):
            return resource['url']

    return None
```

---

### Option 4: Regional COG APIs (for specific regions)

**Approach:** Integrate with regional COG APIs where available

**Pros:**
- More frequent updates (SANDAG daily)
- Regional specificity
- May have richer data

**Cons:**
- Must integrate multiple APIs
- Different data formats per region
- Not all COGs have APIs
- Doesn't cover entire state

**Recommended for:**
- Applications focused on specific regions
- Projects needing real-time data
- Integration with other regional data sources

**Example - SANDAG Socrata API:**
```python
def get_sandag_rhna_data(jurisdiction: str) -> dict:
    """
    Get RHNA data from SANDAG Open Data Portal.

    Uses Socrata SODA API.
    """
    # SANDAG dataset ID: as8h-a2a4
    base_url = "https://opendata.sandag.org/resource/as8h-a2a4.json"

    params = {
        "$where": f"jurisdiction='{jurisdiction}'",
        "$limit": 1000
    }

    response = requests.get(base_url, params=params)
    return response.json()
```

---

## Fallback Strategies

### 1. Hardcoded Jurisdiction List (Current Approach)

**When to use:** As temporary solution or backup

**Implementation:**
```python
# Update quarterly based on HCD publications
HIGH_PERFORMING_JURISDICTIONS = [
    "San Francisco",
    "San Jose",
    "Sacramento",
    # Add more based on latest HCD determination
]

def get_affordability_fallback(jurisdiction: str) -> float:
    """Fallback when data unavailable."""
    if any(city in jurisdiction for city in HIGH_PERFORMING_JURISDICTIONS):
        return 10.0
    return 50.0  # Conservative default
```

**Pros:**
- Always available
- Fast
- No external dependencies

**Cons:**
- Requires manual updates
- May be inaccurate
- Legally risky if outdated

---

### 2. Manual Override + Cache

**When to use:** For production systems requiring accuracy

**Implementation:**
```python
class RHNAService:
    def __init__(self):
        self.cached_data = self._load_cached_data()
        self.manual_overrides = self._load_overrides()

    def get_affordability(self, jurisdiction: str) -> dict:
        # Priority 1: Manual override (for corrections)
        if jurisdiction in self.manual_overrides:
            return self.manual_overrides[jurisdiction]

        # Priority 2: Cached HCD data
        if jurisdiction in self.cached_data:
            return self.cached_data[jurisdiction]

        # Priority 3: Conservative default
        return {'percentage': 50.0, 'source': 'default'}
```

---

### 3. User Verification Required

**When to use:** For mission-critical determinations

**Implementation:**
- Display data source and date to user
- Require user to confirm or override
- Provide links to HCD determination documents
- Document user's confirmation for audit trail

```python
def get_affordability_with_verification(jurisdiction: str) -> dict:
    result = rhna_service.get_affordability(jurisdiction)

    return {
        **result,
        'requires_verification': True,
        'verification_url': 'https://www.hcd.ca.gov/planning-and-community-development/statutory-determinations',
        'message': f'Based on {result["source"]} data from {result["last_updated"]}. Please verify with local planning department.'
    }
```

---

## Data Update Frequency Summary

| Source | Update Frequency | Latency | Reliability |
|--------|-----------------|---------|-------------|
| RHNA Progress Report CSV | Biweekly | ~2 weeks | High |
| SB35 Determination Dataset | Annual | ~1 year | High (official) |
| APR Dashboard | Annual | Fiscal year end | High |
| SMAP Dashboard | Daily | ~1 day | High |
| CKAN API Metadata | Real-time | <1 min | Medium |
| SANDAG Open Data | Near real-time | <1 day | High |
| SCAG Regional Data | Varies | Unknown | Medium |
| ABAG Data Packets | Per cycle | Unknown | High |

**Recommendation:** Use biweekly RHNA Progress Report as primary source, with annual SB35 Determination as authoritative backup.

---

## Implementation Roadmap

### Phase 1: Replace Hardcoded Logic (Immediate)

1. **Download HCD SB35 Determination CSV**
   - Parse into local database or JSON
   - Create lookup function by jurisdiction
   - Update `get_affordability_requirement()` in sb35.py

2. **Add Data Source Attribution**
   - Include last updated date in response
   - Add disclaimer about verifying with planning department
   - Log data source for audit trail

3. **Testing**
   - Test against known high-performing jurisdictions
   - Test against known low-performing jurisdictions
   - Validate Bay Area 20% exception

**Estimated Effort:** 2-4 hours

---

### Phase 2: Automated Data Refresh (Short-term)

1. **Implement Cache System**
   - Create `RHNADataService` class
   - Local file cache in `data/rhna_cache/`
   - Weekly refresh schedule

2. **CKAN API Integration**
   - Check for dataset updates
   - Download new CSV when available
   - Validate data integrity

3. **Admin Interface**
   - View current data version
   - Manually trigger refresh
   - View cache status

**Estimated Effort:** 1-2 days

---

### Phase 3: Calculate RHNA Progress (Medium-term)

1. **Download APR Table A2 Data**
   - Parse building permit data by income level
   - Calculate cumulative progress vs RHNA allocation
   - Determine pro-rata expected progress

2. **Implement Calculation Logic**
   - Above moderate progress percentage
   - Apply 50% threshold
   - Handle Bay Area exception

3. **Historical Tracking**
   - Store historical determinations
   - Track changes over time
   - Alert on jurisdiction status changes

**Estimated Effort:** 3-5 days

---

### Phase 4: Regional COG Integration (Long-term)

1. **SANDAG API**
   - Implement Socrata API client
   - Real-time data for San Diego region

2. **SCAG ArcGIS REST Services**
   - Identify RHNA layers
   - Query by jurisdiction
   - Parse GeoJSON/JSON response

3. **ABAG Data Integration**
   - Download Housing Needs Data Packets
   - Parse Excel files
   - Extract RHNA progress

4. **Unified Interface**
   - Abstract data source behind common interface
   - Route requests to appropriate regional source
   - Fallback to state data if regional unavailable

**Estimated Effort:** 1-2 weeks

---

## Legal and Compliance Considerations

### 1. Data Accuracy Disclaimer

**Required:** Always include disclaimer that users should verify RHNA status with local planning department

**Example:**
```
This determination is based on [source] data from [date].
Jurisdictions' RHNA status may change. Always verify current
status with the local planning department and review HCD's
latest determination at:
https://www.hcd.ca.gov/planning-and-community-development/statutory-determinations
```

### 2. Data Source Attribution

**Required:** Clearly state data source and last updated date

**Example:**
```python
return {
    'percentage': 10.0,
    'data_source': 'HCD SB35 Determination Dataset',
    'data_date': '2024-01-15',
    'determination_url': 'https://data.ca.gov/dataset/sb-35-data',
    'disclaimer': 'User must verify with local jurisdiction'
}
```

### 3. Update Frequency

**Best Practice:**
- Check for updates weekly minimum
- Display data staleness warning if >30 days old
- Require manual confirmation for >90 day old data

### 4. Manual Override Capability

**Recommended:** Allow users to override determination with documentation

**Use case:** When user has more recent information from planning department

---

## Testing Data

### Known High-Performing Jurisdictions (10% requirement)

Based on historical HCD determinations:
- San Francisco
- San Jose
- Sacramento
- Daly City
- Fremont

### Known Low-Performing Jurisdictions (50% requirement)

Many suburban jurisdictions fail to meet above-moderate RHNA, including:
- Various Bay Area suburbs
- Los Angeles area suburbs
- Southern California cities

**Testing Strategy:**
1. Manually verify 5-10 jurisdictions against latest HCD determination
2. Test boundary cases (jurisdictions near 50% threshold)
3. Validate Bay Area 20% exception
4. Test error handling for unknown jurisdictions

---

## Resources and References

### Official HCD Resources

- **Statutory Determinations:** https://www.hcd.ca.gov/planning-and-community-development/statutory-determinations
- **SMAP Dashboard:** https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process-dashboard
- **RHNA Portal:** https://www.hcd.ca.gov/planning-and-community-development/regional-housing-needs-allocation
- **APR Information:** https://www.hcd.ca.gov/planning-and-community-development/annual-progress-reports
- **HCD Connect:** Portal for jurisdictions to submit data
- **Contact:** APR@hcd.ca.gov, HCDConnectHPD@hcd.ca.gov

### Data Portals

- **California Open Data:** https://data.ca.gov/
- **RHNA Progress Report:** https://data.ca.gov/dataset/rhna-progress-report
- **SB35 Determination Data:** https://data.ca.gov/dataset/sb-35-data
- **APR Data:** https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year

### Regional COGs

- **ABAG:** https://abag.ca.gov/, https://housing.abag.ca.gov/
- **SCAG:** https://hub.scag.ca.gov/, https://gisdata-scag.opendata.arcgis.com/
- **SANDAG:** https://opendata.sandag.org/, https://datasurfer.sandag.org/api
- **SACOG:** https://data.sacog.org/
- **AMBAG:** https://www.ambag.org/

### Legal References

- **Gov. Code § 65913.4:** SB35 Streamlined Ministerial Approval
- **Gov. Code § 65400:** Annual Progress Report requirement
- **Health & Safety Code § 50093:** Income limit definitions

### Technical Documentation

- **CKAN API Docs:** https://docs.ckan.org/en/latest/api/
- **Socrata SODA API:** https://dev.socrata.com/
- **ArcGIS REST API:** https://developers.arcgis.com/rest/

---

## Appendix A: CSV Data Structure Examples

### RHNA Progress Report CSV (6th Cycle)

Expected columns:
```
jurisdiction, year, income_level, rhna_allocation, permits_issued, progress_pct
"San Francisco", 2022, "Above Moderate", 46598, 25432, 54.6
"San Francisco", 2022, "Very Low", 4583, 1234, 26.9
```

### SB35 Determination Dataset

Expected columns:
```
jurisdiction, county, region, above_moderate_progress, affordability_requirement, determination_year
"San Francisco", "San Francisco", "ABAG", 54.6, 10, 2024
"Los Angeles", "Los Angeles", "SCAG", 32.1, 50, 2024
```

---

## Appendix B: Python Dependencies

Required packages for implementation:

```txt
# requirements.txt additions
pandas>=2.0.0         # CSV parsing
requests>=2.31.0      # HTTP requests
python-dateutil>=2.8.2  # Date handling

# Optional for specific integrations
sodapy>=2.2.0        # Socrata API (SANDAG)
arcgis>=2.2.0        # ArcGIS REST (SCAG)
openpyxl>=3.1.0      # Excel files (ABAG)
```

---

## Appendix C: Next Steps

### Immediate Actions

1. [ ] Download latest SB35 Determination CSV from HCD
2. [ ] Parse CSV and identify data structure
3. [ ] Create jurisdiction lookup dictionary
4. [ ] Replace hardcoded logic in `sb35.py`
5. [ ] Add data source attribution to API responses
6. [ ] Write unit tests for common jurisdictions

### Short-term Actions

1. [ ] Implement `RHNADataService` class
2. [ ] Set up automated weekly refresh (cron or scheduled task)
3. [ ] Create admin endpoint to view data version
4. [ ] Add logging for data updates
5. [ ] Create data validation tests

### Medium-term Actions

1. [ ] Download and parse APR Table A2 data
2. [ ] Implement RHNA progress calculation
3. [ ] Add historical tracking database table
4. [ ] Create alerts for jurisdiction status changes
5. [ ] Build admin dashboard for RHNA data management

### Long-term Actions

1. [ ] Evaluate regional COG API integration needs
2. [ ] Implement SANDAG API integration (if San Diego focus)
3. [ ] Implement SCAG API integration (if SoCal focus)
4. [ ] Build unified data abstraction layer
5. [ ] Consider real-time update subscriptions

---

## Contact and Support

**Questions about RHNA data:**
- HCD APR Team: APR@hcd.ca.gov
- HCD Connect Support: HCDConnectHPD@hcd.ca.gov

**Regional COG contacts:**
- ABAG: info@bayareametro.gov
- SCAG: scaggisadmin@scag.ca.gov
- SANDAG: Via open data portal
- SACOG: Via open data portal
- AMBAG: Via website contact form

**California Open Data Portal:**
- CKAN API support via data.ca.gov

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Author:** Research compiled for Parcel Feasibility Engine project
