/**
 * Coordinate transformation utilities using proj4
 *
 * Santa Monica parcels use NAD83 / California State Plane Zone 5 (EPSG:2229)
 * We need to transform to WGS84 (EPSG:4326) for Leaflet
 */

import proj4 from 'proj4';

// Define California State Plane Zone 5 (NAD83, US Survey Feet)
// EPSG:2229 - used by LA County and Santa Monica
proj4.defs('EPSG:2229', '+proj=lcc +lat_1=34.03333333333333 +lat_2=35.46666666666667 +lat_0=33.5 +lon_0=-118 +x_0=2000000.0001016 +y_0=500000.0001016001 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs');

// WGS84 is already defined in proj4 as 'EPSG:4326'

/**
 * Transform a single point from State Plane to WGS84
 * @param x - State Plane X coordinate (easting in feet)
 * @param y - State Plane Y coordinate (northing in feet)
 * @returns [longitude, latitude] in WGS84
 */
export function statePlaneToWGS84(x: number, y: number): [number, number] {
  const [lon, lat] = proj4('EPSG:2229', 'EPSG:4326', [x, y]);
  return [lon, lat];
}

/**
 * Transform ArcGIS polygon geometry to Leaflet-compatible lat/lng coordinates
 * @param geometry - ArcGIS geometry object with rings
 * @returns Array of polygon rings in [lat, lng] format for Leaflet
 */
export function transformParcelGeometry(geometry: any): [number, number][][] {
  if (!geometry || !geometry.rings || geometry.rings.length === 0) {
    return [];
  }

  return geometry.rings.map((ring: number[][]) => {
    return ring.map(([x, y]) => {
      const [lon, lat] = statePlaneToWGS84(x, y);
      return [lat, lon] as [number, number]; // Leaflet uses [lat, lng]
    });
  });
}

/**
 * Calculate the center point of a polygon
 * @param rings - Polygon rings in [lat, lng] format
 * @returns [lat, lng] center point
 */
export function getPolygonCenter(rings: [number, number][][]): [number, number] {
  if (!rings || rings.length === 0 || rings[0].length === 0) {
    return [0, 0];
  }

  const outerRing = rings[0];
  let latSum = 0;
  let lngSum = 0;

  for (const [lat, lng] of outerRing) {
    latSum += lat;
    lngSum += lng;
  }

  return [
    latSum / outerRing.length,
    lngSum / outerRing.length,
  ];
}
