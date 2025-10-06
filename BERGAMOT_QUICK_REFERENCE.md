# Bergamot Area Plan - Quick Reference Guide

## Overview
The Bergamot Area Plan provides tiered development standards across three districts near the Expo Line light rail station.

## Districts

### Transit Village (BTV)
**Character:** High-density, transit-oriented, pedestrian-focused
**Location:** Near Expo Line station

| Tier | FAR | Height | Notes |
|------|-----|--------|-------|
| 1 | 1.75 | 32 ft | Base as-of-right |
| 2 | 2.0 | 60 ft | Requires community benefits |
| 3 | 2.5 | 75 ft | Requires Development Agreement |

**Setbacks:** Front 5', Rear 10', Side 5'
**Lot Coverage:** 80%

### Mixed-Use Creative (MUC)
**Character:** Arts, creative offices, production space
**Location:** Creative corridor area

| Tier | FAR | Height | Notes |
|------|-----|--------|-------|
| 1 | 1.5 | 32 ft | Base as-of-right |
| 2 | 1.7 | 47 ft | Requires community benefits |
| 3 | 2.2 | 57 ft | Requires Development Agreement |

**Setbacks:** Front 5', Rear 10', Side 5'
**Lot Coverage:** 80%

### Conservation Art Center (CAC)
**Character:** Arts/cultural uses, museum-quality
**Location:** Cultural district

**Size Threshold:** 100,000 sqft

#### Large Sites (≥100,000 sqft)
*Typically city-owned properties*

| Tier | FAR | Height | Notes |
|------|-----|--------|-------|
| 1 | 1.0 | 32 ft | Base standards |
| 2 | 1.0 | 60 ft | Height for cultural facilities |
| 3 | 1.0 | 75 ft | Maximum height |

#### Small Sites (<100,000 sqft)
*Private properties*

| Tier | FAR | Height | Notes |
|------|-----|--------|-------|
| 1 | 1.0 | 32 ft | Base standards |
| 2 | 1.5 | 60 ft | Enhanced FAR |
| 3 | 2.5 | 86 ft | **Exceptional standards** |

**Setbacks:** Front 10', Rear 15', Side 10' (more spacious than BTV/MUC)
**Lot Coverage:** 60% (more open space)

## Parking Requirements

| Tier | Spaces per Unit | Reduction from Tier 1 |
|------|----------------|----------------------|
| 1 | 1.0 | Baseline |
| 2 | 0.75 | -25% |
| 3 | 0.5 | -50% |

*Further reductions may apply via AB2097 if near transit*

## Community Benefits

### Tier 1
- **Required:** None (as-of-right development)
- **Approval:** Administrative

### Tier 2
- **Required:** One or more community benefits
- **Typical Options:**
  - 15-20% affordable housing
  - Public art/cultural space
  - Enhanced sustainability (LEED Silver+)
- **Approval:** Community Development Director

### Tier 3
- **Required:** Multiple substantial community benefits
- **Typical Package:**
  - 25%+ affordable housing
  - Public art/cultural space
  - Sustainability features (LEED Gold+)
  - Enhanced design/public realm
- **Approval:** Planning Commission + Development Agreement

## Unit Estimation Formula

```
Tier 1: max_building_sqft / 1,000 sqft per unit
Tier 2: max_building_sqft / 950 sqft per unit
Tier 3: max_building_sqft / 900 sqft per unit
```

## Special Provisions

### Buildings Over 90 Feet
- Additional design review required
- Enhanced massing/articulation standards
- Shadow studies

### All Tiers
- **Maximum Podium Height:** 35 feet
- **Expo Line Integration:** Required connectivity and access
- **Ground Floor:** Active uses encouraged
- **Sustainability:** Enhanced standards expected

## Legal Citations

- **SMMC Chapter 9.04.090** - Bergamot definitions
- **SMMC Chapter 9.12** - Bergamot Area Plan regulations
- **SMMC § 9.12.030 Table A/B** - Development standards
- **SMMC § 9.23.030** - Community Benefits requirements
- **Bergamot Area Plan** - Adopted 9/2013, amended 10/2023

## Code Usage

### Check if Parcel is in Bergamot
```python
from app.rules.bergamot_scenarios import is_in_bergamot_area

if is_in_bergamot_area(parcel):
    # Parcel qualifies for Bergamot standards
```

### Get District
```python
from app.rules.bergamot_scenarios import get_bergamot_district

district = get_bergamot_district(parcel)  # Returns 'BTV', 'MUC', 'CAC', or None
```

### Generate All Scenarios
```python
from app.rules.bergamot_scenarios import generate_all_bergamot_scenarios

scenarios = generate_all_bergamot_scenarios(parcel)
# Returns list of 3 DevelopmentScenario objects (Tier 1, 2, 3)
```

### Generate Specific Tier
```python
from app.rules.bergamot_scenarios import (
    create_bergamot_tier_1_scenario,
    create_bergamot_tier_2_scenario,
    create_bergamot_tier_3_scenario
)

tier_1 = create_bergamot_tier_1_scenario(parcel, 'BTV')
tier_2 = create_bergamot_tier_2_scenario(parcel, 'BTV')
tier_3 = create_bergamot_tier_3_scenario(parcel, 'BTV')
```

## Example Output

For a 25,000 sqft BTV parcel:

| Tier | Units | Building SF | Parking | Community Benefits |
|------|-------|-------------|---------|-------------------|
| 1 | 43 | 43,750 | 43 spaces | None required |
| 2 | 52 | 50,000 | 39 spaces | Required |
| 3 | 69 | 62,500 | 34 spaces | Substantial required |

## FAR Comparison Chart

For 10,000 sqft lot:

```
                 Tier 1    Tier 2    Tier 3
BTV             1.75      2.0       2.5
MUC             1.5       1.7       2.2
CAC (Small)     1.0       1.5       2.5 ⭐
CAC (Large)     1.0       1.0       1.0
```

⭐ CAC small sites get exceptional FAR 2.5 at Tier 3

## Height Comparison Chart

For 10,000 sqft lot:

```
                 Tier 1    Tier 2    Tier 3
BTV             32 ft     60 ft     75 ft
MUC             32 ft     47 ft     57 ft
CAC (Small)     32 ft     60 ft     86 ft ⭐
CAC (Large)     32 ft     60 ft     75 ft
```

⭐ CAC small sites get exceptional 86 ft at Tier 3

## District Selection Guide

**Choose BTV if:**
- Maximum density desired
- Near Expo Line station
- Transit-oriented development focus

**Choose MUC if:**
- Creative/arts programming
- Flexible mixed-use
- Moderate density

**Choose CAC if:**
- Cultural/arts focus
- Museum-quality character
- More open space required
- (Small sites get exceptional Tier 3)

## Integration with Other Programs

### State Density Bonus
Bergamot tiers can stack with State Density Bonus for additional units/height

### AB2097
Near-transit parcels get additional parking reductions beyond tier reductions

### Community Benefits
Some community benefits may satisfy both Bergamot tier requirements and density bonus affordable housing requirements

## Testing

Run tests:
```bash
# Unit tests
python test_bergamot_scenarios.py

# Integration tests
python test_bergamot_integration.py

# Examples
python example_bergamot_usage.py
```

## Files

- **Core Module:** `app/rules/bergamot_scenarios.py`
- **Standards:** `app/rules/tiered_standards.py`
- **Integration:** `app/api/analyze.py` (lines 201-214)
- **Tests:** `test_bergamot_scenarios.py`
- **Integration Tests:** `test_bergamot_integration.py`
- **Examples:** `example_bergamot_usage.py`
- **Documentation:** `BERGAMOT_IMPLEMENTATION_SUMMARY.md`

## Contact

For questions about:
- **Code implementation:** See `app/rules/bergamot_scenarios.py`
- **Standards:** See `app/rules/tiered_standards.py` (lines 56-95)
- **Legal requirements:** Consult Santa Monica Planning Division (310) 458-8341
- **Community benefits:** See SMMC § 9.23.030

---

*Last updated: October 2025*
*Based on: Bergamot Area Plan (2013, amended 2023)*
