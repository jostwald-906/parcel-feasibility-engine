"""
FRED (Federal Reserve Economic Data) API Client

Fetches economic data series from the St. Louis Federal Reserve FRED API.

Key Series Used:
- WPUSI012011: Producer Price Index - Construction Materials (for cost escalation)
- ECICONWAG: Employment Cost Index - Construction Wages & Salaries (for wage escalation)
- DGS10: 10-Year Treasury Constant Maturity Rate (for construction financing)

API Documentation: https://fred.stlouisfed.org/docs/api/fred/
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from datetime import date as date_type
import logging

logger = logging.getLogger(__name__)


class FredObservation(BaseModel):
    """Single FRED data observation."""

    date: date_type = Field(..., description="Observation date")
    value: float = Field(..., description="Observation value")
    series_id: str = Field(..., description="FRED series ID")


class FredClient:
    """
    Client for fetching FRED economic data.

    This is a stub implementation that returns cached/default values.
    For live FRED data, requires FRED API key from https://fred.stlouisfed.org/docs/api/api_key.html
    """

    def __init__(self, api_key: Optional[str] = None, use_live_data: bool = False):
        """
        Initialize FRED client.

        Args:
            api_key: FRED API key (required for live data)
            use_live_data: If True, fetch live data from FRED API (requires api_key)
        """
        self.api_key = api_key
        self.use_live_data = use_live_data and api_key is not None

        # Cached baseline values (as of January 2025)
        self._cached_data = {
            "WPUSI012011": {  # Construction Materials PPI
                "value": 140.5,
                "date": date_type(2025, 1, 15),
                "description": "Producer Price Index by Commodity: Inputs to Construction",
            },
            "ECICONWAG": {  # Construction Wages ECI
                "value": 145.2,
                "date": date_type(2024, 12, 31),
                "description": "Employment Cost Index: Wages and Salaries: Construction",
            },
            "DGS10": {  # 10-Year Treasury Rate
                "value": 4.25,
                "date": date_type(2025, 1, 15),
                "description": "10-Year Treasury Constant Maturity Rate (percent)",
            },
        }

        if self.use_live_data:
            logger.info("FRED client initialized with live data fetching enabled")
        else:
            logger.info("FRED client initialized with cached baseline data (2025-01)")

    def get_latest_observation(self, series_id: str) -> FredObservation:
        """
        Get latest observation for a FRED series.

        Args:
            series_id: FRED series ID (e.g., 'WPUSI012011')

        Returns:
            FredObservation with latest value and date

        Raises:
            ValueError: If series_id is not found
        """
        if self.use_live_data:
            # TODO: Implement live FRED API fetching
            logger.warning(f"Live FRED data not implemented, using cached value for {series_id}")
            return self._get_cached_observation(series_id)
        else:
            return self._get_cached_observation(series_id)

    def _get_cached_observation(self, series_id: str) -> FredObservation:
        """Get cached observation from baseline data."""
        if series_id not in self._cached_data:
            raise ValueError(
                f"FRED series {series_id} not found in cached data. "
                f"Available series: {', '.join(self._cached_data.keys())}"
            )

        cached = self._cached_data[series_id]
        return FredObservation(
            date=cached["date"],
            value=cached["value"],
            series_id=series_id,
        )

    def get_observation_at_date(self, series_id: str, target_date: date_type) -> FredObservation:
        """
        Get observation for a specific date.

        Args:
            series_id: FRED series ID
            target_date: Target date for observation

        Returns:
            FredObservation for the specified date (or nearest available)

        Note:
            In cached mode, returns the cached value regardless of date.
        """
        if self.use_live_data:
            # TODO: Implement date-specific fetching
            logger.warning(f"Date-specific FRED data not implemented, using cached value for {series_id}")
            return self._get_cached_observation(series_id)
        else:
            # For cached data, just return the baseline value
            return self._get_cached_observation(series_id)

    def get_series_info(self, series_id: str) -> dict:
        """
        Get metadata about a FRED series.

        Args:
            series_id: FRED series ID

        Returns:
            Dict with series metadata
        """
        if series_id not in self._cached_data:
            raise ValueError(f"FRED series {series_id} not found")

        cached = self._cached_data[series_id]
        return {
            "id": series_id,
            "title": cached["description"],
            "last_updated": cached["date"].isoformat(),
            "units": "Index" if "PPI" in series_id or "ECI" in series_id else "Percent",
        }


def get_fred_client(api_key: Optional[str] = None, use_live_data: bool = False) -> FredClient:
    """
    Get FRED client instance.

    Args:
        api_key: FRED API key (optional, for live data)
        use_live_data: Enable live data fetching (requires api_key)

    Returns:
        FredClient instance
    """
    return FredClient(api_key=api_key, use_live_data=use_live_data)
