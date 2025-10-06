"""
Analysis request and response models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.parcel import ParcelBase
from app.models.proposed_project import ProposedProject


class RentControlUnit(BaseModel):
    """Model for a rent-controlled unit."""

    unit: str = Field(..., description="Unit identifier")
    mar: str = Field(..., description="Maximum Allowable Rent (formatted with $)")
    tenancy_date: str = Field(..., description="Most recent tenancy registration date")
    bedrooms: str = Field(..., description="Number of bedrooms")
    parcel: str = Field(..., description="Parcel number")


class RentControlData(BaseModel):
    """Model for rent control information."""

    is_rent_controlled: bool = Field(False, description="Whether property has rent-controlled units")
    total_units: int = Field(0, description="Total number of units with MAR data")
    avg_mar: Optional[float] = Field(None, description="Average MAR across all units (excludes $0 exempt units)")
    units: List[RentControlUnit] = Field(default_factory=list, description="Individual unit details")


class AnalysisRequest(BaseModel):
    """Request model for parcel feasibility analysis."""

    parcel: ParcelBase = Field(..., description="Parcel information")

    # Proposed project details (optional - for validation against allowed scenarios)
    proposed_project: Optional[ProposedProject] = Field(
        None,
        description="Proposed project details for validation against allowed development"
    )

    # Analysis options
    include_sb9: bool = Field(True, description="Include SB9 lot split analysis")
    include_sb35: bool = Field(True, description="Include SB35 streamlining analysis")
    include_ab2011: bool = Field(True, description="Include AB2011 office conversion analysis")
    include_density_bonus: bool = Field(True, description="Include density bonus analysis")

    # Development preferences
    target_affordability_pct: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Target percentage of affordable units"
    )
    prefer_max_density: bool = Field(True, description="Prefer maximum allowable density")

    # Debug mode
    debug: bool = Field(False, description="Enable debug mode with detailed decision logging")


class DevelopmentScenario(BaseModel):
    """Model for a development scenario."""

    scenario_name: str = Field(..., description="Name of the scenario")
    legal_basis: str = Field(..., description="Legal basis (zoning code, SB9, etc.)")

    # Development metrics
    max_units: int = Field(..., ge=0, description="Maximum units allowed")
    max_building_sqft: float = Field(..., ge=0, description="Maximum building square footage")
    max_height_ft: float = Field(..., gt=0, description="Maximum building height")
    max_stories: int = Field(..., gt=0, description="Maximum stories")

    # Requirements
    parking_spaces_required: int = Field(0, ge=0, description="Required parking spaces")
    affordable_units_required: int = Field(0, ge=0, description="Required affordable units")

    # Constraints
    setbacks: Dict[str, float] = Field(
        default_factory=dict,
        description="Setback requirements (front, rear, side)"
    )
    lot_coverage_pct: float = Field(..., ge=0, le=100, description="Maximum lot coverage percentage")

    # Financial estimates (optional)
    estimated_buildable_sqft: Optional[float] = Field(None, description="Estimated buildable square footage")
    notes: List[str] = Field(default_factory=list, description="Additional notes and considerations")

    # Density bonus specific fields (optional)
    concessions_applied: Optional[List[str]] = Field(None, description="Concessions applied (§ 65915(d))")
    waivers_applied: Optional[List[str]] = Field(None, description="Waivers applied (§ 65915(e))")


class AnalysisResponse(BaseModel):
    """Response model for parcel feasibility analysis."""

    parcel_apn: str = Field(..., description="Analyzed parcel APN")
    analysis_date: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

    # Base zoning scenario
    base_scenario: DevelopmentScenario = Field(..., description="Base zoning scenario")

    # Alternative scenarios
    alternative_scenarios: List[DevelopmentScenario] = Field(
        default_factory=list,
        description="Alternative development scenarios (SB9, SB35, etc.)"
    )

    # Recommendations
    recommended_scenario: str = Field(..., description="Recommended scenario name")
    recommendation_reason: str = Field(..., description="Reason for recommendation")

    # Compliance summary
    applicable_laws: List[str] = Field(default_factory=list, description="Applicable state laws")
    potential_incentives: List[str] = Field(default_factory=list, description="Potential incentives available")

    # Warnings and constraints
    warnings: List[str] = Field(default_factory=list, description="Warnings and constraints")

    # Rent control information
    rent_control: Optional[RentControlData] = Field(None, description="Rent control data if available")

    # CNEL (noise) analysis
    cnel_analysis: Optional[Dict[str, Any]] = Field(None, description="Community Noise Equivalent Level analysis")

    # Community benefits analysis
    community_benefits: Optional[Dict[str, Any]] = Field(None, description="Available community benefits for tier upgrades")

    # Proposed project validation (if proposed_project was provided in request)
    proposed_validation: Optional[Dict[str, Any]] = Field(
        None,
        description="Validation results comparing proposed project against allowed scenarios"
    )

    # Debug information (only included when debug=True)
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug information with decision trace")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisSummary(BaseModel):
    """Summary model for quick analysis overview."""

    parcel_apn: str
    max_units_base: int
    max_units_with_incentives: int
    recommended_approach: str
    key_opportunities: List[str]
