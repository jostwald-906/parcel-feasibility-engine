# Bergamot Area Plan Scenarios - Implementation Summary

## Overview
Successfully implemented the Bergamot Area Plan scenarios module following the DCP pattern. The module generates tiered development scenarios for parcels within Santa Monica's Bergamot Area Plan boundaries across three districts: Transit Village (BTV), Mixed-Use Creative (MUC), and Conservation Art Center (CAC).

## Files Created

### 1. Core Module
**Path:** `/Users/Jordan_Ostwald/Parcel Feasibility Engine/app/rules/bergamot_scenarios.py`

**Functions Implemented:**
- `is_in_bergamot_area(parcel)` - Checks if parcel is within Bergamot boundaries
- `get_bergamot_district(parcel)` - Returns district code (BTV, MUC, or CAC)
- `create_bergamot_tier_1_scenario(parcel, district)` - Tier 1 base standards
- `create_bergamot_tier_2_scenario(parcel, district)` - Tier 2 with community benefits
- `create_bergamot_tier_3_scenario(parcel, district)` - Tier 3 maximum standards
- `generate_all_bergamot_scenarios(parcel)` - Generate all applicable scenarios
- `get_current_bergamot_tier(parcel)` - Determine current tier designation

### 2. API Integration
**Path:** `/Users/Jordan_Ostwald/Parcel Feasibility Engine/app/api/analyze.py`

**Changes:**
- Imported `is_in_bergamot_area` and `generate_all_bergamot_scenarios`
- Added Bergamot check after AB2011 analysis (line 201-214)
- Adds "Bergamot Area Plan (SMMC Chapter 9.12)" to applicable laws
- Adds "Bergamot tiered development standards" to potential incentives

### 3. Test Suite
**Path:** `/Users/Jordan_Ostwald/Parcel Feasibility Engine/test_bergamot_scenarios.py`

**Tests:**
- BTV district scenario generation
- MUC district scenario generation
- CAC small site (<100,000 sqft) scenario generation
- CAC large site (≥100,000 sqft) scenario generation
- Cross-district tier comparison table
- Edge cases (non-Bergamot parcels, threshold boundaries)

### 4. Integration Tests
**Path:** `/Users/Jordan_Ostwald/Parcel Feasibility Engine/test_bergamot_integration.py`

**Tests:**
- Full API analysis for BTV parcels
- CAC small site exceptional standards verification
- Non-Bergamot parcel filtering

## Implementation Details

### District Standards Summary

#### Transit Village (BTV)
- **Purpose:** Pedestrian-oriented transit hub near Expo Line
- **Tier 1:** FAR 1.75, Height 32 ft
- **Tier 2:** FAR 2.0, Height 60 ft (requires community benefits)
- **Tier 3:** FAR 2.5, Height 75 ft (requires substantial benefits)
- **Setbacks:** Front 5', Rear 10', Side 5'
- **Lot Coverage:** 80%

#### Mixed-Use Creative (MUC)
- **Purpose:** Arts, creative offices, and production space
- **Tier 1:** FAR 1.5, Height 32 ft
- **Tier 2:** FAR 1.7, Height 47 ft (requires community benefits)
- **Tier 3:** FAR 2.2, Height 57 ft (requires substantial benefits)
- **Setbacks:** Front 5', Rear 10', Side 5'
- **Lot Coverage:** 80%

#### Conservation Art Center (CAC)
- **Purpose:** Arts and cultural uses, museum-quality character
- **Size Threshold:** 100,000 sqft divides large/small sites

**Large Sites (≥100,000 sqft):**
- **Tier 1:** FAR 1.0, Height 32 ft
- **Tier 2:** FAR 1.0, Height 60 ft
- **Tier 3:** FAR 1.0, Height 75 ft
- Note: FAR constant, height increases for cultural facilities

**Small Sites (<100,000 sqft):**
- **Tier 1:** FAR 1.0, Height 32 ft
- **Tier 2:** FAR 1.5, Height 60 ft
- **Tier 3:** FAR 2.5, Height 86 ft (exceptional standards)

**Special Characteristics:**
- **Setbacks:** Front 10', Rear 15', Side 10' (more spacious)
- **Lot Coverage:** 60% (more open space)

### Unit Estimation
Following DCP pattern:
- **Tier 1:** 1,000 sqft/unit
- **Tier 2:** 950 sqft/unit
- **Tier 3:** 900 sqft/unit

### Parking Requirements
Progressive reduction by tier:
- **Tier 1:** 1.0 spaces/unit (standard)
- **Tier 2:** 0.75 spaces/unit (reduced)
- **Tier 3:** 0.5 spaces/unit (minimal)

### Community Benefits
- **Tier 1:** NOT required (base as-of-right)
- **Tier 2:** Required (typically 15-20% affordable housing OR public art/cultural space)
- **Tier 3:** Substantial benefits required (typically 25%+ affordable + public art + sustainability)

### Legal Citations
All scenarios include proper CITE references:
- SMMC Chapter 9.04.090 (Bergamot definitions)
- SMMC Chapter 9.12 (Bergamot Area Plan)
- Bergamot Area Plan (adopted September 2013, amended October 2023)
- SMMC § 9.23.030 (Community Benefits)

## Test Results

### Unit Test Results (test_bergamot_scenarios.py)

**Test 1: BTV District (25,000 sqft lot)**
- ✓ Generated 3 scenarios (Tier 1-3)
- ✓ Tier 1: 43 units, FAR 1.75, 32 ft
- ✓ Tier 2: 52 units, FAR 2.0, 60 ft
- ✓ Tier 3: 69 units, FAR 2.5, 75 ft

**Test 2: MUC District (15,000 sqft lot)**
- ✓ Generated 3 scenarios (Tier 1-3)
- ✓ Correct parking ratios: 1.0 → 0.73 → 0.5

**Test 3: CAC Small Site (50,000 sqft)**
- ✓ Correctly identified as small site
- ✓ Tier 3 exceptional standards: FAR 2.5, Height 86 ft
- ✓ Proper setbacks for CAC character

**Test 4: CAC Large Site (125,000 sqft)**
- ✓ Correctly identified as large site
- ✓ Constant FAR 1.0 across all tiers
- ✓ Height increases by tier (32 → 60 → 75 ft)

**Test 5: Cross-District Comparison**
- ✓ All districts generated correct standards
- ✓ Tier progression consistent across districts

**Test 6: Edge Cases**
- ✓ Non-Bergamot parcel: 0 scenarios
- ✓ Bergamot overlay without district code: 0 scenarios
- ✓ CAC exactly at 100,000 sqft: Treated as large site
- ✓ CAC at 99,999 sqft: Treated as small site

### Integration Test Results (test_bergamot_integration.py)

**Test 1: BTV via Analysis API**
- ✓ 3 Bergamot scenarios generated
- ✓ "Bergamot Area Plan (SMMC Chapter 9.12)" in applicable_laws
- ✓ "Bergamot tiered development standards" in potential_incentives

**Test 2: CAC Small Site via Analysis API**
- ✓ Tier 3 FAR correctly 2.5
- ✓ Tier 3 height correctly 86 ft
- ✓ Exceptional standards properly applied

**Test 3: Non-Bergamot Parcel**
- ✓ No Bergamot scenarios generated
- ✓ Bergamot not in applicable laws

## Key Features

### 1. District Detection
The module intelligently detects Bergamot parcels through:
- Zoning codes starting with 'BTV', 'MUC', or 'CAC'
- Overlay codes containing 'BERGAMOT'

### 2. Size-Based CAC Variants
Automatically applies correct CAC standards based on lot size:
```python
is_large_site = parcel.lot_size_sqft >= 100000
tier_key = f'{tier_num}_large' if is_large_site else f'{tier_num}_small'
```

### 3. District-Specific Character
Each district has appropriate:
- Setbacks (BTV/MUC: urban, CAC: spacious)
- Lot coverage (BTV/MUC: 80%, CAC: 60%)
- Notes reflecting district goals

### 4. Progressive Tier Benefits
Clear progression from Tier 1 → 2 → 3:
- Increasing FAR and height
- Decreasing parking requirements
- Escalating community benefit requirements

### 5. Comprehensive Notes
Each scenario includes:
- FAR and height specifications
- Community benefit requirements
- District-specific provisions
- Bergamot Area Plan goals
- Special design requirements (podium height, Expo integration)

## Sample Output

For a 25,000 sqft BTV parcel:

```
Bergamot Tier 1 (BTV)
- Legal Basis: SMMC Chapter 9.12 - Bergamot Area Plan Tier 1 (Transit Village)
- Max Units: 43
- Max Building: 43,750 sqft (FAR 1.75)
- Max Height: 32 ft (2 stories)
- Parking: 43 spaces (1.0 per unit)
- Notes:
  • Tier 1 base standards: FAR 1.75, Height 32.0 ft
  • Community benefits NOT required at Tier 1
  • Bergamot Area Plan emphasizes creative and arts uses
  • Enhanced sustainability and pedestrian design expected
  • Transit Village: Pedestrian-oriented design with Expo Line integration
```

## Edge Cases Handled

1. **Non-Bergamot parcels:** Returns empty scenario list
2. **Bergamot overlay without district code:** Detects area but returns empty list (no district)
3. **CAC size threshold:** Correctly handles 100,000 sqft boundary
4. **Height >90 ft:** Adds warning about additional design requirements
5. **Existing units:** Context added via `add_existing_units_context()`

## Code Quality

### Follows DCP Pattern
- Consistent function naming and structure
- Same parameter patterns
- Similar scenario construction logic
- Parallel note formatting

### Well-Documented
- Comprehensive docstrings
- CITE references throughout
- Inline comments for complex logic
- Clear variable names

### Type Safety
- Type hints on all functions
- Proper Optional returns
- Pydantic model validation

### Error Handling
- Graceful handling of missing standards
- Safe dictionary lookups
- None returns for invalid cases

## Next Steps

### Potential Enhancements

1. **GIS Integration**
   - Replace zoning code inference with actual GIS boundary checks
   - Precise district mapping from spatial data

2. **Development Agreements**
   - Add helper functions for Tier 3 DA requirements
   - Generate DA checklist based on district

3. **Community Benefits Calculator**
   - Quantify affordable housing requirements
   - Calculate public art/cultural space minimums
   - LEED certification tracking

4. **Density Bonus Stacking**
   - Combine Bergamot tiers with State Density Bonus
   - AB2011 conversion within Bergamot area

5. **Special Provisions**
   - Large site design standards (>90 ft buildings)
   - Podium height compliance checking
   - Expo Line integration requirements

## Citations & References

### Santa Monica Municipal Code
- **SMMC Chapter 9.04.090:** Bergamot district definitions
- **SMMC Chapter 9.12:** Bergamot Area Plan regulations
- **SMMC § 9.23.030:** Community Benefits requirements
- **SMMC § 9.12.030 Table A/B:** Tier-specific development standards

### Planning Documents
- **Bergamot Area Plan:** Adopted September 2013, amended October 2023
- **Downtown Community Plan:** Used as pattern/reference (July 2017)

### Related Modules
- `app/rules/tiered_standards.py` - Standards definitions
- `app/rules/dcp_scenarios.py` - Pattern template
- `app/services/community_benefits.py` - Benefits analysis

## Conclusion

The Bergamot Area Plan scenarios module has been successfully implemented and tested. It:

✅ Generates accurate scenarios for all three districts (BTV, MUC, CAC)
✅ Correctly handles size-based CAC variants
✅ Applies progressive tier standards with proper community benefit notes
✅ Integrates seamlessly with the analysis API
✅ Follows established code patterns and conventions
✅ Includes comprehensive test coverage
✅ Provides proper legal citations
✅ Handles edge cases gracefully

The module is production-ready and can be used to analyze parcels within the Bergamot Area Plan for development feasibility.
