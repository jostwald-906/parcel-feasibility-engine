"""
Validation logic for proposed projects against allowed scenarios.
"""
from typing import List, Dict, Any, Optional
from app.models.proposed_project import ProposedProject
from app.models.analysis import DevelopmentScenario
from pydantic import BaseModel


class ValidationWarning(BaseModel):
    """Validation warning for a proposed project."""
    field: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    details: Optional[Dict[str, Any]] = None


def validate_proposed_vs_allowed(
    proposed: ProposedProject,
    allowed: DevelopmentScenario,
    parcel_lot_size_sqft: float
) -> List[ValidationWarning]:
    """
    Compare proposed project against allowed development scenario.

    Returns list of warnings/violations organized by severity:
    - error: Proposed exceeds allowed, project cannot proceed as-is
    - warning: Potential issue, may need additional approvals
    - info: Informational, no action required

    Args:
        proposed: Proposed project details
        allowed: Allowed development scenario (could be base zoning or with bonuses)
        parcel_lot_size_sqft: Parcel lot size for calculations

    Returns:
        List of validation warnings
    """
    warnings: List[ValidationWarning] = []

    # 1. Check proposed units vs max allowed
    if proposed.proposed_units:
        if proposed.proposed_units > allowed.max_units:
            warnings.append(ValidationWarning(
                field="proposed_units",
                severity="error",
                message=f"Proposed {proposed.proposed_units} units exceeds maximum allowed {allowed.max_units}",
                details={
                    "proposed": proposed.proposed_units,
                    "allowed": allowed.max_units,
                    "excess": proposed.proposed_units - allowed.max_units
                }
            ))
        elif proposed.proposed_units == allowed.max_units:
            warnings.append(ValidationWarning(
                field="proposed_units",
                severity="info",
                message=f"Proposed units matches maximum allowed ({allowed.max_units})",
                details={"proposed": proposed.proposed_units, "allowed": allowed.max_units}
            ))

    # 2. Check proposed height vs max allowed
    if proposed.proposed_height_ft:
        if proposed.proposed_height_ft > allowed.max_height_ft:
            warnings.append(ValidationWarning(
                field="proposed_height_ft",
                severity="warning",
                message=(
                    f"Proposed height {proposed.proposed_height_ft}ft exceeds base allowed {allowed.max_height_ft}ft. "
                    f"May qualify for height bonus through density bonus or tier upgrade."
                ),
                details={
                    "proposed": proposed.proposed_height_ft,
                    "allowed": allowed.max_height_ft,
                    "excess": proposed.proposed_height_ft - allowed.max_height_ft
                }
            ))

    # 3. Check proposed building sqft vs max allowed
    if proposed.total_building_sqft:
        if proposed.total_building_sqft > allowed.max_building_sqft:
            warnings.append(ValidationWarning(
                field="total_building_sqft",
                severity="error",
                message=(
                    f"Proposed building size {proposed.total_building_sqft:,.0f} sqft "
                    f"exceeds maximum {allowed.max_building_sqft:,.0f} sqft"
                ),
                details={
                    "proposed": proposed.total_building_sqft,
                    "allowed": allowed.max_building_sqft,
                    "excess": proposed.total_building_sqft - allowed.max_building_sqft
                }
            ))

    # 4. Check parking compliance
    if proposed.parking and proposed.parking.proposed_spaces is not None:
        if proposed.parking.proposed_spaces < allowed.parking_spaces_required:
            # This could be OK under AB 2097 near transit
            warnings.append(ValidationWarning(
                field="parking_spaces",
                severity="warning",
                message=(
                    f"Proposed {proposed.parking.proposed_spaces} spaces is less than "
                    f"required {allowed.parking_spaces_required}. Check AB 2097 eligibility "
                    f"(within ½ mile of transit) for parking reductions."
                ),
                details={
                    "proposed": proposed.parking.proposed_spaces,
                    "required": allowed.parking_spaces_required,
                    "deficit": allowed.parking_spaces_required - proposed.parking.proposed_spaces
                }
            ))

    # 5. Check affordable housing requirements
    total_affordable_proposed = 0
    if proposed.affordable_housing:
        total_affordable_proposed = (
            (proposed.affordable_housing.very_low_income_units or 0) +
            (proposed.affordable_housing.low_income_units or 0) +
            (proposed.affordable_housing.moderate_income_units or 0)
        )

    if total_affordable_proposed < allowed.affordable_units_required:
        warnings.append(ValidationWarning(
            field="affordable_housing",
            severity="error",
            message=(
                f"Proposed {total_affordable_proposed} affordable units is less than "
                f"required {allowed.affordable_units_required} for this scenario"
            ),
            details={
                "proposed": total_affordable_proposed,
                "required": allowed.affordable_units_required,
                "deficit": allowed.affordable_units_required - total_affordable_proposed
            }
        ))
    elif total_affordable_proposed > allowed.affordable_units_required:
        warnings.append(ValidationWarning(
            field="affordable_housing",
            severity="info",
            message=(
                f"Proposed {total_affordable_proposed} affordable units exceeds minimum "
                f"required {allowed.affordable_units_required}. May qualify for additional bonuses."
            ),
            details={
                "proposed": total_affordable_proposed,
                "required": allowed.affordable_units_required,
                "surplus": total_affordable_proposed - allowed.affordable_units_required
            }
        ))

    # 6. Check unit mix vs total proposed units
    if proposed.unit_mix and proposed.proposed_units:
        total_from_mix = (
            (proposed.unit_mix.studio or 0) +
            (proposed.unit_mix.one_bedroom or 0) +
            (proposed.unit_mix.two_bedroom or 0) +
            (proposed.unit_mix.three_plus_bedroom or 0)
        )

        if total_from_mix != proposed.proposed_units:
            warnings.append(ValidationWarning(
                field="unit_mix",
                severity="warning",
                message=(
                    f"Unit mix total ({total_from_mix}) does not match proposed units "
                    f"({proposed.proposed_units})"
                ),
                details={
                    "unit_mix_total": total_from_mix,
                    "proposed_units": proposed.proposed_units,
                    "difference": abs(total_from_mix - proposed.proposed_units)
                }
            ))

    # 7. Check lot coverage
    if proposed.site_configuration and proposed.site_configuration.lot_coverage_pct:
        if proposed.site_configuration.lot_coverage_pct > allowed.lot_coverage_pct:
            warnings.append(ValidationWarning(
                field="lot_coverage_pct",
                severity="error",
                message=(
                    f"Proposed lot coverage {proposed.site_configuration.lot_coverage_pct}% "
                    f"exceeds maximum {allowed.lot_coverage_pct}%"
                ),
                details={
                    "proposed": proposed.site_configuration.lot_coverage_pct,
                    "allowed": allowed.lot_coverage_pct,
                    "excess": proposed.site_configuration.lot_coverage_pct - allowed.lot_coverage_pct
                }
            ))

    # 8. Check setbacks (if provided in allowed scenario)
    if proposed.site_configuration and proposed.site_configuration.setbacks and allowed.setbacks:
        proposed_setbacks = proposed.site_configuration.setbacks

        # Front setback
        if "front" in allowed.setbacks and proposed_setbacks.front_ft < allowed.setbacks["front"]:
            warnings.append(ValidationWarning(
                field="setbacks.front_ft",
                severity="error",
                message=(
                    f"Proposed front setback {proposed_setbacks.front_ft}ft is less than "
                    f"required {allowed.setbacks['front']}ft"
                ),
                details={
                    "proposed": proposed_setbacks.front_ft,
                    "required": allowed.setbacks["front"]
                }
            ))

        # Rear setback
        if "rear" in allowed.setbacks and proposed_setbacks.rear_ft < allowed.setbacks["rear"]:
            warnings.append(ValidationWarning(
                field="setbacks.rear_ft",
                severity="error",
                message=(
                    f"Proposed rear setback {proposed_setbacks.rear_ft}ft is less than "
                    f"required {allowed.setbacks['rear']}ft"
                ),
                details={
                    "proposed": proposed_setbacks.rear_ft,
                    "required": allowed.setbacks["rear"]
                }
            ))

        # Side setback
        if "side" in allowed.setbacks and proposed_setbacks.side_ft < allowed.setbacks["side"]:
            warnings.append(ValidationWarning(
                field="setbacks.side_ft",
                severity="error",
                message=(
                    f"Proposed side setback {proposed_setbacks.side_ft}ft is less than "
                    f"required {allowed.setbacks['side']}ft"
                ),
                details={
                    "proposed": proposed_setbacks.side_ft,
                    "required": allowed.setbacks["side"]
                }
            ))

    # 9. Mixed-use compatibility check
    if proposed.mixed_use and proposed.ground_floor_use:
        # Check if zoning allows mixed-use (this would need zoning data)
        warnings.append(ValidationWarning(
            field="mixed_use",
            severity="info",
            message=(
                f"Mixed-use project with {proposed.ground_floor_use} ground floor. "
                f"Verify zoning allows mixed-use development."
            ),
            details={
                "ground_floor_use": proposed.ground_floor_use,
                "commercial_sqft": proposed.commercial_sqft
            }
        ))

    return warnings


def format_warnings_for_response(warnings: List[ValidationWarning]) -> Dict[str, Any]:
    """
    Format validation warnings for API response.

    Groups warnings by severity and provides summary.
    """
    errors = [w for w in warnings if w.severity == "error"]
    warnings_list = [w for w in warnings if w.severity == "warning"]
    info = [w for w in warnings if w.severity == "info"]

    return {
        "is_valid": len(errors) == 0,
        "total_issues": len(warnings),
        "errors": [w.dict() for w in errors],
        "warnings": [w.dict() for w in warnings_list],
        "info": [w.dict() for w in info],
        "summary": {
            "error_count": len(errors),
            "warning_count": len(warnings_list),
            "info_count": len(info)
        }
    }
