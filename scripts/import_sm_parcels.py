"""
Import Santa Monica parcel data from GIS services.
Populates the parcel_cache table for autocomplete.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlmodel import Session, SQLModel, create_engine, select
from app.models.parcel_cache import ParcelCache
from app.core.config import settings

# Santa Monica GIS REST service for parcels
SANTA_MONICA_PARCELS_URL = "https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer/0/query"


async def fetch_all_parcels():
    """Fetch all Santa Monica parcels from GIS service."""
    print("Fetching parcels from Santa Monica GIS service...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        params = {
            "where": "1=1",
            "outFields": "APN,SiteAddress,ZONING,LotSizeSF,OBJECTID",
            "f": "json",
            "resultRecordCount": 1000,
            "resultOffset": 0
        }

        all_features = []
        batch_count = 0

        while True:
            try:
                response = await client.get(SANTA_MONICA_PARCELS_URL, params=params)
                response.raise_for_status()
                data = response.json()

                features = data.get("features", [])

                if not features:
                    break

                all_features.extend(features)
                batch_count += 1
                print(f"  Fetched batch {batch_count}: {len(features)} parcels (total: {len(all_features)})")

                params["resultOffset"] += len(features)

                # Safety limit
                if len(all_features) > 50000:
                    print("  Reached 50,000 parcel limit, stopping fetch")
                    break

            except httpx.HTTPError as e:
                print(f"  HTTP error during fetch: {e}")
                break

        return all_features


async def import_parcels():
    """Import parcels into database."""
    # Create engine and check if we need to update
    engine = create_engine(str(settings.DATABASE_URL))
    SQLModel.metadata.create_all(engine)

    # Check if we already pulled data today
    with Session(engine) as session:
        from datetime import datetime, timedelta

        # Check most recent update timestamp
        latest_parcel = session.exec(
            select(ParcelCache).order_by(ParcelCache.last_updated.desc()).limit(1)
        ).first()

        if latest_parcel:
            time_since_update = datetime.utcnow() - latest_parcel.last_updated
            if time_since_update < timedelta(days=1):
                print(f"Data was updated {time_since_update} ago. Skipping import (updates are limited to once per day).")
                print(f"Last update: {latest_parcel.last_updated}")
                print(f"Next update available after: {latest_parcel.last_updated + timedelta(days=1)}")
                return

    # Fetch parcels from GIS
    features = await fetch_all_parcels()

    if not features:
        print("No parcels fetched. Exiting.")
        return

    print(f"\nImporting {len(features)} parcels into database...")

    imported_count = 0
    skipped_count = 0
    error_count = 0

    with Session(engine) as session:
        for feature in features:
            try:
                attrs = feature.get("attributes", {})

                # Skip if no APN
                apn = attrs.get("APN")
                if not apn or apn.strip() == "":
                    skipped_count += 1
                    continue

                # Check if parcel already exists
                existing = session.exec(
                    select(ParcelCache).where(ParcelCache.apn == apn)
                ).first()

                if existing:
                    # Update existing record
                    existing.address = attrs.get("SiteAddress", "")
                    existing.lot_size_sqft = attrs.get("LotSizeSF")
                    existing.zoning_code = attrs.get("ZONING")
                    session.add(existing)
                else:
                    # Create new record
                    parcel = ParcelCache(
                        apn=apn,
                        address=attrs.get("SiteAddress", ""),
                        lot_size_sqft=attrs.get("LotSizeSF"),
                        zoning_code=attrs.get("ZONING"),
                        # Parse geometry if available (WKT conversion)
                        geometry_wkt=None  # TODO: Convert geometry to WKT if needed
                    )
                    session.add(parcel)

                imported_count += 1

                # Commit in batches
                if imported_count % 100 == 0:
                    session.commit()
                    print(f"  Committed {imported_count} parcels...")

            except Exception as e:
                error_count += 1
                print(f"  Error importing parcel {attrs.get('APN', 'UNKNOWN')}: {e}")
                continue

        # Final commit
        session.commit()

    print(f"\nImport complete!")
    print(f"  Successfully imported: {imported_count}")
    print(f"  Skipped (no APN): {skipped_count}")
    print(f"  Errors: {error_count}")


if __name__ == "__main__":
    asyncio.run(import_parcels())
