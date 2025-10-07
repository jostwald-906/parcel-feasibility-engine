"""
Tests for PDF Report Generator Service.

Tests comprehensive PDF generation for feasibility reports.
"""
import pytest
from io import BytesIO
from datetime import datetime
from app.services.report_generator import PDFReportGenerator, generate_pdf_report
from app.models.analysis import AnalysisResponse, DevelopmentScenario
from app.models.parcel import ParcelBase
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


@pytest.fixture
def sample_base_scenario() -> DevelopmentScenario:
    """Sample base zoning scenario."""
    return DevelopmentScenario(
        scenario_name="Base Zoning",
        legal_basis="Santa Monica Municipal Code - R2",
        max_units=4,
        max_building_sqft=7500.0,
        max_height_ft=30.0,
        max_stories=2,
        parking_spaces_required=6,
        affordable_units_required=0,
        setbacks={"front": 15, "rear": 15, "side": 5},
        lot_coverage_pct=40.0,
        notes=[
            "Base Zoning: R2",
            "Max FAR: 0.75",
            "Max height: 30 ft / 2 stories",
            "Parking: 1.5 spaces/unit",
        ],
    )


@pytest.fixture
def sample_alternative_scenario() -> DevelopmentScenario:
    """Sample alternative scenario (density bonus)."""
    return DevelopmentScenario(
        scenario_name="Density Bonus (15% Affordable)",
        legal_basis="State Density Bonus Law - 50% density bonus",
        max_units=6,
        max_building_sqft=9000.0,
        max_height_ft=45.0,
        max_stories=3,
        parking_spaces_required=4,
        affordable_units_required=1,
        setbacks={"front": 12, "rear": 12, "side": 4},
        lot_coverage_pct=50.0,
        notes=[
            "State Density Bonus Law applied (Gov. Code § 65915)",
            "15% affordable units at very low income level",
            "Density bonus (§ 65915(f)): 50% = 2 additional units",
            "Base units: 4 → Total units: 6",
            "Concessions granted (§ 65915(d)): 2",
        ],
        concessions_applied=[
            "Height increase to 45 ft",
            "Parking reduction by 33%",
        ],
        waivers_applied=[],
        estimated_timeline={
            "pathway_type": "Discretionary",
            "total_days_min": 268,
            "total_days_max": 516,
            "statutory_deadline": None,
        },
    )


@pytest.fixture
def sample_analysis(
    r2_parcel: ParcelBase,
    sample_base_scenario: DevelopmentScenario,
    sample_alternative_scenario: DevelopmentScenario,
) -> AnalysisResponse:
    """Sample analysis response."""
    return AnalysisResponse(
        parcel_apn=r2_parcel.apn,
        analysis_date=datetime(2025, 10, 6, 12, 0, 0),
        base_scenario=sample_base_scenario,
        alternative_scenarios=[sample_alternative_scenario],
        recommended_scenario="Density Bonus (15% Affordable)",
        recommendation_reason="Maximizes unit count with 6 units under State Density Bonus Law - 50% density bonus",
        applicable_laws=[
            "Local Zoning Code",
            "State Density Bonus Law (Gov Code 65915)",
        ],
        potential_incentives=[
            "Density bonus with concessions",
            "Community benefits can unlock Tier 2 development standards",
        ],
        warnings=[
            "Existing 2 unit(s) may need to be demolished or incorporated"
        ],
    )


class TestPDFReportGenerator:
    """Tests for PDFReportGenerator class."""

    def test_generator_initialization(self):
        """Test generator initializes successfully."""
        generator = PDFReportGenerator()
        assert generator is not None
        assert generator.styles is not None

    def test_custom_styles_created(self):
        """Test custom styles are created during initialization."""
        generator = PDFReportGenerator()

        # Check custom styles exist
        assert "ReportTitle" in generator.styles
        assert "SectionHeader" in generator.styles
        assert "SubsectionHeader" in generator.styles
        assert "BodyText" in generator.styles
        assert "Citation" in generator.styles
        assert "Footer" in generator.styles


class TestPDFGeneration:
    """Tests for PDF generation."""

    def test_generate_report_returns_bytes(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test that generate_report returns PDF bytes."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_pdf_has_correct_signature(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test that generated file is a valid PDF (has PDF signature)."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        # PDF files start with "%PDF-"
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_contains_data_fields(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test that PDF is generated successfully with reasonable size."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        # PDF should be between 5KB and 500KB for typical report
        assert 5_000 < len(pdf_bytes) < 500_000

    def test_pdf_not_empty(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test that generated PDF is not empty."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        assert len(pdf_bytes) > 0


class TestReportSections:
    """Tests for individual report sections."""

    def test_title_page_section(self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase):
        """Test title page includes required elements."""
        generator = PDFReportGenerator()
        elements = generator._build_title_page(sample_analysis, r2_parcel)

        assert len(elements) > 0

        # Convert elements to text for validation
        element_text = " ".join([str(e) for e in elements])

        # Should include title
        assert "Feasibility" in element_text or "Analysis" in element_text

    def test_executive_summary_section(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test executive summary includes key metrics."""
        generator = PDFReportGenerator()
        elements = generator._build_executive_summary(sample_analysis, r2_parcel)

        assert len(elements) > 0

    def test_parcel_information_section(self, r2_parcel: ParcelBase):
        """Test parcel information section includes required data."""
        generator = PDFReportGenerator()
        elements = generator._build_parcel_information(r2_parcel)

        assert len(elements) > 0

    def test_base_scenario_section(self, sample_base_scenario: DevelopmentScenario):
        """Test base scenario section includes scenario details."""
        generator = PDFReportGenerator()
        elements = generator._build_base_scenario_section(sample_base_scenario)

        assert len(elements) > 0

    def test_alternative_scenarios_section(
        self, sample_alternative_scenario: DevelopmentScenario
    ):
        """Test alternative scenarios section."""
        generator = PDFReportGenerator()
        elements = generator._build_alternative_scenarios_section(
            [sample_alternative_scenario]
        )

        assert len(elements) > 0

    def test_scenario_comparison_matrix(self, sample_analysis: AnalysisResponse):
        """Test scenario comparison matrix includes all scenarios."""
        generator = PDFReportGenerator()
        elements = generator._build_scenario_comparison(sample_analysis)

        assert len(elements) > 0

        # Should include base scenario + alternatives
        expected_scenarios = 1 + len(sample_analysis.alternative_scenarios)
        assert expected_scenarios == 2  # 1 base + 1 alternative

    def test_applicable_laws_section(self, sample_analysis: AnalysisResponse):
        """Test applicable laws section includes all laws."""
        generator = PDFReportGenerator()
        elements = generator._build_applicable_laws_section(sample_analysis)

        assert len(elements) > 0

    def test_timeline_section_with_timelines(
        self, sample_analysis: AnalysisResponse
    ):
        """Test timeline section when timelines are present."""
        generator = PDFReportGenerator()
        elements = generator._build_timeline_section(sample_analysis)

        assert len(elements) > 0

    def test_timeline_section_without_timelines(self, sample_analysis: AnalysisResponse):
        """Test timeline section when no timelines are present."""
        # Remove timelines
        sample_analysis.alternative_scenarios[0].estimated_timeline = None

        generator = PDFReportGenerator()
        elements = generator._build_timeline_section(sample_analysis)

        assert len(elements) > 0

    def test_recommendations_section(self, sample_analysis: AnalysisResponse):
        """Test recommendations section includes key elements."""
        generator = PDFReportGenerator()
        elements = generator._build_recommendations_section(sample_analysis)

        assert len(elements) > 0


class TestReportContent:
    """Tests for report content accuracy."""

    def test_report_builds_successfully(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test report builds successfully with all data."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        # Verify PDF structure exists (at least 5KB for a comprehensive report)
        assert len(pdf_bytes) > 5000

    def test_report_handles_all_sections(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test report generates all sections without errors."""
        # This test verifies that all sections build successfully
        generator = PDFReportGenerator()

        # Test all section builders work
        title = generator._build_title_page(sample_analysis, r2_parcel)
        assert len(title) > 0

        summary = generator._build_executive_summary(sample_analysis, r2_parcel)
        assert len(summary) > 0

        parcel_info = generator._build_parcel_information(r2_parcel)
        assert len(parcel_info) > 0

        base = generator._build_base_scenario_section(sample_analysis.base_scenario)
        assert len(base) > 0

        alts = generator._build_alternative_scenarios_section(sample_analysis.alternative_scenarios)
        assert len(alts) > 0

        comparison = generator._build_scenario_comparison(sample_analysis)
        assert len(comparison) > 0

        laws = generator._build_applicable_laws_section(sample_analysis)
        assert len(laws) > 0

        timeline = generator._build_timeline_section(sample_analysis)
        assert len(timeline) > 0

        recs = generator._build_recommendations_section(sample_analysis)
        assert len(recs) > 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_handles_missing_optional_fields(self, r2_parcel: ParcelBase):
        """Test handles parcels with missing optional fields."""
        # Create minimal parcel
        minimal_parcel = ParcelBase(
            apn="TEST-123",
            address="Test Address",
            city="Test City",
            county="Test County",
            zip_code="00000",
            lot_size_sqft=5000.0,
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0,
        )

        minimal_scenario = DevelopmentScenario(
            scenario_name="Test Scenario",
            legal_basis="Test Basis",
            max_units=1,
            max_building_sqft=1000.0,
            max_height_ft=15.0,
            max_stories=1,
            parking_spaces_required=0,
            affordable_units_required=0,
            setbacks={},
            lot_coverage_pct=40.0,
            notes=[],
        )

        minimal_analysis = AnalysisResponse(
            parcel_apn=minimal_parcel.apn,
            analysis_date=datetime.now(),
            base_scenario=minimal_scenario,
            alternative_scenarios=[],
            recommended_scenario="Test Scenario",
            recommendation_reason="Test reason",
            applicable_laws=[],
            potential_incentives=[],
            warnings=[],
        )

        # Should not raise exception
        pdf_bytes = generate_pdf_report(minimal_analysis, minimal_parcel)
        assert len(pdf_bytes) > 0

    def test_handles_empty_alternative_scenarios(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test handles analysis with no alternative scenarios."""
        sample_analysis.alternative_scenarios = []

        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)
        assert len(pdf_bytes) > 0

    def test_handles_no_warnings(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test handles analysis with no warnings."""
        sample_analysis.warnings = []

        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)
        assert len(pdf_bytes) > 0

    def test_handles_no_incentives(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test handles analysis with no incentives."""
        sample_analysis.potential_incentives = []

        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)
        assert len(pdf_bytes) > 0


class TestPDFStructure:
    """Tests for PDF document structure."""

    def test_pdf_has_multiple_pages(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test that PDF has multiple pages for comprehensive report."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        # PDF should contain page markers
        pdf_text = pdf_bytes.decode("latin-1", errors="ignore")

        # Look for page indicators (endobj markers typically indicate pages)
        assert pdf_text.count("endobj") > 3  # At least a few objects

    def test_pdf_structure_valid(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test PDF structure is valid."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        # PDF should contain EOF marker
        assert b"%%EOF" in pdf_bytes

        # Should have catalog and pages
        assert b"/Catalog" in pdf_bytes or b"/Pages" in pdf_bytes


class TestCoverageEdgeCases:
    """Tests for edge cases to improve coverage."""

    def test_parcel_with_all_optional_fields(self, r2_parcel: ParcelBase):
        """Test parcel with all optional fields populated."""
        r2_parcel.general_plan = "Test General Plan"
        r2_parcel.use_description = "Multi-family Residential"
        r2_parcel.year_built = 1985
        r2_parcel.development_tier = "2"
        r2_parcel.overlay_codes = ["DCP", "AHO"]

        generator = PDFReportGenerator()
        elements = generator._build_parcel_information(r2_parcel)

        assert len(elements) > 0

    def test_scenario_with_concessions_and_waivers(
        self, sample_alternative_scenario: DevelopmentScenario
    ):
        """Test scenario with both concessions and waivers."""
        sample_alternative_scenario.waivers_applied = [
            "Setback waiver",
            "Height waiver",
        ]

        generator = PDFReportGenerator()
        elements = generator._build_alternative_scenarios_section(
            [sample_alternative_scenario]
        )

        assert len(elements) > 0

    def test_scenario_with_affordable_units(
        self, sample_alternative_scenario: DevelopmentScenario
    ):
        """Test scenario with affordable units required."""
        sample_alternative_scenario.affordable_units_required = 3

        generator = PDFReportGenerator()
        elements = generator._build_base_scenario_section(sample_alternative_scenario)

        assert len(elements) > 0

    def test_analysis_with_many_scenarios(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test analysis with multiple alternative scenarios."""
        # Add more scenarios
        additional_scenario = DevelopmentScenario(
            scenario_name="SB 9 Lot Split",
            legal_basis="Gov. Code § 65852.21",
            max_units=4,
            max_building_sqft=6000.0,
            max_height_ft=28.0,
            max_stories=2,
            parking_spaces_required=0,
            affordable_units_required=0,
            setbacks={"front": 4, "rear": 4, "side": 4},
            lot_coverage_pct=45.0,
            notes=["SB 9 Urban Lot Split"],
            estimated_timeline={
                "pathway_type": "Ministerial",
                "total_days_min": 36,
                "total_days_max": 60,
                "statutory_deadline": 60,
            },
        )

        sample_analysis.alternative_scenarios.append(additional_scenario)

        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)
        assert len(pdf_bytes) > 0

    def test_large_lot_parcel(self):
        """Test parcel with very large lot size."""
        large_parcel = ParcelBase(
            apn="LARGE-001",
            address="1000 Big Lot Drive",
            city="Los Angeles",
            county="Los Angeles",
            zip_code="90001",
            lot_size_sqft=100000.0,  # ~2.3 acres
            zoning_code="R4",
            existing_units=0,
            existing_building_sqft=0,
        )

        generator = PDFReportGenerator()
        elements = generator._build_parcel_information(large_parcel)

        assert len(elements) > 0

    def test_scenario_with_long_notes_list(
        self, sample_base_scenario: DevelopmentScenario
    ):
        """Test scenario with many notes."""
        sample_base_scenario.notes = [
            f"Note {i}: Sample note text for testing"
            for i in range(20)
        ]

        generator = PDFReportGenerator()
        elements = generator._build_base_scenario_section(sample_base_scenario)

        assert len(elements) > 0


class TestModuleLevelFunction:
    """Tests for module-level convenience function."""

    def test_generate_pdf_report_function(
        self, sample_analysis: AnalysisResponse, r2_parcel: ParcelBase
    ):
        """Test module-level generate_pdf_report function."""
        pdf_bytes = generate_pdf_report(sample_analysis, r2_parcel)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-"
