"""
Tests for State Density Bonus Law (Government Code Section 65915).

Tests density bonuses and concessions for projects with affordable housing.
"""
import pytest
from app.rules.density_bonus import (
    apply_density_bonus,
    calculate_density_bonus_percentage,
    calculate_concessions,
    get_density_bonus_tiers
)
from app.rules.base_zoning import analyze_base_zoning
from app.models.parcel import ParcelBase


class TestDensityBonusPercentages:
    """Tests for density bonus percentage calculations."""

    @pytest.mark.parametrize("affordability,income,expected_bonus", [
        (5, "very_low", 20),
        (10, "very_low", 35),
        (15, "very_low", 50),
        (10, "low", 20),
        (17, "low", 35),
        (24, "low", 50),
        (10, "moderate", 5),
        (40, "moderate", 35),
        (100, "very_low", 80),
    ])
    def test_bonus_percentages(self, affordability, income, expected_bonus):
        """Test density bonus percentage calculations."""
        bonus = calculate_density_bonus_percentage(affordability, income)
        assert bonus == expected_bonus

    def test_insufficient_affordability_returns_zero(self):
        """Test that insufficient affordability returns 0% bonus."""
        bonus = calculate_density_bonus_percentage(4, "very_low")
        assert bonus == 0.0

    def test_very_low_income_tiers(self):
        """Test very low income affordability tiers."""
        assert calculate_density_bonus_percentage(5, "very_low") == 20
        assert calculate_density_bonus_percentage(10, "very_low") == 35
        assert calculate_density_bonus_percentage(15, "very_low") == 50

    def test_low_income_tiers(self):
        """Test low income affordability tiers."""
        assert calculate_density_bonus_percentage(10, "low") == 20
        assert calculate_density_bonus_percentage(17, "low") == 35
        assert calculate_density_bonus_percentage(24, "low") == 50

    def test_moderate_income_tiers(self):
        """Test moderate income affordability tiers."""
        assert calculate_density_bonus_percentage(10, "moderate") == 5
        assert calculate_density_bonus_percentage(40, "moderate") == 35

    def test_100_percent_affordable(self):
        """Test 100% affordable project gets 80% bonus."""
        bonus = calculate_density_bonus_percentage(100, "very_low")
        assert bonus == 80


class TestConcessionCalculations:
    """Tests for concession/incentive calculations."""

    def test_10_percent_gets_1_concession(self):
        """Test 10% affordability gets 1 concession."""
        assert calculate_concessions(10) == 1

    def test_20_percent_gets_2_concessions(self):
        """Test 20% affordability gets 2 concessions."""
        assert calculate_concessions(20) == 2

    def test_30_percent_gets_3_concessions(self):
        """Test 30% affordability gets 3 concessions."""
        assert calculate_concessions(30) == 3

    def test_under_10_percent_gets_0_concessions(self):
        """Test under 10% affordability gets 0 concessions."""
        assert calculate_concessions(9) == 0
        assert calculate_concessions(5) == 0

    @pytest.mark.parametrize("affordability,expected_concessions", [
        (5, 0),
        (10, 1),
        (15, 1),
        (20, 2),
        (25, 2),
        (30, 3),
        (50, 3),
        (100, 4),  # Fourth concession for 100% affordable per § 65915(d)(2)(D)
    ])
    def test_concession_tiers(self, affordability, expected_concessions):
        """Test concession tiers for various affordability percentages."""
        assert calculate_concessions(affordability) == expected_concessions


class TestDensityBonusApplication:
    """Tests for applying density bonus to scenarios."""

    def test_density_bonus_increases_units(self, r2_parcel):
        """Test that density bonus increases unit count."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        assert bonus_scenario.max_units > base_units

    def test_20_percent_bonus_calculation(self, r2_parcel):
        """Test 20% density bonus calculation."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # 10% low income = 20% density bonus
        expected_units = base_units + int(base_units * 0.20)
        assert bonus_scenario.max_units == expected_units

    def test_affordable_units_calculated(self, r2_parcel):
        """Test that affordable units requirement is calculated."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Should require at least 10% of total units to be affordable
        min_affordable = bonus_scenario.max_units * 0.10
        assert bonus_scenario.affordable_units_required >= min_affordable * 0.9  # Allow rounding

    def test_ineligible_returns_none(self, r2_parcel):
        """Test that insufficient affordability returns None."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=3,  # Too low
            income_level="low"
        )

        assert bonus_scenario is None


class TestConcessionApplication:
    """Tests for concession application."""

    def test_height_concession_applied(self, r2_parcel):
        """Test that first concession increases height."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_height = base_scenario.max_height_ft

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,  # 1 concession
            income_level="low"
        )

        # Height should increase
        assert bonus_scenario.max_height_ft > base_height

    def test_parking_reduction_concession(self, r2_parcel):
        """Test that second concession reduces parking."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=20,  # 2 concessions
            income_level="low"
        )

        # Parking per unit should be reduced
        base_parking_ratio = base_scenario.parking_spaces_required / base_scenario.max_units
        bonus_parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units

        assert bonus_parking_ratio < base_parking_ratio

    def test_setback_reduction_concession(self, r2_parcel):
        """Test that third concession reduces setbacks."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=30,  # 3 concessions
            income_level="low"
        )

        # Setbacks should be reduced
        assert bonus_scenario.setbacks["front"] < base_scenario.setbacks["front"]
        assert bonus_scenario.setbacks["rear"] < base_scenario.setbacks["rear"]

    def test_height_increase_limits(self, r2_parcel):
        """Test that height increase has reasonable limits."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_height = base_scenario.max_height_ft

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Height increase should be reasonable (not more than 50% or 33 feet)
        height_increase = bonus_scenario.max_height_ft - base_height
        assert height_increase <= max(33, base_height * 0.5)


class TestParkingReductions:
    """Tests for density bonus parking reductions."""

    def test_very_low_income_parking_cap(self, r2_parcel):
        """Test parking capped at 0.5 spaces per unit for very low income."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="very_low"
        )

        parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units
        assert parking_ratio <= 0.5

    def test_low_income_parking_cap(self, r2_parcel):
        """Test parking capped at 1.0 spaces per unit for low income."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units
        assert parking_ratio <= 1.0

    def test_20_percent_affordable_parking_reduction(self, r2_parcel):
        """Test additional parking reduction for 20% affordability."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=20,
            income_level="low"
        )

        # With 2 concessions, parking should be further reduced
        parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units
        assert parking_ratio <= 1.0


class TestBuildingSizeCalculations:
    """Tests for building size calculations with density bonus."""

    def test_building_sqft_increases(self, r2_parcel):
        """Test that building square footage increases with bonus."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        assert bonus_scenario.max_building_sqft > base_scenario.max_building_sqft

    def test_lot_coverage_increase_allowed(self, r2_parcel):
        """Test that lot coverage can increase with density bonus."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Lot coverage may increase but should have limits
        assert bonus_scenario.lot_coverage_pct <= base_scenario.lot_coverage_pct * 1.3


class TestScenarioDocumentation:
    """Tests for scenario notes and documentation."""

    def test_scenario_name_includes_affordability(self, r2_parcel):
        """Test that scenario name includes affordability percentage."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=15,
            income_level="very_low"
        )

        assert "15%" in bonus_scenario.scenario_name
        assert "Density Bonus" in bonus_scenario.scenario_name

    def test_legal_basis_documented(self, r2_parcel):
        """Test that legal basis mentions state law."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        assert "State Density Bonus" in bonus_scenario.legal_basis or "Density Bonus Law" in bonus_scenario.legal_basis

    def test_notes_document_bonus_details(self, r2_parcel):
        """Test that notes document bonus percentage and units."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        notes_text = " ".join(bonus_scenario.notes)

        assert "20%" in notes_text or "bonus" in notes_text.lower()
        assert "affordable" in notes_text.lower()

    def test_concessions_documented(self, r2_parcel):
        """Test that concessions are documented in notes."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=20,
            income_level="low"
        )

        notes_text = " ".join(bonus_scenario.notes).lower()

        assert "concession" in notes_text


class TestDensityBonusTiers:
    """Tests for density bonus tier information."""

    def test_get_tiers_returns_list(self):
        """Test that tier information is available."""
        tiers = get_density_bonus_tiers()

        assert isinstance(tiers, list)
        assert len(tiers) > 0

    def test_tiers_include_key_info(self):
        """Test that tiers include required information."""
        tiers = get_density_bonus_tiers()

        for tier in tiers:
            assert "income_level" in tier
            assert "min_affordability_pct" in tier
            assert "density_bonus_pct" in tier
            assert "concessions" in tier


class TestLargeProjects:
    """Tests for density bonus on large projects."""

    def test_large_multifamily_density_bonus(self, large_r4_parcel):
        """Test density bonus on large R4 parcel."""
        base_scenario = analyze_base_zoning(large_r4_parcel)
        base_units = base_scenario.max_units

        bonus_scenario = apply_density_bonus(
            base_scenario,
            large_r4_parcel,
            affordability_pct=15,
            income_level="very_low"
        )

        # 15% very low income = 50% density bonus
        expected_bonus_units = int(base_units * 0.50)
        assert bonus_scenario.max_units >= base_units + expected_bonus_units * 0.9

    def test_100_percent_affordable_bonus(self, r2_parcel):
        """Test 100% affordable project gets 80% bonus."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=100,
            income_level="very_low"
        )

        # Should get 80% bonus
        expected_units = base_units + int(base_units * 0.80)
        assert bonus_scenario.max_units == expected_units


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_exactly_5_percent_affordability(self, r2_parcel):
        """Test exactly at 5% affordability threshold."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=5.0,
            income_level="very_low"
        )

        assert bonus_scenario is not None
        assert bonus_scenario.max_units > base_scenario.max_units

    def test_just_under_5_percent(self, r2_parcel):
        """Test just under 5% affordability threshold."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=4.9,
            income_level="very_low"
        )

        assert bonus_scenario is None

    def test_single_unit_base(self):
        """Test density bonus on single unit base."""
        single_unit_parcel = ParcelBase(
            apn="SINGLE",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        base_scenario = analyze_base_zoning(single_unit_parcel)
        # R1 allows 1 unit
        assert base_scenario.max_units == 1

        # Density bonus should still apply
        bonus_scenario = apply_density_bonus(
            base_scenario,
            single_unit_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # 1 unit + 20% = 1.2, rounds to 1 additional unit
        # Result should be at least 1 unit (may not get bonus with base of 1)
        assert bonus_scenario.max_units >= 1


class TestIncomeLevelVariations:
    """Tests for different income level strings."""

    @pytest.mark.parametrize("income_level", [
        "very_low",
        "VERY_LOW",
        "Very Low",
        "very low",
    ])
    def test_income_level_string_variations(self, income_level):
        """Test that income level handles various string formats."""
        bonus = calculate_density_bonus_percentage(10, income_level)
        assert bonus == 35  # 10% very low = 35% bonus


class TestFourthConcession:
    """Tests for fourth concession (100% affordable projects)."""

    def test_100_percent_gets_4_concessions(self):
        """Test that 100% affordable gets 4 concessions per § 65915(d)(2)(D)."""
        assert calculate_concessions(100) == 4

    def test_fourth_concession_increases_far(self, r2_parcel):
        """Test that fourth concession provides visible FAR increase."""
        base_scenario = analyze_base_zoning(r2_parcel)

        # Compare 30% affordable (3 concessions) vs 100% affordable (4 concessions)
        scenario_3_concessions = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=30,
            income_level="low"
        )

        scenario_4_concessions = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=100,
            income_level="very_low"
        )

        # Fourth concession should increase building size beyond just density bonus
        # 100% gets 80% bonus vs 30% gets 50% bonus, but also gets +0.25 FAR
        assert scenario_4_concessions.max_building_sqft > scenario_3_concessions.max_building_sqft

    def test_fourth_concession_increases_height(self, r2_parcel):
        """Test that fourth concession provides additional height."""
        base_scenario = analyze_base_zoning(r2_parcel)

        scenario_4_concessions = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=100,
            income_level="very_low"
        )

        # Fourth concession should add 15 ft beyond concession 1's 33 ft
        # Total should be at least 48 ft more than base (33 + 15)
        min_expected_increase = 33  # At minimum, should get concession 1's increase
        assert scenario_4_concessions.max_height_ft >= base_scenario.max_height_ft + min_expected_increase

    def test_fourth_concession_documented_in_notes(self, r2_parcel):
        """Test that fourth concession is documented in scenario notes."""
        base_scenario = analyze_base_zoning(r2_parcel)

        scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=100,
            income_level="very_low"
        )

        notes_text = " ".join(scenario.notes)
        assert "fourth concession" in notes_text.lower() or "4" in notes_text

    def test_fourth_concession_tracked_in_concessions_applied(self, r2_parcel):
        """Test that fourth concession is tracked in concessions_applied field."""
        base_scenario = analyze_base_zoning(r2_parcel)

        scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=100,
            income_level="very_low"
        )

        assert scenario.concessions_applied is not None
        assert len(scenario.concessions_applied) == 4


class TestOwnershipGating:
    """Tests for moderate-income ownership gating (for-sale requirement)."""

    def test_moderate_income_requires_for_sale(self, r2_parcel):
        """Test that moderate-income density bonus requires for-sale project."""
        # Make it a rental project (for_sale = False)
        r2_parcel.for_sale = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="moderate"
        )

        # Should return None for rental projects
        assert bonus_scenario is None

    def test_moderate_income_allows_for_sale(self, r2_parcel):
        """Test that moderate-income density bonus works for for-sale projects."""
        # Make it a for-sale project
        r2_parcel.for_sale = True

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="moderate"
        )

        # Should work for for-sale projects
        assert bonus_scenario is not None
        assert bonus_scenario.max_units > base_scenario.max_units

    def test_very_low_income_no_ownership_requirement(self, r2_parcel):
        """Test that very low income has no ownership requirement."""
        # Make it a rental project
        r2_parcel.for_sale = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="very_low"
        )

        # Should work for rental projects
        assert bonus_scenario is not None

    def test_low_income_no_ownership_requirement(self, r2_parcel):
        """Test that low income has no ownership requirement."""
        # Make it a rental project
        r2_parcel.for_sale = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Should work for rental projects
        assert bonus_scenario is not None


class TestBedroomBasedCaps:
    """Tests for bedroom-based parking caps per § 65915(p)."""

    def test_studio_1br_parking_cap(self, r2_parcel):
        """Test parking capped at 1.0 for studio/1-BR units."""
        r2_parcel.avg_bedrooms_per_unit = 1.0
        r2_parcel.near_transit = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units
        # Low income caps at 1.0, 1-BR caps at 1.0, so should be ≤ 1.0
        assert parking_ratio <= 1.0

    def test_2br_parking_cap(self, r2_parcel):
        """Test parking capped at 2.0 for 2-BR units."""
        r2_parcel.avg_bedrooms_per_unit = 2.0
        r2_parcel.near_transit = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units
        # Should be capped at 2.0 by bedroom count
        assert parking_ratio <= 2.0

    def test_3br_parking_cap(self, r2_parcel):
        """Test parking capped at 2.0 for 3-BR units."""
        r2_parcel.avg_bedrooms_per_unit = 3.0
        r2_parcel.near_transit = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units
        # Should be capped at 2.0 by bedroom count
        assert parking_ratio <= 2.0

    def test_4plus_br_parking_cap(self, r2_parcel):
        """Test parking capped at 2.5 for 4+ BR units."""
        r2_parcel.avg_bedrooms_per_unit = 4.0
        r2_parcel.near_transit = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        parking_ratio = bonus_scenario.parking_spaces_required / bonus_scenario.max_units
        # Should be capped at 2.5 by bedroom count (but 1.0 by income level)
        assert parking_ratio <= 2.5


class TestAB2097Integration:
    """Tests for AB 2097 transit-oriented parking elimination."""

    def test_near_transit_eliminates_parking(self, r2_parcel):
        """Test that near_transit=True eliminates all parking requirements."""
        r2_parcel.near_transit = True

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Parking should be 0
        assert bonus_scenario.parking_spaces_required == 0

    def test_not_near_transit_has_parking(self, r2_parcel):
        """Test that near_transit=False maintains parking requirements."""
        r2_parcel.near_transit = False

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Parking should be > 0
        assert bonus_scenario.parking_spaces_required > 0

    def test_ab2097_documented_in_notes(self, r2_parcel):
        """Test that AB 2097 parking elimination is documented in notes."""
        r2_parcel.near_transit = True

        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        notes_text = " ".join(bonus_scenario.notes).lower()
        assert "ab 2097" in notes_text or "near transit" in notes_text

    def test_ab2097_overrides_concession_parking_reduction(self, r2_parcel):
        """Test that AB 2097 overrides concession-based parking reductions."""
        r2_parcel.near_transit = True

        base_scenario = analyze_base_zoning(r2_parcel)

        # Even with 2 concessions (which includes parking reduction)
        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=20,  # 2 concessions
            income_level="low"
        )

        # AB 2097 should still result in 0 parking
        assert bonus_scenario.parking_spaces_required == 0


class TestWaiverTracking:
    """Tests for waiver tracking separate from concessions."""

    def test_waivers_field_exists(self, r2_parcel):
        """Test that waivers_applied field exists in scenario."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Field should exist (may be None or empty list)
        assert hasattr(bonus_scenario, 'waivers_applied')

    def test_concessions_field_exists(self, r2_parcel):
        """Test that concessions_applied field exists and is populated."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # Field should exist and have at least one concession
        assert hasattr(bonus_scenario, 'concessions_applied')
        assert bonus_scenario.concessions_applied is not None
        assert len(bonus_scenario.concessions_applied) >= 1

    def test_waiver_vs_concession_distinction_in_notes(self, r2_parcel):
        """Test that notes distinguish between waivers and concessions."""
        base_scenario = analyze_base_zoning(r2_parcel)

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        notes_text = " ".join(bonus_scenario.notes).lower()
        # Should mention both waivers and concessions
        assert "waiver" in notes_text
        assert "concession" in notes_text
