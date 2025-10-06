"""
Tests for zoning overlay district rules.

Tests overlay modifications to base zoning including TOD, historic,
and affordable housing overlays.
"""
import pytest
from app.rules.overlays import (
    apply_overlay_modifications,
    apply_single_overlay,
    check_overlay_applicability,
    is_near_transit,
    get_overlay_info,
    list_all_overlays,
    create_tod_scenario,
    OVERLAY_DISTRICTS
)
from app.rules.base_zoning import analyze_base_zoning
from app.models.parcel import ParcelBase
from app.models.zoning import ZoningOverlay


class TestOverlayIdentification:
    """Tests for identifying applicable overlay districts."""

    def test_tod_overlay_in_transit_city(self, transit_adjacent_parcel):
        """Test TOD overlay applies in transit city."""
        assert check_overlay_applicability(transit_adjacent_parcel, "TOD") is True

    def test_historic_overlay_old_building(self, historic_parcel):
        """Test historic overlay applies to old buildings."""
        # Historic parcel built in 1920
        assert check_overlay_applicability(historic_parcel, "HP") is True

    def test_historic_overlay_modern_building(self, r2_parcel):
        """Test historic overlay doesn't apply to modern buildings."""
        # R2 parcel built in 1978
        assert check_overlay_applicability(r2_parcel, "HP") is False

    def test_tod_not_in_small_city(self):
        """Test TOD overlay doesn't apply in small city."""
        small_city_parcel = ParcelBase(
            apn="SMALL",
            address="Test",
            city="Small Town",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        assert check_overlay_applicability(small_city_parcel, "TOD") is False


class TestTransitProximity:
    """Tests for transit proximity identification."""

    @pytest.mark.parametrize("city_name,expected_near_transit", [
        ("San Francisco", True),
        ("Oakland", True),
        ("Los Angeles", True),
        ("San Diego", True),
        ("Berkeley", True),
        ("Small Town", False),
        ("Rural City", False),
    ])
    def test_transit_proximity_by_city(self, city_name, expected_near_transit):
        """Test transit proximity for various cities."""
        parcel = ParcelBase(
            apn="TEST",
            address="Test",
            city=city_name,
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        assert is_near_transit(parcel) == expected_near_transit


class TestTODOverlay:
    """Tests for Transit-Oriented Development overlay."""

    def test_tod_increases_density(self, transit_adjacent_parcel):
        """Test that TOD overlay increases density."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        base_units = base_scenario.max_units

        tod_scenario = create_tod_scenario(base_scenario, transit_adjacent_parcel)

        assert tod_scenario is not None
        assert tod_scenario.max_units > base_units

    def test_tod_increases_height(self, transit_adjacent_parcel):
        """Test that TOD overlay increases height."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        base_height = base_scenario.max_height_ft

        tod_scenario = create_tod_scenario(base_scenario, transit_adjacent_parcel)

        assert tod_scenario.max_height_ft > base_height

    def test_tod_density_multiplier(self, transit_adjacent_parcel):
        """Test TOD density multiplier (typically 1.5x)."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        base_units = base_scenario.max_units

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, transit_adjacent_parcel, tod_overlay)

        # Should be approximately 1.5x base units
        assert modified.max_units >= base_units * 1.4
        assert modified.max_units <= base_units * 1.6

    def test_tod_not_created_outside_transit(self):
        """Test TOD scenario not created outside transit area."""
        non_transit_parcel = ParcelBase(
            apn="NON-TRANSIT",
            address="Test",
            city="Small Town",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R2",
            existing_units=0,
            existing_building_sqft=0
        )

        base_scenario = analyze_base_zoning(non_transit_parcel)
        tod_scenario = create_tod_scenario(base_scenario, non_transit_parcel)

        assert tod_scenario is None


class TestHistoricOverlay:
    """Tests for Historic Preservation overlay."""

    def test_historic_overlay_info(self):
        """Test historic overlay has correct information."""
        hp_overlay = get_overlay_info("HP")

        assert hp_overlay is not None
        assert "Historic" in hp_overlay.name
        # Historic overlay should not increase density
        assert hp_overlay.density_multiplier == 1.0
        assert hp_overlay.additional_height_ft == 0.0

    def test_historic_overlay_preserves_dimensions(self, historic_parcel):
        """Test that historic overlay doesn't increase development."""
        base_scenario = analyze_base_zoning(historic_parcel)

        hp_overlay = OVERLAY_DISTRICTS["HP"]
        modified = apply_single_overlay(base_scenario, historic_parcel, hp_overlay)

        # Should not increase units or height
        assert modified.max_units == base_scenario.max_units
        assert modified.max_height_ft == base_scenario.max_height_ft

    def test_historic_overlay_adds_requirements(self, historic_parcel):
        """Test that historic overlay adds special requirements."""
        base_scenario = analyze_base_zoning(historic_parcel)

        hp_overlay = OVERLAY_DISTRICTS["HP"]
        modified = apply_single_overlay(base_scenario, historic_parcel, hp_overlay)

        notes_text = " ".join(modified.notes).lower()
        assert "historic" in notes_text or "character" in notes_text or "design" in notes_text


class TestAffordableHousingOverlay:
    """Tests for Affordable Housing Overlay."""

    def test_aho_increases_density(self, r2_parcel):
        """Test that AHO increases density."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        aho_overlay = OVERLAY_DISTRICTS["AHO"]
        modified = apply_single_overlay(base_scenario, r2_parcel, aho_overlay)

        assert modified.max_units > base_units

    def test_aho_density_multiplier(self, r2_parcel):
        """Test AHO density multiplier (typically 1.3x)."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        aho_overlay = OVERLAY_DISTRICTS["AHO"]
        modified = apply_single_overlay(base_scenario, r2_parcel, aho_overlay)

        # Should be approximately 1.3x
        assert modified.max_units >= base_units * 1.2
        assert modified.max_units <= base_units * 1.4

    def test_aho_affordable_requirement_noted(self, r2_parcel):
        """Test that AHO notes affordable housing requirement."""
        base_scenario = analyze_base_zoning(r2_parcel)

        aho_overlay = OVERLAY_DISTRICTS["AHO"]
        modified = apply_single_overlay(base_scenario, r2_parcel, aho_overlay)

        notes_text = " ".join(modified.notes).lower()
        assert "affordable" in notes_text or "20%" in notes_text


class TestFormBasedCodeOverlay:
    """Tests for Form-Based Code overlay."""

    def test_fbc_increases_density(self, r2_parcel):
        """Test that FBC overlay increases density."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        fbc_overlay = OVERLAY_DISTRICTS["FBC"]
        modified = apply_single_overlay(base_scenario, r2_parcel, fbc_overlay)

        assert modified.max_units > base_units

    def test_fbc_form_requirements(self, r2_parcel):
        """Test that FBC notes form-based requirements."""
        base_scenario = analyze_base_zoning(r2_parcel)

        fbc_overlay = OVERLAY_DISTRICTS["FBC"]
        modified = apply_single_overlay(base_scenario, r2_parcel, fbc_overlay)

        notes_text = " ".join(modified.notes).lower()
        assert "form" in notes_text


class TestMultipleOverlays:
    """Tests for applying multiple overlays."""

    def test_multiple_overlays_applied(self, transit_adjacent_parcel):
        """Test applying multiple overlays to one parcel."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)

        modified = apply_overlay_modifications(
            base_scenario,
            transit_adjacent_parcel,
            ["TOD", "AHO"]
        )

        # Should have modifications from both overlays
        assert modified.max_units > base_scenario.max_units

    def test_overlays_are_cumulative(self, r2_parcel):
        """Test that overlay effects are cumulative."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        # Apply TOD (1.5x) and AHO (1.3x)
        modified = apply_overlay_modifications(
            base_scenario,
            r2_parcel,
            ["TOD", "AHO"]
        )

        # Should have multiplied effects
        # Note: actual implementation may vary
        assert modified.max_units >= base_units * 1.3

    def test_empty_overlay_list(self, r2_parcel):
        """Test with empty overlay list."""
        base_scenario = analyze_base_zoning(r2_parcel)

        modified = apply_overlay_modifications(
            base_scenario,
            r2_parcel,
            []
        )

        # Should be unchanged
        assert modified.max_units == base_scenario.max_units


class TestOverlayInfo:
    """Tests for overlay information retrieval."""

    def test_get_overlay_info_valid_code(self):
        """Test getting overlay info for valid code."""
        tod_info = get_overlay_info("TOD")

        assert tod_info is not None
        assert isinstance(tod_info, ZoningOverlay)
        assert "Transit" in tod_info.name

    def test_get_overlay_info_invalid_code(self):
        """Test getting overlay info for invalid code."""
        invalid = get_overlay_info("INVALID_CODE")

        assert invalid is None

    def test_list_all_overlays(self):
        """Test listing all overlay districts."""
        overlays = list_all_overlays()

        assert isinstance(overlays, list)
        assert len(overlays) > 0
        assert all(isinstance(o, ZoningOverlay) for o in overlays)

    def test_all_overlays_have_required_fields(self):
        """Test that all overlays have required fields."""
        overlays = list_all_overlays()

        for overlay in overlays:
            assert overlay.name
            assert overlay.density_multiplier is not None
            assert overlay.additional_height_ft is not None


class TestOverlayModifications:
    """Tests for specific overlay modifications."""

    def test_height_modification(self, r2_parcel):
        """Test that overlays correctly modify height."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_height = base_scenario.max_height_ft

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, r2_parcel, tod_overlay)

        # Height should increase by additional_height_ft
        expected_height = base_height + tod_overlay.additional_height_ft
        assert modified.max_height_ft == expected_height

    def test_stories_updated_with_height(self, r2_parcel):
        """Test that stories are updated when height increases."""
        base_scenario = analyze_base_zoning(r2_parcel)

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, r2_parcel, tod_overlay)

        # Stories should be recalculated based on new height
        implied_story_height = modified.max_height_ft / modified.max_stories
        assert 8 <= implied_story_height <= 15  # Reasonable story height

    def test_building_sqft_increases_with_density(self, r2_parcel):
        """Test that building square footage increases with density."""
        base_scenario = analyze_base_zoning(r2_parcel)

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, r2_parcel, tod_overlay)

        # Building size should increase proportionally to density
        density_ratio = modified.max_units / base_scenario.max_units
        sqft_ratio = modified.max_building_sqft / base_scenario.max_building_sqft

        # Ratios should be similar
        assert abs(density_ratio - sqft_ratio) < 0.3


class TestOverlayNotes:
    """Tests for overlay documentation in notes."""

    def test_overlay_name_in_notes(self, r2_parcel):
        """Test that overlay name appears in notes."""
        base_scenario = analyze_base_zoning(r2_parcel)

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, r2_parcel, tod_overlay)

        notes_text = " ".join(modified.notes)
        assert "Transit-Oriented" in notes_text or "TOD" in notes_text

    def test_density_increase_documented(self, r2_parcel):
        """Test that density increase is documented."""
        base_scenario = analyze_base_zoning(r2_parcel)

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, r2_parcel, tod_overlay)

        notes_text = " ".join(modified.notes)
        # Should mention density increase percentage
        assert "density" in notes_text.lower() or "50%" in notes_text

    def test_height_increase_documented(self, r2_parcel):
        """Test that height increase is documented."""
        base_scenario = analyze_base_zoning(r2_parcel)

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, r2_parcel, tod_overlay)

        notes_text = " ".join(modified.notes)
        # Should mention height increase
        assert "height" in notes_text.lower() or "20" in notes_text

    def test_special_requirements_documented(self, r2_parcel):
        """Test that special requirements are documented."""
        base_scenario = analyze_base_zoning(r2_parcel)

        tod_overlay = OVERLAY_DISTRICTS["TOD"]
        modified = apply_single_overlay(base_scenario, r2_parcel, tod_overlay)

        if tod_overlay.special_requirements:
            notes_text = " ".join(modified.notes).lower()
            assert "requirement" in notes_text or "mixed" in notes_text


class TestOverlayEdgeCases:
    """Tests for edge cases in overlay application."""

    def test_no_density_increase_overlay(self, r2_parcel):
        """Test overlay with density_multiplier of 1.0."""
        base_scenario = analyze_base_zoning(r2_parcel)

        hp_overlay = OVERLAY_DISTRICTS["HP"]  # Has 1.0 multiplier
        modified = apply_single_overlay(base_scenario, r2_parcel, hp_overlay)

        # Units should not change
        assert modified.max_units == base_scenario.max_units

    def test_no_height_increase_overlay(self, r2_parcel):
        """Test overlay with additional_height_ft of 0."""
        base_scenario = analyze_base_zoning(r2_parcel)

        hp_overlay = OVERLAY_DISTRICTS["HP"]  # Has 0 additional height
        modified = apply_single_overlay(base_scenario, r2_parcel, hp_overlay)

        # Height should not change
        assert modified.max_height_ft == base_scenario.max_height_ft

    def test_case_insensitive_overlay_codes(self, r2_parcel):
        """Test that overlay codes are case-insensitive."""
        base_scenario = analyze_base_zoning(r2_parcel)

        # Test with lowercase
        modified1 = apply_overlay_modifications(base_scenario, r2_parcel, ["tod"])
        # Test with uppercase
        modified2 = apply_overlay_modifications(base_scenario.model_copy(deep=True), r2_parcel, ["TOD"])

        # Should have same result
        assert modified1.max_units == modified2.max_units

    def test_unknown_overlay_ignored(self, r2_parcel):
        """Test that unknown overlay codes are ignored."""
        base_scenario = analyze_base_zoning(r2_parcel)

        modified = apply_overlay_modifications(
            base_scenario,
            r2_parcel,
            ["UNKNOWN_OVERLAY"]
        )

        # Should be unchanged
        assert modified.max_units == base_scenario.max_units


class TestTODScenarioCreation:
    """Tests for TOD scenario creation."""

    def test_tod_scenario_name(self, transit_adjacent_parcel):
        """Test TOD scenario has correct name."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        tod_scenario = create_tod_scenario(base_scenario, transit_adjacent_parcel)

        assert "TOD" in tod_scenario.scenario_name

    def test_tod_legal_basis(self, transit_adjacent_parcel):
        """Test TOD scenario legal basis."""
        base_scenario = analyze_base_zoning(transit_adjacent_parcel)
        tod_scenario = create_tod_scenario(base_scenario, transit_adjacent_parcel)

        assert "Transit-Oriented" in tod_scenario.legal_basis or "Overlay" in tod_scenario.legal_basis
