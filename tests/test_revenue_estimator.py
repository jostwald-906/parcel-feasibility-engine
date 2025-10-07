"""
Tests for Revenue Projection Service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.revenue_estimator import (
    RevenueInputs,
    EconomicAssumptions,
    OperatingExpenses,
    RevenueProjection,
    calculate_market_rents,
    calculate_affordable_rents,
    calculate_gross_income,
    calculate_property_tax,
    calculate_operating_expenses,
    calculate_noi,
    project_revenue_stream,
    estimate_revenue
)
from app.clients.hud_fmr_client import FMRData
from app.services.ami_calculator import AMICalculator, AffordableRent


@pytest.fixture
def sample_fmr_data():
    """Sample FMR data for Los Angeles."""
    return FMRData(
        zip_code="90401",
        metro_code="METRO42644M42644",
        metro_name="Los Angeles-Long Beach-Anaheim, CA",
        county_name="Los Angeles County",
        state="CA",
        year=2024,
        fmr_0br=1823.0,
        fmr_1br=2156.0,
        fmr_2br=2815.0,
        fmr_3br=3866.0,
        fmr_4br=4614.0,
        smallarea_status=1,  # SAFMR available
        fmr_percentile=40
    )


@pytest.fixture
def sample_revenue_inputs():
    """Sample revenue inputs for testing."""
    return RevenueInputs(
        zip_code="90401",
        county="Los Angeles",
        market_unit_mix={1: 20, 2: 30},
        affordable_unit_mix={1: 5, 2: 5},
        ami_percentages=[50.0, 60.0, 80.0],
        quality_factor=1.0,
        utility_allowance=150.0
    )


@pytest.fixture
def sample_economic_assumptions():
    """Sample economic assumptions."""
    return EconomicAssumptions(
        vacancy_rate=0.05,
        property_tax_rate=0.0125,
        insurance_rate=0.006,
        management_rate=0.05,
        utilities_per_unit_annual=800.0,
        maintenance_per_unit_annual=1200.0,
        reserves_per_unit_annual=500.0,
        marketing_per_unit_annual=200.0,
        construction_cost_per_sqft=350.0,
        rent_growth_rate=0.03,
        expense_growth_rate=0.025
    )


class TestRevenueInputs:
    """Tests for RevenueInputs model."""

    def test_total_units_calculation(self):
        """Test total units calculation."""
        inputs = RevenueInputs(
            zip_code="90401",
            county="Los Angeles",
            market_unit_mix={1: 10, 2: 15},
            affordable_unit_mix={1: 3, 2: 2}
        )

        assert inputs.total_units == 30
        assert inputs.market_units == 25
        assert inputs.affordable_units == 5

    def test_quality_factor_validation(self):
        """Test quality factor must be in range 0.8-1.2."""
        # Valid quality factors
        RevenueInputs(
            zip_code="90401",
            county="Los Angeles",
            market_unit_mix={1: 10},
            quality_factor=0.8  # Class C
        )
        RevenueInputs(
            zip_code="90401",
            county="Los Angeles",
            market_unit_mix={1: 10},
            quality_factor=1.2  # Class A
        )

        # Invalid quality factors
        with pytest.raises(Exception):  # Pydantic validation error
            RevenueInputs(
                zip_code="90401",
                county="Los Angeles",
                market_unit_mix={1: 10},
                quality_factor=0.5  # Too low
            )

        with pytest.raises(Exception):
            RevenueInputs(
                zip_code="90401",
                county="Los Angeles",
                market_unit_mix={1: 10},
                quality_factor=1.5  # Too high
            )


class TestMarketRentCalculation:
    """Tests for market rent calculation using HUD FMR."""

    @pytest.mark.asyncio
    async def test_calculate_market_rents_base_fmr(self, sample_fmr_data):
        """Test calculating market rents with quality factor 1.0."""
        mock_client = Mock()
        mock_client.get_fmr_by_zip = AsyncMock(return_value=sample_fmr_data)
        mock_client.get_fmr_for_bedroom = lambda data, br: {
            0: 1823.0, 1: 2156.0, 2: 2815.0, 3: 3866.0, 4: 4614.0
        }[br]

        market_rents, fmr_data = await calculate_market_rents(
            zip_code="90401",
            unit_mix={0: 5, 1: 10, 2: 15},
            quality_factor=1.0,
            hud_client=mock_client
        )

        # Quality factor 1.0 = no adjustment
        assert market_rents["studio"] == 1823.0
        assert market_rents["1br"] == 2156.0
        assert market_rents["2br"] == 2815.0
        assert fmr_data.smallarea_status == 1  # SAFMR

    @pytest.mark.asyncio
    async def test_calculate_market_rents_class_c(self, sample_fmr_data):
        """Test calculating market rents with Class C quality (0.85)."""
        mock_client = Mock()
        mock_client.get_fmr_by_zip = AsyncMock(return_value=sample_fmr_data)
        mock_client.get_fmr_for_bedroom = lambda data, br: {
            0: 1823.0, 1: 2156.0, 2: 2815.0
        }[br]

        market_rents, _ = await calculate_market_rents(
            zip_code="90401",
            unit_mix={1: 10, 2: 15},
            quality_factor=0.85,  # Class C (below market)
            hud_client=mock_client
        )

        # 15% discount from FMR
        assert market_rents["1br"] == pytest.approx(2156.0 * 0.85)
        assert market_rents["2br"] == pytest.approx(2815.0 * 0.85)

    @pytest.mark.asyncio
    async def test_calculate_market_rents_class_a(self, sample_fmr_data):
        """Test calculating market rents with Class A quality (1.15)."""
        mock_client = Mock()
        mock_client.get_fmr_by_zip = AsyncMock(return_value=sample_fmr_data)
        mock_client.get_fmr_for_bedroom = lambda data, br: {
            1: 2156.0, 2: 2815.0
        }[br]

        market_rents, _ = await calculate_market_rents(
            zip_code="90401",
            unit_mix={1: 10, 2: 15},
            quality_factor=1.15,  # Class A (above market)
            hud_client=mock_client
        )

        # 15% premium over FMR
        assert market_rents["1br"] == pytest.approx(2156.0 * 1.15)
        assert market_rents["2br"] == pytest.approx(2815.0 * 1.15)


class TestAffordableRentCalculation:
    """Tests for affordable rent calculation using AMI."""

    def test_calculate_affordable_rents(self):
        """Test calculating affordable rents using AMI calculator."""
        mock_calculator = Mock(spec=AMICalculator)

        # Mock affordable rent responses
        def mock_calculate_max_rent(county, ami_pct, bedrooms, utility_allowance):
            # Return different rents for different AMI levels
            base_rent = {0: 800, 1: 1000, 2: 1200}[bedrooms]
            ami_factor = ami_pct / 100.0
            return AffordableRent(
                county=county,
                ami_pct=ami_pct,
                bedrooms=bedrooms,
                household_size=bedrooms + 2,
                income_limit=50000 * ami_factor,
                max_rent_with_utilities=base_rent * ami_factor + 150,
                max_rent_no_utilities=base_rent * ami_factor,
                utility_allowance=150.0
            )

        mock_calculator.calculate_max_rent = mock_calculate_max_rent

        affordable_rents = calculate_affordable_rents(
            county="Los Angeles",
            unit_mix_affordable={0: 2, 1: 5, 2: 8},
            ami_percentages=[50.0, 60.0, 80.0],
            utility_allowance=150.0,
            ami_calculator=mock_calculator
        )

        # Should have rents for each bedroom type
        assert "studio" in affordable_rents
        assert "1br" in affordable_rents
        assert "2br" in affordable_rents

        # Rents should be averages of AMI levels
        # Studio: (800*0.5 + 800*0.6 + 800*0.8) / 3 = 506.67
        assert affordable_rents["studio"] == pytest.approx(506.67, abs=1)


class TestGrossIncomeCalculation:
    """Tests for gross potential income calculation."""

    def test_calculate_gross_income_market_only(self):
        """Test GPI calculation with market-rate units only."""
        market_rents = {"1br": 2000.0, "2br": 2500.0}
        affordable_rents = {}
        market_unit_mix = {1: 10, 2: 15}
        affordable_unit_mix = {}

        gpi = calculate_gross_income(
            market_rents,
            affordable_rents,
            market_unit_mix,
            affordable_unit_mix
        )

        # GPI = (10 units × $2000 × 12) + (15 units × $2500 × 12)
        expected = (10 * 2000 * 12) + (15 * 2500 * 12)
        assert gpi == expected

    def test_calculate_gross_income_mixed(self):
        """Test GPI calculation with market and affordable units."""
        market_rents = {"1br": 2000.0, "2br": 2500.0}
        affordable_rents = {"1br": 1200.0, "2br": 1500.0}
        market_unit_mix = {1: 10, 2: 15}
        affordable_unit_mix = {1: 5, 2: 5}

        gpi = calculate_gross_income(
            market_rents,
            affordable_rents,
            market_unit_mix,
            affordable_unit_mix
        )

        # Market: (10 × 2000 × 12) + (15 × 2500 × 12) = 690,000
        # Affordable: (5 × 1200 × 12) + (5 × 1500 × 12) = 162,000
        # Total: 852,000
        expected = (10 * 2000 * 12) + (15 * 2500 * 12) + (5 * 1200 * 12) + (5 * 1500 * 12)
        assert gpi == expected


class TestPropertyTaxCalculation:
    """Tests for property tax calculation (Prop 13)."""

    def test_calculate_property_tax_prop13_base(self):
        """Test property tax calculation with Prop 13 base rate (1%)."""
        assessed_value = 10_000_000
        tax_rate = 0.01  # 1% base

        tax = calculate_property_tax(assessed_value, tax_rate)

        assert tax == 100_000

    def test_calculate_property_tax_with_local_adders(self):
        """Test property tax with local voter-approved add-ons."""
        assessed_value = 10_000_000
        tax_rate = 0.0125  # 1% base + 0.25% local

        tax = calculate_property_tax(assessed_value, tax_rate)

        assert tax == 125_000

    def test_calculate_property_tax_typical_california(self):
        """Test property tax with typical California rate (1.1-1.3%)."""
        assessed_value = 5_000_000
        tax_rate = 0.012  # Typical California rate

        tax = calculate_property_tax(assessed_value, tax_rate)

        assert tax == 60_000


class TestOperatingExpensesCalculation:
    """Tests for operating expenses calculation."""

    def test_calculate_operating_expenses(self, sample_economic_assumptions):
        """Test comprehensive operating expense calculation."""
        expenses = calculate_operating_expenses(
            num_units=50,
            total_buildable_sqft=50_000,
            assessed_value=10_000_000,
            effective_gross_income=1_500_000,
            assumptions=sample_economic_assumptions
        )

        # Verify individual components
        assert expenses.property_tax == 125_000  # 10M × 1.25%
        assert expenses.insurance == pytest.approx(105_000)  # 50k SF × 350 × 0.6%
        assert expenses.management == 75_000  # 1.5M × 5%
        assert expenses.utilities == 40_000  # 50 units × 800
        assert expenses.maintenance == 60_000  # 50 units × 1200
        assert expenses.reserves == 25_000  # 50 units × 500
        assert expenses.marketing == 10_000  # 50 units × 200

        # Verify total
        expected_total = 125_000 + 105_000 + 75_000 + 40_000 + 60_000 + 25_000 + 10_000
        assert expenses.total == pytest.approx(expected_total)


class TestNOICalculation:
    """Tests for Net Operating Income calculation."""

    def test_calculate_noi(self):
        """Test NOI calculation."""
        gpi = 1_500_000
        vacancy_rate = 0.05
        expenses = OperatingExpenses(
            property_tax=125_000,
            insurance=105_000,
            management=75_000,
            utilities=40_000,
            maintenance=60_000,
            reserves=25_000,
            marketing=10_000
        )

        vacancy, egi, noi = calculate_noi(gpi, vacancy_rate, expenses)

        # Verify calculations
        assert vacancy == 75_000  # 1.5M × 5%
        assert egi == 1_425_000  # 1.5M - 75k
        assert noi == pytest.approx(985_000)  # 1.425M - 440k expenses

    def test_calculate_noi_zero_vacancy(self):
        """Test NOI with zero vacancy."""
        gpi = 1_500_000
        vacancy_rate = 0.0
        expenses = OperatingExpenses(
            property_tax=100_000,
            insurance=50_000,
            management=75_000,
            utilities=40_000,
            maintenance=60_000,
            reserves=25_000,
            marketing=10_000
        )

        vacancy, egi, noi = calculate_noi(gpi, vacancy_rate, expenses)

        assert vacancy == 0
        assert egi == gpi
        assert noi == gpi - expenses.total


class TestRevenueProjections:
    """Tests for multi-year revenue projections."""

    def test_project_revenue_stream_10_years(self):
        """Test 10-year revenue projections with growth."""
        projections = project_revenue_stream(
            base_noi=1_000_000,
            base_gpi=1_500_000,
            base_expenses=500_000,
            rent_growth_rate=0.03,  # 3% rent growth
            expense_growth_rate=0.025,  # 2.5% expense growth
            years=10
        )

        assert len(projections) == 10

        # Year 1 should match base
        year_1 = projections[0]
        assert year_1["year"] == 1
        assert year_1["gpi"] == 1_500_000
        assert year_1["operating_expenses"] == 500_000
        assert year_1["noi"] == pytest.approx(1_000_000)

        # Year 10 should show growth
        year_10 = projections[9]
        assert year_10["year"] == 10
        assert year_10["gpi"] > 1_500_000  # Rent growth
        assert year_10["operating_expenses"] > 500_000  # Expense growth
        assert year_10["noi"] > 1_000_000  # Net growth (rents > expenses)

    def test_project_revenue_stream_noi_grows(self):
        """Test that NOI grows when rent growth exceeds expense growth."""
        projections = project_revenue_stream(
            base_noi=1_000_000,
            base_gpi=1_500_000,
            base_expenses=500_000,
            rent_growth_rate=0.04,  # 4% rent growth
            expense_growth_rate=0.02,  # 2% expense growth
            years=5
        )

        # NOI should increase each year
        for i in range(1, len(projections)):
            assert projections[i]["noi"] > projections[i-1]["noi"]


class TestFullRevenueEstimation:
    """Tests for end-to-end revenue estimation."""

    @pytest.mark.asyncio
    async def test_estimate_revenue_complete(
        self,
        sample_revenue_inputs,
        sample_economic_assumptions,
        sample_fmr_data
    ):
        """Test complete revenue estimation pipeline."""
        # Mock HUD client
        mock_hud_client = Mock()
        mock_hud_client.get_fmr_by_zip = AsyncMock(return_value=sample_fmr_data)
        mock_hud_client.get_fmr_for_bedroom = lambda data, br: {
            1: 2156.0, 2: 2815.0
        }[br]

        # Mock AMI calculator
        mock_ami_calculator = Mock(spec=AMICalculator)

        def mock_calculate_max_rent(county, ami_pct, bedrooms, utility_allowance):
            base_rent = {1: 1000, 2: 1200}[bedrooms]
            ami_factor = ami_pct / 100.0
            return AffordableRent(
                county=county,
                ami_pct=ami_pct,
                bedrooms=bedrooms,
                household_size=bedrooms + 2,
                income_limit=50000 * ami_factor,
                max_rent_with_utilities=base_rent * ami_factor + 150,
                max_rent_no_utilities=base_rent * ami_factor,
                utility_allowance=150.0
            )

        mock_ami_calculator.calculate_max_rent = mock_calculate_max_rent

        # Estimate revenue
        projection = await estimate_revenue(
            inputs=sample_revenue_inputs,
            total_buildable_sqft=60_000,
            assessed_value=15_000_000,
            assumptions=sample_economic_assumptions,
            hud_client=mock_hud_client,
            ami_calculator=mock_ami_calculator,
            include_projections=True,
            projection_years=10
        )

        # Verify structure
        assert projection.gross_potential_income > 0
        assert projection.effective_gross_income < projection.gross_potential_income
        assert projection.net_operating_income < projection.effective_gross_income
        assert projection.vacancy_loss > 0

        # Verify per-unit metrics
        assert projection.gpi_per_unit == pytest.approx(
            projection.gross_potential_income / sample_revenue_inputs.total_units
        )
        assert projection.noi_per_unit == pytest.approx(
            projection.net_operating_income / sample_revenue_inputs.total_units
        )

        # Verify rents
        assert "1br" in projection.market_rents
        assert "2br" in projection.market_rents
        assert "1br" in projection.affordable_rents
        assert "2br" in projection.affordable_rents

        # Verify projections
        assert projection.projections is not None
        assert len(projection.projections) == 10

        # Verify source notes
        assert "fmr_source" in projection.source_notes
        assert "ami_source" in projection.source_notes
        assert projection.source_notes["safmr_used"] is True

    @pytest.mark.asyncio
    async def test_estimate_revenue_no_projections(
        self,
        sample_revenue_inputs,
        sample_economic_assumptions,
        sample_fmr_data
    ):
        """Test revenue estimation without multi-year projections."""
        mock_hud_client = Mock()
        mock_hud_client.get_fmr_by_zip = AsyncMock(return_value=sample_fmr_data)
        mock_hud_client.get_fmr_for_bedroom = lambda data, br: 2500.0

        mock_ami_calculator = Mock(spec=AMICalculator)
        mock_ami_calculator.calculate_max_rent = Mock(
            return_value=AffordableRent(
                county="Los Angeles",
                ami_pct=50.0,
                bedrooms=1,
                household_size=3,
                income_limit=50000,
                max_rent_with_utilities=1400,
                max_rent_no_utilities=1250,
                utility_allowance=150
            )
        )

        projection = await estimate_revenue(
            inputs=sample_revenue_inputs,
            total_buildable_sqft=60_000,
            assessed_value=15_000_000,
            assumptions=sample_economic_assumptions,
            hud_client=mock_hud_client,
            ami_calculator=mock_ami_calculator,
            include_projections=False
        )

        # Should not include projections
        assert projection.projections is None


class TestSourceNotesDocumentation:
    """Tests for source notes and documentation."""

    @pytest.mark.asyncio
    async def test_source_notes_completeness(
        self,
        sample_revenue_inputs,
        sample_economic_assumptions,
        sample_fmr_data
    ):
        """Test that source notes document all key assumptions."""
        mock_hud_client = Mock()
        mock_hud_client.get_fmr_by_zip = AsyncMock(return_value=sample_fmr_data)
        mock_hud_client.get_fmr_for_bedroom = lambda data, br: 2500.0

        mock_ami_calculator = Mock(spec=AMICalculator)
        mock_ami_calculator.calculate_max_rent = Mock(
            return_value=AffordableRent(
                county="Los Angeles",
                ami_pct=50.0,
                bedrooms=1,
                household_size=3,
                income_limit=50000,
                max_rent_with_utilities=1400,
                max_rent_no_utilities=1250,
                utility_allowance=150
            )
        )

        projection = await estimate_revenue(
            inputs=sample_revenue_inputs,
            total_buildable_sqft=60_000,
            assessed_value=15_000_000,
            assumptions=sample_economic_assumptions,
            hud_client=mock_hud_client,
            ami_calculator=mock_ami_calculator
        )

        # Verify source notes
        notes = projection.source_notes

        # Must document FMR source
        assert "fmr_source" in notes
        assert "Los Angeles" in notes["fmr_source"]

        # Must document methodology
        assert "fmr_methodology" in notes
        assert "40th percentile" in notes["fmr_methodology"]

        # Must document SAFMR usage
        assert "safmr_used" in notes
        assert notes["safmr_used"] is True

        # Must document quality factor
        assert "quality_factor" in notes

        # Must document AMI source
        assert "ami_source" in notes

        # Must document assumptions
        assert "vacancy_assumption" in notes
        assert "tax_rate" in notes
        assert "expense_assumptions" in notes
        assert "growth_rates" in notes
