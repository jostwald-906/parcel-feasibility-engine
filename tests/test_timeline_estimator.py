"""
Tests for timeline estimator service.

Tests timeline estimation for different development pathways:
- Ministerial (SB 9, SB 35, AB 2011, ADU)
- Administrative
- Discretionary
"""

import pytest
from app.services.timeline_estimator import (
    estimate_timeline,
    detect_pathway_type,
    EntitlementTimeline,
    TimelineStep,
)
from app.models.parcel import ParcelBase


class TestPathwayDetection:
    """Tests for pathway type detection."""

    def test_sb9_detected_as_ministerial(self):
        """SB 9 should be detected as ministerial."""
        pathway = detect_pathway_type("SB 9 Lot Split (Gov. Code § 65852.21)")
        assert pathway == "Ministerial"

    def test_sb35_detected_as_ministerial(self):
        """SB 35 should be detected as ministerial."""
        pathway = detect_pathway_type("SB 35 Streamlined Approval (Gov. Code § 65913.4)")
        assert pathway == "Ministerial"

    def test_ab2011_detected_as_ministerial(self):
        """AB 2011 should be detected as ministerial."""
        pathway = detect_pathway_type("AB 2011 Office Conversion (Gov. Code § 65912.100)")
        assert pathway == "Ministerial"

    def test_adu_detected_as_ministerial(self):
        """ADU should be detected as ministerial."""
        pathway = detect_pathway_type("ADU - Accessory Dwelling Unit (Gov. Code § 65852.2)")
        assert pathway == "Ministerial"

    def test_administrative_detected(self):
        """Administrative permits should be detected."""
        pathway = detect_pathway_type("Administrative Review Permit (ARP)")
        assert pathway == "Administrative"

    def test_discretionary_default(self):
        """Non-ministerial/administrative should default to discretionary."""
        pathway = detect_pathway_type("Conditional Use Permit")
        assert pathway == "Discretionary"

    def test_case_insensitive(self):
        """Pathway detection should be case insensitive."""
        pathway = detect_pathway_type("sb 9 lot split")
        assert pathway == "Ministerial"


class TestSB9Timeline:
    """Tests for SB 9 timeline estimation."""

    def test_sb9_timeline_structure(self):
        """SB 9 timeline should have correct structure."""
        timeline = estimate_timeline(
            scenario_name="SB 9 Lot Split",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        assert isinstance(timeline, EntitlementTimeline)
        assert timeline.pathway_type == "Ministerial"
        assert timeline.statutory_deadline == 60
        assert len(timeline.steps) > 0
        assert len(timeline.notes) > 0

    def test_sb9_timeline_within_60_days(self):
        """SB 9 timeline should be within statutory 60-day deadline."""
        timeline = estimate_timeline(
            scenario_name="SB 9 Lot Split",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        assert timeline.total_days_min <= 60
        assert timeline.total_days_max <= 60

    def test_sb9_steps_valid(self):
        """SB 9 timeline steps should have valid data."""
        timeline = estimate_timeline(
            scenario_name="SB 9 Lot Split",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        for step in timeline.steps:
            assert isinstance(step, TimelineStep)
            assert step.days_min > 0
            assert step.days_max >= step.days_min
            assert len(step.step_name) > 0
            assert len(step.description) > 0

    def test_sb9_total_matches_sum(self):
        """SB 9 timeline total should match sum of steps."""
        timeline = estimate_timeline(
            scenario_name="SB 9 Lot Split",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        sum_min = sum(step.days_min for step in timeline.steps)
        sum_max = sum(step.days_max for step in timeline.steps)

        assert timeline.total_days_min == sum_min
        assert timeline.total_days_max == sum_max


class TestSB35Timeline:
    """Tests for SB 35 timeline estimation."""

    def test_sb35_timeline_structure(self):
        """SB 35 timeline should have correct structure."""
        timeline = estimate_timeline(
            scenario_name="SB 35 Streamlined",
            legal_basis="SB 35 (Gov. Code § 65913.4)",
            max_units=50,
        )

        assert timeline.pathway_type == "Ministerial"
        assert timeline.statutory_deadline == 90

    def test_sb35_timeline_within_90_days(self):
        """SB 35 timeline should be within statutory 90-day deadline."""
        timeline = estimate_timeline(
            scenario_name="SB 35 Streamlined",
            legal_basis="SB 35 (Gov. Code § 65913.4)",
            max_units=50,
        )

        assert timeline.total_days_min <= 90
        assert timeline.total_days_max <= 90


class TestAB2011Timeline:
    """Tests for AB 2011 timeline estimation."""

    def test_ab2011_timeline_ministerial(self):
        """AB 2011 should be ministerial pathway."""
        timeline = estimate_timeline(
            scenario_name="AB 2011 Conversion",
            legal_basis="AB 2011 (Gov. Code § 65912.100)",
            max_units=30,
        )

        assert timeline.pathway_type == "Ministerial"
        assert timeline.statutory_deadline is None  # No specific statutory deadline

    def test_ab2011_timeline_reasonable(self):
        """AB 2011 timeline should be reasonable (3-6 months)."""
        timeline = estimate_timeline(
            scenario_name="AB 2011 Conversion",
            legal_basis="AB 2011 (Gov. Code § 65912.100)",
            max_units=30,
        )

        # Should be roughly 3-6 months (90-180 days)
        assert timeline.total_days_min >= 60
        assert timeline.total_days_max <= 200


class TestADUTimeline:
    """Tests for ADU timeline estimation."""

    def test_adu_timeline_structure(self):
        """ADU timeline should have correct structure."""
        timeline = estimate_timeline(
            scenario_name="ADU",
            legal_basis="ADU (Gov. Code § 65852.2)",
            max_units=2,
        )

        assert timeline.pathway_type == "Ministerial"
        assert timeline.statutory_deadline == 60

    def test_adu_timeline_within_60_days(self):
        """ADU timeline should be within statutory 60-day deadline."""
        timeline = estimate_timeline(
            scenario_name="ADU",
            legal_basis="ADU (Gov. Code § 65852.2)",
            max_units=2,
        )

        assert timeline.total_days_min <= 60
        assert timeline.total_days_max <= 60


class TestAdministrativeTimeline:
    """Tests for administrative timeline estimation."""

    def test_administrative_timeline_structure(self):
        """Administrative timeline should have correct structure."""
        timeline = estimate_timeline(
            scenario_name="Administrative Permit",
            legal_basis="Administrative Review Permit (ARP)",
            max_units=8,
        )

        assert timeline.pathway_type == "Administrative"
        assert timeline.statutory_deadline is None

    def test_administrative_timeline_reasonable(self):
        """Administrative timeline should be reasonable (3-6 months)."""
        timeline = estimate_timeline(
            scenario_name="Administrative Permit",
            legal_basis="Administrative Review Permit",
            max_units=8,
        )

        # Should be roughly 3-6 months (90-180 days)
        assert timeline.total_days_min >= 60
        assert timeline.total_days_max <= 200


class TestDiscretionaryTimeline:
    """Tests for discretionary timeline estimation."""

    def test_discretionary_timeline_structure(self):
        """Discretionary timeline should have correct structure."""
        timeline = estimate_timeline(
            scenario_name="Conditional Use Permit",
            legal_basis="CUP",
            max_units=20,
        )

        assert timeline.pathway_type == "Discretionary"
        assert timeline.statutory_deadline is None

    def test_discretionary_timeline_longer_than_ministerial(self):
        """Discretionary timeline should be longer than ministerial."""
        discretionary = estimate_timeline(
            scenario_name="CUP",
            legal_basis="Conditional Use Permit",
            max_units=20,
        )

        ministerial = estimate_timeline(
            scenario_name="SB 9",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        assert discretionary.total_days_min > ministerial.total_days_min
        assert discretionary.total_days_max > ministerial.total_days_max

    def test_discretionary_large_project_longer(self):
        """Large discretionary projects should take longer."""
        small_project = estimate_timeline(
            scenario_name="Small CUP",
            legal_basis="Conditional Use Permit",
            max_units=8,
        )

        large_project = estimate_timeline(
            scenario_name="Large CUP",
            legal_basis="Conditional Use Permit",
            max_units=50,
        )

        # Large projects should have longer timelines
        assert large_project.total_days_max >= small_project.total_days_max

    def test_discretionary_timeline_range(self):
        """Discretionary timeline should be 6-18 months range."""
        timeline = estimate_timeline(
            scenario_name="CUP",
            legal_basis="Conditional Use Permit",
            max_units=20,
        )

        # Should be roughly 6-18 months (180-540 days)
        assert timeline.total_days_min >= 150
        assert timeline.total_days_max <= 600


class TestTimelineSteps:
    """Tests for timeline step structure."""

    def test_steps_have_required_fields(self):
        """All timeline steps should have required fields."""
        timeline = estimate_timeline(
            scenario_name="Test",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        for step in timeline.steps:
            assert hasattr(step, "step_name")
            assert hasattr(step, "days_min")
            assert hasattr(step, "days_max")
            assert hasattr(step, "description")
            assert hasattr(step, "required_submittals")

    def test_steps_chronological(self):
        """Timeline steps should be in chronological order."""
        timeline = estimate_timeline(
            scenario_name="Test",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        cumulative = 0
        for step in timeline.steps:
            assert step.days_min > 0
            cumulative += step.days_min

        # Total should match
        assert cumulative == timeline.total_days_min

    def test_submittals_list_type(self):
        """Required submittals should be a list."""
        timeline = estimate_timeline(
            scenario_name="Test",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        for step in timeline.steps:
            assert isinstance(step.required_submittals, list)


class TestTimelineNotes:
    """Tests for timeline notes."""

    def test_ministerial_notes_mention_no_hearing(self):
        """Ministerial timelines should note no public hearing required."""
        timeline = estimate_timeline(
            scenario_name="SB 9",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        notes_text = " ".join(timeline.notes).lower()
        assert "no public hearing" in notes_text or "ministerial" in notes_text

    def test_sb9_notes_mention_statutory_deadline(self):
        """SB 9 notes should mention 60-day statutory deadline."""
        timeline = estimate_timeline(
            scenario_name="SB 9",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        notes_text = " ".join(timeline.notes)
        assert "60 days" in notes_text or "60-day" in notes_text

    def test_discretionary_notes_mention_ceqa(self):
        """Discretionary timelines should mention CEQA."""
        timeline = estimate_timeline(
            scenario_name="CUP",
            legal_basis="Conditional Use Permit",
            max_units=20,
        )

        notes_text = " ".join(timeline.notes)
        assert "CEQA" in notes_text or "environmental" in notes_text.lower()


class TestTimelineWithParcel:
    """Tests for timeline estimation with parcel context."""

    @pytest.fixture
    def r1_parcel(self):
        """Create R1 parcel for testing."""
        return ParcelBase(
            apn="1234-567-890",
            address="123 Main St",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90401",
            lot_size_sqft=5000,
            zoning_code="R1",
            existing_units=1,
            existing_building_sqft=1500,
        )

    def test_timeline_with_parcel_context(self, r1_parcel):
        """Timeline estimation should accept parcel parameter."""
        timeline = estimate_timeline(
            scenario_name="SB 9",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
            parcel=r1_parcel,
        )

        assert timeline.pathway_type == "Ministerial"

    def test_timeline_without_parcel(self):
        """Timeline estimation should work without parcel."""
        timeline = estimate_timeline(
            scenario_name="SB 9",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
            parcel=None,
        )

        assert timeline.pathway_type == "Ministerial"


class TestTimelineComparison:
    """Tests for comparing different pathway timelines."""

    def test_ministerial_faster_than_discretionary(self):
        """Ministerial pathways should be faster than discretionary."""
        ministerial = estimate_timeline(
            scenario_name="SB 9",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        discretionary = estimate_timeline(
            scenario_name="CUP",
            legal_basis="Conditional Use Permit",
            max_units=4,
        )

        assert ministerial.total_days_max < discretionary.total_days_min

    def test_pathway_ranking(self):
        """Pathways should rank: Ministerial < Administrative < Discretionary."""
        ministerial = estimate_timeline(
            scenario_name="SB 9",
            legal_basis="SB 9 (Gov. Code § 65852.21)",
            max_units=4,
        )

        administrative = estimate_timeline(
            scenario_name="ARP",
            legal_basis="Administrative Review Permit",
            max_units=4,
        )

        discretionary = estimate_timeline(
            scenario_name="CUP",
            legal_basis="Conditional Use Permit",
            max_units=4,
        )

        assert ministerial.total_days_max <= administrative.total_days_max
        assert administrative.total_days_max <= discretionary.total_days_max
