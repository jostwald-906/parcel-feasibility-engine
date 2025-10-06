"""
Configuration settings for the Parcel Feasibility Engine.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ============================================
    # API Configuration
    # ============================================
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Santa Monica Parcel Feasibility Engine"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "California housing development feasibility analysis API"

    # Debug & Logging
    API_DEBUG_MODE: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    DEBUG: bool = False

    # ============================================
    # Database Configuration
    # ============================================
    DATABASE_URL: str = "sqlite:///./parcel_feasibility.db"

    # ============================================
    # CORS Configuration
    # ============================================
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ============================================
    # Feature Flags - State Housing Laws
    # ============================================
    ENABLE_AB2011: bool = True
    ENABLE_SB35: bool = True
    ENABLE_DENSITY_BONUS: bool = True
    ENABLE_SB9: bool = True
    ENABLE_AB2097: bool = True

    # ============================================
    # GIS Service Endpoints
    # ============================================
    # Santa Monica GIS Services
    SANTA_MONICA_PARCEL_SERVICE_URL: str = "https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer"
    SANTA_MONICA_ZONING_SERVICE_URL: str = "https://gis.smgov.net/arcgis/rest/services/Planning/Zoning/MapServer"
    SANTA_MONICA_OVERLAY_SERVICE_URL: str = "https://gis.smgov.net/arcgis/rest/services/Planning/Overlays/MapServer"
    SANTA_MONICA_TRANSIT_SERVICE_URL: str = "https://gis.smgov.net/arcgis/rest/services/Transportation/Transit/MapServer"

    # Regional GIS Services
    SCAG_REGIONAL_SERVICE_URL: str = "https://gisdata.scag.ca.gov/arcgis/rest/services"
    METRO_TRANSIT_SERVICE_URL: str = "https://developer.metro.net/gis/"

    # GIS Configuration
    GIS_REQUEST_TIMEOUT: int = 30
    GIS_MAX_RETRIES: int = 3
    GIS_CACHE_TTL: int = 3600

    # ============================================
    # External Services
    # ============================================
    # Geocoding
    GEOCODING_API_KEY: Optional[str] = None
    GEOCODING_PROVIDER: str = "google"

    # LLM Narrative Generation
    OPENAI_API_KEY: Optional[str] = None
    NARRATIVE_MODEL: str = "gpt-4"
    ENABLE_NARRATIVE_GENERATION: bool = False

    # ============================================
    # Analysis Defaults
    # ============================================
    DEFAULT_PARKING_SPACE_SIZE: float = 320.0  # sq ft
    DEFAULT_UNIT_SIZE: float = 1000.0  # sq ft
    MIN_OPEN_SPACE_PER_UNIT: float = 100.0  # sq ft

    # ============================================
    # Security
    # ============================================
    API_KEY_ENABLED: bool = False
    API_KEY: Optional[str] = None
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    # ============================================
    # Environment
    # ============================================
    ENVIRONMENT: str = "development"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature flag is enabled."""
        feature_map = {
            "ab2011": self.ENABLE_AB2011,
            "sb35": self.ENABLE_SB35,
            "density_bonus": self.ENABLE_DENSITY_BONUS,
            "sb9": self.ENABLE_SB9,
            "ab2097": self.ENABLE_AB2097,
        }
        return feature_map.get(feature.lower(), False)


# Create global settings instance
settings = Settings()
