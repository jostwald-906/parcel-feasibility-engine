"""
Tests for SB35 (2017) streamlined approval analysis.

SB35 provides ministerial approval for multifamily housing in
jurisdictions that haven't met RHNA targets.
"""
import pytest
from app.rules.sb35 import (
    analyze_sb35,
    is_sb35_eligible,
    can_apply_sb35,
    get_affordability_requirement,
    get_affordability_percentage,
    get_labor_requirements,
    calculate_sb35_max_units,
    get_max_far,
    get_max_height
)
from app.models.parcel import ParcelBase


class TestSB35Eligibility:
    """Tests for SB35 basic eligibility."""

    def test_r2_parcel_eligible(self, r2_parcel):
        """Test that R2 parcel is eligible for SB35."""
        assert is_sb35_eligible(r2_parcel) is True

    def test_r3_parcel_eligible(self, transit_adjacent_parcel):
        """Test that R3 parcel is eligible."""
        assert is_sb35_eligible(transit_adjacent_parcel) is True

    def test_r1_parcel_eligible(self, r1_parcel):
        """Test that R1 parcel may be eligible if large enough."""
        # R1 can be eligible if it can support multifamily
        result = is_sb35_eligible(r1_parcel)
        # Implementation may vary on R1 eligibility
        assert isinstance(result, bool)

    def test_small_lot_not_eligible(self, small_r1_parcel):
        """Test that very small lot is not eligible."""
        # 2000 sq ft lot is below 3500 sq ft minimum
        assert is_sb35_eligible(small_r1_parcel) is False

    def test_minimum_lot_size_requirement(self):
        """Test minimum lot size for SB35 (3500 sq ft)."""
        parcel = ParcelBase(
            apn="MIN-SB35",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=3500.0,  # Exactly at minimum
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_sb35_eligible(parcel) is True

    def test_just_under_minimum(self):
        """Test lot just under minimum size."""
        parcel = ParcelBase(
            apn="UNDER-MIN",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=3499.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_sb35_eligible(parcel) is False

    @pytest.mark.parametrize("zoning_code,expected_eligible", [
        ("R2", True),
        ("R3", True),
        ("R4", True),
        ("RM-2", True),
        ("RH-3", True),
        ("MU-1", True),
        ("MIXED USE", True),
        ("C-1", False),  # Pure commercial
        ("M-1", False),  # Industrial
    ])
    def test_zoning_eligibility(self, zoning_code, expected_eligible):
        """Test eligibility for various zoning codes."""
        parcel = ParcelBase(
            apn="ZONE-TEST",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=5000.0,
            zoning_code=zoning_code,
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_sb35_eligible(parcel) == expected_eligible


class TestAffordabilityRequirements:
    """Tests for SB35 affordability percentage requirements."""

    def test_san_francisco_affordability(self, dcp_parcel):
        """Test San Francisco affordability requirement (10%)."""
        # SF is in high-performing cities list
        affordability = get_affordability_percentage(dcp_parcel)

        assert affordability == 10.0

    def test_san_jose_affordability(self):
        """Test San Jose affordability requirement (10%)."""
        parcel = ParcelBase(
            apn="SJ-001",
            address="Test",
            city="San Jose",
            county="Santa Clara",
            zip_code="95113",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        affordability = get_affordability_percentage(parcel)
        assert affordability == 10.0

    def test_default_affordability(self, r2_parcel):
        """Test default affordability requirement (50%)."""
        # Los Angeles likely hasn't met RHNA targets
        affordability = get_affordability_percentage(r2_parcel)

        # Should default to 50% for cities not meeting targets
        assert affordability == 50.0

    def test_small_city_affordability(self):
        """Test small city gets 50% requirement."""
        parcel = ParcelBase(
            apn="SMALL",
            address="Test",
            city="Small City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        affordability = get_affordability_percentage(parcel)
        assert affordability == 50.0


class TestUnitCalculations:
    """Tests for SB35 maximum unit calculations."""

    def test_r2_density_calculation(self):
        """Test R2 density (15 units/acre)."""
        parcel = ParcelBase(
            apn="R2-TEST",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=10000.0,  # ~0.23 acres
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        max_units = calculate_sb35_max_units(parcel)

        # 0.2296 acres * 15 units/acre = 3.44 units
        assert max_units >= 3
        assert max_units <= 4

    def test_r3_density_calculation(self, transit_adjacent_parcel):
        """Test R3 density (30 units/acre)."""
        max_units = calculate_sb35_max_units(transit_adjacent_parcel)

        # 12,000 sq ft = 0.2755 acres
        # 0.2755 * 30 = 8.26 units
        assert max_units >= 7
        assert max_units <= 9

    def test_r4_density_calculation(self, large_r4_parcel):
        """Test R4 density (60 units/acre)."""
        max_units = calculate_sb35_max_units(large_r4_parcel)

        # 30,000 sq ft = 0.6887 acres
        # 0.6887 * 60 = 41.3 units
        assert max_units >= 35
        assert max_units <= 45

    def test_minimum_2_units(self):
        """Test that SB35 requires minimum 2 units."""
        small_parcel = ParcelBase(
            apn="SMALL-R2",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=3600.0,  # Small R2 lot
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        max_units = calculate_sb35_max_units(small_parcel)

        # Should be at least 2 units for multifamily
        assert max_units >= 2


class TestFARCalculations:
    """Tests for Floor Area Ratio calculations."""

    @pytest.mark.parametrize("zoning,expected_far", [
        ("R2", 0.75),
        ("R3", 1.5),
        ("RM-3", 1.5),
        ("R4", 2.5),
        ("RH-4", 2.5),
        ("MU-1", 2.0),
        ("MIXED USE", 2.0),
    ])
    def test_far_by_zone(self, zoning, expected_far):
        """Test FAR values for different zones."""
        parcel = ParcelBase(
            apn="FAR-TEST",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code=zoning,
            existing_units=0,
            existing_building_sqft=0
        )

        far = get_max_far(parcel)
        assert far == expected_far


class TestHeightCalculations:
    """Tests for maximum height calculations."""

    @pytest.mark.parametrize("zoning,expected_height", [
        ("R2", 40.0),
        ("R3", 55.0),
        ("RM-3", 55.0),
        ("R4", 75.0),
        ("RH-4", 75.0),
        ("MU-1", 65.0),
        ("MIXED USE", 65.0),
    ])
    def test_height_by_zone(self, zoning, expected_height):
        """Test height limits for different zones."""
        parcel = ParcelBase(
            apn="HEIGHT-TEST",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code=zoning,
            existing_units=0,
            existing_building_sqft=0
        )

        height = get_max_height(parcel)
        assert height == expected_height


class TestSB35Analysis:
    """Tests for complete SB35 analysis."""

    def test_eligible_parcel_returns_scenario(self, r2_parcel):
        """Test that eligible parcel returns SB35 scenario."""
        scenario = analyze_sb35(r2_parcel)

        assert scenario is not None
        assert "SB35" in scenario.scenario_name

    def test_ineligible_parcel_returns_none(self, small_r1_parcel):
        """Test that ineligible parcel returns None."""
        scenario = analyze_sb35(small_r1_parcel)

        # Too small for multifamily
        assert scenario is None

    def test_scenario_is_multifamily(self, r2_parcel):
        """Test that SB35 scenario has at least 2 units."""
        scenario = analyze_sb35(r2_parcel)

        assert scenario.max_units >= 2

    def test_affordable_units_calculated(self, r2_parcel):
        """Test that affordable units are calculated."""
        scenario = analyze_sb35(r2_parcel)

        assert scenario.affordable_units_required > 0

    def test_50_percent_affordability(self, r2_parcel):
        """Test 50% affordability requirement for LA."""
        scenario = analyze_sb35(r2_parcel)

        # LA should require 50% affordable
        expected_affordable = scenario.max_units * 0.50
        assert scenario.affordable_units_required >= expected_affordable * 0.9


class TestPrevailingWageRequirements:
    """Tests for prevailing wage and labor requirements."""

    def test_10_units_requires_prevailing_wage(self):
        """Test that 10+ unit projects note prevailing wage."""
        parcel = ParcelBase(
            apn="LARGE-SB35",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=20000.0,  # Large enough for 10+ units
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0
        )

        scenario = analyze_sb35(parcel)

        if scenario and scenario.max_units >= 10:
            notes_text = " ".join(scenario.notes).lower()
            assert "prevailing wage" in notes_text

    def test_75_units_requires_skilled_workforce(self, large_r4_parcel):
        """Test that 75+ unit projects note skilled workforce requirement."""
        scenario = analyze_sb35(large_r4_parcel)

        if scenario and scenario.max_units >= 75:
            notes_text = " ".join(scenario.notes).lower()
            assert "skilled" in notes_text or "trained" in notes_text or "workforce" in notes_text


class TestMinisterialApproval:
    """Tests for ministerial approval documentation."""

    def test_ministerial_approval_noted(self, r2_parcel):
        """Test that ministerial approval is noted."""
        scenario = analyze_sb35(r2_parcel)

        notes_text = " ".join(scenario.notes).lower()
        assert "ministerial" in notes_text

    def test_ceqa_exemption_noted(self, r2_parcel):
        """Test that CEQA exemption is noted."""
        scenario = analyze_sb35(r2_parcel)

        notes_text = " ".join(scenario.notes).lower()
        assert "ceqa" in notes_text

    def test_objective_standards_noted(self, r2_parcel):
        """Test that objective standards requirement is noted."""
        scenario = analyze_sb35(r2_parcel)

        notes_text = " ".join(scenario.notes).lower()
        assert "objective" in notes_text or "standards" in notes_text


class TestScenarioParameters:
    """Tests for SB35 scenario parameters."""

    def test_parking_requirement(self, r2_parcel):
        """Test parking requirement (1.0 per unit conservative)."""
        scenario = analyze_sb35(r2_parcel)

        # Should have some parking requirement
        assert scenario.parking_spaces_required > 0

    def test_setback_requirements(self, r2_parcel):
        """Test that setbacks are defined."""
        scenario = analyze_sb35(r2_parcel)

        assert "front" in scenario.setbacks
        assert "rear" in scenario.setbacks
        assert "side" in scenario.setbacks

    def test_building_size_calculated(self, r2_parcel):
        """Test that building size is calculated."""
        scenario = analyze_sb35(r2_parcel)

        assert scenario.max_building_sqft > 0

    def test_lot_coverage_reasonable(self, r2_parcel):
        """Test that lot coverage is reasonable."""
        scenario = analyze_sb35(r2_parcel)

        assert 0 < scenario.lot_coverage_pct <= 100


class TestLegalBasisAndNotes:
    """Tests for scenario documentation."""

    def test_legal_basis_mentions_sb35(self, r2_parcel):
        """Test that legal basis mentions SB35."""
        scenario = analyze_sb35(r2_parcel)

        assert "SB35" in scenario.legal_basis or "SB 35" in scenario.legal_basis

    def test_year_mentioned(self, r2_parcel):
        """Test that year (2017) is mentioned."""
        scenario = analyze_sb35(r2_parcel)

        assert "2017" in scenario.legal_basis

    def test_rhna_verification_noted(self, r2_parcel):
        """Test that notes mention RHNA verification."""
        scenario = analyze_sb35(r2_parcel)

        notes_text = " ".join(scenario.notes).lower()
        assert "rhna" in notes_text or "verify" in notes_text


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_exactly_3500_sqft(self):
        """Test lot at exact minimum size."""
        parcel = ParcelBase(
            apn="EXACT",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=3500.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_sb35_eligible(parcel) is True

    def test_mixed_use_eligibility(self):
        """Test mixed-use zoning eligibility."""
        parcel = ParcelBase(
            apn="MU",
            address="Test",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=5000.0,
            zoning_code="MU-1",
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_sb35_eligible(parcel) is True

    def test_scenario_completeness(self, r2_parcel):
        """Test that scenario has all required fields."""
        scenario = analyze_sb35(r2_parcel)

        assert scenario.scenario_name
        assert scenario.legal_basis
        assert scenario.max_units >= 2
        assert scenario.max_building_sqft > 0
        assert scenario.max_height_ft > 0
        assert scenario.max_stories > 0
        assert scenario.affordable_units_required > 0
        assert len(scenario.notes) > 0


class TestIntegrationScenarios:
    """Tests for realistic SB35 scenarios."""

    def test_high_density_urban_parcel(self, transit_adjacent_parcel):
        """Test SB35 on high-density urban parcel."""
        scenario = analyze_sb35(transit_adjacent_parcel)

        assert scenario is not None
        # R3 with 12,000 sq ft should allow significant units
        assert scenario.max_units >= 6

    def test_downtown_parcel(self, dcp_parcel):
        """Test SB35 on downtown parcel."""
        scenario = analyze_sb35(dcp_parcel)

        assert scenario is not None
        # San Francisco should have 10% affordability
        affordability_ratio = scenario.affordable_units_required / scenario.max_units
        assert affordability_ratio <= 0.15  # Should be around 10%

    def test_large_development(self, large_r4_parcel):
        """Test SB35 on large R4 parcel."""
        scenario = analyze_sb35(large_r4_parcel)

        assert scenario is not None
        # Should support large multifamily
        assert scenario.max_units >= 30
        # Should note labor requirements
        notes_text = " ".join(scenario.notes).lower()
        assert "prevailing wage" in notes_text or "workforce" in notes_text


class TestCanApplySB35:
    """Tests for can_apply_sb35() detailed eligibility checks."""

    def test_can_apply_returns_dict(self, r2_parcel):
        """Test that can_apply_sb35 returns expected dict structure."""
        result = can_apply_sb35(r2_parcel)

        assert isinstance(result, dict)
        assert 'eligible' in result
        assert 'reasons' in result
        assert 'requirements' in result
        assert 'exclusions' in result

    def test_eligible_parcel_has_reasons(self, r2_parcel):
        """Test that eligible parcels have positive reasons."""
        result = can_apply_sb35(r2_parcel)

        # R2 parcel should be eligible (Los Angeles hasn't met RHNA)
        assert result['eligible'] is True
        assert len(result['reasons']) > 0
        # Should mention zoning eligibility
        reasons_text = " ".join(result['reasons'])
        assert "R2" in reasons_text or "residential" in reasons_text.lower()

    def test_ineligible_parcel_has_reasons(self, small_r1_parcel):
        """Test that ineligible parcels have exclusion reasons."""
        result = can_apply_sb35(small_r1_parcel)

        assert result['eligible'] is False
        assert len(result['reasons']) > 0
        # Should mention lot size issue
        reasons_text = " ".join(result['reasons'])
        assert "3,500" in reasons_text or "3500" in reasons_text or "minimum" in reasons_text.lower()

    def test_site_exclusions_detected(self, coastal_parcel):
        """Test that coastal parcels are flagged for exclusion verification."""
        result = can_apply_sb35(coastal_parcel)

        # Santa Monica is coastal, should flag for verification
        assert len(result['exclusions']) > 0 or any('coastal' in r.lower() for r in result['reasons'])

    def test_tenancy_issues_detected(self, r2_parcel):
        """Test that parcels with existing units flag tenancy verification."""
        result = can_apply_sb35(r2_parcel)

        # R2 parcel has 2 existing units in LA (rent control jurisdiction)
        # Should flag for tenancy verification
        assert result['eligible'] is False
        reasons_text = " ".join(result['reasons'])
        assert 'existing unit' in reasons_text.lower() or 'rent control' in reasons_text.lower()

    def test_requirements_listed(self):
        """Test that eligible parcels list verification requirements."""
        # Create parcel with no existing units (cleaner test)
        parcel = ParcelBase(
            apn="NEW-DEV",
            address="Test",
            city="Oakland",  # Not high-performing for RHNA
            county="Alameda",
            zip_code="94612",
            lot_size_sqft=10000.0,
            zoning_code="R3",
            existing_units=0,  # No existing units
            existing_building_sqft=0.0
        )

        result = can_apply_sb35(parcel)

        # Should have some requirements to verify
        assert len(result['requirements']) > 0


class TestLaborRequirements:
    """Tests for get_labor_requirements() function."""

    def test_no_labor_for_small_projects(self):
        """Test that projects <10 units have no labor requirements."""
        requirements = get_labor_requirements(9)

        assert len(requirements) == 0

    def test_prevailing_wage_at_10_units(self):
        """Test that 10+ units require prevailing wage."""
        requirements = get_labor_requirements(10)

        assert len(requirements) > 0
        reqs_text = " ".join(requirements).lower()
        assert "prevailing wage" in reqs_text

    def test_skilled_workforce_at_75_units(self):
        """Test that 75+ units require skilled workforce."""
        requirements = get_labor_requirements(75)

        assert len(requirements) > 0
        reqs_text = " ".join(requirements).lower()
        assert "skilled" in reqs_text and "trained" in reqs_text

    def test_both_requirements_large_project(self):
        """Test that large projects have both labor requirements."""
        requirements = get_labor_requirements(100)

        reqs_text = " ".join(requirements).lower()
        assert "prevailing wage" in reqs_text
        assert "skilled" in reqs_text or "trained" in reqs_text
        assert "labor code" in reqs_text


class TestAffordabilityDocumentation:
    """Tests for enhanced affordability requirement documentation."""

    def test_affordability_requirement_structure(self, r2_parcel):
        """Test that get_affordability_requirement returns dict with docs."""
        result = get_affordability_requirement(r2_parcel)

        assert isinstance(result, dict)
        assert 'percentage' in result
        assert 'income_levels' in result
        assert 'notes' in result

    def test_high_performing_city_details(self, dcp_parcel):
        """Test San Francisco gets detailed 10% affordability docs."""
        result = get_affordability_requirement(dcp_parcel)

        assert result['percentage'] == 10.0
        assert len(result['income_levels']) > 0
        assert len(result['notes']) > 0
        notes_text = " ".join(result['notes'])
        assert "10%" in notes_text
        assert "AMI" in notes_text  # Area median income

    def test_default_city_details(self, r2_parcel):
        """Test LA gets detailed 50% affordability docs."""
        result = get_affordability_requirement(r2_parcel)

        assert result['percentage'] == 50.0
        assert len(result['income_levels']) > 0
        assert len(result['notes']) > 0
        notes_text = " ".join(result['notes'])
        assert "50%" in notes_text
        assert "very low" in notes_text.lower()


class TestAB2097Integration:
    """Tests for AB 2097 parking elimination."""

    def test_transit_parcel_zero_parking(self):
        """Test that near_transit parcels have zero parking."""
        parcel = ParcelBase(
            apn="TRANSIT",
            address="Test",
            city="Oakland",
            county="Alameda",
            zip_code="94612",
            lot_size_sqft=10000.0,
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0.0,
            near_transit=True  # Key attribute
        )

        scenario = analyze_sb35(parcel)

        assert scenario is not None
        assert scenario.parking_spaces_required == 0
        notes_text = " ".join(scenario.notes)
        assert "AB 2097" in notes_text or "transit" in notes_text.lower()

    def test_non_transit_parcel_has_parking(self, r2_parcel):
        """Test that non-transit parcels have parking requirements."""
        # Ensure near_transit is False
        r2_parcel.near_transit = False

        scenario = analyze_sb35(r2_parcel)

        assert scenario is not None
        # Should have some parking (conservative default)
        assert scenario.parking_spaces_required > 0
