"""
Tests for economic feasibility Pydantic models.

Validates model structure, validation rules, and JSON serialization.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.economic_feasibility import (
    EconomicAssumptions,
    ConstructionInputs,
    ConstructionCostEstimate,
    RevenueInputs,
    RevenueProjection,
    TimelineInputs,
    CashFlow,
    FinancialMetrics,
    SensitivityInput,
    TornadoResult,
    MonteCarloInputs,
    MonteCarloResult,
    SensitivityAnalysis,
    FeasibilityAnalysis,
    FeasibilityRequest,
)


class TestEconomicAssumptions:
    """Tests for EconomicAssumptions model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        assumptions = EconomicAssumptions()

        assert assumptions.discount_rate == 0.12
        assert assumptions.cap_rate == 0.045
        assert assumptions.location_factor == 1.0
        assert assumptions.quality_factor == 1.0
        assert assumptions.vacancy_rate == 0.07
        assert assumptions.tax_rate == 0.012
        assert assumptions.rent_growth_rate == 0.03
        assert assumptions.expense_growth_rate == 0.025
        assert assumptions.use_ccci is False

    def test_custom_values(self):
        """Test custom values can be set."""
        assumptions = EconomicAssumptions(
            discount_rate=0.15,
            risk_free_rate=0.035,
            location_factor=1.3,
            cap_rate=0.05
        )

        assert assumptions.discount_rate == 0.15
        assert assumptions.risk_free_rate == 0.035
        assert assumptions.location_factor == 1.3
        assert assumptions.cap_rate == 0.05

    def test_validation_discount_rate_range(self):
        """Test discount rate must be within 1%-30%."""
        # Valid
        EconomicAssumptions(discount_rate=0.01)
        EconomicAssumptions(discount_rate=0.30)

        # Invalid - too low
        with pytest.raises(ValidationError):
            EconomicAssumptions(discount_rate=0.0)

        # Invalid - too high
        with pytest.raises(ValidationError):
            EconomicAssumptions(discount_rate=0.35)

    def test_validation_location_factor_range(self):
        """Test location factor must be within 0.5-2.0."""
        # Valid
        EconomicAssumptions(location_factor=0.5)
        EconomicAssumptions(location_factor=2.0)

        # Invalid
        with pytest.raises(ValidationError):
            EconomicAssumptions(location_factor=0.4)

        with pytest.raises(ValidationError):
            EconomicAssumptions(location_factor=2.5)

    def test_source_references_defaults(self):
        """Test source references are populated with defaults."""
        assumptions = EconomicAssumptions()

        assert "risk_free_rate" in assumptions.source_references
        assert "FRED DGS10" in assumptions.source_references["risk_free_rate"]
        assert "location_factor" in assumptions.source_references


class TestConstructionInputs:
    """Tests for ConstructionInputs model."""

    def test_valid_inputs(self):
        """Test valid construction inputs."""
        inputs = ConstructionInputs(
            total_buildable_sf=25000.0,
            num_units=30,
            construction_type="wood_frame",
            construction_duration_months=18,
            predevelopment_duration_months=12
        )

        assert inputs.total_buildable_sf == 25000.0
        assert inputs.num_units == 30
        assert inputs.construction_type == "wood_frame"
        assert inputs.permit_fees_per_unit == 15000.0  # Default

    def test_construction_type_validation(self):
        """Test construction type must be valid."""
        # Valid types
        for ctype in ["wood_frame", "concrete", "steel"]:
            inputs = ConstructionInputs(
                total_buildable_sf=10000,
                num_units=10,
                construction_type=ctype,
                construction_duration_months=12,
                predevelopment_duration_months=6
            )
            assert inputs.construction_type == ctype

        # Invalid type
        with pytest.raises(ValidationError):
            ConstructionInputs(
                total_buildable_sf=10000,
                num_units=10,
                construction_type="brick",
                construction_duration_months=12,
                predevelopment_duration_months=6
            )

    def test_positive_values_required(self):
        """Test buildable_sf and num_units must be > 0."""
        with pytest.raises(ValidationError):
            ConstructionInputs(
                total_buildable_sf=0,
                num_units=10,
                construction_type="wood_frame",
                construction_duration_months=12,
                predevelopment_duration_months=6
            )

        with pytest.raises(ValidationError):
            ConstructionInputs(
                total_buildable_sf=10000,
                num_units=0,
                construction_type="wood_frame",
                construction_duration_months=12,
                predevelopment_duration_months=6
            )


class TestRevenueInputs:
    """Tests for RevenueInputs model."""

    def test_valid_inputs(self):
        """Test valid revenue inputs."""
        inputs = RevenueInputs(
            parcel_zip="90401",
            county="Los Angeles",
            market_units=25,
            affordable_units=5,
            unit_mix={0: 5, 1: 15, 2: 8, 3: 2}
        )

        assert inputs.parcel_zip == "90401"
        assert inputs.county == "Los Angeles"
        assert inputs.market_units == 25
        assert inputs.affordable_units == 5
        assert sum(inputs.unit_mix.values()) == 30

    def test_zip_code_validation(self):
        """Test ZIP code must be 5 digits."""
        # Valid
        RevenueInputs(
            parcel_zip="90401",
            county="Los Angeles",
            market_units=10,
            affordable_units=0,
            unit_mix={1: 10}
        )

        # Invalid - 9 digits (ZIP+4)
        with pytest.raises(ValidationError):
            RevenueInputs(
                parcel_zip="90401-1234",
                county="Los Angeles",
                market_units=10,
                affordable_units=0,
                unit_mix={1: 10}
            )

        # Invalid - 4 digits
        with pytest.raises(ValidationError):
            RevenueInputs(
                parcel_zip="9040",
                county="Los Angeles",
                market_units=10,
                affordable_units=0,
                unit_mix={1: 10}
            )

    def test_unit_mix_validation(self):
        """Test unit mix bedroom counts must be 0-5."""
        # Valid - studio (0BR) through 4BR
        RevenueInputs(
            parcel_zip="90401",
            county="Los Angeles",
            market_units=10,
            affordable_units=0,
            unit_mix={0: 2, 1: 3, 2: 3, 3: 1, 4: 1}
        )

        # Invalid - negative bedrooms
        with pytest.raises(ValidationError):
            RevenueInputs(
                parcel_zip="90401",
                county="Los Angeles",
                market_units=10,
                affordable_units=0,
                unit_mix={-1: 5, 1: 5}
            )

        # Invalid - 6 bedrooms (too many)
        with pytest.raises(ValidationError):
            RevenueInputs(
                parcel_zip="90401",
                county="Los Angeles",
                market_units=10,
                affordable_units=0,
                unit_mix={6: 10}
            )


class TestTimelineInputs:
    """Tests for TimelineInputs model."""

    def test_valid_timeline(self):
        """Test valid timeline inputs."""
        timeline = TimelineInputs(
            predevelopment_months=12,
            construction_months=18,
            lease_up_months=6,
            operating_years=10
        )

        assert timeline.predevelopment_months == 12
        assert timeline.construction_months == 18
        assert timeline.lease_up_months == 6
        assert timeline.operating_years == 10

    def test_positive_values_required(self):
        """Test all timeline values must be > 0."""
        with pytest.raises(ValidationError):
            TimelineInputs(
                predevelopment_months=0,
                construction_months=18,
                lease_up_months=6
            )


class TestCashFlow:
    """Tests for CashFlow model."""

    def test_valid_cash_flow(self):
        """Test valid cash flow period."""
        cf = CashFlow(
            period=0,
            period_type="predevelopment",
            revenue=0.0,
            operating_expenses=0.0,
            capital_expenditure=500000.0,
            net_cash_flow=-500000.0,
            cumulative_cash_flow=-500000.0
        )

        assert cf.period == 0
        assert cf.period_type == "predevelopment"
        assert cf.net_cash_flow == -500000.0

    def test_period_type_validation(self):
        """Test period type must be valid."""
        # Valid types
        for ptype in ["predevelopment", "construction", "lease_up", "operations"]:
            CashFlow(
                period=0,
                period_type=ptype,
                net_cash_flow=0.0,
                cumulative_cash_flow=0.0
            )

        # Invalid type
        with pytest.raises(ValidationError):
            CashFlow(
                period=0,
                period_type="invalid",
                net_cash_flow=0.0,
                cumulative_cash_flow=0.0
            )


class TestMonteCarloInputs:
    """Tests for MonteCarloInputs model."""

    def test_valid_inputs(self):
        """Test valid Monte Carlo inputs."""
        inputs = MonteCarloInputs(
            iterations=10000,
            cost_per_sf_std=30.0,
            rent_growth_std=0.01,
            cap_rate_min=0.04,
            cap_rate_mode=0.045,
            cap_rate_max=0.06,
            delay_months_mean=0.0,
            delay_months_std=3.0,
            random_seed=42
        )

        assert inputs.iterations == 10000
        assert inputs.random_seed == 42

    def test_iteration_bounds(self):
        """Test iterations must be 1000-100000."""
        # Valid
        MonteCarloInputs(
            iterations=1000,
            cost_per_sf_std=30.0,
            rent_growth_std=0.01,
            cap_rate_min=0.04,
            cap_rate_mode=0.045,
            cap_rate_max=0.06
        )

        # Invalid - too few
        with pytest.raises(ValidationError):
            MonteCarloInputs(
                iterations=500,
                cost_per_sf_std=30.0,
                rent_growth_std=0.01,
                cap_rate_min=0.04,
                cap_rate_mode=0.045,
                cap_rate_max=0.06
            )


class TestFeasibilityRequest:
    """Tests for FeasibilityRequest model."""

    def test_valid_request(self):
        """Test valid feasibility request."""
        request = FeasibilityRequest(
            parcel_apn="4293-021-012",
            scenario_name="SB 9 Lot Split",
            units=30,
            buildable_sf=25000.0,
            timeline=TimelineInputs(
                predevelopment_months=12,
                construction_months=18,
                lease_up_months=6
            )
        )

        assert request.parcel_apn == "4293-021-012"
        assert request.scenario_name == "SB 9 Lot Split"
        assert request.units == 30
        assert request.buildable_sf == 25000.0
        assert request.run_sensitivity is True  # Default
        assert request.run_monte_carlo is True  # Default

    def test_uses_default_assumptions(self):
        """Test request uses default economic assumptions if not provided."""
        request = FeasibilityRequest(
            parcel_apn="4293-021-012",
            scenario_name="Test",
            units=10,
            buildable_sf=10000.0,
            timeline=TimelineInputs(
                predevelopment_months=12,
                construction_months=18,
                lease_up_months=6
            )
        )

        # Should have default assumptions
        assert request.assumptions.discount_rate == 0.12
        assert request.assumptions.cap_rate == 0.045

    def test_custom_assumptions(self):
        """Test custom assumptions can be provided."""
        request = FeasibilityRequest(
            parcel_apn="4293-021-012",
            scenario_name="Test",
            units=10,
            buildable_sf=10000.0,
            timeline=TimelineInputs(
                predevelopment_months=12,
                construction_months=18,
                lease_up_months=6
            ),
            assumptions=EconomicAssumptions(
                discount_rate=0.15,
                location_factor=1.35
            )
        )

        assert request.assumptions.discount_rate == 0.15
        assert request.assumptions.location_factor == 1.35


class TestJSONSerialization:
    """Tests for JSON serialization of models."""

    def test_economic_assumptions_serialization(self):
        """Test EconomicAssumptions can be serialized to JSON."""
        assumptions = EconomicAssumptions(
            discount_rate=0.15,
            location_factor=1.3
        )

        json_data = assumptions.model_dump()
        assert json_data["discount_rate"] == 0.15
        assert json_data["location_factor"] == 1.3

        # Test round-trip
        assumptions2 = EconomicAssumptions(**json_data)
        assert assumptions2.discount_rate == 0.15

    def test_feasibility_request_serialization(self):
        """Test FeasibilityRequest can be serialized and deserialized."""
        request = FeasibilityRequest(
            parcel_apn="4293-021-012",
            scenario_name="Test",
            units=30,
            buildable_sf=25000.0,
            timeline=TimelineInputs(
                predevelopment_months=12,
                construction_months=18,
                lease_up_months=6
            ),
            assumptions=EconomicAssumptions(discount_rate=0.15)
        )

        # Serialize to dict
        json_data = request.model_dump()
        assert json_data["parcel_apn"] == "4293-021-012"
        assert json_data["assumptions"]["discount_rate"] == 0.15

        # Deserialize back
        request2 = FeasibilityRequest(**json_data)
        assert request2.parcel_apn == "4293-021-012"
        assert request2.assumptions.discount_rate == 0.15

    def test_feasibility_analysis_datetime_serialization(self):
        """Test FeasibilityAnalysis serializes datetime correctly."""
        from app.models.economic_feasibility import (
            ConstructionCostEstimate,
            RevenueProjection,
            FinancialMetrics,
            SensitivityAnalysis,
            MonteCarloResult
        )

        analysis = FeasibilityAnalysis(
            scenario_name="Test",
            parcel_apn="4293-021-012",
            construction_cost_estimate=ConstructionCostEstimate(
                hard_costs=6000000.0,
                soft_costs=1500000.0,
                architecture_engineering=420000.0,
                permits_and_fees=450000.0,
                construction_financing=300000.0,
                legal_consulting=180000.0,
                contingency=450000.0,
                total_cost=7500000.0,
                cost_per_unit=250000.0,
                cost_per_sf=300.0
            ),
            revenue_projection=RevenueProjection(
                annual_gross_income=900000.0,
                vacancy_loss=63000.0,
                effective_gross_income=837000.0,
                operating_expenses=270000.0,
                annual_noi=567000.0,
                noi_per_unit=18900.0
            ),
            financial_metrics=FinancialMetrics(
                npv=2500000.0,
                irr=0.18,
                payback_period_years=7.5,
                profitability_index=1.33,
                return_on_cost=0.075,
                exit_value=12600000.0
            ),
            sensitivity_analysis=SensitivityAnalysis(
                tornado=[],
                monte_carlo=MonteCarloResult(
                    probability_npv_positive=0.87,
                    mean_npv=2300000.0,
                    std_npv=800000.0,
                    percentiles={
                        "p10": 800000.0,
                        "p25": 1500000.0,
                        "p50": 2250000.0,
                        "p75": 3100000.0,
                        "p90": 3800000.0
                    }
                )
            ),
            decision_recommendation="Recommended - Strong Feasibility",
            analysis_timestamp=datetime(2025, 1, 15, 10, 30, 0)
        )

        # Serialize to JSON-compatible dict
        json_data = analysis.model_dump()

        # Check datetime is serialized as ISO string
        assert isinstance(json_data["analysis_timestamp"], datetime)

        # Use model_dump_json for actual JSON string
        json_str = analysis.model_dump_json()
        assert "2025-01-15" in json_str


class TestModelExamples:
    """Test that model examples are valid."""

    def test_economic_assumptions_example(self):
        """Test EconomicAssumptions example is valid."""
        example = EconomicAssumptions.model_config["json_schema_extra"]["example"]
        assumptions = EconomicAssumptions(**example)
        assert assumptions.discount_rate == 0.12

    def test_construction_inputs_example(self):
        """Test ConstructionInputs example is valid."""
        example = ConstructionInputs.model_config["json_schema_extra"]["example"]
        inputs = ConstructionInputs(**example)
        assert inputs.num_units == 30

    def test_revenue_inputs_example(self):
        """Test RevenueInputs example is valid."""
        example = RevenueInputs.model_config["json_schema_extra"]["example"]
        inputs = RevenueInputs(**example)
        assert inputs.parcel_zip == "90401"

    def test_feasibility_request_example(self):
        """Test FeasibilityRequest example is valid."""
        example = FeasibilityRequest.model_config["json_schema_extra"]["example"]
        request = FeasibilityRequest(**example)
        assert request.units == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
