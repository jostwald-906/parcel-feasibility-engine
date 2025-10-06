"""
Base City Configuration

Abstract base class defining the interface for city-specific configurations.
Each city module should inherit from CityConfig and implement:
- Zoning codes and categories
- GIS service URLs
- Local overlay rules (special plan areas, historic districts, etc.)
- City-specific development standards

State law programs (SB9, SB35, AB2011, Density Bonus) are handled separately
in app/rules/state_law/ and apply uniformly across all California cities.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ZoningCode(BaseModel):
    """Standard zoning code structure."""
    code: str
    description: str
    category: str
    base_far: Optional[float] = None
    base_height_ft: Optional[float] = None


class GISServiceConfig(BaseModel):
    """GIS service connection configuration."""
    url: str
    layer_name: str
    layer_id: Optional[int] = None
    geometry_type: str
    fields: Dict[str, str]
    key_fields: List[str] = []


class OverlayZone(BaseModel):
    """Overlay zone or special plan area."""
    name: str
    code: str
    description: str
    gis_service: Optional[GISServiceConfig] = None
    applies_by_zoning: bool = False  # True if overlay is inferred from base zoning code
    affected_zones: List[str] = []  # Zoning codes this overlay applies to


class CityConfig(ABC):
    """
    Abstract base class for city-specific configurations.

    Each city should implement this class to provide:
    - Zoning codes and their development standards
    - GIS service connections
    - Overlay zones and special plan areas
    - City-specific development rules
    """

    @property
    @abstractmethod
    def city_name(self) -> str:
        """Full city name (e.g., 'Santa Monica')."""
        pass

    @property
    @abstractmethod
    def city_code(self) -> str:
        """Short code for city (e.g., 'SM', 'LA', 'SF')."""
        pass

    @property
    @abstractmethod
    def state(self) -> str:
        """State code (always 'CA' for California cities)."""
        pass

    @property
    @abstractmethod
    def municipal_code_url(self) -> str:
        """URL to the city's municipal code (for citations)."""
        pass

    # Zoning Configuration

    @abstractmethod
    def get_zoning_codes(self) -> List[ZoningCode]:
        """
        Return all zoning codes for this city.

        Returns:
            List of ZoningCode objects with base development standards
        """
        pass

    @abstractmethod
    def get_zoning_categories(self) -> Dict[str, List[str]]:
        """
        Return zoning codes organized by category.

        Returns:
            Dict mapping category name to list of zoning code strings
            Example: {"Residential": ["R1", "R2"], "Commercial": ["C1", "C2"]}
        """
        pass

    def get_zoning_by_code(self, code: str) -> Optional[ZoningCode]:
        """
        Get zoning details for a specific code.

        Args:
            code: Zoning code (e.g., 'R1', 'C2')

        Returns:
            ZoningCode object or None if not found
        """
        for zone in self.get_zoning_codes():
            if zone.code.upper() == code.upper():
                return zone
        return None

    # GIS Configuration

    @abstractmethod
    def get_parcel_service(self) -> GISServiceConfig:
        """Return GIS service config for parcel data."""
        pass

    @abstractmethod
    def get_zoning_service(self) -> GISServiceConfig:
        """Return GIS service config for zoning data."""
        pass

    def get_historic_service(self) -> Optional[GISServiceConfig]:
        """Return GIS service config for historic districts/resources."""
        return None

    def get_coastal_service(self) -> Optional[GISServiceConfig]:
        """Return GIS service config for coastal zone."""
        return None

    def get_flood_service(self) -> Optional[GISServiceConfig]:
        """Return GIS service config for flood zones."""
        return None

    def get_transit_service(self) -> Optional[GISServiceConfig]:
        """Return GIS service config for transit stops/routes."""
        return None

    @abstractmethod
    def get_overlay_services(self) -> List[GISServiceConfig]:
        """
        Return GIS services for overlay zones and special plan areas.

        Returns:
            List of GIS service configs for overlays
        """
        pass

    def get_hazard_services(self) -> List[GISServiceConfig]:
        """Return GIS services for environmental hazards."""
        return []

    # Overlay Zones and Special Plan Areas

    @abstractmethod
    def get_overlay_zones(self) -> List[OverlayZone]:
        """
        Return overlay zones and special plan areas for this city.

        Returns:
            List of OverlayZone objects
        """
        pass

    def get_overlay_by_code(self, code: str) -> Optional[OverlayZone]:
        """
        Get overlay zone details by code.

        Args:
            code: Overlay code (e.g., 'DCP', 'BERGAMOT')

        Returns:
            OverlayZone object or None if not found
        """
        for overlay in self.get_overlay_zones():
            if overlay.code.upper() == code.upper():
                return overlay
        return None

    # City-Specific Rules

    @abstractmethod
    def get_special_plan_areas(self) -> List[str]:
        """
        Return list of special plan area identifiers.

        These trigger city-specific scenario generation logic.

        Returns:
            List of plan area codes (e.g., ['DCP', 'BERGAMOT', 'SPECIFIC_PLAN_X'])
        """
        pass

    def supports_tiered_development(self) -> bool:
        """
        Whether this city uses tiered development standards.

        Returns:
            True if city has tier-based FAR/height systems
        """
        return False

    def get_tier_standards(self, zone_code: str) -> Optional[Dict[str, Any]]:
        """
        Get tiered development standards for a zone.

        Args:
            zone_code: Zoning code

        Returns:
            Dict of tier standards or None if not tiered
            Example: {'1': {'far': 2.0, 'height': 45}, '2': {'far': 3.0, 'height': 60}}
        """
        return None

    # Coastal Zone (California-specific)

    def is_in_coastal_zone(self) -> bool:
        """Whether this entire city is within the California Coastal Zone."""
        return False

    def get_coastal_boundary_reference(self) -> Optional[str]:
        """
        Reference point for coastal zone determination (if applicable).

        For cities like Santa Monica where entire city is in coastal zone,
        this can return a geographic reference (e.g., street name) that
        divides areas with different CDP requirements.

        Returns:
            Geographic reference string or None
        """
        return None

    # Utility Methods

    def to_dict(self) -> Dict[str, Any]:
        """Export city configuration as dictionary."""
        return {
            "city_name": self.city_name,
            "city_code": self.city_code,
            "state": self.state,
            "municipal_code_url": self.municipal_code_url,
            "zoning_codes": [z.model_dump() for z in self.get_zoning_codes()],
            "zoning_categories": self.get_zoning_categories(),
            "overlay_zones": [o.model_dump() for o in self.get_overlay_zones()],
            "special_plan_areas": self.get_special_plan_areas(),
            "supports_tiered_development": self.supports_tiered_development(),
            "in_coastal_zone": self.is_in_coastal_zone(),
        }
