"""
Census Construction Spending (C30) API client.

IMPORTANT: This data is for TREND CONTEXT ONLY, NOT per-project cost estimation.

The Census C30 dataset provides aggregated construction spending data at the national
and regional level. This is useful for understanding industry trends and inflation
patterns, but should NOT be used to estimate costs for individual projects.

For actual construction cost estimation, use:
- RS Means cost data
- Local contractor bids
- Consulting cost estimators

API Documentation: https://www.census.gov/data/developers/data-sets/eits.html
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

import pandas as pd
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.cache import (
    generate_cache_key,
    load_from_cache,
    save_to_cache
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CensusC30ClientError(Exception):
    """Base exception for Census C30 client errors."""
    pass


class CensusC30Client:
    """
    Async client for Census Construction Spending (C30) data.

    WARNING: This data is for TREND ANALYSIS ONLY.
    Do NOT use for per-project cost estimation.

    The C30 dataset provides monthly construction spending data for various
    categories at national and regional levels. Useful for understanding
    inflation trends and market conditions, but not granular enough for
    project-level cost estimation.
    """

    BASE_URL = "https://api.census.gov/data/timeseries/eits/resconst"

    # Common series IDs for residential construction
    SERIES_IDS = {
        "total_private_residential": "Total private residential construction spending",
        "single_family": "Single family residential construction",
        "multifamily": "Multifamily residential construction (2+ units)",
    }

    def __init__(self, cache_ttl_hours: int = 168):
        """
        Initialize Census C30 client.

        Note: Census API does not require an API key for this dataset.

        Args:
            cache_ttl_hours: Cache time-to-live in hours (default: 168 = 1 week)
        """
        self.cache_ttl_hours = cache_ttl_hours

        logger.info(
            "Census C30 client initialized",
            extra={
                "cache_ttl_hours": cache_ttl_hours,
                "warning": "Data for trend context only, not per-project costs"
            }
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def get_construction_spending(
        self,
        series_id: str,
        start_year: int,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get construction spending time series data.

        WARNING: Use for trend analysis only, NOT for project cost estimation.

        Args:
            series_id: Census series identifier
            start_year: Starting year (e.g., 2020)
            end_year: Ending year (defaults to current year)

        Returns:
            DataFrame with date index and spending values

        Raises:
            CensusC30ClientError: If API call fails

        Example:
            >>> client = CensusC30Client()
            >>> df = await client.get_construction_spending(
            ...     "multifamily",
            ...     start_year=2020,
            ...     end_year=2024
            ... )
        """
        if end_year is None:
            end_year = datetime.now().year

        cache_key = generate_cache_key("c30", series_id, start_year, end_year)
        cached = load_from_cache("census", cache_key, ttl_hours=self.cache_ttl_hours)

        if cached:
            logger.info(
                "Loaded Census C30 data from cache",
                extra={
                    "series_id": series_id,
                    "cached_at": cached["cached_at"],
                    "rows": len(cached["data"]["values"])
                }
            )
            # Reconstruct DataFrame from cached data
            df = pd.DataFrame({
                "period": cached["data"]["periods"],
                "value": cached["data"]["values"]
            })
            df["date"] = pd.to_datetime(df["period"], format="%Y%m")
            df.set_index("date", inplace=True)
            return df

        logger.info(
            "Fetching Census C30 data from API",
            extra={
                "series_id": series_id,
                "start_year": start_year,
                "end_year": end_year,
                "warning": "Data for trend context only"
            }
        )

        try:
            # Build API request
            # Note: Census API query syntax varies by dataset
            # This is a simplified example - actual implementation may need adjustment
            params = {
                "get": "cell_value,time_slot_id",
                "for": "us:*",
                "time": f"from {start_year} to {end_year}"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params
                )
                response.raise_for_status()
                data = response.json()

            # Parse response into DataFrame
            # First row is headers, rest is data
            if len(data) < 2:
                raise CensusC30ClientError("No data returned from Census API")

            headers = data[0]
            rows = data[1:]

            df = pd.DataFrame(rows, columns=headers)

            # Convert period to datetime
            df["date"] = pd.to_datetime(df["time_slot_id"], format="%Y%m")
            df["value"] = pd.to_numeric(df["cell_value"], errors="coerce")
            df.set_index("date", inplace=True)
            df = df[["value"]].sort_index()

            # Save to cache
            cache_data = {
                "periods": df.index.strftime("%Y%m").tolist(),
                "values": df["value"].tolist()
            }

            save_to_cache(
                "census",
                cache_key,
                cache_data,
                metadata={
                    "series_id": series_id,
                    "start_year": start_year,
                    "end_year": end_year,
                    "rows": len(df),
                    "warning": "Data for trend context only, not per-project costs"
                }
            )

            logger.info(
                "Fetched Census C30 data successfully",
                extra={
                    "series_id": series_id,
                    "rows": len(df),
                    "date_range": f"{df.index[0]} to {df.index[-1]}"
                }
            )

            return df

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching Census C30 data: {e.response.status_code}",
                extra={"series_id": series_id, "response": e.response.text}
            )
            raise CensusC30ClientError(
                f"Failed to fetch Census C30 data for {series_id}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch Census C30 data: {e}",
                extra={"series_id": series_id}
            )
            raise CensusC30ClientError(
                f"Failed to fetch Census C30 data for {series_id}: {e}"
            )

    async def get_latest_spending(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent construction spending value for a series.

        WARNING: Use for trend analysis only, NOT for project cost estimation.

        Args:
            series_id: Census series identifier

        Returns:
            Dictionary with latest value, period, and metadata

        Raises:
            CensusC30ClientError: If API call fails
        """
        current_year = datetime.now().year
        df = await self.get_construction_spending(
            series_id,
            start_year=current_year - 1,
            end_year=current_year
        )

        if df.empty:
            return None

        latest_date = df.index[-1]
        latest_value = df.iloc[-1]["value"]

        return {
            "series_id": series_id,
            "value": float(latest_value),
            "period": latest_date.strftime("%Y-%m"),
            "as_of_date": latest_date.isoformat(),
            "warning": "Data for trend context only, not per-project cost estimation"
        }

    @staticmethod
    def get_available_series() -> Dict[str, str]:
        """
        Get available series IDs and their descriptions.

        Returns:
            Dictionary mapping series IDs to descriptions
        """
        return CensusC30Client.SERIES_IDS.copy()


# Module-level convenience function
_default_client: Optional[CensusC30Client] = None


def get_census_client(cache_ttl_hours: int = 168) -> CensusC30Client:
    """
    Get a singleton Census C30 client instance.

    Args:
        cache_ttl_hours: Cache time-to-live in hours

    Returns:
        CensusC30Client instance
    """
    global _default_client
    if _default_client is None:
        _default_client = CensusC30Client(cache_ttl_hours=cache_ttl_hours)
    return _default_client
