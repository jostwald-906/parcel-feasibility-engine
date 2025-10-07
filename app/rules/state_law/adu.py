"""
Accessory Dwelling Unit (ADU) and Junior ADU (JADU) Analysis

Implements Gov. Code § 65852.2 (ADU) and § 65852.22 (JADU).

Key Provisions:
- Ministerial approval required (no discretionary review)
- Size limits based on bedrooms: 850/1,000/1,200 sq ft
- JADU: 500 sq ft max within existing structure
- Parking: NONE required (AB 68, AB 681, AB 671)
- Setbacks: 4 ft sides/rear, or 0 ft for conversions
- Height: 16 ft (1-story), 25 ft (2-story)

References:
- Gov. Code § 65852.2: Accessory Dwelling Units
- Gov. Code § 65852.22: Junior Accessory Dwelling Units
- AB 68 (2019): Parking prohibition, reduced setbacks
- AB 681 (2019): Size limit standardization
- AB 671 (2019): Additional parking prohibitions

ADU Size Limits (§ 65852.2(a)(1)):
- Studio/1-BR: Up to 850 sq ft
- 2-BR: Up to 1,000 sq ft
- 3+ BR: Up to 1,200 sq ft
- Attached ADUs: Can match primary dwelling size

JADU Requirements (§ 65852.22):
- 500 sq ft maximum
- Must be within existing or proposed single-family structure
- Efficiency kitchen allowed
- Owner-occupancy required (either primary or JADU)

Setback Requirements (§ 65852.2(d)(1)):
- New construction: 4 ft from side/rear property lines
- Conversions: 0 ft (existing space, no expansion)

Parking (AB 68/681/671):
- Zero parking required for ADUs
- Cannot require replacement of spaces removed for ADU
- Applies statewide, preempts local parking requirements

Height Limits (§ 65852.2(a)(1)):
- Detached single-story: 16 ft maximum
- Detached two-story: 25 ft maximum
- Attached: Follows primary dwelling height
"""

from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from typing import List, Optional


def analyze_adu(parcel: ParcelBase) -> List[DevelopmentScenario]:
    """
    Analyze ADU/JADU eligibility and generate scenarios.

    Returns up to 4 scenarios:
    1. Detached ADU (max size based on bedrooms)
    2. Attached ADU (can match primary dwelling)
    3. JADU (500 sq ft within existing structure)
    4. Combo: ADU + JADU (both allowed per statute)

    Args:
        parcel: Parcel information

    Returns:
        List of ADU/JADU development scenarios
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


def _is_residential_zoning(zoning_code: str) -> bool:
    """Check if zoning code is residential."""
    if not zoning_code:
        return False

    zone = zoning_code.upper()
    residential_indicators = ['R', 'RES', 'RESIDENTIAL', 'SINGLE', 'MULTI', 'FAMILY']

    return any(indicator in zone for indicator in residential_indicators)


def _calculate_max_adu_size(parcel: ParcelBase) -> int:
    """
    Calculate max ADU size based on bedrooms (§ 65852.2(a)(1)).

    Size limits:
    - Studio/1-BR: 850 sq ft
    - 2-BR: 1,000 sq ft
    - 3+ BR: 1,200 sq ft
    """
    # Use avg_bedrooms_per_unit if available, otherwise default to 2-BR
    avg_bedrooms = getattr(parcel, 'avg_bedrooms_per_unit', None)

    if avg_bedrooms is None:
        # Default to 2-BR size for unknown bedroom count
        return 1000

    if avg_bedrooms <= 1:
        return 850
    elif avg_bedrooms < 2.5:  # 1.01 to 2.49 -> 2-BR category
        return 1000
    else:  # 2.5+ bedrooms -> 3+ BR category
        return 1200


def _create_detached_adu_scenario(
    parcel: ParcelBase,
    coastal_note: Optional[str] = None
) -> Optional[DevelopmentScenario]:
    """
    Create detached ADU scenario.

    Args:
        parcel: Parcel information
        coastal_note: Optional coastal zone warning

    Returns:
        Detached ADU scenario
    """
    max_adu_size = _calculate_max_adu_size(parcel)

    # Check if lot can accommodate detached ADU (reasonable minimum)
    # ADU needs space for 4 ft setbacks + building footprint
    min_lot_size_needed = 800  # sq ft (conservative estimate)
    if parcel.lot_size_sqft < min_lot_size_needed:
        return None

    # Height: 16 ft for single-story, 25 ft for two-story
    max_height_ft = 25.0  # Allow two-story option
    max_stories = 2

    # Setbacks: 4 ft side/rear (§ 65852.2(d)(1))
    setbacks = {
        "side": 4.0,
        "rear": 4.0,
        "front": 10.0  # Front typically follows local standards
    }

    # Parking: ZERO required (AB 68/681/671)
    parking_spaces_required = 0

    # Calculate lot coverage (conservative for detached)
    # Assume ~500 sq ft footprint for 1000 sq ft building (2 stories)
    estimated_footprint = max_adu_size / 2  # Assume 2 stories
    if parcel.lot_size_sqft > 0:
        lot_coverage_pct = min((estimated_footprint / parcel.lot_size_sqft) * 100, 30.0)
    else:
        lot_coverage_pct = 30.0  # Default if lot size is invalid

    # Build notes with statute references
    notes = [
        "Detached ADU - Ministerial Approval (Gov. Code § 65852.2)",
        f"Max size: {max_adu_size} sq ft (based on bedroom count per § 65852.2(a)(1))",
        "Height: 16 ft (1-story) or 25 ft (2-story) maximum",
        "Setbacks: 4 ft side/rear (§ 65852.2(d)(1))",
        "Parking: ZERO spaces required (AB 68, AB 681, AB 671)",
        "No discretionary review - ministerial approval required",
        "Cannot be sold separately from primary residence",
        "Short-term rentals subject to local regulations"
    ]

    if coastal_note:
        notes.insert(1, coastal_note)

    return DevelopmentScenario(
        scenario_name="Detached ADU",
        legal_basis="Gov. Code § 65852.2 - Accessory Dwelling Units",
        max_units=parcel.existing_units + 1,  # Add 1 ADU to existing
        max_building_sqft=parcel.existing_building_sqft + max_adu_size,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_adu_size * 0.95,  # 95% efficiency
        notes=notes
    )


def _create_attached_adu_scenario(
    parcel: ParcelBase,
    coastal_note: Optional[str] = None
) -> Optional[DevelopmentScenario]:
    """
    Create attached ADU scenario.

    Attached ADUs can be larger - up to size of primary dwelling or
    standard bedroom-based limits, whichever is greater.

    Args:
        parcel: Parcel information
        coastal_note: Optional coastal zone warning

    Returns:
        Attached ADU scenario
    """
    max_standard_size = _calculate_max_adu_size(parcel)

    # For attached ADUs, can match primary dwelling size (§ 65852.2(a)(1)(D))
    # Use greater of standard limit or primary dwelling size (up to 1,200 sq ft)
    max_adu_size = min(
        max(max_standard_size, parcel.existing_building_sqft),
        1200  # Statutory cap for attached ADUs
    )

    # Attached ADU uses existing structure, so less lot size constraint
    if parcel.existing_building_sqft < 400:
        return None

    # Height follows primary dwelling
    max_height_ft = 30.0  # Typical residential height
    max_stories = 2

    # Setbacks: 0 ft for conversions (§ 65852.2(d)(1)(B))
    setbacks = {
        "side": 0.0,  # Conversion of existing space
        "rear": 0.0,
        "front": 0.0
    }

    # Parking: ZERO required
    parking_spaces_required = 0

    # Lot coverage minimal impact (uses existing structure)
    if parcel.lot_size_sqft > 0:
        lot_coverage_pct = min((parcel.existing_building_sqft / parcel.lot_size_sqft) * 100, 100.0)
    else:
        lot_coverage_pct = 40.0  # Default if lot size is invalid

    notes = [
        "Attached ADU - Ministerial Approval (Gov. Code § 65852.2)",
        f"Max size: {int(max_adu_size)} sq ft (attached ADU can match primary dwelling)",
        "Conversion of existing space: 0 ft setbacks (§ 65852.2(d)(1)(B))",
        "Parking: ZERO spaces required (AB 68, AB 681, AB 671)",
        "No discretionary review - ministerial approval required",
        "Attached to or within existing primary dwelling",
        "Can be internal conversion or addition to existing structure"
    ]

    if coastal_note:
        notes.insert(1, coastal_note)

    return DevelopmentScenario(
        scenario_name="Attached ADU",
        legal_basis="Gov. Code § 65852.2 - Accessory Dwelling Units (Attached)",
        max_units=parcel.existing_units + 1,
        max_building_sqft=parcel.existing_building_sqft + max_adu_size,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_adu_size * 0.95,
        notes=notes
    )


def _create_jadu_scenario(
    parcel: ParcelBase,
    coastal_note: Optional[str] = None
) -> Optional[DevelopmentScenario]:
    """
    Create JADU (Junior ADU) scenario.

    JADUs are 500 sq ft max, must be within existing/proposed SF structure.

    Args:
        parcel: Parcel information
        coastal_note: Optional coastal zone warning

    Returns:
        JADU scenario
    """
    max_jadu_size = 500  # Statutory maximum (§ 65852.22)

    # JADU requires existing or proposed single-family structure
    if parcel.existing_building_sqft < 500:
        return None

    # Height follows existing structure
    max_height_ft = 25.0
    max_stories = 2

    # Setbacks: 0 ft (within existing structure)
    setbacks = {
        "side": 0.0,
        "rear": 0.0,
        "front": 0.0
    }

    # Parking: ZERO required
    parking_spaces_required = 0

    # Lot coverage: no impact (within existing structure)
    if parcel.lot_size_sqft > 0:
        lot_coverage_pct = min((parcel.existing_building_sqft / parcel.lot_size_sqft) * 100, 100.0)
    else:
        lot_coverage_pct = 30.0  # Default if lot size is invalid

    notes = [
        "Junior ADU (JADU) - Ministerial Approval (Gov. Code § 65852.22)",
        "Max size: 500 sq ft (statutory maximum)",
        "Must be within existing or proposed single-family structure",
        "Efficiency kitchen allowed (with sink, cooking surface, food storage)",
        "Parking: ZERO spaces required",
        "Owner-occupancy required (either primary dwelling or JADU)",
        "Separate entrance from primary dwelling allowed",
        "Bathroom can be shared with primary dwelling"
    ]

    if coastal_note:
        notes.insert(1, coastal_note)

    return DevelopmentScenario(
        scenario_name="Junior ADU (JADU)",
        legal_basis="Gov. Code § 65852.22 - Junior Accessory Dwelling Units",
        max_units=parcel.existing_units + 1,
        max_building_sqft=parcel.existing_building_sqft + max_jadu_size,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_jadu_size * 0.95,
        notes=notes
    )


def _create_combo_scenario(
    parcel: ParcelBase,
    coastal_note: Optional[str] = None
) -> Optional[DevelopmentScenario]:
    """
    Create combo ADU + JADU scenario.

    State law allows both ADU and JADU on the same parcel.

    Args:
        parcel: Parcel information
        coastal_note: Optional coastal zone warning

    Returns:
        Combo ADU + JADU scenario
    """
    max_adu_size = _calculate_max_adu_size(parcel)
    max_jadu_size = 500

    # Need sufficient lot size and existing structure for combo
    if parcel.lot_size_sqft < 3000 or parcel.existing_building_sqft < 800:
        return None

    # Combined building square footage
    total_new_sqft = max_adu_size + max_jadu_size

    # Height follows detached ADU limits
    max_height_ft = 25.0
    max_stories = 2

    # Setbacks: 4 ft for detached ADU, 0 ft for JADU (in existing)
    setbacks = {
        "side": 4.0,  # For detached ADU
        "rear": 4.0,
        "front": 10.0
    }

    # Parking: ZERO required
    parking_spaces_required = 0

    # Lot coverage
    estimated_footprint = max_adu_size / 2  # Assume 2-story detached
    if parcel.lot_size_sqft > 0:
        lot_coverage_pct = min(
            ((parcel.existing_building_sqft + estimated_footprint) / parcel.lot_size_sqft) * 100,
            40.0
        )
    else:
        lot_coverage_pct = 40.0  # Default if lot size is invalid

    notes = [
        "ADU + JADU Combo - Maximum Density (Gov. Code § 65852.2 & § 65852.22)",
        f"Detached ADU: {max_adu_size} sq ft + JADU: {max_jadu_size} sq ft = {total_new_sqft} sq ft total",
        "2 additional units allowed (1 ADU + 1 JADU)",
        "ADU: 4 ft side/rear setbacks; JADU: within existing structure (0 ft setbacks)",
        "Parking: ZERO spaces required for both units",
        "JADU owner-occupancy requirement applies",
        "Both units ministerial approval - no discretionary review",
        "Maximum allowed accessory dwelling units under state law"
    ]

    if coastal_note:
        notes.insert(1, coastal_note)

    return DevelopmentScenario(
        scenario_name="ADU + JADU Combo",
        legal_basis="Gov. Code § 65852.2 & § 65852.22 - Maximum ADU/JADU",
        max_units=parcel.existing_units + 2,  # Add both ADU and JADU
        max_building_sqft=parcel.existing_building_sqft + total_new_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=total_new_sqft * 0.95,
        notes=notes
    )


def get_adu_info() -> dict:
    """
    Get ADU/JADU program information for reference.

    Returns:
        Dict with ADU/JADU program details
    """
    return {
        "program_name": "Accessory Dwelling Units (ADU) and Junior ADUs (JADU)",
        "legal_basis": [
            "Gov. Code § 65852.2 - Accessory Dwelling Units",
            "Gov. Code § 65852.22 - Junior Accessory Dwelling Units"
        ],
        "key_bills": [
            "AB 68 (2019) - Parking prohibition, reduced setbacks",
            "AB 681 (2019) - Size standardization",
            "AB 671 (2019) - Additional parking prohibitions"
        ],
        "size_limits": {
            "adu_studio_1br": 850,
            "adu_2br": 1000,
            "adu_3plus_br": 1200,
            "jadu_max": 500
        },
        "parking_required": 0,
        "setbacks": {
            "new_construction": "4 ft side/rear",
            "conversion": "0 ft"
        },
        "height_limits": {
            "detached_1_story": 16,
            "detached_2_story": 25
        },
        "approval_type": "Ministerial (no discretionary review)",
        "eligibility": "All residential parcels (state law preempts local restrictions)"
    }
