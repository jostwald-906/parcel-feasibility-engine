/**
 * Simplified ArcGIS Client using attribute queries instead of spatial queries
 *
 * This version works around spatial reference issues by using center_lat/center_lon fields
 */

import { GIS_SERVICES } from './gis-config';
import { cachedFetch } from './gis-cache';

export interface ParcelDataSimple {
  apn: string;
  address: string;
  city: string;
  zip: string;
  useCode: string;
  useDescription: string;
  yearBuilt?: string;
  units?: number;
  sqft?: number;
  center_lat?: number;
  center_lon?: number;
  lotSizeSqft?: number;
  lotPerimeter?: number;
  lotWidth?: number;
  lotDepth?: number;
  geometry?: any; // ArcGIS geometry (rings in State Plane coordinates)
}

/**
 * Calculate approximate width and depth from polygon geometry
 * Uses actual edge lengths to find the two longest perpendicular sides
 */
function calculateDimensions(geometry: any, area: number, perimeter: number): { width: number; depth: number } {
  if (!geometry || !geometry.rings || geometry.rings.length === 0) {
    // Fallback: assume square lot
    const side = Math.sqrt(area);
    return { width: Math.round(side), depth: Math.round(side) };
  }

  const ring = geometry.rings[0]; // Outer ring

  // Calculate all edge lengths
  const edges: number[] = [];
  for (let i = 0; i < ring.length - 1; i++) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[i + 1];
    const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    edges.push(length);
  }

  if (edges.length < 3) {
    // Not enough edges, use area to estimate
    const side = Math.sqrt(area);
    return { width: Math.round(side), depth: Math.round(side) };
  }

  // Sort edges by length
  const sortedEdges = [...edges].sort((a, b) => b - a);

  // Use the longest edge as width
  const longestEdge = sortedEdges[0];

  // Calculate depth using area formula: area = width * depth
  // This ensures width × depth = area (approximately)
  const depth = area / longestEdge;

  return {
    width: Math.round(longestEdge),
    depth: Math.round(depth),
  };
}

/**
 * Find nearest parcel to clicked coordinates using center_lat/center_lon
 */
export async function getParcelNearPoint(lon: number, lat: number): Promise<ParcelDataSimple | null> {
  // Query all parcels and find closest one (within 0.001 degrees ~100m)
  const tolerance = 0.001;

  const whereClause = `center_lat BETWEEN ${lat - tolerance} AND ${lat + tolerance} AND center_lon BETWEEN ${lon - tolerance} AND ${lon + tolerance}`;

  try {
    const data = await cachedFetch<any>(`${GIS_SERVICES.PARCELS_PUBLIC.url}/query`, {
      where: whereClause,
      outFields: 'apn,ain,situsaddress,situscity,situszip,usecode,usedescription,yearbuilt1,units1,sqftmain1,center_lat,center_lon,Shape__Area,Shape__Length',
      f: 'json',
      returnGeometry: true,
    });

    if (!data.features || data.features.length === 0) {
      return null;
    }

    // Find closest parcel
    let closestParcel = data.features[0];
    let minDistance = Infinity;

    for (const feature of data.features) {
      const attrs = feature.attributes;
      const dist = Math.sqrt(
        Math.pow(attrs.center_lat - lat, 2) + Math.pow(attrs.center_lon - lon, 2)
      );
      if (dist < minDistance) {
        minDistance = dist;
        closestParcel = feature;
      }
    }

    const attrs = closestParcel.attributes;
    const geometry = closestParcel.geometry;

    // Calculate dimensions from geometry
    let lotWidth: number | undefined;
    let lotDepth: number | undefined;

    if (attrs.Shape__Area && geometry) {
      const dims = calculateDimensions(geometry, attrs.Shape__Area, attrs.Shape__Length || 0);
      lotWidth = dims.width;
      lotDepth = dims.depth;
    }

    return {
      apn: attrs.apn || '',
      address: attrs.situsaddress || '',
      city: attrs.situscity || 'Santa Monica',
      zip: attrs.situszip || '',
      useCode: attrs.usecode || '',
      useDescription: attrs.usedescription || '',
      yearBuilt: attrs.yearbuilt1,
      units: attrs.units1,
      sqft: attrs.sqftmain1,
      center_lat: attrs.center_lat,
      center_lon: attrs.center_lon,
      lotSizeSqft: attrs.Shape__Area ? Math.round(attrs.Shape__Area) : undefined,
      lotPerimeter: attrs.Shape__Length ? Math.round(attrs.Shape__Length) : undefined,
      lotWidth,
      lotDepth,
      geometry, // Include the geometry for map display
    };
  } catch (error) {
    console.error('Error querying parcel:', error);
    return null;
  }
}

/**
 * Get parcel by APN
 */
export async function getParcelByAPN(apn: string): Promise<ParcelDataSimple | null> {
  try {
    const data = await cachedFetch<any>(`${GIS_SERVICES.PARCELS_PUBLIC.url}/query`, {
      where: `apn = '${apn}'`,
      outFields: '*',
      f: 'json',
      returnGeometry: true,
    });

    if (!data.features || data.features.length === 0) {
      return null;
    }

    const attrs = data.features[0].attributes;

    return {
      apn: attrs.apn || '',
      address: attrs.situsaddress || '',
      city: attrs.situscity || 'Santa Monica',
      zip: attrs.situszip || '',
      useCode: attrs.usecode || '',
      useDescription: attrs.usedescription || '',
      yearBuilt: attrs.yearbuilt1,
      units: attrs.units1,
      sqft: attrs.sqftmain1,
      center_lat: attrs.center_lat,
      center_lon: attrs.center_lon,
      lotSizeSqft: attrs.Shape__Area ? Math.round(attrs.Shape__Area) : undefined,
      lotPerimeter: attrs.Shape__Length ? Math.round(attrs.Shape__Length) : undefined,
    };
  } catch (error) {
    console.error('Error querying parcel by APN:', error);
    return null;
  }
}
