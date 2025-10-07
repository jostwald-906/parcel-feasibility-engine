"""
Federal Reserve Economic Data (FRED) API client.

Provides cached access to FRED economic time series data with retry logic.

FRED series used:
- WPUSI012011: Producer Price Index for new multi-unit residential construction
- ECICONWAG: Employment Cost Index for construction wages
- DGS10: 10-Year Treasury Constant Maturity Rate

Documentation: https://fred.stlouisfed.org/docs/api/fred/
"""

import os
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
from fredapi import Fred
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.cache import (
    generate_cache_key,
    load_from_cache,
    save_to_cache,
    get_cache_dir
)
from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FREDClientError(Exception):
    """Base exception for FRED client errors."""
    pass


class FREDClient:
    """
    Client for Federal Reserve Economic Data (FRED) API.

    Uses fredapi library with caching to CSV files for performance.
    Implements retry logic with exponential backoff.
    """

    # Supported FRED series
    SUPPORTED_SERIES = {
        "WPUSI012011": "Producer Price Index for new multi-unit residential construction",
        "ECICONWAG": "Employment Cost Index for construction wages",
        "DGS10": "10-Year Treasury Constant Maturity Rate"
    }

    def __init__(self, api_key: Optional[str] = None, cache_ttl_hours: int = 24):
        """
        Initialize FRED client.

        Args:
            api_key: FRED API key (defaults to FRED_API_KEY from settings)
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
        """
        self.api_key = api_key or settings.FRED_API_KEY
        if not self.api_key:
            raise FREDClientError(
                "FRED API key is required. Set FRED_API_KEY environment variable."
            )

        self.cache_ttl_hours = cache_ttl_hours
        self._fred_client: Optional[Fred] = None

        logger.info(
            "FRED client initialized",
            extra={"cache_ttl_hours": cache_ttl_hours}
        )

    @property
    def fred(self) -> Fred:
        """Lazy-load FRED client."""
        if self._fred_client is None:
            self._fred_client = Fred(api_key=self.api_key)
        return self._fred_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def get_series(
        self,
        series_id: str,
        observation_start: Optional[str] = None,
        observation_end: Optional[str] = None
    ) -> pd.Series:
        """
        Get a FRED time series with caching.

        Args:
            series_id: FRED series ID (e.g., 'WPUSI012011')
            observation_start: Start date in YYYY-MM-DD format (optional)
            observation_end: End date in YYYY-MM-DD format (optional)

        Returns:
            Pandas Series with date index and values

        Raises:
            FREDClientError: If series is not supported or API call fails
        """
        if series_id not in self.SUPPORTED_SERIES:
            raise FREDClientError(
                f"Unsupported FRED series: {series_id}. "
                f"Supported series: {', '.join(self.SUPPORTED_SERIES.keys())}"
            )

        # Generate cache key
        cache_key = generate_cache_key(series_id, observation_start, observation_end)

        # Try to load from cache
        cached = load_from_cache("fred", cache_key, ttl_hours=self.cache_ttl_hours)
        if cached:
            logger.info(
                f"Loaded FRED series from cache",
                extra={
                    "series_id": series_id,
                    "cached_at": cached["cached_at"],
                    "observations": len(cached["data"]["values"])
                }
            )
            # Reconstruct pandas Series from cached data
            return pd.Series(
                data=cached["data"]["values"],
                index=pd.to_datetime(cached["data"]["index"]),
                name=series_id
            )

        # Fetch from FRED API
        logger.info(
            f"Fetching FRED series from API",
            extra={
                "series_id": series_id,
                "observation_start": observation_start,
                "observation_end": observation_end
            }
        )

        try:
            series = self.fred.get_series(
                series_id,
                observation_start=observation_start,
                observation_end=observation_end
            )

            # Save to cache
            cache_data = {
                "index": series.index.strftime("%Y-%m-%d").tolist(),
                "values": series.tolist()
            }
            save_to_cache(
                "fred",
                cache_key,
                cache_data,
                metadata={
                    "series_id": series_id,
                    "series_name": self.SUPPORTED_SERIES[series_id],
                    "observation_start": observation_start,
                    "observation_end": observation_end,
                    "observations": len(series)
                }
            )

            logger.info(
                f"Fetched FRED series successfully",
                extra={
                    "series_id": series_id,
                    "observations": len(series),
                    "start_date": str(series.index[0]),
                    "end_date": str(series.index[-1])
                }
            )

            return series

        except Exception as e:
            logger.error(
                f"Failed to fetch FRED series: {e}",
                extra={"series_id": series_id}
            )
            raise FREDClientError(f"Failed to fetch FRED series {series_id}: {e}")

    def get_latest_value(self, series_id: str) -> Tuple[float, datetime]:
        """
        Get the most recent observation for a FRED series.

        Args:
            series_id: FRED series ID (e.g., 'WPUSI012011')

        Returns:
            Tuple of (value, as_of_date)

        Raises:
            FREDClientError: If series is not supported or API call fails
        """
        series = self.get_series(series_id)

        if series.empty:
            raise FREDClientError(f"No data available for series {series_id}")

        # Get the most recent non-null value
        series_clean = series.dropna()
        if series_clean.empty:
            raise FREDClientError(f"No valid data available for series {series_id}")

        latest_date = series_clean.index[-1]
        latest_value = series_clean.iloc[-1]

        logger.info(
            f"Retrieved latest value for FRED series",
            extra={
                "series_id": series_id,
                "value": latest_value,
                "as_of_date": str(latest_date)
            }
        )

        return float(latest_value), latest_date.to_pydatetime()

    def get_series_info(self, series_id: str) -> dict:
        """
        Get information about a FRED series.

        Args:
            series_id: FRED series ID

        Returns:
            Dictionary with series information
        """
        if series_id not in self.SUPPORTED_SERIES:
            raise FREDClientError(f"Unsupported FRED series: {series_id}")

        return {
            "series_id": series_id,
            "name": self.SUPPORTED_SERIES[series_id],
            "supported": True
        }

    def get_current_indices(self):
        """
        Get current construction cost indices from FRED.

        Returns:
            CostIndicesResponse with latest PPI, ECI, and risk-free rate
        """
        from app.models.economic_feasibility import CostIndicesResponse
        from datetime import datetime

        try:
            # Fetch latest values for all series
            ppi_value, ppi_date = self.get_latest_value("WPUSI012011")  # Materials PPI
            rf_value, rf_date = self.get_latest_value("DGS10")  # 10-Year Treasury

            # Try to get wage data, but it's optional
            try:
                wages_value, wages_date = self.get_latest_value("ECICONWAG")
            except Exception:
                wages_value = None
                wages_date = None

            # Use most recent date as "as of" date
            as_of_date = max(ppi_date, rf_date)

            return CostIndicesResponse(
                as_of_date=as_of_date.strftime("%Y-%m-%d"),
                materials_ppi=ppi_value,
                construction_wages_eci=wages_value,
                risk_free_rate_pct=rf_value,
                data_source="Federal Reserve Economic Data (FRED)",
                series_ids={
                    "materials_ppi": "WPUSI012011",
                    "risk_free_rate": "DGS10",
                    "construction_wages": "ECICONWAG"
                }
            )
        except Exception as e:
            logger.error(f"Failed to fetch current indices: {e}")
            raise

    @staticmethod
    def get_supported_series() -> dict:
        """
        Get all supported FRED series.

        Returns:
            Dictionary mapping series IDs to descriptions
        """
        return FREDClient.SUPPORTED_SERIES.copy()


# Module-level convenience function
_default_client: Optional[FREDClient] = None


def get_fred_client(cache_ttl_hours: int = 24) -> FREDClient:
    """
    Get a singleton FRED client instance.

    Args:
        cache_ttl_hours: Cache time-to-live in hours

    Returns:
        FREDClient instance
    """
    global _default_client
    if _default_client is None:
        _default_client = FREDClient(cache_ttl_hours=cache_ttl_hours)
    return _default_client
