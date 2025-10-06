"""
Tests for base zoning analysis.

Tests the base_zoning module which calculates development potential
under standard local zoning regulations.
"""
import pytest
from app.rules.base_zoning import (
    analyze_base_zoning,
    check_dimensional_standards
)
from app.models.parcel import ParcelBase


class TestBaseZoningAnalysis:
    """Tests for base zoning scenario generation."""

    def test_r1_single_family_zoning(self, r1_parcel):
        """Test that R1 zoning allows 1 unit."""
        scenario = analyze_base_zoning(r1_parcel)

        assert scenario.scenario_name == "Base Zoning"
        assert scenario.max_units == 1
        assert scenario.max_height_ft == 35.0
        assert scenario.max_stories == 2
        assert scenario.parking_spaces_required == 2
        assert "Base zoning: R1" in scenario.notes[0]

    def test_r2_multi_family_density(self, r2_parcel):
        """Test R2 zoning density calculation (15 units/acre)."""
        scenario = analyze_base_zoning(r2_parcel)

        # 10,000 sq ft = 0.2296 acres
        # 0.2296 acres * 15 units/acre = 3.44 units
        # Should allow at least 2 units (minimum for R2)
        assert scenario.max_units >= 2
        assert scenario.max_units <= 5  # Reasonable upper bound
        assert scenario.max_height_ft == 40.0
        assert scenario.max_stories == 3
        assert scenario.parking_spaces_required > 0

    def test_r3_medium_density(self, transit_adjacent_parcel):
        """Test R3 zoning with 30 units/acre density."""
        # Transit adjacent parcel is R3 zoned
        scenario = analyze_base_zoning(transit_adjacent_parcel)

        # 12,000 sq ft = 0.2755 acres
        # 0.2755 acres * 30 units/acre = 8.26 units
        assert scenario.max_units >= 7
        assert scenario.max_units <= 10
        assert scenario.max_height_ft == 55.0
        assert scenario.max_stories == 4

    def test_r4_high_density(self, large_r4_parcel):
        """Test R4 zoning with 60 units/acre density."""
        scenario = analyze_base_zoning(large_r4_parcel)

        # 30,000 sq ft = 0.6887 acres
        # 0.6887 acres * 60 units/acre = 41.3 units
        assert scenario.max_units >= 35
        assert scenario.max_units <= 45
        assert scenario.max_height_ft == 75.0
        assert scenario.max_stories == 6
        assert scenario.parking_spaces_required == scenario.max_units  # 1.0 per unit

    def test_commercial_zoning(self, commercial_parcel):
        """Test commercial zone with mixed-use potential."""
        scenario = analyze_base_zoning(commercial_parcel)

        assert scenario.max_units > 0  # Should allow residential
        assert scenario.max_height_ft >= 45.0
        assert scenario.max_far >= 1.5

    @pytest.mark.parametrize("zoning_code,expected_units", [
        ("R1", 1),
        ("RS", 1),
        ("R1-5000", 1),
    ])
    def test_single_family_variations(self, zoning_code, expected_units):
        """Test various single-family zoning code formats."""
        parcel = ParcelBase(
            apn="TEST-001",
            address="Test Address",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=6000.0,
            zoning_code=zoning_code,
            existing_units=0,
            existing_building_sqft=0
        )

        scenario = analyze_base_zoning(parcel)
        assert scenario.max_units == expected_units


class TestSetbackCalculations:
    """Tests for setback requirements."""

    def test_r1_setbacks(self, r1_parcel):
        """Test R1 setback requirements."""
        scenario = analyze_base_zoning(r1_parcel)

        assert "front" in scenario.setbacks
        assert "rear" in scenario.setbacks
        assert "side" in scenario.setbacks

        # R1 typically has larger setbacks
        assert scenario.setbacks["front"] >= 15.0
        assert scenario.setbacks["rear"] >= 10.0
        assert scenario.setbacks["side"] >= 5.0

    def test_multi_family_setbacks(self, r2_parcel):
        """Test multi-family setback requirements."""
        scenario = analyze_base_zoning(r2_parcel)

        # Multi-family may have different setbacks
        assert all(sb >= 0 for sb in scenario.setbacks.values())


class TestBuildingParameters:
    """Tests for building size and coverage calculations."""

    def test_far_calculation(self, r1_parcel):
        """Test FAR-based building size calculation."""
        scenario = analyze_base_zoning(r1_parcel)

        # R1 typically has FAR of 0.5
        expected_max = r1_parcel.lot_size_sqft * 0.5
        assert scenario.max_building_sqft <= expected_max * 1.1  # 10% tolerance

    def test_lot_coverage_limits(self, r1_parcel):
        """Test lot coverage percentage limits."""
        scenario = analyze_base_zoning(r1_parcel)

        assert 0 < scenario.lot_coverage_pct <= 100
        # R1 typically has 40% coverage
        assert scenario.lot_coverage_pct <= 60  # Reasonable upper limit

    def test_buildable_area_estimate(self, r2_parcel):
        """Test estimated buildable square footage."""
        scenario = analyze_base_zoning(r2_parcel)

        # Buildable should be less than max (accounting for walls, circulation)
        assert scenario.estimated_buildable_sqft <= scenario.max_building_sqft
        assert scenario.estimated_buildable_sqft >= scenario.max_building_sqft * 0.75

    def test_height_to_stories_ratio(self, r2_parcel):
        """Test that height and stories are consistent."""
        scenario = analyze_base_zoning(r2_parcel)

        # Typical story height is 10-12 feet
        implied_story_height = scenario.max_height_ft / scenario.max_stories
        assert 8 <= implied_story_height <= 15  # Reasonable range


class TestParkingRequirements:
    """Tests for parking space calculations."""

    def test_r1_parking(self, r1_parcel):
        """Test R1 parking (typically 2 spaces per unit)."""
        scenario = analyze_base_zoning(r1_parcel)

        # 1 unit * 2 spaces/unit = 2 spaces
        assert scenario.parking_spaces_required == 2

    def test_r2_parking(self, r2_parcel):
        """Test R2 parking (typically 1.5 spaces per unit)."""
        scenario = analyze_base_zoning(r2_parcel)

        # Should have parking requirement
        assert scenario.parking_spaces_required > 0
        # Ratio should be reasonable
        ratio = scenario.parking_spaces_required / scenario.max_units
        assert 1.0 <= ratio <= 2.0

    def test_high_density_parking(self, large_r4_parcel):
        """Test high-density parking (typically 1.0 spaces per unit)."""
        scenario = analyze_base_zoning(large_r4_parcel)

        # R4 typically requires less parking
        ratio = scenario.parking_spaces_required / scenario.max_units
        assert 0.5 <= ratio <= 1.5


class TestDimensionalStandards:
    """Tests for dimensional standard compliance checking."""

    def test_r1_minimum_lot_size(self, r1_parcel):
        """Test R1 minimum lot size compliance."""
        checks = check_dimensional_standards(r1_parcel)

        assert "min_lot_size" in checks
        # 6000 sq ft lot should meet R1 minimum (typically 5000)
        assert checks["min_lot_size"] is True

    def test_small_lot_fails_minimum(self, small_r1_parcel):
        """Test that undersized lot fails dimensional standards."""
        checks = check_dimensional_standards(small_r1_parcel)

        # 2000 sq ft lot should fail R1 minimum
        assert checks["min_lot_size"] is False

    def test_r2_minimum_lot_size(self, r2_parcel):
        """Test R2 minimum lot size compliance."""
        checks = check_dimensional_standards(r2_parcel)

        # R2 typically has 3500 sq ft minimum
        assert checks["min_lot_size"] is True

    def test_minimum_width_check(self, r1_parcel):
        """Test minimum width standard."""
        checks = check_dimensional_standards(r1_parcel)

        assert "min_width" in checks
        # 60 ft width should meet minimum (typically 40 ft)
        assert checks["min_width"] is True

    def test_missing_width_dimension(self):
        """Test handling of missing width information."""
        parcel = ParcelBase(
            apn="TEST-002",
            address="Test Address",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=6000.0,
            lot_width_ft=None,  # Missing width
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        checks = check_dimensional_standards(parcel)
        # Should handle missing width gracefully
        assert checks["min_width"] is None


class TestExistingDevelopment:
    """Tests for parcels with existing development."""

    def test_existing_units_noted(self, r1_parcel):
        """Test that existing units are noted in scenario."""
        scenario = analyze_base_zoning(r1_parcel)

        # Should mention existing units in notes
        notes_text = " ".join(scenario.notes)
        assert "existing" in notes_text.lower()

    def test_vacant_parcel(self, dcp_parcel):
        """Test vacant parcel (no existing development)."""
        scenario = analyze_base_zoning(dcp_parcel)

        # Should still generate valid scenario
        assert scenario.max_units > 0
        assert scenario.max_building_sqft > 0


class TestZoningCodeVariations:
    """Tests for different zoning code formats and variations."""

    @pytest.mark.parametrize("code,min_units,max_height", [
        ("R1", 1, 35.0),
        ("R2", 2, 40.0),
        ("R3", 3, 55.0),
        ("R4", 5, 75.0),
        ("RM-2", 2, 40.0),
        ("RH-3", 5, 55.0),
    ])
    def test_various_residential_codes(self, code, min_units, max_height):
        """Test various residential zoning code formats."""
        parcel = ParcelBase(
            apn="TEST-PARAM",
            address="Test Address",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=10000.0,
            zoning_code=code,
            existing_units=0,
            existing_building_sqft=0
        )

        scenario = analyze_base_zoning(parcel)

        assert scenario.max_units >= min_units
        assert scenario.max_height_ft >= max_height * 0.9  # Allow some variation


class TestScenarioMetadata:
    """Tests for scenario metadata and documentation."""

    def test_legal_basis_includes_zoning_code(self, r1_parcel):
        """Test that legal basis references the zoning code."""
        scenario = analyze_base_zoning(r1_parcel)

        assert "R1" in scenario.legal_basis
        assert "Zoning" in scenario.legal_basis

    def test_notes_include_key_parameters(self, r2_parcel):
        """Test that notes document key zoning parameters."""
        scenario = analyze_base_zoning(r2_parcel)

        notes_text = " ".join(scenario.notes).lower()

        # Should document key parameters
        assert "zoning" in notes_text or "density" in notes_text
        assert any(char.isdigit() for char in notes_text)  # Contains numbers

    def test_scenario_completeness(self, r1_parcel):
        """Test that scenario has all required fields."""
        scenario = analyze_base_zoning(r1_parcel)

        # All required fields should be present
        assert scenario.scenario_name
        assert scenario.legal_basis
        assert scenario.max_units > 0
        assert scenario.max_building_sqft > 0
        assert scenario.max_height_ft > 0
        assert scenario.max_stories > 0
        assert scenario.setbacks
        assert len(scenario.setbacks) >= 3  # front, rear, side
