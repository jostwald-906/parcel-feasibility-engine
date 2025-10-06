"""
Proposed project data models.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class UnitMix(BaseModel):
    """Breakdown of units by bedroom count."""
    studio: int = Field(0, ge=0, description="Number of studio units")
    one_bedroom: int = Field(0, ge=0, description="Number of 1-bedroom units")
    two_bedroom: int = Field(0, ge=0, description="Number of 2-bedroom units")
    three_plus_bedroom: int = Field(0, ge=0, description="Number of 3+ bedroom units")


class AffordableHousing(BaseModel):
    """Affordable housing details."""
    total_affordable_units: int = Field(0, ge=0, description="Total affordable units")
    very_low_income_units: int = Field(0, ge=0, description="Very low income units (<50% AMI)")
    low_income_units: int = Field(0, ge=0, description="Low income units (50-80% AMI)")
    moderate_income_units: int = Field(0, ge=0, description="Moderate income units (80-120% AMI)")
    affordability_duration_years: int = Field(55, ge=1, description="Affordability duration in years")


class Parking(BaseModel):
    """Parking specifications."""
    proposed_spaces: int = Field(0, ge=0, description="Number of proposed parking spaces")
    parking_type: Literal['surface', 'underground', 'structured', 'mixed'] = Field(
        'surface', description="Type of parking structure"
    )
    bicycle_spaces: int = Field(0, ge=0, description="Number of bicycle parking spaces")


class Setbacks(BaseModel):
    """Building setback requirements."""
    front_ft: float = Field(0, ge=0, description="Front setback in feet")
    rear_ft: float = Field(0, ge=0, description="Rear setback in feet")
    side_ft: float = Field(0, ge=0, description="Side setback in feet")


class SiteConfiguration(BaseModel):
    """Site layout configuration."""
    lot_coverage_pct: float = Field(0, ge=0, le=100, description="Lot coverage percentage")
    open_space_sqft: float = Field(0, ge=0, description="Open space in square feet")
    setbacks: Setbacks = Field(default_factory=Setbacks, description="Building setbacks")


class ProposedProject(BaseModel):
    """Comprehensive proposed project details."""

    # Existing fields (for backward compatibility)
    average_bedrooms_per_unit: Optional[float] = Field(None, ge=0, description="Average bedrooms per unit")
    for_sale_project: Optional[bool] = Field(None, description="Project is for-sale (ownership)")

    # Project Type & Use
    ownership_type: Optional[Literal['for-sale', 'rental', 'mixed']] = Field(
        None, description="Ownership type of the project"
    )
    mixed_use: Optional[bool] = Field(None, description="Is this a mixed-use project?")
    ground_floor_use: Optional[Literal['retail', 'office', 'commercial', 'live-work']] = Field(
        None, description="Ground floor use type (if mixed-use)"
    )
    commercial_sqft: Optional[float] = Field(None, ge=0, description="Commercial square footage")

    # Building Specifications
    proposed_stories: Optional[int] = Field(None, ge=1, description="Number of proposed stories")
    proposed_height_ft: Optional[float] = Field(None, ge=0, description="Proposed height in feet")
    proposed_units: Optional[int] = Field(None, ge=1, description="Total proposed units")
    average_unit_size_sqft: Optional[float] = Field(None, ge=0, description="Average unit size in sqft")
    total_building_sqft: Optional[float] = Field(None, ge=0, description="Total building square footage")

    # Unit Mix
    unit_mix: Optional[UnitMix] = Field(None, description="Breakdown of units by bedroom count")

    # Affordable Housing
    affordable_housing: Optional[AffordableHousing] = Field(None, description="Affordable housing plan")

    # Parking
    parking: Optional[Parking] = Field(None, description="Parking specifications")

    # Site Configuration
    site_configuration: Optional[SiteConfiguration] = Field(None, description="Site layout configuration")
