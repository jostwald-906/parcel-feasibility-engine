'use client';

import { useState, useEffect } from 'react';
import { Building2, Ruler, Home, AlertTriangle, Sliders, Waves, Landmark, Droplet, Bus, FileText, AlertCircle } from 'lucide-react';
import type { Parcel, AnalysisRequest, ProposedProject } from '@/lib/types';
import type { ParcelAnalysis } from '@/lib/arcgis-client';
import { mapOverlaysToTier } from '@/lib/arcgis-client';
import ParcelAutocomplete from './ParcelAutocomplete';
import ProposedProjectForm from './ProposedProjectForm';
import { SANTA_MONICA_ZONING_CODES, ZONING_CATEGORIES, ZONING_CODES_BY_CATEGORY } from '@/lib/constants/zoning-codes';

interface ParcelFormProps {
  onSubmit: (request: AnalysisRequest) => void;
  isLoading?: boolean;
  initialData?: ParcelAnalysis | null;
}

export default function ParcelForm({ onSubmit, isLoading = false, initialData = null }: ParcelFormProps) {
  const [formData, setFormData] = useState<Partial<Parcel>>({
    apn: '',
    address: '',
    city: 'Santa Monica',
    county: 'Los Angeles',
    zip_code: '',
    lot_size_sqft: undefined,
    zoning_code: 'R1',
    existing_units: 0,
    existing_building_sqft: 0,
    year_built: undefined,
    latitude: undefined,
    longitude: undefined,
    for_sale: false,
    avg_bedrooms_per_unit: undefined,
    near_transit: undefined,
    street_row_width: undefined,
  });

  // Check if current zoning code is in our known list
  const isKnownZoningCode = SANTA_MONICA_ZONING_CODES.some(z => z.code === formData.zoning_code);

  // Helper: Check if zoning is commercial/office/mixed-use for AB 2011
  const isCommercialZoning = (zoningCode: string): boolean => {
    const code = zoningCode.toUpperCase();
    const commercialPatterns = ['C', 'COMMERCIAL', 'OFFICE', 'O', 'MU', 'MIXED'];
    return commercialPatterns.some(pattern => code.includes(pattern));
  };

  // Helper: Check SB35 eligibility (site exclusions)
  const isSB35Eligible = (data?: ParcelAnalysis | null): boolean => {
    if (!data) return true;

    // SB35 site exclusions per Gov. Code § 65913.4(a)(6)
    return !(
      data.historic.isHistoric ||
      data.environmental.inWetlands ||
      data.environmental.inConservationArea ||
      data.environmental.fireHazardZone === 'Very High' ||
      data.environmental.nearHazardousWaste ||
      (data.coastal.inCoastalZone && data.flood.inFloodZone)
    );
  };

  // Helper: Get SB35 exclusion reason
  const getSB35ExclusionReason = (data?: ParcelAnalysis | null): string | null => {
    if (!data) return null;
    if (data.historic.isHistoric) return 'Historic property';
    if (data.environmental.inWetlands) return 'Wetlands';
    if (data.environmental.inConservationArea) return 'Conservation area';
    if (data.environmental.fireHazardZone === 'Very High') return 'Very High fire hazard zone';
    if (data.environmental.nearHazardousWaste) return 'Near hazardous waste site';
    if (data.coastal.inCoastalZone && data.flood.inFloodZone) return 'Coastal high hazard zone';
    return null;
  };

  // Helper: Check if zoning is single-family for SB9
  const isSingleFamilyZoning = (zoningCode: string): boolean => {
    const code = zoningCode.toUpperCase();
    return code.includes('R1') || code.includes('RS') || code.includes('SINGLE');
  };

  // Helper: Check SB9 eligibility
  const isSB9Eligible = (data?: ParcelAnalysis | null, zoningCode?: string): boolean => {
    const zoning = zoningCode || data?.zoning.zoneCode || formData.zoning_code || '';

    // Must be single-family zoning
    if (!isSingleFamilyZoning(zoning)) {
      return false;
    }

    // Cannot be historic
    if (data?.historic.isHistoric) {
      return false;
    }

    return true;
  };

  // Helper: Get SB9 exclusion reason
  const getSB9ExclusionReason = (data?: ParcelAnalysis | null, zoningCode?: string): string | null => {
    const zoning = zoningCode || data?.zoning.zoneCode || formData.zoning_code || '';

    if (!isSingleFamilyZoning(zoning)) {
      return 'Not single-family zoning (requires R1, RS, or similar)';
    }

    if (data?.historic.isHistoric) {
      return 'Historic property';
    }

    return null;
  };

  // Helper: Check AB 2011 eligibility
  const isAB2011Eligible = (data?: ParcelAnalysis | null, zoningCode?: string): boolean => {
    // Must have commercial/office/mixed-use zoning
    const zoning = zoningCode || data?.zoning.zoneCode || formData.zoning_code || '';
    if (!isCommercialZoning(zoning)) {
      return false;
    }

    // Cannot be historic (similar to SB 9)
    if (data?.historic.isHistoric) {
      return false;
    }

    return true;
  };

  // Auto-populate form when parcel is selected from map
  useEffect(() => {
    if (initialData) {
      // Map overlays to tier and overlay codes
      const tierData = mapOverlaysToTier(initialData.overlays || []);

      setFormData({
        apn: initialData.parcel.apn || '',
        address: initialData.parcel.address || '',
        city: initialData.parcel.city || 'Santa Monica',
        county: 'Los Angeles',
        zip_code: initialData.parcel.zip || '',
        lot_size_sqft: initialData.parcel.lotSizeSqft || undefined,
        lot_width_ft: initialData.parcel.lotWidth || undefined,
        lot_depth_ft: initialData.parcel.lotDepth || undefined,
        zoning_code: initialData.zoning.zoneCode || 'R1',
        existing_units: initialData.parcel.units || 0,
        existing_building_sqft: initialData.parcel.sqft || 0,
        year_built: initialData.parcel.yearBuilt ? parseInt(initialData.parcel.yearBuilt) : undefined,
        latitude: initialData.parcel.latitude,
        longitude: initialData.parcel.longitude,
        near_transit: initialData.transit.withinHalfMile,
        for_sale: false,
        avg_bedrooms_per_unit: undefined,
        // Environmental and hazard flags
        in_coastal_zone: initialData.coastal.inCoastalZone,
        in_flood_zone: initialData.flood.inFloodZone,
        is_historic_property: initialData.historic.isHistoric,
        // Environmental GIS data for SB35/AB2011 exclusions
        in_wetlands: initialData.environmental.inWetlands,
        in_conservation_area: initialData.environmental.inConservationArea,
        fire_hazard_zone: initialData.environmental.fireHazardZone,
        near_hazardous_waste: initialData.environmental.nearHazardousWaste,
        in_earthquake_fault_zone: initialData.environmental.inEarthquakeFaultZone,
        // Tier and overlay data
        development_tier: tierData.development_tier,
        overlay_codes: tierData.overlay_codes,
        // AB 2011 street ROW width
        street_row_width: initialData.street.rowWidth ?? undefined,
      });

      // Auto-disable SB9 if not eligible
      if (!isSB9Eligible(initialData)) {
        setOptions(prev => ({ ...prev, include_sb9: false }));
      }

      // Auto-disable SB35 if has site exclusions
      if (!isSB35Eligible(initialData)) {
        setOptions(prev => ({ ...prev, include_sb35: false }));
      }

      // Auto-disable AB2011 if not eligible
      if (!isAB2011Eligible(initialData)) {
        setOptions(prev => ({ ...prev, include_ab2011: false }));
      }
    }
  }, [initialData]);

  // Auto-update analysis options when zoning code changes
  useEffect(() => {
    if (formData.zoning_code) {
      // Auto-disable SB9 if zoning becomes non-single-family
      if (!isSB9Eligible(initialData, formData.zoning_code)) {
        setOptions(prev => ({ ...prev, include_sb9: false }));
      }

      // Auto-disable AB2011 if zoning becomes non-commercial
      if (!isAB2011Eligible(initialData, formData.zoning_code)) {
        setOptions(prev => ({ ...prev, include_ab2011: false }));
      }
    }
  }, [formData.zoning_code, initialData]);

  const [options, setOptions] = useState({
    include_sb9: true,
    include_sb35: true,
    include_ab2011: false,
    include_density_bonus: true,
    target_affordability_pct: 15,
  });

  const [proposedProject, setProposedProject] = useState<ProposedProject | undefined>(undefined);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const parsedValue = type === 'number' ? (value === '' ? undefined : parseFloat(value)) : value;

    setFormData(prev => ({
      ...prev,
      [name]: parsedValue,
    }));
  };

  const handleOptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, type, checked, value } = e.target;
    setOptions(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : parseFloat(value),
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.apn || !formData.address || !formData.lot_size_sqft || !formData.zoning_code) {
      alert('Please fill in all required fields');
      return;
    }

    const request: AnalysisRequest = {
      parcel: formData as Parcel,
      proposed_project: proposedProject,
      ...options,
    };

    onSubmit(request);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* STEP 1: Site Identification */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-1">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">1. Site Identification</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">Basic parcel information and location</p>

        <div className="space-y-4">
          {/* APN - with autocomplete */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              APN (Assessor Parcel Number) *
            </label>
            <ParcelAutocomplete
              onParcelSelected={(analysis) => {
                // Auto-populate form from GIS data
                setFormData({
                  apn: analysis.parcel.apn,
                  address: analysis.parcel.situsFullAddress || analysis.parcel.address,
                  city: analysis.parcel.city || 'Santa Monica',
                  county: 'Los Angeles',
                  zip_code: analysis.parcel.zip || '',
                  lot_size_sqft: analysis.parcel.lotSizeSqft || undefined,
                  lot_width_ft: analysis.parcel.lotWidth || undefined,
                  lot_depth_ft: analysis.parcel.lotDepth || undefined,
                  zoning_code: analysis.zoning.zoneCode || 'R1',
                  existing_units: analysis.parcel.units || 0,
                  existing_building_sqft: analysis.parcel.sqft || 0,
                  year_built: analysis.parcel.yearBuilt ? parseInt(analysis.parcel.yearBuilt) : undefined,
                  latitude: analysis.parcel.latitude,
                  longitude: analysis.parcel.longitude,
                  for_sale: false,
                  avg_bedrooms_per_unit: analysis.parcel.bedrooms ? analysis.parcel.bedrooms / (analysis.parcel.units || 1) : undefined,
                  near_transit: analysis.transit.withinHalfMile,
                  // Environmental and hazard flags
                  in_coastal_zone: analysis.coastal.inCoastalZone,
                  in_flood_zone: analysis.flood.inFloodZone,
                  is_historic_property: analysis.historic.isHistoric,
                  // Environmental GIS data for SB35/AB2011 exclusions
                  in_wetlands: analysis.environmental.inWetlands,
                  in_conservation_area: analysis.environmental.inConservationArea,
                  fire_hazard_zone: analysis.environmental.fireHazardZone,
                  near_hazardous_waste: analysis.environmental.nearHazardousWaste,
                  in_earthquake_fault_zone: analysis.environmental.inEarthquakeFaultZone,
                  // AB 2011 street ROW width
                  street_row_width: analysis.street.rowWidth ?? undefined,
                  ...mapOverlaysToTier(analysis.overlays),
                });
              }}
              placeholder="Search by APN (e.g., 4289-005-004)"
            />
            <p className="text-xs text-gray-500 mt-1">
              Type at least 3 characters to search. You can also manually enter values below.
            </p>
          </div>

          {/* Manual APN entry (fallback) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Or enter APN manually
            </label>
            <input
              type="text"
              name="apn"
              value={formData.apn}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              placeholder="4276-019-030"
              required
            />
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Street Address *
            </label>
            <input
              type="text"
              name="address"
              value={formData.address}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              placeholder="123 Main Street"
              required
            />
          </div>

          {/* City & ZIP */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                City *
              </label>
              <input
                type="text"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ZIP Code *
              </label>
              <input
                type="text"
                name="zip_code"
                value={formData.zip_code}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="90401"
                required
              />
            </div>
          </div>

          {/* Lat/Long (optional, collapsible) */}
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-600 hover:text-gray-900 font-medium">
              Advanced: Coordinates (optional)
            </summary>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  name="latitude"
                  step="0.000001"
                  value={formData.latitude || ''}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  placeholder="34.0195"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  name="longitude"
                  step="0.000001"
                  value={formData.longitude || ''}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  placeholder="-118.4912"
                />
              </div>
            </div>
          </details>
        </div>
      </div>

      {/* STEP 2: Site Characteristics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-1">
          <Ruler className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">2. Site Characteristics</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">Lot dimensions and zoning designation</p>

        <div className="space-y-4">
          {/* Lot Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Lot Size (sq ft) *
            </label>
            <input
              type="number"
              name="lot_size_sqft"
              value={formData.lot_size_sqft || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              placeholder="5000"
              required
            />
          </div>

          {/* Width & Depth */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lot Width (ft)
              </label>
              <input
                type="number"
                name="lot_width_ft"
                value={formData.lot_width_ft || ''}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lot Depth (ft)
              </label>
              <input
                type="number"
                name="lot_depth_ft"
                value={formData.lot_depth_ft || ''}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                placeholder="100"
              />
            </div>
          </div>

          {/* Zoning Code */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Zoning Code *
            </label>
            <select
              name="zoning_code"
              value={formData.zoning_code}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              required
            >
              {/* If zoning code from GIS is not in our known list, show it as the first option */}
              {!isKnownZoningCode && formData.zoning_code && (
                <option value={formData.zoning_code}>
                  {formData.zoning_code} - {initialData?.zoning.zoneDescription || 'From GIS Data'}
                </option>
              )}

              {ZONING_CATEGORIES.map(category => (
                <optgroup key={category} label={category}>
                  {ZONING_CODES_BY_CATEGORY[category]?.map(zone => (
                    <option key={zone.code} value={zone.code}>
                      {zone.code} - {zone.description}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            {!isKnownZoningCode && formData.zoning_code && (
              <p className="text-xs text-amber-600 mt-1">
                ⚠️ Custom zoning code from GIS data. Verify with local zoning ordinance.
              </p>
            )}
          </div>

          {/* AB 2011 Street ROW Width */}
          {isCommercialZoning(formData.zoning_code || '') && (
            <details className="text-sm">
              <summary className="cursor-pointer text-gray-600 hover:text-gray-900 font-medium">
                AB 2011: Street Right-of-Way Width (optional)
              </summary>
              <div className="mt-2 space-y-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Street ROW Width (feet)
                  </label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={formData.street_row_width || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      street_row_width: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                    placeholder="e.g., 100"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    For AB 2011 corridor classification: 70-99 ft = Narrow (40 u/ac), 100-150 ft = Wide (60 u/ac)
                  </p>
                  {initialData?.street.dataSource === 'estimated' && (
                    <p className="text-xs text-amber-600 mt-1">
                      ⚠️ Estimated from street classification: {initialData.street.streetName || 'Unknown street'}.
                      {' '}For accurate ROW width, contact: <a href="mailto:gis.mailbox@santamonica.gov" className="underline">gis.mailbox@santamonica.gov</a>
                    </p>
                  )}
                </div>
              </div>
            </details>
          )}
        </div>
      </div>

      {/* STEP 3: Existing Conditions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-1">
          <Home className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">3. Existing Conditions</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">Current development on the site</p>

        {/* Current Use Information */}
        {(initialData?.parcel?.useDescription || initialData?.parcel?.useCode) && (
          <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="text-xs font-semibold text-gray-600 mb-1">Current Use</div>
            {initialData.parcel.useDescription && (
              <div className="text-sm font-medium text-gray-900">{initialData.parcel.useDescription}</div>
            )}
            {initialData.parcel.useCode && (
              <div className="text-xs text-gray-500 mt-0.5">Code: {initialData.parcel.useCode}</div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Existing Units
            </label>
            <input
              type="number"
              name="existing_units"
              value={formData.existing_units}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              placeholder="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Existing Building (sq ft)
            </label>
            <input
              type="number"
              name="existing_building_sqft"
              value={formData.existing_building_sqft}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              placeholder="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Year Built
            </label>
            <input
              type="number"
              name="year_built"
              value={formData.year_built || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              placeholder="1955"
            />
          </div>
        </div>
      </div>

      {/* STEP 4: Proposed Project Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-1">
          <Building2 className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">4. Proposed Project Details</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Information about your proposed development (optional - for validation against allowed scenarios)
        </p>

        <ProposedProjectForm
          value={proposedProject}
          onChange={setProposedProject}
        />

        {/* AB 2097 Parking Elimination Notice */}
        {formData.near_transit && (
          <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg mt-4">
            <AlertCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="text-sm font-medium text-green-900">AB 2097 Parking Elimination Applies</span>
              <p className="text-xs text-green-700 mt-1">
                This parcel is within ½ mile of quality transit. Under AB 2097, parking requirements may be eliminated or significantly reduced for qualifying developments.
              </p>
            </div>
          </div>
        )}

        {/* Coastal Zone Warning for Santa Monica */}
        {formData.city?.toLowerCase().includes('santa monica') && (
          <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg mt-4">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="text-sm font-medium text-amber-900">Coastal Zone Consideration</span>
              <p className="text-xs text-amber-700 mt-1">
                Santa Monica is within the California Coastal Zone. Some state housing laws may require coordination with the Local Coastal Program (LCP) and Coastal Development Permits (CDP).
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Site Constraints (if available from GIS) */}
      {initialData && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="text-lg font-semibold text-gray-900">Site Constraints</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">Regulatory constraints identified from GIS data</p>

          <div className="space-y-3">
            {initialData.historic.isHistoric && (
              <div className="flex items-start gap-3 p-3 bg-amber-50 border-l-4 border-amber-500 rounded">
                <Landmark className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-amber-900">Historic Resource</p>
                  <p className="text-sm text-amber-700 mt-1">
                    {initialData.historic.resourceName || 'Listed as historic resource'}. SB 9 lot splits are not eligible.
                  </p>
                </div>
              </div>
            )}

            {initialData.coastal.inCoastalZone && (
              <div className="flex items-start gap-3 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
                <Waves className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">Coastal Zone</p>
                  <p className="text-sm text-blue-700 mt-1">
                    Coastal Development Permit (CDP) may be required. Additional review by Coastal Commission.
                  </p>
                </div>
              </div>
            )}

            {initialData.flood.inFloodZone && (
              <div className="flex items-start gap-3 p-3 bg-sky-50 border-l-4 border-sky-500 rounded">
                <Droplet className="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-sky-900">Flood Zone</p>
                  <p className="text-sm text-sky-700 mt-1">
                    FEMA flood zone {initialData.flood.fldZone || 'identified'}. Flood insurance and elevation requirements may apply.
                  </p>
                </div>
              </div>
            )}

            {initialData.transit.withinHalfMile && (
              <div className="flex items-start gap-3 p-3 bg-green-50 border-l-4 border-green-500 rounded">
                <Bus className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">Transit-Oriented Location (AB 2097)</p>
                  <p className="text-sm text-green-700 mt-1">
                    Within 1/2 mile of major transit stop. Parking requirements may be reduced or eliminated under AB 2097.
                  </p>
                </div>
              </div>
            )}

            {!initialData.historic.isHistoric && !initialData.coastal.inCoastalZone && !initialData.flood.inFloodZone && !initialData.transit.withinHalfMile && (
              <div className="flex items-start gap-3 p-3 bg-gray-50 border border-gray-200 rounded">
                <div className="flex-1">
                  <p className="text-sm text-gray-600">✓ No special constraints identified</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analysis Options */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-1">
          <Sliders className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">5. Analysis Options</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">Select which California housing laws to evaluate</p>

        <div className="space-y-3">
          <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
            <input
              type="checkbox"
              name="include_sb9"
              checked={options.include_sb9}
              onChange={handleOptionChange}
              disabled={!isSB9Eligible(initialData, formData.zoning_code)}
              className="w-4 h-4 mt-0.5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <div className="flex-1">
              <span className={`text-sm font-medium ${!isSB9Eligible(initialData, formData.zoning_code) ? 'text-gray-400' : 'text-gray-900'}`}>
                SB 9 (2021) - Lot Splits & Duplexes
              </span>
              <p className="text-xs text-gray-600 mt-1">
                Up to 4 units on single-family lots
                {!isSB9Eligible(initialData, formData.zoning_code) && ` (Not eligible - ${getSB9ExclusionReason(initialData, formData.zoning_code)})`}
              </p>
            </div>
          </label>

          <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
            <input
              type="checkbox"
              name="include_sb35"
              checked={options.include_sb35}
              onChange={handleOptionChange}
              disabled={!isSB35Eligible(initialData)}
              className="w-4 h-4 mt-0.5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <div className="flex-1">
              <span className={`text-sm font-medium ${!isSB35Eligible(initialData) ? 'text-gray-400' : 'text-gray-900'}`}>
                SB 35 (2017) - Streamlined Approval
              </span>
              <p className="text-xs text-gray-600 mt-1">
                Ministerial approval for multifamily projects with required affordable housing (10-50% depending on RHNA performance)
                {!isSB35Eligible(initialData) && ` (Not eligible - ${getSB35ExclusionReason(initialData)})`}
              </p>
            </div>
          </label>

          {/* SB 35 Additional Context (when enabled) */}
          {options.include_sb35 && (
            <div className="ml-11 p-3 bg-indigo-50 border border-indigo-200 rounded-lg space-y-2">
              <p className="text-xs font-medium text-indigo-900">SB 35 Requirements:</p>
              <ul className="text-xs text-indigo-700 space-y-1 ml-4 list-disc">
                <li><strong>Affordability:</strong> 10% in high-performing cities (SF, San Jose, Sacramento), 50% elsewhere</li>
                <li><strong>Labor Standards:</strong> Prevailing wage at 10+ units, skilled & trained workforce at 75+ units</li>
                <li><strong>Parking:</strong> AB 2097 transit parking elimination applies if near transit (shown above)</li>
                <li><strong>Approval:</strong> Ministerial (no discretionary review), CEQA exempt</li>
                <li><strong>Standards:</strong> Must meet all local objective design standards</li>
              </ul>
              <p className="text-xs text-indigo-600 italic mt-2">
                Note: Eligibility requires residential/mixed-use zoning, 3,500+ sf lot, and jurisdiction RHNA compliance.
              </p>
            </div>
          )}

          <label className={`flex items-start gap-3 p-3 border border-gray-200 rounded-lg transition-colors ${
            isAB2011Eligible(initialData, formData.zoning_code)
              ? 'hover:bg-gray-50 cursor-pointer'
              : 'bg-gray-50 cursor-not-allowed'
          }`}>
            <input
              type="checkbox"
              name="include_ab2011"
              checked={options.include_ab2011}
              onChange={handleOptionChange}
              disabled={!isAB2011Eligible(initialData, formData.zoning_code)}
              className="w-4 h-4 mt-0.5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <div className="flex-1">
              <span className={`text-sm font-medium ${
                isAB2011Eligible(initialData, formData.zoning_code) ? 'text-gray-900' : 'text-gray-400'
              }`}>
                AB 2011 (2022) - Affordable Corridor Housing
              </span>
              <p className="text-xs text-gray-600 mt-1">
                Ministerial multifamily housing on commercial corridors with state density/height minimums
                {!isAB2011Eligible(initialData, formData.zoning_code) && (
                  <>
                    {' '}
                    {!isCommercialZoning(formData.zoning_code || '') && '(Not eligible - Requires commercial/office/mixed-use zoning)'}
                    {isCommercialZoning(formData.zoning_code || '') && initialData?.historic.isHistoric && '(Not eligible - Historic property)'}
                  </>
                )}
              </p>
            </div>
          </label>

          {/* AB 2011 Additional Context (when eligible) */}
          {options.include_ab2011 && isAB2011Eligible(initialData, formData.zoning_code) && (
            <div className="ml-11 p-3 bg-purple-50 border border-purple-200 rounded-lg space-y-2">
              <p className="text-xs font-medium text-purple-900">AB 2011 Requirements:</p>
              <ul className="text-xs text-purple-700 space-y-1 ml-4 list-disc">
                <li><strong>Affordability:</strong> Either 100% affordable OR mixed-income (minimum % varies by jurisdiction)</li>
                <li><strong>Labor Standards:</strong> Prevailing wage and skilled & trained workforce requirements apply</li>
                <li><strong>Parking:</strong> AB 2097 transit parking elimination may apply (shown above if near transit)</li>
                <li><strong>Design:</strong> Must meet local objective design standards while respecting state minimum floors</li>
                <li><strong>Protected Units:</strong> Cannot demolish rent-controlled or deed-restricted affordable units</li>
              </ul>
              <p className="text-xs text-purple-600 italic mt-2">
                Note: Backend analysis will apply state minimum density/height floors (30-80 u/ac, 35-65 ft) based on corridor tier.
              </p>
            </div>
          )}

          <label className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
            <input
              type="checkbox"
              name="include_density_bonus"
              checked={options.include_density_bonus}
              onChange={handleOptionChange}
              className="w-4 h-4 mt-0.5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex-1">
              <span className="text-sm font-medium text-gray-900">Density Bonus Law</span>
              <p className="text-xs text-gray-600 mt-1">
                Additional density and concessions for affordable housing
              </p>
            </div>
          </label>

          {options.include_density_bonus && (
            <div className="ml-11 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Affordability Level (%)
              </label>
              <input
                type="number"
                name="target_affordability_pct"
                value={options.target_affordability_pct}
                onChange={handleOptionChange}
                min="0"
                max="100"
                step="5"
                className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              />
              <p className="text-xs text-gray-600 mt-2">
                Percentage of units set aside as affordable (e.g., 15% = 15% affordable, 85% market-rate)
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          type="submit"
          disabled={isLoading}
          className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing...
            </span>
          ) : (
            'Analyze Development Potential'
          )}
        </button>
      </div>
    </form>
  );
}
