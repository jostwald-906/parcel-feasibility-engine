'use client';

import { Building2, Shield, Waves, Landmark, Droplet, Bus, AlertTriangle, Home, Maximize2, Loader2 } from 'lucide-react';
import type { ParcelAnalysis } from '@/lib/arcgis-client';
import OverlayDetailCard from './OverlayDetailCard';

interface ParcelInfoPanelProps {
  analysis: ParcelAnalysis | null;
  isLoading?: boolean;
}

export default function ParcelInfoPanel({ analysis, isLoading }: ParcelInfoPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          <h3 className="text-lg font-semibold text-gray-900">Loading Parcel Data...</h3>
        </div>
        <p className="text-sm text-gray-500">
          Querying GIS systems for parcel information, zoning, and constraints...
        </p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900">Parcel Information</h3>
        </div>
        <p className="text-sm text-gray-500">
          Click on the map or enter parcel details to view comprehensive information
        </p>
      </div>
    );
  }

  const { parcel, zoning, historic, coastal, flood, transit, hazards, overlays } = analysis;

  return (
    <div className="space-y-4">
      {/* Basic Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Parcel Details</h3>
        </div>

        <dl className="space-y-3">
          <div>
            <dt className="text-xs font-medium text-gray-500 uppercase">APN</dt>
            <dd className="text-sm font-semibold text-gray-900">{parcel.apn}</dd>
          </div>

          <div>
            <dt className="text-xs font-medium text-gray-500 uppercase">Address</dt>
            <dd className="text-sm text-gray-900">{parcel.situsFullAddress || parcel.address}</dd>
          </div>

          {parcel.lotSizeSqft && (
            <div>
              <dt className="text-xs font-medium text-gray-500 uppercase">Lot Size</dt>
              <dd className="text-sm text-gray-900">{parcel.lotSizeSqft.toLocaleString()} sq ft</dd>
            </div>
          )}

          {parcel.lotWidth && parcel.lotDepth && (
            <div>
              <dt className="text-xs font-medium text-gray-500 uppercase">Dimensions</dt>
              <dd className="text-sm text-gray-900">{parcel.lotWidth}&apos; × {parcel.lotDepth}&apos;</dd>
            </div>
          )}

          {parcel.yearBuilt && (
            <div>
              <dt className="text-xs font-medium text-gray-500 uppercase">Year Built</dt>
              <dd className="text-sm text-gray-900">{parcel.yearBuilt}</dd>
            </div>
          )}

          {parcel.units !== undefined && parcel.units > 0 && (
            <div>
              <dt className="text-xs font-medium text-gray-500 uppercase">Existing Units</dt>
              <dd className="text-sm text-gray-900">{parcel.units}</dd>
            </div>
          )}

          {parcel.sqft && (
            <div>
              <dt className="text-xs font-medium text-gray-500 uppercase">Building Sq Ft</dt>
              <dd className="text-sm text-gray-900">{parcel.sqft.toLocaleString()} sq ft</dd>
            </div>
          )}

          {(parcel.useType || parcel.useDescription) && (
            <div>
              {parcel.useType && (
                <dd className="text-sm font-semibold text-gray-900 mb-1">{parcel.useType}</dd>
              )}
              {parcel.useDescription && (
                <dd className="text-sm text-gray-700">{parcel.useDescription}</dd>
              )}
            </div>
          )}
        </dl>
      </div>

      {/* Zoning */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">Zoning</h3>
        </div>

        <dl className="space-y-3">
          <div>
            <dt className="text-xs font-medium text-gray-500 uppercase">Zone Code</dt>
            <dd className="text-sm font-semibold text-indigo-700">{zoning.zoneCode || 'Unknown'}</dd>
          </div>

          {zoning.zoneDescription && (
            <div>
              <dt className="text-xs font-medium text-gray-500 uppercase">Description</dt>
              <dd className="text-sm text-gray-900">{zoning.zoneDescription}</dd>
            </div>
          )}

          {zoning.overlay && (
            <div>
              <dt className="text-xs font-medium text-gray-500 uppercase">Overlay</dt>
              <dd className="text-sm text-gray-900">{zoning.overlay}</dd>
            </div>
          )}
        </dl>
      </div>

      {/* Constraints & Overlays */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-amber-600" />
          <h3 className="text-lg font-semibold text-gray-900">Constraints</h3>
        </div>

        <div className="space-y-3">
          {/* Historic */}
          {historic.isHistoric ? (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border-l-4 border-amber-500 rounded">
              <Landmark className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-amber-900">Historic Resource</p>
                {historic.resourceName && (
                  <p className="text-xs text-amber-700 mt-1">{historic.resourceName}</p>
                )}
                {historic.architecturalStyle && (
                  <p className="text-xs text-amber-600 mt-0.5">{historic.architecturalStyle}</p>
                )}
              </div>
            </div>
          ) : null}

          {/* Coastal */}
          {coastal.inCoastalZone ? (
            <div className="flex items-start gap-2 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
              <Waves className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-blue-900">Coastal Zone</p>
                <p className="text-xs text-blue-700 mt-1">CDP may be required</p>
              </div>
            </div>
          ) : null}

          {/* Flood */}
          {flood.inFloodZone ? (
            <div className="flex items-start gap-2 p-3 bg-sky-50 border-l-4 border-sky-500 rounded">
              <Droplet className="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-sky-900">Flood Zone {flood.fldZone}</p>
                <p className="text-xs text-sky-700 mt-1">Flood insurance may be required</p>
              </div>
            </div>
          ) : null}

          {/* Transit Proximity */}
          {transit.withinHalfMile ? (
            <div className="flex items-start gap-2 p-3 bg-green-50 border-l-4 border-green-500 rounded">
              <Bus className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-green-900">Transit Accessible (AB 2097)</p>
                {transit.nearestStopName && (
                  <p className="text-xs text-green-700 mt-1">
                    {transit.nearestStopName}
                    {transit.nearestStopDistance && ` • ${Math.round(transit.nearestStopDistance)}m`}
                  </p>
                )}
              </div>
            </div>
          ) : null}

          {/* Hazards */}
          {(hazards.faultZone || hazards.liquefactionZone || hazards.landslideZone) && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border-l-4 border-red-500 rounded">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-red-900">Geohazard Zone</p>
                <div className="text-xs text-red-700 mt-1 space-y-0.5">
                  {hazards.faultZone && <p>• Fault Zone</p>}
                  {hazards.liquefactionZone && <p>• Liquefaction Risk</p>}
                  {hazards.landslideZone && <p>• Landslide Risk</p>}
                </div>
              </div>
            </div>
          )}

          {/* No Constraints */}
          {!historic.isHistoric && !coastal.inCoastalZone && !flood.inFloodZone && !hazards.faultZone && !hazards.liquefactionZone && !hazards.landslideZone && (
            <div className="flex items-start gap-2 p-3 bg-gray-50 border-l-4 border-gray-300 rounded">
              <Shield className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-600">No major constraints identified</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Overlays */}
      {overlays && overlays.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Maximize2 className="w-5 h-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">Overlays & Plans</h3>
          </div>

          <div className="space-y-3">
            {/* Deduplicate overlays by name */}
            {Array.from(new Map(overlays.map(o => [o.name, o])).values()).map((overlay, idx) => {
              const codeLink = getOverlayCodeLink(overlay.name);
              return (
                <OverlayDetailCard
                  key={idx}
                  overlay={{
                    name: overlay.name,
                    description: getOverlayDescription(overlay.name),
                    impact: {
                      impact_type: getOverlayImpactType(overlay.name),
                      far_multiplier: getOverlayFARMultiplier(overlay.name),
                      height_bonus_ft: getOverlayHeightBonus(overlay.name),
                      density_bonus_pct: getOverlayDensityBonus(overlay.name),
                    },
                    requirements: getOverlayRequirements(overlay.name),
                    eligibility: getOverlayEligibility(overlay.name),
                    municipal_code_section: codeLink?.section,
                  }}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Development Opportunities */}
      {transit.withinHalfMile && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
          <div className="flex items-center gap-2 mb-3">
            <Home className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-semibold text-blue-900">Development Opportunities</h3>
          </div>

          <ul className="space-y-2 text-xs text-blue-800">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>AB 2097: Eligible for parking reduction (within ½ mile of transit)</span>
            </li>
            {!historic.isHistoric && zoning.zoneCode?.startsWith('R') && (
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>SB 9: May be eligible for lot split and duplex development</span>
              </li>
            )}
            <li className="flex items-start gap-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>Density Bonus: May qualify for additional units with affordable housing</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}

// Helper functions to enrich overlay data
function getOverlayDescription(name: string): string {
  const nameUpper = name.toUpperCase();

  // Environmental Overlays
  if (nameUpper.includes('CNEL') || nameUpper.includes('NOISE')) {
    return 'Identifies areas with elevated noise levels from traffic, airports, or other sources. May require enhanced acoustic design and mitigation measures for residential development.';
  }

  // Special Plans
  if (nameUpper.includes('DOWNTOWN') || nameUpper.includes('DCP')) {
    return 'Tiered development standards allowing increased density and height in exchange for community benefits such as affordable housing, public open space, or arts facilities. Three-tier system (TA and NV districts).';
  }

  if (nameUpper.includes('BERGAMOT')) {
    return 'Mixed-use creative district with tiered FAR and height standards. Emphasizes arts, creative industries, and transit-oriented development. Three districts: BTV (Transit Village), MUC (Mixed-Use Creative), and CAC (Conservation Art Center).';
  }

  // Housing Overlays
  if (nameUpper.includes('MODERATE') && nameUpper.includes('HOUSING')) {
    return 'Allows increased density (up to 50% bonus) and height (+33 ft) for projects with moderate-income housing. Eliminates parking minimums. SMMC Chapter 9.17.';
  }

  if (nameUpper.includes('AFFORDABLE') || (nameUpper.includes('HOUSING') && nameUpper.includes('OVERLAY'))) {
    return 'State-mandated overlay providing streamlined approval and development bonuses for 100% affordable housing projects. By-right approval for qualifying projects.';
  }

  // Transportation
  if (nameUpper.includes('TRANSIT')) {
    return 'Within 0.5 miles of major transit stop. Eligible for parking reductions under AB 2097 and enhanced development under SB 35.';
  }

  if (nameUpper.includes('BIKE')) {
    return 'Area targeted for enhanced bicycle infrastructure. May include protected bike lanes, bike parking requirements, and connectivity improvements.';
  }

  return 'Special planning area with modified development standards. Click to expand for details.';
}

function getOverlayImpactType(name: string): 'opportunity' | 'neutral' | 'constraint' {
  const constraints = ['CNEL', 'Noise', 'Historic', 'Conservation'];
  const opportunities = ['Downtown', 'Bergamot', 'Housing', 'Affordable', 'Transit'];

  if (constraints.some(c => name.includes(c))) return 'constraint';
  if (opportunities.some(o => name.includes(o))) return 'opportunity';
  return 'neutral';
}

function getOverlayRequirements(name: string): string[] {
  const requirements: Record<string, string[]> = {
    'CNEL': [
      'Acoustic analysis required for noise levels above 60 dB',
      'Enhanced window glazing (STC 30-40 depending on level)',
      'Mechanical ventilation to allow closed windows',
      'Interior noise target: 45 dB CNEL maximum'
    ],
    'Downtown Community Plan': [
      'Tier 2+: Community benefits required (affordable housing, public space, etc.)',
      'Tier 3: Multiple substantial benefits + Development Agreement',
      'Enhanced sustainability standards (LEED Silver or higher recommended)',
      'Ground-floor activation and pedestrian design'
    ],
    'Bergamot': [
      'Arts and creative uses strongly encouraged',
      'Tier 2+: Community benefits required',
      'Enhanced pedestrian realm and public space',
      'Sustainable building practices (all-electric preferred)'
    ],
    'Housing Overlay': [
      'Affordability requirements (income targeting varies)',
      'Deed restrictions (typically 55 years minimum)',
      'May combine with State Density Bonus for additional benefits'
    ]
  };

  for (const [key, reqs] of Object.entries(requirements)) {
    if (name.includes(key)) {
      return reqs;
    }
  }

  return ['Contact Santa Monica Planning Division for specific requirements'];
}

function getOverlayFARMultiplier(name: string): number | undefined {
  if (name.includes('Downtown') || name.includes('DCP')) {
    return 3.5; // Typical Tier 2 with housing
  }
  if (name.includes('Bergamot')) {
    return 2.0; // Typical Tier 2
  }
  if (name.includes('Housing Overlay') || name.includes('Affordable')) {
    return 1.5; // Bonus multiplier
  }
  return undefined;
}

function getOverlayHeightBonus(name: string): number | undefined {
  if (name.includes('Downtown') || name.includes('DCP')) {
    return 15; // Typical Tier 2 bonus
  }
  if (name.includes('Bergamot')) {
    return 28; // Tier 2 increase from base
  }
  if (name.includes('Housing Overlay')) {
    return 33; // MHO height bonus
  }
  return undefined;
}

function getOverlayDensityBonus(name: string): number | undefined {
  if (name.includes('Housing Overlay')) {
    return 50; // Up to 50% density increase
  }
  if (name.includes('Density Bonus')) {
    return 35; // State density bonus (typical)
  }
  return undefined;
}

function getOverlayEligibility(name: string): string[] {
  const eligibility: Record<string, string[]> = {
    'Downtown': [
      'Within Downtown Community Plan boundaries',
      'Minimum lot size varies by tier',
      'Compliance with design guidelines'
    ],
    'Bergamot': [
      'Within Bergamot Area Plan boundaries',
      'BTV, MUC, or CAC zoning designation',
      'Arts/creative uses encouraged'
    ],
    'Housing': [
      'Minimum affordability levels required',
      'Compliance with HCD income targeting',
      'Long-term deed restrictions'
    ]
  };

  for (const [key, elig] of Object.entries(eligibility)) {
    if (name.includes(key)) {
      return elig;
    }
  }

  return ['See Planning Division for eligibility criteria'];
}

function getOverlayCodeLink(name: string): { section: string; url: string } | undefined {
  const codeLinks: Record<string, { section: string; url: string }> = {
    'Downtown': {
      section: 'SMMC Chapter 9.10',
      url: 'https://www.smgov.net/departments/pcd/agendas/Planning-Commission/2017/20170725/s2017072505-A.pdf'
    },
    'Bergamot': {
      section: 'SMMC Chapter 9.12',
      url: 'https://www.smgov.net/departments/pcd/Plans/Bergamot-Area-Plan/'
    },
    'Housing Overlay': {
      section: 'SMMC Chapter 9.17',
      url: 'https://library.municode.com/ca/santa_monica/codes/code_of_ordinances'
    },
    'CNEL': {
      section: 'CA Title 24, Part 2',
      url: 'https://up.codes/viewer/california/ca-building-code-2022/chapter/12/interior-environment'
    }
  };

  for (const [key, link] of Object.entries(codeLinks)) {
    if (name.includes(key)) {
      return link;
    }
  }

  return undefined;
}
