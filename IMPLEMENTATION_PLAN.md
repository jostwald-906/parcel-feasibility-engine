# Implementation Plan - Frontend Improvements

## Priority 1: Fix Network Error (CRITICAL)

### Issue
Frontend is getting "Network Error" when calling the analyze API endpoint.

### Root Cause Investigation Needed
The frontend types show `AnalysisRequest` has a `parcel` field which matches the backend schema. Need to investigate:
1. Check ParcelForm component to see how it constructs the AnalysisRequest
2. Check browser console/network tab for actual request payload
3. Verify CORS headers from Railway backend

### Action Items
1. Check [ParcelForm.tsx](frontend/components/ParcelForm.tsx) - line where `onAnalyze` is called
2. Add console.log before API call to inspect request payload
3. Test with curl to verify backend is working:
   ```bash
   curl -X POST https://parcel-feasibility-engine-production.up.railway.app/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "parcel": {
         "apn": "4293-001-001",
         "address": "123 Main St, Santa Monica, CA",
         "lot_size_sqft": 5000,
         "zoning_code": "R1",
         "existing_units": 1
       },
       "include_sb9": true,
       "include_density_bonus": true
     }'
   ```
4. Check Railway backend CORS settings - may need to add Vercel domain to `BACKEND_CORS_ORIGINS`

---

## Priority 2: APN Autocomplete with Real Data

### Current State
- Typing an APN shows a dropdown with fake/placeholder APNs
- No addresses are shown
- No real Santa Monica parcel data

### Implementation Steps

#### Backend Changes

**1. Create Parcel Database Table**
File: `app/models/parcel_cache.py`
```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ParcelCache(SQLModel, table=True):
    """Cached Santa Monica parcel data for quick lookups."""
    __tablename__ = "parcel_cache"

    id: Optional[int] = Field(default=None, primary_key=True)
    apn: str = Field(index=True, unique=True)
    address: str = Field(index=True)
    street_number: Optional[str]
    street_name: Optional[str]
    city: str = "Santa Monica"
    zip_code: Optional[str]
    lot_size_sqft: Optional[float]
    zoning_code: Optional[str]
    existing_units: Optional[int]
    geometry_wkt: Optional[str]  # WKT format for parcel boundary
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

**2. Create GIS Data Import Script**
File: `scripts/import_sm_parcels.py`
```python
"""
Import Santa Monica parcel data from GIS services.
Populates the parcel_cache table for autocomplete.
"""
import asyncio
import httpx
from app.core.database import engine
from app.models.parcel_cache import ParcelCache
from sqlmodel import Session, select

SANTA_MONICA_PARCELS_URL = "https://gis.smgov.net/arcgis/rest/services/PublicWorks/Parcels/MapServer/0/query"

async def fetch_all_parcels():
    """Fetch all Santa Monica parcels from GIS service."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        params = {
            "where": "1=1",
            "outFields": "APN,SiteAddress,ZONING,LotSizeSF",
            "f": "json",
            "resultRecordCount": 5000,
            "resultOffset": 0
        }

        all_features = []
        while True:
            response = await client.get(SANTA_MONICA_PARCELS_URL, params=params)
            data = response.json()
            features = data.get("features", [])

            if not features:
                break

            all_features.extend(features)
            params["resultOffset"] += len(features)

        return all_features

async def import_parcels():
    """Import parcels into database."""
    features = await fetch_all_parcels()

    with Session(engine) as session:
        for feature in features:
            attrs = feature["attributes"]

            parcel = ParcelCache(
                apn=attrs.get("APN"),
                address=attrs.get("SiteAddress"),
                lot_size_sqft=attrs.get("LotSizeSF"),
                zoning_code=attrs.get("ZONING"),
                # Parse geometry if available
                geometry_wkt=None  # TODO: Convert geometry to WKT
            )

            session.add(parcel)

        session.commit()
        print(f"Imported {len(features)} parcels")

if __name__ == "__main__":
    asyncio.run(import_parcels())
```

**3. Create Autocomplete API Endpoint**
File: `app/api/autocomplete.py`
```python
from fastapi import APIRouter, Query
from typing import List
from sqlmodel import Session, select, or_
from app.core.database import engine
from app.models.parcel_cache import ParcelCache
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/autocomplete", tags=["Autocomplete"])

class AutocompleteResult(BaseModel):
    apn: str
    address: str
    zoning_code: str | None
    lot_size_sqft: float | None

@router.get("/parcels", response_model=List[AutocompleteResult])
async def autocomplete_parcels(
    q: str = Query(..., min_length=2, description="Search query (APN or address)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Autocomplete search for Santa Monica parcels.

    Searches by APN or address and returns matching results.
    """
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
                address=p.address,
                zoning_code=p.zoning_code,
                lot_size_sqft=p.lot_size_sqft
            )
            for p in parcels
        ]
```

Add router to `app/main.py`:
```python
from app.api import autocomplete
app.include_router(autocomplete.router)
```

#### Frontend Changes

**1. Create Autocomplete Component**
File: `frontend/components/APNAutocomplete.tsx`
```typescript
import { useState, useEffect } from 'react';
import axios from 'axios';

interface AutocompleteResult {
  apn: string;
  address: string;
  zoning_code: string | null;
  lot_size_sqft: number | null;
}

interface Props {
  value: string;
  onChange: (apn: string, result?: AutocompleteResult) => void;
}

export default function APNAutocomplete({ value, onChange }: Props) {
  const [query, setQuery] = useState(value);
  const [results, setResults] = useState<AutocompleteResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    const search = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/autocomplete/parcels`,
          { params: { q: query, limit: 10 } }
        );
        setResults(response.data);
        setShowResults(true);
      } catch (error) {
        console.error('Autocomplete error:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    const debounce = setTimeout(search, 300);
    return () => clearTimeout(debounce);
  }, [query]);

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setShowResults(true)}
        onBlur={() => setTimeout(() => setShowResults(false), 200)}
        placeholder="Enter APN or address..."
        className="w-full px-4 py-2 border rounded-lg"
      />

      {showResults && results.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {results.map((result) => (
            <button
              key={result.apn}
              onClick={() => {
                setQuery(result.apn);
                onChange(result.apn, result);
                setShowResults(false);
              }}
              className="w-full px-4 py-2 text-left hover:bg-blue-50 border-b last:border-b-0"
            >
              <div className="font-semibold">{result.apn}</div>
              <div className="text-sm text-gray-600">{result.address}</div>
              <div className="text-xs text-gray-500">
                {result.zoning_code} • {result.lot_size_sqft?.toLocaleString()} sqft
              </div>
            </button>
          ))}
        </div>
      )}

      {isLoading && (
        <div className="absolute right-3 top-3">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 rounded-full border-t-transparent" />
        </div>
      )}
    </div>
  );
}
```

**2. Integrate into ParcelForm**
Replace the APN input field in `frontend/components/ParcelForm.tsx`:
```typescript
import APNAutocomplete from './APNAutocomplete';

// In the form:
<APNAutocomplete
  value={formData.apn}
  onChange={(apn, result) => {
    setFormData(prev => ({
      ...prev,
      apn,
      address: result?.address || prev.address,
      lot_size_sqft: result?.lot_size_sqft || prev.lot_size_sqft,
      zoning_code: result?.zoning_code || prev.zoning_code
    }));
  }}
/>
```

---

## Priority 3: Expand Proposed Project Details

### Current State
Very sparse - only has "Average Bedrooms per Unit" and "For-Sale Project" checkbox.

### Proposed Expanded Form

Add the following fields to the "Proposed Project Details" section:

#### Project Type & Use
- [ ] Ownership Type (For-Sale, Rental, Mixed)
- [ ] Mixed-Use Project (Yes/No)
  - If Yes: Ground Floor Use (Retail, Office, Commercial, Live-Work)
  - Commercial Square Footage

#### Building Specifications
- [ ] Proposed Stories (number)
- [ ] Proposed Height (feet)
- [ ] Total Proposed Units (number)
- [ ] Average Unit Size (sqft)
- [ ] Total Building Square Footage

#### Unit Mix Breakdown
- [ ] Studio Units (count)
- [ ] 1-Bedroom Units (count)
- [ ] 2-Bedroom Units (count)
- [ ] 3+ Bedroom Units (count)

#### Affordable Housing Plan
- [ ] Total Affordable Units (number)
- [ ] Very Low Income Units (< 50% AMI) - count & percentage
- [ ] Low Income Units (50-80% AMI) - count & percentage
- [ ] Moderate Income Units (80-120% AMI) - count & percentage
- [ ] Affordability Duration (years) - default 55

#### Parking & Access
- [ ] Proposed Parking Spaces (number)
- [ ] Parking Type (Surface, Underground, Structured, Mixed)
- [ ] Bicycle Parking Spaces (number)

#### Site Configuration
- [ ] Lot Coverage Percentage (calculated or manual)
- [ ] Open Space (sqft)
- [ ] Setbacks (Front, Rear, Side - feet)

### Implementation

**1. Update Parcel Interface**
File: `frontend/lib/types.ts`
```typescript
export interface ProposedProject {
  // Existing
  average_bedrooms_per_unit?: number;
  for_sale_project?: boolean;

  // New fields
  ownership_type?: 'for-sale' | 'rental' | 'mixed';
  mixed_use?: boolean;
  ground_floor_use?: 'retail' | 'office' | 'commercial' | 'live-work' | null;
  commercial_sqft?: number;

  proposed_stories?: number;
  proposed_height_ft?: number;
  proposed_units?: number;
  average_unit_size_sqft?: number;
  total_building_sqft?: number;

  unit_mix?: {
    studio: number;
    one_bedroom: number;
    two_bedroom: number;
    three_plus_bedroom: number;
  };

  affordable_housing?: {
    total_affordable_units: number;
    very_low_income_units: number;  // <50% AMI
    low_income_units: number;        // 50-80% AMI
    moderate_income_units: number;   // 80-120% AMI
    affordability_duration_years: number;
  };

  parking?: {
    proposed_spaces: number;
    parking_type: 'surface' | 'underground' | 'structured' | 'mixed';
    bicycle_spaces: number;
  };

  site_configuration?: {
    lot_coverage_pct: number;
    open_space_sqft: number;
    setbacks: {
      front_ft: number;
      rear_ft: number;
      side_ft: number;
    };
  };
}
```

**2. Update Backend Models**
File: `app/models/parcel.py` - add ProposedProject model matching frontend

**3. Create Comprehensive Form Component**
File: `frontend/components/ProposedProjectForm.tsx`
- Group fields into collapsible sections
- Add validation (e.g., affordable units ≤ total units)
- Auto-calculate fields (e.g., total affordable = sum of income tiers)
- Show warnings (e.g., "Exceeds base zoning height")

**4. Add Validation Logic**
File: `app/rules/proposed_validation.py`
```python
def validate_proposed_vs_allowed(
    proposed: ProposedProject,
    allowed: DevelopmentScenario
) -> List[ValidationWarning]:
    """
    Compare proposed project against allowed scenario.
    Returns list of warnings/violations.
    """
    warnings = []

    if proposed.proposed_units > allowed.max_units:
        warnings.append({
            "field": "proposed_units",
            "severity": "error",
            "message": f"Proposed {proposed.proposed_units} units exceeds maximum allowed {allowed.max_units}"
        })

    if proposed.proposed_height_ft > allowed.max_height_ft:
        warnings.append({
            "field": "proposed_height_ft",
            "severity": "warning",
            "message": f"Proposed height {proposed.proposed_height_ft}ft exceeds base zoning {allowed.max_height_ft}ft (may qualify for height bonus)"
        })

    # Check parking compliance
    if proposed.parking.proposed_spaces < allowed.parking_spaces_required:
        warnings.append({
            "field": "parking_spaces",
            "severity": "warning",
            "message": f"Proposed {proposed.parking.proposed_spaces} spaces is less than required {allowed.parking_spaces_required} (check AB2097 eligibility)"
        })

    return warnings
```

---

## Testing Checklist

### Network Error Fix
- [ ] Can submit analysis request without error
- [ ] Backend receives correct payload format
- [ ] Results display properly in frontend

### APN Autocomplete
- [ ] Search by APN returns results
- [ ] Search by address returns results
- [ ] Selecting result auto-fills form fields
- [ ] Database contains recent Santa Monica parcel data

### Proposed Project Details
- [ ] All new fields save correctly
- [ ] Validation warnings show appropriately
- [ ] Proposed vs. allowed comparison works
- [ ] Affordability calculations are correct

---

## Deployment Steps

After implementing fixes:

1. **Backend**
   ```bash
   # Run parcel import script
   python scripts/import_sm_parcels.py

   # Push to GitHub
   git add .
   git commit -m "feat: Add APN autocomplete and expanded project details"
   git push origin main

   # Railway will auto-deploy
   ```

2. **Frontend**
   ```bash
   # Push to GitHub
   git add .
   git commit -m "feat: Add APN autocomplete and expanded project form"
   git push origin main

   # Vercel will auto-deploy
   ```

3. **Environment Variables** (if needed)
   - Railway: Add any new config vars
   - Vercel: Verify `NEXT_PUBLIC_API_URL` still set

---

## Estimated Time

- Network Error Fix: **30 minutes**
- APN Autocomplete: **3-4 hours** (backend + frontend + data import)
- Expanded Project Details: **4-6 hours** (form redesign + validation logic)

**Total: ~8-10 hours of development work**

---

## Next Session Priorities

1. Start with Network Error debugging (quick win)
2. Then APN autocomplete (high user value)
3. Then expanded form (comprehensive but time-intensive)

Good luck! 🚀
