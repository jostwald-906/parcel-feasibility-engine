"""
Tests for Economic Feasibility API endpoints.

Test Coverage:
- POST /compute: Full feasibility analysis
- GET /cost-indices: FRED cost index retrieval
- GET /market-rents/{zip_code}: HUD FMR retrieval
- POST /assumptions/validate: Assumption validation
- GET /defaults: Smart default generation
- Error handling for all endpoints
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.economic_feasibility import (
    FeasibilityRequest,
    EconomicAssumptions,
    Timeline,
    CostIndicesResponse,
    MarketRentResponse,
)


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture
def sample_feasibility_request():
    """Sample feasibility request for testing."""
    return {
        "parcel_apn": "4293-001-015",
        "scenario_name": "Base Zoning",
        "units": 20,
        "buildable_sf": 18000,
        "zip_code": "90401",
        "county": "Los Angeles",
        "timeline": {
            "predevelopment_months": 12,
            "construction_months": 24,
            "lease_up_months": 6,
            "operating_years": 10
        },
        "assumptions": {
            "discount_rate": 0.12,
            "cap_rate": 0.05,
            "quality_factor": 1.0,
            "location_factor": 2.1,
            "property_tax_rate": 0.0125,
            "operating_expense_ratio": 0.35,
            "vacancy_rate": 0.05,
            "annual_rent_growth": 0.03,
            "annual_expense_growth": 0.025
        },
        "run_sensitivity": True,
        "run_monte_carlo": False
    }


@pytest.fixture
def sample_economic_assumptions():
    """Sample economic assumptions for testing."""
    return {
        "discount_rate": 0.12,
        "cap_rate": 0.05,
        "quality_factor": 1.0,
        "location_factor": 2.1,
        "property_tax_rate": 0.0125,
        "operating_expense_ratio": 0.35,
        "vacancy_rate": 0.05,
        "annual_rent_growth": 0.03,
        "annual_expense_growth": 0.025
    }


class TestComputeFeasibility:
    """Tests for POST /compute endpoint."""

    @pytest.mark.skip(reason="Requires FRED/HUD client implementation")
    @patch('app.api.economic_feasibility.EconomicFeasibilityCalculator')
    async def test_compute_feasibility_success(
        self, mock_calculator_class, client, sample_feasibility_request
    ):
        """Test successful feasibility analysis computation."""
        # Mock calculator instance
        mock_calculator = Mock()
        mock_calculator.compute_feasibility = AsyncMock(return_value={
            "parcel_apn": "4293-001-015",
            "scenario_name": "Base Zoning",
            "analysis_date": datetime.now().isoformat(),
            "npv": 2450000.0,
            "irr": 0.185,
            "profitability_index": 1.45,
            "payback_years": 6.2,
            "recommendation": "Proceed",
            "data_sources": {}
        })
        mock_calculator_class.return_value = mock_calculator

        # Make request
        response = client.post(
            "/api/v1/economic-feasibility/compute",
            json=sample_feasibility_request
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["npv"] == 2450000.0
        assert data["irr"] == 0.185
        assert data["recommendation"] == "Proceed"

    def test_compute_feasibility_invalid_request(self, client):
        """Test compute with invalid request data."""
        invalid_request = {
            "parcel_apn": "TEST",
            "scenario_name": "Test",
            # Missing required fields
        }

        response = client.post(
            "/api/v1/economic-feasibility/compute",
            json=invalid_request
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.skip(reason="Requires data source mocking")
    def test_compute_feasibility_data_source_error(self, client, sample_feasibility_request):
        """Test handling of data source unavailability."""
        with patch('app.services.fred_client.FredClient') as mock_fred:
            mock_fred.return_value.get_current_indices.side_effect = Exception("FRED API unavailable")

            response = client.post(
                "/api/v1/economic-feasibility/compute",
                json=sample_feasibility_request
            )

            assert response.status_code == 503
            data = response.json()
            assert "Data source unavailable" in data["detail"]["error"]


class TestCostIndices:
    """Tests for GET /cost-indices endpoint."""

    @pytest.mark.skip(reason="Requires FRED client implementation")
    @patch('app.api.economic_feasibility.get_fred_client')
    async def test_get_cost_indices_success(self, mock_get_client, client):
        """Test successful cost indices retrieval."""
        # Mock FRED client
        mock_client = AsyncMock()
        mock_client.get_current_indices = AsyncMock(return_value=CostIndicesResponse(
            as_of_date="2025-09-30",
            materials_ppi=315.2,
            construction_wages_eci=142.8,
            risk_free_rate_pct=4.15,
            data_source="Federal Reserve Economic Data (FRED)",
            series_ids={
                "materials": "WPUSI012011",
                "wages": "ECICONWAG",
                "risk_free_rate": "DGS10"
            }
        ))
        mock_get_client.return_value = mock_client

        response = client.get("/api/v1/economic-feasibility/cost-indices")

        assert response.status_code == 200
        data = response.json()
        assert "materials_ppi" in data
        assert "construction_wages_eci" in data
        assert "risk_free_rate_pct" in data

    @pytest.mark.skip(reason="Requires FRED client implementation")
    def test_get_cost_indices_fred_unavailable(self, client):
        """Test cost indices when FRED API is unavailable."""
        with patch('app.services.fred_client.FredClient') as mock_fred:
            mock_fred.return_value.get_current_indices.side_effect = Exception("API timeout")

            response = client.get("/api/v1/economic-feasibility/cost-indices")

            assert response.status_code == 503


class TestMarketRents:
    """Tests for GET /market-rents/{zip_code} endpoint."""

    @pytest.mark.skip(reason="Requires HUD client implementation")
    @patch('app.api.economic_feasibility.get_hud_client')
    async def test_get_market_rents_success(self, mock_get_client, client):
        """Test successful market rent retrieval."""
        # Mock HUD client
        mock_client = AsyncMock()
        mock_client.get_fmr_by_zip = AsyncMock(return_value=MarketRentResponse(
            zip_code="90401",
            year=2025,
            rents_by_bedroom={
                "0": 1850.0,
                "1": 2100.0,
                "2": 2650.0,
                "3": 3450.0,
                "4": 4100.0
            },
            fmr_type="SAFMR",
            metro_area="Los Angeles-Long Beach-Anaheim, CA",
            data_source="HUD FMR 2025",
            effective_date="2024-10-01"
        ))
        mock_get_client.return_value = mock_client

        response = client.get("/api/v1/economic-feasibility/market-rents/90401")

        assert response.status_code == 200
        data = response.json()
        assert data["zip_code"] == "90401"
        assert "rents_by_bedroom" in data
        assert data["fmr_type"] == "SAFMR"

    def test_get_market_rents_invalid_zip(self, client):
        """Test market rents with invalid ZIP code."""
        response = client.get("/api/v1/economic-feasibility/market-rents/INVALID")

        assert response.status_code == 422
        data = response.json()
        assert "ZIP code must be 5 digits" in data["detail"]

    @pytest.mark.skip(reason="Requires HUD client implementation")
    def test_get_market_rents_not_found(self, client):
        """Test market rents for ZIP not in database."""
        with patch('app.services.hud_fmr_client.HudFMRClient') as mock_hud:
            mock_hud.return_value.get_fmr_by_zip.return_value = None

            response = client.get("/api/v1/economic-feasibility/market-rents/99999")

            assert response.status_code == 404


class TestValidateAssumptions:
    """Tests for POST /assumptions/validate endpoint."""

    def test_validate_assumptions_valid(self, client, sample_economic_assumptions):
        """Test validation with valid assumptions."""
        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert isinstance(data["warnings"], list)
        assert isinstance(data["errors"], list)

    def test_validate_assumptions_discount_rate_too_low(self, client, sample_economic_assumptions):
        """Test validation with discount rate too low."""
        sample_economic_assumptions["discount_rate"] = 0.02  # 2% (too low)

        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert any("at least 5%" in error for error in data["errors"])

    def test_validate_assumptions_discount_rate_too_high(self, client, sample_economic_assumptions):
        """Test validation with discount rate too high."""
        sample_economic_assumptions["discount_rate"] = 0.30  # 30% (too high)

        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert any("exceeds 25%" in error for error in data["errors"])

    def test_validate_assumptions_high_discount_rate_warning(self, client, sample_economic_assumptions):
        """Test validation with high but valid discount rate."""
        sample_economic_assumptions["discount_rate"] = 0.20  # 20% (high but valid)

        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True  # Valid, but should have warnings
        assert any("high" in warning.lower() for warning in data["warnings"])

    def test_validate_assumptions_cap_rate_warnings(self, client, sample_economic_assumptions):
        """Test validation with unusual cap rates."""
        # Test low cap rate
        sample_economic_assumptions["cap_rate"] = 0.02  # 2% (unusual)

        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        assert response.status_code == 200
        data = response.json()
        assert any("below 3%" in warning for warning in data["warnings"])

        # Test high cap rate
        sample_economic_assumptions["cap_rate"] = 0.10  # 10% (high)

        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        data = response.json()
        assert any("above 8%" in warning for warning in data["warnings"])

    def test_validate_assumptions_quality_factor_warnings(self, client, sample_economic_assumptions):
        """Test validation with extreme quality factors."""
        # Test low quality factor
        sample_economic_assumptions["quality_factor"] = 0.7  # Below 0.8

        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        assert response.status_code == 200
        data = response.json()
        assert any("below 0.8" in warning for warning in data["warnings"])

        # Test high quality factor
        sample_economic_assumptions["quality_factor"] = 1.3  # Above 1.2

        response = client.post(
            "/api/v1/economic-feasibility/assumptions/validate",
            json=sample_economic_assumptions
        )

        data = response.json()
        assert any("above 1.2" in warning for warning in data["warnings"])


class TestDefaultAssumptions:
    """Tests for GET /defaults endpoint."""

    @pytest.mark.skip(reason="Requires FRED client implementation")
    @patch('app.api.economic_feasibility.get_fred_client')
    async def test_get_default_assumptions_success(self, mock_get_client, client):
        """Test successful default assumptions generation."""
        # Mock FRED client
        mock_client = AsyncMock()
        mock_client.get_current_indices = AsyncMock(return_value=Mock(
            risk_free_rate_pct=4.15
        ))
        mock_get_client.return_value = mock_client

        response = client.get("/api/v1/economic-feasibility/defaults")

        assert response.status_code == 200
        data = response.json()
        assert "discount_rate" in data
        assert "cap_rate" in data
        assert "location_factor" in data
        assert "notes" in data
        assert isinstance(data["notes"], list)

    @pytest.mark.skip(reason="Requires FRED client implementation")
    def test_get_default_assumptions_with_county(self, client):
        """Test default assumptions for specific county."""
        response = client.get(
            "/api/v1/economic-feasibility/defaults?county=San Francisco"
        )

        assert response.status_code == 200
        data = response.json()
        # San Francisco should have higher location factor
        assert data["location_factor"] >= 2.0

    @pytest.mark.skip(reason="Requires FRED client implementation")
    def test_get_default_assumptions_fred_fallback(self, client):
        """Test default assumptions when FRED is unavailable."""
        with patch('app.services.fred_client.FredClient') as mock_fred:
            mock_fred.return_value.get_current_indices.side_effect = Exception("API timeout")

            response = client.get("/api/v1/economic-feasibility/defaults")

            # Should still succeed with fallback values
            assert response.status_code == 200
            data = response.json()
            assert "discount_rate" in data
            # Should have note about fallback
            assert any("fallback" in note.lower() for note in data.get("notes", []))


class TestErrorHandling:
    """Tests for error handling across all endpoints."""

    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payload."""
        response = client.post(
            "/api/v1/economic-feasibility/compute",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        incomplete_request = {
            "parcel_apn": "TEST"
            # Missing all other required fields
        }

        response = client.post(
            "/api/v1/economic-feasibility/compute",
            json=incomplete_request
        )

        assert response.status_code == 422

    def test_invalid_data_types(self, client):
        """Test handling of invalid data types."""
        invalid_request = {
            "parcel_apn": "TEST",
            "scenario_name": "Test",
            "units": "not_a_number",  # Should be int
            "buildable_sf": "also_not_a_number",  # Should be float
        }

        response = client.post(
            "/api/v1/economic-feasibility/compute",
            json=invalid_request
        )

        assert response.status_code == 422


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation generation."""

    def test_openapi_schema_generated(self, client):
        """Test that OpenAPI schema includes economic feasibility endpoints."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Verify economic feasibility endpoints are documented
        paths = schema.get("paths", {})
        assert "/api/v1/economic-feasibility/compute" in paths
        assert "/api/v1/economic-feasibility/cost-indices" in paths
        assert "/api/v1/economic-feasibility/market-rents/{zip_code}" in paths
        assert "/api/v1/economic-feasibility/assumptions/validate" in paths
        assert "/api/v1/economic-feasibility/defaults" in paths

    def test_endpoint_documentation_complete(self, client):
        """Test that endpoints have complete documentation."""
        response = client.get("/openapi.json")
        schema = response.json()

        # Check /compute endpoint documentation
        compute_endpoint = schema["paths"]["/api/v1/economic-feasibility/compute"]["post"]
        assert "summary" in compute_endpoint
        assert "description" in compute_endpoint
        assert "responses" in compute_endpoint
        assert "200" in compute_endpoint["responses"]
        assert "422" in compute_endpoint["responses"]
        assert "503" in compute_endpoint["responses"]

    def test_tags_properly_configured(self, client):
        """Test that Economic Feasibility tag is properly configured."""
        response = client.get("/openapi.json")
        schema = response.json()

        # Verify tag exists
        tags = schema.get("tags", [])
        tag_names = [tag["name"] for tag in tags]
        assert "Economic Feasibility" in tag_names


class TestRateLimiting:
    """Tests for rate limiting considerations."""

    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    def test_rate_limiting_applied(self, client):
        """Test that rate limiting is applied to expensive endpoints."""
        # Make many rapid requests
        for _ in range(150):  # Exceed typical 120/min FRED limit
            response = client.get("/api/v1/economic-feasibility/cost-indices")

        # Should get rate limit error
        assert response.status_code == 429


# Integration test helpers
@pytest.fixture
def mock_all_clients():
    """Mock all external clients for integration testing."""
    with patch('app.services.fred_client.FredClient') as mock_fred, \
         patch('app.services.hud_fmr_client.HudFMRClient') as mock_hud, \
         patch('app.services.ami_calculator.get_ami_calculator') as mock_ami:

        # Configure mocks
        mock_fred_instance = Mock()
        mock_fred_instance.get_current_indices = AsyncMock()
        mock_fred.return_value = mock_fred_instance

        mock_hud_instance = Mock()
        mock_hud_instance.get_fmr_by_zip = AsyncMock()
        mock_hud.return_value = mock_hud_instance

        mock_ami_instance = Mock()
        mock_ami.return_value = mock_ami_instance

        yield {
            'fred': mock_fred_instance,
            'hud': mock_hud_instance,
            'ami': mock_ami_instance
        }


class TestDependencyInjection:
    """Tests for dependency injection pattern."""

    @pytest.mark.skip(reason="Requires full client implementation")
    def test_singleton_fred_client(self, client, mock_all_clients):
        """Test that FRED client is reused across requests."""
        # Make multiple requests
        client.get("/api/v1/economic-feasibility/cost-indices")
        client.get("/api/v1/economic-feasibility/defaults")

        # Verify singleton behavior (client created once)
        # This would need instrumentation of the dependency system

    @pytest.mark.skip(reason="Requires full client implementation")
    def test_client_cleanup_on_shutdown(self, client):
        """Test that clients are properly cleaned up on app shutdown."""
        # This would test shutdown hooks if implemented
        pass
