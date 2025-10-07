"""
Parcel data models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ParcelBase(BaseModel):
    """Base parcel model with common attributes."""

    apn: str = Field(..., description="Assessor's Parcel Number")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    county: str = Field(..., description="County name")
    zip_code: str = Field(..., description="ZIP code")

    # Parcel dimensions
    lot_size_sqft: float = Field(..., gt=0, description="Lot size in square feet")
    lot_width_ft: Optional[float] = Field(None, gt=0, description="Lot width in feet")
    lot_depth_ft: Optional[float] = Field(None, gt=0, description="Lot depth in feet")

    # Zoning information
    zoning_code: str = Field(..., description="Zoning designation code")
    general_plan: Optional[str] = Field(None, description="General plan designation")

    # Existing development
    existing_units: int = Field(0, ge=0, description="Number of existing units")
    existing_building_sqft: float = Field(0, ge=0, description="Existing building square footage")
    year_built: Optional[int] = Field(None, description="Year existing structure was built")

    # Current use information
    use_code: Optional[str] = Field(None, description="Property use code from assessor data")
    use_description: Optional[str] = Field(None, description="Property use description (e.g., 'Single Family Residence', 'Super Market')")

    # Geographic coordinates
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")

    # Optional project/context fields (used by some rules)
    for_sale: Optional[bool] = Field(None, description="Project is for-sale (ownership) rather than rental")
    avg_bedrooms_per_unit: Optional[float] = Field(
        None, description="Average bedrooms per unit for parking calculations"
    )
    near_transit: Optional[bool] = Field(
        None, description="Within 0.5 miles of a major transit stop (AB 2097)"
    )

    # Environmental data
    cnel_db: Optional[float] = Field(
        None, ge=0, le=100, description="Community Noise Equivalent Level in decibels (CNEL)"
    )

    # ==========================================================================
    # Tier and Overlay Information for Development Standards
    # ==========================================================================
    # These fields control tier-aware FAR and height resolution in app/rules/tiered_standards.py
    # See docs/tier_standards_citations_needed.md for required Santa Monica Municipal Code citations

    development_tier: Optional[str] = Field(
        None,
        description=(
            "Development tier for tiered FAR/height standards. "
            "Valid values: '1', '2', '3' for Downtown Community Plan (DCP) tiers. "
            "Tier 1 = base standards, Tier 2/3 = enhanced intensity. "
            "See app/rules/tiered_standards.py for tier multipliers/bonuses."
        ),
        pattern=r'^[1-3]$'  # Enforce valid tier values
    )

    overlay_codes: Optional[List[str]] = Field(
        None,
        description=(
            "List of overlay zone codes that modify base zoning standards. "
            "Recognized overlays: "
            "'DCP' (Downtown Community Plan - requires development_tier), "
            "'Bergamot' (Bergamot Area Plan - district-specific FAR/height), "
            "'AHO' (Affordable Housing Overlay - additive bonuses). "
            "Multiple overlays can apply; precedence: Bergamot > DCP > Base, then + AHO. "
            "See app/rules/tiered_standards.py for overlay resolution logic."
        ),
        # Add validation in custom validator
    )

    # AB 2011 site exclusion flags
    in_coastal_high_hazard: Optional[bool] = Field(
        None, description="Parcel is in coastal high hazard zone (AB 2011 exclusion)"
    )
    in_prime_farmland: Optional[bool] = Field(
        None, description="Parcel is on prime farmland or farmland of statewide importance"
    )
    in_wetlands: Optional[bool] = Field(
        None, description="Parcel contains wetlands (Clean Water Act - from CARI GIS)"
    )
    in_conservation_area: Optional[bool] = Field(
        None, description="Parcel has conservation easement or is in protected area (from CPAD GIS)"
    )
    is_historic_property: Optional[bool] = Field(
        None, description="Parcel contains a historic resource or structure"
    )
    in_flood_zone: Optional[bool] = Field(
        None, description="Parcel is in FEMA flood hazard zone"
    )
    in_coastal_zone: Optional[bool] = Field(
        None, description="Parcel is in California Coastal Zone (may require CDP)"
    )

    # Additional environmental GIS fields for SB35/AB2011 site exclusions
    fire_hazard_zone: Optional[str] = Field(
        None, description="Fire hazard severity zone from CAL FIRE (e.g., 'Very High', 'High', 'Moderate')"
    )
    near_hazardous_waste: Optional[bool] = Field(
        None, description="Parcel is within 500ft of hazardous waste site (DTSC EnviroStor)"
    )
    in_earthquake_fault_zone: Optional[bool] = Field(
        None, description="Parcel is in Alquist-Priolo earthquake fault zone (from CGS GIS)"
    )

    # Protected housing and tenancy flags
    has_rent_controlled_units: Optional[bool] = Field(
        None, description="Parcel has rent-controlled units (AB 2011 protected housing)"
    )
    rent_control_status: Optional[str] = Field(
        None,
        description=(
            "Manual override for rent control status. Valid values: 'yes', 'no', 'unknown'. "
            "Use this when automatic rent control lookup is unavailable or to override API results. "
            "If set, this value takes precedence over has_rent_controlled_units flag."
        )
    )
    has_deed_restricted_affordable: Optional[bool] = Field(
        None, description="Parcel has deed-restricted affordable housing"
    )
    has_ellis_act_units: Optional[bool] = Field(
        None, description="Parcel had units withdrawn under Ellis Act within lookback period"
    )
    has_recent_tenancy: Optional[bool] = Field(
        None, description="Parcel had residential tenancy within last 10 years"
    )
    protected_units_count: Optional[int] = Field(
        None, ge=0, description="Number of protected residential units on parcel"
    )

    # AB 2011 labor standards compliance
    prevailing_wage_commitment: Optional[bool] = Field(
        None, description="Developer commits to prevailing wage (required for all AB 2011)"
    )
    skilled_trained_workforce_commitment: Optional[bool] = Field(
        None, description="Developer commits to skilled & trained workforce (required 50+ units)"
    )
    healthcare_benefits_commitment: Optional[bool] = Field(
        None, description="Developer commits to healthcare benefits for workers"
    )

    # AB 2011 corridor width classification
    street_row_width: Optional[float] = Field(
        None,
        ge=0,
        description=(
            "Street right-of-way (ROW) width in feet for AB 2011 corridor classification. "
            "70-99 ft = Narrow corridor (40 u/ac, 35 ft height), "
            "100-150 ft = Wide corridor (60 u/ac, 45 ft height). "
            "Can be estimated from street classification or manually entered."
        )
    )


class ParcelCreate(ParcelBase):
    """Model for creating a new parcel."""
    pass


class Parcel(ParcelBase):
    """Complete parcel model with database fields."""

    id: int = Field(..., description="Database ID")

    class Config:
        from_attributes = True
