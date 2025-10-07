"""
Tests for ADU/JADU (Accessory Dwelling Unit) Analysis.

Tests Gov. Code § 65852.2 (ADU) and § 65852.22 (JADU) implementation.
"""
import pytest
from app.rules.state_law.adu import (
    analyze_adu,
    _is_residential_zoning,
    _calculate_max_adu_size,
    _create_detached_adu_scenario,
    _create_attached_adu_scenario,
    _create_jadu_scenario,
    _create_combo_scenario,
    get_adu_info
)
from app.models.parcel import ParcelBase


class TestADUEligibility:
    """Tests for ADU eligibility checks."""

    def test_residential_zoning_eligible(self, r1_parcel):
        """Test that residential parcels are eligible for ADU."""
        scenarios = analyze_adu(r1_parcel)
        assert len(scenarios) > 0

    def test_commercial_zoning_ineligible(self, commercial_parcel):
        """Test that commercial parcels are not eligible for ADU."""
        scenarios = analyze_adu(commercial_parcel)
        assert len(scenarios) == 0

    @pytest.mark.parametrize("zoning_code,expected_eligible", [
        ("R1", True),
        ("R2", True),
        ("R3", True),
        ("RS", True),
        ("RES", True),
        ("RESIDENTIAL", True),
        ("SINGLE-FAMILY", True),
        ("MULTI-FAMILY", True),
        ("C1", False),
        ("C2", False),
        ("C-OFFICE", False),
        ("M1", False),
        ("M-LIGHT", False),
    ])
    def test_zoning_code_eligibility(self, r1_parcel, zoning_code, expected_eligible):
        """Test various zoning codes for eligibility."""
        r1_parcel.zoning_code = zoning_code
        scenarios = analyze_adu(r1_parcel)

        if expected_eligible:
            assert len(scenarios) > 0, f"Expected {zoning_code} to be eligible"
        else:
            assert len(scenarios) == 0, f"Expected {zoning_code} to be ineligible"

    def test_coastal_zone_allowed_with_note(self, r1_parcel):
        """Test that ADU allowed in coastal zone with CDP note."""
        r1_parcel.in_coastal_zone = True
        scenarios = analyze_adu(r1_parcel)

        assert len(scenarios) > 0
        # Check for coastal note in at least one scenario
        has_coastal_note = any(
            any("Coastal" in note for note in scenario.notes)
            for scenario in scenarios
        )
        assert has_coastal_note


class TestADUSizeCalculations:
    """Tests for ADU size calculations per § 65852.2(a)(1)."""

    def test_studio_1br_size_850(self, r1_parcel):
        """Test studio/1-BR ADU size is 850 sq ft."""
        r1_parcel.avg_bedrooms_per_unit = 1
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 850

    def test_2br_size_1000(self, r1_parcel):
        """Test 2-BR ADU size is 1,000 sq ft."""
        r1_parcel.avg_bedrooms_per_unit = 2
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 1000

    def test_3plus_br_size_1200(self, r1_parcel):
        """Test 3+ BR ADU size is 1,200 sq ft."""
        r1_parcel.avg_bedrooms_per_unit = 3
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 1200

        r1_parcel.avg_bedrooms_per_unit = 4
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 1200

    def test_unknown_bedrooms_defaults_to_1000(self, r1_parcel):
        """Test unknown bedroom count defaults to 1,000 sq ft (2-BR)."""
        r1_parcel.avg_bedrooms_per_unit = None
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 1000

    @pytest.mark.parametrize("bedrooms,expected_size", [
        (0, 850),
        (0.5, 850),
        (1, 850),
        (1.5, 1000),
        (2, 1000),
        (2.5, 1200),
        (3, 1200),
        (4, 1200),
        (5, 1200),
    ])
    def test_size_calculation_parametrized(self, r1_parcel, bedrooms, expected_size):
        """Test size calculations for various bedroom counts."""
        r1_parcel.avg_bedrooms_per_unit = bedrooms
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == expected_size


class TestDetachedADU:
    """Tests for detached ADU scenarios."""

    def test_detached_adu_created(self, r1_parcel):
        """Test detached ADU scenario is created for eligible parcel."""
        scenario = _create_detached_adu_scenario(r1_parcel)
        assert scenario is not None
        assert scenario.scenario_name == "Detached ADU"

    def test_detached_adu_adds_one_unit(self, r1_parcel):
        """Test detached ADU adds 1 unit to existing count."""
        r1_parcel.existing_units = 1
        scenario = _create_detached_adu_scenario(r1_parcel)
        assert scenario.max_units == 2  # 1 existing + 1 ADU

    def test_detached_adu_zero_parking(self, r1_parcel):
        """Test detached ADU requires zero parking per AB 68/681/671."""
        scenario = _create_detached_adu_scenario(r1_parcel)
        assert scenario.parking_spaces_required == 0

    def test_detached_adu_4ft_setbacks(self, r1_parcel):
        """Test detached ADU has 4 ft side/rear setbacks per § 65852.2(d)(1)."""
        scenario = _create_detached_adu_scenario(r1_parcel)
        assert scenario.setbacks["side"] == 4.0
        assert scenario.setbacks["rear"] == 4.0

    def test_detached_adu_height_25ft(self, r1_parcel):
        """Test detached ADU max height is 25 ft (2-story)."""
        scenario = _create_detached_adu_scenario(r1_parcel)
        assert scenario.max_height_ft == 25.0
        assert scenario.max_stories == 2

    def test_detached_adu_statutory_references(self, r1_parcel):
        """Test detached ADU notes include statute references."""
        scenario = _create_detached_adu_scenario(r1_parcel)
        notes_text = " ".join(scenario.notes)

        assert "65852.2" in notes_text
        assert "AB 68" in notes_text or "AB 681" in notes_text or "AB 671" in notes_text
        assert "Ministerial" in notes_text or "ministerial" in notes_text.lower()

    def test_tiny_lot_no_detached_adu(self, small_r1_parcel):
        """Test very small lot cannot accommodate detached ADU."""
        small_r1_parcel.lot_size_sqft = 500  # Very small
        scenario = _create_detached_adu_scenario(small_r1_parcel)
        assert scenario is None


class TestAttachedADU:
    """Tests for attached ADU scenarios."""

    def test_attached_adu_created(self, r1_parcel):
        """Test attached ADU scenario created when existing structure present."""
        scenario = _create_attached_adu_scenario(r1_parcel)
        assert scenario is not None
        assert scenario.scenario_name == "Attached ADU"

    def test_attached_adu_can_match_primary(self, r1_parcel):
        """Test attached ADU can match primary dwelling size."""
        r1_parcel.existing_building_sqft = 2000
        r1_parcel.avg_bedrooms_per_unit = 1  # Would normally be 850 sq ft

        scenario = _create_attached_adu_scenario(r1_parcel)

        # Should use larger of standard (850) or primary dwelling (2000)
        # But capped at 1,200 per statute
        assert scenario.max_building_sqft >= r1_parcel.existing_building_sqft + 1200

    def test_attached_adu_zero_setbacks(self, r1_parcel):
        """Test attached ADU has 0 ft setbacks for conversions."""
        scenario = _create_attached_adu_scenario(r1_parcel)
        assert scenario.setbacks["side"] == 0.0
        assert scenario.setbacks["rear"] == 0.0
        assert scenario.setbacks["front"] == 0.0

    def test_attached_adu_zero_parking(self, r1_parcel):
        """Test attached ADU requires zero parking."""
        scenario = _create_attached_adu_scenario(r1_parcel)
        assert scenario.parking_spaces_required == 0

    def test_attached_adu_requires_existing_structure(self, r1_parcel):
        """Test attached ADU requires minimum existing structure."""
        r1_parcel.existing_building_sqft = 300  # Too small
        scenario = _create_attached_adu_scenario(r1_parcel)
        assert scenario is None

        r1_parcel.existing_building_sqft = 500  # Sufficient
        scenario = _create_attached_adu_scenario(r1_parcel)
        assert scenario is not None

    def test_attached_adu_1200_cap(self, r1_parcel):
        """Test attached ADU capped at 1,200 sq ft per statute."""
        r1_parcel.existing_building_sqft = 3000  # Large primary dwelling
        scenario = _create_attached_adu_scenario(r1_parcel)

        # New ADU portion should not exceed 1,200 sq ft
        adu_size = scenario.max_building_sqft - r1_parcel.existing_building_sqft
        assert adu_size <= 1200


class TestJADU:
    """Tests for JADU (Junior ADU) scenarios per § 65852.22."""

    def test_jadu_created(self, r1_parcel):
        """Test JADU scenario created when existing structure present."""
        scenario = _create_jadu_scenario(r1_parcel)
        assert scenario is not None
        assert scenario.scenario_name == "Junior ADU (JADU)"

    def test_jadu_500_sqft_max(self, r1_parcel):
        """Test JADU is 500 sq ft maximum per § 65852.22."""
        scenario = _create_jadu_scenario(r1_parcel)

        jadu_size = scenario.max_building_sqft - r1_parcel.existing_building_sqft
        assert jadu_size == 500

    def test_jadu_zero_setbacks(self, r1_parcel):
        """Test JADU has 0 ft setbacks (within existing structure)."""
        scenario = _create_jadu_scenario(r1_parcel)
        assert scenario.setbacks["side"] == 0.0
        assert scenario.setbacks["rear"] == 0.0
        assert scenario.setbacks["front"] == 0.0

    def test_jadu_zero_parking(self, r1_parcel):
        """Test JADU requires zero parking."""
        scenario = _create_jadu_scenario(r1_parcel)
        assert scenario.parking_spaces_required == 0

    def test_jadu_requires_existing_structure(self, r1_parcel):
        """Test JADU requires existing structure of at least 500 sq ft."""
        r1_parcel.existing_building_sqft = 400  # Too small
        scenario = _create_jadu_scenario(r1_parcel)
        assert scenario is None

        r1_parcel.existing_building_sqft = 500  # Sufficient
        scenario = _create_jadu_scenario(r1_parcel)
        assert scenario is not None

    def test_jadu_owner_occupancy_note(self, r1_parcel):
        """Test JADU notes include owner-occupancy requirement."""
        scenario = _create_jadu_scenario(r1_parcel)
        notes_text = " ".join(scenario.notes).lower()

        assert "owner" in notes_text and "occupancy" in notes_text

    def test_jadu_statutory_references(self, r1_parcel):
        """Test JADU notes include § 65852.22 reference."""
        scenario = _create_jadu_scenario(r1_parcel)
        notes_text = " ".join(scenario.notes)

        assert "65852.22" in notes_text


class TestComboADUJADU:
    """Tests for combo ADU + JADU scenarios."""

    def test_combo_created(self, r1_parcel):
        """Test combo ADU + JADU scenario created when eligible."""
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500
        scenario = _create_combo_scenario(r1_parcel)

        assert scenario is not None
        assert "ADU + JADU" in scenario.scenario_name

    def test_combo_adds_two_units(self, r1_parcel):
        """Test combo adds 2 units (1 ADU + 1 JADU)."""
        r1_parcel.existing_units = 1
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500

        scenario = _create_combo_scenario(r1_parcel)

        assert scenario.max_units == 3  # 1 existing + 1 ADU + 1 JADU

    def test_combo_zero_parking(self, r1_parcel):
        """Test combo requires zero parking."""
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500

        scenario = _create_combo_scenario(r1_parcel)
        assert scenario.parking_spaces_required == 0

    def test_combo_requires_sufficient_lot(self, r1_parcel):
        """Test combo requires sufficient lot size and structure."""
        # Too small lot
        r1_parcel.lot_size_sqft = 2000
        r1_parcel.existing_building_sqft = 1500
        scenario = _create_combo_scenario(r1_parcel)
        assert scenario is None

        # Too small structure
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 500
        scenario = _create_combo_scenario(r1_parcel)
        assert scenario is None

        # Sufficient both
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500
        scenario = _create_combo_scenario(r1_parcel)
        assert scenario is not None

    def test_combo_total_sqft(self, r1_parcel):
        """Test combo total square footage is ADU + JADU."""
        r1_parcel.avg_bedrooms_per_unit = 2  # 1,000 sq ft ADU
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500

        scenario = _create_combo_scenario(r1_parcel)

        expected_new_sqft = 1000 + 500  # ADU + JADU
        actual_new_sqft = scenario.max_building_sqft - r1_parcel.existing_building_sqft

        assert actual_new_sqft == expected_new_sqft


class TestADUScenarioGeneration:
    """Tests for full ADU scenario generation."""

    def test_generates_multiple_scenarios(self, r1_parcel):
        """Test that analyze_adu generates multiple scenarios."""
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500
        r1_parcel.existing_units = 1

        scenarios = analyze_adu(r1_parcel)

        # Should generate: detached, attached, JADU, combo
        assert len(scenarios) >= 3

    def test_scenario_names_unique(self, r1_parcel):
        """Test that scenario names are unique."""
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500

        scenarios = analyze_adu(r1_parcel)
        scenario_names = [s.scenario_name for s in scenarios]

        assert len(scenario_names) == len(set(scenario_names))

    def test_all_scenarios_have_zero_parking(self, r1_parcel):
        """Test that all ADU scenarios have zero parking required."""
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500

        scenarios = analyze_adu(r1_parcel)

        for scenario in scenarios:
            assert scenario.parking_spaces_required == 0

    def test_all_scenarios_ministerial(self, r1_parcel):
        """Test that all scenarios note ministerial approval."""
        r1_parcel.lot_size_sqft = 6000
        r1_parcel.existing_building_sqft = 1500

        scenarios = analyze_adu(r1_parcel)

        for scenario in scenarios:
            notes_text = " ".join(scenario.notes).lower()
            assert "ministerial" in notes_text

    def test_vacant_lot_only_detached(self, r1_parcel):
        """Test vacant lot only gets detached ADU scenario."""
        r1_parcel.existing_building_sqft = 0
        r1_parcel.existing_units = 0

        scenarios = analyze_adu(r1_parcel)

        # Should only have detached ADU (no attached, JADU, or combo)
        assert len(scenarios) == 1
        assert scenarios[0].scenario_name == "Detached ADU"

    def test_small_existing_structure_limited_scenarios(self, r1_parcel):
        """Test small existing structure limits scenarios."""
        r1_parcel.existing_building_sqft = 600
        r1_parcel.lot_size_sqft = 2500

        scenarios = analyze_adu(r1_parcel)

        # Should have detached, attached, JADU, but no combo (lot too small)
        scenario_names = [s.scenario_name for s in scenarios]
        assert "Detached ADU" in scenario_names
        assert "Attached ADU" in scenario_names
        assert "Junior ADU (JADU)" in scenario_names


class TestADUInfo:
    """Tests for ADU program information."""

    def test_get_adu_info_returns_dict(self):
        """Test get_adu_info returns program information."""
        info = get_adu_info()

        assert isinstance(info, dict)
        assert "program_name" in info
        assert "legal_basis" in info
        assert "size_limits" in info
        assert "parking_required" in info

    def test_adu_info_parking_zero(self):
        """Test ADU info confirms zero parking required."""
        info = get_adu_info()
        assert info["parking_required"] == 0

    def test_adu_info_size_limits(self):
        """Test ADU info has correct size limits."""
        info = get_adu_info()

        assert info["size_limits"]["adu_studio_1br"] == 850
        assert info["size_limits"]["adu_2br"] == 1000
        assert info["size_limits"]["adu_3plus_br"] == 1200
        assert info["size_limits"]["jadu_max"] == 500

    def test_adu_info_ministerial(self):
        """Test ADU info confirms ministerial approval."""
        info = get_adu_info()
        assert "Ministerial" in info["approval_type"] or "ministerial" in info["approval_type"].lower()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_lot_size(self, r1_parcel):
        """Test handling of zero lot size."""
        r1_parcel.lot_size_sqft = 0
        scenarios = analyze_adu(r1_parcel)

        # Should not crash, may return empty or limited scenarios
        assert isinstance(scenarios, list)

    def test_negative_bedroom_count(self, r1_parcel):
        """Test handling of negative bedroom count."""
        r1_parcel.avg_bedrooms_per_unit = -1
        max_size = _calculate_max_adu_size(r1_parcel)

        # Should default to 850 (studio/1-BR size)
        assert max_size == 850

    def test_very_large_primary_dwelling(self, r1_parcel):
        """Test attached ADU with very large primary dwelling."""
        r1_parcel.existing_building_sqft = 10000  # Very large

        scenario = _create_attached_adu_scenario(r1_parcel)

        # Should still cap at 1,200 sq ft for attached ADU
        adu_size = scenario.max_building_sqft - r1_parcel.existing_building_sqft
        assert adu_size <= 1200

    def test_fractional_bedrooms(self, r1_parcel):
        """Test handling of fractional bedroom counts."""
        # 1.5 bedrooms should be in 2-BR category (1,000 sq ft)
        r1_parcel.avg_bedrooms_per_unit = 1.5
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 1000

        # 2.5 bedrooms should be in 3+ category (1,200 sq ft)
        r1_parcel.avg_bedrooms_per_unit = 2.5
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 1200

        # 2.4 bedrooms should still be in 2-BR category (1,000 sq ft)
        r1_parcel.avg_bedrooms_per_unit = 2.4
        max_size = _calculate_max_adu_size(r1_parcel)
        assert max_size == 1000


class TestCoastalZone:
    """Tests for Coastal Zone ADU scenarios."""

    def test_coastal_zone_scenarios_include_note(self, coastal_parcel):
        """Test Coastal Zone parcels include CDP note."""
        coastal_parcel.in_coastal_zone = True
        scenarios = analyze_adu(coastal_parcel)

        # At least one scenario should have coastal note
        has_coastal_note = False
        for scenario in scenarios:
            if any("Coastal" in note or "CDP" in note for note in scenario.notes):
                has_coastal_note = True
                break

        assert has_coastal_note

    def test_coastal_zone_still_eligible(self, coastal_parcel):
        """Test Coastal Zone parcels still eligible (not excluded)."""
        coastal_parcel.in_coastal_zone = True
        scenarios = analyze_adu(coastal_parcel)

        assert len(scenarios) > 0
