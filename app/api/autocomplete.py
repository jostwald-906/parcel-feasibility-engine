"""Autocomplete API endpoints for parcel search."""
from fastapi import APIRouter, Query, HTTPException
from typing import List
from sqlmodel import Session, select, or_
from app.core.database import engine
from app.models.parcel_cache import ParcelCache
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/autocomplete", tags=["Autocomplete"])


class AutocompleteResult(BaseModel):
    """Autocomplete result for a parcel."""
    apn: str
    address: str
    zoning_code: str | None = None
    lot_size_sqft: float | None = None


@router.get("/parcels", response_model=List[AutocompleteResult])
async def autocomplete_parcels(
    q: str = Query(..., min_length=2, description="Search query (APN or address)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Autocomplete search for Santa Monica parcels.

    Searches by APN or address and returns matching results.

    Args:
        q: Search query (minimum 2 characters)
        limit: Maximum number of results (default 10, max 50)

    Returns:
        List of matching parcels with APN, address, zoning, and lot size
    """
    try:
        with Session(engine) as session:
            # Search by APN or address
            statement = (
                select(ParcelCache)
                .where(
                    or_(
                        ParcelCache.apn.ilike(f"{q}%"),
                        ParcelCache.address.ilike(f"%{q}%")
                    )
                )
                .limit(limit)
            )

            parcels = session.exec(statement).all()

            return [
                AutocompleteResult(
                    apn=p.apn,
                    address=p.address or "",
                    zoning_code=p.zoning_code,
                    lot_size_sqft=p.lot_size_sqft
                )
                for p in parcels
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete search failed: {str(e)}")
