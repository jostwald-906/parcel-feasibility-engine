/**
 * TypeScript types for GIS data structures
 */

export interface ParcelGISData {
  apn: string;
  address: string;
  lotArea: number;
  geometry: {
    type: 'Polygon';
    coordinates: [number, number][][];
  };
  centroid: {
    lat: number;
    lng: number;
  };
}

export interface ZoningData {
  zoneCode: string;
  overlay?: string;
  maxHeight?: number;
  maxFAR?: number;
  parkingRatio?: number;
  allowedUses?: string[];
}

export interface HistoricData {
  isHistoric: boolean;
  districtName?: string;
  landmarkId?: string;
  status?: string;
}

export interface CoastalData {
  isCoastal: boolean;
  zoneType?: string;
  appealJurisdiction?: string;
}

export interface FloodData {
  isInFloodZone: boolean;
  zoneType?: string;
  floodRisk?: string;
  baseFloodElevation?: number;
}

export interface SpecificPlanData {
  plans: Array<{
    name: string;
    type: string;
    adoptedDate?: string;
  }>;
}

export interface AffordableOverlayData {
  hasOverlay: boolean;
  overlayType?: string;
  maxDensity?: number;
  affordabilityRequirement?: number;
}

export interface TransitProximityData {
  isNearTransit: boolean;
  distance: number;
  nearestStop?: string;
  ab2097Eligible: boolean;
}

export interface SetbackData {
  front: number;
  side: number;
  rear: number;
}

export interface ParcelOverlayData {
  parcel: ParcelGISData;
  zoning: ZoningData;
  historic: HistoricData;
  coastal: CoastalData;
  flood: FloodData;
  specificPlans: SpecificPlanData;
  affordableOverlay: AffordableOverlayData;
  transitProximity: TransitProximityData;
  setbacks?: SetbackData;
}

export interface SB9Eligibility {
  eligible: boolean;
  reasons: string[];
  maxUnits: number;
  allowLotSplit: boolean;
}

export interface SB35Eligibility {
  eligible: boolean;
  reasons: string[];
  streamlinedApproval: boolean;
  affordabilityRequired: number;
}
