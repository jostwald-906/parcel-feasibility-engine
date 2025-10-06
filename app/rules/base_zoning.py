"""
Base zoning analysis rules.
"""
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from app.rules.tiered_standards import compute_max_far, compute_max_height, get_tier_info
from typing import Dict


def analyze_base_zoning(parcel: ParcelBase) -> DevelopmentScenario:
    """
    Analyze development potential under base zoning regulations.

    This function applies standard zoning rules based on the parcel's zoning code.
    In a production system, this would query a zoning database.

    Args:
        parcel: Parcel information

    Returns:
        Development scenario under base zoning
    """
    # Parse zoning code to determine development standards
    # This is simplified - real implementation would query zoning database

    zoning_code = parcel.zoning_code.upper()

    # Initialize default values
    max_units = 1
    max_far = 0.5
    max_height_ft = 35.0
    max_stories = 2
    lot_coverage_pct = 40.0
    parking_per_unit = 2.0

    front_setback = 20.0
    rear_setback = 15.0
    side_setback = 5.0

    # Determine zoning parameters based on code
    if "R1" in zoning_code or "RS" in zoning_code:
        # Single-family residential
        max_units = 1
        max_far = 0.5
        max_height_ft = 35.0
        max_stories = 2
        lot_coverage_pct = 40.0
        parking_per_unit = 2.0

    elif "R2" in zoning_code or "RD" in zoning_code:
        # Low-density multi-family
        density_per_acre = 15.0
        max_units = max(int((parcel.lot_size_sqft / 43560) * density_per_acre), 2)
        max_far = 0.75
        max_height_ft = 40.0
        max_stories = 3
        lot_coverage_pct = 50.0
        parking_per_unit = 1.5

    elif "R3" in zoning_code or "RM" in zoning_code:
        # Medium-density multi-family
        density_per_acre = 30.0
        max_units = int((parcel.lot_size_sqft / 43560) * density_per_acre)
        max_far = 1.5
        max_height_ft = 55.0
        max_stories = 4
        lot_coverage_pct = 60.0
        parking_per_unit = 1.5

    elif "R4" in zoning_code or "RH" in zoning_code:
        # High-density multi-family
        density_per_acre = 60.0
        max_units = int((parcel.lot_size_sqft / 43560) * density_per_acre)
        max_far = 2.5
        max_height_ft = 75.0
        max_stories = 6
        lot_coverage_pct = 70.0
        parking_per_unit = 1.0

    elif "C" in zoning_code or "COMMERCIAL" in zoning_code:
        # Commercial - assume mixed-use allowed
        density_per_acre = 40.0
        max_units = int((parcel.lot_size_sqft / 43560) * density_per_acre)
        max_far = 2.0
        max_height_ft = 65.0
        max_stories = 5
        lot_coverage_pct = 80.0
        parking_per_unit = 1.0

    elif "MU" in zoning_code or "MIXED" in zoning_code or "NV" in zoning_code or "WT" in zoning_code:
        # Mixed-use zones (MUBL, MUBM, MUBH, MUB, MUCR, NV - Neighborhood Village, WT - Wilshire Transition)
        if "NV" in zoning_code:
            # Neighborhood Village - moderate density mixed-use
            density_per_acre = 25.0
            max_far = 1.0
            max_height_ft = 35.0
            max_stories = 2
            lot_coverage_pct = 60.0
            parking_per_unit = 1.0
        elif "WT" in zoning_code:
            # Wilshire Transition - mixed-use transition zone
            # TODO(SM): Confirm actual WT standards from municipal code
            density_per_acre = 35.0
            max_far = 1.75
            max_height_ft = 50.0
            max_stories = 4
            lot_coverage_pct = 65.0
            parking_per_unit = 1.0
        elif "MUBL" in zoning_code:
            # Mixed-Use Boulevard Low
            density_per_acre = 30.0
            max_far = 1.5
            max_height_ft = 45.0
            max_stories = 3
            lot_coverage_pct = 65.0
            parking_per_unit = 1.0
        elif "MUBM" in zoning_code:
            # Mixed-Use Boulevard Medium
            density_per_acre = 50.0
            max_far = 2.0
            max_height_ft = 55.0
            max_stories = 4
            lot_coverage_pct = 70.0
            parking_per_unit = 1.0
        elif "MUBH" in zoning_code:
            # Mixed-Use Boulevard High
            density_per_acre = 75.0
            max_far = 3.0
            max_height_ft = 84.0
            max_stories = 7
            lot_coverage_pct = 75.0
            parking_per_unit = 0.75
        else:
            # Generic mixed-use
            density_per_acre = 40.0
            max_far = 2.0
            max_height_ft = 65.0
            max_stories = 5
            lot_coverage_pct = 70.0
            parking_per_unit = 1.0

        max_units = max(int((parcel.lot_size_sqft / 43560) * density_per_acre), 1)

    # Apply tier-aware FAR and height (considers overlays and tiers)
    tiered_far, far_source = compute_max_far(parcel)
    tiered_height, height_source = compute_max_height(parcel)

    # Use tiered values if different from base
    if tiered_far != max_far or tiered_height != max_height_ft:
        max_far = tiered_far
        max_height_ft = tiered_height
        # Recalculate stories based on tiered height
        max_stories = int(max_height_ft / 11)

    # Calculate maximum building square footage
    max_building_sqft = min(
        parcel.lot_size_sqft * max_far,
        parcel.lot_size_sqft * (lot_coverage_pct / 100) * max_stories
    )

    # Calculate parking requirement
    parking_spaces_required = int(max_units * parking_per_unit)

    # Build setbacks dictionary
    setbacks: Dict[str, float] = {
        "front": front_setback,
        "rear": rear_setback,
        "side": side_setback
    }

    # Create notes
    notes = [
        f"Base zoning: {parcel.zoning_code}",
        f"Density calculation: {max_units} units allowed by zoning",
        f"FAR limit: {max_far} ({far_source})",
        f"Height limit: {max_height_ft} ft / {max_stories} stories ({height_source})"
    ]

    # Add tier info if applicable
    tier_info = get_tier_info(parcel)
    if tier_info:
        notes.insert(1, f"Development standards: {tier_info}")

    if parcel.existing_units > 0:
        notes.append(f"Note: {parcel.existing_units} existing unit(s) on parcel")

    # Create scenario
    scenario = DevelopmentScenario(
        scenario_name="Base Zoning",
        legal_basis=f"Local Zoning Code - {parcel.zoning_code}",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=0,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.85,  # Account for circulation, walls
        notes=notes
    )

    return scenario


def check_dimensional_standards(parcel: ParcelBase) -> Dict[str, bool]:
    """
    Check if parcel meets minimum dimensional standards.

    Args:
        parcel: Parcel information

    Returns:
        Dictionary of compliance checks
    """
    checks = {}

    # Minimum lot size (varies by zone)
    zoning_code = parcel.zoning_code.upper()

    if "R1" in zoning_code:
        min_lot_size = 5000.0
        checks["min_lot_size"] = parcel.lot_size_sqft >= min_lot_size
    elif "R2" in zoning_code:
        min_lot_size = 3500.0
        checks["min_lot_size"] = parcel.lot_size_sqft >= min_lot_size
    else:
        checks["min_lot_size"] = True

    # Minimum width
    if parcel.lot_width_ft:
        checks["min_width"] = parcel.lot_width_ft >= 40.0
    else:
        checks["min_width"] = None  # Unknown

    return checks
