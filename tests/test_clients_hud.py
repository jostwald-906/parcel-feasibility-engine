"""
Tests for HUD FMR API client.

Tests the HUD Fair Market Rents client with mocked responses.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from app.clients.hud_fmr_client import HUDFMRClient, HUDFMRClientError
from app.core.cache import clear_cache


@pytest.fixture(autouse=True)
def clear_hud_cache():
    """Clear HUD cache before and after each test."""
    clear_cache("hud")
    yield
    clear_cache("hud")


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = None
        yield mock_instance


class TestHUDFMRClientInitialization:
    """Tests for HUD FMR client initialization."""

    def test_init_without_api_token_raises_error(self):
        """Test that initializing without API token raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(HUDFMRClientError, match="API token is required"):
                HUDFMRClient()

    def test_init_with_api_token(self):
        """Test successful initialization with API token."""
        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            assert client.api_token == "test_token"
            assert client.cache_ttl_hours == 168

    def test_init_with_custom_ttl(self):
        """Test initialization with custom cache TTL."""
        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient(cache_ttl_hours=24)
            assert client.cache_ttl_hours == 24

    def test_headers_include_bearer_token(self):
        """Test that headers include Bearer token."""
        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            assert client.headers["Authorization"] == "Bearer test_token"
            assert client.headers["Content-Type"] == "application/json"


class TestHUDFMRClientListStates:
    """Tests for list_states method."""

    @pytest.mark.asyncio
    async def test_list_states_success(self, mock_httpx_client):
        """Test successful state list retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "results": [
                    {"state_code": "CA", "state_name": "California"},
                    {"state_code": "NY", "state_name": "New York"},
                ]
            }
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            states = await client.list_states()

            assert len(states) == 2
            assert states[0]["state_code"] == "CA"
            assert states[1]["state_code"] == "NY"

    @pytest.mark.asyncio
    async def test_list_states_caching(self, mock_httpx_client):
        """Test that state list is cached."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "results": [{"state_code": "CA", "state_name": "California"}]
            }
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()

            # First call
            states1 = await client.list_states()
            assert mock_httpx_client.get.call_count == 1

            # Second call - should use cache
            states2 = await client.list_states()
            assert mock_httpx_client.get.call_count == 1  # Still 1

            assert states1 == states2

    @pytest.mark.asyncio
    async def test_list_states_api_error(self, mock_httpx_client):
        """Test that API errors are properly raised."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error",
            request=Mock(),
            response=mock_response
        )
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()

            with pytest.raises(HUDFMRClientError, match="Failed to fetch state list"):
                await client.list_states()


class TestHUDFMRClientListCounties:
    """Tests for list_counties method."""

    @pytest.mark.asyncio
    async def test_list_counties_success(self, mock_httpx_client):
        """Test successful county list retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "results": [
                    {"county_name": "Los Angeles", "fips_code": "CNTY06037"},
                    {"county_name": "San Francisco", "fips_code": "CNTY06075"},
                ]
            }
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            counties = await client.list_counties("CA")

            assert len(counties) == 2
            assert counties[0]["county_name"] == "Los Angeles"
            assert counties[1]["fips_code"] == "CNTY06075"

    @pytest.mark.asyncio
    async def test_list_counties_normalizes_state_code(self, mock_httpx_client):
        """Test that state code is normalized to uppercase."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"results": []}
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            await client.list_counties("ca")  # lowercase

            # Should have called API with uppercase
            call_args = mock_httpx_client.get.call_args
            assert "CA" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_counties_caching(self, mock_httpx_client):
        """Test that county list is cached."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"results": [{"county_name": "Los Angeles"}]}
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()

            counties1 = await client.list_counties("CA")
            assert mock_httpx_client.get.call_count == 1

            counties2 = await client.list_counties("CA")
            assert mock_httpx_client.get.call_count == 1  # Cached

            assert counties1 == counties2


class TestHUDFMRClientGetFMRData:
    """Tests for get_fmr_data method."""

    @pytest.mark.asyncio
    async def test_get_fmr_data_success(self, mock_httpx_client):
        """Test successful FMR data retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "fmr_0": 1200,  # Efficiency
                "fmr_1": 1400,  # 1BR
                "fmr_2": 1700,  # 2BR
                "fmr_3": 2300,  # 3BR
                "fmr_4": 2700,  # 4BR
                "smallarea_status": 0
            }
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            fmr_data = await client.get_fmr_data("METRO42100N42100")

            assert fmr_data["fmr_2"] == 1700
            assert fmr_data["smallarea_status"] == 0

    @pytest.mark.asyncio
    async def test_get_fmr_data_with_year(self, mock_httpx_client):
        """Test FMR data retrieval with year parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"fmr_2": 1600}
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            await client.get_fmr_data("METRO42100N42100", year=2024)

            # Check that year was passed as parameter
            call_args = mock_httpx_client.get.call_args
            assert call_args[1]["params"]["year"] == 2024

    @pytest.mark.asyncio
    async def test_get_fmr_data_detects_safmr(self, mock_httpx_client):
        """Test that SAFMR status is detected."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "fmr_2": 1800,
                "smallarea_status": 1  # SAFMR available
            }
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            fmr_data = await client.get_fmr_data("METRO42100N42100")

            assert fmr_data["smallarea_status"] == 1

    @pytest.mark.asyncio
    async def test_get_fmr_data_caching(self, mock_httpx_client):
        """Test that FMR data is cached."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"fmr_2": 1700}
        }
        mock_httpx_client.get.return_value = mock_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()

            data1 = await client.get_fmr_data("METRO42100N42100")
            assert mock_httpx_client.get.call_count == 1

            data2 = await client.get_fmr_data("METRO42100N42100")
            assert mock_httpx_client.get.call_count == 1  # Cached

            assert data1 == data2


class TestHUDFMRClientGetCountyFMR:
    """Tests for get_county_fmr convenience method."""

    @pytest.mark.asyncio
    async def test_get_county_fmr_success(self, mock_httpx_client):
        """Test successful county FMR lookup."""
        # Mock counties list
        counties_response = Mock()
        counties_response.json.return_value = {
            "data": {
                "results": [
                    {"county_name": "Los Angeles", "fips_code": "CNTY06037"},
                ]
            }
        }

        # Mock FMR data
        fmr_response = Mock()
        fmr_response.json.return_value = {
            "data": {"fmr_2": 1700}
        }

        mock_httpx_client.get.side_effect = [counties_response, fmr_response]

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            fmr_data = await client.get_county_fmr("CA", "Los Angeles")

            assert fmr_data["fmr_2"] == 1700

    @pytest.mark.asyncio
    async def test_get_county_fmr_case_insensitive(self, mock_httpx_client):
        """Test that county name lookup is case-insensitive."""
        counties_response = Mock()
        counties_response.json.return_value = {
            "data": {
                "results": [
                    {"county_name": "Los Angeles", "fips_code": "CNTY06037"},
                ]
            }
        }

        fmr_response = Mock()
        fmr_response.json.return_value = {
            "data": {"fmr_2": 1700}
        }

        mock_httpx_client.get.side_effect = [counties_response, fmr_response]

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            fmr_data = await client.get_county_fmr("CA", "los angeles")  # lowercase

            assert fmr_data is not None
            assert fmr_data["fmr_2"] == 1700

    @pytest.mark.asyncio
    async def test_get_county_fmr_not_found(self, mock_httpx_client):
        """Test that None is returned if county not found."""
        counties_response = Mock()
        counties_response.json.return_value = {
            "data": {
                "results": [
                    {"county_name": "Los Angeles", "fips_code": "CNTY06037"},
                ]
            }
        }

        mock_httpx_client.get.return_value = counties_response

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            fmr_data = await client.get_county_fmr("CA", "Nonexistent County")

            assert fmr_data is None


class TestHUDFMRClientRetry:
    """Tests for retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, mock_httpx_client):
        """Test that client retries on timeout."""
        # Fail twice, then succeed
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"results": []}
        }

        mock_httpx_client.get.side_effect = [
            httpx.TimeoutException("Timeout"),
            httpx.TimeoutException("Timeout"),
            mock_response
        ]

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()
            states = await client.list_states()

            assert states == []
            assert mock_httpx_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausts_after_max_attempts(self, mock_httpx_client):
        """Test that retry gives up after max attempts."""
        mock_httpx_client.get.side_effect = httpx.TimeoutException("Timeout")

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client = HUDFMRClient()

            with pytest.raises(HUDFMRClientError):
                await client.list_states()

            # Should have retried 3 times
            assert mock_httpx_client.get.call_count == 3


class TestHUDFMRClientConvenience:
    """Tests for convenience functions."""

    def test_get_hud_client_singleton(self):
        """Test that get_hud_client returns singleton."""
        from app.clients.hud_fmr_client import get_hud_client

        with patch.dict("os.environ", {"HUD_API_TOKEN": "test_token"}):
            client1 = get_hud_client()
            client2 = get_hud_client()

            # Should be the same instance
            assert client1 is client2
