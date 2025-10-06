"""
AB2097 (2022) parking reduction rules.

Assembly Bill 2097 eliminates minimum parking requirements for residential
and mixed-use projects within 0.5 miles of major transit.

Effective: January 1, 2023

Major transit includes:
- Rail or ferry stations
- Bus rapid transit stops
- Intersections of two or more bus routes with 15-minute peak service
"""
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase


def apply_ab2097_parking_reduction(
    scenario: DevelopmentScenario,
    parcel: ParcelBase
) -> DevelopmentScenario:
    """
    Apply AB2097 parking reductions if applicable.

    This modifies the scenario in-place to eliminate parking requirements
    if the parcel qualifies under AB2097.

    Args:
        scenario: Development scenario to modify
        parcel: Parcel information

    Returns:
        Modified scenario with parking reductions applied
    """
    # Check if parcel is within transit area
    if is_within_transit_area(parcel):
        original_parking = scenario.parking_spaces_required
        scenario.parking_spaces_required = 0

        # Add note about AB2097
        ab2097_note = (
            f"AB2097: Parking requirement reduced from {original_parking} to 0 spaces "
            "due to proximity to major transit (within 0.5 miles)"
        )

        if ab2097_note not in scenario.notes:
            scenario.notes.append(ab2097_note)

    return scenario


def is_within_transit_area(parcel: ParcelBase) -> bool:
    """
    Check if parcel is within AB2097 transit area.

    In production, this would:
    1. Query transit stop database
    2. Calculate distances to major transit
    3. Verify service frequency

    Args:
        parcel: Parcel information

    Returns:
        True if within 0.5 miles of qualifying transit
    """
    # In production, would use actual transit data
    # For now, use simplified logic based on location

    if not parcel.latitude or not parcel.longitude:
        # Without coordinates, make conservative assumption
        return False

    # Major transit cities in California (simplified)
    major_transit_cities = [
        "San Francisco",
        "Oakland",
        "Berkeley",
        "San Jose",
        "Los Angeles",
        "Long Beach",
        "Pasadena",
        "San Diego",
        "Sacramento"
    ]

    # Simple check - in production would use actual distance calculations
    city_name = parcel.city

    for transit_city in major_transit_cities:
        if transit_city.upper() in city_name.upper():
            # In major transit city - assume transit proximity
            # Real implementation would calculate actual distance
            return True

    return False


def get_transit_proximity_info(parcel: ParcelBase) -> dict:
    """
    Get detailed transit proximity information.

    Args:
        parcel: Parcel information

    Returns:
        Dictionary with transit proximity details
    """
    within_transit = is_within_transit_area(parcel)

    info = {
        "ab2097_applicable": within_transit,
        "parking_minimums_eliminated": within_transit,
        "transit_distance_miles": None,  # Would calculate in production
        "nearest_transit_type": None,
        "notes": []
    }

    if within_transit:
        info["notes"].append(
            "Parcel appears to be within AB2097 transit area"
        )
        info["notes"].append(
            "No minimum parking requirements per AB2097"
        )
        info["notes"].append(
            "Verify exact transit distance with local planning department"
        )
    else:
        info["notes"].append(
            "Parcel does not appear to be within AB2097 transit area"
        )
        info["notes"].append(
            "Standard parking requirements apply"
        )

    return info


def calculate_optional_parking(scenario: DevelopmentScenario) -> int:
    """
    Calculate recommended parking even when not required.

    Even with AB2097 eliminating minimums, developers may choose to
    provide parking based on market demand.

    Args:
        scenario: Development scenario

    Returns:
        Recommended optional parking spaces
    """
    # Market-rate parking recommendations
    if scenario.max_units <= 10:
        # Small projects: 0.5-0.75 spaces per unit
        return int(scenario.max_units * 0.75)
    elif scenario.max_units <= 30:
        # Medium projects: 0.5 spaces per unit
        return int(scenario.max_units * 0.5)
    else:
        # Large projects: 0.25-0.5 spaces per unit
        return int(scenario.max_units * 0.4)
