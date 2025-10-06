"""
Zoning overlay district rules.

Overlay districts modify base zoning regulations for specific areas.
Common overlays include:
- Historic preservation overlays
- Transit-oriented development (TOD) overlays
- Affordable housing overlay zones
- Form-based code overlays
"""
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from app.models.zoning import ZoningOverlay
from typing import List, Optional


# Define common overlay districts
OVERLAY_DISTRICTS = {
    "TOD": ZoningOverlay(
        name="Transit-Oriented Development Overlay",
        description="Encourages higher-density development near transit",
        additional_height_ft=20.0,
        density_multiplier=1.5,
        special_requirements="Mixed-use encouraged, ground-floor retail preferred"
    ),
    "AHO": ZoningOverlay(
        name="Affordable Housing Overlay",
        description="Allows increased density for affordable housing projects",
        additional_height_ft=15.0,
        density_multiplier=1.3,
        special_requirements="Minimum 20% affordable units required"
    ),
    "HP": ZoningOverlay(
        name="Historic Preservation Overlay",
        description="Protects historic structures and character",
        additional_height_ft=0.0,
        density_multiplier=1.0,
        special_requirements="Design review required, must maintain historic character"
    ),
    "FBC": ZoningOverlay(
        name="Form-Based Code Overlay",
        description="Regulates building form rather than use",
        additional_height_ft=10.0,
        density_multiplier=1.2,
        special_requirements="Must meet form standards for building placement and design"
    )
}


def apply_overlay_modifications(
    base_scenario: DevelopmentScenario,
    parcel: ParcelBase,
    overlay_codes: List[str]
) -> DevelopmentScenario:
    """
    Apply overlay district modifications to base scenario.

    Args:
        base_scenario: Base development scenario
        parcel: Parcel information
        overlay_codes: List of overlay district codes

    Returns:
        Modified scenario with overlay rules applied
    """
    scenario = base_scenario

    for overlay_code in overlay_codes:
        overlay = OVERLAY_DISTRICTS.get(overlay_code.upper())
        if overlay:
            scenario = apply_single_overlay(scenario, parcel, overlay)

    return scenario


def apply_single_overlay(
    scenario: DevelopmentScenario,
    parcel: ParcelBase,
    overlay: ZoningOverlay
) -> DevelopmentScenario:
    """
    Apply a single overlay district to scenario.

    Args:
        scenario: Development scenario
        parcel: Parcel information
        overlay: Overlay district definition

    Returns:
        Modified scenario
    """
    # Apply height modification
    if overlay.additional_height_ft:
        scenario.max_height_ft += overlay.additional_height_ft
        scenario.max_stories = int(scenario.max_height_ft / 11)  # Assume 11 ft per story

    # Apply density modification
    if overlay.density_multiplier and overlay.density_multiplier > 1.0:
        original_units = scenario.max_units
        scenario.max_units = int(scenario.max_units * overlay.density_multiplier)
        additional_units = scenario.max_units - original_units

        # Increase building square footage proportionally
        scenario.max_building_sqft *= overlay.density_multiplier

    # Add note about overlay
    overlay_note = f"Overlay: {overlay.name}"
    if overlay.density_multiplier and overlay.density_multiplier > 1.0:
        overlay_note += f" (+{int((overlay.density_multiplier - 1) * 100)}% density)"
    if overlay.additional_height_ft:
        overlay_note += f" (+{overlay.additional_height_ft} ft height)"

    scenario.notes.append(overlay_note)

    if overlay.special_requirements:
        scenario.notes.append(f"Requirement: {overlay.special_requirements}")

    return scenario


def check_overlay_applicability(
    parcel: ParcelBase,
    overlay_code: str
) -> bool:
    """
    Check if an overlay district applies to a parcel.

    In production, this would query GIS data to determine overlay districts.

    Args:
        parcel: Parcel information
        overlay_code: Overlay district code

    Returns:
        True if overlay applies to parcel
    """
    # Simplified logic - in production would use GIS queries
    overlay_code = overlay_code.upper()

    # TOD overlays typically apply near transit
    if overlay_code == "TOD":
        return is_near_transit(parcel)

    # Historic overlays based on property age
    if overlay_code == "HP":
        return parcel.year_built and parcel.year_built < 1945

    # Default: unknown without GIS data
    return False


def is_near_transit(parcel: ParcelBase) -> bool:
    """
    Check if parcel is near transit (for TOD overlays).

    Args:
        parcel: Parcel information

    Returns:
        True if near transit
    """
    # Simplified check - same logic as AB2097
    major_transit_cities = [
        "San Francisco", "Oakland", "Berkeley", "San Jose",
        "Los Angeles", "Long Beach", "San Diego", "Sacramento"
    ]

    for city in major_transit_cities:
        if city.upper() in parcel.city.upper():
            return True

    return False


def get_overlay_info(overlay_code: str) -> Optional[ZoningOverlay]:
    """
    Get information about a specific overlay district.

    Args:
        overlay_code: Overlay district code

    Returns:
        Overlay information or None if not found
    """
    return OVERLAY_DISTRICTS.get(overlay_code.upper())


def list_all_overlays() -> List[ZoningOverlay]:
    """
    Get list of all defined overlay districts.

    Returns:
        List of overlay district definitions
    """
    return list(OVERLAY_DISTRICTS.values())


def create_tod_scenario(
    base_scenario: DevelopmentScenario,
    parcel: ParcelBase
) -> Optional[DevelopmentScenario]:
    """
    Create a TOD overlay scenario if applicable.

    Args:
        base_scenario: Base zoning scenario
        parcel: Parcel information

    Returns:
        TOD scenario or None if not applicable
    """
    if not is_near_transit(parcel):
        return None

    tod_overlay = OVERLAY_DISTRICTS["TOD"]
    scenario = apply_single_overlay(
        base_scenario.model_copy(deep=True),
        parcel,
        tod_overlay
    )

    scenario.scenario_name = "TOD Overlay"
    scenario.legal_basis += " + Transit-Oriented Development Overlay"

    return scenario
