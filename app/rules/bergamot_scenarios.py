"""
Bergamot Area Plan Scenario Generation

Creates development scenarios for parcels within Santa Monica's Bergamot Area Plan,
applying tiered development standards based on district and community benefits provided.

CITE: SMMC Chapter 9.04.090 (Bergamot definitions)
CITE: SMMC Chapter 9.12 (Bergamot Area Plan)
CITE: Bergamot Area Plan (adopted September 2013, amended October 2023)
"""

from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from app.rules.tiered_standards import (
    BERGAMOT_BTV_STANDARDS,
    BERGAMOT_MUC_STANDARDS,
    BERGAMOT_CAC_STANDARDS,
)
from typing import List, Optional


def is_in_bergamot_area(parcel: ParcelBase) -> bool:
    """
    Check if parcel is within Bergamot Area Plan boundaries.

    In production, this would query GIS overlays. For now, we infer from:
    - Zoning codes starting with 'BTV', 'MUC', or 'CAC'
    - Overlay codes containing 'BERGAMOT'

    Args:
        parcel: Parcel information

    Returns:
        True if parcel is within Bergamot Area Plan boundaries
    """
    zoning = parcel.zoning_code.upper()

    # Check zoning code
    if zoning.startswith('BTV') or zoning.startswith('MUC') or zoning.startswith('CAC'):
        return True

    # Check overlay codes
    if hasattr(parcel, 'overlay_codes') and parcel.overlay_codes:
        for code in parcel.overlay_codes:
            if 'BERGAMOT' in code.upper():
                return True

    return False


def get_bergamot_district(parcel: ParcelBase) -> Optional[str]:
    """
    Determine which Bergamot district the parcel is in.

    Args:
        parcel: Parcel information

    Returns:
        'BTV' for Transit Village, 'MUC' for Mixed-Use Creative,
        'CAC' for Conservation Art Center, or None if not in Bergamot
    """
    zoning = parcel.zoning_code.upper()

    if zoning.startswith('BTV'):
        return 'BTV'
    elif zoning.startswith('MUC'):
        return 'MUC'
    elif zoning.startswith('CAC'):
        return 'CAC'

    # Check overlay codes as fallback
    if hasattr(parcel, 'overlay_codes') and parcel.overlay_codes:
        for code in parcel.overlay_codes:
            code_upper = code.upper()
            if 'BTV' in code_upper:
                return 'BTV'
            elif 'MUC' in code_upper:
                return 'MUC'
            elif 'CAC' in code_upper:
                return 'CAC'

    return None


def create_bergamot_tier_1_scenario(
    parcel: ParcelBase,
    district: str
) -> Optional[DevelopmentScenario]:
    """
    Create Tier 1 (base) Bergamot scenario - no community benefits required.

    CITE: SMMC Chapter 9.12 - Tier 1 Base Standards

    Args:
        parcel: Parcel information
        district: 'BTV', 'MUC', or 'CAC'

    Returns:
        DevelopmentScenario for Tier 1 development
    """
    # Select appropriate standards based on district
    if district == 'BTV':
        standards = BERGAMOT_BTV_STANDARDS.get('1')
        district_name = 'Transit Village'
    elif district == 'MUC':
        standards = BERGAMOT_MUC_STANDARDS.get('1')
        district_name = 'Mixed-Use Creative'
    elif district == 'CAC':
        # For CAC, determine size category
        is_large_site = parcel.lot_size_sqft >= 100000
        tier_key = '1_large' if is_large_site else '1_small'
        standards = BERGAMOT_CAC_STANDARDS.get(tier_key)
        district_name = 'Conservation Art Center'
    else:
        return None

    if not standards:
        return None

    far = standards['far']
    height = standards['height']

    # Calculate max building sqft from FAR
    max_building_sqft = parcel.lot_size_sqft * far

    # Estimate units (assume 1,000 sqft per unit for Tier 1)
    avg_unit_size = 1000
    max_units = int(max_building_sqft / avg_unit_size)

    # Estimate stories
    max_stories = int(height / 11)  # ~11 ft per story

    # District-specific setbacks
    if district == 'CAC':
        # CAC has more spacious character
        setbacks = {
            "front": 10,
            "rear": 15,
            "side": 10
        }
        lot_coverage = 60.0  # More open space
    else:
        # BTV/MUC are more urban
        setbacks = {
            "front": 5,
            "rear": 10,
            "side": 5
        }
        lot_coverage = 80.0

    # Standard parking for Tier 1
    parking_ratio = 1.0
    parking_spaces = int(max_units * parking_ratio)

    scenario = DevelopmentScenario(
        scenario_name=f"Bergamot Tier 1 ({district})",
        legal_basis=f"SMMC Chapter 9.12 - Bergamot Area Plan Tier 1 ({district_name})",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=height,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage,
        notes=[
            f"Tier 1 base standards: FAR {far}, Height {height} ft",
            "Community benefits NOT required at Tier 1",
            "Bergamot Area Plan emphasizes creative and arts uses",
            "Enhanced sustainability and pedestrian design expected",
            "Ground-floor active uses encouraged"
        ]
    )

    # Add district-specific notes
    if district == 'BTV':
        scenario.notes.append("Transit Village: Pedestrian-oriented design with Expo Line integration")
    elif district == 'MUC':
        scenario.notes.append("Mixed-Use Creative: Arts, creative offices, and production space encouraged")
    elif district == 'CAC':
        scenario.notes.append("Conservation Art Center: Arts and cultural uses prioritized, museum-quality character")
        if parcel.lot_size_sqft >= 100000:
            scenario.notes.append("Large site (≥100,000 sqft): City-owned property standards apply")

    return scenario


def create_bergamot_tier_2_scenario(
    parcel: ParcelBase,
    district: str
) -> Optional[DevelopmentScenario]:
    """
    Create Tier 2 Bergamot scenario - requires community benefits.

    CITE: SMMC Chapter 9.12 - Tier 2 Standards
    CITE: SMMC § 9.23.030 - Community Benefits

    Args:
        parcel: Parcel information
        district: 'BTV', 'MUC', or 'CAC'

    Returns:
        DevelopmentScenario for Tier 2 development
    """
    # Select appropriate standards based on district
    if district == 'BTV':
        standards = BERGAMOT_BTV_STANDARDS.get('2')
        district_name = 'Transit Village'
    elif district == 'MUC':
        standards = BERGAMOT_MUC_STANDARDS.get('2')
        district_name = 'Mixed-Use Creative'
    elif district == 'CAC':
        # For CAC, determine size category
        is_large_site = parcel.lot_size_sqft >= 100000
        tier_key = '2_large' if is_large_site else '2_small'
        standards = BERGAMOT_CAC_STANDARDS.get(tier_key)
        district_name = 'Conservation Art Center'
    else:
        return None

    if not standards:
        return None

    far = standards['far']
    height = standards['height']

    # Calculate max building sqft from FAR
    max_building_sqft = parcel.lot_size_sqft * far

    # Estimate units (assume 950 sqft per unit for Tier 2)
    avg_unit_size = 950
    max_units = int(max_building_sqft / avg_unit_size)

    # Estimate stories
    max_stories = int(height / 11)

    # District-specific setbacks
    if district == 'CAC':
        setbacks = {
            "front": 10,
            "rear": 15,
            "side": 10
        }
        lot_coverage = 60.0
    else:
        setbacks = {
            "front": 5,
            "rear": 10,
            "side": 5
        }
        lot_coverage = 80.0

    # Reduced parking for Tier 2
    parking_ratio = 0.75
    parking_spaces = int(max_units * parking_ratio)

    scenario = DevelopmentScenario(
        scenario_name=f"Bergamot Tier 2 ({district})",
        legal_basis=f"SMMC Chapter 9.12 - Bergamot Area Plan Tier 2 ({district_name})",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=height,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces,
        affordable_units_required=0,  # Set by community benefit requirements
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage,
        notes=[
            f"Tier 2 standards: FAR {far}, Height {height} ft",
            "✅ REQUIRES: Community benefits for tier upgrade",
            "Typical: 15-20% affordable housing OR public art/cultural space",
            "Enhanced sustainability features expected (LEED Silver+)",
            "Bergamot Area Plan emphasizes creative and arts uses",
            "Community Development Director approval required"
        ]
    )

    # Add district-specific notes
    if district == 'BTV':
        scenario.notes.append("Transit Village: Enhanced pedestrian connectivity and transit access")
    elif district == 'MUC':
        scenario.notes.append("Mixed-Use Creative: Workspace for artists, makers, and creative industries")
    elif district == 'CAC':
        scenario.notes.append("Conservation Art Center: Cultural programming and public art integration")
        if parcel.lot_size_sqft >= 100000:
            scenario.notes.append("Large site: Limited FAR increase, focus on height for special cultural facilities")
        else:
            scenario.notes.append("Small site: Enhanced FAR to support arts/cultural uses")

    return scenario


def create_bergamot_tier_3_scenario(
    parcel: ParcelBase,
    district: str
) -> Optional[DevelopmentScenario]:
    """
    Create Tier 3 (maximum) Bergamot scenario - requires substantial community benefits.

    CITE: SMMC Chapter 9.12 - Tier 3 Standards
    CITE: SMMC § 9.23.030 - Community Benefits

    Args:
        parcel: Parcel information
        district: 'BTV', 'MUC', or 'CAC'

    Returns:
        DevelopmentScenario for Tier 3 development
    """
    # Select appropriate standards based on district
    if district == 'BTV':
        standards = BERGAMOT_BTV_STANDARDS.get('3')
        district_name = 'Transit Village'
    elif district == 'MUC':
        standards = BERGAMOT_MUC_STANDARDS.get('3')
        district_name = 'Mixed-Use Creative'
    elif district == 'CAC':
        # For CAC, determine size category
        is_large_site = parcel.lot_size_sqft >= 100000
        tier_key = '3_large' if is_large_site else '3_small'
        standards = BERGAMOT_CAC_STANDARDS.get(tier_key)
        district_name = 'Conservation Art Center'
    else:
        return None

    if not standards:
        return None

    far = standards['far']
    height = standards['height']

    # Calculate max building sqft from FAR
    max_building_sqft = parcel.lot_size_sqft * far

    # Estimate units (assume 900 sqft per unit for Tier 3)
    avg_unit_size = 900
    max_units = int(max_building_sqft / avg_unit_size)

    # Estimate stories
    max_stories = int(height / 11)

    # District-specific setbacks
    if district == 'CAC':
        setbacks = {
            "front": 10,
            "rear": 15,
            "side": 10
        }
        lot_coverage = 60.0
    else:
        setbacks = {
            "front": 5,
            "rear": 10,
            "side": 5
        }
        lot_coverage = 80.0

    # Minimal parking for Tier 3
    parking_ratio = 0.5
    parking_spaces = int(max_units * parking_ratio)

    scenario = DevelopmentScenario(
        scenario_name=f"Bergamot Tier 3 ({district})",
        legal_basis=f"SMMC Chapter 9.12 - Bergamot Area Plan Tier 3 ({district_name})",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=height,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces,
        affordable_units_required=0,  # Set by community benefit requirements
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage,
        notes=[
            f"Tier 3 maximum standards: FAR {far}, Height {height} ft",
            "✅ REQUIRES: Substantial community benefits",
            "Typical: 25%+ affordable housing + public art/cultural space + sustainability features",
            "Development Agreement required",
            "LEED Gold or higher expected",
            "Bergamot Area Plan goals: arts, creative uses, sustainability",
            "Planning Commission approval required"
        ]
    )

    # Add district-specific notes
    if district == 'BTV':
        scenario.notes.append("Transit Village: Maximum integration with Expo Line and pedestrian network")
        scenario.notes.append("Buildings >90 ft have additional design standards")
    elif district == 'MUC':
        scenario.notes.append("Mixed-Use Creative: Significant creative workspace and arts programming")
        scenario.notes.append("Buildings >90 ft have additional design standards")
    elif district == 'CAC':
        if parcel.lot_size_sqft >= 100000:
            scenario.notes.append("Large site: Maximum height for cultural/civic facilities, limited FAR")
            scenario.notes.append("City-owned property: Cultural and arts programming prioritized")
        else:
            scenario.notes.append("Small site: Exceptional FAR (2.5) and height (86 ft) for arts uses")
            scenario.notes.append("Must demonstrate significant cultural/arts benefit to community")
        scenario.notes.append("Conservation Art Center: Premium cultural destination character required")

    # Special provisions
    if height > 90:
        scenario.notes.append("⚠️ Height exceeds 90 ft: Additional design review and massing requirements apply")

    scenario.notes.append("Maximum podium height: 35 feet")
    scenario.notes.append("Expo Light Rail integration and connectivity required")

    return scenario


def generate_all_bergamot_scenarios(parcel: ParcelBase) -> List[DevelopmentScenario]:
    """
    Generate all applicable Bergamot Area Plan scenarios for a parcel.

    This creates multiple scenarios showing progressive development potential
    through the Bergamot tier system.

    Args:
        parcel: Parcel information

    Returns:
        List of DevelopmentScenario objects for different Bergamot tiers
    """
    scenarios = []

    # Check if parcel is in Bergamot area
    if not is_in_bergamot_area(parcel):
        return scenarios

    district = get_bergamot_district(parcel)
    if not district:
        return scenarios

    # Tier 1 (base)
    tier_1 = create_bergamot_tier_1_scenario(parcel, district)
    if tier_1:
        scenarios.append(tier_1)

    # Tier 2 (with community benefits)
    tier_2 = create_bergamot_tier_2_scenario(parcel, district)
    if tier_2:
        scenarios.append(tier_2)

    # Tier 3 (maximum with substantial benefits)
    tier_3 = create_bergamot_tier_3_scenario(parcel, district)
    if tier_3:
        scenarios.append(tier_3)

    return scenarios


def get_current_bergamot_tier(parcel: ParcelBase) -> Optional[int]:
    """
    Determine the current Bergamot tier designation for a parcel.

    This would typically be retrieved from GIS data or parcel attributes.
    For now, we infer from development_tier attribute.

    Args:
        parcel: Parcel information

    Returns:
        Tier number (1, 2, 3) or None if not in Bergamot or tier unknown
    """
    if not is_in_bergamot_area(parcel):
        return None

    # Check if parcel has explicit tier designation
    if hasattr(parcel, 'development_tier') and parcel.development_tier:
        import re
        tier_match = re.search(r'\d+', str(parcel.development_tier))
        if tier_match:
            return int(tier_match.group())

    # Default to Tier 1 if in Bergamot area but no explicit tier
    return 1
