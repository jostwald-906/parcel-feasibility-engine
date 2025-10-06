# AB 2011 API Usage Examples

## Quick Reference Guide for AB 2011 Functions

---

## 1. Basic Eligibility Check (Simple Boolean)

```python
from app.models.parcel import ParcelBase
from app.rules.ab2011 import is_ab2011_eligible

# Create parcel
parcel = ParcelBase(
    apn="5299-012-034",
    address="1234 Main Street",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=15000.0,
    zoning_code="C-2",  # Commercial
    existing_units=0,
    existing_building_sqft=8000.0,
    # Required for eligibility
    prevailing_wage_commitment=True,
    in_coastal_high_hazard=False,
    has_rent_controlled_units=False,
)

# Simple check
if is_ab2011_eligible(parcel):
    print("Parcel is eligible for AB 2011!")
else:
    print("Parcel is not eligible for AB 2011")
```

---

## 2. Detailed Eligibility Check (With Reasons)

```python
from app.rules.ab2011 import can_apply_ab2011

# Get detailed eligibility information
eligibility = can_apply_ab2011(parcel)

print(f"Eligible: {eligibility['eligible']}")
print(f"\nReasons:")
for reason in eligibility['reasons']:
    print(f"  ✓ {reason}")

if not eligibility['eligible']:
    print(f"\nExclusions:")
    for exclusion in eligibility['exclusions']:
        print(f"  ✗ {exclusion}")

if eligibility['warnings']:
    print(f"\nWarnings:")
    for warning in eligibility['warnings']:
        print(f"  ⚠ {warning}")

# Output:
# Eligible: True
#
# Reasons:
#   ✓ Parcel has eligible commercial zoning: C-2
#   ✓ Corridor classified as: Tier 2 - Major Transit Corridor
#   ✓ State minimum floors: 50.0 u/ac density, 45.0 ft height
#   ✓ Site is not in coastal high hazard zone
#   ✓ No rent-controlled units on parcel
#   ✓ Prevailing wage commitment confirmed (REQUIRED for all AB 2011)
```

---

## 3. Check Individual Components

### Corridor Eligibility

```python
from app.rules.ab2011 import check_corridor_eligibility

corridor = check_corridor_eligibility(parcel)

print(f"Is Corridor: {corridor['is_corridor']}")
print(f"Tier: {corridor['tier']}")
print(f"Tier Name: {corridor['tier_name']}")
print(f"State Floors: {corridor['state_floors']}")

# Output:
# Is Corridor: True
# Tier: mid
# Tier Name: Tier 2 - Major Transit Corridor
# State Floors: {'min_density_u_ac': 50.0, 'min_height_ft': 45.0}
```

### Site Exclusions

```python
from app.rules.ab2011 import check_site_exclusions

exclusions = check_site_exclusions(parcel)

if exclusions['excluded']:
    print("Parcel is excluded due to:")
    for reason in exclusions['exclusion_reasons']:
        print(f"  - {reason}")
else:
    print("Parcel passes site exclusion checks")
    for check in exclusions['passed_checks']:
        print(f"  ✓ {check}")
```

### Protected Housing

```python
from app.rules.ab2011 import check_protected_housing

housing = check_protected_housing(parcel)

if housing['protected']:
    print("Parcel has protected housing:")
    for reason in housing['protection_reasons']:
        print(f"  - {reason}")
else:
    print("No protected housing issues")
```

### Labor Standards

```python
from app.rules.ab2011 import check_labor_compliance

labor = check_labor_compliance(parcel, project_units=50)

if labor['compliant']:
    print("Labor standards are met:")
    for req in labor['met_requirements']:
        print(f"  ✓ {req}")
else:
    print("Labor standards NOT met:")
    for req in labor['missing_requirements']:
        print(f"  ✗ {req}")

print(f"\nSkilled workforce required: {labor['skilled_workforce_required']}")
```

---

## 4. Generate Development Scenario

```python
from app.rules.ab2011 import analyze_ab2011

# Generate single scenario (mixed-income track)
scenario = analyze_ab2011(parcel)

if scenario:
    print(f"Scenario: {scenario.scenario_name}")
    print(f"Legal Basis: {scenario.legal_basis}")
    print(f"Max Units: {scenario.max_units}")
    print(f"Max Height: {scenario.max_height_ft} ft")
    print(f"Max Stories: {scenario.max_stories}")
    print(f"Parking Required: {scenario.parking_spaces_required}")
    print(f"Affordable Units: {scenario.affordable_units_required}")
    print(f"\nNotes:")
    for note in scenario.notes:
        print(f"  - {note}")
else:
    print("Parcel is not eligible - no scenario generated")

# Output:
# Scenario: AB2011 Corridor Housing
# Legal Basis: AB2011 (2022) - Corridor Multifamily (Mixed-Income)
# Max Units: 17
# Max Height: 45.0 ft
# Max Stories: 4
# Parking Required: 0  # (if near transit)
# Affordable Units: 3
```

---

## 5. Generate Both Tracks (Mixed-Income + 100% Affordable)

```python
from app.rules.ab2011 import analyze_ab2011_tracks

# Generate both scenarios
scenarios = analyze_ab2011_tracks(parcel)

for scenario in scenarios:
    print(f"\n{scenario.scenario_name}")
    print(f"  Units: {scenario.max_units}")
    print(f"  Affordable: {scenario.affordable_units_required}")
    print(f"  Parking: {scenario.parking_spaces_required}")

# Output:
# AB2011 Corridor Housing (Mixed-Income)
#   Units: 17
#   Affordable: 3 (15%)
#   Parking: 0
#
# AB2011 Corridor Housing (100% Affordable)
#   Units: 17
#   Affordable: 17 (100%)
#   Parking: 0
```

---

## 6. Example: Ineligible Parcel (Residential Zoning)

```python
# Residential parcel - not eligible
residential_parcel = ParcelBase(
    apn="5299-012-999",
    address="456 Residential Ave",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=10000.0,
    zoning_code="R-1",  # RESIDENTIAL - not eligible
    existing_units=1,
    existing_building_sqft=2000.0,
    prevailing_wage_commitment=True,
)

eligibility = can_apply_ab2011(residential_parcel)

print(f"Eligible: {eligibility['eligible']}")
print(f"\nExclusions:")
for exclusion in eligibility['exclusions']:
    print(f"  ✗ {exclusion}")

# Output:
# Eligible: False
#
# Exclusions:
#   ✗ Parcel is not on an eligible AB 2011 corridor
#   ✗ Parcel is not zoned for commercial/office/mixed-use
```

---

## 7. Example: Excluded Parcel (Protected Housing)

```python
# Commercial parcel with rent-controlled units
protected_parcel = ParcelBase(
    apn="5299-012-888",
    address="789 Main Street",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=15000.0,
    zoning_code="C-2",  # Commercial - eligible
    existing_units=10,
    existing_building_sqft=8000.0,
    prevailing_wage_commitment=True,
    has_rent_controlled_units=True,  # PROTECTED
)

eligibility = can_apply_ab2011(protected_parcel)

print(f"Eligible: {eligibility['eligible']}")
print(f"\nExclusions:")
for exclusion in eligibility['exclusions']:
    print(f"  ✗ {exclusion}")

# Output:
# Eligible: False
#
# Exclusions:
#   ✗ EXCLUDED: Parcel contains rent-controlled units (AB 2011 protection)
```

---

## 8. Example: Missing Labor Standards

```python
# Commercial parcel without prevailing wage commitment
no_labor_parcel = ParcelBase(
    apn="5299-012-777",
    address="321 Office Blvd",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=20000.0,
    zoning_code="OFFICE",  # Commercial - eligible
    existing_units=0,
    existing_building_sqft=15000.0,
    prevailing_wage_commitment=False,  # MISSING - REQUIRED
)

eligibility = can_apply_ab2011(no_labor_parcel)

print(f"Eligible: {eligibility['eligible']}")
print(f"\nExclusions:")
for exclusion in eligibility['exclusions']:
    print(f"  ✗ {exclusion}")

# Output:
# Eligible: False
#
# Exclusions:
#   ✗ REQUIRED: Prevailing wage commitment missing - MANDATORY for all AB 2011 projects
```

---

## 9. Example: Large Project (Skilled Workforce Required)

```python
# Large commercial parcel - skilled workforce required
large_parcel = ParcelBase(
    apn="5299-012-666",
    address="555 Regional Plaza",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=87120.0,  # 2 acres
    zoning_code="C-3",  # High-tier corridor
    existing_units=0,
    existing_building_sqft=30000.0,
    prevailing_wage_commitment=True,
    skilled_trained_workforce_commitment=True,  # REQUIRED for 50+ units
)

# Check labor compliance
labor = check_labor_compliance(large_parcel, project_units=160)

print(f"Compliant: {labor['compliant']}")
print(f"Skilled workforce required: {labor['skilled_workforce_required']}")
print(f"\nMet Requirements:")
for req in labor['met_requirements']:
    print(f"  ✓ {req}")

# Output:
# Compliant: True
# Skilled workforce required: True
#
# Met Requirements:
#   ✓ Prevailing wage commitment confirmed (REQUIRED for all AB 2011)
#   ✓ Skilled & trained workforce commitment confirmed (REQUIRED for 160 units >= 50)
```

---

## 10. Example: Coastal Zone Parcel

```python
# Parcel in coastal zone
coastal_parcel = ParcelBase(
    apn="5299-012-555",
    address="100 Ocean Avenue",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=12000.0,
    zoning_code="C-2",
    existing_units=0,
    existing_building_sqft=6000.0,
    prevailing_wage_commitment=True,
    in_coastal_zone=True,  # Coastal zone flag
    near_transit=True,
)

scenario = analyze_ab2011(coastal_parcel)

if scenario:
    print(f"Scenario: {scenario.scenario_name}")
    print(f"\nCoastal Zone Notes:")
    for note in scenario.notes:
        if "COASTAL" in note or "CDP" in note or "LCP" in note:
            print(f"  - {note}")

# Output:
# Scenario: AB2011 Corridor Housing
#
# Coastal Zone Notes:
#   - COASTAL ZONE REQUIREMENTS:
#   - Parcel is in California Coastal Zone
#   - Coastal Development Permit (CDP) may be required
#   - Must comply with Local Coastal Program (LCP)
#   - Coordinate with California Coastal Commission
```

---

## 11. Example: Near Transit (AB 2097 Parking Elimination)

```python
# Parcel near major transit
transit_parcel = ParcelBase(
    apn="5299-012-444",
    address="200 Transit Circle",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=10000.0,
    zoning_code="C-2",
    existing_units=0,
    existing_building_sqft=5000.0,
    prevailing_wage_commitment=True,
    near_transit=True,  # Within 0.5 miles of major transit
)

scenario = analyze_ab2011(transit_parcel)

if scenario:
    print(f"Parking Required: {scenario.parking_spaces_required}")
    print(f"\nParking Notes:")
    for note in scenario.notes:
        if "AB2097" in note or "parking" in note.lower():
            print(f"  - {note}")

# Output:
# Parking Required: 0
#
# Parking Notes:
#   - AB2097: Parking requirement reduced from 5 to 0 spaces due to proximity to major transit (within 0.5 miles)
```

---

## 12. Tier-Based Density Calculations

```python
from app.rules.ab2011 import apply_ab2011_standards

# Low tier (C-1): 30 u/ac, 35 ft
low_tier_parcel = ParcelBase(
    apn="LOW-TIER",
    address="Low Tier Street",
    city="Santa Monica",
    county="Los Angeles",
    zip_code="90401",
    lot_size_sqft=43560.0,  # 1 acre
    zoning_code="C-1",
    existing_units=0,
    existing_building_sqft=5000.0,
)

standards_low = apply_ab2011_standards(low_tier_parcel, tier="low")
print(f"Low Tier (1 acre):")
print(f"  Minimum Units: {standards_low['final_min_units']}")
print(f"  Minimum Height: {standards_low['final_min_height_ft']} ft")

# Mid tier (C-2): 50 u/ac, 45 ft
standards_mid = apply_ab2011_standards(low_tier_parcel, tier="mid")
print(f"\nMid Tier (1 acre):")
print(f"  Minimum Units: {standards_mid['final_min_units']}")
print(f"  Minimum Height: {standards_mid['final_min_height_ft']} ft")

# High tier (C-3): 80 u/ac, 65 ft
standards_high = apply_ab2011_standards(low_tier_parcel, tier="high")
print(f"\nHigh Tier (1 acre):")
print(f"  Minimum Units: {standards_high['final_min_units']}")
print(f"  Minimum Height: {standards_high['final_min_height_ft']} ft")

# Output:
# Low Tier (1 acre):
#   Minimum Units: 30
#   Minimum Height: 35.0 ft
#
# Mid Tier (1 acre):
#   Minimum Units: 50
#   Minimum Height: 45.0 ft
#
# High Tier (1 acre):
#   Minimum Units: 80
#   Minimum Height: 65.0 ft
```

---

## 13. Batch Processing Multiple Parcels

```python
from typing import List
from app.models.parcel import ParcelBase
from app.rules.ab2011 import can_apply_ab2011, analyze_ab2011

def analyze_parcels_batch(parcels: List[ParcelBase]):
    """Analyze multiple parcels for AB 2011 eligibility."""
    results = []

    for parcel in parcels:
        eligibility = can_apply_ab2011(parcel)
        scenario = analyze_ab2011(parcel) if eligibility['eligible'] else None

        results.append({
            'apn': parcel.apn,
            'address': parcel.address,
            'eligible': eligibility['eligible'],
            'scenario': scenario,
            'exclusions': eligibility['exclusions'] if not eligibility['eligible'] else []
        })

    return results

# Process batch
parcels = [parcel1, parcel2, parcel3, ...]
results = analyze_parcels_batch(parcels)

# Print summary
eligible_count = sum(1 for r in results if r['eligible'])
print(f"Total Parcels: {len(results)}")
print(f"Eligible: {eligible_count}")
print(f"Ineligible: {len(results) - eligible_count}")
```

---

## Common Field Values Reference

### Required for ALL Parcels
```python
apn: str                      # "5299-012-034"
address: str                  # "1234 Main Street"
city: str                     # "Santa Monica"
county: str                   # "Los Angeles"
zip_code: str                 # "90401"
lot_size_sqft: float          # 15000.0
zoning_code: str              # "C-1", "C-2", "C-3", "OFFICE", "MIXED-USE"
existing_units: int           # 0
existing_building_sqft: float # 8000.0
```

### Eligibility Flags (Optional but Important)
```python
# Labor Standards (REQUIRED for eligibility)
prevailing_wage_commitment: bool = True
skilled_trained_workforce_commitment: bool = True  # If 50+ units
healthcare_benefits_commitment: bool = False  # Recommended

# Site Exclusions (False = not excluded)
in_coastal_high_hazard: bool = False
in_prime_farmland: bool = False
in_wetlands: bool = False
in_conservation_area: bool = False
is_historic_property: bool = False
in_flood_zone: bool = False
in_coastal_zone: bool = False

# Protected Housing (False = not protected)
has_rent_controlled_units: bool = False
has_deed_restricted_affordable: bool = False
has_ellis_act_units: bool = False
has_recent_tenancy: bool = False
protected_units_count: int = 0

# AB 2097 Integration
near_transit: bool = True  # Within 0.5 miles of major transit
```

---

## Error Handling Best Practices

```python
from app.rules.ab2011 import can_apply_ab2011, analyze_ab2011

try:
    # Check eligibility first
    eligibility = can_apply_ab2011(parcel)

    if not eligibility['eligible']:
        # Handle ineligibility
        print("Parcel is not eligible for AB 2011:")
        for exclusion in eligibility['exclusions']:
            print(f"  - {exclusion}")
        return None

    # Generate scenario
    scenario = analyze_ab2011(parcel)

    if scenario is None:
        # Shouldn't happen if eligibility check passed, but handle it
        print("Warning: Eligibility passed but scenario generation failed")
        return None

    # Process scenario
    return scenario

except Exception as e:
    print(f"Error analyzing parcel {parcel.apn}: {e}")
    return None
```

---

## Integration with API Endpoint Example

```python
from fastapi import APIRouter, HTTPException
from app.models.parcel import ParcelBase
from app.models.analysis import DevelopmentScenario
from app.rules.ab2011 import can_apply_ab2011, analyze_ab2011_tracks

router = APIRouter()

@router.post("/analyze/ab2011")
def analyze_ab2011_endpoint(parcel: ParcelBase) -> dict:
    """
    Analyze parcel for AB 2011 eligibility and generate scenarios.

    Returns both eligibility details and development scenarios (if eligible).
    """
    # Check eligibility
    eligibility = can_apply_ab2011(parcel)

    # Generate scenarios if eligible
    scenarios = []
    if eligibility['eligible']:
        scenarios = analyze_ab2011_tracks(parcel)

    return {
        "eligibility": {
            "eligible": eligibility['eligible'],
            "reasons": eligibility['reasons'],
            "exclusions": eligibility['exclusions'],
            "warnings": eligibility['warnings'],
            "corridor_tier": eligibility['corridor_info']['tier'],
            "corridor_tier_name": eligibility['corridor_info']['tier_name'],
        },
        "scenarios": [s.dict() for s in scenarios],
        "scenario_count": len(scenarios)
    }
```

---

**For more information, see:**
- Implementation Report: `AB2011_IMPLEMENTATION_REPORT.md`
- Test Suite: `tests/test_ab2011_eligibility.py`
- Source Code: `app/rules/ab2011.py`
