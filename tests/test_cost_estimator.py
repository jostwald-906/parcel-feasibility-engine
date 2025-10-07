"""
Tests for Construction Cost Estimator Service.

Tests cover:
- Hard costs calculation accuracy
- Soft costs breakdown
- Escalation factors (PPI, ECI)
- Construction financing calculation
- Source notes completeness
- CCCI fallback path
- Property tests (costs increase with inputs)
- Error handling
"""
import pytest
from app.services.cost_estimator import (
    estimate_construction_cost,
    calculate_construction_type_factor,
    calculate_construction_financing,
    get_escalation_factor,
    get_wage_escalation_factor,
    get_construction_financing_rate,
)
from app.models.financial import ConstructionInputs, EconomicAssumptions
from app.services.fred_client import FredClient, FredObservation
from app.core.config import settings
from datetime import date as date_type
from unittest.mock import Mock, patch
import pytest_asyncio


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def basic_inputs():
    """Basic construction inputs for testing."""
    return ConstructionInputs(
        buildable_sqft=10000.0,
        num_units=10,
        construction_type="wood_frame",
        location_factor=2.3,
        permit_fees_per_unit=5000.0,
        construction_duration_months=18,
    )


@pytest.fixture
def default_assumptions():
    """Default economic assumptions."""
    return EconomicAssumptions(
        use_wage_adjustment=False,
        use_ccci=False,
    )


@pytest.fixture
def mock_fred_client():
    """Mock FRED client with baseline data."""
    client = Mock(spec=FredClient)

    # Mock PPI observation (WPUSI012011)
    client.get_latest_observation.side_effect = lambda series_id: {
        "WPUSI012011": FredObservation(
            date=date_type(2025, 1, 15),
            value=140.5,
            series_id="WPUSI012011",
        ),
        "ECICONWAG": FredObservation(
            date=date_type(2024, 12, 31),
            value=145.2,
            series_id="ECICONWAG",
        ),
        "DGS10": FredObservation(
            date=date_type(2025, 1, 15),
            value=4.25,
            series_id="DGS10",
        ),
    }[series_id]

    return client


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestConstructionTypeFactors:
    """Tests for construction type cost multipliers."""

    def test_wood_frame_baseline(self):
        """Wood frame should be baseline (1.0x)."""
        factor = calculate_construction_type_factor("wood_frame")
        assert factor == 1.0

    def test_concrete_premium(self):
        """Concrete should be 25% premium."""
        factor = calculate_construction_type_factor("concrete")
        assert factor == 1.25

    def test_steel_premium(self):
        """Steel should be 15% premium."""
        factor = calculate_construction_type_factor("steel")
        assert factor == 1.15

    def test_unknown_type_defaults_to_baseline(self):
        """Unknown construction type should default to 1.0."""
        factor = calculate_construction_type_factor("unknown_type")
        assert factor == 1.0


class TestConstructionFinancing:
    """Tests for construction loan interest calculation."""

    def test_basic_calculation(self):
        """Test basic construction financing calculation."""
        # $1,000,000 principal, 6.5% rate, 1.5 years
        interest = calculate_construction_financing(
            principal=1000000,
            annual_rate=0.065,
            duration_years=1.5,
        )

        # Expected: $1M × 0.065 × 1.5 / 2 = $48,750
        expected = 1000000 * 0.065 * 1.5 / 2
        assert interest == pytest.approx(expected, rel=0.01)

    def test_zero_duration_zero_cost(self):
        """Zero duration should result in zero financing cost."""
        interest = calculate_construction_financing(1000000, 0.065, 0.0)
        assert interest == 0.0

    def test_zero_rate_zero_cost(self):
        """Zero interest rate should result in zero financing cost."""
        interest = calculate_construction_financing(1000000, 0.0, 1.5)
        assert interest == 0.0

    def test_higher_rate_higher_cost(self):
        """Higher interest rate should result in higher cost."""
        low_rate = calculate_construction_financing(1000000, 0.050, 1.5)
        high_rate = calculate_construction_financing(1000000, 0.080, 1.5)
        assert high_rate > low_rate


# =============================================================================
# Test Escalation Factors
# =============================================================================


@pytest.mark.asyncio
class TestEscalationFactors:
    """Tests for cost escalation factor calculations."""

    async def test_ppi_escalation_calculation(self, mock_fred_client):
        """Test PPI-based materials escalation."""
        escalation, note = await get_escalation_factor(mock_fred_client)

        # Expected: 140.5 / 140.0 = 1.0036
        expected_escalation = 140.5 / settings.REF_PPI_VALUE
        assert escalation == pytest.approx(expected_escalation, rel=0.001)
        assert "WPUSI012011" in note
        assert "140.5" in note

    async def test_wage_escalation_calculation(self, mock_fred_client):
        """Test wage escalation from ECI data."""
        wage_factor, note = await get_wage_escalation_factor(mock_fred_client)

        # Expected: 145.2 / 125.0 = 1.1616
        expected_factor = 145.2 / 125.0
        assert wage_factor == pytest.approx(expected_factor, rel=0.001)
        assert "ECICONWAG" in note

    async def test_construction_financing_rate(self, mock_fred_client):
        """Test construction financing rate calculation."""
        rate, note = await get_construction_financing_rate(mock_fred_client)

        # Expected: 4.25% + 2.5% spread = 6.75% = 0.0675
        expected_rate = 0.0425 + settings.CONSTRUCTION_LOAN_SPREAD
        assert rate == pytest.approx(expected_rate, rel=0.001)
        assert "DGS10" in note
        assert "4.25" in note

    async def test_ppi_fallback_on_error(self):
        """Test fallback to 1.0 when FRED data unavailable."""
        error_client = Mock(spec=FredClient)
        error_client.get_latest_observation.side_effect = Exception("API Error")

        escalation, note = await get_escalation_factor(error_client)

        assert escalation == 1.0
        assert "unavailable" in note.lower()

    async def test_ccci_fallback_not_implemented(self, mock_fred_client):
        """Test CCCI escalation falls back to PPI."""
        escalation, note = await get_escalation_factor(
            mock_fred_client,
            use_ccci=True,
            ccci_client=Mock(),
        )

        # Should fall back to PPI
        assert escalation > 0
        assert "WPUSI012011" in note


# =============================================================================
# Test Full Cost Estimation
# =============================================================================


@pytest.mark.asyncio
class TestFullCostEstimation:
    """Tests for complete cost estimation."""

    async def test_basic_estimate(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test basic cost estimation with default assumptions."""
        estimate = await estimate_construction_cost(
            inputs=basic_inputs,
            assumptions=default_assumptions,
            fred_client=mock_fred_client,
        )

        # Verify structure
        assert estimate.total_cost > 0
        assert estimate.cost_per_unit > 0
        assert estimate.cost_per_buildable_sf > 0

        # Verify breakdowns exist
        assert estimate.hard_costs.total_hard_cost > 0
        assert estimate.soft_costs.total_soft_cost > 0
        assert estimate.contingency_amount > 0

        # Verify totals match
        expected_total = (
            estimate.hard_costs.total_hard_cost
            + estimate.soft_costs.total_soft_cost
            + estimate.contingency_amount
        )
        assert estimate.total_cost == pytest.approx(expected_total, rel=0.01)

    async def test_cost_per_unit_calculation(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test cost per unit is correctly calculated."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        expected_per_unit = estimate.total_cost / basic_inputs.num_units
        assert estimate.cost_per_unit == pytest.approx(expected_per_unit, rel=0.01)

    async def test_cost_per_sf_calculation(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test cost per buildable SF is correctly calculated."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        expected_per_sf = estimate.total_cost / basic_inputs.buildable_sqft
        assert estimate.cost_per_buildable_sf == pytest.approx(expected_per_sf, rel=0.01)

    async def test_hard_costs_include_all_factors(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test hard costs include all escalation and multiplier factors."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        hard = estimate.hard_costs

        # Verify all factors are present
        assert hard.base_cost_per_sf == settings.REF_COST_PER_SF
        assert hard.materials_escalation_factor > 0
        assert hard.wage_escalation_factor == 1.0  # Not enabled in default assumptions
        assert hard.construction_type_factor == 1.0  # Wood frame baseline
        assert hard.location_factor == basic_inputs.location_factor
        assert hard.common_area_factor == settings.COMMON_AREA_FACTOR

    async def test_soft_costs_breakdown(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test soft costs are broken down correctly."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        soft = estimate.soft_costs

        # All components should be positive
        assert soft.architecture_engineering > 0
        assert soft.permits_fees > 0
        assert soft.construction_financing > 0
        assert soft.legal_consulting > 0
        assert soft.developer_fee > 0

        # Total should match sum
        expected_total = (
            soft.architecture_engineering
            + soft.permits_fees
            + soft.construction_financing
            + soft.legal_consulting
            + soft.developer_fee
        )
        assert soft.total_soft_cost == pytest.approx(expected_total, rel=0.01)

    async def test_permits_fees_calculation(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test permit fees are per-unit based."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        expected_permits = basic_inputs.permit_fees_per_unit * basic_inputs.num_units
        assert estimate.soft_costs.permits_fees == pytest.approx(expected_permits, rel=0.01)

    async def test_contingency_calculation(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test contingency is calculated as % of hard + soft."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        subtotal = estimate.hard_costs.total_hard_cost + estimate.soft_costs.total_soft_cost
        expected_contingency = subtotal * settings.CONTINGENCY_PCT

        assert estimate.contingency_amount == pytest.approx(expected_contingency, rel=0.01)
        assert estimate.contingency_pct == settings.CONTINGENCY_PCT


# =============================================================================
# Test Source Notes
# =============================================================================


@pytest.mark.asyncio
class TestSourceNotes:
    """Tests for source notes transparency."""

    async def test_source_notes_completeness(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test all required source notes are present."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        notes = estimate.source_notes

        # Required notes
        required_keys = [
            "base_cost_per_sf",
            "materials_ppi_series",
            "location_factor",
            "construction_type",
            "total_buildable_sf",
            "interest_rate",
        ]

        for key in required_keys:
            assert key in notes, f"Missing source note: {key}"
            assert notes[key], f"Empty source note: {key}"

    async def test_ppi_note_includes_fred_data(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test PPI note includes FRED series and date."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        ppi_note = estimate.source_notes["materials_ppi_series"]
        assert "WPUSI012011" in ppi_note
        assert "FRED" in ppi_note
        assert "140.5" in ppi_note

    async def test_wage_note_when_enabled(self, basic_inputs, mock_fred_client):
        """Test wage escalation note when wage adjustment enabled."""
        assumptions = EconomicAssumptions(use_wage_adjustment=True)
        estimate = await estimate_construction_cost(
            basic_inputs, assumptions, mock_fred_client
        )

        wage_note = estimate.source_notes["wage_eci_series"]
        assert "ECICONWAG" in wage_note

    async def test_wage_note_when_disabled(self, basic_inputs, default_assumptions, mock_fred_client):
        """Test wage note when wage adjustment disabled."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        wage_note = estimate.source_notes["wage_eci_series"]
        assert "Not applied" in wage_note


# =============================================================================
# Test Parametric Variations
# =============================================================================


@pytest.mark.asyncio
class TestParametricVariations:
    """Tests for parametric cost variations."""

    async def test_concrete_costs_more_than_wood(self, basic_inputs, default_assumptions, mock_fred_client):
        """Concrete construction should cost more than wood frame."""
        # Wood frame estimate
        wood_inputs = basic_inputs.model_copy()
        wood_inputs.construction_type = "wood_frame"
        wood_estimate = await estimate_construction_cost(
            wood_inputs, default_assumptions, mock_fred_client
        )

        # Concrete estimate
        concrete_inputs = basic_inputs.model_copy()
        concrete_inputs.construction_type = "concrete"
        concrete_estimate = await estimate_construction_cost(
            concrete_inputs, default_assumptions, mock_fred_client
        )

        assert concrete_estimate.total_cost > wood_estimate.total_cost

    async def test_higher_location_factor_increases_cost(
        self, basic_inputs, default_assumptions, mock_fred_client
    ):
        """Higher location factor should increase total cost."""
        # Base location factor (2.3)
        base_estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        # Higher location factor (3.0)
        high_loc_inputs = basic_inputs.model_copy()
        high_loc_inputs.location_factor = 3.0
        high_estimate = await estimate_construction_cost(
            high_loc_inputs, default_assumptions, mock_fred_client
        )

        assert high_estimate.total_cost > base_estimate.total_cost

    async def test_more_units_increases_total_cost(
        self, basic_inputs, default_assumptions, mock_fred_client
    ):
        """More units should increase total cost."""
        # 10 units
        base_estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        # 20 units (double SF to keep density constant)
        more_units_inputs = basic_inputs.model_copy()
        more_units_inputs.num_units = 20
        more_units_inputs.buildable_sqft = 20000
        more_estimate = await estimate_construction_cost(
            more_units_inputs, default_assumptions, mock_fred_client
        )

        assert more_estimate.total_cost > base_estimate.total_cost

    async def test_wage_adjustment_increases_cost(self, basic_inputs, mock_fred_client):
        """Enabling wage adjustment should increase cost."""
        # Without wage adjustment
        no_wage = EconomicAssumptions(use_wage_adjustment=False)
        no_wage_estimate = await estimate_construction_cost(
            basic_inputs, no_wage, mock_fred_client
        )

        # With wage adjustment
        with_wage = EconomicAssumptions(use_wage_adjustment=True)
        with_wage_estimate = await estimate_construction_cost(
            basic_inputs, with_wage, mock_fred_client
        )

        assert with_wage_estimate.total_cost > no_wage_estimate.total_cost

    async def test_longer_construction_increases_financing_cost(
        self, basic_inputs, default_assumptions, mock_fred_client
    ):
        """Longer construction duration should increase financing cost."""
        # 12 months
        short_inputs = basic_inputs.model_copy()
        short_inputs.construction_duration_months = 12
        short_estimate = await estimate_construction_cost(
            short_inputs, default_assumptions, mock_fred_client
        )

        # 24 months
        long_inputs = basic_inputs.model_copy()
        long_inputs.construction_duration_months = 24
        long_estimate = await estimate_construction_cost(
            long_inputs, default_assumptions, mock_fred_client
        )

        assert long_estimate.soft_costs.construction_financing > short_estimate.soft_costs.construction_financing


# =============================================================================
# Test Custom Assumptions
# =============================================================================


@pytest.mark.asyncio
class TestCustomAssumptions:
    """Tests for custom economic assumptions."""

    async def test_custom_architecture_pct(self, basic_inputs, mock_fred_client):
        """Test custom architecture percentage is applied."""
        assumptions = EconomicAssumptions(architecture_pct=0.15)  # 15% instead of default 10%
        estimate = await estimate_construction_cost(
            basic_inputs, assumptions, mock_fred_client
        )

        # Calculate expected architecture cost
        expected_arch = estimate.hard_costs.total_hard_cost * 0.15
        assert estimate.soft_costs.architecture_engineering == pytest.approx(expected_arch, rel=0.01)

    async def test_custom_contingency_pct(self, basic_inputs, mock_fred_client):
        """Test custom contingency percentage is applied."""
        assumptions = EconomicAssumptions(contingency_pct=0.20)  # 20% instead of default 12%
        estimate = await estimate_construction_cost(
            basic_inputs, assumptions, mock_fred_client
        )

        subtotal = estimate.hard_costs.total_hard_cost + estimate.soft_costs.total_soft_cost
        expected_contingency = subtotal * 0.20

        assert estimate.contingency_amount == pytest.approx(expected_contingency, rel=0.01)
        assert estimate.contingency_pct == 0.20


# =============================================================================
# Test Error Handling
# =============================================================================


@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling and edge cases."""

    async def test_handles_fred_api_failure_gracefully(self, basic_inputs, default_assumptions):
        """Test graceful handling of FRED API failures."""
        error_client = Mock(spec=FredClient)
        error_client.get_latest_observation.side_effect = Exception("API Error")

        # Should not raise, should use fallback values
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, error_client
        )

        assert estimate.total_cost > 0
        assert "unavailable" in estimate.source_notes["materials_ppi_series"].lower()

    async def test_creates_fred_client_if_not_provided(self, basic_inputs, default_assumptions):
        """Test FRED client is created if not provided."""
        # Don't provide fred_client
        estimate = await estimate_construction_cost(basic_inputs, default_assumptions)

        assert estimate.total_cost > 0
        assert estimate.source_notes is not None


# =============================================================================
# Property-Based Tests
# =============================================================================


@pytest.mark.asyncio
class TestCostProperties:
    """Property-based tests for cost estimation."""

    async def test_cost_proportional_to_square_footage(
        self, default_assumptions, mock_fred_client
    ):
        """Total cost should be roughly proportional to square footage."""
        inputs_5k = ConstructionInputs(
            buildable_sqft=5000,
            num_units=5,
            construction_type="wood_frame",
            location_factor=2.3,
            permit_fees_per_unit=5000,
            construction_duration_months=18,
        )

        inputs_10k = ConstructionInputs(
            buildable_sqft=10000,
            num_units=10,
            construction_type="wood_frame",
            location_factor=2.3,
            permit_fees_per_unit=5000,
            construction_duration_months=18,
        )

        estimate_5k = await estimate_construction_cost(
            inputs_5k, default_assumptions, mock_fred_client
        )
        estimate_10k = await estimate_construction_cost(
            inputs_10k, default_assumptions, mock_fred_client
        )

        # Cost should roughly double (within 10% tolerance due to fixed soft costs)
        ratio = estimate_10k.total_cost / estimate_5k.total_cost
        assert 1.8 < ratio < 2.2

    async def test_hard_costs_always_exceed_soft_costs(
        self, basic_inputs, default_assumptions, mock_fred_client
    ):
        """Hard costs should always be greater than soft costs."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        assert estimate.hard_costs.total_hard_cost > estimate.soft_costs.total_soft_cost

    async def test_total_cost_equals_sum_of_parts(
        self, basic_inputs, default_assumptions, mock_fred_client
    ):
        """Total cost must equal sum of hard + soft + contingency."""
        estimate = await estimate_construction_cost(
            basic_inputs, default_assumptions, mock_fred_client
        )

        sum_of_parts = (
            estimate.hard_costs.total_hard_cost
            + estimate.soft_costs.total_soft_cost
            + estimate.contingency_amount
        )

        assert estimate.total_cost == pytest.approx(sum_of_parts, abs=1.0)  # Allow $1 rounding
