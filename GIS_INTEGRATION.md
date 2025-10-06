# Santa Monica GIS Integration Guide

## Overview

The Parcel Feasibility Engine now includes **interactive GIS capabilities** powered by Santa Monica's ArcGIS REST services. Users can click on any parcel on a map to automatically query zoning, overlays, historic designations, coastal zones, transit proximity, and other regulatory layers.

---

## Architecture

### 1. GIS Service Configuration

**File:** [`frontend/lib/gis-config.ts`](frontend/lib/gis-config.ts)

Centralized configuration for all ArcGIS REST endpoints:

```typescript
export const GIS_SERVICES = {
  PARCELS_PUBLIC: { url: '...' },    // 23,586 tax parcels with APN
  ZONING: { url: '...' },            // Base zoning + overlays
  HISTORIC: { url: '...' },          // Historic districts
  COASTAL_ZONE: { url: '...' },      // Coastal Zone boundary
  TRANSIT_STOPS: { url: '...' },     // LA Metro stops & Expo Line
  // ... more layers
};
```

**Santa Monica Bounding Box:**
- Center: 34.0195°N, -118.4912°W
- Zoom: 13
- Coverage: Full Santa Monica city limits

### 2. GIS Utilities

**File:** [`frontend/lib/gis-utils.ts`](frontend/lib/gis-utils.ts)

Core functions for querying ArcGIS FeatureServer endpoints:

#### Query Functions

```typescript
// Query by point (lat/lng click)
queryByPoint(serviceUrl, point, options)

// Query by polygon (parcel geometry)
queryByPolygon(serviceUrl, polygon, options)

// Query by attribute (WHERE clause)
queryByAttribute(serviceUrl, whereClause, options)
```

#### Distance Calculations

```typescript
// Haversine formula for distances in miles
calculateDistance(point1, point2)

// Find nearest transit stop
findNearestTransitStop(transitServiceUrl, point)

// Check AB 2097 eligibility (0.5 mi from transit)
checkAB2097Eligibility(transitServiceUrl, parcelPoint)
```

#### Batch Queries

```typescript
// Query all overlay layers at once
queryAllLayers(point, parcelGeometry, serviceUrls)
```

Returns:
- Zoning data
- Historic designation
- Coastal zone status
- Flood zones
- Specific plans
- Affordable housing overlays

### 3. TypeScript Types

**File:** [`frontend/lib/gis-types.ts`](frontend/lib/gis-types.ts)

Strong typing for all GIS data structures:

```typescript
interface ParcelOverlayData {
  parcel: ParcelGISData;
  zoning: ZoningData;
  historic: HistoricData;
  coastal: CoastalData;
  flood: FloodData;
  specificPlans: SpecificPlanData;
  affordableOverlay: AffordableOverlayData;
  transitProximity: TransitProximityData;
}
```

---

## Interactive Map Component

### ParcelMap Component

**File:** [`frontend/components/ParcelMap.tsx`](frontend/components/ParcelMap.tsx)

Leaflet-based interactive map with:

#### Features

1. **Click-to-Select Parcels**
   - User clicks anywhere on map
   - System queries `Parcels Public` layer
   - Highlights selected parcel in blue

2. **Automatic Overlay Queries**
   - Runs 6+ concurrent queries for:
     - Base zoning
     - Historic districts
     - Coastal zone
     - Flood zones
     - Specific plans
     - Affordable overlays
   - Displays results in info panel

3. **Transit Proximity**
   - Calculates distance to nearest Metro/Expo stop
   - Flags AB 2097 eligibility (0.5 mi threshold)
   - Shows stop name and distance

4. **Visual Feedback**
   - Loading spinner during queries
   - Error messages for failed requests
   - Info panel with overlay summary
   - Polygon highlighting with tooltips

#### Usage

```tsx
import ParcelMapWrapper from '@/components/ParcelMapWrapper';

<ParcelMapWrapper
  onParcelSelected={(gisData) => {
    // Auto-populate form with GIS data
    console.log(gisData.parcel.apn);
    console.log(gisData.zoning.zoneCode);
    console.log(gisData.transitProximity.ab2097Eligible);
  }}
  height="600px"
/>
```

### Map Wrapper (SSR Fix)

**File:** [`frontend/components/ParcelMapWrapper.tsx`](frontend/components/ParcelMapWrapper.tsx)

Dynamic import wrapper to avoid SSR issues with Leaflet (requires `window`):

```tsx
const ParcelMap = dynamic(() => import('./ParcelMap'), {
  ssr: false,
  loading: () => <LoadingSpinner />
});
```

---

## Data Flow

### 1. User Interaction

```
User clicks map at (34.0195, -118.4912)
  ↓
Convert to ArcGIS Point { x: -118.4912, y: 34.0195 }
  ↓
Query Parcels Public layer
  ↓
Retrieve parcel geometry (polygon) + APN
```

### 2. Overlay Queries (Parallel)

```
Promise.all([
  queryByPolygon(ZONING, parcelGeometry),
  queryByPolygon(HISTORIC, parcelGeometry),
  queryByPolygon(COASTAL, parcelGeometry),
  queryByPolygon(FLOOD, parcelGeometry),
  queryByPolygon(SPECIFIC_PLANS, parcelGeometry),
  queryByPolygon(AFFORDABLE_OVERLAY, parcelGeometry),
  checkAB2097Eligibility(TRANSIT_STOPS, parcelCentroid)
])
```

### 3. Result Aggregation

```typescript
{
  parcel: { apn: "4276-019-030", address: "123 Main St", ... },
  zoning: { zoneCode: "R1", maxHeight: 35, ... },
  historic: { isHistoric: false },
  coastal: { isCoastal: true, zoneType: "Appeal" },
  transitProximity: {
    ab2097Eligible: true,
    distance: 0.3,
    nearestStop: "Expo/Bundy Station"
  }
}
```

### 4. Callback to Parent

```tsx
onParcelSelected(aggregatedData)
  ↓
Auto-populate ParcelForm
  ↓
User clicks "Analyze Parcel"
  ↓
Full feasibility analysis runs
```

---

## State Law Integration

The GIS system automatically determines eligibility for California housing laws:

### SB 9 (2021) - Lot Splits & Duplexes

**Eligibility Checks:**
- ✅ Zone is single-family residential (R1)
- ✅ NOT in historic district
- ✅ NOT in coastal zone (or additional steps required)
- ✅ NOT in flood zone
- ✅ Lot size ≥ 2,400 sq ft (for split)

```typescript
const sb9Eligible =
  zoning.zoneCode === 'R1' &&
  !historic.isHistoric &&
  !coastal.isCoastal &&
  !flood.isInFloodZone &&
  parcel.lotArea >= 2400;
```

### SB 35 (2017) - Streamlined Approval

**Eligibility Checks:**
- ✅ Multi-family zone (R2, R3, R4)
- ✅ Meets affordability requirements
- ✅ NOT in historic district
- ✅ Within urbanized area

### AB 2097 (2022) - Parking Removal

**Eligibility Checks:**
- ✅ Within 0.5 miles of major transit stop
- ✅ Calculate using Haversine distance

```typescript
const ab2097Eligible = transitProximity.distance <= 0.5;
// Result: parking requirement = 0
```

### Density Bonus Law

**Bonus Calculations:**
- Query `Affordable Overlay` layer
- Check if parcel is in Housing Element rezoning
- Apply bonus percentages based on affordability

---

## ArcGIS REST Service URLs

### Updating Endpoints

When actual service URLs are obtained from Santa Monica's portal, update [`gis-config.ts`](frontend/lib/gis-config.ts):

```typescript
// Replace {OrgID} with actual organization ID
PARCELS_PUBLIC: {
  url: 'https://services5.arcgis.com/abcd1234/ArcGIS/rest/services/Parcels_Public/FeatureServer/0'
}
```

### Finding Service URLs

1. Navigate to [data.smgov.net](https://data.smgov.net)
2. Search for layer (e.g., "Parcels Public")
3. Click "View Item" or "View API"
4. Copy FeatureServer URL
5. Test with: `{url}?f=pjson`

### Example Query

```bash
curl "https://services5.arcgis.com/{OrgID}/ArcGIS/rest/services/Parcels_Public/FeatureServer/0/query?where=1=1&outFields=*&f=json" | jq
```

---

## Testing

### Test Parcels

Use these known Santa Monica parcels for testing:

| APN | Address | Zone | Special Notes |
|-----|---------|------|---------------|
| 4276-019-030 | 123 Main St | R1 | Standard single-family |
| 4293-001-015 | Ocean Ave | R2 | Near Expo Line (AB 2097) |
| 4285-012-008 | Montana Ave | C-2 | Commercial conversion (AB 2011) |
| 4280-005-020 | Pico Blvd | R3 | Specific Plan area |

### Test Workflow

1. Start dev server: `npm run dev`
2. Navigate to http://localhost:3001
3. Click "Select from Map"
4. Click on a parcel
5. Verify:
   - ✅ Parcel highlights in blue
   - ✅ APN displays in popup
   - ✅ Info panel shows zoning + overlays
   - ✅ Transit distance calculates
   - ✅ No console errors

---

## Performance Optimizations

### Caching

Implement request caching by APN:

```typescript
const cache = new Map<string, ParcelOverlayData>();

if (cache.has(apn)) {
  return cache.get(apn);
}

const data = await queryAllLayers(...);
cache.set(apn, data);
```

### Debouncing

Prevent excessive queries on rapid clicks:

```typescript
const handleMapClick = debounce(async (lat, lng) => {
  // Query logic
}, 500);
```

### Loading States

```tsx
{isLoading && (
  <div className="absolute top-4 right-4">
    <Loader2 className="animate-spin" />
    Querying GIS data...
  </div>
)}
```

---

## Error Handling

### Network Errors

```typescript
try {
  const result = await queryByPoint(url, point);
  if (result.error) {
    setError(result.error.message);
  }
} catch (err) {
  setError('Service unavailable');
}
```

### Missing Data

```typescript
const zoneCode = zoning?.attributes.ZONE_CODE || 'Unknown';
const isHistoric = !!historic; // Handle null safely
```

### Graceful Degradation

If a layer fails:
- Show warning icon
- Display partial results
- Allow user to proceed with manual input

---

## Future Enhancements

### Phase 2

1. **Form Auto-Population**
   - Map parcel data → ParcelForm fields
   - Pre-fill APN, address, lot size, zoning
   - One-click analysis from map selection

2. **Multi-Parcel Selection**
   - Draw polygon on map
   - Select multiple parcels
   - Batch analysis

3. **Layer Toggles**
   - Show/hide zoning districts
   - Overlay historic districts
   - Display transit buffers (0.5 mi radius)

### Phase 3

4. **3D Visualization**
   - Extrude parcels by height limit
   - Show development scenarios in 3D
   - Mapbox GL JS integration

5. **Advanced Filters**
   - Filter parcels by criteria
   - "Find all R1 parcels near transit"
   - "Show SB 9 eligible lots"

6. **Export Capabilities**
   - Export parcel analysis to PDF
   - Include map screenshot
   - Shareable report links

---

## Troubleshooting

### Map Not Loading

**Issue:** Blank white space instead of map

**Fix:**
```bash
# Ensure Leaflet CSS is imported
# Check frontend/app/layout.tsx for:
import "leaflet/dist/leaflet.css";
```

### Marker Icons Missing

**Issue:** Blue squares instead of map pins

**Fix:**
```typescript
// Add to ParcelMap.tsx
import L from 'leaflet';
import 'leaflet/dist/images/marker-icon.png';
import 'leaflet/dist/images/marker-shadow.png';
```

### CORS Errors

**Issue:** `Access-Control-Allow-Origin` errors

**Fix:**
- Use proxy in Next.js API routes
- Or request CORS enablement from Santa Monica IT

### Service Timeouts

**Issue:** Queries taking > 10 seconds

**Fix:**
```typescript
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);

fetch(url, { signal: controller.signal });
```

---

## API Reference

### GIS Utilities

```typescript
// Point queries
queryByPoint(url: string, point: Point, options?: QueryOptions): Promise<ArcGISQueryResult>

// Polygon queries
queryByPolygon(url: string, polygon: Polygon, options?: QueryOptions): Promise<ArcGISQueryResult>

// Attribute queries
queryByAttribute(url: string, where: string, options?: QueryOptions): Promise<ArcGISQueryResult>

// Distance calculations
calculateDistance(point1: Point, point2: Point): number // miles

// Transit checks
checkAB2097Eligibility(transitUrl: string, parcelPoint: Point): Promise<{
  eligible: boolean;
  distance: number;
  nearestStop?: string;
}>

// Batch queries
queryAllLayers(point: Point, geometry: Polygon, urls: ServiceUrls): Promise<OverlayData>
```

### Types

See [`gis-types.ts`](frontend/lib/gis-types.ts) for complete type definitions.

---

*Last Updated: October 2025*
*Parcel Feasibility Engine v1.0*
