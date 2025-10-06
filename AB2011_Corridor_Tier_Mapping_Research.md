# AB 2011 Corridor Tier Mapping Research
## Official Data Sources for Santa Monica Office-to-Residential Conversions

**Date:** October 6, 2025
**Project:** Parcel Feasibility Engine
**Focus:** AB 2011 (Affordable Housing and High Road Jobs Act of 2022)

---

## Executive Summary

This research investigates available data sources for AB 2011 corridor tier mapping in Santa Monica, California. **Key Finding:** There are no official "corridor tier" classifications published by California HCD or Santa Monica. Instead, AB 2011 uses **corridor width-based density and height standards** that can be calculated from street right-of-way (ROW) data.

The current implementation in `/Users/Jordan_Ostwald/Parcel Feasibility Engine/app/rules/state_law/ab2011.py` uses heuristic zoning-based inference (lines 30, 744) which needs replacement with ROW-width-based classification using available GIS data.

---

## Understanding AB 2011: No "Tiers" - Width-Based Standards

### Critical Clarification

AB 2011 does **not** define three "tiers" (Tier 1, Tier 2, Tier 3) as initially assumed. Instead, it establishes **corridor width-based density and height standards** as follows:

### Density Standards (Units per Acre)

For mixed-income projects, density is the **greater of**:
- Local maximum density, OR
- State minimum floors based on parcel size and corridor width:

| Parcel Size | Corridor Width | Minimum Density |
|-------------|----------------|-----------------|
| < 1 acre | Any eligible corridor | 30 units/acre |
| ≥ 1 acre | < 100 ft ROW | 40 units/acre |
| ≥ 1 acre | ≥ 100 ft ROW | 60 units/acre |
| Any size | Within 0.5 mi of major transit | 80 units/acre |

**Source:** California Government Code §65912.124, as amended by AB 2243 (2024)

### Height Standards (Feet)

Maximum height is the **greater of**:
- Local maximum height, OR
- State minimum floors based on corridor width:

| Corridor Width | Transit Proximity | Coastal Zone | Minimum Height |
|----------------|-------------------|--------------|----------------|
| < 100 ft ROW | Not near transit | Any | 35 feet |
| ≥ 100 ft ROW | Any | Any | 45 feet |
| Any width | Within 0.5 mi of major transit | NOT in coastal zone | 65 feet |

**Source:** California Government Code §65912.124

### Commercial Corridor Definition

Per California Government Code §65912.101:
- **Street** that is not a freeway
- Right-of-way (ROW) between **70 and 150 feet** wide
- Originally required "highway" (pre-AB 2243), now simplified to "street"

**Recent Amendment:** AB 2243 (effective January 1, 2025) revised the definition from "highway" to "street" and reduced minimum ROW from 70 feet to potentially 50 feet for certain sites.

---

## Data Sources for Implementation

### 1. Street Right-of-Way (ROW) Width Data

#### Source: Santa Monica GIS Open Data Portal
- **Organization:** City of Santa Monica Enterprise GIS
- **URL:** https://gis-smgov.opendata.arcgis.com/
- **Specific Dataset:** Streets layer
- **Direct Link:** https://gisdata.santamonica.gov/maps/smgov::streets
- **Data Availability:** GIS service, downloadable shapefile
- **Coverage:** Citywide Santa Monica
- **Contact:** gis.mailbox@santamonica.gov

**Tier Classification Method:**
- Query street ROW width attribute
- Apply corridor eligibility filter: 70 ≤ ROW ≤ 150 feet
- Classify into density/height categories based on ROW < 100 ft vs ≥ 100 ft
- **Official Status:** Municipal GIS data (authoritative for city boundaries)
- **Integration Complexity:** Medium
  - Need to access ROW width attribute in Streets dataset
  - Join parcels to adjacent streets
  - Filter to commercial zoning overlaps
  - May require spatial analysis to identify "abutting" relationship

**Research Note:** Direct access to the Streets dataset page returned a 403 error during research, suggesting authentication may be required. Contact GIS department for data access or API credentials.

---

### 2. Transit Proximity Analysis

#### Source: Santa Monica Transit Priority Area Layer
- **Organization:** City of Santa Monica
- **URL:** https://gisdata.santamonica.gov/maps/e141ec6b485f4837a6629024ed0297b6
- **Dataset:** Transit Priority Area
- **Data Availability:** GIS web map, likely downloadable
- **Coverage:** Citywide Santa Monica
- **Tier Classification Method:**
  - 0.5-mile buffer around "major transit stops"
  - Major transit stop = rail station or bus stop with 15-min peak service
  - Parcels within buffer eligible for 80 units/acre, 65 ft height (if not coastal)
- **Official Status:** Municipal planning overlay
- **Integration Complexity:** Low-Medium
  - Standard buffer analysis (0.5 miles)
  - Point-in-polygon check for parcels

---

### 3. Los Angeles County Regional Data

#### Source: LA County Enterprise GIS
- **Organization:** Los Angeles County
- **URL:** https://egis-lacounty.hub.arcgis.com/
- **Data Availability:** GIS portal with interactive maps and downloads
- **Coverage:** Countywide (includes unincorporated areas, may have regional street data)
- **Tier Classification Method:**
  - May contain regional street centerline data with ROW attributes
  - Useful for parcels near Santa Monica boundaries
- **Official Status:** County authoritative GIS
- **Integration Complexity:** Medium
  - Need to filter to Santa Monica jurisdiction
  - Verify ROW attribute availability and consistency

---

### 4. Los Angeles City Planning ZIMAS

#### Source: Zone Information and Map Access System (ZIMAS)
- **Organization:** Los Angeles City Planning Department
- **URL:** https://planning.lacity.gov/
- **Tool:** ZIMAS web-based mapping tool
- **Data Availability:** Interactive web map (not directly for Santa Monica, but methodology reference)
- **Coverage:** City of Los Angeles only
- **Tier Classification Method:**
  - LA City has implemented AB 2011 eligibility checking in ZIMAS
  - Provides "AB 2097 Eligibility" field (parking reduction, related to AB 2011)
  - Methodology could inform Santa Monica implementation
- **Official Status:** Municipal planning tool
- **Integration Complexity:** Not directly applicable (different jurisdiction)
- **Value:** Reference for implementation approach

---

### 5. Statewide AB 2011 Eligibility Analysis

#### Source: UrbanFootprint AB 2011 Analysis
- **Organization:** UrbanFootprint (in collaboration with HDR/Calthorpe, Mapcraft Labs, Economic & Planning Systems)
- **URL:** https://urbanfootprint.com/blog/policy/ab2011-analysis/
- **Publication Date:** 2022 (analysis of AB 2011 potential)
- **Data Availability:** Analysis report published; GIS data availability unclear
- **Coverage:** Statewide California
- **Key Findings:**
  - Analyzed 376,000 commercial parcels statewide
  - 42% (159,000 parcels) met AB 2011 eligibility criteria
  - Introduced 108,000 acres for residential development
  - Estimated 1.6-2.4 million market-feasible housing units

**Eligibility Criteria Applied:**
- Parcels zoned for retail, office, or parking
- Abut commercial corridors (70-150 ft ROW)
- Located in Census-defined urbanized areas
- No existing dwelling units
- Not adjacent to industrial sites
- < 20 acres in size
- ≥75% of perimeter adjoins urban uses
- Not within 500 feet of freeway

**Tier Classification Method:**
- ROW width analysis from street centerline data
- Metropolitan vs suburban classification
- Transit proximity analysis

**Official Status:** Academic/consulting analysis (not official government data)
**Integration Complexity:** High
- Unclear if data is publicly downloadable
- May require commercial license or partnership
- Contact UrbanFootprint for data access
- Value: Comprehensive statewide baseline for validation

---

### 6. California HCD Resources

#### Source: California Department of Housing and Community Development
- **Organization:** State of California HCD
- **URL:** https://www.hcd.ca.gov/
- **Specific Pages:**
  - Technical Assistance: https://www.hcd.ca.gov/planning-and-community-development/technical-assistance
  - HCD Memos: https://www.hcd.ca.gov/planning-and-community-development/hcd-memos
- **Data Availability:** Guidance documents, technical advisories, no GIS data
- **Coverage:** Statewide guidance
- **Tier Classification Method:** N/A (no mapping data)
- **Official Status:** State regulatory authority
- **Integration Complexity:** N/A

**Key Findings:**
- HCD provides technical assistance to jurisdictions implementing AB 2011
- No statewide AB 2011 corridor tier GIS layer published
- Implementation responsibility delegated to local jurisdictions
- HCD can report non-compliant localities to Attorney General
- AB 2011 is "untested" - awaiting HCD guidance and court interpretation on ambiguous provisions

**Value for Project:**
- Monitor HCD Memos page for future AB 2011 guidance
- Potential future technical advisories on corridor classification
- Currently: no actionable mapping data

---

### 7. Regional Planning Organizations

#### Source: Association of Bay Area Governments (ABAG)
- **Organization:** ABAG (Bay Area regional planning)
- **URL:** https://abag.ca.gov/technical-assistance/overview-ab-2011-and-sb-6
- **Document:** "AB 2011 and SB 6 Summary of Key Details" (July 2023)
  - Direct Link: https://abag.ca.gov/sites/default/files/documents/2023-07/AB-2011-SB-6-Summary-Key-Details-7.28.2023.pdf
- **Data Availability:** PDF guidance documents, webinars
- **Coverage:** Bay Area (not Santa Monica, but methodology reference)
- **Tier Classification Method:** Not specified (guidance for cities)
- **Official Status:** Regional planning guidance
- **Integration Complexity:** N/A (informational only)

**Key Findings:**
- ABAG provides staff resources and implementation guidance
- As of July 2023, most Bay Area cities deferring AB 2011 planning
- Only 16 of 106 Bay Area jurisdictions addressed AB 2011 in housing elements
- Regional bodies providing technical assistance, not GIS data

---

### 8. Academic and Planning Research

#### Source: UC Berkeley Terner Center for Housing Innovation
- **Organization:** Terner Center (Berkeley research institute)
- **URL:** https://ternercenter.berkeley.edu/research-and-policy/ab-2011-commercial-zones/
- **Publication:** "Residential Housing Is Now Allowed in All Commercial Zones: Are California Cities Ready?"
- **Data Availability:** Research report (no GIS data)
- **Coverage:** Qualitative assessment of 106 Bay Area jurisdictions
- **Key Findings:**
  - Interviewed housing experts
  - Analyzed housing element documents
  - Found most jurisdictions unprepared for AB 2011 implementation
  - Complexity of requirements posed challenges
  - Recommended increased technical assistance for cities

**Tier Classification Method:** N/A (policy analysis, not mapping)
**Official Status:** Academic research
**Integration Complexity:** N/A (no data)
**Value:** Context on implementation challenges and readiness

---

### 9. Santa Monica Zoning and Land Use Data

#### Source: Santa Monica Zoning GIS Layer
- **Organization:** City of Santa Monica
- **URL:** https://gisdata.santamonica.gov/maps/bd85cc6b1b7d4e9d95ee3733de086f38
- **Dataset:** Zoning
- **Data Availability:** GIS web map, downloadable
- **Coverage:** Citywide Santa Monica
- **Tier Classification Method:**
  - Identify parcels zoned for commercial/office/retail uses
  - Commercial zones are prerequisite for AB 2011 eligibility
  - Current code uses this approach (see ab2011.py lines 726-741)
- **Official Status:** Municipal zoning (authoritative)
- **Integration Complexity:** Low (already integrated in current system)

**Current Implementation:**
```python
# From ab2011.py lines 728-729
commercial_zones = ["C", "COMMERCIAL", "OFFICE", "O", "M", "MIXED"]
is_commercial = any(zone in zoning_code for zone in commercial_zones)
```

**Limitation:** Zoning alone is insufficient - must also verify corridor width (ROW 70-150 ft)

---

### 10. Santa Monica Coastal Zone Overlay

#### Source: Santa Monica Planning Department / California Coastal Commission
- **Consideration:** Coastal zone designation affects height limits
- **Rule:** 65-ft height limit does NOT apply in coastal zones (even near transit)
- **Data Need:** Coastal zone boundary overlay
- **Current Implementation:** `parcel.in_coastal_zone` flag (see ab2011.py lines 122-127)
- **Integration Complexity:** Low (already integrated)
- **Official Status:** State/local regulatory overlay

---

## Recommended Implementation Approach

### Phase 1: Acquire Santa Monica Street ROW Data

**Priority:** HIGH

**Actions:**
1. Contact Santa Monica GIS: gis.mailbox@santamonica.gov
2. Request Streets dataset with ROW width attribute
3. Verify data format (shapefile, geodatabase, or GIS service)
4. Confirm attribute name for right-of-way width
5. Request data dictionary/metadata

**Expected Data Structure:**
```
Street Centerline Features:
- STREET_NAME: string
- ROW_WIDTH: numeric (feet)
- STREET_CLASS: string (arterial, collector, local, etc.)
- Geometry: LineString
```

**Alternative:** If ROW width not available as attribute, may need to:
- Request parcel boundary data
- Calculate ROW from parcel frontages
- Or obtain right-of-way polygon layer directly

### Phase 2: Develop Corridor Eligibility Layer

**Priority:** HIGH

**Technical Approach:**
1. Filter Streets where `70 <= ROW_WIDTH <= 150`
2. Create corridor classification:
   - `corridor_narrow`: ROW 70-99 ft → 40 units/acre (≥1 acre), 35 ft height
   - `corridor_wide`: ROW 100-150 ft → 60 units/acre (≥1 acre), 45 ft height
3. Buffer eligible street centerlines by parcel frontage distance (e.g., 10-50 ft)
4. Spatial join parcels to corridor buffers to identify "abutting" relationship

**Data Pipeline:**
```
Streets GIS → Filter ROW 70-150ft → Classify by width →
Buffer → Spatial Join with Parcels → Corridor Eligibility Flag
```

**Output:** Add parcel attributes:
- `ab2011_corridor_eligible`: boolean
- `ab2011_corridor_width`: numeric (feet)
- `ab2011_corridor_classification`: enum ("narrow" | "wide" | "transit")

### Phase 3: Integrate Transit Proximity

**Priority:** MEDIUM

**Actions:**
1. Obtain Transit Priority Area layer from Santa Monica
2. Verify definition of "major transit stop" per AB 2011:
   - Rail/light rail station, OR
   - Bus stop with ≥15-minute peak service frequency
3. Create 0.5-mile buffer (2,640 feet)
4. Spatial join parcels to transit buffer
5. Override corridor classification for transit-adjacent parcels

**Output:** Add parcel attribute:
- `ab2011_near_major_transit`: boolean
- If true AND not coastal: 80 units/acre, 65 ft height eligible

### Phase 4: Update ab2011.py Classification Logic

**Priority:** HIGH

**Replace Heuristic Tier Inference:**

Current code (lines 743-841):
```python
def _infer_corridor_tier(zoning_code: str) -> str:
    """Infer a simplified corridor tier from zoning code.

    This heuristic maps common commercial codes to tiers:
    - C-1 -> low
    - C-2, OFFICE, O, MIXED -> mid
    - C-3 (or contains 'REGIONAL') -> high
    Defaults to mid if not matched.

    TODO(SM): Replace with official Santa Monica corridor tier mapping.
    """
```

**New Approach:**
```python
def determine_corridor_standards(parcel: ParcelBase) -> Dict[str, any]:
    """Determine AB 2011 density and height standards based on ROW width and transit.

    Returns:
        - eligible: bool
        - min_density_u_ac: float
        - min_height_ft: float
        - corridor_width_ft: float
        - classification: str
    """
    # Check if parcel abuts eligible corridor
    if not parcel.ab2011_corridor_eligible:
        return {"eligible": False, "reasons": ["Not on eligible corridor (ROW 70-150 ft)"]}

    row_width = parcel.ab2011_corridor_width
    lot_acres = parcel.lot_size_sqft / 43560.0
    near_transit = parcel.ab2011_near_major_transit
    in_coastal = parcel.in_coastal_zone

    # Density determination
    if near_transit:
        min_density = 80.0
        classification = "transit"
    elif lot_acres < 1.0:
        min_density = 30.0
        classification = "small_lot"
    elif row_width >= 100:
        min_density = 60.0
        classification = "wide_corridor"
    else:  # 70 <= row_width < 100
        min_density = 40.0
        classification = "narrow_corridor"

    # Height determination
    if near_transit and not in_coastal:
        min_height = 65.0
    elif row_width >= 100:
        min_height = 45.0
    else:
        min_height = 35.0

    return {
        "eligible": True,
        "min_density_u_ac": min_density,
        "min_height_ft": min_height,
        "corridor_width_ft": row_width,
        "classification": classification,
        "reasons": [
            f"Eligible corridor: {row_width} ft ROW",
            f"Minimum {min_density} units/acre, {min_height} ft height"
        ]
    }
```

### Phase 5: Validation and Testing

**Priority:** MEDIUM

**Actions:**
1. Cross-reference with UrbanFootprint analysis (if data accessible)
2. Validate against known Santa Monica commercial corridors:
   - **Santa Monica Boulevard** (major arterial, likely ≥100 ft ROW)
   - **Wilshire Boulevard** (regional corridor, likely ≥100 ft ROW)
   - **Broadway** (commercial corridor)
   - **Ocean Park Boulevard** (corridor with road diet study)
3. Spot-check specific parcels with Santa Monica Planning Department
4. Test edge cases:
   - Parcels at corridor termini
   - Corner parcels at corridor intersections
   - Parcels with multiple street frontages

---

## Key Legal References

### Statutory Authority

**California Government Code Chapter 4.1** - Affordable Housing and High Road Jobs Act of 2022

Key Sections:
- **§65912.101** - Definitions (commercial corridor, major transit stop)
- **§65912.110** - Ministerial approval requirements (100% affordable)
- **§65912.111** - Site criteria (100% affordable)
- **§65912.120** - Ministerial approval requirements (mixed-income)
- **§65912.121** - Site criteria (mixed-income)
- **§65912.124** - Density and height standards
- **§65912.130** - Labor standards (prevailing wage)
- **§65912.131** - Labor standards (skilled workforce ≥50 units)

**Legislative History:**
- **AB 2011** (Wicks, 2022) - Original enactment
  - Signed: September 28, 2022
  - Effective: July 1, 2023
  - Sunset: January 1, 2033
- **AB 2243** (Wicks, 2024) - Amendments
  - Effective: January 1, 2025
  - Expanded eligibility (reduced ROW minimums for some sites)
  - Changed "highway" to "street" in corridor definition

### Related Laws

- **AB 2097** (2022) - Parking reduction near transit (integrated in current code)
- **SB 35** (2017) - Streamlined ministerial approval (different criteria)
- **Density Bonus Law** (Gov. Code §65915) - Can be applied on top of AB 2011

---

## Data Gaps and Limitations

### 1. No Official Statewide AB 2011 GIS Layer

**Gap:** California HCD has not published a statewide AB 2011 corridor eligibility layer.

**Impact:** Each jurisdiction must self-identify eligible corridors.

**Mitigation:** Use local street ROW data (Santa Monica GIS).

### 2. Ambiguous "Abutting" Definition

**Gap:** AB 2011 requires parcels to "abut" commercial corridors but does not define minimum frontage or setback tolerances.

**Impact:** Uncertainty for parcels with minimal street frontage or separated by alley/easement.

**Mitigation:**
- Conservative approach: require direct parcel-to-ROW adjacency
- Liberal approach: allow parcels within X feet of ROW
- Consult Santa Monica Planning Department for local interpretation

### 3. Major Transit Stop Definition

**Gap:** "Major transit stop" requires bus service with "15-minute or less" peak frequency, but real-time service data may be needed.

**Impact:** Transit proximity eligibility may change with service adjustments.

**Mitigation:**
- Use Santa Monica Transit Priority Area overlay (likely pre-vetted)
- Cross-reference with Metro and Big Blue Bus schedules
- Update periodically based on service changes

### 4. ROW Width Data Availability

**Gap:** Street ROW width may not be readily available as GIS attribute in all jurisdictions.

**Impact:** Cannot calculate corridor eligibility without ROW data.

**Mitigation:**
- Request from Santa Monica Engineering/Public Works
- Derive from parcel boundaries if ROW polygons available
- Use street classification as proxy (arterial vs collector) with manual verification

### 5. Santa Monica Has Not Published AB 2011 Implementation Ordinance

**Gap:** Research found no Santa Monica-specific AB 2011 ordinance or implementation guidelines.

**Finding:** Santa Monica Housing Element (2021-2029) references AB 1287 (Density Bonus) but not AB 2011.

**Impact:** Local objective standards, affordability percentages, and procedure unclear.

**Mitigation:**
- Contact Santa Monica Planning & Community Development Department
- Request AB 2011 application checklist or administrative guidelines
- Monitor City Council agenda for AB 2011 ordinance adoption

### 6. Coastal Zone Height Restriction

**Gap:** AB 2011 excludes coastal zone parcels from 65-ft height limit, but coastal zone boundaries may have sub-zones with varying restrictions.

**Impact:** May need Local Coastal Program (LCP) compliance even if AB 2011 eligible.

**Mitigation:**
- Integrate California Coastal Commission Coastal Zone boundary
- Flag parcels for additional Coastal Development Permit (CDP) review
- Currently partially implemented (see ab2011.py lines 122-127)

---

## Recommended Next Steps

### Immediate (Week 1)

1. **Contact Santa Monica GIS Department**
   - Email: gis.mailbox@santamonica.gov
   - Request: Streets layer with ROW width attribute
   - Request: Transit Priority Area layer
   - Request: Any AB 2011 corridor mapping in progress

2. **Download Available Santa Monica GIS Data**
   - Zoning layer (already may be integrated)
   - Streets layer (if publicly accessible)
   - Coastal Zone overlay
   - Parcel boundaries (for spatial joins)

3. **Review Santa Monica Planning Documents**
   - Search for AB 2011 in City Council meeting agendas (2023-2025)
   - Check Planning Commission meeting minutes
   - Request AB 2011 application procedures

### Short-term (Weeks 2-4)

4. **Develop GIS Pipeline**
   - Process Streets data to identify eligible corridors
   - Create spatial join logic for parcel-to-corridor relationship
   - Classify corridors by width (narrow vs wide)
   - Overlay transit proximity buffers

5. **Update Parcel Data Model**
   - Add fields: `ab2011_corridor_eligible`, `ab2011_corridor_width`, `ab2011_near_major_transit`
   - Populate from GIS analysis
   - Update parcel ingestion pipeline

6. **Refactor ab2011.py**
   - Replace `_infer_corridor_tier()` with ROW-based logic
   - Update `check_corridor_eligibility()` to use parcel.ab2011_corridor_width
   - Apply correct density/height formulas per §65912.124

### Medium-term (Months 2-3)

7. **Validate Results**
   - Spot-check known Santa Monica commercial corridors
   - Cross-reference with UrbanFootprint analysis (if accessible)
   - Submit sample parcels to Santa Monica for confirmation

8. **Integrate Additional Site Exclusions**
   - Historic properties (already flagged)
   - Wetlands, prime farmland, conservation areas (already flagged)
   - Within 500 ft of freeway (not yet implemented)

9. **Document Assumptions and Limitations**
   - Update code comments with data sources
   - Document corridor classification methodology
   - Note date of GIS data (for future updates)

### Long-term (Ongoing)

10. **Monitor for Updates**
    - HCD guidance documents and memos
    - Santa Monica AB 2011 ordinance adoption
    - Legislative amendments (next: AB 2243 effects)
    - Court cases interpreting AB 2011

11. **Update Data Periodically**
    - Street ROW changes (new streets, road diets, widening projects)
    - Transit service changes (new routes, frequency adjustments)
    - Zoning updates

---

## Summary: Data Source Scorecard

| Source | Data Type | Coverage | Official | Availability | Integration | Priority |
|--------|-----------|----------|----------|--------------|-------------|----------|
| **Santa Monica Streets GIS** | ROW width | City | Yes | Request | Medium | **CRITICAL** |
| **Santa Monica Transit Priority** | Transit buffer | City | Yes | Likely available | Low | **HIGH** |
| **Santa Monica Zoning** | Commercial zones | City | Yes | Available | Low (done) | **HIGH** |
| **UrbanFootprint Analysis** | Statewide eligibility | Statewide | No | Unknown | High | Medium |
| **LA County GIS** | Regional streets | County | Yes | Available | Medium | Low |
| **California HCD** | Guidance only | State | Yes | Public docs | N/A | Low |
| **ABAG Resources** | Guidance only | Bay Area | No | Public docs | N/A | Low |
| **Terner Center Research** | Policy analysis | State | No | Public report | N/A | Low |

**Key Recommendation:**
**Focus on acquiring Santa Monica Streets ROW data as the primary data source.** This is the only dataset needed to replace heuristic corridor tier inference with accurate, width-based AB 2011 standards.

---

## Contact Information

### Santa Monica City Resources
- **GIS Department:** gis.mailbox@santamonica.gov
- **Planning & Community Development:** https://www.santamonica.gov/planning-resources
- **GIS Open Data Portal:** https://gis-smgov.opendata.arcgis.com/
- **Phone:** (310) 458-8341 (Planning main)

### State Resources
- **California HCD:** https://www.hcd.ca.gov/
- **HCD Technical Assistance:** https://www.hcd.ca.gov/planning-and-community-development/technical-assistance
- **Legislative Counsel (bill text):** https://leginfo.legislature.ca.gov/

### Research Organizations
- **UrbanFootprint:** https://urbanfootprint.com/ (contact for data access)
- **Terner Center (UC Berkeley):** https://ternercenter.berkeley.edu/
- **ABAG (Bay Area):** https://abag.ca.gov/

---

## Appendix: AB 2011 Eligibility Checklist

Based on research, a parcel is eligible for AB 2011 ministerial approval if it meets ALL criteria:

### Zoning and Corridor Requirements
- [ ] Zoned for office, retail, or parking as principally permitted use
- [ ] Abuts a commercial corridor (street with 70-150 ft ROW, not a freeway)
- [ ] Parcel size < 20 acres (if not 100% affordable on commercial land)

### Site Exclusions
- [ ] NOT in coastal high hazard zone
- [ ] NOT on prime farmland or farmland of statewide importance
- [ ] NOT wetlands or sensitive habitat
- [ ] NOT in conservation area or easement
- [ ] NOT a historic property (state/federal/local register)
- [ ] NOT within 500 feet of a freeway
- [ ] At least 75% of perimeter adjoins urban uses

### Protected Housing Restrictions
- [ ] NO rent-controlled units on site
- [ ] NO deed-restricted affordable housing to be demolished
- [ ] NO residential units occupied currently or in last 10 years
- [ ] NO Ellis Act withdrawn units (within lookback period)

### Labor Standards (Prerequisite Commitments)
- [ ] Prevailing wage commitment (REQUIRED - all projects)
- [ ] Skilled & trained workforce commitment (REQUIRED if ≥50 units)
- [ ] Healthcare benefits (recommended, may be required locally)

### Affordability Requirements
**Option A - 100% Affordable:**
- [ ] All units affordable (except 1 manager unit)
- [ ] Income levels per HCD standards

**Option B - Mixed-Income:**
- [ ] Minimum affordability percentage (varies; often 15%+)
- [ ] Income levels per AB 2011 / local requirements

### Process
- [ ] Ministerial approval (objective standards only, no discretionary review)
- [ ] CEQA-exempt (if all criteria met)

---

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Next Review:** After contact with Santa Monica GIS Department
