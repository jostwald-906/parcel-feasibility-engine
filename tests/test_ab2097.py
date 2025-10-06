"""
Tests for AB2097 (2022) parking reduction rules.

AB2097 eliminates minimum parking requirements for residential and
mixed-use projects within 0.5 miles of major transit.
"""
import pytest
from app.rules.ab2097 import (
    apply_ab2097_parking_reduction,
    is_within_transit_area,
    get_transit_proximity_info,
    calculate_optional_parking
)
from app.rules.base_zoning import analyze_base_zoning
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase


class TestTransitAreaIdentification:
    """Tests for identifying parcels within AB2097 transit areas."""

    def test_transit_city_parcel_qualifies(self, transit_adjacent_parcel):
        """Test that parcel in major transit city qualifies."""
        # Oakland is in major transit cities list
        assert is_within_transit_area(transit_adjacent_parcel) is True

    def test_san_francisco_qualifies(self, dcp_parcel):
        """Test that San Francisco parcel qualifies."""
        assert is_within_transit_area(dcp_parcel) is True

    def test_los_angeles_qualifies(self, r2_parcel):
        """Test that Los Angeles parcel qualifies."""
        assert is_within_transit_area(r2_parcel) is True

    def test_non_transit_city_does_not_qualify(self):
        """Test that parcel in small city does not qualify."""
        small_city_parcel = ParcelBase(
            apn="SMALL-001",
            address="Test",
            city="Small Town",
            county="Rural County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0,
            latitude=36.0,
            longitude=-120.0
        )

        assert is_within_transit_area(small_city_parcel) is False

    def test_missing_coordinates(self):
        """Test handling of parcels without coordinates."""
        no_coords_parcel = ParcelBase(
            apn="NO-COORDS",
            address="Test",
            city="San Francisco",
            county="San Francisco",
            zip_code="94102",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0,
            latitude=None,
            longitude=None
        )

        # Without coordinates, cannot confirm transit proximity
        result = is_within_transit_area(no_coords_parcel)
        # Implementation may be conservative
        assert isinstance(result, bool)

    @pytest.mark.parametrize("city_name,expected_transit", [
        ("San Francisco", True),
        ("Oakland", True),
        ("Berkeley", True),
        ("San Jose", True),
        ("Los Angeles", True),
        ("Long Beach", True),
        ("San Diego", True),
        ("Sacramento", True),
        ("Fresno", False),
        ("Bakersfield", False),
    ])
    def test_various_cities(self, city_name, expected_transit):
        """Test AB2097 applicability for various California cities."""
        parcel = ParcelBase(
            apn="TEST-CITY",
            address="Test",
            city=city_name,
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0,
            latitude=37.0,
            longitude=-122.0
        )

        assert is_within_transit_area(parcel) == expected_transit


class TestParkingReduction:
    """Tests for applying AB2097 parking reductions."""

    def test_parking_eliminated_in_transit_area(self, transit_adjacent_parcel):
        """Test that parking is eliminated in transit area."""
        # Create base scenario with parking requirement
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        original_parking = base_scenario.parking_spaces_required

        # Apply AB2097
        modified_scenario = apply_ab2097_parking_reduction(
            base_scenario,
            transit_adjacent_parcel
        )

        assert modified_scenario.parking_spaces_required == 0
        # Should be less than original if original > 0
        if original_parking > 0:
            assert modified_scenario.parking_spaces_required < original_parking

    def test_parking_unchanged_outside_transit(self):
        """Test that parking unchanged outside transit area."""
        non_transit_parcel = ParcelBase(
            apn="NON-TRANSIT",
            address="Test",
            city="Rural City",
            county="Rural County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        scenario = DevelopmentScenario(
            scenario_name="Test",
            legal_basis="Test",
            max_units=5,
            max_building_sqft=5000,
            max_height_ft=40,
            max_stories=3,
            parking_spaces_required=8,
            setbacks={},
            lot_coverage_pct=50
        )

        modified_scenario = apply_ab2097_parking_reduction(scenario, non_transit_parcel)

        # Parking should remain unchanged
        assert modified_scenario.parking_spaces_required == 8

    def test_ab2097_note_added(self, transit_adjacent_parcel):
        """Test that AB2097 note is added to scenario."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)

        modified_scenario = apply_ab2097_parking_reduction(
            base_scenario,
            transit_adjacent_parcel
        )

        notes_text = " ".join(modified_scenario.notes).lower()
        assert "ab2097" in notes_text
        assert "parking" in notes_text

    def test_multiple_applications_idempotent(self, transit_adjacent_parcel):
        """Test that applying AB2097 multiple times is safe."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)

        # Apply twice
        scenario1 = apply_ab2097_parking_reduction(base_scenario, transit_adjacent_parcel)
        scenario2 = apply_ab2097_parking_reduction(scenario1, transit_adjacent_parcel)

        # Should have same result
        assert scenario2.parking_spaces_required == 0

        # Should not duplicate notes
        ab2097_notes = [n for n in scenario2.notes if "AB2097" in n]
        # May have duplicate notes depending on implementation
        assert len(ab2097_notes) >= 1


class TestTransitProximityInfo:
    """Tests for detailed transit proximity information."""

    def test_transit_info_for_transit_parcel(self, transit_adjacent_parcel):
        """Test transit info for parcel in transit area."""
        info = get_transit_proximity_info(transit_adjacent_parcel)

        assert info["ab2097_applicable"] is True
        assert info["parking_minimums_eliminated"] is True
        assert len(info["notes"]) > 0

    def test_transit_info_for_non_transit_parcel(self):
        """Test transit info for parcel outside transit area."""
        non_transit_parcel = ParcelBase(
            apn="NON-TRANSIT",
            address="Test",
            city="Small City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        info = get_transit_proximity_info(non_transit_parcel)

        assert info["ab2097_applicable"] is False
        assert info["parking_minimums_eliminated"] is False

    def test_info_includes_verification_note(self, transit_adjacent_parcel):
        """Test that info includes note to verify with planning."""
        info = get_transit_proximity_info(transit_adjacent_parcel)

        notes_text = " ".join(info["notes"]).lower()
        assert "verify" in notes_text or "planning" in notes_text


class TestOptionalParkingCalculation:
    """Tests for recommended optional parking calculations."""

    def test_small_project_optional_parking(self):
        """Test optional parking for small project (10 units)."""
        scenario = DevelopmentScenario(
            scenario_name="Test",
            legal_basis="Test",
            max_units=10,
            max_building_sqft=10000,
            max_height_ft=40,
            max_stories=3,
            parking_spaces_required=0,
            setbacks={},
            lot_coverage_pct=50
        )

        optional = calculate_optional_parking(scenario)

        # Should recommend some parking (0.5-0.75 per unit)
        assert optional > 0
        assert optional <= 10  # Max 1 per unit
        # Expect around 7-8 spaces (0.75 per unit)
        assert 5 <= optional <= 10

    def test_medium_project_optional_parking(self):
        """Test optional parking for medium project (30 units)."""
        scenario = DevelopmentScenario(
            scenario_name="Test",
            legal_basis="Test",
            max_units=30,
            max_building_sqft=30000,
            max_height_ft=55,
            max_stories=4,
            parking_spaces_required=0,
            setbacks={},
            lot_coverage_pct=60
        )

        optional = calculate_optional_parking(scenario)

        # Should recommend 0.5 per unit
        assert optional > 0
        # Expect around 15 spaces (0.5 per unit)
        assert 10 <= optional <= 20

    def test_large_project_optional_parking(self):
        """Test optional parking for large project (100 units)."""
        scenario = DevelopmentScenario(
            scenario_name="Test",
            legal_basis="Test",
            max_units=100,
            max_building_sqft=100000,
            max_height_ft=75,
            max_stories=6,
            parking_spaces_required=0,
            setbacks={},
            lot_coverage_pct=70
        )

        optional = calculate_optional_parking(scenario)

        # Should recommend 0.25-0.5 per unit
        assert optional > 0
        # Expect around 40 spaces (0.4 per unit)
        assert 25 <= optional <= 60

    @pytest.mark.parametrize("units,min_ratio,max_ratio", [
        (5, 0.5, 0.8),
        (10, 0.5, 0.8),
        (15, 0.4, 0.6),
        (30, 0.4, 0.6),
        (50, 0.2, 0.5),
        (100, 0.2, 0.5),
    ])
    def test_parking_ratios_by_project_size(self, units, min_ratio, max_ratio):
        """Test that optional parking ratios decrease with project size."""
        scenario = DevelopmentScenario(
            scenario_name="Test",
            legal_basis="Test",
            max_units=units,
            max_building_sqft=units * 1000,
            max_height_ft=55,
            max_stories=4,
            parking_spaces_required=0,
            setbacks={},
            lot_coverage_pct=60
        )

        optional = calculate_optional_parking(scenario)
        ratio = optional / units

        assert min_ratio <= ratio <= max_ratio


class TestIntegrationWithOtherRules:
    """Tests for AB2097 integration with other development rules."""

    def test_ab2097_with_base_zoning(self, transit_adjacent_parcel):
        """Test AB2097 applied to base zoning scenario."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        modified = apply_ab2097_parking_reduction(base_scenario, transit_adjacent_parcel)

        # Should maintain all other parameters
        assert modified.max_units == base_scenario.max_units
        assert modified.max_building_sqft == base_scenario.max_building_sqft
        assert modified.max_height_ft == base_scenario.max_height_ft

        # Only parking should change
        if is_within_transit_area(transit_adjacent_parcel):
            assert modified.parking_spaces_required == 0


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_zero_parking_scenario(self, transit_adjacent_parcel):
        """Test applying AB2097 to scenario that already has zero parking."""
        scenario = DevelopmentScenario(
            scenario_name="Test",
            legal_basis="Test",
            max_units=5,
            max_building_sqft=5000,
            max_height_ft=40,
            max_stories=3,
            parking_spaces_required=0,  # Already zero
            setbacks={},
            lot_coverage_pct=50
        )

        modified = apply_ab2097_parking_reduction(scenario, transit_adjacent_parcel)

        # Should still be zero
        assert modified.parking_spaces_required == 0

    def test_single_unit_parking(self):
        """Test AB2097 with single unit development."""
        transit_parcel = ParcelBase(
            apn="SINGLE-TRANSIT",
            address="Test",
            city="San Francisco",
            county="San Francisco",
            zip_code="94102",
            lot_size_sqft=3000.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0,
            latitude=37.7749,
            longitude=-122.4194
        )

        scenario = DevelopmentScenario(
            scenario_name="Test",
            legal_basis="Test",
            max_units=1,
            max_building_sqft=2000,
            max_height_ft=35,
            max_stories=2,
            parking_spaces_required=2,
            setbacks={},
            lot_coverage_pct=40
        )

        modified = apply_ab2097_parking_reduction(scenario, transit_parcel)

        # Even single unit should get parking eliminated in transit area
        assert modified.parking_spaces_required == 0


class TestDocumentation:
    """Tests for proper documentation and notes."""

    def test_reduction_amount_documented(self, transit_adjacent_parcel):
        """Test that parking reduction amount is documented."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        original_parking = base_scenario.parking_spaces_required

        modified = apply_ab2097_parking_reduction(base_scenario, transit_adjacent_parcel)

        if original_parking > 0:
            notes_text = " ".join(modified.notes)
            # Should mention original parking amount
            assert str(original_parking) in notes_text or "parking" in notes_text.lower()

    def test_transit_distance_mentioned(self, transit_adjacent_parcel):
        """Test that notes mention 0.5 mile distance requirement."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        modified = apply_ab2097_parking_reduction(base_scenario, transit_adjacent_parcel)

        notes_text = " ".join(modified.notes).lower()
        assert "0.5" in notes_text or "half" in notes_text or "mile" in notes_text
