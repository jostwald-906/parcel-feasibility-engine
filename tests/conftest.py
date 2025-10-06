"""
Test fixtures for Parcel Feasibility Engine tests.

This module provides pytest fixtures with various parcel scenarios
for testing different zoning rules and state laws.
"""
import pytest
from app.models.parcel import ParcelBase


@pytest.fixture
def r1_parcel() -> ParcelBase:
    """
    Single-family residential parcel.

    Suitable for testing:
    - Base R1 zoning
    - SB9 eligibility (lot splits and duplexes)
    - Dimensional standards
    """
    return ParcelBase(
        apn="123-456-789",
        address="123 Main Street",
        city="San Diego",
        county="San Diego",
        zip_code="92101",
        lot_size_sqft=6000.0,
        lot_width_ft=60.0,
        lot_depth_ft=100.0,
        zoning_code="R1",
        general_plan="Single Family Residential",
        existing_units=1,
        existing_building_sqft=1800.0,
        year_built=1965,
        latitude=32.7157,
        longitude=-117.1611
    )


@pytest.fixture
def r2_parcel() -> ParcelBase:
    """
    Low-density multi-family residential parcel.

    Suitable for testing:
    - Base R2 zoning
    - Multi-family density calculations
    - Density bonus scenarios
    - SB35 eligibility
    """
    return ParcelBase(
        apn="234-567-890",
        address="456 Oak Avenue",
        city="Los Angeles",
        county="Los Angeles",
        zip_code="90012",
        lot_size_sqft=10000.0,
        lot_width_ft=80.0,
        lot_depth_ft=125.0,
        zoning_code="R2",
        general_plan="Low Density Residential",
        existing_units=2,
        existing_building_sqft=2400.0,
        year_built=1978,
        latitude=34.0522,
        longitude=-118.2437
    )


@pytest.fixture
def dcp_parcel() -> ParcelBase:
    """
    Downtown Community Plan parcel.

    Suitable for testing:
    - Higher density zoning
    - AB2097 parking reductions (transit proximity)
    - TOD overlays
    - Mixed-use scenarios
    """
    return ParcelBase(
        apn="345-678-901",
        address="789 Downtown Boulevard",
        city="San Francisco",
        county="San Francisco",
        zip_code="94102",
        lot_size_sqft=5000.0,
        lot_width_ft=50.0,
        lot_depth_ft=100.0,
        zoning_code="RM-3",
        general_plan="Downtown Mixed Use",
        existing_units=0,
        existing_building_sqft=0.0,
        year_built=None,
        latitude=37.7749,
        longitude=-122.4194
    )


@pytest.fixture
def coastal_parcel() -> ParcelBase:
    """
    Coastal Zone parcel.

    Suitable for testing:
    - Environmental overlay restrictions
    - Height limitations
    - Special setback requirements
    """
    return ParcelBase(
        apn="456-789-012",
        address="321 Beach Road",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90401",
        lot_size_sqft=7500.0,
        lot_width_ft=75.0,
        lot_depth_ft=100.0,
        zoning_code="R1-C",
        general_plan="Coastal Residential",
        existing_units=1,
        existing_building_sqft=2000.0,
        year_built=1955,
        latitude=34.0195,
        longitude=-118.4912
    )


@pytest.fixture
def historic_parcel() -> ParcelBase:
    """
    Historic District parcel.

    Suitable for testing:
    - Historic overlay restrictions
    - SB9 ineligibility (historic properties)
    - Design review requirements
    """
    return ParcelBase(
        apn="567-890-123",
        address="555 Heritage Lane",
        city="Pasadena",
        county="Los Angeles",
        zip_code="91101",
        lot_size_sqft=8000.0,
        lot_width_ft=80.0,
        lot_depth_ft=100.0,
        zoning_code="R1",
        general_plan="Single Family Residential",
        existing_units=1,
        existing_building_sqft=2200.0,
        year_built=1920,
        latitude=34.1478,
        longitude=-118.1445
    )


@pytest.fixture
def transit_adjacent_parcel() -> ParcelBase:
    """
    Parcel adjacent to major transit.

    Suitable for testing:
    - AB2097 parking elimination
    - TOD overlay applicability
    - SB35 streamlining
    - Higher density scenarios
    """
    return ParcelBase(
        apn="678-901-234",
        address="999 Transit Plaza",
        city="Oakland",
        county="Alameda",
        zip_code="94612",
        lot_size_sqft=12000.0,
        lot_width_ft=100.0,
        lot_depth_ft=120.0,
        zoning_code="R3",
        general_plan="Transit Oriented Development",
        existing_units=0,
        existing_building_sqft=0.0,
        year_built=None,
        latitude=37.8044,
        longitude=-122.2712
    )


@pytest.fixture
def commercial_parcel() -> ParcelBase:
    """
    Commercial parcel with existing office building.

    Suitable for testing:
    - AB2011 conversion eligibility
    - Commercial to residential conversion
    - Mixed-use scenarios
    """
    return ParcelBase(
        apn="789-012-345",
        address="100 Commerce Street",
        city="San Jose",
        county="Santa Clara",
        zip_code="95113",
        lot_size_sqft=15000.0,
        lot_width_ft=100.0,
        lot_depth_ft=150.0,
        zoning_code="C-2",
        general_plan="Commercial",
        existing_units=0,
        existing_building_sqft=20000.0,
        year_built=1985,
        latitude=37.3382,
        longitude=-121.8863
    )


@pytest.fixture
def small_r1_parcel() -> ParcelBase:
    """
    Small R1 parcel below typical minimums.

    Suitable for testing:
    - Dimensional standard violations
    - SB9 lot split ineligibility (too small)
    - Minimum lot size requirements
    """
    return ParcelBase(
        apn="890-123-456",
        address="222 Small Lot Drive",
        city="San Diego",
        county="San Diego",
        zip_code="92103",
        lot_size_sqft=2000.0,
        lot_width_ft=40.0,
        lot_depth_ft=50.0,
        zoning_code="R1",
        general_plan="Single Family Residential",
        existing_units=1,
        existing_building_sqft=900.0,
        year_built=1972,
        latitude=32.7503,
        longitude=-117.1745
    )


@pytest.fixture
def large_r4_parcel() -> ParcelBase:
    """
    Large high-density multi-family parcel.

    Suitable for testing:
    - High-density zoning calculations
    - Large density bonus scenarios
    - Multi-story development
    """
    return ParcelBase(
        apn="901-234-567",
        address="777 Highrise Way",
        city="Los Angeles",
        county="Los Angeles",
        zip_code="90015",
        lot_size_sqft=30000.0,
        lot_width_ft=150.0,
        lot_depth_ft=200.0,
        zoning_code="R4",
        general_plan="High Density Residential",
        existing_units=0,
        existing_building_sqft=0.0,
        year_built=None,
        latitude=34.0407,
        longitude=-118.2468
    )
