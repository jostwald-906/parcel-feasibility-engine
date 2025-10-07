/**
 * GIS Utility Functions for ArcGIS REST Services
 *
 * Provides functions to query Santa Monica's ArcGIS FeatureServer endpoints
 */

import { SPATIAL_REFERENCE } from './gis-config';
import { cachedFetch } from './gis-cache';

export interface Point {
  x: number; // longitude
  y: number; // latitude
  spatialReference?: { wkid: number };
}

export interface Polygon {
  rings: number[][][]; // array of rings (outer ring + optional holes)
  spatialReference?: { wkid: number };
}

export interface ArcGISQueryParams {
  geometry?: string;
  geometryType?: 'esriGeometryPoint' | 'esriGeometryPolygon' | 'esriGeometryEnvelope';
  inSR?: number;
  spatialRel?: 'esriSpatialRelIntersects' | 'esriSpatialRelContains' | 'esriSpatialRelWithin';
  outFields?: string;
  returnGeometry?: boolean;
  where?: string;
  f?: 'json' | 'pjson';
  distance?: number;
  units?: string;
  resultRecordCount?: number;
}

export interface ArcGISFeature {
  attributes: Record<string, string | number | boolean | null>;
  geometry?: Point | Polygon | Record<string, unknown>;
}

export interface ArcGISQueryResult {
  features: ArcGISFeature[];
  spatialReference?: { wkid: number };
  error?: {
    code: number;
    message: string;
  };
}

/**
 * Query an ArcGIS FeatureServer by point geometry
 */
export async function queryByPoint(
  serviceUrl: string,
  point: Point,
  options: Partial<ArcGISQueryParams> = {}
): Promise<ArcGISQueryResult> {
  const params = new URLSearchParams({
    geometry: JSON.stringify(point),
    geometryType: 'esriGeometryPoint',
    inSR: String(point.spatialReference?.wkid || SPATIAL_REFERENCE.wkid),
    // Don't set outSR - we want geometry in native State Plane (2229) for proper transformation
    spatialRel: options.spatialRel || 'esriSpatialRelIntersects',
    outFields: options.outFields || '*',
    returnGeometry: String(options.returnGeometry ?? false),
    f: 'json',
  });

  if (options.where) {
    params.set('where', options.where);
  }

  if (options.distance !== undefined) {
    params.set('distance', String(options.distance));
  }

  if (options.units) {
    params.set('units', options.units);
  }

  if (options.resultRecordCount !== undefined) {
    params.set('resultRecordCount', String(options.resultRecordCount));
  }

  try {
    // Use cached fetch
    const paramsObj = Object.fromEntries(params.entries());
    const data = await cachedFetch<ArcGISQueryResult>(`${serviceUrl}/query`, paramsObj);
    return data;
  } catch (error) {
    console.error('ArcGIS query error:', error);
    return { features: [], error: { code: -1, message: String(error) } };
  }
}

/**
 * Query an ArcGIS FeatureServer by polygon geometry
 */
export async function queryByPolygon(
  serviceUrl: string,
  polygon: Polygon,
  options: Partial<ArcGISQueryParams> = {}
): Promise<ArcGISQueryResult> {
  const params = new URLSearchParams({
    geometry: JSON.stringify(polygon),
    geometryType: 'esriGeometryPolygon',
    inSR: String(polygon.spatialReference?.wkid || 2229), // Use polygon's SR, default to State Plane
    spatialRel: options.spatialRel || 'esriSpatialRelIntersects',
    outFields: options.outFields || '*',
    returnGeometry: String(options.returnGeometry ?? false),
    f: 'json',
  });

  if (options.where) {
    params.set('where', options.where);
  }

  try {
    // Use cached fetch
    const paramsObj = Object.fromEntries(params.entries());
    const data = await cachedFetch<ArcGISQueryResult>(`${serviceUrl}/query`, paramsObj);
    return data;
  } catch (error) {
    console.error('ArcGIS query error:', error);
    return { features: [], error: { code: -1, message: String(error) } };
  }
}

/**
 * Query features by attribute (WHERE clause)
 */
export async function queryByAttribute(
  serviceUrl: string,
  whereClause: string,
  options: Partial<ArcGISQueryParams> = {}
): Promise<ArcGISQueryResult> {
  const params = new URLSearchParams({
    where: whereClause,
    outFields: options.outFields || '*',
    returnGeometry: String(options.returnGeometry ?? false),
    f: 'json',
  });

  if (options.resultRecordCount !== undefined) {
    params.set('resultRecordCount', String(options.resultRecordCount));
  }

  try {
    // Use cached fetch
    const paramsObj = Object.fromEntries(params.entries());
    const data = await cachedFetch<ArcGISQueryResult>(`${serviceUrl}/query`, paramsObj);
    return data;
  } catch (error) {
    console.error('ArcGIS query error:', error);
    return { features: [], error: { code: -1, message: String(error) } };
  }
}

/**
 * Calculate distance between two points using Haversine formula
 * Returns distance in meters
 */
export function calculateDistance(point1: Point, point2: Point): number {
  const R = 6371000; // Earth's radius in meters
  const lat1 = (point1.y * Math.PI) / 180;
  const lat2 = (point2.y * Math.PI) / 180;
  const deltaLat = ((point2.y - point1.y) * Math.PI) / 180;
  const deltaLng = ((point2.x - point1.x) * Math.PI) / 180;

  const a =
    Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // Returns distance in meters
}

/**
 * Find nearest transit stop to a point
 */
export async function findNearestTransitStop(
  transitServiceUrl: string,
  point: Point
): Promise<{
  distance: number;
  stop: ArcGISFeature | null;
}> {
  // Query all transit stops
  const result = await queryByAttribute(transitServiceUrl, '1=1', {
    returnGeometry: true,
    outFields: '*',
  });

  if (!result.features || result.features.length === 0) {
    return { distance: Infinity, stop: null };
  }

  // Find closest stop
  let minDistance = Infinity;
  let nearestStop: ArcGISFeature | null = null;

  for (const feature of result.features) {
    if (feature.geometry && 'x' in feature.geometry && 'y' in feature.geometry) {
      const geom = feature.geometry as Point;
      const lon = typeof geom.x === 'number' ? geom.x : typeof feature.attributes.LONGITUDE === 'number' ? feature.attributes.LONGITUDE : 0;
      const lat = typeof geom.y === 'number' ? geom.y : typeof feature.attributes.LATITUDE === 'number' ? feature.attributes.LATITUDE : 0;

      const stopPoint: Point = { x: lon, y: lat };
      const distance = calculateDistance(point, stopPoint);
      if (distance < minDistance) {
        minDistance = distance;
        nearestStop = feature;
      }
    }
  }

  return { distance: minDistance, stop: nearestStop };
}

/**
 * Check if parcel is within 0.5 miles of major transit (AB 2097)
 */
export async function checkAB2097Eligibility(
  transitServiceUrl: string,
  parcelPoint: Point
): Promise<{
  eligible: boolean;
  distance: number;
  nearestStop?: string;
}> {
  const { distance, stop } = await findNearestTransitStop(transitServiceUrl, parcelPoint);

  return {
    eligible: distance <= 0.5,
    distance,
    nearestStop: stop?.attributes?.STOP_NAME ? String(stop.attributes.STOP_NAME) : 'Unknown',
  };
}

/**
 * Convert Leaflet LatLng to ArcGIS Point
 */
export function leafletToArcGISPoint(lat: number, lng: number): Point {
  return { x: lng, y: lat };
}

/**
 * Convert ArcGIS polygon to Leaflet polygon coordinates
 */
export function arcGISToLeafletPolygon(arcgisPolygon: Polygon): [number, number][][] {
  return arcgisPolygon.rings.map(ring =>
    ring.map(coord => [coord[1], coord[0]] as [number, number])
  );
}

/**
 * Batch query multiple layers for a parcel
 */
export async function queryAllLayers(
  point: Point,
  parcelGeometry: Polygon,
  serviceUrls: {
    zoning: string;
    historic: string;
    coastal: string;
    flood: string;
    specificPlans: string;
    affordableOverlay: string;
  }
): Promise<{
  zoning: ArcGISFeature | null;
  historic: ArcGISFeature | null;
  coastal: ArcGISFeature | null;
  flood: ArcGISFeature | null;
  specificPlans: ArcGISFeature[];
  affordableOverlay: ArcGISFeature | null;
}> {
  const [zoning, historic, coastal, flood, specificPlans, affordableOverlay] = await Promise.all([
    queryByPolygon(serviceUrls.zoning, parcelGeometry),
    queryByPolygon(serviceUrls.historic, parcelGeometry),
    queryByPolygon(serviceUrls.coastal, parcelGeometry),
    queryByPolygon(serviceUrls.flood, parcelGeometry),
    queryByPolygon(serviceUrls.specificPlans, parcelGeometry),
    queryByPolygon(serviceUrls.affordableOverlay, parcelGeometry),
  ]);

  return {
    zoning: zoning.features[0] || null,
    historic: historic.features[0] || null,
    coastal: coastal.features[0] || null,
    flood: flood.features[0] || null,
    specificPlans: specificPlans.features || [],
    affordableOverlay: affordableOverlay.features[0] || null,
  };
}
