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

        NOTE: HUD's /data/{zipcode} endpoint returns 400 errors. This method uses a workaround
        by fetching statedata and finding the appropriate metro area based on ZIP code patterns.

        Args:
            zip_code: 5-digit ZIP code
            year: Data year (defaults to latest available - 2025)

        Returns:
            FMRData with rents by bedroom count

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If ZIP code not found or invalid response

        Examples:
            >>> client = HudFMRClient()
            >>> fmr_data = await client.get_fmr_by_zip("90401")  # Santa Monica
            >>> print(f"2BR FMR: ${fmr_data.fmr_2br}")
            2BR FMR: $2815
        """
        # Validate ZIP code format
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            raise ValueError(f"Invalid ZIP code format: {zip_code}")

        # Default to 2025 if no year specified
        if year is None:
            year = 2025

        # Map ZIP code to metro area (hardcoded for CA major metros)
        # ZIP → Metro mapping for California
        metro_name = self._zip_to_metro(zip_code)

        logger.info(
            "Fetching HUD FMR data via statedata endpoint",
            extra={"zip_code": zip_code, "year": year, "predicted_metro": metro_name}
        )

        # Fetch California statedata
        url = f"{self.BASE_URL}/statedata/CA?year={year}"

        client = await self._get_client()
        try:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                raise ValueError(f"HUD API error: {data['error']}")

            if "data" not in data or "metroareas" not in data["data"]:
                raise ValueError(f"Unexpected API response structure")

            # Find the metro area matching our ZIP code
            metros = data["data"]["metroareas"]
            metro_data = None

            # First try exact metro name match
            for metro in metros:
                if metro_name.lower() in metro["metro_name"].lower():
                    metro_data = metro
                    break

            # If no match, use LA as default for Southern CA ZIPs starting with 9
            if metro_data is None and zip_code.startswith("9"):
                for metro in metros:
                    if "Los Angeles" in metro["metro_name"]:
                        metro_data = metro
                        logger.warning(
                            f"Using Los Angeles metro FMR as fallback for ZIP {zip_code}",
                            extra={"zip_code": zip_code}
                        )
                        break

            if metro_data is None:
                raise ValueError(
                    f"Could not find FMR data for ZIP {zip_code}. "
                    f"Predicted metro: {metro_name}"
                )

            # Parse FMR data
            fmr_data = FMRData(
                zip_code=zip_code,
                metro_code=metro_data["code"],
                metro_name=metro_data["metro_name"],
                county_name="",  # Not available in statedata response
                state="CA",
                year=int(data["data"]["year"]),
                fmr_0br=float(metro_data["Efficiency"]),
                fmr_1br=float(metro_data["One-Bedroom"]),
                fmr_2br=float(metro_data["Two-Bedroom"]),
                fmr_3br=float(metro_data["Three-Bedroom"]),
                fmr_4br=float(metro_data["Four-Bedroom"]),
                smallarea_status=int(metro_data["smallarea_status"]),
                fmr_percentile=int(metro_data.get("FMR Percentile", 40))
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

    def _zip_to_metro(self, zip_code: str) -> str:
        """
        Map ZIP code to metro area name (California only).

        This is a simplified mapping based on ZIP code ranges.
        For production, use a proper ZIP→CBSA database.

        Args:
            zip_code: 5-digit ZIP code

        Returns:
            Predicted metro area name
        """
        # Convert to int for range checking
        zip_int = int(zip_code)

        # San Francisco-Oakland-Berkeley (94000-94999)
        if 94000 <= zip_int <= 94999:
            return "San Francisco"

        # San Jose-Sunnyvale-Santa Clara (95000-95199)
        elif 95000 <= zip_int <= 95199:
            return "San Jose"

        # Sacramento-Roseville-Folsom (94200-94299, 95600-95899)
        elif 95600 <= zip_int <= 95899:
            return "Sacramento"

        # San Diego-Chula Vista-Carlsbad (91900-92199, 92200-92899)
        elif 91900 <= zip_int <= 92199 or 92100 <= zip_int <= 92199:
            return "San Diego"

        # Riverside-San Bernardino-Ontario (92200-92599, 92800-92899)
        elif (92200 <= zip_int <= 92599) or (92800 <= zip_int <= 92899):
            return "Riverside"

        # Los Angeles-Long Beach-Anaheim (90001-90899, 91001-91899)
        elif (90000 <= zip_int <= 90899) or (91000 <= zip_int <= 91899):
            return "Los Angeles"

        # Default to Los Angeles for unrecognized CA ZIP
        else:
            return "Los Angeles"

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
