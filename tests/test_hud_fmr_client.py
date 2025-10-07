"""
Tests for HUD Fair Market Rent (FMR) API Client.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.clients.hud_fmr_client import (
    HudFMRClient,
    FMRData,
    get_hud_fmr_client
)


@pytest.fixture
def mock_hud_response():
    """Mock HUD API response with SAFMR data."""
    return {
        "data": {
            "basicdata": {
                "metro_code": "METRO42644M42644",
                "cbsa_code": "31080",
                "areaname": "Los Angeles-Long Beach-Anaheim, CA",
                "countyname": "Los Angeles County",
                "state_alpha": "CA",
                "year": "2024",
                "Efficiency": "1823",
                "One-Bedroom": "2156",
                "Two-Bedroom": "2815",
                "Three-Bedroom": "3866",
                "Four-Bedroom": "4614",
                "smallarea_status": "1"
            }
        }
    }


@pytest.fixture
def mock_hud_response_no_safmr():
    """Mock HUD API response without SAFMR (metro-wide only)."""
    return {
        "data": {
            "basicdata": {
                "metro_code": "METRO12345M12345",
                "cbsa_code": "12345",
                "areaname": "Fresno, CA",
                "countyname": "Fresno County",
                "state_alpha": "CA",
                "year": "2024",
                "Efficiency": "900",
                "One-Bedroom": "1050",
                "Two-Bedroom": "1250",
                "Three-Bedroom": "1600",
                "Four-Bedroom": "1850",
                "smallarea_status": "0"
            }
        }
    }


class TestHudFMRClient:
    """Tests for HUD FMR client initialization and configuration."""

    def test_client_initializes(self):
        """Test client initializes successfully."""
        client = HudFMRClient()
        assert client is not None
        assert client.timeout == 30

    def test_client_custom_timeout(self):
        """Test client accepts custom timeout."""
        client = HudFMRClient(timeout=60)
        assert client.timeout == 60

    def test_singleton_instance(self):
        """Test get_hud_fmr_client returns singleton."""
        client1 = get_hud_fmr_client()
        client2 = get_hud_fmr_client()
        assert client1 is client2


class TestFMRDataFetching:
    """Tests for FMR data fetching."""

    @pytest.mark.asyncio
    async def test_fetch_fmr_with_safmr(self, mock_hud_response):
        """Test fetching FMR data with SAFMR available."""
        client = HudFMRClient()

        # Mock HTTP client
        mock_response = Mock()
        mock_response.json.return_value = mock_hud_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.get.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http_client):
            fmr_data = await client.get_fmr_by_zip("90401")

        # Verify FMR data
        assert fmr_data.zip_code == "90401"
        assert fmr_data.metro_name == "Los Angeles-Long Beach-Anaheim, CA"
        assert fmr_data.county_name == "Los Angeles County"
        assert fmr_data.state == "CA"
        assert fmr_data.year == 2024
        assert fmr_data.smallarea_status == 1  # SAFMR available

        # Verify FMR values
        assert fmr_data.fmr_0br == 1823.0
        assert fmr_data.fmr_1br == 2156.0
        assert fmr_data.fmr_2br == 2815.0
        assert fmr_data.fmr_3br == 3866.0
        assert fmr_data.fmr_4br == 4614.0

        # Verify percentile
        assert fmr_data.fmr_percentile == 40

    @pytest.mark.asyncio
    async def test_fetch_fmr_without_safmr(self, mock_hud_response_no_safmr):
        """Test fetching FMR data without SAFMR (metro-wide only)."""
        client = HudFMRClient()

        mock_response = Mock()
        mock_response.json.return_value = mock_hud_response_no_safmr
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.get.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http_client):
            fmr_data = await client.get_fmr_by_zip("93721")

        assert fmr_data.smallarea_status == 0  # No SAFMR
        assert fmr_data.metro_name == "Fresno, CA"
        assert fmr_data.fmr_2br == 1250.0

    @pytest.mark.asyncio
    async def test_fetch_fmr_with_year(self, mock_hud_response):
        """Test fetching FMR data for specific year."""
        client = HudFMRClient()

        mock_response = Mock()
        mock_response.json.return_value = mock_hud_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.get.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http_client):
            fmr_data = await client.get_fmr_by_zip("90401", year=2023)

        # Verify year was passed to API
        mock_http_client.get.assert_called_once()
        call_url = mock_http_client.get.call_args[0][0]
        assert "year=2023" in call_url


class TestFMRValidation:
    """Tests for FMR data validation and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_zip_code_format(self):
        """Test error on invalid ZIP code format."""
        client = HudFMRClient()

        with pytest.raises(ValueError, match="Invalid ZIP code format"):
            await client.get_fmr_by_zip("123")  # Too short

        with pytest.raises(ValueError, match="Invalid ZIP code format"):
            await client.get_fmr_by_zip("ABCDE")  # Non-numeric

        with pytest.raises(ValueError, match="Invalid ZIP code format"):
            await client.get_fmr_by_zip("")  # Empty

    @pytest.mark.asyncio
    async def test_api_error_response(self):
        """Test handling of API error responses."""
        client = HudFMRClient()

        mock_response = Mock()
        mock_response.json.return_value = {"error": "ZIP code not found"}
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.get.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http_client):
            with pytest.raises(ValueError, match="HUD API error"):
                await client.get_fmr_by_zip("99999")

    @pytest.mark.asyncio
    async def test_malformed_response(self):
        """Test handling of malformed API response."""
        client = HudFMRClient()

        mock_response = Mock()
        mock_response.json.return_value = {"unexpected": "structure"}
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.get.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http_client):
            with pytest.raises(ValueError, match="Unexpected API response structure"):
                await client.get_fmr_by_zip("90401")


class TestFMRBedroomLookup:
    """Tests for bedroom-specific FMR lookups."""

    def test_get_fmr_for_bedroom(self):
        """Test getting FMR for specific bedroom count."""
        fmr_data = FMRData(
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
            smallarea_status=1
        )

        client = HudFMRClient()

        # Test each bedroom count
        assert client.get_fmr_for_bedroom(fmr_data, 0) == 1823.0
        assert client.get_fmr_for_bedroom(fmr_data, 1) == 2156.0
        assert client.get_fmr_for_bedroom(fmr_data, 2) == 2815.0
        assert client.get_fmr_for_bedroom(fmr_data, 3) == 3866.0
        assert client.get_fmr_for_bedroom(fmr_data, 4) == 4614.0

    def test_get_fmr_for_5plus_bedrooms(self):
        """Test getting FMR for 5+ bedrooms (uses 4BR rate)."""
        fmr_data = FMRData(
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
            smallarea_status=1
        )

        client = HudFMRClient()

        # 5+ bedrooms should use 4BR rate
        assert client.get_fmr_for_bedroom(fmr_data, 5) == 4614.0
        assert client.get_fmr_for_bedroom(fmr_data, 10) == 4614.0


class TestClientLifecycle:
    """Tests for client lifecycle management."""

    @pytest.mark.asyncio
    async def test_client_close(self):
        """Test client closes HTTP connection."""
        client = HudFMRClient()

        # Create mock HTTP client
        mock_http_client = AsyncMock()
        client._client = mock_http_client

        # Close client
        await client.close()

        # Verify aclose was called
        mock_http_client.aclose.assert_called_once()
        assert client._client is None
