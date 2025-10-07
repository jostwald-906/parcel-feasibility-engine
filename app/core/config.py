"""
Configuration settings for the Parcel Feasibility Engine.
"""
from pydantic import Field
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
    DATABASE_URL: str = Field(
        default="sqlite:///./parcel_feasibility.db",
        description="Database connection string (PostgreSQL in production, SQLite in dev)"
    )

    # ============================================
    # CORS Configuration
    # ============================================
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://parcel-feasibility-engine.vercel.app",
        "https://*.vercel.app"
    ]

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

    # GIS Cache Configuration
    GIS_CACHE_MAX_SIZE: int = 1000  # Maximum number of parcels to cache in memory
    GIS_CACHE_TTL_HOURS: int = 24  # Cache time-to-live in hours

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
    # Security & Authentication
    # ============================================
    API_KEY_ENABLED: bool = False
    API_KEY: Optional[str] = None
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    # JWT Authentication
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ============================================
    # Payment Processing (Stripe)
    # ============================================
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID_PRO: Optional[str] = None  # Monthly subscription price ID

    # Subscription limits (for free tier if implemented)
    FREE_TIER_MONTHLY_LIMIT: int = 3
    REQUIRE_SUBSCRIPTION: bool = False  # Set to True to enforce subscriptions

    # ============================================
    # Construction Cost Estimation
    # ============================================
    # Base cost parameters
    REF_COST_PER_SF: float = 350.0  # 2025 US baseline cost per SF
    REF_PPI_DATE: str = "2025-01-01"  # Reference date for PPI baseline
    REF_PPI_VALUE: float = 140.0  # Baseline PPI value for escalation calculations

    # Soft cost percentages
    ARCHITECTURE_PCT: float = 0.10  # Architecture/Engineering as % of hard cost
    LEGAL_PCT: float = 0.04  # Legal/Consulting as % of hard cost
    DEVELOPER_FEE_PCT: float = 0.15  # Developer fee as % of (hard + soft)
    CONTINGENCY_PCT: float = 0.12  # Contingency as % of (hard + soft)

    # Financing parameters
    CONSTRUCTION_LOAN_SPREAD: float = 0.025  # 2.5% spread over 10Y Treasury

    # Common area factor
    COMMON_AREA_FACTOR: float = 1.15  # 15% additional SF for common areas

    # FRED API configuration
    FRED_API_KEY: Optional[str] = None  # Federal Reserve Economic Data API key
    FRED_API_ENABLED: bool = False  # Enable live FRED data fetching

    # HUD FMR API configuration
    HUD_API_TOKEN: Optional[str] = None  # HUD Fair Market Rents API token
    CENSUS_API_KEY: Optional[str] = None  # US Census Bureau API key (optional)

    # ============================================
    # Error Monitoring (Sentry)
    # ============================================
    SENTRY_DSN: Optional[str] = None  # Sentry Data Source Name for error tracking
    SENTRY_ENABLED: bool = False  # Enable Sentry error monitoring
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions for performance monitoring
    SENTRY_ENVIRONMENT: Optional[str] = None  # Sentry environment (defaults to ENVIRONMENT)

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
