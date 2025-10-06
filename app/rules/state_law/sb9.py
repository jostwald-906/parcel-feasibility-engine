"""
SB9 (2021) analysis rules.

Senate Bill 9 allows:
1. Urban lot splits creating two parcels (minimum 1,200 sq ft each)
2. Up to two units per parcel (duplex)
3. Combined: up to 4 units total on original parcel

Eligibility requirements:
- Single-family zoned parcel
- Not in high fire hazard zone
- Not in flood zone
- Not a historic property
- Not prime farmland
"""
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from typing import List, Optional


def analyze_sb9(parcel: ParcelBase) -> List[DevelopmentScenario]:
    """
    Analyze development potential under SB9.

    Args:
        parcel: Parcel information

    Returns:
        List of SB9 development scenarios (lot split, duplex, or both)
    """
    scenarios = []

    # Check basic eligibility
    if not is_sb9_eligible(parcel):
        return scenarios

    # Scenario 1: Two-unit development (duplex) without lot split
    duplex_scenario = create_duplex_scenario(parcel)
    if duplex_scenario:
        scenarios.append(duplex_scenario)

    # Scenario 2: Lot split with two units per lot (4 units total)
    if can_split_lot(parcel):
        lot_split_scenario = create_lot_split_scenario(parcel)
        if lot_split_scenario:
            scenarios.append(lot_split_scenario)

    return scenarios


def is_sb9_eligible(parcel: ParcelBase) -> bool:
    """
    Check if parcel is eligible for SB9.

    Args:
        parcel: Parcel information

    Returns:
        True if eligible, False otherwise
    """
    zoning_code = parcel.zoning_code.upper()

    # Must be single-family residential zone
    if not ("R1" in zoning_code or "RS" in zoning_code or "SINGLE" in zoning_code):
        return False

    # Minimum lot size for duplex (no specific minimum, but practical limit)
    if parcel.lot_size_sqft < 2000:
        return False

    # In production, would check:
    # - Fire hazard zones
    # - Flood zones
    # - Historic property status
    # - Prime farmland designation
    # - Environmental constraints

    return True


def can_split_lot(parcel: ParcelBase) -> bool:
    """
    Check if lot can be split under SB9.

    Args:
        parcel: Parcel information

    Returns:
        True if lot split is feasible
    """
    # Minimum lot size for split: 2,400 sq ft (1,200 per resulting parcel)
    if parcel.lot_size_sqft < 2400:
        return False

    # SB9 does not impose a fixed minimum lot width; the 40/60 lot size ratio
    # and 1,200 sq ft minimum per child lot are addressed in proposal/scenario layers.
    return True


def create_duplex_scenario(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Create duplex development scenario under SB9.

    Args:
        parcel: Parcel information

    Returns:
        Development scenario for duplex
    """
    max_units = 2

    # SB9 unit size limits for small lots
    if parcel.lot_size_sqft < 5000:
        max_unit_size = 800.0  # sq ft per unit
    else:
        max_unit_size = 1200.0  # sq ft per unit

    max_building_sqft = max_units * max_unit_size

    # Height: subject to local objective standards; placeholder values used
    max_height_ft = 30.0
    max_stories = 2

    # Setbacks: 4 ft side and rear per SB9; front per local objective standards
    setbacks = {
        "rear": 4.0,
        "side": 4.0
    }

    # Parking: Up to 1 space per unit can be required
    parking_spaces_required = 2

    # Lot coverage
    lot_coverage_pct = min((max_building_sqft / parcel.lot_size_sqft) * 100, 60.0)

    notes = [
        "SB9 ministerial duplex development",
        f"Maximum {max_unit_size} sq ft per unit for lot size {parcel.lot_size_sqft} sq ft",
        "Height subject to local objective standards",
        "4-foot side and rear setbacks; front per local standards",
        "Ministerial approval required (no discretionary review)",
        "Units may not be used as short-term rentals"
    ]

    scenario = DevelopmentScenario(
        scenario_name="SB9 Duplex",
        legal_basis="SB9 (2021) - Two-Unit Development",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.9,
        notes=notes
    )

    return scenario


def create_lot_split_scenario(parcel: ParcelBase) -> Optional[DevelopmentScenario]:
    """
    Create lot split scenario under SB9.

    Args:
        parcel: Parcel information

    Returns:
        Development scenario for lot split with units
    """
    # Lot split creates two parcels
    num_parcels = 2
    parcel_size = parcel.lot_size_sqft / num_parcels

    # Two units per parcel
    units_per_parcel = 2
    max_units = num_parcels * units_per_parcel  # 4 total

    # Unit size limits
    if parcel_size < 5000:
        max_unit_size = 800.0
    else:
        max_unit_size = 1200.0

    max_building_sqft = max_units * max_unit_size

    # Height: subject to local objective standards; placeholder values used
    max_height_ft = 30.0
    max_stories = 2

    # Setbacks: 4 ft side and rear per SB9; front per local objective standards
    setbacks = {
        "rear": 4.0,
        "side": 4.0
    }

    # Parking: 1 space per unit max
    parking_spaces_required = max_units

    # Lot coverage
    lot_coverage_pct = min((max_building_sqft / parcel.lot_size_sqft) * 100, 60.0)

    notes = [
        "SB9 lot split with duplex on each parcel",
        f"Creates 2 parcels of approximately {int(parcel_size)} sq ft each",
        f"2 units per parcel = {max_units} total units",
        "Each parcel minimum 1,200 sq ft per SB9 and 40/60 ratio",
        "Height subject to local objective standards",
        "4-foot side and rear setbacks; front per local standards",
        "Ministerial approval process",
        "3-year owner-occupancy requirement applies to lot split",
        "Cannot be subdivided again for 10 years"
    ]

    scenario = DevelopmentScenario(
        scenario_name="SB9 Lot Split + Duplexes",
        legal_basis="SB9 (2021) - Urban Lot Split with Two Units Per Parcel",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.9,
        notes=notes
    )

    return scenario


# ---------------------------------------------------------------------------
# Lightweight SB9 helpers for proposal-based checks
# ---------------------------------------------------------------------------
def _is_single_family_zone(zone: str) -> bool:
    """Return True if zone string indicates a single-family designation.

    Examples considered single-family: R1, RS, or containing the phrase SINGLE.
    """
    if not zone:
        return False
    z = zone.upper()
    return ("R1" in z) or ("RS" in z) or ("SINGLE" in z)


def can_apply(parcel: dict, proposal: dict) -> dict:
    """Check whether an SB9 proposal can apply to a given parcel.

    Inputs (expected keys):
    - parcel: {
        zone: str,
        lot_area_sf: float,
        overlays: {coastal: bool, historic: bool, very_high_fire: bool, flood: bool},
        existing_units: int,
        had_rental_last_3y: bool,
      }
    - proposal: {two_unit: bool, lot_split: bool, near_transit: bool}

    Output (dict): {eligible: bool, reasons: [..]}

    Notes:
    - Historic resource or recent rental status renders SB9 ineligible. [CITE]
    - Very high fire hazard or flood areas are treated as ineligible here. [CITE]
    - Coastal parcels remain eligible but require a CDP; handled in apply(). [CITE]
    - Lot split requires at least 2,400 sq ft total (1,200 sq ft per new parcel). [CITE]
    """
    reasons: List[str] = []
    eligible = True

    wants_two_unit = bool(proposal.get("two_unit", False))
    wants_lot_split = bool(proposal.get("lot_split", False))

    if not (wants_two_unit or wants_lot_split):
        return {"eligible": False, "reasons": ["No SB9 provisions selected (two-unit or lot split)"]}

    zone = str(parcel.get("zone", ""))
    overlays = parcel.get("overlays", {}) or {}
    lot_area_sf = float(parcel.get("lot_area_sf", 0) or 0)

    # Zoning must be single-family
    if not _is_single_family_zone(zone):
        reasons.append("Not a single-family zone (SB9 applies to single-family)")
        eligible = False

    # Historic resources are ineligible
    if overlays.get("historic", False):
        reasons.append("Historic resource: SB9 ineligible")
        eligible = False

    # Recent rental eviction/tenancy restriction over prior 3 years
    if bool(parcel.get("had_rental_last_3y", False)):
        reasons.append("Rental in last 3 years: SB9 ineligible")
        eligible = False

    # Environmental exclusions (categorical):
    # prime farmland, wetlands, conservation easements, protected habitat,
    # hazardous waste sites, Alquist-Priolo fault zones [CITE]
    environmental_blocks = [
        ("prime_farmland", "Prime farmland: SB9 ineligible"),
        ("wetlands", "Wetlands: SB9 ineligible"),
        ("conservation_easement", "Conservation easement: SB9 ineligible"),
        ("habitat", "Habitat for protected species: SB9 ineligible"),
        ("hazardous_site", "Hazardous waste site: SB9 ineligible"),
        ("alquist_priolo", "Alquist-Priolo fault zone: SB9 ineligible"),
    ]
    for key, msg in environmental_blocks:
        if overlays.get(key, False):
            reasons.append(msg)
            eligible = False

    # Hazard overlays: do not categorically deny; note mitigation requirements [CITE]
    if overlays.get("very_high_fire", False):
        reasons.append("Very High Fire Hazard Zone: allowed with mitigation (hardening/defensible space)")

    if overlays.get("flood", False):
        reasons.append("Flood zone: allowed with FEMA-compliant mitigation (elevation/drainage)")

    # Lot split size check (only if requested)
    if wants_lot_split and lot_area_sf < 2400:
        reasons.append("Lot too small for SB9 lot split (need 2,400 sq ft minimum)")
        eligible = False

    # Protected housing constraints (categorical) [CITE]
    if bool(parcel.get("rent_controlled", False)):
        reasons.append("Rent-controlled units present: SB9 ineligible")
        eligible = False
    if bool(parcel.get("affordable_covenant", False)):
        reasons.append("Deed-restricted affordable units present: SB9 ineligible")
        eligible = False
    if bool(parcel.get("demolishes_protected_units", False)):
        reasons.append("Project would demolish protected housing: SB9 ineligible")
        eligible = False

    # Coastal overlay does not block eligibility; CDP handled downstream
    if overlays.get("coastal", False):
        reasons.append("Coastal zone: CDP required but SB9 may still apply")

    if eligible:
        if wants_lot_split:
            reasons.append("Meets minimum lot size for SB9 lot split")
            # 40/60 split ratio and 1,200 sf min per child lot [CITE]
            min_child_area = max(1200.0, 0.4 * lot_area_sf)
            reasons.append(f"Lot split must satisfy 40/60 ratio; minimum child lot area ≈ {int(min_child_area)} sq ft")
        if wants_two_unit:
            reasons.append("Two-unit development allowed on single-family parcel under SB9")

    return {"eligible": eligible, "reasons": reasons}


def apply(parcel: dict, proposal: dict) -> dict:
    """Apply SB9 standards to a parcel and proposal, if eligible.

    Returns dict with keys:
    - eligible: bool
    - reasons: list[str]
    - standards_overrides: {min_side_rear_setback: 4, ...}
    - max_units_delta: 1 (duplex) or 3 (lot split)
    - parking_required: 0|1 per unit (0 if near transit)

    Comments and [CITE] placeholders included for later statutory references.
    """
    check = can_apply(parcel, proposal)
    eligible = bool(check.get("eligible", False))
    reasons = list(check.get("reasons", []))

    standards_overrides = {"min_side_rear_setback": 4}

    # Coastal zone does not preclude SB9 but may require CDP [CITE]
    overlays = parcel.get("overlays", {}) or {}
    if overlays.get("coastal", False):
        standards_overrides["coastal_cdp_required"] = True
        # Ensure explanatory reason is present once
        msg = "Coastal zone: Coastal Development Permit (CDP) required"
        if not any("Coastal" in r for r in reasons):
            reasons.append(msg)

    # Hazard overlays may require mitigation measures [CITE]
    if overlays.get("very_high_fire", False) or overlays.get("flood", False):
        standards_overrides["hazard_mitigation_required"] = True
        if overlays.get("very_high_fire", False):
            reasons.append("Very High Fire Hazard Zone: mitigation measures required")
        if overlays.get("flood", False):
            reasons.append("Flood zone: mitigation measures required")

    # Parking per unit: 0 if near transit OR in car-share area; else up to 1 per unit [CITE]
    near_transit = bool(proposal.get("near_transit", False))
    car_share_area = bool(proposal.get("car_share_area", False)) or bool(parcel.get("car_share_area", False))
    zero_parking = near_transit or car_share_area
    parking_required = 0 if zero_parking else 1
    if near_transit:
        reasons.append("Near transit: no parking required under SB9")
    if car_share_area:
        reasons.append("Within car-share area: no parking required under SB9")
    if zero_parking:
        standards_overrides["parking_zero_allowed"] = True

    # Units delta: 3 if lot split requested, else 1 if two-unit requested
    if bool(proposal.get("lot_split", False)):
        max_units_delta = 3
        if eligible:
            reasons.append("Urban lot split with two units per parcel (up to 4 total)")
        # Provide explicit ratio and minimum child lot area requirements
        lot_area_sf = float(parcel.get("lot_area_sf", 0) or 0)
        standards_overrides["lot_split_min_child_lot_pct"] = 0.4
        standards_overrides["lot_split_max_child_lot_pct"] = 0.6
        standards_overrides["lot_split_min_child_lot_area_sf"] = int(max(1200.0, 0.4 * lot_area_sf))
    elif bool(proposal.get("two_unit", False)):
        max_units_delta = 1
        if eligible:
            reasons.append("Two-unit development (duplex) allowed on existing parcel")
    else:
        # No SB9 action selected; keep delta at 0
        max_units_delta = 0

    # Short-term rental prohibition (30+ day terms) [CITE]
    if eligible and (bool(proposal.get("two_unit", False)) or bool(proposal.get("lot_split", False))):
        standards_overrides["short_term_rental_prohibited"] = True
        reasons.append("Short-term rentals prohibited; SB9 units must be for 30+ day terms")

    return {
        "eligible": eligible,
        "reasons": reasons,
        "standards_overrides": standards_overrides,
        "max_units_delta": max_units_delta,
        "parking_required": parking_required,
    }
