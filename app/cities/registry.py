"""
City Registry

Central registry for managing multiple city configurations.
Provides dynamic loading and switching between cities.
"""

from typing import Dict, Optional, List
from app.cities.base import CityConfig
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CityRegistry:
    """
    Registry for city configurations.

    Manages available cities and provides lookup/switching functionality.
    """

    def __init__(self):
        self._cities: Dict[str, CityConfig] = {}
        self._default_city: Optional[str] = None
        self._load_cities()

    def _load_cities(self):
        """Load all available city configurations."""
        try:
            # Santa Monica
            from app.cities.santa_monica import santa_monica
            self.register_city(santa_monica)
            self._default_city = "SM"
            logger.info("Loaded Santa Monica city configuration")

            # Future cities will be added here:
            # from app.cities.los_angeles import los_angeles
            # self.register_city(los_angeles)
            #
            # from app.cities.san_francisco import san_francisco
            # self.register_city(san_francisco)

        except Exception as e:
            logger.error(f"Error loading city configurations: {e}", exc_info=True)

    def register_city(self, city_config: CityConfig):
        """
        Register a city configuration.

        Args:
            city_config: CityConfig instance to register
        """
        code = city_config.city_code
        self._cities[code] = city_config
        logger.info(f"Registered city: {city_config.city_name} ({code})")

    def get_city(self, city_code: str) -> Optional[CityConfig]:
        """
        Get city configuration by code.

        Args:
            city_code: City code (e.g., 'SM', 'LA', 'SF')

        Returns:
            CityConfig instance or None if not found
        """
        return self._cities.get(city_code.upper())

    def get_default_city(self) -> CityConfig:
        """
        Get the default city configuration.

        Returns:
            Default CityConfig (currently Santa Monica)
        """
        if not self._default_city or self._default_city not in self._cities:
            raise ValueError("No default city configured")
        return self._cities[self._default_city]

    def list_cities(self) -> List[Dict[str, str]]:
        """
        List all available cities.

        Returns:
            List of dicts with city info: [{'code': 'SM', 'name': 'Santa Monica', 'state': 'CA'}, ...]
        """
        return [
            {
                "code": city.city_code,
                "name": city.city_name,
                "state": city.state
            }
            for city in self._cities.values()
        ]

    def get_city_by_name(self, city_name: str) -> Optional[CityConfig]:
        """
        Get city configuration by name (case-insensitive).

        Args:
            city_name: City name (e.g., 'Santa Monica', 'Los Angeles')

        Returns:
            CityConfig instance or None if not found
        """
        for city in self._cities.values():
            if city.city_name.lower() == city_name.lower():
                return city
        return None

    @property
    def available_cities(self) -> List[str]:
        """Get list of available city codes."""
        return list(self._cities.keys())


# Singleton instance
city_registry = CityRegistry()


def get_city_config(city_code: Optional[str] = None) -> CityConfig:
    """
    Convenience function to get city configuration.

    Args:
        city_code: Optional city code. If None, returns default city (Santa Monica).

    Returns:
        CityConfig instance

    Raises:
        ValueError: If city code not found
    """
    if city_code is None:
        return city_registry.get_default_city()

    city = city_registry.get_city(city_code)
    if city is None:
        raise ValueError(f"City '{city_code}' not found. Available cities: {city_registry.available_cities}")

    return city
