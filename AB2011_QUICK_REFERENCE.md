# AB 2011 Quick Reference Card

## Eligibility Requirements Checklist

### ✅ MUST HAVE (All Required)

#### 1. Corridor Eligibility
- [ ] Commercial zoning (C-1, C-2, C-3)
- [ ] Office zoning (O, OFFICE)
- [ ] Mixed-use zoning (M, MIXED)

#### 2. Site NOT in Exclusion Zones
- [ ] NOT in coastal high hazard zone
- [ ] NOT on prime farmland
- [ ] NOT in wetlands
- [ ] NOT in conservation area
- [ ] NOT a historic property

#### 3. NO Protected Housing
- [ ] NO rent-controlled units
- [ ] NO deed-restricted affordable housing
- [ ] NO Ellis Act withdrawn units
- [ ] NO recent residential tenancy (10 years)

#### 4. Labor Standards Commitment
- [ ] Prevailing wage commitment (ALL projects)
- [ ] Skilled & trained workforce (if 50+ units)
- [ ] Healthcare benefits (recommended)

---

## Corridor Tiers & Standards

| Tier | Zoning Examples | Min Density | Min Height | Example Streets |
|------|----------------|-------------|------------|-----------------|
| **Low (Tier 1)** | C-1 | 30 u/ac | 35 ft | Neighborhood commercial |
| **Mid (Tier 2)** | C-2, Office, Mixed | 50 u/ac | 45 ft | Major arterials w/ transit |
| **High (Tier 3)** | C-3, Regional | 80 u/ac | 65 ft | Regional commercial centers |

---

## Development Tracks

### Mixed-Income Track
- Affordability: 15% (placeholder, TODO: Santa Monica specific)
- All other units market-rate
- Ministerial approval

### 100% Affordable Track
- All units affordable (except 1 manager unit)
- Deeper affordability levels
- Ministerial approval

---

## Parking Requirements

### With AB 2097 (Near Transit)
- **0 spaces** if within ½ mile of major transit
- Major transit = rail, BRT, or 2+ bus routes w/ 15-min peak service

### Without AB 2097
- Default: 0.5 spaces per unit (placeholder)
- TODO: Integrate car-share locations for zero parking

---

## Coastal Zone Requirements

If parcel has `in_coastal_zone = True`:
- ⚠️ Coastal Development Permit (CDP) may be required
- ⚠️ Must comply with Local Coastal Program (LCP)
- ⚠️ Coordinate with California Coastal Commission
- Does NOT block eligibility, adds requirements

---

## Function Quick Reference

### Simple Check (Boolean)
```python
from app.rules.ab2011 import is_ab2011_eligible
eligible = is_ab2011_eligible(parcel)  # True/False
```

### Detailed Check (With Reasons)
```python
from app.rules.ab2011 import can_apply_ab2011
result = can_apply_ab2011(parcel)
# result['eligible'] = True/False
# result['reasons'] = [...]
# result['exclusions'] = [...]
```

### Generate Scenario
```python
from app.rules.ab2011 import analyze_ab2011
scenario = analyze_ab2011(parcel)  # None if ineligible
```

### Generate Both Tracks
```python
from app.rules.ab2011 import analyze_ab2011_tracks
scenarios = analyze_ab2011_tracks(parcel)  # [] if ineligible
```

---

## Common Exclusion Reasons

### Corridor Ineligibility
- "Parcel is not zoned for commercial/office/mixed-use"
- "Parcel is not on an eligible AB 2011 corridor"

### Site Exclusions
- "EXCLUDED: Parcel is in coastal high hazard zone"
- "EXCLUDED: Parcel is on prime farmland or farmland of statewide importance"
- "EXCLUDED: Parcel contains wetlands or sensitive habitat"
- "EXCLUDED: Parcel has conservation easement or is in protected area"
- "EXCLUDED: Parcel contains historic resource or structure"

### Protected Housing
- "EXCLUDED: Parcel contains rent-controlled units (AB 2011 protection)"
- "EXCLUDED: Parcel has deed-restricted affordable housing (protected)"
- "EXCLUDED: Parcel had units withdrawn under Ellis Act within lookback period"
- "EXCLUDED: Parcel had residential tenancy within last 10 years (AB 2011 protection)"

### Labor Standards
- "REQUIRED: Prevailing wage commitment missing - MANDATORY for all AB 2011 projects"
- "REQUIRED: Skilled & trained workforce commitment missing - MANDATORY for projects with 50+ units"

---

## Required Parcel Fields

### Minimum Required
```python
parcel = ParcelBase(
    apn="...",
    address="...",
    city="...",
    county="...",
    zip_code="...",
    lot_size_sqft=...,
    zoning_code="...",      # C-1, C-2, C-3, OFFICE, MIXED
    existing_units=0,
    existing_building_sqft=0.0,
)
```

### For Full Eligibility Check
```python
# Add these flags (defaults to None/False = eligible)
prevailing_wage_commitment=True,           # REQUIRED
skilled_trained_workforce_commitment=True, # If 50+ units
in_coastal_high_hazard=False,
in_prime_farmland=False,
in_wetlands=False,
in_conservation_area=False,
is_historic_property=False,
has_rent_controlled_units=False,
has_deed_restricted_affordable=False,
has_ellis_act_units=False,
has_recent_tenancy=False,
protected_units_count=0,
```

### Optional Enhancements
```python
in_coastal_zone=True,     # Adds CDP notes
near_transit=True,        # Triggers AB 2097 parking elimination
overlay_codes=["TOD"],    # May upgrade tier
latitude=34.0195,         # For spatial analysis
longitude=-118.4912,
```

---

## Labor Standards Thresholds

| Requirement | Threshold | Mandatory? |
|-------------|-----------|------------|
| Prevailing Wage | **ALL projects** (0+ units) | ✅ YES |
| Skilled & Trained Workforce | **50+ units** | ✅ YES (if threshold met) |
| Healthcare Benefits | Varies by jurisdiction | ⚠️ Recommended |

---

## Unit Count Calculations

### Formula
```
Minimum Units = ceil(Lot Acres × Tier Min Density)

where:
  Lot Acres = lot_size_sqft / 43,560
  Tier Min Density = 30, 50, or 80 u/ac
```

### Examples (1 Acre = 43,560 sq ft)
- **0.5 acres, Low tier**: 0.5 × 30 = 15 units
- **1.0 acres, Mid tier**: 1.0 × 50 = 50 units
- **2.0 acres, High tier**: 2.0 × 80 = 160 units

---

## Height & Stories

### Height Formula
```
Minimum Height = Tier Min Height (35, 45, or 65 ft)
Max Stories = ceil(Min Height / 12 ft per story)
```

### Examples
- **Low tier**: 35 ft → 3 stories
- **Mid tier**: 45 ft → 4 stories
- **High tier**: 65 ft → 6 stories

---

## Common Warnings (Non-Blocking)

- "WARNING: Parcel is in flood hazard zone - additional requirements may apply"
- "WARNING: Parcel has existing units - verify no demolition of residential units required"
- "Healthcare benefits commitment not indicated - may be required by local jurisdiction"

---

## TODO Items (Santa Monica Data Needed)

### High Priority
1. [ ] Official corridor mapping (replace zoning heuristic)
2. [ ] Rent control database integration
3. [ ] Labor standards verification system
4. [ ] GIS layer integration (exclusions)

### Medium Priority
5. [ ] Alquist-Priolo fault zone mapping
6. [ ] Car-share location database (AB 2097)
7. [ ] Local Coastal Program (LCP) details
8. [ ] Objective design standards (ODDS)

### Data Fields
9. [ ] ROW width thresholds
10. [ ] Frontage length requirements
11. [ ] Corridor spacing criteria
12. [ ] Santa Monica-specific affordability %

---

## Testing

### Run Full Test Suite
```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine"
./venv/bin/python -m pytest tests/test_ab2011_eligibility.py -v
```

### Test Count
- **60+ comprehensive tests**
- **8 test classes**
- Coverage: Corridor, Exclusions, Housing, Labor, Integration

---

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `app/rules/ab2011.py` | Implementation | 921 |
| `app/models/parcel.py` | Data model | 138 |
| `tests/test_ab2011_eligibility.py` | Unit tests | 487 |
| `AB2011_IMPLEMENTATION_REPORT.md` | Full report | - |
| `AB2011_API_EXAMPLES.md` | Code examples | - |

---

## Decision Flow

```
┌─────────────────────┐
│   Parcel Input      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 1. Corridor Check   │
│    (Zoning & Tier)  │
└──────────┬──────────┘
           │
           ├─── ❌ Not Commercial → INELIGIBLE
           │
           ▼
┌─────────────────────┐
│ 2. Site Exclusions  │
│    (5 checks)       │
└──────────┬──────────┘
           │
           ├─── ❌ In Exclusion Zone → INELIGIBLE
           │
           ▼
┌─────────────────────┐
│ 3. Protected Housing│
│    (5 checks)       │
└──────────┬──────────┘
           │
           ├─── ❌ Has Protections → INELIGIBLE
           │
           ▼
┌─────────────────────┐
│ 4. Labor Standards  │
│    (Wage + Skilled) │
└──────────┬──────────┘
           │
           ├─── ❌ Missing Commitment → INELIGIBLE
           │
           ▼
┌─────────────────────┐
│  ✅ ELIGIBLE!       │
│  Generate Scenarios │
└──────────┬──────────┘
           │
           ├─── Mixed-Income Scenario
           └─── 100% Affordable Scenario
```

---

**Last Updated**: 2025-10-06
**Version**: 1.0.0
**Status**: Production Ready (pending Santa Monica data integration)
