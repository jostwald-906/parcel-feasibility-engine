"""
SB35 (2017) streamlining analysis.

Senate Bill 35 provides streamlined, ministerial approval for multifamily
housing developments in cities that have not met their Regional Housing
Needs Allocation (RHNA) targets.

Key requirements:
- Multifamily development (2+ units)
- In locality that hasn't met RHNA targets
- Meets all objective standards
- Includes required affordable housing percentage:
  * 10% affordable if locality met > 50% of RHNA
  * 50% affordable if locality met < 50% of RHNA
- Prevailing wage for projects with 10+ units
- Union labor for projects with 75+ units

Benefits:
- Ministerial approval (no discretionary review)
- CEQA exemption
- Faster approval timeline
"""
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from typing import Optional
import math


def analyze_sb35(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Analyze development potential under SB35 streamlining.

    Args:
        parcel: Parcel information

    Returns:
        SB35 scenario if eligible, None otherwise
    """
    # Check basic eligibility
    if not is_sb35_eligible(parcel):
        return None

    # Determine affordability requirement based on jurisdiction
    # In production, would query RHNA progress data
    affordability_req = get_affordability_requirement(parcel)
    affordability_pct = affordability_req['percentage']

    # Calculate maximum density
    # SB35 allows development at zoning maximum
    max_units = calculate_sb35_max_units(parcel)

    if max_units < 2:
        return None  # Must be multifamily

    # Calculate building parameters
    max_far = get_max_far(parcel)
    max_building_sqft = parcel.lot_size_sqft * max_far

    # Height limits - typically allow what zoning permits
    max_height_ft = get_max_height(parcel)
    max_stories = int(max_height_ft / 11)

    # Parking - AB 2097 parking elimination (near transit)
    # AB 2097 (2022) prohibits minimum parking requirements for residential/mixed-use
    # projects within 1/2 mile of "major transit stop" or "high-quality transit corridor"
    parking_per_unit = 1.0  # Conservative default
    near_transit = bool(getattr(parcel, "near_transit", False))
    parking_eliminated_reason = None

    if near_transit:
        # AB 2097 eliminates parking requirements
        parking_per_unit = 0.0
        parking_eliminated_reason = "AB 2097: Within 1/2 mile of major transit stop"

    parking_spaces_required = int(max_units * max(parking_per_unit, 0.0))

    # Setbacks - must meet objective standards
    setbacks = {
        "front": 10.0,
        "rear": 10.0,
        "side": 5.0
    }

    # Calculate affordable units
    affordable_units_required = math.ceil(max_units * (affordability_pct / 100))

    # Lot coverage
    lot_coverage_pct = min((max_building_sqft / parcel.lot_size_sqft) * 100, 70.0)

    # Build notes
    notes = [
        "SB35 streamlined ministerial approval",
        "Ministerial approval - no discretionary review",
        "CEQA exempt per SB35",
        "Must meet all local objective standards",
    ]

    # Affordability requirements (detailed documentation)
    notes.extend(affordability_req['notes'])

    # AB 2097 parking notes
    if near_transit and parking_eliminated_reason:
        notes.append(f"Parking: {parking_eliminated_reason}")
        notes.append("AB 2097 'major transit stop' = existing rail/ferry with service interval ≤15 min peak, or bus rapid transit/intersection ≥2 routes with ≤15 min interval peak")
    elif near_transit:
        notes.append("AB 2097 parking elimination applied (within 1/2 mile of quality transit)")
    else:
        notes.append(f"Parking: {parking_per_unit} space(s) per unit (conservative estimate - verify local requirements)")

    # Labor standards (detailed documentation)
    labor_reqs = get_labor_requirements(max_units)
    notes.extend(labor_reqs)

    # Additional SB35 requirements
    notes.append("Must complete construction within specific timeline (verify local jurisdiction timeline)")
    notes.append("Verify jurisdiction's RHNA progress with planning department")

    scenario = DevelopmentScenario(
        scenario_name="SB35 Streamlined",
        legal_basis=f"SB35 (2017) - Streamlined Ministerial Approval",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=affordable_units_required,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.85,
        notes=notes
    )

    return scenario


def can_apply_sb35(parcel: ParcelBase) -> dict:
    """
    Check SB 35 eligibility with detailed reasons.

    This function performs a comprehensive eligibility check including:
    - RHNA compliance (jurisdiction must not meet housing goals)
    - Site exclusions (coastal hazard, farmland, conservation, historic)
    - Protected tenancy checks (rent control, Ellis Act, displacement)
    - Zoning requirements (residential/mixed-use, minimum lot size)

    Args:
        parcel: Parcel information

    Returns:
        {
            'eligible': bool,
            'reasons': List[str],  # Why eligible or not eligible
            'requirements': List[str],  # Additional requirements if eligible
            'exclusions': List[str]  # Site exclusion factors if any
        }

    References:
        Gov. Code § 65913.4 - SB 35 Streamlined Ministerial Approval
    """
    reasons = []
    requirements = []
    exclusions = []
    eligible = True

    # 1. ZONING REQUIREMENTS
    zoning_code = parcel.zoning_code.upper()
    residential_zones = ["R1", "R2", "R3", "R4", "RM", "RH", "MU", "MIXED"]
    is_residential = any(zone in zoning_code for zone in residential_zones)

    if not is_residential:
        eligible = False
        reasons.append(f"Ineligible zoning: {parcel.zoning_code}. SB 35 requires residential or mixed-use zoning.")
    else:
        reasons.append(f"Zoning {parcel.zoning_code} permits residential use.")

    # 2. MINIMUM LOT SIZE (3,500 sq ft for practical multifamily)
    if parcel.lot_size_sqft < 3500:
        eligible = False
        reasons.append(f"Lot size {parcel.lot_size_sqft:,.0f} sq ft is below 3,500 sq ft minimum for multifamily development.")
    else:
        reasons.append(f"Lot size {parcel.lot_size_sqft:,.0f} sq ft meets minimum requirement.")

    # 3. RHNA COMPLIANCE CHECK
    # TODO: Integrate with RHNA API/database when available
    # For now, use placeholder logic based on city
    rhna_status = _check_rhna_status(parcel)
    if rhna_status['on_track']:
        # If jurisdiction is on track, SB 35 doesn't apply
        eligible = False
        reasons.append(f"Jurisdiction ({parcel.city}) is on track to meet RHNA housing goals. SB 35 applies only to jurisdictions below target.")
    else:
        reasons.append(f"Jurisdiction ({parcel.city}) has not met RHNA housing targets (assumed - verify with planning department).")
        requirements.append("Verify jurisdiction's actual RHNA progress with local planning department")

    # 4. SITE EXCLUSION CHECKS (Gov. Code § 65913.4(a)(6))
    site_exclusions = _check_site_exclusions(parcel)
    if site_exclusions:
        eligible = False
        exclusions.extend(site_exclusions)
        reasons.append(f"Site is excluded from SB 35: {', '.join(site_exclusions)}")

    # 5. PROTECTED TENANCY CHECKS (Gov. Code § 65913.4(a)(7))
    tenancy_issues = _check_protected_tenancy(parcel)
    if tenancy_issues:
        eligible = False
        reasons.extend(tenancy_issues)
    else:
        # Note: This assumes no existing tenants; actual verification needed
        requirements.append("Verify no protected tenancies (rent-controlled units, Ellis Act withdrawals in past 15 years)")

    # 6. MULTIFAMILY REQUIREMENT
    if eligible:
        max_units = calculate_sb35_max_units(parcel)
        if max_units < 2:
            eligible = False
            reasons.append(f"Parcel can only support {max_units} unit(s). SB 35 requires multifamily (2+ units).")
        else:
            reasons.append(f"Parcel can support {max_units} units (multifamily eligible).")

    return {
        'eligible': eligible,
        'reasons': reasons,
        'requirements': requirements,
        'exclusions': exclusions
    }


def _check_rhna_status(parcel: ParcelBase) -> dict:
    """
    Check jurisdiction's RHNA (Regional Housing Needs Allocation) status.

    Args:
        parcel: Parcel information

    Returns:
        {'on_track': bool, 'performance_level': str}

    Note:
        Uses official HCD RHNA determination data to check if jurisdiction
        is exempt from SB35 (meaning they met RHNA targets).
    """
    from app.services.rhna_service import rhna_service

    # Query official HCD RHNA data
    determination = rhna_service.get_sb35_affordability(
        jurisdiction=parcel.city,
        county=getattr(parcel, 'county', None)
    )

    # If jurisdiction is exempt, they met their RHNA targets
    on_track = determination.get('is_exempt', False)

    return {
        'on_track': on_track,
        'performance_level': 'high' if on_track else 'low'
    }


def _check_site_exclusions(parcel: ParcelBase) -> list:
    """
    Check for SB 35 site exclusions per Gov. Code § 65913.4(a)(6).

    Excluded sites:
    - Sites in coastal high hazard zones or special flood hazard areas
    - Prime farmland or farmland of statewide importance
    - Wetlands, as defined in federal Clean Water Act
    - Very high fire hazard severity zones
    - Hazardous waste sites (Cortese List)
    - Conservation lands or habitat for protected species
    - Lands under conservation easement
    - Historic properties on national/state/local register

    Args:
        parcel: Parcel information

    Returns:
        List of exclusion reasons, empty if no exclusions

    Note:
        Uses parcel attribute flags when available (in_coastal_high_hazard, in_prime_farmland, etc.).
        Falls back to heuristic checks when flags are not set.
    """
    exclusions = []

    # Check for coastal high hazard zone (use flag if available)
    # Note: This is about FEMA flood hazard, not CA Coastal Zone (which is for CDP requirements)
    if getattr(parcel, 'in_coastal_high_hazard', None) is True:
        exclusions.append("Site is in coastal high hazard zone (FEMA flood zone)")
    elif getattr(parcel, 'in_coastal_high_hazard', None) is None:
        # Only warn if both in coastal zone AND no explicit flood zone data
        # This prevents false positives for inland coastal cities
        in_coastal_zone = getattr(parcel, 'in_coastal_zone', None)
        in_flood_zone = getattr(parcel, 'in_flood_zone', None)

        # If we have coastal zone data but it's False, no need to check further
        if in_coastal_zone is False:
            pass  # Not in coastal zone, so not a coastal high hazard concern
        # If in coastal zone but not in flood zone, likely OK
        elif in_coastal_zone is True and in_flood_zone is False:
            pass  # In coastal zone for CDP but not flood zone, likely OK for SB35
        # If in coastal zone and flood zone, definitely flag
        elif in_coastal_zone is True and in_flood_zone is True:
            exclusions.append("Site is in coastal zone and flood zone - likely coastal high hazard (SB35 exclusion)")
        # If in coastal zone but flood zone unknown, warn for verification
        elif in_coastal_zone is True and in_flood_zone is None:
            exclusions.append("Site in coastal zone - verify FEMA flood hazard status for SB35 eligibility")
        # Fallback: No GIS data available, use conservative city-based heuristic
        elif in_coastal_zone is None:
            coastal_cities = ["Santa Monica", "Malibu", "Venice", "Manhattan Beach", "Hermosa Beach",
                              "Redondo Beach", "Palos Verdes", "San Pedro", "Long Beach"]
            if any(city.lower() in parcel.city.lower() for city in coastal_cities):
                exclusions.append("Potential coastal high hazard zone - requires FEMA flood map verification")

    # Check for flood zone
    if getattr(parcel, 'in_flood_zone', None) is True:
        exclusions.append("Site is in FEMA special flood hazard area")

    # Check for prime farmland
    if getattr(parcel, 'in_prime_farmland', None) is True:
        exclusions.append("Site is on prime farmland or farmland of statewide importance")
    elif getattr(parcel, 'in_prime_farmland', None) is None:
        # Fallback: check zoning for agricultural indicators
        if any(indicator in parcel.zoning_code.upper() for indicator in ["AG", "A-"]):
            exclusions.append(f"Zoning {parcel.zoning_code} may indicate agricultural land - verify farmland status")

    # Check for wetlands (using GIS data from CARI)
    if getattr(parcel, 'in_wetlands', None) is True:
        exclusions.append("Site contains wetlands (per Clean Water Act - CARI GIS data)")

    # Check for conservation area (using GIS data from CPAD)
    if getattr(parcel, 'in_conservation_area', None) is True:
        exclusions.append("Site has conservation easement or is in protected habitat area (CPAD)")
    elif getattr(parcel, 'in_conservation_area', None) is None:
        # Fallback: check zoning for conservation indicators
        if any(indicator in parcel.zoning_code.upper() for indicator in ["OS", "CONS"]):
            exclusions.append(f"Zoning {parcel.zoning_code} may indicate conservation land - verify status")

    # Check for historic property
    if getattr(parcel, 'is_historic_property', None) is True:
        exclusions.append("Site contains historic resource or structure (on historic register)")
    elif getattr(parcel, 'is_historic_property', None) is None:
        # Fallback: check year built as indicator
        if parcel.year_built and parcel.year_built < 1945:
            exclusions.append(f"Property built in {parcel.year_built} may be historic - verify with local historic register")

    # Check for very high fire hazard severity zone (using GIS data from CAL FIRE/LA County)
    fire_hazard_zone = getattr(parcel, 'fire_hazard_zone', None)
    if fire_hazard_zone and 'very high' in str(fire_hazard_zone).lower():
        exclusions.append("Site is in Very High Fire Hazard Severity Zone (CAL FIRE)")

    # Check for hazardous waste sites within 500ft (using GIS data from DTSC EnviroStor)
    if getattr(parcel, 'near_hazardous_waste', None) is True:
        exclusions.append("Site is within 500 feet of hazardous waste site (DTSC Cortese List)")

    return exclusions


def _check_protected_tenancy(parcel: ParcelBase) -> list:
    """
    Check for protected tenancy issues per Gov. Code § 65913.4(a)(7).

    SB 35 prohibits:
    - Demolition or alteration of housing subject to rent control or price restrictions
    - Demolition of occupied housing (without relocation assistance)
    - Sites where owner has withdrawn units via Ellis Act in past 15 years
    - Sites where owner has demolished housing in past 10 years

    Args:
        parcel: Parcel information

    Returns:
        List of tenancy issues, empty if no issues

    Note:
        Uses parcel attribute flags when available (has_rent_controlled_units, has_ellis_act_units, etc.).
        Falls back to heuristic checks when flags are not set.
    """
    issues = []

    # Check for rent-controlled units
    if getattr(parcel, 'has_rent_controlled_units', None) is True:
        issues.append("Site has rent-controlled units. SB 35 prohibits demolition or alteration of rent-controlled housing.")
        return issues  # Fatal issue - no need to check further

    # Check for deed-restricted affordable housing
    if getattr(parcel, 'has_deed_restricted_affordable', None) is True:
        issues.append("Site has deed-restricted affordable housing. SB 35 prohibits demolition of price-restricted units.")
        return issues  # Fatal issue

    # Check for Ellis Act withdrawals
    if getattr(parcel, 'has_ellis_act_units', None) is True:
        issues.append("Site had units withdrawn under Ellis Act within past 15 years. SB 35 prohibits development on Ellis Act sites.")
        return issues  # Fatal issue

    # Check for recent tenancy
    if getattr(parcel, 'has_recent_tenancy', None) is True:
        issues.append("Site had residential tenancy within last 10 years. Tenant relocation assistance and compliance required.")
        # Note: This is not necessarily fatal - relocation can be provided

    # Fallback checks when flags are not available
    if getattr(parcel, 'has_rent_controlled_units', None) is None:
        # Check for existing units (potential tenancy)
        if parcel.existing_units > 0:
            # In rent control jurisdictions, flag for verification
            rent_control_cities = ["Los Angeles", "San Francisco", "Oakland", "Berkeley", "Santa Monica",
                                   "West Hollywood", "Beverly Hills", "East Palo Alto", "San Jose"]
            if any(city in parcel.city for city in rent_control_cities):
                issues.append(f"{parcel.city} has rent control ordinances. Property has {parcel.existing_units} existing unit(s). Verify: (1) no rent control/price restrictions, (2) no Ellis Act withdrawal in past 15 years, (3) relocation plan if tenants will be displaced.")
            else:
                # Non-rent control jurisdiction - just verify displacement compliance
                if parcel.existing_building_sqft > 0:
                    issues.append(f"Existing building on site with {parcel.existing_units} unit(s). If demolition proposed, verify compliance with tenant displacement and relocation requirements.")

    return issues


def is_sb35_eligible(parcel: ParcelBase) -> bool:
    """
    Check if parcel is eligible for SB35 (legacy function for backward compatibility).

    Args:
        parcel: Parcel information

    Returns:
        True if eligible

    Note:
        This is a simplified eligibility check maintained for backward compatibility.
        Use can_apply_sb35() for detailed eligibility analysis with reasons.
    """
    result = can_apply_sb35(parcel)
    return result['eligible']


def get_labor_requirements(max_units: int) -> list:
    """
    Return applicable labor requirements based on unit count.

    SB 35 labor standards per Gov. Code § 65913.4(a)(8):
    - Prevailing wage: Required for projects with 10 or more units
    - Skilled and trained workforce: Required for projects with 75 or more units

    Args:
        max_units: Maximum number of units in development

    Returns:
        List of labor requirement notes

    References:
        - Gov. Code § 65913.4(a)(8) - SB 35 Labor Standards
        - Labor Code § 1720 et seq. - Prevailing Wage Law
        - Labor Code § 2600-2603 - Skilled and Trained Workforce
    """
    requirements = []

    if max_units >= 10:
        requirements.append("LABOR: Prevailing wage required (10+ units)")
        requirements.append("  - All workers must be paid prevailing wage rates per Labor Code § 1720")
        requirements.append("  - Must file certified payroll records with Labor Commissioner")
        requirements.append("  - Penalties for non-compliance: contract debarment and back wages")

    if max_units >= 75:
        requirements.append("LABOR: Skilled and trained workforce required (75+ units)")
        requirements.append("  - Apprentices from state-approved programs must constitute specified hours")
        requirements.append("  - Graduates of approved apprenticeship programs required for journey-level work")
        requirements.append("  - Contractor must participate in approved apprenticeship program for each trade")
        requirements.append("  - Per Labor Code § 2600-2603")

    if max_units >= 10:
        # General note about enforcement
        requirements.append("Labor compliance monitored by Division of Labor Standards Enforcement (DLSE)")

    return requirements


def get_affordability_requirement(parcel: ParcelBase) -> dict:
    """
    Determine affordability requirement based on jurisdiction's RHNA progress.

    Per Gov. Code § 65913.4(a)(5), affordability requirements are:
    - 10% of units at affordable rent for lower income households IF jurisdiction
      has met > 50% of its RHNA above moderate-income housing need
    - 50% of units at affordable rent (with income targeting) IF jurisdiction
      has NOT met > 50% of its RHNA above moderate-income housing need

    Income categories (per Health & Safety Code § 50093):
    - Very Low Income: ≤50% of area median income (AMI)
    - Lower Income: >50% and ≤80% of AMI
    - Moderate Income: >80% and ≤120% of AMI

    Args:
        parcel: Parcel information

    Returns:
        {
            'percentage': float,  # Required percentage (10.0 or 50.0)
            'income_levels': List[str],  # Target income levels
            'notes': List[str]  # Additional documentation
        }

    References:
        - Gov. Code § 65913.4(a)(5) - SB 35 Affordability Requirements
        - Health & Safety Code § 50093 - Income Limit Definitions
    """
    from app.services.rhna_service import rhna_service

    # Query official HCD RHNA determination data
    return rhna_service.get_sb35_affordability(
        jurisdiction=parcel.city,
        county=getattr(parcel, 'county', None)
    )


def get_affordability_percentage(parcel: ParcelBase) -> float:
    """
    Get affordability percentage (legacy function for backward compatibility).

    Args:
        parcel: Parcel information

    Returns:
        Required percentage of affordable units (10.0 or 50.0)

    Note:
        Use get_affordability_requirement() for detailed affordability documentation.
    """
    result = get_affordability_requirement(parcel)
    return result['percentage']


def calculate_sb35_max_units(parcel: ParcelBase) -> int:
    """
    Calculate maximum units under SB35.

    Args:
        parcel: Parcel information

    Returns:
        Maximum number of units
    """
    # SB35 allows development at maximum allowed density
    zoning_code = parcel.zoning_code.upper()

    # Determine density by zone
    if "R2" in zoning_code or "RD" in zoning_code:
        density_per_acre = 15.0
    elif "R3" in zoning_code or "RM" in zoning_code:
        density_per_acre = 30.0
    elif "R4" in zoning_code or "RH" in zoning_code:
        density_per_acre = 60.0
    elif "MU" in zoning_code or "MIXED" in zoning_code:
        density_per_acre = 40.0
    else:
        # Conservative default
        density_per_acre = 20.0

    max_units = int((parcel.lot_size_sqft / 43560) * density_per_acre)

    return max(max_units, 2)  # Minimum 2 units for multifamily


def get_max_far(parcel: ParcelBase) -> float:
    """
    Get maximum FAR based on zoning (tier-aware).

    Args:
        parcel: Parcel information

    Returns:
        Maximum floor area ratio
    """
    from app.rules.tiered_standards import compute_max_far

    # Use tiered FAR resolver which considers overlays
    far, _ = compute_max_far(parcel)
    return far


def get_max_height(parcel: ParcelBase) -> float:
    """
    Get maximum height based on zoning (tier-aware).

    Args:
        parcel: Parcel information

    Returns:
        Maximum height in feet
    """
    from app.rules.tiered_standards import compute_max_height

    # Use tiered height resolver which considers overlays
    height, _ = compute_max_height(parcel)
    return height
