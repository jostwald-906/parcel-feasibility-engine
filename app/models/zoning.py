"""
Zoning regulation models.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ZoningBase(BaseModel):
    """Base zoning model."""

    code: str = Field(..., description="Zoning code")
    jurisdiction: str = Field(..., description="City or county jurisdiction")
    description: Optional[str] = Field(None, description="Zoning description")

    # Density controls
    max_density_units_per_acre: Optional[float] = Field(None, ge=0, description="Maximum units per acre")
    min_lot_size_sqft: Optional[float] = Field(None, gt=0, description="Minimum lot size in square feet")

    # Height controls
    max_height_ft: Optional[float] = Field(None, gt=0, description="Maximum building height in feet")
    max_stories: Optional[int] = Field(None, gt=0, description="Maximum number of stories")

    # Coverage controls
    max_lot_coverage_pct: Optional[float] = Field(None, ge=0, le=100, description="Maximum lot coverage percentage")
    max_far: Optional[float] = Field(None, ge=0, description="Maximum floor area ratio")

    # Setbacks
    front_setback_ft: Optional[float] = Field(None, ge=0, description="Front setback in feet")
    rear_setback_ft: Optional[float] = Field(None, ge=0, description="Rear setback in feet")
    side_setback_ft: Optional[float] = Field(None, ge=0, description="Side setback in feet")

    # Parking requirements
    parking_spaces_per_unit: Optional[float] = Field(None, ge=0, description="Required parking spaces per unit")

    # Use restrictions
    residential_allowed: bool = Field(True, description="Whether residential use is allowed")
    multi_family_allowed: bool = Field(False, description="Whether multi-family is allowed")


class ZoningCreate(ZoningBase):
    """Model for creating new zoning regulation."""
    pass


class Zoning(ZoningBase):
    """Complete zoning model with database fields."""

    id: int = Field(..., description="Database ID")

    class Config:
        from_attributes = True


class ZoningOverlay(BaseModel):
    """Model for zoning overlay districts."""

    name: str = Field(..., description="Overlay district name")
    description: Optional[str] = Field(None, description="Overlay description")
    additional_height_ft: Optional[float] = Field(None, description="Additional height allowed")
    density_multiplier: Optional[float] = Field(None, gt=0, description="Density multiplier")
    special_requirements: Optional[str] = Field(None, description="Special requirements")
