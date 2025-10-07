"""
Tests for FRED API client.

Tests the FRED client with mocked responses to ensure caching,
retry logic, and data handling work correctly.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from app.clients.fred_client import FREDClient, FREDClientError
from app.core.cache import get_cache_dir, clear_cache


@pytest.fixture(autouse=True)
def clear_fred_cache():
    """Clear FRED cache before and after each test."""
    clear_cache("fred")
    yield
    clear_cache("fred")


@pytest.fixture
def mock_fred_api():
    """Mock fredapi.Fred for testing."""
    with patch("app.clients.fred_client.Fred") as mock_fred:
        # Create a mock instance
        mock_instance = MagicMock()
        mock_fred.return_value = mock_instance

        # Mock get_series to return a pandas Series
        mock_series = pd.Series(
            data=[100.0, 101.5, 103.2, 104.8],
            index=pd.date_range(start="2024-01-01", periods=4, freq="M"),
            name="WPUSI012011"
        )
        mock_instance.get_series.return_value = mock_series

        yield mock_instance


class TestFREDClientInitialization:
    """Tests for FRED client initialization."""

    def test_init_without_api_key_raises_error(self):
        """Test that initializing without API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(FREDClientError, match="API key is required"):
                FREDClient()

    def test_init_with_api_key(self):
        """Test successful initialization with API key."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()
            assert client.api_key == "test_key"
            assert client.cache_ttl_hours == 24

    def test_init_with_custom_ttl(self):
        """Test initialization with custom cache TTL."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient(cache_ttl_hours=48)
            assert client.cache_ttl_hours == 48


class TestFREDClientGetSeries:
    """Tests for get_series method."""

    def test_get_series_success(self, mock_fred_api):
        """Test successful series retrieval."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()
            series = client.get_series("WPUSI012011")

            assert isinstance(series, pd.Series)
            assert len(series) == 4
            assert series.iloc[0] == 100.0
            mock_fred_api.get_series.assert_called_once()

    def test_get_series_unsupported_raises_error(self):
        """Test that unsupported series raises error."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()

            with pytest.raises(FREDClientError, match="Unsupported FRED series"):
                client.get_series("INVALID_SERIES")

    def test_get_series_with_date_range(self, mock_fred_api):
        """Test series retrieval with date range."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()
            series = client.get_series(
                "WPUSI012011",
                observation_start="2024-01-01",
                observation_end="2024-12-31"
            )

            assert isinstance(series, pd.Series)
            mock_fred_api.get_series.assert_called_once_with(
                "WPUSI012011",
                observation_start="2024-01-01",
                observation_end="2024-12-31"
            )

    def test_get_series_caching(self, mock_fred_api):
        """Test that series data is cached and reused."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()

            # First call - should hit API
            series1 = client.get_series("WPUSI012011")
            assert mock_fred_api.get_series.call_count == 1

            # Second call - should use cache
            series2 = client.get_series("WPUSI012011")
            assert mock_fred_api.get_series.call_count == 1  # Still 1, not 2

            # Series should be identical
            pd.testing.assert_series_equal(series1, series2)

    def test_get_series_api_error_raises(self, mock_fred_api):
        """Test that API errors are properly raised."""
        mock_fred_api.get_series.side_effect = Exception("API Error")

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()

            with pytest.raises(FREDClientError, match="Failed to fetch"):
                client.get_series("WPUSI012011")


class TestFREDClientGetLatestValue:
    """Tests for get_latest_value method."""

    def test_get_latest_value_success(self, mock_fred_api):
        """Test successful latest value retrieval."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()
            value, as_of_date = client.get_latest_value("WPUSI012011")

            assert value == 104.8  # Last value in mock series
            assert isinstance(as_of_date, datetime)

    def test_get_latest_value_empty_series_raises(self, mock_fred_api):
        """Test that empty series raises error."""
        # Mock empty series
        mock_fred_api.get_series.return_value = pd.Series([], dtype=float)

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()

            with pytest.raises(FREDClientError, match="No data available"):
                client.get_latest_value("WPUSI012011")

    def test_get_latest_value_handles_null_values(self, mock_fred_api):
        """Test that null values are handled correctly."""
        # Mock series with null values
        mock_series = pd.Series(
            data=[100.0, None, 103.2, None],
            index=pd.date_range(start="2024-01-01", periods=4, freq="M")
        )
        mock_fred_api.get_series.return_value = mock_series

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()
            value, as_of_date = client.get_latest_value("WPUSI012011")

            # Should return last non-null value
            assert value == 103.2


class TestFREDClientMetadata:
    """Tests for metadata methods."""

    def test_get_series_info(self):
        """Test get_series_info returns correct metadata."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()
            info = client.get_series_info("WPUSI012011")

            assert info["series_id"] == "WPUSI012011"
            assert "Producer Price Index" in info["name"]
            assert info["supported"] is True

    def test_get_series_info_unsupported_raises(self):
        """Test get_series_info for unsupported series raises error."""
        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()

            with pytest.raises(FREDClientError, match="Unsupported"):
                client.get_series_info("INVALID")

    def test_get_supported_series(self):
        """Test get_supported_series returns all series."""
        supported = FREDClient.get_supported_series()

        assert "WPUSI012011" in supported
        assert "ECICONWAG" in supported
        assert "DGS10" in supported
        assert len(supported) >= 3


class TestFREDClientRetry:
    """Tests for retry logic."""

    def test_retry_on_transient_error(self, mock_fred_api):
        """Test that client retries on transient errors."""
        # Fail twice, then succeed
        mock_fred_api.get_series.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            pd.Series(
                data=[100.0],
                index=pd.date_range(start="2024-01-01", periods=1, freq="M")
            )
        ]

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()
            series = client.get_series("WPUSI012011")

            assert len(series) == 1
            assert mock_fred_api.get_series.call_count == 3

    def test_retry_exhausts_after_max_attempts(self, mock_fred_api):
        """Test that retry gives up after max attempts."""
        # Always fail
        mock_fred_api.get_series.side_effect = Exception("Persistent error")

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client = FREDClient()

            with pytest.raises(FREDClientError, match="Failed to fetch"):
                client.get_series("WPUSI012011")

            # Should have retried 3 times
            assert mock_fred_api.get_series.call_count == 3


class TestFREDClientConvenience:
    """Tests for convenience functions."""

    def test_get_fred_client_singleton(self):
        """Test that get_fred_client returns singleton."""
        from app.clients.fred_client import get_fred_client

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            client1 = get_fred_client()
            client2 = get_fred_client()

            # Should be the same instance
            assert client1 is client2


@pytest.mark.parametrize("series_id,expected_keyword", [
    ("WPUSI012011", "Producer Price Index"),
    ("ECICONWAG", "Employment Cost Index"),
    ("DGS10", "Treasury"),
])
def test_supported_series_names(series_id, expected_keyword):
    """Test that supported series have expected keywords in names."""
    supported = FREDClient.get_supported_series()
    assert expected_keyword in supported[series_id]
