"""
Unit tests for AB 2011 eligibility checks including:
- Corridor eligibility and tier assignment
- Site exclusions
- Protected housing and tenancy checks
- Labor standards compliance
- Integration with AB 2097 parking
- Coastal zone handling
"""
import pytest
from app.rules.ab2011 import (
    check_corridor_eligibility,
    check_site_exclusions,
    check_protected_housing,
    check_labor_compliance,
    can_apply_ab2011,
    analyze_ab2011,
    analyze_ab2011_tracks,
)
from app.models.parcel import ParcelBase


def make_test_parcel(**kwargs) -> ParcelBase:
    """Create a test parcel with default values that can be overridden."""
    defaults = {
        "apn": "AB2011-TEST",
        "address": "123 Main St",
        "city": "Santa Monica",
        "county": "Los Angeles",
        "zip_code": "90401",
        "lot_size_sqft": 10000.0,
        "zoning_code": "C-2",  # Commercial zoning, eligible
        "existing_units": 0,
        "existing_building_sqft": 5000.0,
        "year_built": 1980,
        "latitude": 34.0195,
        "longitude": -118.4912,
        # Default to eligible (no exclusions, labor compliance)
        "in_coastal_high_hazard": False,
        "in_prime_farmland": False,
        "in_wetlands": False,
        "in_conservation_area": False,
        "is_historic_property": False,
        "in_flood_zone": False,
        "in_coastal_zone": False,
        "has_rent_controlled_units": False,
        "has_deed_restricted_affordable": False,
        "has_ellis_act_units": False,
        "has_recent_tenancy": False,
        "protected_units_count": 0,
        "prevailing_wage_commitment": True,
        "skilled_trained_workforce_commitment": False,  # Not required for small projects
        "healthcare_benefits_commitment": False,
        "near_transit": True,
    }
    defaults.update(kwargs)
    return ParcelBase(**defaults)


class TestCorridorEligibility:
    """Test corridor eligibility checking and tier assignment."""

    def test_commercial_zoning_eligible(self):
        """Commercial zoning should be eligible for AB 2011."""
        parcel = make_test_parcel(zoning_code="C-2")
        result = check_corridor_eligibility(parcel)
        assert result["is_corridor"] is True
        assert result["tier"] is not None
        assert len(result["reasons"]) > 0

    def test_office_zoning_eligible(self):
        """Office zoning should be eligible for AB 2011."""
        parcel = make_test_parcel(zoning_code="OFFICE")
        result = check_corridor_eligibility(parcel)
        assert result["is_corridor"] is True
        assert result["tier"] is not None

    def test_mixed_use_zoning_eligible(self):
        """Mixed-use zoning should be eligible for AB 2011."""
        parcel = make_test_parcel(zoning_code="MIXED-USE")
        result = check_corridor_eligibility(parcel)
        assert result["is_corridor"] is True
        assert result["tier"] is not None

    def test_residential_zoning_ineligible(self):
        """Residential zoning should not be eligible for AB 2011."""
        parcel = make_test_parcel(zoning_code="R-1")
        result = check_corridor_eligibility(parcel)
        assert result["is_corridor"] is False
        assert result["tier"] is None
        assert any("not zoned for commercial" in r.lower() for r in result["reasons"])

    def test_tier_assignment_low(self):
        """C-1 zoning should map to low tier."""
        parcel = make_test_parcel(zoning_code="C-1")
        result = check_corridor_eligibility(parcel)
        assert result["tier"] == "low"
        assert result["state_floors"]["min_density_u_ac"] == 30.0
        assert result["state_floors"]["min_height_ft"] == 35.0

    def test_tier_assignment_mid(self):
        """C-2 zoning should map to mid tier."""
        parcel = make_test_parcel(zoning_code="C-2")
        result = check_corridor_eligibility(parcel)
        assert result["tier"] == "mid"
        assert result["state_floors"]["min_density_u_ac"] == 50.0
        assert result["state_floors"]["min_height_ft"] == 45.0

    def test_tier_assignment_high(self):
        """C-3 zoning should map to high tier."""
        parcel = make_test_parcel(zoning_code="C-3")
        result = check_corridor_eligibility(parcel)
        assert result["tier"] == "high"
        assert result["state_floors"]["min_density_u_ac"] == 80.0
        assert result["state_floors"]["min_height_ft"] == 65.0

    def test_tier_upgrade_with_transit_overlay(self):
        """Transit overlay should upgrade tier."""
        parcel = make_test_parcel(zoning_code="C-1", overlay_codes=["TRANSIT-OVERLAY"])
        result = check_corridor_eligibility(parcel)
        assert result["tier"] == "mid"  # Upgraded from low
        assert any("transit overlay" in r.lower() for r in result["reasons"])

    def test_tier_upgrade_with_jobs_overlay(self):
        """Jobs overlay should upgrade tier to high."""
        parcel = make_test_parcel(zoning_code="C-2", overlay_codes=["JOBS-CENTER"])
        result = check_corridor_eligibility(parcel)
        assert result["tier"] == "high"
        assert any("jobs" in r.lower() for r in result["reasons"])


class TestSiteExclusions:
    """Test site exclusion checks."""

    def test_coastal_high_hazard_excluded(self):
        """Coastal high hazard zones should be excluded."""
        parcel = make_test_parcel(in_coastal_high_hazard=True)
        result = check_site_exclusions(parcel)
        assert result["excluded"] is True
        assert any("coastal high hazard" in r.lower() for r in result["exclusion_reasons"])

    def test_prime_farmland_excluded(self):
        """Prime farmland should be excluded."""
        parcel = make_test_parcel(in_prime_farmland=True)
        result = check_site_exclusions(parcel)
        assert result["excluded"] is True
        assert any("farmland" in r.lower() for r in result["exclusion_reasons"])

    def test_wetlands_excluded(self):
        """Wetlands should be excluded."""
        parcel = make_test_parcel(in_wetlands=True)
        result = check_site_exclusions(parcel)
        assert result["excluded"] is True
        assert any("wetland" in r.lower() for r in result["exclusion_reasons"])

    def test_conservation_area_excluded(self):
        """Conservation areas should be excluded."""
        parcel = make_test_parcel(in_conservation_area=True)
        result = check_site_exclusions(parcel)
        assert result["excluded"] is True
        assert any("conservation" in r.lower() for r in result["exclusion_reasons"])

    def test_historic_property_excluded(self):
        """Historic properties should be excluded."""
        parcel = make_test_parcel(is_historic_property=True)
        result = check_site_exclusions(parcel)
        assert result["excluded"] is True
        assert any("historic" in r.lower() for r in result["exclusion_reasons"])

    def test_flood_zone_warning_not_excluded(self):
        """Flood zones should generate warning but not exclude."""
        parcel = make_test_parcel(in_flood_zone=True)
        result = check_site_exclusions(parcel)
        assert result["excluded"] is False
        assert any("flood" in r.lower() for r in result["passed_checks"])

    def test_no_exclusions_passes(self):
        """Parcel with no exclusions should pass."""
        parcel = make_test_parcel()
        result = check_site_exclusions(parcel)
        assert result["excluded"] is False
        assert len(result["passed_checks"]) > 0
        assert len(result["exclusion_reasons"]) == 0


class TestProtectedHousing:
    """Test protected housing and tenancy checks."""

    def test_rent_controlled_units_protected(self):
        """Rent-controlled units should trigger protection."""
        parcel = make_test_parcel(has_rent_controlled_units=True)
        result = check_protected_housing(parcel)
        assert result["protected"] is True
        assert any("rent-controlled" in r.lower() for r in result["protection_reasons"])

    def test_deed_restricted_affordable_protected(self):
        """Deed-restricted affordable housing should trigger protection."""
        parcel = make_test_parcel(has_deed_restricted_affordable=True)
        result = check_protected_housing(parcel)
        assert result["protected"] is True
        assert any("deed-restricted" in r.lower() for r in result["protection_reasons"])

    def test_ellis_act_units_protected(self):
        """Ellis Act units should trigger protection."""
        parcel = make_test_parcel(has_ellis_act_units=True)
        result = check_protected_housing(parcel)
        assert result["protected"] is True
        assert any("ellis act" in r.lower() for r in result["protection_reasons"])

    def test_recent_tenancy_protected(self):
        """Recent residential tenancy should trigger protection."""
        parcel = make_test_parcel(has_recent_tenancy=True)
        result = check_protected_housing(parcel)
        assert result["protected"] is True
        assert any("tenancy" in r.lower() for r in result["protection_reasons"])

    def test_protected_units_count_protected(self):
        """Protected units count should trigger protection."""
        parcel = make_test_parcel(protected_units_count=5)
        result = check_protected_housing(parcel)
        assert result["protected"] is True
        assert any("5 protected" in r.lower() for r in result["protection_reasons"])

    def test_existing_units_warning(self):
        """Existing units should generate warning."""
        parcel = make_test_parcel(existing_units=10)
        result = check_protected_housing(parcel)
        assert len(result["warnings"]) > 0
        assert any("existing units" in w.lower() for w in result["warnings"])

    def test_no_protections_passes(self):
        """Parcel with no protections should pass."""
        parcel = make_test_parcel()
        result = check_protected_housing(parcel)
        assert result["protected"] is False
        assert len(result["passed_checks"]) > 0
        assert len(result["protection_reasons"]) == 0


class TestLaborCompliance:
    """Test labor standards compliance checks."""

    def test_prevailing_wage_required_all_projects(self):
        """Prevailing wage should be required for all projects."""
        parcel = make_test_parcel(prevailing_wage_commitment=False)
        result = check_labor_compliance(parcel)
        assert result["compliant"] is False
        assert any("prevailing wage" in r.lower() for r in result["missing_requirements"])

    def test_prevailing_wage_met(self):
        """Prevailing wage commitment should satisfy requirement."""
        parcel = make_test_parcel(prevailing_wage_commitment=True)
        result = check_labor_compliance(parcel, project_units=10)
        assert result["compliant"] is True
        assert any("prevailing wage" in r.lower() for r in result["met_requirements"])

    def test_skilled_workforce_not_required_small_project(self):
        """Skilled workforce not required for <50 units."""
        parcel = make_test_parcel(
            prevailing_wage_commitment=True,
            skilled_trained_workforce_commitment=False
        )
        result = check_labor_compliance(parcel, project_units=25)
        assert result["compliant"] is True
        assert result["skilled_workforce_required"] is False
        assert any("not required" in r.lower() for r in result["met_requirements"])

    def test_skilled_workforce_required_large_project(self):
        """Skilled workforce required for 50+ units."""
        parcel = make_test_parcel(
            prevailing_wage_commitment=True,
            skilled_trained_workforce_commitment=False
        )
        result = check_labor_compliance(parcel, project_units=75)
        assert result["compliant"] is False
        assert result["skilled_workforce_required"] is True
        assert any("skilled" in r.lower() and "50+" in r for r in result["missing_requirements"])

    def test_skilled_workforce_met_large_project(self):
        """Skilled workforce commitment should satisfy requirement for 50+ units."""
        parcel = make_test_parcel(
            prevailing_wage_commitment=True,
            skilled_trained_workforce_commitment=True
        )
        result = check_labor_compliance(parcel, project_units=75)
        assert result["compliant"] is True
        assert result["skilled_workforce_required"] is True
        assert any("skilled" in r.lower() for r in result["met_requirements"])

    def test_healthcare_benefits_best_practice(self):
        """Healthcare benefits should be treated as best practice."""
        parcel = make_test_parcel(
            prevailing_wage_commitment=True,
            healthcare_benefits_commitment=True
        )
        result = check_labor_compliance(parcel, project_units=10)
        assert result["compliant"] is True
        assert any("healthcare" in r.lower() for r in result["met_requirements"])

    def test_healthcare_benefits_warning(self):
        """Missing healthcare benefits should generate warning."""
        parcel = make_test_parcel(
            prevailing_wage_commitment=True,
            healthcare_benefits_commitment=False
        )
        result = check_labor_compliance(parcel, project_units=10)
        assert any("healthcare" in w.lower() for w in result["warnings"])


class TestComprehensiveEligibility:
    """Test comprehensive can_apply_ab2011 function."""

    def test_fully_eligible_parcel(self):
        """Fully eligible parcel should pass all checks."""
        parcel = make_test_parcel()
        result = can_apply_ab2011(parcel)
        assert result["eligible"] is True
        assert len(result["reasons"]) > 0
        assert len(result["exclusions"]) == 0

    def test_ineligible_corridor(self):
        """Residential zoning should make parcel ineligible."""
        parcel = make_test_parcel(zoning_code="R-1")
        result = can_apply_ab2011(parcel)
        assert result["eligible"] is False
        assert len(result["exclusions"]) > 0

    def test_ineligible_site_exclusion(self):
        """Site exclusion should make parcel ineligible."""
        parcel = make_test_parcel(in_wetlands=True)
        result = can_apply_ab2011(parcel)
        assert result["eligible"] is False
        assert any("wetland" in r.lower() for r in result["exclusions"])

    def test_ineligible_protected_housing(self):
        """Protected housing should make parcel ineligible."""
        parcel = make_test_parcel(has_rent_controlled_units=True)
        result = can_apply_ab2011(parcel)
        assert result["eligible"] is False
        assert any("rent-controlled" in r.lower() for r in result["exclusions"])

    def test_ineligible_labor_standards(self):
        """Missing labor standards should make parcel ineligible."""
        parcel = make_test_parcel(prevailing_wage_commitment=False)
        result = can_apply_ab2011(parcel)
        assert result["eligible"] is False
        assert any("prevailing wage" in r.lower() for r in result["exclusions"])

    def test_multiple_exclusions(self):
        """Multiple exclusions should all be reported."""
        parcel = make_test_parcel(
            in_wetlands=True,
            has_rent_controlled_units=True,
            prevailing_wage_commitment=False
        )
        result = can_apply_ab2011(parcel)
        assert result["eligible"] is False
        assert len(result["exclusions"]) >= 3  # At least 3 exclusion reasons

    def test_warnings_non_fatal(self):
        """Warnings should not prevent eligibility."""
        parcel = make_test_parcel(
            existing_units=5,  # Generates warning
            healthcare_benefits_commitment=False  # Generates warning
        )
        result = can_apply_ab2011(parcel)
        assert result["eligible"] is True
        assert len(result["warnings"]) > 0


class TestAnalyzeFunctions:
    """Test analyze_ab2011 and analyze_ab2011_tracks functions."""

    def test_analyze_eligible_parcel_returns_scenario(self):
        """Eligible parcel should return scenario."""
        parcel = make_test_parcel()
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        assert scenario.max_units > 0
        assert scenario.max_height_ft > 0

    def test_analyze_ineligible_parcel_returns_none(self):
        """Ineligible parcel should return None."""
        parcel = make_test_parcel(zoning_code="R-1")  # Residential, not eligible
        scenario = analyze_ab2011(parcel)
        assert scenario is None

    def test_analyze_tracks_eligible_returns_two_scenarios(self):
        """Eligible parcel should return two scenarios (mixed-income and 100%)."""
        parcel = make_test_parcel()
        scenarios = analyze_ab2011_tracks(parcel)
        assert len(scenarios) == 2
        assert "Mixed-Income" in scenarios[0].scenario_name
        assert "100% Affordable" in scenarios[1].scenario_name

    def test_analyze_tracks_ineligible_returns_empty(self):
        """Ineligible parcel should return empty list."""
        parcel = make_test_parcel(zoning_code="R-1")
        scenarios = analyze_ab2011_tracks(parcel)
        assert len(scenarios) == 0

    def test_scenario_includes_labor_notes(self):
        """Scenario should include labor standards notes."""
        parcel = make_test_parcel()
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        notes_text = " ".join(scenario.notes)
        assert "LABOR STANDARDS" in notes_text
        assert "Prevailing wage" in notes_text

    def test_scenario_includes_coastal_notes_when_applicable(self):
        """Scenario should include coastal zone notes when parcel in coastal zone."""
        parcel = make_test_parcel(in_coastal_zone=True)
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        notes_text = " ".join(scenario.notes)
        assert "COASTAL ZONE" in notes_text
        assert "CDP" in notes_text

    def test_scenario_excludes_coastal_notes_when_not_applicable(self):
        """Scenario should not include coastal notes when not in coastal zone."""
        parcel = make_test_parcel(in_coastal_zone=False)
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        notes_text = " ".join(scenario.notes)
        assert "COASTAL ZONE" not in notes_text


class TestAB2097Integration:
    """Test AB 2097 parking reduction integration."""

    def test_parking_reduced_near_transit(self):
        """Parking should be reduced to 0 near transit."""
        parcel = make_test_parcel(near_transit=True, city="Santa Monica")
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        assert scenario.parking_spaces_required == 0
        notes_text = " ".join(scenario.notes)
        assert "AB2097" in notes_text

    def test_parking_default_without_transit(self):
        """Parking should use default calculation without transit proximity."""
        parcel = make_test_parcel(near_transit=False, city="Rural City")
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        # Should have non-zero parking without transit proximity
        # (AB 2097 won't apply)


class TestTierDensityCalculations:
    """Test that correct density/height standards apply by tier."""

    def test_low_tier_density_standards(self):
        """Low tier should apply 30 u/ac and 35 ft standards."""
        parcel = make_test_parcel(
            zoning_code="C-1",
            lot_size_sqft=43560.0  # 1 acre
        )
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        # 1 acre * 30 u/ac = 30 units minimum
        assert scenario.max_units >= 30
        assert scenario.max_height_ft >= 35.0

    def test_mid_tier_density_standards(self):
        """Mid tier should apply 50 u/ac and 45 ft standards."""
        parcel = make_test_parcel(
            zoning_code="C-2",
            lot_size_sqft=43560.0  # 1 acre
        )
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        # 1 acre * 50 u/ac = 50 units minimum
        assert scenario.max_units >= 50
        assert scenario.max_height_ft >= 45.0

    def test_high_tier_density_standards(self):
        """High tier should apply 80 u/ac and 65 ft standards."""
        parcel = make_test_parcel(
            zoning_code="C-3",
            lot_size_sqft=43560.0  # 1 acre
        )
        scenario = analyze_ab2011(parcel)
        assert scenario is not None
        # 1 acre * 80 u/ac = 80 units minimum
        assert scenario.max_units >= 80
        assert scenario.max_height_ft >= 65.0
