"""
HUD Fair Market Rent (FMR) API Client

Retrieves FMR and Small Area FMR (SAFMR) data from HUD's API.

Data Source: HUD FMR API
- FMR: https://www.huduser.gov/portal/datasets/fmr.html
- API: https://www.huduser.gov/hudapi/public/fmr/data/{zip_code}

FMR Definition: 40th percentile of gross rents for standard quality units
(24 CFR Part 888)

Small Area FMRs (SAFMRs): ZIP code-level FMRs for more granular market analysis
- Available in select metro areas
- Indicated by smallarea_status=1 in API response
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
import httpx
from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FMRData(BaseModel):
    """Fair Market Rent data for a location."""

    zip_code: str = Field(..., description="ZIP code")
    metro_code: str = Field(..., description="Metro area code (entity_id)")
    metro_name: str = Field(..., description="Metro area name")
    county_name: str = Field(..., description="County name")
    state: str = Field(..., description="State abbreviation")
    year: int = Field(..., description="Data year")

    # FMR by bedroom count
    fmr_0br: float = Field(..., description="Studio/efficiency FMR")
    fmr_1br: float = Field(..., description="1-bedroom FMR")
    fmr_2br: float = Field(..., description="2-bedroom FMR")
    fmr_3br: float = Field(..., description="3-bedroom FMR")
    fmr_4br: float = Field(..., description="4-bedroom FMR")

    # SAFMR indicator
    smallarea_status: int = Field(
        ...,
        description="Small Area FMR status (1=SAFMR available, 0=metro-wide FMR only)"
    )

    # Percentile data (optional)
    fmr_percentile: Optional[int] = Field(
        40,
        description="FMR percentile (typically 40th)"
    )


class HudFMRClient:
    """
    Client for HUD Fair Market Rent API.

    Retrieves FMR data by ZIP code with automatic SAFMR detection.

    Usage:
        client = HudFMRClient()
        fmr_data = await client.get_fmr_by_zip("90401")
    """

    BASE_URL = "https://www.huduser.gov/hudapi/public/fmr"

    def __init__(self, api_token: Optional[str] = None, timeout: int = 30):
        """
        Initialize HUD FMR client.

        Args:
            api_token: HUD API Bearer token (defaults to HUD_API_TOKEN from settings)
            timeout: Request timeout in seconds
        """
        self.api_token = api_token or settings.HUD_API_TOKEN
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with authentication headers."""
        if self._client is None:
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            self._client = httpx.AsyncClient(timeout=self.timeout, headers=headers)
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_fmr_by_zip(
        self,
        zip_code: str,
        year: Optional[int] = None
    ) -> FMRData:
        """
        Get FMR data for ZIP code.

        Automatically uses SAFMR if available (smallarea_status=1).

        Args:
            zip_code: 5-digit ZIP code
            year: Data year (defaults to latest available)

        Returns:
            FMRData with rents by bedroom count

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If ZIP code not found or invalid response

        Examples:
            >>> client = HudFMRClient()
            >>> fmr_data = await client.get_fmr_by_zip("90401")
            >>> print(f"2BR FMR: ${fmr_data.fmr_2br}")
            2BR FMR: $2815
            >>> print(f"SAFMR: {fmr_data.smallarea_status == 1}")
            SAFMR: True
        """
        # Validate ZIP code format
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            raise ValueError(f"Invalid ZIP code format: {zip_code}")

        # Build URL
        url = f"{self.BASE_URL}/data/{zip_code}"
        if year:
            url += f"?year={year}"

        logger.info(
            "Fetching HUD FMR data",
            extra={"zip_code": zip_code, "year": year}
        )

        # Make API request
        client = await self._get_client()
        try:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()

            # HUD API returns data in 'data' key with 'basicdata' structure
            if "error" in data:
                raise ValueError(f"HUD API error: {data['error']}")

            if "data" not in data or "basicdata" not in data["data"]:
                raise ValueError(f"Unexpected API response structure for ZIP {zip_code}")

            # Extract basic data
            basic = data["data"]["basicdata"]

            # Parse FMR data
            fmr_data = FMRData(
                zip_code=zip_code,
                metro_code=basic.get("metro_code", basic.get("cbsa_code", "")),
                metro_name=basic.get("areaname", ""),
                county_name=basic.get("countyname", ""),
                state=basic.get("state_alpha", ""),
                year=int(basic.get("year", year or 2024)),
                fmr_0br=float(basic.get("Efficiency", 0)),
                fmr_1br=float(basic.get("One-Bedroom", 0)),
                fmr_2br=float(basic.get("Two-Bedroom", 0)),
                fmr_3br=float(basic.get("Three-Bedroom", 0)),
                fmr_4br=float(basic.get("Four-Bedroom", 0)),
                smallarea_status=int(basic.get("smallarea_status", 0)),
                fmr_percentile=40  # HUD FMR is 40th percentile per 24 CFR 888
            )

            logger.info(
                "Successfully fetched HUD FMR data",
                extra={
                    "zip_code": zip_code,
                    "metro_name": fmr_data.metro_name,
                    "is_safmr": fmr_data.smallarea_status == 1,
                    "fmr_2br": fmr_data.fmr_2br
                }
            )

            return fmr_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HUD API request failed: {e}",
                extra={"zip_code": zip_code, "status_code": e.response.status_code}
            )
            raise ValueError(
                f"Failed to fetch FMR data for ZIP {zip_code}: "
                f"HTTP {e.response.status_code}"
            )
        except Exception as e:
            logger.error(
                f"Error fetching HUD FMR data: {e}",
                extra={"zip_code": zip_code}
            )
            raise

    def get_fmr_for_bedroom(self, fmr_data: FMRData, bedrooms: int) -> float:
        """
        Get FMR for specific bedroom count.

        Args:
            fmr_data: FMR data object
            bedrooms: Number of bedrooms (0-4)

        Returns:
            FMR rent for bedroom count

        Examples:
            >>> fmr = client.get_fmr_for_bedroom(fmr_data, 2)
            >>> print(f"2BR FMR: ${fmr}")
            2BR FMR: $2815
        """
        bedroom_map = {
            0: fmr_data.fmr_0br,
            1: fmr_data.fmr_1br,
            2: fmr_data.fmr_2br,
            3: fmr_data.fmr_3br,
            4: fmr_data.fmr_4br,
        }

        # For 5+ bedrooms, use 4BR rate
        if bedrooms >= 4:
            return fmr_data.fmr_4br

        return bedroom_map.get(bedrooms, fmr_data.fmr_2br)


# Singleton instance
_hud_client_instance: Optional[HudFMRClient] = None


def get_hud_fmr_client() -> HudFMRClient:
    """
    Get singleton HUD FMR client instance.

    Returns:
        HudFMRClient instance

    Examples:
        >>> client = get_hud_fmr_client()
        >>> fmr_data = await client.get_fmr_by_zip("90401")
    """
    global _hud_client_instance
    if _hud_client_instance is None:
        _hud_client_instance = HudFMRClient()
    return _hud_client_instance
