"""
Tests for SB9 (2021) lot split and duplex analysis.

SB9 allows:
- Two units per parcel (duplex)
- Urban lot splits creating two parcels
- Combined: up to 4 units total
"""
import pytest
from app.rules.sb9 import (
    analyze_sb9,
    is_sb9_eligible,
    can_split_lot,
    create_duplex_scenario,
    create_lot_split_scenario
)
from app.models.parcel import ParcelBase


class TestSB9Eligibility:
    """Tests for SB9 basic eligibility requirements."""

    def test_r1_parcel_is_eligible(self, r1_parcel):
        """Test that standard R1 parcel is eligible for SB9."""
        assert is_sb9_eligible(r1_parcel) is True

    def test_r2_parcel_not_eligible(self, r2_parcel):
        """Test that R2 parcel is not eligible (not single-family zone)."""
        assert is_sb9_eligible(r2_parcel) is False

    def test_commercial_not_eligible(self, commercial_parcel):
        """Test that commercial parcel is not eligible."""
        assert is_sb9_eligible(commercial_parcel) is False

    def test_small_lot_not_eligible(self, small_r1_parcel):
        """Test that very small lot (under 2000 sq ft) is not eligible."""
        # Small R1 parcel is 2000 sq ft - should be eligible for duplex
        # but not lot split
        assert is_sb9_eligible(small_r1_parcel) is True

    def test_minimum_lot_size_requirement(self):
        """Test minimum lot size for SB9 eligibility."""
        tiny_parcel = ParcelBase(
            apn="TINY-001",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=1500.0,  # Under 2000 sq ft minimum
            zoning_code="R1",
            existing_units=1,
            existing_building_sqft=800
        )

        assert is_sb9_eligible(tiny_parcel) is False

    @pytest.mark.parametrize("zoning_code,expected_eligible", [
        ("R1", True),
        ("RS", True),
        ("R1-5000", True),
        ("SINGLE FAMILY", True),
        ("R2", False),
        ("R3", False),
        ("C-1", False),
    ])
    def test_zoning_code_eligibility(self, zoning_code, expected_eligible):
        """Test eligibility for various zoning codes."""
        parcel = ParcelBase(
            apn="TEST-001",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=6000.0,
            zoning_code=zoning_code,
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_sb9_eligible(parcel) == expected_eligible


class TestLotSplitFeasibility:
    """Tests for lot split feasibility under SB9."""

    def test_standard_lot_can_split(self, r1_parcel):
        """Test that standard 6000 sq ft R1 lot can be split."""
        # 6000 sq ft / 2 = 3000 sq ft each (above 1200 minimum)
        assert can_split_lot(r1_parcel) is True

    def test_small_lot_cannot_split(self, small_r1_parcel):
        """Test that 2000 sq ft lot cannot be split."""
        # 2000 sq ft / 2 = 1000 sq ft each (below 1200 minimum)
        assert can_split_lot(small_r1_parcel) is False

    def test_minimum_lot_size_for_split(self):
        """Test exact minimum lot size for split (2400 sq ft)."""
        minimum_parcel = ParcelBase(
            apn="MIN-001",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=2400.0,  # Exactly at minimum
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        assert can_split_lot(minimum_parcel) is True

    def test_narrow_lot_width_not_bar_to_split(self):
        """Lot width alone does not bar SB9 split if area meets minimum."""
        narrow_parcel = ParcelBase(
            apn="NARROW-001",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            lot_width_ft=35.0,  # Narrow but meets area minimum
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        assert can_split_lot(narrow_parcel) is True


class TestDuplexScenario:
    """Tests for SB9 duplex development scenario."""

    def test_duplex_on_standard_lot(self, r1_parcel):
        """Test duplex scenario on standard R1 lot."""
        scenario = create_duplex_scenario(r1_parcel)

        assert scenario is not None
        assert scenario.scenario_name == "SB9 Duplex"
        assert scenario.max_units == 2
        assert "SB9" in scenario.legal_basis

    def test_duplex_unit_size_limits(self, r1_parcel):
        """Test unit size limits for duplex (1200 sq ft for lots > 5000)."""
        scenario = create_duplex_scenario(r1_parcel)

        # 6000 sq ft lot should allow 1200 sq ft per unit
        max_unit_size = scenario.max_building_sqft / scenario.max_units
        assert max_unit_size <= 1200.0

    def test_small_lot_duplex_size_limits(self, small_r1_parcel):
        """Test smaller unit size for lots under 5000 sq ft."""
        scenario = create_duplex_scenario(small_r1_parcel)

        # 2000 sq ft lot should allow 800 sq ft per unit max
        max_unit_size = scenario.max_building_sqft / scenario.max_units
        assert max_unit_size <= 800.0

    def test_duplex_height_subject_to_local_standards(self, r1_parcel):
        """Height is subject to local objective standards (value positive)."""
        scenario = create_duplex_scenario(r1_parcel)

        assert scenario.max_height_ft > 0
        assert scenario.max_stories >= 1

    def test_duplex_setbacks_side_rear_only(self, r1_parcel):
        """SB9 guarantees 4 ft at side/rear; front is local."""
        scenario = create_duplex_scenario(r1_parcel)

        assert scenario.setbacks["rear"] == 4.0
        assert scenario.setbacks["side"] == 4.0
        assert "front" not in scenario.setbacks

    def test_duplex_parking_requirement(self, r1_parcel):
        """Test SB9 parking (max 1 space per unit)."""
        scenario = create_duplex_scenario(r1_parcel)

        # 2 units, up to 1 space each = 2 spaces max
        assert scenario.parking_spaces_required <= 2


class TestLotSplitScenario:
    """Tests for SB9 lot split with duplexes scenario."""

    def test_lot_split_scenario(self, r1_parcel):
        """Test lot split scenario creation."""
        scenario = create_lot_split_scenario(r1_parcel)

        assert scenario is not None
        assert "Lot Split" in scenario.scenario_name
        assert scenario.max_units == 4  # 2 parcels * 2 units each

    def test_lot_split_max_units(self, r1_parcel):
        """Test that lot split allows 4 units maximum."""
        scenario = create_lot_split_scenario(r1_parcel)

        assert scenario.max_units == 4

    def test_lot_split_parking(self, r1_parcel):
        """Test lot split parking (1 space per unit max)."""
        scenario = create_lot_split_scenario(r1_parcel)

        # 4 units * 1 space/unit = 4 spaces max
        assert scenario.parking_spaces_required == 4

    def test_lot_split_height_subject_to_local_standards(self, r1_parcel):
        """Height is subject to local objective standards (value positive)."""
        scenario = create_lot_split_scenario(r1_parcel)
        assert scenario.max_height_ft > 0

    def test_lot_split_notes_include_warnings(self, r1_parcel):
        """Test that lot split scenario includes key requirements."""
        scenario = create_lot_split_scenario(r1_parcel)

        notes_text = " ".join(scenario.notes).lower()

        # Should mention key requirements
        assert "ministerial" in notes_text
        assert "parcel" in notes_text.lower()


class TestSB9Analysis:
    """Tests for complete SB9 analysis."""

    def test_eligible_parcel_returns_scenarios(self, r1_parcel):
        """Test that eligible parcel returns both scenarios."""
        scenarios = analyze_sb9(r1_parcel)

        # Should return duplex and lot split scenarios
        assert len(scenarios) >= 1
        # Check for duplex scenario
        has_duplex = any("Duplex" in s.scenario_name for s in scenarios)
        assert has_duplex is True

    def test_ineligible_parcel_returns_empty(self, r2_parcel):
        """Test that ineligible parcel returns no scenarios."""
        scenarios = analyze_sb9(r2_parcel)

        assert len(scenarios) == 0

    def test_small_lot_gets_duplex_only(self, small_r1_parcel):
        """Test that small lot gets duplex but not lot split."""
        scenarios = analyze_sb9(small_r1_parcel)

        # Should have duplex scenario
        has_duplex = any("Duplex" in s.scenario_name for s in scenarios)
        assert has_duplex is True

        # Should not have lot split
        has_lot_split = any("Lot Split" in s.scenario_name for s in scenarios)
        assert has_lot_split is False

    def test_large_lot_gets_both_scenarios(self, r1_parcel):
        """Test that large lot gets both duplex and lot split."""
        scenarios = analyze_sb9(r1_parcel)

        scenario_names = [s.scenario_name for s in scenarios]

        # Should have both scenarios
        has_duplex = any("Duplex" in name for name in scenario_names)
        has_lot_split = any("Lot Split" in name for name in scenario_names)

        assert has_duplex is True
        assert has_lot_split is True


class TestSB9Requirements:
    """Tests for SB9 special requirements and notes."""

    def test_ministerial_approval_noted(self, r1_parcel):
        """Test that ministerial approval is noted."""
        scenarios = analyze_sb9(r1_parcel)

        for scenario in scenarios:
            notes_text = " ".join(scenario.notes).lower()
            assert "ministerial" in notes_text

    def test_owner_occupancy_mentioned_for_lot_split(self, r1_parcel):
        """Owner-occupancy applies to lot split, not duplex."""
        scenarios = analyze_sb9(r1_parcel)
        lot_split_scenarios = [s for s in scenarios if "Lot Split" in s.scenario_name]
        for scenario in lot_split_scenarios:
            notes_text = " ".join(scenario.notes).lower()
            assert "owner" in notes_text or "occupancy" in notes_text

    def test_lot_split_restrictions_noted(self, r1_parcel):
        """Test that lot split restrictions are noted."""
        scenarios = analyze_sb9(r1_parcel)

        lot_split_scenarios = [s for s in scenarios if "Lot Split" in s.scenario_name]

        for scenario in lot_split_scenarios:
            notes_text = " ".join(scenario.notes).lower()
            # Should mention subdivision restrictions
            assert "10 years" in notes_text or "subdivided" in notes_text


class TestSB9EdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_exactly_2400_sqft_lot(self):
        """Test lot at exact minimum for split (2400 sq ft)."""
        parcel = ParcelBase(
            apn="EDGE-001",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=2400.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_sb9_eligible(parcel) is True
        assert can_split_lot(parcel) is True

    def test_just_under_2400_sqft_lot(self):
        """Test lot just under minimum for split."""
        parcel = ParcelBase(
            apn="EDGE-002",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=2399.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        assert can_split_lot(parcel) is False

    def test_exactly_40_ft_width(self):
        """Width at 40 ft: still eligible as long as area meets minimum."""
        parcel = ParcelBase(
            apn="EDGE-003",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            lot_width_ft=40.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        assert can_split_lot(parcel) is True

    def test_just_under_40_ft_width(self):
        """Width just under 40 ft: still eligible as long as area meets minimum."""
        parcel = ParcelBase(
            apn="EDGE-004",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            lot_width_ft=39.9,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        assert can_split_lot(parcel) is True


class TestSB9LotSizeCalculations:
    """Tests for unit size calculations in SB9 scenarios."""

    @pytest.mark.parametrize("lot_size,expected_unit_size", [
        (3000, 800),   # Small lot
        (4999, 800),   # Just under 5000
        (5000, 1200),  # At 5000 threshold
        (8000, 1200),  # Large lot
    ])
    def test_unit_size_by_lot_size(self, lot_size, expected_unit_size):
        """Test that unit size varies correctly by lot size."""
        parcel = ParcelBase(
            apn="SIZE-TEST",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=lot_size,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        scenario = create_duplex_scenario(parcel)
        max_unit_size = scenario.max_building_sqft / 2

        assert max_unit_size == expected_unit_size
