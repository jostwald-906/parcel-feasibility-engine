"""
AB2011 (2022) corridor housing rules.

Assembly Bill 2011 (Affordable Housing and High Road Jobs Act of 2022)
establishes ministerial approval for multifamily housing on parcels zoned
for office/commercial/retail uses, subject to: labor standards, affordability
requirements, site/location constraints, and minimum state floors for density
and height along eligible commercial corridors.

This module implements a simplified policy model for AB2011 focused on:
- Eligibility on commercial/office/mixed-use zoning (no existing-building requirement)
- Application of state minimum floors by corridor tier: 30/50/80 u/ac and 35/45/65 ft
- Local-versus-state precedence (final = max(local, state floor))
- Ministerial approval with affordability requirement placeholder

Notes:
- Corridor mapping, labor standards, and detailed site exclusions are out-of-scope
  in this simplified implementation and would be validated upstream.
"""
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from typing import Optional, Tuple, Dict, List
import math
from datetime import datetime
from app.rules.state_law.ab2097 import apply_ab2097_parking_reduction

# ---------------------------------------------------------------------------
# AB2011 TODOs (Santa Monica specifics pending)
#
# TODO(SM): Replace heuristic corridor-tier inference with official corridor map
#           and eligibility criteria (ROW width, frontage length, spacing).
# TODO(SM): Enforce site exclusions (wetlands, habitat, hazardous, Alquist-Priolo,
#           prime/statewide farmland, conservation easements) once layers/flags
#           are integrated into Parcel/overlays.
# TODO(SM): Enforce protected housing + tenancy constraints (rent-controlled,
#           deed-restricted, recent tenancy lookback, demolition of res units).
# TODO(SM): Gate eligibility on labor standards (prevailing wage, skilled &
#           trained workforce thresholds, healthcare benefits if applicable).
# TODO(SM): Apply AB 2097 parking elimination near transit; support car-share
#           areas; integrate local objective design standards (ODDS) for
#           front setbacks, massing, open space, etc., without dipping below
#           state floors.
# TODO(SM): Clarify Coastal Zone applicability (LCP, CDP requirements or limits).
# TODO(SM): Mixed-income affordability % and income levels: replace placeholder
#           with Santa Monica/HCD-specified thresholds.
# ---------------------------------------------------------------------------

# Placeholder constants pending local policy integration
DEFAULT_LOT_COVERAGE_PCT = 60.0  # TODO(SM): derive from local ODDS/objective standards
DEFAULT_STORY_HEIGHT_FT = 12.0   # TODO(SM): confirm story height assumption for height→stories
MIXED_INCOME_MIN_AFFORDABILITY_PCT = 15.0  # TODO(SM): replace with AB2011 mixed-income thresholds
PARKING_PER_UNIT_DEFAULT = 0.5   # TODO(SM): integrate AB 2097 + car-share to allow zero

def analyze_ab2011(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Analyze commercial-to-residential conversion potential under AB2011.

    Now with comprehensive eligibility checking - only returns scenario if
    parcel passes all AB 2011 requirements including corridor eligibility,
    site exclusions, protected housing checks, and labor standards.

    Args:
        parcel: Parcel information with all relevant flags

    Returns:
        AB2011 conversion scenario if eligible, None if ineligible
    """
    # Comprehensive eligibility check with detailed reasons
    eligibility = can_apply_ab2011(parcel)

    if not eligibility["eligible"]:
        # Parcel is ineligible - return None
        # Exclusion reasons available in eligibility["exclusions"]
        return None

    # Get corridor information from eligibility check
    corridor_info = eligibility["corridor_info"]
    tier = corridor_info["tier"]
    tier_name = corridor_info["tier_name"]

    # Apply state floors with local precedence (locals unknown -> None)
    floors = apply_ab2011_standards(parcel, tier=tier)
    final_min_units = max(2, floors["final_min_units"])  # ensure multifamily
    final_min_height = floors["final_min_height_ft"]

    # Derive stories from height (approx 12 ft/story), minimum 2 stories
    max_stories = max(2, int(math.ceil(final_min_height / DEFAULT_STORY_HEIGHT_FT)))
    max_height_ft = final_min_height

    # Building area placeholder from coverage (assume 60% lot coverage over 1 story)
    lot_area = parcel.lot_size_sqft
    lot_coverage_pct = DEFAULT_LOT_COVERAGE_PCT
    max_building_sqft = lot_area * (lot_coverage_pct / 100.0)

    # Initial parking calculation (may be reduced by AB 2097)
    parking_spaces_required = int(final_min_units * PARKING_PER_UNIT_DEFAULT)

    setbacks = {"front": 0.0, "rear": 0.0, "side": 0.0}

    # Affordability placeholder for mixed-income track
    affordability_pct = MIXED_INCOME_MIN_AFFORDABILITY_PCT
    affordable_units_required = int(math.ceil(final_min_units * (affordability_pct / 100.0)))

    # Build notes with eligibility reasons
    notes = [
        "AB2011 corridor housing (mixed-income track)",
        f"Corridor: {tier_name}",
        f"State floors applied: {floors['state_min_density_u_ac']} u/ac, {floors['state_min_height_ft']} ft",
        "Ministerial approval (objective standards only; CEQA ministerial)",
        f"Affordability requirement: {affordability_pct}% ({affordable_units_required} units)",
    ]

    # Add labor standards notes
    labor_info = check_labor_compliance(parcel, project_units=final_min_units)
    notes.append("LABOR STANDARDS:")
    notes.append("  - Prevailing wage: REQUIRED (all projects)")
    if labor_info["skilled_workforce_required"]:
        notes.append("  - Skilled & trained workforce: REQUIRED (50+ units)")
    notes.append("  - Healthcare benefits: Recommended")

    # Add coastal zone notes if applicable
    if parcel.in_coastal_zone:
        notes.append("COASTAL ZONE REQUIREMENTS:")
        notes.append("  - Parcel is in California Coastal Zone")
        notes.append("  - Coastal Development Permit (CDP) may be required")
        notes.append("  - Must comply with Local Coastal Program (LCP)")
        notes.append("  - Coordinate with California Coastal Commission")

    scenario = DevelopmentScenario(
        scenario_name="AB2011 Corridor Housing",
        legal_basis="AB2011 (2022) - Corridor Multifamily (Mixed-Income)",
        max_units=final_min_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=affordable_units_required,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.85,
        notes=notes,
    )

    # Apply AB 2097 parking reduction if applicable
    scenario = apply_ab2097_parking_reduction(scenario, parcel)

    return scenario


def analyze_ab2011_tracks(parcel: ParcelBase) -> List[DevelopmentScenario]:
    """Return AB2011 scenarios for both mixed-income and 100% affordable tracks.

    The two tracks share the same state floors for density/height; the primary
    difference is the affordability requirement. This function produces both
    variants for downstream selection.

    Now with comprehensive eligibility checking - only returns scenarios if
    parcel passes all AB 2011 requirements.
    """
    scenarios: List[DevelopmentScenario] = []

    # Comprehensive eligibility check
    eligibility = can_apply_ab2011(parcel)
    if not eligibility["eligible"]:
        # Return empty list if ineligible
        return scenarios

    # Get corridor information from eligibility check
    corridor_info = eligibility["corridor_info"]
    tier = corridor_info["tier"]
    tier_name = corridor_info["tier_name"]

    floors = apply_ab2011_standards(parcel, tier=tier)
    final_min_units = max(2, floors["final_min_units"])  # ensure multifamily
    final_min_height = floors["final_min_height_ft"]

    lot_area = parcel.lot_size_sqft
    lot_coverage_pct = 60.0
    max_building_sqft = lot_area * (lot_coverage_pct / 100.0)
    max_stories = max(2, int(math.ceil(final_min_height / DEFAULT_STORY_HEIGHT_FT)))

    # Shared defaults
    setbacks = {"front": 0.0, "rear": 0.0, "side": 0.0}
    parking_spaces_required = int(final_min_units * PARKING_PER_UNIT_DEFAULT)

    # Labor standards information
    labor_info = check_labor_compliance(parcel, project_units=final_min_units)

    # Mixed-income track (placeholder 15%)
    mixed_aff_pct = MIXED_INCOME_MIN_AFFORDABILITY_PCT
    mixed_aff_units = int(math.ceil(final_min_units * mixed_aff_pct / 100.0))
    notes_mixed = [
        "AB2011 corridor housing (mixed-income track)",
        f"Corridor: {tier_name}",
        f"State floors applied: {floors['state_min_density_u_ac']} u/ac, {floors['state_min_height_ft']} ft",
        "Ministerial approval (objective standards only; CEQA ministerial)",
        f"Affordability requirement: {mixed_aff_pct}% ({mixed_aff_units} units)",
        "LABOR STANDARDS:",
        "  - Prevailing wage: REQUIRED (all projects)",
    ]
    if labor_info["skilled_workforce_required"]:
        notes_mixed.append("  - Skilled & trained workforce: REQUIRED (50+ units)")
    notes_mixed.append("  - Healthcare benefits: Recommended")

    # Add coastal zone notes if applicable
    if parcel.in_coastal_zone:
        notes_mixed.extend([
            "COASTAL ZONE REQUIREMENTS:",
            "  - Parcel is in California Coastal Zone",
            "  - Coastal Development Permit (CDP) may be required",
            "  - Must comply with Local Coastal Program (LCP)",
        ])

    scenario_mixed = DevelopmentScenario(
        scenario_name="AB2011 Corridor Housing (Mixed-Income)",
        legal_basis="AB2011 (2022) - Corridor Multifamily (Mixed-Income)",
        max_units=final_min_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=final_min_height,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=mixed_aff_units,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.85,
        notes=notes_mixed,
    )

    # Apply AB 2097 parking reduction if applicable
    scenario_mixed = apply_ab2097_parking_reduction(scenario_mixed, parcel)
    scenarios.append(scenario_mixed)

    # 100% affordable track
    aff100_units = final_min_units
    notes_100 = [
        "AB2011 corridor housing (100% affordable track)",
        f"Corridor: {tier_name}",
        f"State floors applied: {floors['state_min_density_u_ac']} u/ac, {floors['state_min_height_ft']} ft",
        "Ministerial approval (objective standards only; CEQA ministerial)",
        "All units restricted affordable (except manager unit)",
        "LABOR STANDARDS:",
        "  - Prevailing wage: REQUIRED (all projects)",
    ]
    if labor_info["skilled_workforce_required"]:
        notes_100.append("  - Skilled & trained workforce: REQUIRED (50+ units)")
    notes_100.append("  - Healthcare benefits: Recommended")

    # Add coastal zone notes if applicable
    if parcel.in_coastal_zone:
        notes_100.extend([
            "COASTAL ZONE REQUIREMENTS:",
            "  - Parcel is in California Coastal Zone",
            "  - Coastal Development Permit (CDP) may be required",
            "  - Must comply with Local Coastal Program (LCP)",
        ])

    scenario_100 = DevelopmentScenario(
        scenario_name="AB2011 Corridor Housing (100% Affordable)",
        legal_basis="AB2011 (2022) - Corridor Multifamily (100% Affordable)",
        max_units=final_min_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=final_min_height,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=aff100_units,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.85,
        notes=notes_100,
    )

    # Apply AB 2097 parking reduction if applicable
    scenario_100 = apply_ab2097_parking_reduction(scenario_100, parcel)
    scenarios.append(scenario_100)

    return scenarios


def can_apply_ab2011(parcel: ParcelBase) -> Dict[str, any]:
    """
    Comprehensive AB 2011 eligibility check with detailed reasons.

    Checks all eligibility requirements including:
    - Corridor eligibility (zoning and tier assignment)
    - Site exclusions (environmental, hazard, agricultural)
    - Protected housing and tenancy protections
    - Labor standards compliance

    Args:
        parcel: Parcel information with all relevant flags

    Returns:
        Dictionary containing:
        - eligible: bool - Overall eligibility determination
        - reasons: List[str] - Detailed list of eligibility factors
        - exclusions: List[str] - List of exclusion reasons if ineligible
        - warnings: List[str] - Non-fatal warnings and requirements
        - corridor_info: Dict - Corridor eligibility details from check_corridor_eligibility
    """
    reasons = []
    exclusions = []
    warnings = []
    eligible = True

    # Step 1: Check corridor eligibility
    corridor_info = check_corridor_eligibility(parcel)
    if not corridor_info["is_corridor"]:
        eligible = False
        exclusions.append("Parcel is not on an eligible AB 2011 corridor")
        exclusions.extend(corridor_info["reasons"])
    else:
        reasons.extend(corridor_info["reasons"])

    # Step 2: Site exclusion checks
    site_exclusions = check_site_exclusions(parcel)
    if site_exclusions["excluded"]:
        eligible = False
        exclusions.extend(site_exclusions["exclusion_reasons"])
    else:
        reasons.extend(site_exclusions["passed_checks"])

    # Step 3: Protected housing and tenancy checks
    housing_protections = check_protected_housing(parcel)
    if housing_protections["protected"]:
        eligible = False
        exclusions.extend(housing_protections["protection_reasons"])
    else:
        reasons.extend(housing_protections["passed_checks"])

    # Step 4: Labor standards compliance check
    labor_compliance = check_labor_compliance(parcel)
    if not labor_compliance["compliant"]:
        eligible = False
        exclusions.extend(labor_compliance["missing_requirements"])
    else:
        reasons.extend(labor_compliance["met_requirements"])

    # Add warnings for any non-fatal issues
    warnings.extend(labor_compliance.get("warnings", []))
    warnings.extend(housing_protections.get("warnings", []))

    return {
        "eligible": eligible,
        "reasons": reasons,
        "exclusions": exclusions,
        "warnings": warnings,
        "corridor_info": corridor_info
    }


def check_site_exclusions(parcel: ParcelBase) -> Dict[str, any]:
    """
    Check for AB 2011 site exclusions based on environmental and hazard criteria.

    AB 2011 excludes parcels that are:
    - In coastal high hazard zones
    - Prime farmland or farmland of statewide importance
    - Wetlands
    - Conservation areas or easements
    - Historic properties
    - Other environmentally sensitive areas

    Args:
        parcel: Parcel with site exclusion flags

    Returns:
        Dictionary with excluded status and reasons
    """
    exclusion_reasons = []
    passed_checks = []
    excluded = False

    # Coastal high hazard zone check
    if parcel.in_coastal_high_hazard:
        excluded = True
        exclusion_reasons.append("EXCLUDED: Parcel is in coastal high hazard zone")
    else:
        passed_checks.append("Site is not in coastal high hazard zone")

    # Prime farmland check
    if parcel.in_prime_farmland:
        excluded = True
        exclusion_reasons.append("EXCLUDED: Parcel is on prime farmland or farmland of statewide importance")
    else:
        passed_checks.append("Site is not on protected farmland")

    # Wetlands check
    if parcel.in_wetlands:
        excluded = True
        exclusion_reasons.append("EXCLUDED: Parcel contains wetlands or sensitive habitat")
    else:
        passed_checks.append("Site does not contain wetlands")

    # Conservation area check
    if parcel.in_conservation_area:
        excluded = True
        exclusion_reasons.append("EXCLUDED: Parcel has conservation easement or is in protected area")
    else:
        passed_checks.append("Site is not in conservation area")

    # Historic property check
    if parcel.is_historic_property:
        excluded = True
        exclusion_reasons.append("EXCLUDED: Parcel contains historic resource or structure")
    else:
        passed_checks.append("Site is not a designated historic property")

    # Flood zone (warning but not absolute exclusion per AB 2011)
    if parcel.in_flood_zone:
        passed_checks.append("WARNING: Parcel is in flood hazard zone - additional requirements may apply")

    # Alquist-Priolo earthquake fault zone check (using GIS data from CGS)
    if getattr(parcel, 'in_earthquake_fault_zone', None) is True:
        excluded = True
        exclusion_reasons.append("EXCLUDED: Parcel is in Alquist-Priolo earthquake fault zone")
    else:
        passed_checks.append("Site is not in Alquist-Priolo earthquake fault zone")

    # Hazardous waste proximity check (using GIS data from DTSC EnviroStor)
    if getattr(parcel, 'near_hazardous_waste', None) is True:
        excluded = True
        exclusion_reasons.append("EXCLUDED: Parcel is within 500 feet of hazardous waste site (DTSC Cortese List)")
    else:
        passed_checks.append("Site is not near hazardous waste sites")

    # Fire hazard zone check (using GIS data from CAL FIRE/LA County)
    fire_hazard_zone = getattr(parcel, 'fire_hazard_zone', None)
    if fire_hazard_zone and 'very high' in str(fire_hazard_zone).lower():
        excluded = True
        exclusion_reasons.append("EXCLUDED: Site is in Very High Fire Hazard Severity Zone")
    else:
        passed_checks.append("Site is not in Very High Fire Hazard Severity Zone")

    return {
        "excluded": excluded,
        "exclusion_reasons": exclusion_reasons,
        "passed_checks": passed_checks
    }


def check_protected_housing(parcel: ParcelBase) -> Dict[str, any]:
    """
    Check for protected housing and tenancy that would exclude AB 2011 eligibility.

    AB 2011 protections include:
    - Rent-controlled units
    - Deed-restricted affordable housing
    - Ellis Act withdrawn units (within lookback period)
    - Recent residential tenancy (10-year lookback)
    - Demolition of residential units

    Args:
        parcel: Parcel with protected housing flags

    Returns:
        Dictionary with protection status and reasons
    """
    protection_reasons = []
    passed_checks = []
    warnings = []
    protected = False

    # Rent control check
    # First check manual override
    if hasattr(parcel, 'rent_control_status') and parcel.rent_control_status:
        status_lower = parcel.rent_control_status.lower()
        if status_lower == 'yes':
            protected = True
            protection_reasons.append("EXCLUDED: Parcel contains rent-controlled units (AB 2011 protection) - MANUAL OVERRIDE")
        elif status_lower == 'no':
            passed_checks.append("No rent-controlled units on parcel (manual override)")
        elif status_lower == 'unknown':
            warnings.append("Rent control status UNKNOWN - verification required with Santa Monica Rent Control Board before proceeding with AB2011")
    # Fall back to has_rent_controlled_units flag
    elif parcel.has_rent_controlled_units:
        protected = True
        protection_reasons.append("EXCLUDED: Parcel contains rent-controlled units (AB 2011 protection)")
    else:
        passed_checks.append("No rent-controlled units on parcel")

    # Deed-restricted affordable housing check
    if parcel.has_deed_restricted_affordable:
        protected = True
        protection_reasons.append("EXCLUDED: Parcel has deed-restricted affordable housing (protected)")
    else:
        passed_checks.append("No deed-restricted affordable housing on parcel")

    # Ellis Act units check
    if parcel.has_ellis_act_units:
        protected = True
        protection_reasons.append(
            "EXCLUDED: Parcel had units withdrawn under Ellis Act within lookback period"
        )
    else:
        passed_checks.append("No Ellis Act withdrawn units")

    # Recent residential tenancy check (10-year lookback)
    if parcel.has_recent_tenancy:
        protected = True
        protection_reasons.append(
            "EXCLUDED: Parcel had residential tenancy within last 10 years (AB 2011 protection)"
        )
    else:
        passed_checks.append("No recent residential tenancy (10-year lookback)")

    # Protected units count check
    if parcel.protected_units_count and parcel.protected_units_count > 0:
        protected = True
        protection_reasons.append(
            f"EXCLUDED: Parcel has {parcel.protected_units_count} protected residential units"
        )

    # Existing residential units warning
    if parcel.existing_units > 0:
        warnings.append(
            f"WARNING: Parcel has {parcel.existing_units} existing units - "
            "verify no demolition of residential units required"
        )

    # TODO(SM): Add tenant relocation plan requirement check
    # NOTE: Rent control database integration implemented in app/services/rent_control_api.py
    #       with caching, timeout handling, and manual override support via rent_control_status field
    # TODO(SM): Add affordability covenant verification

    return {
        "protected": protected,
        "protection_reasons": protection_reasons,
        "passed_checks": passed_checks,
        "warnings": warnings
    }


def check_labor_compliance(parcel: ParcelBase, project_units: Optional[int] = None) -> Dict[str, any]:
    """
    Check AB 2011 labor standards compliance requirements.

    AB 2011 has strict labor requirements that are prerequisites for eligibility:
    - Prevailing wage: REQUIRED for ALL projects (0+ units)
    - Skilled & trained workforce: REQUIRED for projects with 50+ units
    - Healthcare benefits: Varies by jurisdiction (recommended)

    These are gating requirements - projects must commit to compliance
    before receiving AB 2011 ministerial approval benefits.

    Args:
        parcel: Parcel with labor compliance commitment flags
        project_units: Number of units planned (if known, for threshold checks)

    Returns:
        Dictionary containing:
        - compliant: bool - Whether all required labor standards are met
        - met_requirements: List[str] - Labor requirements that are satisfied
        - missing_requirements: List[str] - Required labor standards not met
        - warnings: List[str] - Additional labor-related notices
    """
    met_requirements = []
    missing_requirements = []
    warnings = []
    compliant = True

    # Prevailing wage is MANDATORY for all AB 2011 projects
    if parcel.prevailing_wage_commitment:
        met_requirements.append("Prevailing wage commitment confirmed (REQUIRED for all AB 2011)")
    else:
        compliant = False
        missing_requirements.append(
            "REQUIRED: Prevailing wage commitment missing - MANDATORY for all AB 2011 projects"
        )

    # Determine project size for skilled workforce threshold
    # Use provided project_units, or estimate from parcel if not provided
    estimated_units = project_units
    if estimated_units is None and parcel.lot_size_sqft:
        # Rough estimate: assume mid-tier (50 u/ac) for threshold check
        estimated_units = int((parcel.lot_size_sqft / 43560.0) * 50)

    # Skilled & trained workforce required for 50+ units
    skilled_workforce_required = False
    if estimated_units and estimated_units >= 50:
        skilled_workforce_required = True
        if parcel.skilled_trained_workforce_commitment:
            met_requirements.append(
                f"Skilled & trained workforce commitment confirmed (REQUIRED for {estimated_units} units >= 50)"
            )
        else:
            compliant = False
            missing_requirements.append(
                f"REQUIRED: Skilled & trained workforce commitment missing - "
                f"MANDATORY for projects with 50+ units (project has {estimated_units} units)"
            )
    else:
        if estimated_units:
            met_requirements.append(
                f"Skilled & trained workforce not required (project has {estimated_units} units < 50)"
            )
        else:
            warnings.append(
                "Unable to determine unit count - verify skilled & trained workforce "
                "requirement if project will have 50+ units"
            )

    # Healthcare benefits (jurisdiction-dependent, treated as best practice)
    if parcel.healthcare_benefits_commitment:
        met_requirements.append("Healthcare benefits commitment confirmed (best practice)")
    else:
        warnings.append(
            "Healthcare benefits commitment not indicated - may be required by local jurisdiction"
        )

    # Add general labor requirements notice
    if compliant:
        met_requirements.append(
            "Project meets AB 2011 labor standards requirements for ministerial approval"
        )
    else:
        warnings.append(
            "AB 2011 provides ministerial approval ONLY when labor standards are met - "
            "failure to commit results in ineligibility"
        )

    # TODO(SM): Add Santa Monica-specific labor requirements
    # TODO(SM): Integrate with prevailing wage rate schedules
    # TODO(SM): Add apprenticeship ratio requirements
    # TODO(SM): Verify healthcare benefits threshold for Santa Monica

    return {
        "compliant": compliant,
        "met_requirements": met_requirements,
        "missing_requirements": missing_requirements,
        "warnings": warnings,
        "skilled_workforce_required": skilled_workforce_required,
        "estimated_units": estimated_units
    }


def is_ab2011_eligible(parcel: ParcelBase) -> bool:
    """
    Simplified boolean eligibility check for AB2011 conversion.

    For detailed eligibility with reasons, use can_apply_ab2011() instead.

    Args:
        parcel: Parcel information

    Returns:
        True if eligible for commercial-to-residential conversion
    """
    eligibility = can_apply_ab2011(parcel)
    return eligibility["eligible"]


def estimate_conversion_feasibility(parcel: ParcelBase) -> dict:
    """
    Provide detailed feasibility analysis for AB2011 conversion.

    Args:
        parcel: Parcel information

    Returns:
        Dictionary with feasibility details
    """
    feasibility = {
        "eligible": is_ab2011_eligible(parcel),
        "estimated_units": 0,
        "estimated_cost_per_sqft": 0,
        "considerations": [],
        "requirements": []
    }

    if not feasibility["eligible"]:
        feasibility["considerations"].append("Not eligible for AB2011 conversion")
        return feasibility

    # Estimate units
    avg_unit_size = 850.0
    estimated_units = int(parcel.existing_building_sqft / avg_unit_size)
    feasibility["estimated_units"] = estimated_units

    # Estimate conversion cost
    # Varies widely: $100-300/sq ft depending on building condition
    if parcel.year_built:
        building_age = datetime.now().year - parcel.year_built
        if building_age > 50:
            cost_per_sqft = 250.0  # Higher for older buildings
        elif building_age > 30:
            cost_per_sqft = 200.0
        else:
            cost_per_sqft = 150.0
    else:
        cost_per_sqft = 200.0

    feasibility["estimated_cost_per_sqft"] = cost_per_sqft

    # Key considerations
    feasibility["considerations"] = [
        "Existing building condition assessment required",
        "Seismic retrofit may be necessary",
        "Plumbing and electrical upgrades likely needed",
        "ADA accessibility upgrades required",
        "Fire safety system upgrades required",
        f"Estimated conversion cost: ${int(cost_per_sqft * parcel.existing_building_sqft):,}"
    ]

    # Requirements
    feasibility["requirements"] = [
        "Minimum 15% affordable housing",
        "Ministerial review application",
        "Building code compliance verification",
        "Environmental clearance",
        "Tenant relocation plan if applicable",
        "Prevailing wage compliance"
    ]

    return feasibility


# ----------------------------------------------------------------------------
# AB2011 standards application helpers (refactor: eligibility vs. standards)
# ----------------------------------------------------------------------------

def check_corridor_eligibility(parcel: ParcelBase) -> Dict[str, any]:
    """
    Check corridor eligibility for AB 2011 using ROW width-based classification.

    AB 2011 uses corridor width (right-of-way), not tiers. This function checks:
    1. Commercial zoning requirement
    2. Street ROW width (70-150 ft for eligibility)
    3. Transit proximity (overrides width for higher density)

    Args:
        parcel: Parcel information including zoning, street_row_width, and location

    Returns:
        Dictionary containing:
        - is_corridor: bool - Whether parcel is on an eligible corridor
        - tier: str | None - Legacy field for compatibility (maps to classification)
        - tier_name: str | None - Descriptive classification name
        - reasons: List[str] - List of reasons for eligibility determination
        - state_floors: Dict | None - State minimum density/height floors
    """
    reasons = []
    is_corridor = False

    # Check if parcel has required zoning for corridor housing
    zoning_code = (parcel.zoning_code or "").upper()
    commercial_zones = ["C", "COMMERCIAL", "OFFICE", "O", "M", "MIXED"]
    is_commercial = any(zone in zoning_code for zone in commercial_zones)

    if not is_commercial:
        reasons.append("Parcel is not zoned for commercial/office/mixed-use")
        return {
            "is_corridor": False,
            "tier": None,
            "tier_name": None,
            "reasons": reasons,
            "state_floors": None
        }

    reasons.append(f"Parcel has eligible commercial zoning: {parcel.zoning_code}")

    # Get ROW width-based standards
    standards = determine_ab2011_standards(parcel)

    if not standards:
        row_width = getattr(parcel, 'street_row_width', None)
        if row_width is None:
            reasons.append("Street ROW width not provided - cannot determine eligibility")
            reasons.append("Manual ROW width entry required (70-150 ft for eligibility)")
        elif row_width < 70:
            reasons.append(f"Street ROW width ({row_width:.0f} ft) is below minimum (70 ft)")
        elif row_width > 150:
            reasons.append(f"Street ROW width ({row_width:.0f} ft) exceeds maximum (150 ft)")
        else:
            reasons.append(f"Corridor classification failed for {row_width:.0f} ft ROW")

        return {
            "is_corridor": False,
            "tier": None,
            "tier_name": None,
            "reasons": reasons,
            "state_floors": None
        }

    # Parcel is on eligible corridor
    is_corridor = True
    classification = standards['classification']
    tier_name = f"AB 2011 {classification}"
    reasons.append(f"Corridor classification: {classification}")
    reasons.append(standards['basis'])
    reasons.append(f"State minimum floors: {standards['density_per_acre']} u/ac density, {standards['max_height_ft']} ft height")

    # Map classification to legacy tier field for compatibility
    # Transit-Adjacent or Wide Corridor -> "high"
    # Narrow Corridor -> "mid"
    # Small Lot -> "low"
    tier_map = {
        'Transit-Adjacent': 'high',
        'Wide Corridor': 'high',
        'Narrow Corridor': 'mid',
        'Small Lot': 'low'
    }
    tier = tier_map.get(classification, 'mid')

    state_floors = {
        'min_density_u_ac': standards['density_per_acre'],
        'min_height_ft': standards['max_height_ft']
    }

    return {
        "is_corridor": is_corridor,
        "tier": tier,  # Legacy compatibility
        "tier_name": tier_name,
        "reasons": reasons,
        "state_floors": state_floors
    }


def determine_ab2011_standards(parcel: ParcelBase) -> Optional[Dict[str, any]]:
    """
    Determine AB 2011 development standards based on corridor width.

    Gov. Code § 65912.124 - Density and height standards:
    - 70-99 ft ROW: 40 units/acre, 35 ft height
    - 100-150 ft ROW: 60 units/acre, 45 ft height
    - Transit-adjacent (<0.5 mi): 80 units/acre, 65 ft height (not coastal)
    - Small lots (<1 acre): 30 units/acre minimum

    Args:
        parcel: Parcel information with street_row_width and location data

    Returns:
        Dictionary with classification, density, height, and basis, or None if not eligible
    """
    row_width = getattr(parcel, 'street_row_width', None)
    near_major_transit = getattr(parcel, 'near_transit', False)
    in_coastal = getattr(parcel, 'in_coastal_zone', False)
    lot_acres = (parcel.lot_size_sqft or 0) / 43560.0

    # Transit-adjacent takes precedence (if not coastal)
    if near_major_transit and not in_coastal:
        return {
            'classification': 'Transit-Adjacent',
            'density_per_acre': 80.0,
            'max_height_ft': 65.0,
            'basis': 'Within 0.5 mile of major transit stop (§65912.124(b)(3))'
        }

    # Wide corridor (100-150 ft ROW)
    if row_width and row_width >= 100 and row_width <= 150:
        return {
            'classification': 'Wide Corridor',
            'density_per_acre': 60.0,
            'max_height_ft': 45.0,
            'basis': f'{row_width:.0f} ft ROW (§65912.124(b)(2))'
        }

    # Narrow corridor (70-99 ft ROW)
    if row_width and row_width >= 70 and row_width < 100:
        return {
            'classification': 'Narrow Corridor',
            'density_per_acre': 40.0,
            'max_height_ft': 35.0,
            'basis': f'{row_width:.0f} ft ROW (§65912.124(b)(1))'
        }

    # Small lot minimum (applies to any eligible corridor < 1 acre)
    if lot_acres < 1.0 and row_width and row_width >= 70:
        return {
            'classification': 'Small Lot',
            'density_per_acre': 30.0,
            'max_height_ft': 35.0,
            'basis': f'{lot_acres:.2f} acre lot (§65912.124(c))'
        }

    # Not eligible - no qualifying corridor width
    return None
def ab2011_state_floors(tier: str) -> Dict[str, float]:
    """Return state minimum floors for AB2011 by corridor/tier.

    Tiers implement simplified state floors for testing/documentation:
    - low: min density 30 u/ac, min height 35 ft
    - mid: min density 50 u/ac, min height 45 ft
    - high: min density 80 u/ac, min height 65 ft

    [CITE] AB 2011 corridor-based minimum density and height floors.
    """
    t = (tier or "").lower()
    if t == "high":
        return {"min_density_u_ac": 80.0, "min_height_ft": 65.0}
    if t == "mid":
        return {"min_density_u_ac": 50.0, "min_height_ft": 45.0}
    # default to low
    return {"min_density_u_ac": 30.0, "min_height_ft": 35.0}


def ab2011_precedence(local_value: Optional[float], state_floor: float) -> float:
    """Choose the applicable standard given a state floor and an optional local value.

    Rules:
    - State floors are minimums; final = max(local_value, state_floor).
    - If local_value is None or not positive, use the state floor.
    """
    if local_value is None:
        return float(state_floor)
    try:
        lv = float(local_value)
    except (TypeError, ValueError):
        lv = float('nan')
    if not (lv > 0):  # handles NaN and non-positive values
        return float(state_floor)
    return max(lv, float(state_floor))


def apply_ab2011_standards(
    parcel: ParcelBase,
    tier: str,
    local_min_density_u_ac: Optional[float] = None,
    local_max_height_ft: Optional[float] = None,
) -> Dict[str, float]:
    """Apply AB2011 state floors with local-vs-state precedence.

    Inputs:
    - parcel: for lot size to compute minimum units required by density floor
    - tier: one of "low" | "mid" | "high" to select state floors
    - local_min_density_u_ac: jurisdictional minimum density if present
    - local_max_height_ft: jurisdictional maximum height allowance

    Outputs dict:
    - tier: returned as provided
    - state_min_density_u_ac, state_min_height_ft
    - final_min_density_u_ac: max(local_min_density_u_ac, state_min_density_u_ac)
    - final_min_height_ft: max(local_max_height_ft, state_min_height_ft)
    - lot_acres: parcel lot area in acres
    - final_min_units: ceil(final_min_density_u_ac * lot_acres)

    [CITE] AB 2011 minimum density and height floors with local precedence.
    """
    floors = ab2011_state_floors(tier)
    state_density = floors["min_density_u_ac"]
    state_height = floors["min_height_ft"]

    final_density = ab2011_precedence(local_min_density_u_ac, state_density)
    final_height = ab2011_precedence(local_max_height_ft, state_height)

    lot_acres = (parcel.lot_size_sqft or 0) / 43560.0
    final_min_units = int(math.ceil(final_density * lot_acres)) if lot_acres > 0 else 0

    return {
        "tier": (tier or "low").lower(),
        "state_min_density_u_ac": state_density,
        "state_min_height_ft": state_height,
        "final_min_density_u_ac": final_density,
        "final_min_height_ft": final_height,
        "lot_acres": lot_acres,
        "final_min_units": final_min_units,
    }
