"""Parcel cache model for fast autocomplete lookups."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class ParcelCache(SQLModel, table=True):
    """Cached Santa Monica parcel data for quick lookups."""
    __tablename__ = "parcel_cache"

    id: Optional[int] = Field(default=None, primary_key=True)
    apn: str = Field(index=True, unique=True)
    address: str = Field(index=True)
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    city: str = "Santa Monica"
    zip_code: Optional[str] = None
    lot_size_sqft: Optional[float] = None
    zoning_code: Optional[str] = None
    existing_units: Optional[int] = None
    geometry_wkt: Optional[str] = None  # WKT format for parcel boundary
    last_updated: datetime = Field(default_factory=datetime.utcnow)
