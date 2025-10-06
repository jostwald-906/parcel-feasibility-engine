"""
Tests for tiered development standards (FAR and height resolution).

This module tests the tier-aware FAR and height resolution logic that handles:
- Base zoning standards
- Downtown Community Plan (DCP) tier multipliers (Tier 1/2/3)
- Bergamot Area Plan district-specific standards
- Affordable Housing Overlay (AHO) bonuses
- Combined overlay scenarios
"""
import pytest
from app.rules.tiered_standards import (
    get_base_far,
    get_base_height,
    compute_max_far,
    compute_max_height,
    get_tier_info,
    DCP_TIER_FAR_MULTIPLIER,
    DCP_TIER_HEIGHT_BONUS,
    BERGAMOT_FAR,
    BERGAMOT_HEIGHT,
    AHO_FAR_BONUS,
    AHO_HEIGHT_BONUS,
    BASE_ZONE_FAR,
    BASE_ZONE_HEIGHT,
)
from app.models.parcel import ParcelBase


class TestBaseFAR:
    """Tests for base FAR lookup by zoning code."""

    @pytest.mark.parametrize("zoning_code,expected_far", [
        ("R1", 0.5),
        ("R2", 0.75),
        ("R3", 1.5),
        ("R4", 2.5),
        ("NV", 1.0),
        ("WT", 1.75),
        ("MUBL", 1.5),
        ("MUBM", 2.0),
        ("MUBH", 3.0),
        ("MUB", 2.0),
        ("MUCR", 2.0),
        ("C1", 2.0),
        ("C2", 2.0),
        ("C3", 2.0),
        ("OC", 2.0),
        ("OP", 1.5),
        ("I", 1.5),
    ])
    def test_base_far_exact_match(self, zoning_code, expected_far):
        """Test exact match for standard zoning codes."""
        assert get_base_far(zoning_code) == expected_far

    def test_base_far_case_insensitive(self):
        """Test that zone codes are case-insensitive."""
        assert get_base_far("r2") == 0.75
        assert get_base_far("R2") == 0.75
        assert get_base_far("r2") == get_base_far("R2")

    @pytest.mark.parametrize("zoning_code,expected_far", [
        ("R2A", 0.75),  # R2 with suffix
        ("R3-HD", 1.5),  # R3 with suffix
        ("MUBL-1", 1.5),  # MUBL with suffix
    ])
    def test_base_far_partial_match(self, zoning_code, expected_far):
        """Test partial match for codes with suffixes."""
        assert get_base_far(zoning_code) == expected_far

    def test_base_far_unknown_defaults(self):
        """Test that unknown zoning codes return default FAR."""
        assert get_base_far("UNKNOWN") == 1.0
        assert get_base_far("XYZ-123") == 1.0


class TestBaseHeight:
    """Tests for base height lookup by zoning code."""

    @pytest.mark.parametrize("zoning_code,expected_height", [
        ("R1", 35.0),
        ("R2", 40.0),
        ("R3", 55.0),
        ("R4", 75.0),
        ("NV", 35.0),
        ("WT", 50.0),
        ("MUBL", 45.0),
        ("MUBM", 55.0),
        ("MUBH", 84.0),
        ("MUB", 65.0),
        ("MUCR", 65.0),
        ("C1", 65.0),
        ("C2", 65.0),
        ("C3", 65.0),
        ("OC", 65.0),
        ("OP", 55.0),
        ("I", 45.0),
    ])
    def test_base_height_exact_match(self, zoning_code, expected_height):
        """Test exact match for standard zoning codes."""
        assert get_base_height(zoning_code) == expected_height

    def test_base_height_case_insensitive(self):
        """Test that zone codes are case-insensitive."""
        assert get_base_height("r3") == 55.0
        assert get_base_height("R3") == 55.0

    @pytest.mark.parametrize("zoning_code,expected_height", [
        ("R2A", 40.0),
        ("R4-HD", 75.0),
        ("MUBH-2", 84.0),
    ])
    def test_base_height_partial_match(self, zoning_code, expected_height):
        """Test partial match for codes with suffixes."""
        assert get_base_height(zoning_code) == expected_height

    def test_base_height_unknown_defaults(self):
        """Test that unknown zoning codes return default height."""
        assert get_base_height("UNKNOWN") == 35.0
        assert get_base_height("XYZ-123") == 35.0


class TestComputeMaxFARBaseZone:
    """Tests for FAR computation with base zoning (no overlays)."""

    def test_r1_base_far(self):
        """Test R1 base FAR with no overlays."""
        parcel = ParcelBase(
            apn="TEST-001",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=6000.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0,
        )

        far, source = compute_max_far(parcel)

        assert far == 0.5
        assert "Base zoning (R1)" in source

    def test_r4_base_far(self):
        """Test R4 base FAR with no overlays."""
        parcel = ParcelBase(
            apn="TEST-002",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=10000.0,
            zoning_code="R4",
            existing_units=0,
            existing_building_sqft=0,
        )

        far, source = compute_max_far(parcel)

        assert far == 2.5
        assert "Base zoning (R4)" in source

    def test_mubh_base_far(self):
        """Test MUBH (Mixed-Use Boulevard High) base FAR."""
        parcel = ParcelBase(
            apn="TEST-003",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=8000.0,
            zoning_code="MUBH",
            existing_units=0,
            existing_building_sqft=0,
        )

        far, source = compute_max_far(parcel)

        assert far == 3.0
        assert "Base zoning (MUBH)" in source


class TestComputeMaxHeightBaseZone:
    """Tests for height computation with base zoning (no overlays)."""

    def test_r1_base_height(self):
        """Test R1 base height with no overlays."""
        parcel = ParcelBase(
            apn="TEST-004",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=6000.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0,
        )

        height, source = compute_max_height(parcel)

        assert height == 35.0
        assert "Base zoning (R1)" in source

    def test_mubh_base_height(self):
        """Test MUBH base height."""
        parcel = ParcelBase(
            apn="TEST-005",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=8000.0,
            zoning_code="MUBH",
            existing_units=0,
            existing_building_sqft=0,
        )

        height, source = compute_max_height(parcel)

        assert height == 84.0
        assert "Base zoning (MUBH)" in source


class TestDCPTierFAR:
    """Tests for Downtown Community Plan (DCP) tier FAR multipliers."""

    def test_dcp_tier_1_far(self):
        """Test DCP Tier 1 FAR (base tier, 1.0x multiplier)."""
        parcel = ParcelBase(
            apn="DCP-T1",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="1",
            overlay_codes=["DCP"],
        )

        far, source = compute_max_far(parcel)

        # MUBM base = 2.0, Tier 1 multiplier = 1.0
        assert far == 2.0
        assert "DCP Tier 1" in source

    def test_dcp_tier_2_far(self):
        """Test DCP Tier 2 FAR (1.25x multiplier)."""
        parcel = ParcelBase(
            apn="DCP-T2",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="2",
            overlay_codes=["DCP"],
        )

        far, source = compute_max_far(parcel)

        # MUBM base = 2.0, Tier 2 multiplier = 1.25
        assert far == 2.5
        assert "DCP Tier 2" in source

    def test_dcp_tier_3_far(self):
        """Test DCP Tier 3 FAR (1.5x multiplier)."""
        parcel = ParcelBase(
            apn="DCP-T3",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="3",
            overlay_codes=["DCP"],
        )

        far, source = compute_max_far(parcel)

        # MUBM base = 2.0, Tier 3 multiplier = 1.5
        assert far == 3.0
        assert "DCP Tier 3" in source

    def test_dcp_overlay_without_tier(self):
        """Test DCP overlay without tier specified falls back to base."""
        parcel = ParcelBase(
            apn="DCP-NO-TIER",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier=None,  # No tier
            overlay_codes=["DCP"],
        )

        far, source = compute_max_far(parcel)

        # Should fall back to base zoning
        assert far == 2.0
        assert "Base zoning" in source


class TestDCPTierHeight:
    """Tests for Downtown Community Plan (DCP) tier height bonuses."""

    def test_dcp_tier_1_height(self):
        """Test DCP Tier 1 height (no bonus)."""
        parcel = ParcelBase(
            apn="DCP-T1-H",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="1",
            overlay_codes=["DCP"],
        )

        height, source = compute_max_height(parcel)

        # MUBM base = 55.0, Tier 1 bonus = 0
        assert height == 55.0
        assert "DCP Tier 1" in source

    def test_dcp_tier_2_height(self):
        """Test DCP Tier 2 height (+10 ft bonus)."""
        parcel = ParcelBase(
            apn="DCP-T2-H",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="2",
            overlay_codes=["DCP"],
        )

        height, source = compute_max_height(parcel)

        # MUBM base = 55.0, Tier 2 bonus = +10
        assert height == 65.0
        assert "DCP Tier 2" in source

    def test_dcp_tier_3_height(self):
        """Test DCP Tier 3 height (+20 ft bonus)."""
        parcel = ParcelBase(
            apn="DCP-T3-H",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="3",
            overlay_codes=["DCP"],
        )

        height, source = compute_max_height(parcel)

        # MUBM base = 55.0, Tier 3 bonus = +20
        assert height == 75.0
        assert "DCP Tier 3" in source


class TestBergamotOverlay:
    """Tests for Bergamot Area Plan overlay standards."""

    def test_bergamot_default_far(self):
        """Test Bergamot overlay uses default FAR (2.0)."""
        parcel = ParcelBase(
            apn="BERG-01",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUB",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["Bergamot"],
        )

        far, source = compute_max_far(parcel)

        # Bergamot default = 2.0 (regardless of base zoning)
        assert far == 2.0
        assert "Bergamot" in source

    def test_bergamot_default_height(self):
        """Test Bergamot overlay uses default height (65 ft)."""
        parcel = ParcelBase(
            apn="BERG-02",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUB",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["Bergamot"],
        )

        height, source = compute_max_height(parcel)

        # Bergamot default = 65.0 ft
        assert height == 65.0
        assert "Bergamot" in source

    def test_bergamot_overrides_base_zoning(self):
        """Test that Bergamot overlay overrides base zoning standards."""
        parcel = ParcelBase(
            apn="BERG-03",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="R2",  # Base FAR = 0.75
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["Bergamot"],
        )

        far, source = compute_max_far(parcel)

        # Bergamot overrides R2 base (0.75) with 2.0
        assert far == 2.0
        assert "Bergamot" in source


class TestAHOBonus:
    """Tests for Affordable Housing Overlay (AHO) bonuses."""

    def test_aho_far_bonus_alone(self):
        """Test AHO FAR bonus without other overlays."""
        parcel = ParcelBase(
            apn="AHO-01",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="R3",  # Base FAR = 1.5
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["AHO"],
        )

        far, source = compute_max_far(parcel)

        # R3 base = 1.5, AHO bonus = +0.5
        assert far == 2.0
        assert "AHO bonus" in source

    def test_aho_height_bonus_alone(self):
        """Test AHO height bonus without other overlays."""
        parcel = ParcelBase(
            apn="AHO-02",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="R3",  # Base height = 55.0
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["AHO"],
        )

        height, source = compute_max_height(parcel)

        # R3 base = 55.0, AHO bonus = +15.0
        assert height == 70.0
        assert "AHO bonus" in source


class TestCombinedOverlays:
    """Tests for combined overlay scenarios."""

    def test_dcp_tier_2_plus_aho_far(self):
        """Test DCP Tier 2 combined with AHO bonus for FAR."""
        parcel = ParcelBase(
            apn="COMBO-01",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",  # Base FAR = 2.0
            existing_units=0,
            existing_building_sqft=0,
            development_tier="2",
            overlay_codes=["DCP", "AHO"],
        )

        far, source = compute_max_far(parcel)

        # MUBM base = 2.0, Tier 2 = 2.5, + AHO = 3.0
        assert far == 3.0
        assert "DCP Tier 2" in source
        assert "AHO bonus" in source

    def test_dcp_tier_3_plus_aho_height(self):
        """Test DCP Tier 3 combined with AHO bonus for height."""
        parcel = ParcelBase(
            apn="COMBO-02",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",  # Base height = 55.0
            existing_units=0,
            existing_building_sqft=0,
            development_tier="3",
            overlay_codes=["DCP", "AHO"],
        )

        height, source = compute_max_height(parcel)

        # MUBM base = 55.0, Tier 3 = 75.0, + AHO = 90.0
        assert height == 90.0
        assert "DCP Tier 3" in source
        assert "AHO bonus" in source

    def test_bergamot_plus_aho(self):
        """Test Bergamot overlay combined with AHO bonus."""
        parcel = ParcelBase(
            apn="COMBO-03",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUB",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["Bergamot", "AHO"],
        )

        far, source = compute_max_far(parcel)
        height, height_source = compute_max_height(parcel)

        # Bergamot = 2.0, + AHO = 2.5
        assert far == 2.5
        assert "Bergamot" in source
        assert "AHO bonus" in source

        # Bergamot = 65.0, + AHO = 80.0
        assert height == 80.0
        assert "Bergamot" in height_source
        assert "AHO bonus" in height_source


class TestTierInfo:
    """Tests for tier information helper function."""

    def test_tier_info_dcp_tier_1(self):
        """Test tier info for DCP Tier 1."""
        parcel = ParcelBase(
            apn="INFO-01",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="1",
            overlay_codes=["DCP"],
        )

        info = get_tier_info(parcel)

        assert info is not None
        assert "Downtown Community Plan Tier 1" in info

    def test_tier_info_bergamot(self):
        """Test tier info for Bergamot overlay."""
        parcel = ParcelBase(
            apn="INFO-02",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUB",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["Bergamot"],
        )

        info = get_tier_info(parcel)

        assert info is not None
        assert "Bergamot Area Plan" in info

    def test_tier_info_aho(self):
        """Test tier info for AHO overlay."""
        parcel = ParcelBase(
            apn="INFO-03",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["AHO"],
        )

        info = get_tier_info(parcel)

        assert info is not None
        assert "Affordable Housing Overlay" in info

    def test_tier_info_multiple_overlays(self):
        """Test tier info with multiple overlays."""
        parcel = ParcelBase(
            apn="INFO-04",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="2",
            overlay_codes=["DCP", "AHO"],
        )

        info = get_tier_info(parcel)

        assert info is not None
        assert "Downtown Community Plan Tier 2" in info
        assert "Affordable Housing Overlay" in info

    def test_tier_info_no_overlays(self):
        """Test tier info returns None when no overlays present."""
        parcel = ParcelBase(
            apn="INFO-05",
            address="Test",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=10000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0,
        )

        info = get_tier_info(parcel)

        assert info is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_overlay_list(self):
        """Test handling of empty overlay list."""
        parcel = ParcelBase(
            apn="EDGE-01",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=10000.0,
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=[],
        )

        far, source = compute_max_far(parcel)

        # Should use base zoning
        assert far == 1.5
        assert "Base zoning (R3)" in source

    def test_none_overlay_codes(self):
        """Test handling of None overlay_codes."""
        parcel = ParcelBase(
            apn="EDGE-02",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=10000.0,
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=None,
        )

        far, source = compute_max_far(parcel)
        height, height_source = compute_max_height(parcel)

        # Should use base zoning
        assert far == 1.5
        assert height == 55.0

    def test_invalid_tier_value(self):
        """Test handling of invalid tier value."""
        parcel = ParcelBase(
            apn="EDGE-03",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=10000.0,
            zoning_code="MUBM",
            existing_units=0,
            existing_building_sqft=0,
            development_tier="99",  # Invalid tier
            overlay_codes=["DCP"],
        )

        far, source = compute_max_far(parcel)

        # Should fall back to base zoning for invalid tier
        assert far == 2.0
        assert "Base zoning" in source

    def test_unknown_overlay_code(self):
        """Test handling of unknown overlay code."""
        parcel = ParcelBase(
            apn="EDGE-04",
            address="Test",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=10000.0,
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0,
            overlay_codes=["UNKNOWN"],
        )

        far, source = compute_max_far(parcel)

        # Should use base zoning
        assert far == 1.5
        assert "Base zoning (R3)" in source


class TestConstantValues:
    """Tests to verify tier constant values are as expected."""

    def test_dcp_tier_multipliers(self):
        """Test DCP tier multiplier constants."""
        assert DCP_TIER_FAR_MULTIPLIER['1'] == 1.0
        assert DCP_TIER_FAR_MULTIPLIER['2'] == 1.25
        assert DCP_TIER_FAR_MULTIPLIER['3'] == 1.5

    def test_dcp_tier_height_bonuses(self):
        """Test DCP tier height bonus constants."""
        assert DCP_TIER_HEIGHT_BONUS['1'] == 0
        assert DCP_TIER_HEIGHT_BONUS['2'] == 10
        assert DCP_TIER_HEIGHT_BONUS['3'] == 20

    def test_bergamot_standards(self):
        """Test Bergamot area plan constants."""
        assert BERGAMOT_FAR['default'] == 2.0
        assert BERGAMOT_HEIGHT['default'] == 65.0

    def test_aho_bonuses(self):
        """Test AHO bonus constants."""
        assert AHO_FAR_BONUS == 0.5
        assert AHO_HEIGHT_BONUS == 15.0

    def test_base_zone_completeness(self):
        """Test that base zone tables include expected codes."""
        expected_zones = ['R1', 'R2', 'R3', 'R4', 'NV', 'WT', 'MUBL', 'MUBM', 'MUBH', 'MUB', 'MUCR']

        for zone in expected_zones:
            assert zone in BASE_ZONE_FAR, f"{zone} missing from BASE_ZONE_FAR"
            assert zone in BASE_ZONE_HEIGHT, f"{zone} missing from BASE_ZONE_HEIGHT"
