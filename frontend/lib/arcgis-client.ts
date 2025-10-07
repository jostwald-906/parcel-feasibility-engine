/**
 * Typed ArcGIS REST API Client
 *
 * Provides type-safe query functions for Santa Monica GIS services.
 * Uses the auto-discovered service endpoints from connections.json.
 */

import { queryByPoint, queryByPolygon, queryByAttribute, calculateDistance } from './gis-utils';
import type { Point, Polygon, ArcGISQueryResult } from './gis-utils';

// Import discovered service endpoints
import connectionsData from './connections.json';

const connections = connectionsData as {
  parcels?: { url: string; fields: Record<string, string> };
  zoning?: { url: string; fields: Record<string, string> };
  historic?: { url: string; fields: Record<string, string> };
  coastal?: { url: string; fields: Record<string, string> };
  flood?: { url: string; fields: Record<string, string> };
  transit?: { url: string; fields: Record<string, string> };
  parking?: { url: string; fields: Record<string, string> };
  setbacks?: { url: string; fields: Record<string, string> };
  streets?: { url: string; fields: Record<string, string> };
  overlays?: Array<{ url: string; layerName: string }>;
  hazards?: Array<{ url: string; layerName: string }>;
};

/**
 * Parcel data structure
 */
export interface ParcelData {
  apn: string;
  ain: string;
  address: string;
  situsFullAddress: string;
  city: string;
  zip: string;
  useCode: string;
  useType: string;
  useDescription: string;
  yearBuilt?: string;
  units?: number;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
  geometry?: Polygon;
  lotSizeSqft?: number;
  lotWidth?: number;
  lotDepth?: number;
  latitude?: number;
  longitude?: number;
}

/**
 * Zoning data structure
 */
export interface ZoningData {
  zoneCode: string;
  zoneDescription: string;
  overlay?: string;
  overlayDescription?: string;
  majorCategory: string;
}

/**
 * Historic preservation data
 */
export interface HistoricData {
  isHistoric: boolean;
  resourceName?: string;
  resourceEvaluation?: string;
  districtName?: string;
  inDistrict?: boolean;
  individuallyEligible?: boolean;
  architecturalStyle?: string;
  yearBuilt?: string;
}

/**
 * Coastal zone data
 */
export interface CoastalData {
  inCoastalZone: boolean;
  zoneType?: string;
}

/**
 * Flood zone data (FEMA)
 */
export interface FloodData {
  inFloodZone: boolean;
  fldZone?: string;
  floodway?: boolean;
  bfe?: number; // Base Flood Elevation
}

/**
 * Transit proximity data (for AB 2097)
 */
export interface TransitProximityData {
  nearestStopName?: string;
  nearestStopDistance?: number; // meters
  withinHalfMile: boolean; // AB 2097 eligibility
  stopType?: string;
}

/**
 * Parking overlay data
 */
export interface ParkingData {
  unbundledParkingRequired: boolean;
  parkingDistrict?: string;
}

/**
 * Development standards/setbacks
 */
export interface SetbackData {
  frontSetback?: number;
  sideSetback?: number;
  rearSetback?: number;
  maxHeight?: number;
}

/**
 * Geohazard data
 */
export interface HazardData {
  faultZone: boolean;
  liquefactionZone: boolean;
  landslideZone: boolean;
  seismicHazardZone: boolean;
}

/**
 * Specific plan/overlay data
 */
export interface OverlayData {
  name: string;
  type: string;
  description?: string;
}

/**
 * CNEL noise data
 */
export interface CNELData {
  cnel_db: number | null;
  category?: string;
}

/**
 * Street right-of-way data
 */
export interface StreetROWData {
  rowWidth: number | null; // Right-of-way width in feet
  streetName: string | null;
  streetType: string | null; // Arterial, collector, local, etc.
  dataSource: 'gis' | 'estimated' | 'manual';
  estimationNote?: string;
}

/**
 * Environmental data for SB35 and AB2011 site exclusion checks
 */
export interface EnvironmentalData {
  inWetlands: boolean;
  inConservationArea: boolean;
  fireHazardZone: string | null; // "Very High", "High", "Moderate", or null
  nearHazardousWaste: boolean;
  inEarthquakeFaultZone: boolean;
}

/**
 * Complete parcel analysis result
 */
export interface ParcelAnalysis {
  parcel: ParcelData;
  zoning: ZoningData;
  historic: HistoricData;
  coastal: CoastalData;
  flood: FloodData;
  transit: TransitProximityData;
  parking: ParkingData;
  setbacks: SetbackData;
  hazards: HazardData;
  overlays: OverlayData[];
  cnel?: CNELData;
  environmental: EnvironmentalData;
  street: StreetROWData;
}

/**
 * Get parcel data at a specific point (map click)
 */
export async function getParcelAtPoint(lon: number, lat: number): Promise<ParcelData | null> {
  if (!connections.parcels) {
    throw new Error('Parcels service not configured');
  }

  const point: Point = { x: lon, y: lat, spatialReference: { wkid: 4326 } };
  const result = await queryByPoint(connections.parcels.url, point, {
    outFields: '*',
    returnGeometry: true,
  });

  if (!result.features || result.features.length === 0) {
    return null;
  }

  const feature = result.features[0];
  const attrs = feature.attributes;

  // Ensure geometry has spatial reference (should be 2229 State Plane)
  const geometry = feature.geometry as Polygon | undefined;
  if (geometry && !geometry.spatialReference) {
    geometry.spatialReference = result.spatialReference || { wkid: 2229 };
  }

  // Calculate lot size and dimensions from geometry
  const lotSizeSqft = attrs.Shape__Area && typeof attrs.Shape__Area === 'number' ? Math.round(attrs.Shape__Area) : undefined;
  let lotWidth: number | undefined;
  let lotDepth: number | undefined;

  if (geometry && lotSizeSqft) {
    // Calculate dimensions using the same logic as the simple client
    const ring = geometry.rings?.[0];
    if (ring && ring.length >= 3) {
      const edges: number[] = [];
      for (let i = 0; i < ring.length - 1; i++) {
        const [x1, y1] = ring[i];
        const [x2, y2] = ring[i + 1];
        const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        edges.push(length);
      }

      if (edges.length >= 1) {
        const sortedEdges = [...edges].sort((a, b) => b - a);
        const longestEdge = sortedEdges[0];
        const depth = lotSizeSqft / longestEdge;
        lotWidth = Math.round(longestEdge);
        lotDepth = Math.round(depth);
      }
    }
  }

  return {
    apn: String(attrs.apn || attrs.APN || ''),
    ain: String(attrs.ain || attrs.AIN || ''),
    address: String(attrs.situsaddress || attrs.SITUSADDRESS || ''),
    situsFullAddress: String(attrs.situsfulladdress || attrs.SITUSFULLADDRESS || ''),
    city: String(attrs.situscity || attrs.SITUSCITY || 'Santa Monica'),
    zip: String(attrs.situszip || attrs.SITUSZIP || ''),
    useCode: String(attrs.usecode || attrs.USECODE || ''),
    useType: String(attrs.usetype || attrs.UseType || attrs.USETYPE || ''),
    useDescription: String(attrs.usedescription || attrs.USEDESCRIPTION || ''),
    yearBuilt: attrs.yearbuilt1 ? String(attrs.yearbuilt1) : attrs.YEARBUILT1 ? String(attrs.YEARBUILT1) : undefined,
    units: typeof attrs.units1 === 'number' ? attrs.units1 : typeof attrs.UNITS1 === 'number' ? attrs.UNITS1 : undefined,
    bedrooms: typeof attrs.bedrooms1 === 'number' ? attrs.bedrooms1 : typeof attrs.BEDROOMS1 === 'number' ? attrs.BEDROOMS1 : undefined,
    bathrooms: typeof attrs.bathrooms1 === 'number' ? attrs.bathrooms1 : typeof attrs.BATHROOMS1 === 'number' ? attrs.BATHROOMS1 : undefined,
    sqft: typeof attrs.sqftmain1 === 'number' ? attrs.sqftmain1 : typeof attrs.SQFTMAIN1 === 'number' ? attrs.SQFTMAIN1 : undefined,
    lotSizeSqft,
    lotWidth,
    lotDepth,
    geometry,
  };
}

/**
 * Get zoning information for a parcel geometry
 */
export async function getZoningForParcel(parcelGeom: Polygon, centerPoint?: Point): Promise<ZoningData | null> {
  if (!connections.zoning) {
    throw new Error('Zoning service not configured');
  }

  // If we have a center point, use point query which is more reliable than polygon intersection
  if (centerPoint) {
    console.log('Querying zoning with center point:', centerPoint);

    const result = await queryByPoint(connections.zoning.url, centerPoint, {
      outFields: '*',
      returnGeometry: false,
    });

    if (result.error) {
      console.error('Zoning query error:', result.error);
    }

    if (!result.features || result.features.length === 0) {
      console.warn('No zoning features found for center point');
      return null;
    }

    const attrs = result.features[0].attributes;
    console.log('Zoning query result:', attrs);

    return {
      zoneCode: String(attrs.zoning || attrs.ZONING || attrs.zone_code || ''),
      zoneDescription: String(attrs.zonedesc || attrs.ZONEDESC || ''),
      overlay: attrs.overlay ? String(attrs.overlay) : attrs.OVERLAY ? String(attrs.OVERLAY) : undefined,
      overlayDescription: attrs.overlaydes ? String(attrs.overlaydes) : attrs.OVERLAYDES ? String(attrs.OVERLAYDES) : undefined,
      majorCategory: String(attrs.major_cat || attrs.MAJOR_CAT || ''),
    };
  }

  // Fallback to polygon query
  console.log('Querying zoning with geometry SR:', parcelGeom.spatialReference);

  const result = await queryByPolygon(connections.zoning.url, parcelGeom, {
    outFields: '*',
    returnGeometry: false,
  });

  if (result.error) {
    console.error('Zoning query error:', result.error);
  }

  if (!result.features || result.features.length === 0) {
    console.warn('No zoning features found');
    return null;
  }

  const attrs = result.features[0].attributes;
  console.log('Zoning query result:', attrs);

  return {
    zoneCode: String(attrs.zoning || attrs.ZONING || attrs.zone_code || ''),
    zoneDescription: String(attrs.zonedesc || attrs.ZONEDESC || ''),
    overlay: attrs.overlay ? String(attrs.overlay) : attrs.OVERLAY ? String(attrs.OVERLAY) : undefined,
    overlayDescription: attrs.overlaydes ? String(attrs.overlaydes) : attrs.OVERLAYDES ? String(attrs.OVERLAYDES) : undefined,
    majorCategory: String(attrs.major_cat || attrs.MAJOR_CAT || ''),
  };
}

/**
 * Get specific plan overlays for a parcel
 */
export async function getOverlaysForParcel(parcelGeom: Polygon): Promise<OverlayData[]> {
  if (!connections.overlays || connections.overlays.length === 0) {
    return [];
  }

  const overlayPromises = connections.overlays.map(async (overlay) => {
    try {
      const result = await queryByPolygon(overlay.url, parcelGeom, {
        outFields: '*',
        returnGeometry: false,
      });

      if (result.features && result.features.length > 0) {
        const attrs = result.features[0].attributes;

        // Determine a clean overlay name based on the service
        let overlayName = overlay.layerName;

        // Bergamot handling - get district name
        if (overlayName.toLowerCase().includes('bergamot')) {
          const districtName = attrs.area_name || attrs.label || attrs.district;
          if (districtName) {
            overlayName = `Bergamot Area Plan - ${districtName}`;
          } else {
            overlayName = 'Bergamot Area Plan';
          }
        }

        // CNEL handling
        if (overlayName.toLowerCase().includes('cnel') || overlayName.toLowerCase().includes('noise')) {
          overlayName = 'Community Noise Equivalent Levels (CNEL)';
        }

        // Downtown handling
        if (overlayName.toLowerCase().includes('downtown')) {
          overlayName = 'Downtown Community Plan';
        }

        const overlayData: OverlayData = {
          name: overlayName,
          type: String(attrs.area_name || attrs.label || attrs.district || attrs.cnel || ''),
        };

        if (attrs.description) {
          overlayData.description = String(attrs.description);
        }

        return overlayData;
      }
    } catch (error) {
      console.warn(`Failed to query overlay ${overlay.layerName}:`, error);
    }
    return null;
  });

  const results = await Promise.all(overlayPromises);
  return results.filter((r): r is OverlayData => r !== null);
}

/**
 * Get CNEL (Community Noise Equivalent Level) data for a parcel
 */
export async function getCNELForParcel(parcelGeom: Polygon): Promise<CNELData> {
  // Find CNEL service in overlays
  const cnelService = connections.overlays?.find(
    (overlay) => overlay.layerName.toLowerCase().includes('cnel') || overlay.layerName.toLowerCase().includes('noise')
  );

  if (!cnelService) {
    return { cnel_db: null };
  }

  try {
    const result = await queryByPolygon(cnelService.url, parcelGeom, {
      outFields: '*',
      returnGeometry: false,
    });

    if (!result.features || result.features.length === 0) {
      return { cnel_db: null };
    }

    const attrs = result.features[0].attributes;

    // Parse CNEL value - it may be stored as a string like "60-65" or a number
    let cnelDb: number | null = null;
    const cnelField = attrs.cnel || attrs.CNEL || attrs.cnel_db || attrs.CNEL_DB;

    if (cnelField) {
      if (typeof cnelField === 'number') {
        cnelDb = cnelField;
      } else if (typeof cnelField === 'string') {
        // Try to parse range like "60-65" - take the midpoint
        const rangeMatch = cnelField.match(/(\d+)\s*-\s*(\d+)/);
        if (rangeMatch) {
          const low = parseInt(rangeMatch[1], 10);
          const high = parseInt(rangeMatch[2], 10);
          cnelDb = (low + high) / 2;
        } else {
          // Try to parse as single number
          const parsed = parseFloat(cnelField);
          if (!isNaN(parsed)) {
            cnelDb = parsed;
          }
        }
      }
    }

    return {
      cnel_db: cnelDb,
      category: cnelField ? String(cnelField) : undefined,
    };
  } catch (error) {
    console.warn('CNEL query error:', error);
    return { cnel_db: null };
  }
}

/**
 * Map overlay data to development tier and overlay codes for backend analysis.
 *
 * Maps Santa Monica overlays to:
 * - development_tier: DCP tier (1/2/3) or null
 * - overlay_codes: Array of overlay identifiers (DCP, Bergamot, AHO, etc.)
 */
export function mapOverlaysToTier(overlays: OverlayData[]): {
  development_tier?: string;
  overlay_codes?: string[];
} {
  const overlay_codes: string[] = [];
  let development_tier: string | undefined;

  for (const overlay of overlays) {
    const name = overlay.name.toLowerCase();
    const type = overlay.type.toLowerCase();

    // Downtown Community Plan (DCP) tiers
    if (name.includes('downtown') || name.includes('dcp')) {
      overlay_codes.push('DCP');

      // Extract tier from type/description
      // TODO(SM): Confirm actual tier attribute names from GIS
      if (type.includes('tier 1') || type.includes('t1')) {
        development_tier = '1';
      } else if (type.includes('tier 2') || type.includes('t2')) {
        development_tier = '2';
      } else if (type.includes('tier 3') || type.includes('t3')) {
        development_tier = '3';
      }
    }

    // Bergamot Area Plan
    if (name.includes('bergamot')) {
      overlay_codes.push('Bergamot');
    }

    // Affordable Housing Overlay (AHO)
    if (name.includes('affordable') || name.includes('aho')) {
      overlay_codes.push('AHO');
    }
  }

  return {
    development_tier,
    overlay_codes: overlay_codes.length > 0 ? overlay_codes : undefined,
  };
}

/**
 * Get historic preservation status for a parcel
 */
export async function getHistoricForParcel(parcelGeom: Polygon): Promise<HistoricData> {
  if (!connections.historic) {
    return { isHistoric: false };
  }

  const result = await queryByPolygon(connections.historic.url, parcelGeom, {
    outFields: '*',
    returnGeometry: false,
  });

  if (result.error) {
    console.warn('Historic query error:', result.error);
  }

  if (!result.features || result.features.length === 0) {
    return { isHistoric: false };
  }

  const attrs = result.features[0].attributes;

  return {
    isHistoric: true,
    resourceName: attrs.resource_name ? String(attrs.resource_name) : attrs.RESOURCE_NAME ? String(attrs.RESOURCE_NAME) : undefined,
    resourceEvaluation: attrs.resource_evaluation ? String(attrs.resource_evaluation) : attrs.RESOURCE_EVALUATION ? String(attrs.RESOURCE_EVALUATION) : undefined,
    districtName: attrs.district_name ? String(attrs.district_name) : attrs.DISTRICT_NAME ? String(attrs.DISTRICT_NAME) : undefined,
    inDistrict: (attrs.located_in_district_ || attrs.LOCATED_IN_DISTRICT_) === 'Yes',
    individuallyEligible: (attrs.individually_eligible || attrs.INDIVIDUALLY_ELIGIBLE) === 'Yes',
    architecturalStyle: attrs.architectural_style ? String(attrs.architectural_style) : attrs.ARCHITECTURAL_STYLE ? String(attrs.ARCHITECTURAL_STYLE) : undefined,
    yearBuilt: attrs.year_built ? String(attrs.year_built) : attrs.YEAR_BUILT ? String(attrs.YEAR_BUILT) : undefined,
  };
}

/**
 * Check if parcel is in coastal zone
 */
export async function getCoastalForParcel(parcelGeom: Polygon): Promise<CoastalData> {
  if (!connections.coastal) {
    return { inCoastalZone: false };
  }

  const result = await queryByPolygon(connections.coastal.url, parcelGeom, {
    outFields: '*',
    returnGeometry: false,
  });

  if (!result.features || result.features.length === 0) {
    return { inCoastalZone: false };
  }

  // All of Santa Monica is within the CA Coastal Zone boundary,
  // but CDP requirements are stricter for parcels near the ocean.
  // Use a simple distance heuristic: only flag parcels west of Ocean Ave
  // (approximately -118.495 longitude) as being in the active coastal zone.

  // Calculate centroid longitude from parcel geometry
  const ring = parcelGeom.rings?.[0];
  if (!ring || ring.length === 0) {
    return { inCoastalZone: false };
  }

  // Calculate average longitude (x coordinate)
  let sumX = 0;
  let count = 0;
  for (const [x] of ring) {
    sumX += x;
    count++;
  }
  const centroidX = sumX / count;

  // Convert from State Plane (feet) to approximate longitude if needed
  // If coordinates are in State Plane CA Zone 5 (WKID 2229), they'll be large numbers (6M-7M range)
  // For Santa Monica, Ocean Ave is roughly at longitude -118.495
  // In State Plane CA Zone 5, this is approximately 6,425,000 feet
  const OCEAN_AVE_X_APPROX = 6425000; // State Plane feet

  // Only flag as coastal zone if parcel is west of Ocean Ave
  const isNearOcean = centroidX < OCEAN_AVE_X_APPROX;

  const attrs = result.features[0].attributes;

  return {
    inCoastalZone: isNearOcean,
    zoneType: attrs.zone_type ? String(attrs.zone_type) : attrs.ZONE_TYPE ? String(attrs.ZONE_TYPE) : attrs.type ? String(attrs.type) : undefined,
  };
}

/**
 * Get FEMA flood zone information
 */
export async function getFloodForParcel(parcelGeom: Polygon): Promise<FloodData> {
  if (!connections.flood) {
    return { inFloodZone: false };
  }

  const result = await queryByPolygon(connections.flood.url, parcelGeom, {
    outFields: '*',
    returnGeometry: false,
  });

  if (!result.features || result.features.length === 0) {
    return { inFloodZone: false };
  }

  const attrs = result.features[0].attributes;
  const fldZone = attrs.fld_zone ? String(attrs.fld_zone) : attrs.FLD_ZONE ? String(attrs.FLD_ZONE) : attrs.zone ? String(attrs.zone) : undefined;

  // Determine if parcel is actually in a flood zone
  // Zone X (or X500) = Minimal flood hazard (0.2% annual chance) - NOT considered a flood zone
  // Zones A, AE, AH, AO, AR, A99, V, VE = Special Flood Hazard Areas (1% annual chance) - THESE ARE flood zones
  const isActualFloodZone = fldZone ?
    !fldZone.toUpperCase().startsWith('X') && // Exclude Zone X variants
    fldZone.toUpperCase() !== 'AREA OF MINIMAL FLOOD HAZARD' &&
    fldZone.toUpperCase() !== 'MINIMAL' : false;

  return {
    inFloodZone: isActualFloodZone,
    fldZone: fldZone,
    floodway: (attrs.floodway || attrs.FLOODWAY) === 'Yes',
    bfe: typeof attrs.bfe === 'number' ? attrs.bfe : typeof attrs.BFE === 'number' ? attrs.BFE : undefined,
  };
}

/**
 * Find nearest transit stop and check AB 2097 eligibility
 */
export async function getTransitNearPoint(lon: number, lat: number): Promise<TransitProximityData> {
  if (!connections.transit) {
    return { withinHalfMile: false };
  }

  const point: Point = { x: lon, y: lat, spatialReference: { wkid: 4326 } };

  // Query transit stops within 1 mile (to find nearest)
  const result = await queryByPoint(connections.transit.url, point, {
    outFields: '*',
    returnGeometry: true,
    distance: 1609, // 1 mile in meters
    units: 'esriSRUnit_Meter',
  });

  if (!result.features || result.features.length === 0) {
    return { withinHalfMile: false };
  }

  // Find nearest stop
  let nearestStop = result.features[0];
  let minDistance = Infinity;

  for (const feature of result.features) {
    const attrs = feature.attributes;
    // Use stop_lat/stop_lon from attributes (WGS84) instead of geometry (State Plane)
    if (attrs.stop_lat && attrs.stop_lon && typeof attrs.stop_lat === 'number' && typeof attrs.stop_lon === 'number') {
      const stopPoint: Point = {
        x: attrs.stop_lon,
        y: attrs.stop_lat,
        spatialReference: { wkid: 4326 },
      };
      const distance = calculateDistance(point, stopPoint);
      if (distance < minDistance) {
        minDistance = distance;
        nearestStop = feature;
      }
    }
  }

  const attrs = nearestStop.attributes;
  const withinHalfMile = minDistance <= 804.67; // 0.5 miles in meters

  return {
    nearestStopName: attrs.stop_name ? String(attrs.stop_name) : attrs.STOP_NAME ? String(attrs.STOP_NAME) : undefined,
    nearestStopDistance: minDistance,
    withinHalfMile,
    stopType: attrs.stop_desc ? String(attrs.stop_desc) : attrs.STOP_DESC ? String(attrs.STOP_DESC) : attrs.location_type ? String(attrs.location_type) : undefined,
  };
}

/**
 * Get development standards/setbacks for a zone
 */
export async function getStandardsForZone(zoneCode: string): Promise<SetbackData> {
  if (!connections.setbacks) {
    return {};
  }

  const result = await queryByPoint(
    connections.setbacks.url,
    { x: 0, y: 0, spatialReference: { wkid: 4326 } },
    {
      where: `zone_code = '${zoneCode}'`,
      outFields: '*',
      returnGeometry: false,
    }
  );

  if (!result.features || result.features.length === 0) {
    return {};
  }

  const attrs = result.features[0].attributes;

  return {
    frontSetback: typeof attrs.front_setback === 'number' ? attrs.front_setback : typeof attrs.FRONT_SETBACK === 'number' ? attrs.FRONT_SETBACK : undefined,
    sideSetback: typeof attrs.side_setback === 'number' ? attrs.side_setback : typeof attrs.SIDE_SETBACK === 'number' ? attrs.SIDE_SETBACK : undefined,
    rearSetback: typeof attrs.rear_setback === 'number' ? attrs.rear_setback : typeof attrs.REAR_SETBACK === 'number' ? attrs.REAR_SETBACK : undefined,
    maxHeight: typeof attrs.max_height === 'number' ? attrs.max_height : typeof attrs.MAX_HEIGHT === 'number' ? attrs.MAX_HEIGHT : undefined,
  };
}

/**
 * Check geohazards for a parcel
 */
export async function getHazardsForParcel(parcelGeom: Polygon): Promise<HazardData> {
  if (!connections.hazards || connections.hazards.length === 0) {
    return {
      faultZone: false,
      liquefactionZone: false,
      landslideZone: false,
      seismicHazardZone: false,
    };
  }

  const hazardPromises = connections.hazards.map(async (hazard) => {
    const result = await queryByPolygon(hazard.url, parcelGeom, {
      outFields: '*',
      returnGeometry: false,
    });
    return {
      layerName: hazard.layerName.toLowerCase(),
      found: result.features && result.features.length > 0,
    };
  });

  const results = await Promise.all(hazardPromises);

  return {
    faultZone: results.some((r) => r.layerName.includes('fault') && r.found),
    liquefactionZone: results.some((r) => r.layerName.includes('liquefaction') && r.found),
    landslideZone: results.some((r) => r.layerName.includes('landslide') && r.found),
    seismicHazardZone: results.some((r) => r.layerName.includes('seismic') && r.found),
  };
}

/**
 * Check if parcel intersects wetlands using CARI (California Aquatic Resource Inventory)
 * API: https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds2835_fpu/FeatureServer/0
 */
export async function queryWetlands(parcelGeom: Polygon): Promise<boolean> {
  const CARI_URL = 'https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds2835_fpu/FeatureServer/0';

  try {
    console.log('[ENV] Querying wetlands (CARI)...');
    const result = await queryByPolygon(CARI_URL, parcelGeom, {
      outFields: 'CARI_id,clicklabel,major_class',
      returnGeometry: false,
    });

    const hasWetlands = result.features && result.features.length > 0;
    if (hasWetlands) {
      console.log('[ENV] Wetlands found:', result.features[0].attributes);
    } else {
      console.log('[ENV] No wetlands found');
    }
    return hasWetlands;
  } catch (error) {
    console.error('[ENV] Wetlands query error:', error);
    return false; // Fail gracefully - assume no wetlands if service unavailable
  }
}

/**
 * Check if parcel is in conservation area using CPAD (California Protected Areas Database)
 * API: https://services.gis.ca.gov/arcgis/rest/services/Boundaries/CA_Protected_Areas_Database/MapServer/0
 */
export async function queryConservationAreas(parcelGeom: Polygon): Promise<boolean> {
  const CPAD_URL = 'https://services.gis.ca.gov/arcgis/rest/services/Boundaries/CA_Protected_Areas_Database/MapServer/0';

  try {
    console.log('[ENV] Querying conservation areas (CPAD)...');
    const result = await queryByPolygon(CPAD_URL, parcelGeom, {
      outFields: 'UNIT_NAME,MNG_AGENCY,ACCESS_TYP',
      returnGeometry: false,
    });

    const inConservation = result.features && result.features.length > 0;
    if (inConservation) {
      console.log('[ENV] Conservation area found:', result.features[0].attributes);
    } else {
      console.log('[ENV] Not in conservation area');
    }
    return inConservation;
  } catch (error) {
    console.error('[ENV] Conservation area query error:', error);
    return false; // Fail gracefully
  }
}

/**
 * Check fire hazard severity zone using LA County CAL FIRE FHSZ
 * API: https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/Hazards/MapServer/2
 * Returns: "Very High", "High", "Moderate", or null
 */
export async function queryFireHazardZone(parcelGeom: Polygon): Promise<string | null> {
  const LA_FIRE_URL = 'https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/Hazards/MapServer/2';

  try {
    console.log('[ENV] Querying fire hazard zones (LA County CAL FIRE)...');
    const result = await queryByPolygon(LA_FIRE_URL, parcelGeom, {
      outFields: 'HAZ_CLASS,FHSZ_CLASS,SRA_LRA',
      returnGeometry: false,
    });

    if (!result.features || result.features.length === 0) {
      console.log('[ENV] Not in fire hazard zone');
      return null;
    }

    const attrs = result.features[0].attributes;
    const hazClass = attrs.HAZ_CLASS || attrs.FHSZ_CLASS || attrs.haz_class || attrs.fhsz_class;

    if (hazClass) {
      const hazClassStr = String(hazClass).toUpperCase();
      console.log('[ENV] Fire hazard zone found:', hazClassStr);

      // Normalize to standard values
      if (hazClassStr.includes('VERY HIGH')) return 'Very High';
      if (hazClassStr.includes('HIGH')) return 'High';
      if (hazClassStr.includes('MODERATE')) return 'Moderate';

      return String(hazClass);
    }

    return null;
  } catch (error) {
    console.error('[ENV] Fire hazard zone query error:', error);
    return null; // Fail gracefully
  }
}

/**
 * Check if parcel is within 500ft of hazardous waste site using DTSC EnviroStor
 * API: https://gis.data.ca.gov/datasets/CALOES::dtsc-envirostor-cleanup-sites
 * Service URL needs to be resolved from the dataset page
 */
export async function queryHazardousWasteSites(parcelGeom: Polygon): Promise<boolean> {
  // Using California State Geoportal REST service for DTSC EnviroStor
  const ENVIROSTOR_URL = 'https://services2.arcgis.com/dHCEsdMYCaT5lXuh/arcgis/rest/services/DTSC_EnviroStor_Cleanup_Sites/FeatureServer/0';

  try {
    console.log('[ENV] Querying hazardous waste sites (DTSC EnviroStor)...');

    // Query for sites within 500 feet buffer
    // Note: 500 feet = ~152.4 meters
    const result = await queryByPolygon(ENVIROSTOR_URL, parcelGeom, {
      outFields: 'SITE_NAME,STATUS,SITE_TYPE',
      returnGeometry: false,
      distance: 152.4, // 500 feet in meters
      units: 'esriSRUnit_Meter',
    });

    const nearHazardous = result.features && result.features.length > 0;
    if (nearHazardous) {
      console.log('[ENV] Hazardous waste site nearby:', result.features[0].attributes);
    } else {
      console.log('[ENV] No hazardous waste sites within 500ft');
    }
    return nearHazardous;
  } catch (error) {
    console.error('[ENV] Hazardous waste query error:', error);
    return false; // Fail gracefully
  }
}

/**
 * Check if parcel is in Alquist-Priolo earthquake fault zone
 * API: LA City REST service - https://maps.lacity.org/arcgis/rest/services/Mapping/NavigateLA/MapServer/97
 */
export async function queryEarthquakeFaultZone(parcelGeom: Polygon): Promise<boolean> {
  const LA_FAULT_URL = 'https://maps.lacity.org/arcgis/rest/services/Mapping/NavigateLA/MapServer/97';

  try {
    console.log('[ENV] Querying earthquake fault zones (Alquist-Priolo)...');
    const result = await queryByPolygon(LA_FAULT_URL, parcelGeom, {
      outFields: 'ZONE_NAME,FAULT_NAME,QUAD_NAME',
      returnGeometry: false,
    });

    const inFaultZone = result.features && result.features.length > 0;
    if (inFaultZone) {
      console.log('[ENV] Earthquake fault zone found:', result.features[0].attributes);
    } else {
      console.log('[ENV] Not in earthquake fault zone');
    }
    return inFaultZone;
  } catch (error) {
    console.error('[ENV] Earthquake fault zone query error:', error);
    return false; // Fail gracefully
  }
}

/**
 * Get street ROW (right-of-way) width for a parcel.
 *
 * NOTE: Santa Monica GIS does not provide ROW width as a direct attribute.
 * This function estimates ROW width based on street classification from the
 * Street Centerlines layer.
 *
 * Estimation based on typical California standards:
 * - Arterial (LUCE Class 1): 100-120 ft ROW
 * - Collector (LUCE Class 2): 80-100 ft ROW
 * - Local (LUCE Class 3): 50-70 ft ROW
 * - Known major corridors (Wilshire, Broadway, Lincoln): 120+ ft ROW
 *
 * For accurate ROW widths, contact: gis.mailbox@santamonica.gov
 *
 * @param parcelGeom - Parcel geometry
 * @returns Street ROW data with estimated width
 */
export async function getStreetROWWidth(parcelGeom: Polygon): Promise<StreetROWData> {
  if (!connections.streets) {
    return {
      rowWidth: null,
      streetName: null,
      streetType: null,
      dataSource: 'manual',
      estimationNote: 'Streets service not configured',
    };
  }

  try {
    // Buffer parcel by 20 feet to find adjacent streets
    const result = await queryByPolygon(connections.streets.url, parcelGeom, {
      outFields: 'fullname,type,luce_class',
      returnGeometry: false,
      distance: 20, // 20 feet buffer
      units: 'esriSRUnit_Foot',
    });

    if (!result.features || result.features.length === 0) {
      return {
        rowWidth: null,
        streetName: null,
        streetType: null,
        dataSource: 'estimated',
        estimationNote: 'No street found adjacent to parcel',
      };
    }

    // If multiple streets, use the widest (corner parcels)
    let widestStreet = result.features[0];
    let maxEstimatedWidth = 0;

    for (const feature of result.features) {
      const attrs = feature.attributes;
      const estimatedWidth = estimateROWWidthFromClassification(
        (attrs.fullname || attrs.stname) ? String(attrs.fullname || attrs.stname) : null,
        attrs.type ? String(attrs.type) : null,
        attrs.luce_class ? String(attrs.luce_class) : null
      );

      if (estimatedWidth > maxEstimatedWidth) {
        maxEstimatedWidth = estimatedWidth;
        widestStreet = feature;
      }
    }

    const attrs = widestStreet.attributes;
    const streetName = (attrs.fullname || attrs.stname) ? String(attrs.fullname || attrs.stname) : null;
    const streetType = (attrs.type || attrs.luce_class) ? String(attrs.type || attrs.luce_class) : null;
    const rowWidth = maxEstimatedWidth;

    return {
      rowWidth,
      streetName,
      streetType,
      dataSource: 'estimated',
      estimationNote: `Estimated from street classification. For accurate ROW width, contact gis.mailbox@santamonica.gov`,
    };
  } catch (error) {
    console.error('Street ROW query error:', error);
    return {
      rowWidth: null,
      streetName: null,
      streetType: null,
      dataSource: 'manual',
      estimationNote: 'Error querying streets layer',
    };
  }
}

/**
 * Estimate ROW width from street name and classification.
 * Based on typical California and Santa Monica street standards.
 */
function estimateROWWidthFromClassification(
  streetName: string | null,
  streetType: string | null,
  luceClass: string | null
): number {
  const name = (streetName || '').toUpperCase();
  const type = (streetType || '').toUpperCase();
  const luce = (luceClass || '').toUpperCase();

  // Known major corridors in Santa Monica (wide ROW)
  const majorCorridors = [
    'WILSHIRE',
    'BROADWAY',
    'LINCOLN',
    'SANTA MONICA',
    'PICO',
    'OLYMPIC',
  ];

  if (majorCorridors.some((corridor) => name.includes(corridor))) {
    return 120; // Major arterials typically 100-150 ft
  }

  // LUCE (Land Use Circulation Element) classification
  if (luce.includes('1') || type.includes('ARTERIAL')) {
    return 100; // Arterials: 100-120 ft ROW
  }

  if (luce.includes('2') || type.includes('COLLECTOR')) {
    return 80; // Collectors: 80-100 ft ROW
  }

  if (luce.includes('3') || type.includes('LOCAL')) {
    return 60; // Local streets: 50-70 ft ROW
  }

  // Default for unknown classification
  return 80; // Conservative mid-range estimate
}

/**
 * Complete parcel analysis - queries all services
 */
export async function analyzeParcel(lon: number, lat: number): Promise<ParcelAnalysis | null> {
  // 1. Get parcel data
  const parcel = await getParcelAtPoint(lon, lat);
  if (!parcel || !parcel.geometry) {
    return null;
  }

  // Create center point for more reliable queries
  const centerPoint: Point = {
    x: lon,
    y: lat,
    spatialReference: { wkid: 4326 },
  };

  // 2. Query all overlay services in parallel (including environmental data and street ROW)
  const [zoning, historic, coastal, flood, transit, overlays, hazards, cnel, street, inWetlands, inConservationArea, fireHazardZone, nearHazardousWaste, inEarthquakeFaultZone] = await Promise.all([
    getZoningForParcel(parcel.geometry, centerPoint),
    getHistoricForParcel(parcel.geometry),
    getCoastalForParcel(parcel.geometry),
    getFloodForParcel(parcel.geometry),
    getTransitNearPoint(lon, lat),
    getOverlaysForParcel(parcel.geometry),
    getHazardsForParcel(parcel.geometry),
    getCNELForParcel(parcel.geometry),
    getStreetROWWidth(parcel.geometry),
    // Environmental GIS queries for SB35/AB2011 site exclusions
    queryWetlands(parcel.geometry),
    queryConservationAreas(parcel.geometry),
    queryFireHazardZone(parcel.geometry),
    queryHazardousWasteSites(parcel.geometry),
    queryEarthquakeFaultZone(parcel.geometry),
  ]);

  // 3. Get setback standards if we have zoning
  const setbacks = zoning ? await getStandardsForZone(zoning.zoneCode) : {};

  // 4. Default parking data (placeholder - would need actual service)
  const parking: ParkingData = {
    unbundledParkingRequired: false,
  };

  // 5. Add Downtown Community Plan overlay based on zoning code
  // Downtown Community Plan has no GIS service - it's applied via zoning codes TA and NV
  let finalOverlays = overlays;
  if (zoning && (zoning.zoneCode === 'TA' || zoning.zoneCode === 'NV')) {
    const downtownOverlay: OverlayData = {
      name: 'Downtown Community Plan',
      type: zoning.zoneCode === 'TA' ? 'Transit Adjacent' : 'Neighborhood Village',
      description: 'Tiered development standards allowing increased density and height in exchange for community benefits.',
    };
    finalOverlays = [...overlays, downtownOverlay];
  }

  return {
    parcel,
    zoning: zoning || { zoneCode: '', zoneDescription: '', majorCategory: '' },
    historic,
    coastal,
    flood,
    transit,
    parking,
    setbacks,
    hazards,
    overlays: finalOverlays,
    cnel: cnel.cnel_db !== null ? cnel : undefined,
    environmental: {
      inWetlands,
      inConservationArea,
      fireHazardZone,
      nearHazardousWaste,
      inEarthquakeFaultZone,
    },
    street,
  };
}

/**
 * Batch analyze multiple parcels by APN
 */
export async function batchAnalyzeByAPN(apns: string[]): Promise<Map<string, ParcelAnalysis>> {
  const results = new Map<string, ParcelAnalysis>();

  for (const apn of apns) {
    // Query parcel by APN
    if (!connections.parcels) continue;

    const result = await queryByPoint(
      connections.parcels.url,
      { x: 0, y: 0, spatialReference: { wkid: 4326 } },
      {
        where: `apn = '${apn}' OR APN = '${apn}'`,
        outFields: '*',
        returnGeometry: true,
      }
    );

    if (result.features && result.features.length > 0) {
      const feature = result.features[0];
      const geom = feature.geometry;

      if (geom && 'rings' in geom && geom.rings) {
        const centroid = calculatePolygonCentroid(geom as Polygon);
        const analysis = await analyzeParcel(centroid.x, centroid.y);
        if (analysis) {
          results.set(apn, analysis);
        }
      }
    }
  }

  return results;
}

/**
 * Calculate polygon centroid
 */
function calculatePolygonCentroid(polygon: Polygon): Point {
  const rings = polygon.rings[0];
  let x = 0;
  let y = 0;

  for (const [px, py] of rings) {
    x += px;
    y += py;
  }

  return {
    x: x / rings.length,
    y: y / rings.length,
    spatialReference: polygon.spatialReference,
  };
}

/**
 * Search for parcels by APN (autocomplete)
 * Returns matching parcels for typeahead functionality
 */
export async function searchParcelsByAPN(searchTerm: string): Promise<Array<{ apn: string; address: string }>> {
  if (!connections.parcels || searchTerm.length < 3) {
    return [];
  }

  try {
    // Build a WHERE clause that searches APN flexibly
    // Keep the original search term format (user might type with or without dashes)
    // NOTE: Field names in GIS are lowercase: apn, situsfulladdress
    const whereClause = `apn LIKE '%${searchTerm}%'`;

    // Use queryByAttribute for attribute-based searches (no spatial geometry needed)
    const result = await queryByAttribute(
      connections.parcels.url,
      whereClause,
      {
        outFields: 'apn,situsfulladdress',
        returnGeometry: false,
        resultRecordCount: 10,
      }
    );

    if (!result.features || result.features.length === 0) {
      return [];
    }

    return result.features.map((feature: any) => ({
      apn: feature.attributes.apn || '',
      address: feature.attributes.situsfulladdress || 'No address',
    }));
  } catch (error) {
    console.error('Parcel search error:', error);
    return [];
  }
}

/**
 * Get full parcel analysis by APN
 */
export async function getParcelByAPN(apn: string): Promise<ParcelAnalysis | null> {
  if (!connections.parcels) {
    throw new Error('Parcels service not configured');
  }

  try {
    // Use queryByAttribute for APN lookup (not queryByPoint)
    // NOTE: Field name in GIS is lowercase: apn
    // Keep APN format as-is (GIS stores with dashes like "4289-001-003")
    const result = await queryByAttribute(
      connections.parcels.url,
      `apn = '${apn}'`,
      {
        outFields: '*',
        returnGeometry: true,
      }
    );

    if (!result.features || result.features.length === 0) {
      return null;
    }

    const feature = result.features[0];
    const attrs = feature.attributes;
    const geometry = feature.geometry as Polygon | undefined;

    if (!geometry || !('rings' in geometry) || !geometry.rings) {
      return null;
    }

    // Ensure geometry has spatial reference
    if (!geometry.spatialReference) {
      geometry.spatialReference = result.spatialReference || { wkid: 2229 };
    }

    // Build ParcelData from the feature
    const lotSizeSqft = attrs.Shape__Area && typeof attrs.Shape__Area === 'number' ? Math.round(attrs.Shape__Area) : undefined;
    let lotWidth: number | undefined;
    let lotDepth: number | undefined;

    if (lotSizeSqft) {
      const ring = geometry.rings?.[0];
      if (ring && ring.length >= 3) {
        const edges: number[] = [];
        for (let i = 0; i < ring.length - 1; i++) {
          const [x1, y1] = ring[i];
          const [x2, y2] = ring[i + 1];
          const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
          edges.push(length);
        }

        if (edges.length >= 1) {
          const sortedEdges = [...edges].sort((a, b) => b - a);
          const longestEdge = sortedEdges[0];
          const depth = lotSizeSqft / longestEdge;
          lotWidth = Math.round(longestEdge);
          lotDepth = Math.round(depth);
        }
      }
    }

    const parcel: ParcelData = {
      apn: String(attrs.apn || attrs.APN || ''),
      ain: String(attrs.ain || attrs.AIN || ''),
      address: String(attrs.situsaddress || attrs.SitusAddress || ''),
      situsFullAddress: String(attrs.situsfulladdress || attrs.SitusFullAddress || ''),
      city: String(attrs.situscity || attrs.SitusCity || 'Santa Monica'),
      zip: String(attrs.situszip || attrs.SitusZip || ''),
      useCode: String(attrs.usecode || attrs.UseCode || ''),
      useType: String(attrs.usetype || attrs.UseType || attrs.USETYPE || ''),
      useDescription: String(attrs.usedescription || attrs.UseDescription || ''),
      yearBuilt: attrs.yearbuilt1 || attrs.YearBuilt1 ? String(attrs.yearbuilt1 || attrs.YearBuilt1) : undefined,
      units: Number(attrs.units1 || attrs.Units1 || 0),
      bedrooms: Number(attrs.bedrooms1 || attrs.Bedrooms1 || 0),
      bathrooms: Number(attrs.bathrooms1 || attrs.Bathrooms1 || 0),
      sqft: Number(attrs.sqftmain1 || attrs.SqftMain1 || 0),
      geometry,
      lotSizeSqft,
      lotWidth,
      lotDepth,
      latitude: attrs.center_lat !== null && attrs.center_lat !== undefined ? Number(attrs.center_lat) : undefined,
      longitude: attrs.center_lon !== null && attrs.center_lon !== undefined ? Number(attrs.center_lon) : undefined,
    };

    // Calculate centroid for overlay queries
    const centroid = calculatePolygonCentroid(geometry);

    // Query all overlay services in parallel
    const [zoning, historic, coastal, flood, transit, overlays, hazards, cnel, street, inWetlands, inConservationArea, fireHazardZone, nearHazardousWaste, inEarthquakeFaultZone] = await Promise.all([
      getZoningForParcel(geometry, { x: centroid.x, y: centroid.y, spatialReference: { wkid: 4326 } }),
      getHistoricForParcel(geometry),
      getCoastalForParcel(geometry),
      getFloodForParcel(geometry),
      getTransitNearPoint(centroid.x, centroid.y),
      getOverlaysForParcel(geometry),
      getHazardsForParcel(geometry),
      getCNELForParcel(geometry),
      getStreetROWWidth(geometry),
      queryWetlands(geometry),
      queryConservationAreas(geometry),
      queryFireHazardZone(geometry),
      queryHazardousWasteSites(geometry),
      queryEarthquakeFaultZone(geometry),
    ]);

    // Get setback standards
    const setbacks = zoning ? await getStandardsForZone(zoning.zoneCode) : {};

    // Default parking data
    const parking: ParkingData = {
      unbundledParkingRequired: false,
    };

    // Add Downtown Community Plan overlay if applicable
    let finalOverlays = overlays;
    if (zoning && (zoning.zoneCode === 'TA' || zoning.zoneCode === 'NV')) {
      const downtownOverlay: OverlayData = {
        name: 'Downtown Community Plan',
        type: zoning.zoneCode === 'TA' ? 'Transit Adjacent' : 'Neighborhood Village',
        description: 'Tiered development standards allowing increased density and height in exchange for community benefits.',
      };
      finalOverlays = [...overlays, downtownOverlay];
    }

    return {
      parcel,
      zoning: zoning || { zoneCode: '', zoneDescription: '', majorCategory: '' },
      historic,
      coastal,
      flood,
      transit,
      parking,
      setbacks,
      hazards,
      overlays: finalOverlays,
      cnel: cnel.cnel_db !== null ? cnel : undefined,
      environmental: {
        inWetlands,
        inConservationArea,
        fireHazardZone,
        nearHazardousWaste,
        inEarthquakeFaultZone,
      },
      street,
    };
  } catch (error) {
    console.error('Get parcel by APN error:', error);
    return null;
  }
}
