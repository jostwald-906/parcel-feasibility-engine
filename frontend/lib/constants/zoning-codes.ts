/**
 * Santa Monica Zoning Codes
 *
 * Complete list of zoning codes from Santa Monica GIS Zoning service.
 * Data source: https://gis.santamonica.gov/server/rest/services/Zoning_Update/FeatureServer/0
 *
 * Last updated: 2025-01-06
 */

export interface ZoningCode {
  code: string;
  description: string;
  category: string;
}

export const SANTA_MONICA_ZONING_CODES: ZoningCode[] = [
  // Residential Zones
  { code: "R1", description: "Single-Unit Residential", category: "Residential" },
  { code: "R2", description: "Low Density Residential", category: "Residential" },
  { code: "R3", description: "Medium Density Residential", category: "Residential" },
  { code: "R4", description: "Medium Density Residential", category: "Residential" },
  { code: "RMH", description: "Residential Mobile Home Park", category: "Residential" },
  { code: "OP1", description: "Ocean Park Single-Unit Residential", category: "Residential" },
  { code: "OP2", description: "Ocean Park Low Density Residential", category: "Residential" },
  { code: "OP3", description: "Ocean Park Medium Density Residential", category: "Residential" },
  { code: "OP4", description: "Ocean Park High Density Residential", category: "Residential" },
  { code: "OPD", description: "Ocean Park Duplex", category: "Residential" },

  // Commercial & Mixed-Use Zones
  { code: "NC", description: "Neighborhood Commercial", category: "Commercial & Mixed-Use" },
  { code: "GC", description: "General Commercial", category: "Commercial & Mixed-Use" },
  { code: "MUB", description: "Mixed-Use Boulevard", category: "Commercial & Mixed-Use" },
  { code: "MUBL", description: "Mixed-Use Boulevard Low", category: "Commercial & Mixed-Use" },
  { code: "HMU", description: "Healthcare Mixed-Use", category: "Commercial & Mixed-Use" },
  { code: "OC", description: "Office Campus", category: "Commercial & Mixed-Use" },
  { code: "LT", description: "Lincoln Transition", category: "Commercial & Mixed-Use" },
  { code: "WT", description: "Wilshire Transition", category: "Commercial & Mixed-Use" },
  { code: "OT", description: "Ocean Transition", category: "Commercial & Mixed-Use" },

  // Downtown Community Plan
  { code: "TA", description: "Transit Adjacent", category: "Downtown Community Plan" },
  { code: "NV", description: "Neighborhood Village", category: "Downtown Community Plan" },

  // Bergamot Area Plan
  { code: "BTV", description: "Bergamot Transit Village", category: "Bergamot Area Plan" },
  { code: "MUC", description: "Mixed Use Creative", category: "Bergamot Area Plan" },
  { code: "CAC", description: "Conservation: Art Center", category: "Bergamot Area Plan" },

  // Special Districts
  { code: "OF", description: "Oceanfront", category: "Special Districts" },
  { code: "BC", description: "Bayside Conservation", category: "Special Districts" },
  { code: "CCS", description: "Conservation: Creative Sector", category: "Special Districts" },
  { code: "IC", description: "Industrial Conservation", category: "Special Districts" },
  { code: "CC", description: "Civic Center", category: "Special Districts" },
  { code: "OS", description: "Parks and Open Space", category: "Special Districts" },
  { code: "PL", description: "Institutional/Public Lands", category: "Special Districts" },
];

/**
 * Get zoning codes organized by category for grouped dropdowns
 */
export const ZONING_CODES_BY_CATEGORY = SANTA_MONICA_ZONING_CODES.reduce((acc, zone) => {
  if (!acc[zone.category]) {
    acc[zone.category] = [];
  }
  acc[zone.category].push(zone);
  return acc;
}, {} as Record<string, ZoningCode[]>);

/**
 * Get array of category names in display order
 */
export const ZONING_CATEGORIES = [
  "Residential",
  "Commercial & Mixed-Use",
  "Downtown Community Plan",
  "Bergamot Area Plan",
  "Special Districts",
];

/**
 * Get zoning code description
 */
export function getZoningDescription(code: string): string {
  const zone = SANTA_MONICA_ZONING_CODES.find(z => z.code === code.toUpperCase());
  return zone ? zone.description : "Unknown Zone";
}

/**
 * Get zoning code category
 */
export function getZoningCategory(code: string): string {
  const zone = SANTA_MONICA_ZONING_CODES.find(z => z.code === code.toUpperCase());
  return zone ? zone.category : "Other";
}

/**
 * Check if zoning code is residential
 */
export function isResidentialZone(code: string): boolean {
  return getZoningCategory(code) === "Residential";
}

/**
 * Check if zoning code is single-family (for SB9)
 */
export function isSingleFamilyZone(code: string): boolean {
  return ["R1", "OP1"].includes(code.toUpperCase());
}

/**
 * Check if zoning code is commercial (for AB2011)
 */
export function isCommercialZone(code: string): boolean {
  return getZoningCategory(code) === "Commercial & Mixed-Use";
}

/**
 * Check if zoning code is in Downtown Community Plan
 */
export function isDowntownZone(code: string): boolean {
  return getZoningCategory(code) === "Downtown Community Plan";
}

/**
 * Check if zoning code is in Bergamot Area Plan
 */
export function isBergamotZone(code: string): boolean {
  return getZoningCategory(code) === "Bergamot Area Plan";
}
