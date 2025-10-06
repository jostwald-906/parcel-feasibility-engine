"""
AB2011 (2022) corridor housing tests.

Scope: validate eligibility on commercial/office/mixed zoning and application
of state floors for density and height via the analysis function.
"""
from app.rules.ab2011 import (
    analyze_ab2011,
    analyze_ab2011_tracks,
    is_ab2011_eligible,
)
from app.models.parcel import ParcelBase


class TestAB2011Eligibility:
    def test_commercial_parcel_is_eligible(self, commercial_parcel):
        assert is_ab2011_eligible(commercial_parcel) is True

    def test_residential_parcel_not_eligible(self, r2_parcel):
        assert is_ab2011_eligible(r2_parcel) is False


class TestCorridorFloors:
    def test_low_tier_c1_one_acre(self):
        p = ParcelBase(
            apn="AB2011-C1-1AC",
            address="",
            city="",
            county="",
            zip_code="",
            lot_size_sqft=43560.0,
            zoning_code="C-1",
            existing_units=0,
            existing_building_sqft=0,
        )
        scenario = analyze_ab2011(p)
        assert scenario is not None
        assert scenario.max_units == 30  # 30 u/ac floor
        assert scenario.max_height_ft == 35  # 35 ft floor

    def test_mid_tier_c2_one_acre(self):
        p = ParcelBase(
            apn="AB2011-C2-1AC",
            address="",
            city="",
            county="",
            zip_code="",
            lot_size_sqft=43560.0,
            zoning_code="C-2",
            existing_units=0,
            existing_building_sqft=0,
        )
        scenario = analyze_ab2011(p)
        assert scenario is not None
        assert scenario.max_units == 50  # 50 u/ac floor
        assert scenario.max_height_ft == 45  # 45 ft floor

    def test_high_tier_c3_one_acre(self):
        p = ParcelBase(
            apn="AB2011-C3-1AC",
            address="",
            city="",
            county="",
            zip_code="",
            lot_size_sqft=43560.0,
            zoning_code="C-3",
            existing_units=0,
            existing_building_sqft=0,
        )
        scenario = analyze_ab2011(p)
        assert scenario is not None
        assert scenario.max_units == 80  # 80 u/ac floor
        assert scenario.max_height_ft == 65  # 65 ft floor


class TestScenarioBasics:
    def test_scenario_fields_and_notes(self):
        p = ParcelBase(
            apn="AB2011-BASIC",
            address="",
            city="",
            county="",
            zip_code="",
            lot_size_sqft=20000.0,
            zoning_code="OFFICE",
            existing_units=0,
            existing_building_sqft=0,
        )
        s = analyze_ab2011(p)
        assert s is not None
        assert "AB2011" in s.scenario_name or "AB2011" in s.legal_basis
        assert s.max_units >= 2
        assert s.max_height_ft >= 35
        assert 0 < s.lot_coverage_pct <= 100
        notes_text = " ".join(s.notes).lower()
        assert "ministerial" in notes_text


class TestTracks:
    def test_returns_both_tracks_and_affordability(self):
        p = ParcelBase(
            apn="AB2011-TRACKS",
            address="",
            city="",
            county="",
            zip_code="",
            lot_size_sqft=43560.0,
            zoning_code="C-2",
            existing_units=0,
            existing_building_sqft=0,
        )
        scenarios = analyze_ab2011_tracks(p)
        names = [s.scenario_name for s in scenarios]
        assert any("Mixed-Income" in n for n in names)
        assert any("100% Affordable" in n for n in names)

        # Identify scenarios
        mixed = next(s for s in scenarios if "Mixed-Income" in s.scenario_name)
        full = next(s for s in scenarios if "100% Affordable" in s.scenario_name)

        # 100% track: all units affordable
        assert full.affordable_units_required == full.max_units
        # Mixed track: about 15% affordable
        assert 0 < mixed.affordable_units_required < mixed.max_units
