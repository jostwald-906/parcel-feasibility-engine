# Housing Law Implementation - AI Agent Context

## Overview

This directory contains the core business logic for analyzing parcels under:
1. **Base Zoning**: Santa Monica Municipal Code zoning standards
2. **State Housing Laws**: SB 9, SB 35, AB 2011, Density Bonus Law
3. **Tier Systems**: Downtown Community Plan (DCP), Bergamot Area Plan
4. **Overlays**: Affordable Housing Overlay (AHO), Transit Overlays

**Critical**: All implementations must include **statute references** in code comments and analysis notes.

## Directory Structure

```
app/rules/
├── base_zoning.py              # Base zoning calculations (FAR, height, density)
├── tiered_standards.py         # Tier-aware FAR/height resolution
├── overlays.py                 # Overlay zone handling
├── dcp_scenarios.py            # Downtown Community Plan scenarios
├── bergamot_scenarios.py       # Bergamot Area Plan scenarios
├── proposed_validation.py      # Proposed project validation
└── state_law/                  # California housing laws
    ├── sb9.py                  # SB 9 - Lot splits & duplexes
    ├── sb35.py                 # SB 35 - Streamlined approval
    ├── ab2011.py               # AB 2011 - Affordable corridors
    ├── adu.py                  # ADU/JADU - Accessory Dwelling Units
    └── density_bonus.py        # Density Bonus Law
```

## State Housing Laws (state_law/)

### SB 9 (Gov. Code § 65852.21) - `sb9.py`

**Purpose**: Allow up to 4 units on single-family lots via lot splits and duplex development.

**Key Provisions**:
- Urban lot split: 1 parcel → 2 parcels (§ 65852.21(a)(1))
- Duplex development: Up to 2 units per parcel (§ 65852.21(a)(2))
- Combined: 2 parcels × 2 units = 4 units total
- **Exclusions**: Historic properties (§ 65852.21(j)(1)), rent-controlled units

**Implementation Pattern**:

```python
def analyze_sb9(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Analyze parcel under SB 9 (Gov. Code § 65852.21).

    Returns scenario with maximum 4 units (2 lots × 2 units).
    """
    # 1. Check eligibility (§ 65852.21(j))
    if not is_sb9_eligible(parcel):
        return None

    # 2. Lot split dimensions (§ 65852.21(a)(1))
    min_lot_size = 1200  # sq ft minimum per parcel after split

    # 3. Calculate units
    max_lots = 2
    units_per_lot = 2  # Duplex
    max_units = max_lots * units_per_lot  # = 4

    # 4. Build notes with statute references
    notes = [
        "SB 9 Urban Lot Split with Duplex Development (Gov. Code § 65852.21)",
        f"Lot split: 1 lot → {max_lots} lots (§ 65852.21(a)(1))",
        f"Units per lot: {units_per_lot} (duplex allowed under § 65852.21(a)(2))",
        f"Total potential: {max_units} units",
        "Ministerial approval required (no discretionary review)",
        "4-foot side/rear setbacks allowed (§ 65852.21(d)(1))",
    ]

    return DevelopmentScenario(
        scenario_name="SB 9 (Lot Split + Duplex)",
        legal_basis="Gov. Code § 65852.21 - Urban Lot Splits",
        max_units=max_units,
        # ... other fields
        notes=notes
    )
```

**Eligibility Check**:

```python
def is_sb9_eligible(parcel: ParcelBase) -> bool:
    """Check SB 9 eligibility per § 65852.21(j)."""

    # Must be single-family zoning
    if not is_single_family_zoning(parcel.zoning_code):
        return False

    # Cannot be historic property (§ 65852.21(j)(1))
    if parcel.is_historic_property:
        return False

    # Cannot have rent-controlled units (§ 65852.21(j)(10))
    if parcel.has_rent_controlled_units:
        return False

    # Lot must be large enough for split (minimum 2400 sq ft total)
    if parcel.lot_size_sqft < 2400:
        return False

    return True
```

### SB 35 (Gov. Code § 65913.4) - `sb35.py`

**Purpose**: Streamlined ministerial approval for multifamily projects with affordable housing.

**Key Provisions**:
- **Affordability tiers** (§ 65913.4(a)(5)):
  - 10% in high-performing cities (SF, San Jose, Sacramento)
  - 50% in other jurisdictions
- **Labor standards** (§ 65913.4(a)(8)):
  - Prevailing wage at 10+ units
  - Skilled & trained workforce at 75+ units
- **Site exclusions** (§ 65913.4(a)(6)):
  - Historic properties
  - Wetlands
  - Very high fire hazard zones
  - Coastal high hazard zones
- **CEQA exempt** (§ 65913.4(b))

**Implementation Pattern**:

```python
def analyze_sb35(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Analyze parcel under SB 35 (Gov. Code § 65913.4).

    Streamlined ministerial approval for affordable housing.
    """
    # 1. Check site exclusions (§ 65913.4(a)(6))
    if has_site_exclusions(parcel):
        return None

    # 2. Determine affordability requirement (§ 65913.4(a)(5))
    if is_high_performing_jurisdiction(parcel.city):
        affordability_pct = 10
    else:
        affordability_pct = 50

    # 3. Calculate labor requirements (§ 65913.4(a)(8))
    max_units = calculate_base_units(parcel)
    requires_prevailing_wage = max_units >= 10
    requires_skilled_workforce = max_units >= 75

    # 4. Build notes
    notes = [
        "SB 35 Streamlined Ministerial Approval (Gov. Code § 65913.4)",
        f"Affordability requirement: {affordability_pct}% (§ 65913.4(a)(5))",
        f"Labor standards (§ 65913.4(a)(8)):",
    ]

    if requires_prevailing_wage:
        notes.append("  • Prevailing wage required (10+ units)")
    if requires_skilled_workforce:
        notes.append("  • Skilled & trained workforce required (75+ units)")

    notes.extend([
        "Ministerial approval (no discretionary review)",
        "CEQA exempt (§ 65913.4(b))",
        "Must meet objective design standards",
    ])

    return DevelopmentScenario(...)
```

**Site Exclusion Check**:

```python
def has_site_exclusions(parcel: ParcelBase) -> bool:
    """
    Check SB 35 site exclusions per § 65913.4(a)(6).

    Returns True if parcel has any disqualifying conditions.
    """
    exclusions = [
        parcel.is_historic_property,
        parcel.in_wetlands,
        parcel.in_conservation_area,
        parcel.fire_hazard_zone == "Very High",
        parcel.near_hazardous_waste,
        # Coastal high hazard (coastal zone + flood zone)
        (parcel.in_coastal_zone and parcel.in_flood_zone),
    ]

    return any(exclusions)
```

### AB 2011 (Gov. Code § 65913.5) - `ab2011.py`

**Purpose**: 100% affordable housing on commercial corridors with state minimum density/height floors.

**Key Provisions**:
- **Affordability**: 100% affordable OR mixed-income per local ordinance
- **Corridor tiers** (§ 65913.5(a)(2)):
  - Narrow (70-99 ft ROW): 40 u/ac, 35 ft height
  - Wide (100-150 ft ROW): 60 u/ac, 45 ft height
  - Very wide (150+ ft ROW): 80 u/ac, 65 ft height
- **Labor standards** (§ 65913.5(a)(7)):
  - Prevailing wage (all projects)
  - Skilled & trained workforce (all projects)
- **Protected housing** (§ 65913.5(h)): Cannot demolish rent-controlled or deed-restricted units

**Implementation Pattern**:

```python
def analyze_ab2011(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Analyze parcel under AB 2011 (Gov. Code § 65913.5).

    100% affordable housing on commercial corridors.
    """
    # 1. Check eligibility
    if not is_commercial_zoning(parcel.zoning_code):
        return None

    if parcel.is_historic_property:
        return None

    if has_protected_housing(parcel):
        return None

    # 2. Determine corridor tier (§ 65913.5(a)(2))
    if parcel.street_row_width:
        if parcel.street_row_width >= 150:
            tier = "very_wide"
            min_density = 80  # units per acre
            min_height = 65   # feet
        elif parcel.street_row_width >= 100:
            tier = "wide"
            min_density = 60
            min_height = 45
        elif parcel.street_row_width >= 70:
            tier = "narrow"
            min_density = 40
            min_height = 35
        else:
            # Below 70 ft - not eligible for AB 2011 corridors
            return None
    else:
        # Default to narrow if unknown
        tier = "narrow"
        min_density = 40
        min_height = 35

    # 3. Calculate units from state minimum density
    acres = parcel.lot_size_sqft / 43560
    state_minimum_units = int(acres * min_density)

    # 4. Apply local standards (cannot go below state minimum)
    local_max_units = calculate_base_units(parcel)
    max_units = max(state_minimum_units, local_max_units)

    # 5. Build notes with statute references
    notes = [
        "AB 2011 Affordable Housing Corridors (Gov. Code § 65913.5)",
        f"Corridor tier: {tier.title()} (ROW: {parcel.street_row_width or 'estimated'} ft)",
        f"State minimum density (§ 65913.5(a)(2)): {min_density} units/acre = {state_minimum_units} units",
        f"State minimum height: {min_height} feet",
        f"Actual max units: {max_units} (greater of local or state minimum)",
        "Labor requirements (§ 65913.5(a)(7)):",
        "  • Prevailing wage required",
        "  • Skilled & trained workforce required",
        "Affordability: 100% affordable OR mixed-income per local ordinance",
        "Ministerial approval - no discretionary review",
    ]

    return DevelopmentScenario(
        scenario_name=f"AB 2011 ({tier.title()} Corridor)",
        legal_basis="Gov. Code § 65913.5 - Affordable Housing Corridors",
        max_units=max_units,
        max_height_ft=max(min_height, calculate_base_height(parcel)),
        # ...
        notes=notes
    )
```

**Corridor Width Estimation**:

```python
# If street ROW width not provided, estimate from street classification
def estimate_row_width(street_classification: str) -> float:
    """Estimate right-of-way width from street classification."""
    classifications = {
        "arterial": 100.0,      # Wide corridor
        "collector": 80.0,      # Narrow corridor
        "local": 60.0,          # Below AB 2011 threshold
        "boulevard": 120.0,     # Wide corridor
    }
    return classifications.get(street_classification.lower(), 70.0)
```

### Density Bonus Law (Gov. Code § 65915) - `density_bonus.py`

**Purpose**: Provide density bonuses and concessions for projects with affordable housing.

**Key Provisions**:
- **Density bonuses** (§ 65915(f)):
  - 5% very low income → 20% bonus
  - 10% very low → 35% bonus, 10% low → 20% bonus
  - 15% very low → 50% bonus, 17% low → 35% bonus
  - 100% affordable → 80% bonus
- **Concessions** (§ 65915(d)): 1-4 concessions based on affordability
  - 10% affordable → 1 concession
  - 20% → 2 concessions
  - 30% → 3 concessions
  - 100% → 4 concessions (§ 65915(d)(2)(D))
- **Waivers** (§ 65915(e)): Unlimited if standard prevents construction
- **Parking** (§ 65915(p)): Bedroom-based + income-based caps
- **AB 2097** (§ 65915.1): Near-transit parking elimination

**Implementation Pattern**:

```python
def apply_density_bonus(
    base_scenario: DevelopmentScenario,
    parcel: ParcelBase,
    affordability_pct: float = 10.0,
    income_level: str = "low"
) -> Optional[DevelopmentScenario]:
    """
    Apply State Density Bonus Law (Gov. Code § 65915).

    Args:
        base_scenario: Base zoning scenario
        parcel: Parcel information
        affordability_pct: Percentage of affordable units
        income_level: "very_low", "low", or "moderate"

    Returns:
        Enhanced scenario with density bonus and concessions
    """
    # 1. Calculate density bonus percentage (§ 65915(f))
    bonus_pct = calculate_density_bonus_percentage(affordability_pct, income_level)
    if bonus_pct == 0:
        return None

    # 2. Apply density bonus
    base_units = base_scenario.max_units
    bonus_units = int(base_units * (bonus_pct / 100.0))
    max_units = base_units + bonus_units

    # 3. Calculate concessions (§ 65915(d))
    num_concessions = calculate_concessions(affordability_pct)

    # 4. Apply concessions
    concessions_applied = []

    if num_concessions >= 1:
        # Concession 1: Height increase (§ 65915(d)(2)(B))
        # Up to 33 feet or 3 stories
        max_height_ft = min(
            base_scenario.max_height_ft + 33,
            base_scenario.max_height_ft * 1.5
        )
        concessions_applied.append(f"Height increase to {max_height_ft:.0f} ft")

    if num_concessions >= 2:
        # Concession 2: Parking reduction (§ 65915(p))
        parking_reduction = 0.5  # 50%
        concessions_applied.append("Parking reduction by 50%")

    if num_concessions >= 3:
        # Concession 3: Setback reduction (§ 65915(d))
        setback_reduction = 0.2  # 20%
        concessions_applied.append("Setback reduction by 20%")

    if num_concessions >= 4:
        # Fourth concession for 100% affordable (§ 65915(d)(2)(D))
        far_increase = 0.25
        concessions_applied.append(f"Fourth concession: +{far_increase} FAR, +15 ft height")

    # 5. Calculate parking (§ 65915(p) + AB 2097)
    if parcel.near_transit:
        # AB 2097: Near-transit parking elimination (§ 65915.1)
        parking_spaces_required = 0
    else:
        # Bedroom-based caps (§ 65915(p)(1))
        if parcel.avg_bedrooms_per_unit:
            if parcel.avg_bedrooms_per_unit <= 1:
                bedroom_cap = 1.0
            elif parcel.avg_bedrooms_per_unit <= 3:
                bedroom_cap = 2.0
            else:
                bedroom_cap = 2.5
        else:
            bedroom_cap = 1.5

        # Income-based caps
        if income_level == "very_low" or affordability_pct >= 20:
            income_cap = 0.5
        elif income_level in ("low", "moderate"):
            income_cap = 1.0
        else:
            income_cap = 1.5

        # Take minimum of all caps
        parking_per_unit = min(bedroom_cap, income_cap)

        # Apply concession reduction if applicable
        if num_concessions >= 2:
            parking_per_unit *= 0.5

        parking_spaces_required = int(max_units * parking_per_unit)

    # 6. Build detailed notes
    notes = [
        "State Density Bonus Law applied (Gov. Code § 65915)",
        f"{affordability_pct}% affordable units at {income_level} income level",
        f"Density bonus (§ 65915(f)): {bonus_pct}% = {bonus_units} additional units",
        f"Base units: {base_units} → Total units: {max_units}",
        f"Concessions granted (§ 65915(d)): {num_concessions}",
    ]

    if concessions_applied:
        notes.append("Concessions applied:")
        for i, concession in enumerate(concessions_applied, 1):
            notes.append(f"  {i}. {concession}")

    if parcel.near_transit:
        notes.append("Parking (AB 2097 § 65915.1): Near transit → 0 spaces required")
    else:
        notes.append(f"Parking (§ 65915(p)): {parking_per_unit:.2f} spaces/unit")

    notes.append("Note: Waivers (§ 65915(e)) are tracked separately from concessions.")

    return DevelopmentScenario(
        scenario_name=f"Density Bonus ({affordability_pct}% Affordable)",
        legal_basis=f"State Density Bonus Law - {bonus_pct}% density bonus",
        max_units=max_units,
        parking_spaces_required=parking_spaces_required,
        notes=notes,
        concessions_applied=concessions_applied,
        waivers_applied=[],  # Track separately
    )
```

**Density Bonus Calculation**:

```python
def calculate_density_bonus_percentage(
    affordability_pct: float,
    income_level: str
) -> float:
    """
    Calculate density bonus per § 65915(f).

    100% affordable takes precedence over income-level schedules.
    """
    # 100% affordable gets 80% bonus (§ 65915(f)(4))
    if affordability_pct >= 100:
        return 80.0

    income_level = income_level.lower().replace(" ", "_")

    if income_level == "very_low":
        # § 65915(f)(1)
        if affordability_pct >= 15:
            return 50.0
        elif affordability_pct >= 10:
            return 35.0
        elif affordability_pct >= 5:
            return 20.0

    elif income_level == "low":
        # § 65915(f)(2)
        if affordability_pct >= 24:
            return 50.0
        elif affordability_pct >= 17:
            return 35.0
        elif affordability_pct >= 10:
            return 20.0

    elif income_level == "moderate":
        # § 65915(f)(3) - for-sale only
        if affordability_pct >= 40:
            return 35.0
        elif affordability_pct >= 10:
            return 5.0

    return 0.0
```

**Concessions Calculation**:

```python
def calculate_concessions(affordability_pct: float) -> int:
    """
    Calculate concessions per § 65915(d).

    Note: Waivers under § 65915(e) are separate and unlimited.
    """
    if affordability_pct >= 100:
        return 4  # § 65915(d)(2)(D)
    elif affordability_pct >= 30:
        return 3
    elif affordability_pct >= 20:
        return 2
    elif affordability_pct >= 10:
        return 1
    else:
        return 0
```

### ADU/JADU (Gov. Code § 65852.2 & § 65852.22) - `adu.py`

**Purpose**: Enable Accessory Dwelling Units (ADUs) and Junior ADUs (JADUs) on all residential parcels.

**Key Provisions**:
- **Always eligible** on residential parcels (state law preempts local restrictions)
- **Size limits** (§ 65852.2(a)(1)):
  - Studio/1-BR: 850 sq ft
  - 2-BR: 1,000 sq ft
  - 3+ BR: 1,200 sq ft
- **JADU** (§ 65852.22): 500 sq ft max, within existing structure
- **Parking**: ZERO required (AB 68, AB 681, AB 671)
- **Setbacks**: 4 ft side/rear (new), 0 ft (conversions)
- **Height**: 16 ft (1-story), 25 ft (2-story)
- **Ministerial approval** (no discretionary review)

**Implementation Pattern**:

```python
def analyze_adu(parcel: ParcelBase) -> List[DevelopmentScenario]:
    """
    Analyze ADU/JADU eligibility and generate scenarios.

    Returns up to 4 scenarios:
    1. Detached ADU (max size based on bedrooms)
    2. Attached ADU (can match primary dwelling)
    3. JADU (500 sq ft within existing structure)
    4. Combo: ADU + JADU (both allowed per statute)
    """
    scenarios = []

    # ADUs are allowed on ALL residential parcels per state law
    # State law preempts local restrictions (§ 65852.2(a))
    if not _is_residential_zoning(parcel.zoning_code):
        return scenarios

    # Check for Coastal Zone (different process, still allowed)
    coastal_note = None
    if getattr(parcel, 'in_coastal_zone', False):
        coastal_note = "⚠️ Coastal Zone: Coastal Development Permit (CDP) required but ADU allowed per state law"

    # Scenario 1: Detached ADU
    detached_adu = _create_detached_adu_scenario(parcel, coastal_note)
    if detached_adu:
        scenarios.append(detached_adu)

    # Scenario 2: Attached ADU (if existing structure present)
    if parcel.existing_building_sqft > 0:
        attached_adu = _create_attached_adu_scenario(parcel, coastal_note)
        if attached_adu:
            scenarios.append(attached_adu)

    # Scenario 3: JADU (if existing or proposed single-family structure)
    if parcel.existing_units >= 1 or parcel.existing_building_sqft > 0:
        jadu = _create_jadu_scenario(parcel, coastal_note)
        if jadu:
            scenarios.append(jadu)

    # Scenario 4: Combo ADU + JADU
    if len(scenarios) >= 2:
        combo = _create_combo_scenario(parcel, coastal_note)
        if combo:
            scenarios.append(combo)

    return scenarios
```

**Size Calculation**:

```python
def _calculate_max_adu_size(parcel: ParcelBase) -> int:
    """
    Calculate max ADU size based on bedrooms (§ 65852.2(a)(1)).

    Size limits:
    - Studio/1-BR: 850 sq ft
    - 2-BR: 1,000 sq ft
    - 3+ BR: 1,200 sq ft
    """
    avg_bedrooms = getattr(parcel, 'avg_bedrooms_per_unit', None)

    if avg_bedrooms is None:
        return 1000  # Default to 2-BR size

    if avg_bedrooms <= 1:
        return 850
    elif avg_bedrooms < 2.5:
        return 1000
    else:  # 2.5+ bedrooms
        return 1200
```

**Key Notes in Scenarios**:

```python
notes = [
    "Detached ADU - Ministerial Approval (Gov. Code § 65852.2)",
    f"Max size: {max_adu_size} sq ft (based on bedroom count per § 65852.2(a)(1))",
    "Height: 16 ft (1-story) or 25 ft (2-story) maximum",
    "Setbacks: 4 ft side/rear (§ 65852.2(d)(1))",
    "Parking: ZERO spaces required (AB 68, AB 681, AB 671)",
    "No discretionary review - ministerial approval required",
    "Cannot be sold separately from primary residence",
]

# JADU-specific notes
jadu_notes = [
    "Junior ADU (JADU) - Ministerial Approval (Gov. Code § 65852.22)",
    "Max size: 500 sq ft (statutory maximum)",
    "Must be within existing or proposed single-family structure",
    "Efficiency kitchen allowed (with sink, cooking surface, food storage)",
    "Parking: ZERO spaces required",
    "Owner-occupancy required (either primary dwelling or JADU)",
]
```

**Coastal Zone Handling**:

ADUs are still allowed in Coastal Zones, but may require CDP:

```python
# Check for Coastal Zone (different process, still allowed)
if getattr(parcel, 'in_coastal_zone', False):
    notes.insert(1, "⚠️ Coastal Zone: Coastal Development Permit (CDP) required but ADU allowed per state law")
```

## Base Zoning (base_zoning.py)

### Standard Calculations

```python
def analyze_base_zoning(parcel: ParcelBase) -> DevelopmentScenario:
    """
    Analyze parcel under base zoning (Santa Monica Municipal Code).

    Returns base development rights without state law enhancements.
    """
    # 1. Resolve tier-aware standards
    from app.rules.tiered_standards import resolve_tiered_standards

    standards = resolve_tiered_standards(
        parcel.zoning_code,
        parcel.development_tier,
        parcel.overlay_codes
    )

    # 2. Calculate max units
    if standards.get("units_per_acre"):
        acres = parcel.lot_size_sqft / 43560
        max_units = int(acres * standards["units_per_acre"])
    else:
        max_units = standards.get("max_units", 1)

    # 3. Calculate max building size (FAR)
    max_far = standards.get("max_far", 0.5)
    max_building_sqft = parcel.lot_size_sqft * max_far

    # 4. Height and stories
    max_height_ft = standards.get("max_height_ft", 30)
    max_stories = standards.get("max_stories", int(max_height_ft / 11))

    # 5. Setbacks
    setbacks = {
        "front": standards.get("front_setback", 15),
        "rear": standards.get("rear_setback", 15),
        "side": standards.get("side_setback", 5),
    }

    # 6. Parking (before AB 2097)
    base_parking_ratio = standards.get("parking_ratio", 1.5)
    if parcel.near_transit:
        # AB 2097 elimination
        parking_spaces_required = 0
    else:
        parking_spaces_required = int(max_units * base_parking_ratio)

    # 7. Lot coverage
    lot_coverage_pct = standards.get("lot_coverage_pct", 40)

    # 8. Build notes
    notes = [
        f"Base Zoning: {parcel.zoning_code}",
        f"Max FAR: {max_far}",
        f"Max height: {max_height_ft} ft / {max_stories} stories",
        f"Parking: {base_parking_ratio} spaces/unit",
    ]

    if parcel.development_tier:
        notes.append(f"Development tier: {parcel.development_tier}")

    if parcel.overlay_codes:
        notes.append(f"Overlays: {', '.join(parcel.overlay_codes)}")

    return DevelopmentScenario(
        scenario_name="Base Zoning",
        legal_basis=f"Santa Monica Municipal Code - {parcel.zoning_code}",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        notes=notes
    )
```

## Tier Systems (tiered_standards.py)

### Tier Resolution

```python
def resolve_tiered_standards(
    zoning_code: str,
    development_tier: Optional[str] = None,
    overlay_codes: Optional[List[str]] = None
) -> dict:
    """
    Resolve FAR and height standards with tier/overlay precedence.

    Precedence order:
    1. Bergamot Area Plan (highest - district-specific)
    2. Downtown Community Plan tiers
    3. Base zoning
    4. + Affordable Housing Overlay (additive bonus)

    Args:
        zoning_code: Base zoning code (e.g., "R2", "MU1")
        development_tier: DCP tier ("1", "2", "3")
        overlay_codes: List of overlay codes (e.g., ["DCP", "AHO"])

    Returns:
        Dict with resolved standards (max_far, max_height_ft, etc.)
    """
    # Start with base zoning standards
    standards = get_base_standards(zoning_code)

    # Apply tier/overlay modifications
    if overlay_codes:
        # Bergamot takes precedence
        if "Bergamot" in overlay_codes:
            standards = apply_bergamot_standards(standards, zoning_code)

        # DCP tiers
        elif "DCP" in overlay_codes and development_tier:
            standards = apply_dcp_tier(standards, development_tier)

        # AHO is additive
        if "AHO" in overlay_codes:
            standards = apply_aho_bonus(standards)

    return standards
```

## Common Patterns

### Statute Reference Template

```python
"""
[Law Name] ([Citation]).

[Brief description of law purpose]

References:
- [Citation] § [Section](Subsection): [Description]
- [Citation] § [Section](Subsection): [Description]

[Key provisions]:
- [Provision 1]
- [Provision 2]

[Exclusions/limitations]:
- [Exclusion 1]
- [Exclusion 2]
"""
```

### Eligibility Check Pattern

```python
def is_eligible(parcel: ParcelBase) -> bool:
    """
    Check eligibility per [Citation] § [Section].

    Returns True if parcel is eligible, False otherwise.
    """
    # Positive requirements
    if not meets_requirement_1(parcel):
        return False

    # Exclusions
    if has_exclusion_1(parcel):
        return False

    return True
```

### Notes Building Pattern

```python
notes = [
    f"[Law Name] ([Citation])",
    f"[Key metric]: [value] ([subsection reference])",
]

# Conditional notes
if condition:
    notes.append(f"[Additional detail]: [value]")

# Sub-lists for complex items
notes.append("[Category]:")
for item in items:
    notes.append(f"  • {item}")

# Always end with references
notes.append("Reference: [URL to official statute]")
```

## Testing State Laws

```bash
# Test specific law
pytest tests/test_sb9.py -v
pytest tests/test_density_bonus.py -v

# Test specific scenario
pytest tests/test_density_bonus.py::TestDensityBonusPercentages -v

# Test all state laws
pytest tests/test_sb9.py tests/test_sb35.py tests/test_density_bonus.py -v
```

## Related Documentation

- [Backend CLAUDE.md](../CLAUDE.md) - Overall backend patterns
- [Root CLAUDE.md](../../CLAUDE.md) - Project overview
- California Legislative Information: https://leginfo.legislature.ca.gov/
