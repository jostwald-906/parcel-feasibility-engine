"""
Downtown Community Plan (DCP) Scenario Generation

Creates development scenarios for parcels within Santa Monica's Downtown Community Plan area,
applying tiered development standards based on community benefits provided.

CITE: SMMC Chapter 9.10 (Downtown Districts)
CITE: Downtown Community Plan (July 25, 2017, amended 2023)
CITE: SMMC § 9.23.030 (Community Benefits)
"""

from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from app.rules.tiered_standards import DCP_TA_STANDARDS, DCP_NV_STANDARDS
from typing import List, Optional


def is_in_dcp_area(parcel: ParcelBase) -> bool:
    """
    Check if parcel is within Downtown Community Plan area.

    In production, this would query GIS overlays. For now, we infer from:
    - Zoning codes starting with 'TA' or 'NV'
    - Overlay codes containing 'DCP' or 'DOWNTOWN'

    Args:
        parcel: Parcel information

    Returns:
        True if parcel is within DCP boundaries
    """
    zoning = parcel.zoning_code.upper()

    # Check zoning code
    if zoning.startswith('TA') or zoning.startswith('NV'):
        return True

    # Check overlay codes
    if hasattr(parcel, 'overlay_codes') and parcel.overlay_codes:
        for code in parcel.overlay_codes:
            if 'DCP' in code.upper() or 'DOWNTOWN' in code.upper():
                return True

    return False


def get_dcp_district(parcel: ParcelBase) -> Optional[str]:
    """
    Determine which DCP district the parcel is in (TA or NV).

    Args:
        parcel: Parcel information

    Returns:
        'TA' for Transit Adjacent, 'NV' for Neighborhood Village, None if not in DCP
    """
    zoning = parcel.zoning_code.upper()

    if zoning.startswith('TA'):
        return 'TA'
    elif zoning.startswith('NV'):
        return 'NV'

    # Check overlay codes as fallback
    if hasattr(parcel, 'overlay_codes') and parcel.overlay_codes:
        for code in parcel.overlay_codes:
            if 'TA' in code.upper():
                return 'TA'
            elif 'NV' in code.upper():
                return 'NV'

    return None


def create_dcp_tier_1_scenario(
    parcel: ParcelBase,
    district: str
) -> Optional[DevelopmentScenario]:
    """
    Create Tier 1 (base) DCP scenario - no community benefits required.

    CITE: SMMC Chapter 9.10 - Tier 1 Base Standards

    Args:
        parcel: Parcel information
        district: 'TA' or 'NV'

    Returns:
        DevelopmentScenario for Tier 1 development
    """
    standards = DCP_TA_STANDARDS if district == 'TA' else DCP_NV_STANDARDS
    tier_1 = standards.get('1')

    if not tier_1:
        return None

    far = tier_1['far']
    height = tier_1['height']

    # Calculate max building sqft from FAR
    max_building_sqft = parcel.lot_size_sqft * far

    # Estimate units (assume 1,000 sqft per unit for mixed-use)
    avg_unit_size = 1000
    max_units = int(max_building_sqft / avg_unit_size)

    # Estimate stories
    max_stories = int(height / 11)  # ~11 ft per story

    # Standard setbacks for downtown
    setbacks = {
        "front": 0,    # Build to property line for street activation
        "rear": 10,
        "side": 5
    }

    scenario = DevelopmentScenario(
        scenario_name=f"DCP Tier 1 ({district})",
        legal_basis=f"SMMC Chapter 9.10 - Downtown Community Plan Tier 1 ({district} District)",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=height,
        max_stories=max_stories,
        parking_spaces_required=int(max_units * 0.5),  # Reduced parking in downtown
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=85.0,  # High coverage in urban core
        notes=[
            f"Tier 1 base standards: FAR {far}, Height {height} ft",
            "No community benefits required at Tier 1",
            "Ground-floor commercial encouraged (not required)",
            "Standard development review process"
        ]
    )

    return scenario


def create_dcp_tier_2_scenario(
    parcel: ParcelBase,
    district: str,
    with_housing_bonus: bool = False
) -> Optional[DevelopmentScenario]:
    """
    Create Tier 2 DCP scenario - requires community benefits.

    CITE: SMMC Chapter 9.10 - Tier 2 Standards
    CITE: SMMC § 9.23.030 - Community Benefits

    Args:
        parcel: Parcel information
        district: 'TA' or 'NV'
        with_housing_bonus: If True, apply +0.5 FAR bonus for residential (TA only)

    Returns:
        DevelopmentScenario for Tier 2 development
    """
    standards = DCP_TA_STANDARDS if district == 'TA' else DCP_NV_STANDARDS

    # Select appropriate tier 2 standard
    if district == 'TA':
        tier_key = '2_housing' if with_housing_bonus else '2_nonres'
    else:  # NV
        tier_key = '2_housing' if with_housing_bonus else '2_nonres'

    tier_2 = standards.get(tier_key)

    if not tier_2:
        return None

    far = tier_2['far']
    height = tier_2['height']

    # Calculate max building sqft from FAR
    max_building_sqft = parcel.lot_size_sqft * far

    # Estimate units
    avg_unit_size = 950  # Slightly smaller for increased density
    max_units = int(max_building_sqft / avg_unit_size)

    # Estimate stories
    max_stories = int(height / 11)

    # Standard setbacks
    setbacks = {
        "front": 0,
        "rear": 10,
        "side": 5
    }

    scenario_name = f"DCP Tier 2 ({district})" + (" + Housing Bonus" if with_housing_bonus else "")
    housing_note = " with residential use" if with_housing_bonus else ""

    scenario = DevelopmentScenario(
        scenario_name=scenario_name,
        legal_basis=f"SMMC Chapter 9.10 - Downtown Community Plan Tier 2 ({district} District){housing_note}",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=height,
        max_stories=max_stories,
        parking_spaces_required=int(max_units * 0.5),
        affordable_units_required=0,  # Set by community benefit requirements
        setbacks=setbacks,
        lot_coverage_pct=85.0,
        notes=[
            f"Tier 2 standards: FAR {far}, Height {height} ft",
            "✅ REQUIRES: One or more community benefits (see Community Benefits tab)",
            "Typical: 15-20% affordable housing OR public plaza OR arts/cultural space",
            "Community Development Director approval required",
            "Enhanced sustainability encouraged (LEED Silver+)"
        ]
    )

    if with_housing_bonus:
        scenario.notes.insert(1, f"✅ +0.5 FAR bonus for residential use (FAR {far - 0.5} → {far})")

    return scenario


def create_dcp_tier_3_scenario(
    parcel: ParcelBase,
    district: str,
    is_100pct_affordable: bool = False
) -> Optional[DevelopmentScenario]:
    """
    Create Tier 3 (maximum) DCP scenario - requires substantial community benefits.

    CITE: SMMC Chapter 9.10 - Tier 3 Standards
    CITE: SMMC § 9.23.030 - Community Benefits

    Args:
        parcel: Parcel information
        district: 'TA' or 'NV'
        is_100pct_affordable: Special case for 100% affordable housing projects

    Returns:
        DevelopmentScenario for Tier 3 development
    """
    standards = DCP_TA_STANDARDS if district == 'TA' else DCP_NV_STANDARDS

    # NV district Tier 3 is only available for 100% affordable housing
    if district == 'NV':
        if not is_100pct_affordable:
            return None  # NV doesn't allow market-rate Tier 3
        tier_3 = standards.get('100pct_affordable')
    else:  # TA district
        if is_100pct_affordable:
            # Use special standards for 100% affordable (if defined)
            tier_3 = standards.get('3')  # TA allows Tier 3 for market-rate with benefits
        else:
            tier_3 = standards.get('3')

    if not tier_3:
        return None

    far = tier_3['far']
    height = tier_3['height']

    # Calculate max building sqft from FAR
    max_building_sqft = parcel.lot_size_sqft * far

    # Estimate units
    avg_unit_size = 900  # Smaller for maximum density
    max_units = int(max_building_sqft / avg_unit_size)

    # Estimate stories
    max_stories = int(height / 11)

    # Standard setbacks
    setbacks = {
        "front": 0,
        "rear": 10,
        "side": 5
    }

    if is_100pct_affordable:
        scenario_name = f"DCP Tier 3 - 100% Affordable ({district})"
        affordability_note = "100% affordable housing project"
    else:
        scenario_name = f"DCP Tier 3 ({district})"
        affordability_note = "Market-rate project"

    scenario = DevelopmentScenario(
        scenario_name=scenario_name,
        legal_basis=f"SMMC Chapter 9.10 - Downtown Community Plan Tier 3 ({district} District)",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=height,
        max_stories=max_stories,
        parking_spaces_required=int(max_units * 0.4) if not is_100pct_affordable else 0,  # Reduced for affordable
        affordable_units_required=max_units if is_100pct_affordable else 0,
        setbacks=setbacks,
        lot_coverage_pct=85.0,
        notes=[
            f"Tier 3 maximum standards: FAR {far}, Height {height} ft",
            f"Project type: {affordability_note}"
        ]
    )

    if is_100pct_affordable:
        scenario.notes.extend([
            "✅ 100% affordable housing qualifies for Tier 3",
            "Zero parking requirement (near transit + affordable)",
            "Expedited approval process",
            "May combine with State Density Bonus for additional benefits"
        ])
    else:
        scenario.notes.extend([
            "✅ REQUIRES: Multiple substantial community benefits",
            "Typical: 25%+ affordable housing + public plaza + sustainability features",
            "Planning Commission approval required",
            "Development Agreement required",
            "LEED Gold or higher expected",
            "Highest level of community benefit contribution"
        ])

    # Special case for large sites in TA
    if district == 'TA' and parcel.lot_size_sqft > 50000:
        large_site_standards = DCP_TA_STANDARDS.get('3_large_site')
        if large_site_standards:
            scenario.notes.append(
                f"✅ Large site (>{50000:,} sqft): May qualify for height up to {large_site_standards['height']} ft with enhanced design"
            )

    return scenario


def generate_all_dcp_scenarios(parcel: ParcelBase) -> List[DevelopmentScenario]:
    """
    Generate all applicable DCP scenarios for a parcel.

    This creates multiple scenarios showing progressive development potential
    through the DCP tier system.

    Args:
        parcel: Parcel information

    Returns:
        List of DevelopmentScenario objects for different DCP tiers
    """
    scenarios = []

    # Check if parcel is in DCP area
    if not is_in_dcp_area(parcel):
        return scenarios

    district = get_dcp_district(parcel)
    if not district:
        return scenarios

    # Tier 1 (base)
    tier_1 = create_dcp_tier_1_scenario(parcel, district)
    if tier_1:
        scenarios.append(tier_1)

    # Tier 2 (non-residential)
    tier_2_nonres = create_dcp_tier_2_scenario(parcel, district, with_housing_bonus=False)
    if tier_2_nonres:
        scenarios.append(tier_2_nonres)

    # Tier 2 (with housing bonus) - only for TA
    if district == 'TA':
        tier_2_housing = create_dcp_tier_2_scenario(parcel, district, with_housing_bonus=True)
        if tier_2_housing:
            scenarios.append(tier_2_housing)

    # Tier 3 (market-rate) - only for TA
    if district == 'TA':
        tier_3_market = create_dcp_tier_3_scenario(parcel, district, is_100pct_affordable=False)
        if tier_3_market:
            scenarios.append(tier_3_market)

    # Tier 3 (100% affordable) - both districts
    tier_3_affordable = create_dcp_tier_3_scenario(parcel, district, is_100pct_affordable=True)
    if tier_3_affordable:
        scenarios.append(tier_3_affordable)

    return scenarios


def get_current_dcp_tier(parcel: ParcelBase) -> Optional[int]:
    """
    Determine the current DCP tier designation for a parcel.

    This would typically be retrieved from GIS data or parcel attributes.
    For now, we infer from development_tier attribute.

    Args:
        parcel: Parcel information

    Returns:
        Tier number (1, 2, 3) or None if not in DCP or tier unknown
    """
    if not is_in_dcp_area(parcel):
        return None

    # Check if parcel has explicit tier designation
    if hasattr(parcel, 'development_tier') and parcel.development_tier:
        import re
        tier_match = re.search(r'\d+', str(parcel.development_tier))
        if tier_match:
            return int(tier_match.group())

    # Default to Tier 1 if in DCP area but no explicit tier
    return 1
