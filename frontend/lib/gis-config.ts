/**
 * Santa Monica GIS Service Configuration
 *
 * This file contains ArcGIS REST service endpoints for Santa Monica's open data portal.
 * Update these URLs with actual service endpoints from data.smgov.net
 */

export const GIS_SERVICES = {
  // Primary parcel layer - derived from LA County Assessor data
  PARCELS_PUBLIC: {
    url: 'https://gis.santamonica.gov/server/rest/services/Parcels_Public/FeatureServer/0',
    name: 'Parcels Public',
    description: '23,586 tax parcels with APN and boundaries',
    fields: ['apn', 'ain', 'situsaddress', 'situsfulladdress', 'usecode', 'usedescription', 'yearbuilt1', 'units1', 'sqftmain1'],
  },

  // Base zoning districts and overlays
  ZONING: {
    url: 'https://gis.santamonica.gov/server/rest/services/Zoning_Update/FeatureServer/0',
    name: 'Zoning Districts',
    description: 'Base zoning, overlays, parking regulations',
    fields: ['zoning', 'overlay', 'label', 'major_cat', 'zonedesc', 'overlaydes'],
  },

  // Historic resources
  HISTORIC: {
    url: 'https://gis.santamonica.gov/server/rest/services/Historic_Preservation_Layers/FeatureServer/2',
    name: 'Historic Resources Inventory',
    description: 'Historic districts and individually listed properties',
    fields: ['ain', 'district_name', 'resource_name', 'resource_evaluation', 'individually_eligible', 'architectural_style', 'year_built'],
  },

  // Specific plans and community plan areas (using Bergamot as primary)
  SPECIFIC_PLANS: {
    url: 'https://gis.santamonica.gov/server/rest/services/Bergamot_Area_Plan/FeatureServer/1',
    name: 'Specific Plans',
    description: 'Downtown, Bergamot, Memorial Park plan areas',
    fields: ['area_name', 'label'],
  },

  // Downtown Community Plan overlay
  DOWNTOWN_OVERLAY: {
    url: 'https://gis.santamonica.gov/server/rest/services/DCP_Plan_Designations/FeatureServer/0',
    name: 'Downtown Community Plan',
    description: 'Downtown Community Plan designations',
    fields: ['plan_desig', 'label'],
  },

  // California Coastal Zone
  COASTAL_ZONE: {
    url: 'https://gis.santamonica.gov/server/rest/services/Coastal_Zone/FeatureServer/0',
    name: 'Coastal Zone',
    description: 'California Coastal Zone boundary - requires CDP',
    fields: ['zone_type', 'appeal_jurisdiction'],
  },

  // Flood and environmental hazards
  FLOOD_HAZARD: {
    url: 'https://gis.santamonica.gov/server/rest/services/FEMA_National_Flood_Hazard_Area/MapServer/0',
    name: 'Flood Zones',
    description: 'FEMA flood zones and hazard areas',
    fields: ['fld_zone', 'zone_subty', 'static_bfe'],
  },

  // Transit stops and routes
  TRANSIT_STOPS: {
    url: 'https://gis.santamonica.gov/server/rest/services/Big_Blue_Bus_Stops_and_Routes/FeatureServer/0',
    name: 'Transit Stops',
    description: 'Big Blue Bus stops and major transit',
    fields: ['stop_id', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon'],
  },

  // Major transit stops (for AB 2097 eligibility)
  MAJOR_TRANSIT: {
    url: 'https://gis.santamonica.gov/server/rest/services/Transit_Priority_Area/FeatureServer/3',
    name: 'Major Transit Stops',
    description: 'Half mile buffer from major transit stops',
    fields: ['stop_name', 'route_type'],
  },

  // Setback reference data
  SETBACKS: {
    url: 'https://gis.santamonica.gov/server/rest/services/Setbacks/FeatureServer/0',
    name: 'Setback Standards',
    description: 'Point layer with setback distances by zoning district',
    fields: ['zone_code', 'front_setback', 'side_setback', 'rear_setback'],
  },

  // Unbundled parking overlay
  UNBUNDLED_PARKING: {
    url: 'https://gis.santamonica.gov/server/rest/services/Unbundled_Parking/FeatureServer/0',
    name: 'Unbundled Parking Overlay',
    description: 'Areas requiring unbundled parking for multi-family development',
    fields: ['overlay_type', 'description'],
  },
};

// Santa Monica bounding box for map initialization
export const SANTA_MONICA_BOUNDS = {
  center: [34.0195, -118.4912] as [number, number],
  zoom: 13,
  bounds: {
    north: 34.0598,
    south: 33.9792,
    east: -118.4615,
    west: -118.5209,
  },
};

// Spatial reference system
export const SPATIAL_REFERENCE = {
  wkid: 4326, // WGS84
  wkt: 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]',
};
