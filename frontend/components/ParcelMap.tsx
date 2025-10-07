'use client';

import { useState } from 'react';
import { MapContainer, TileLayer, Polygon, Popup, CircleMarker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Loader2, AlertCircle, Info } from 'lucide-react';
import { analyzeParcel, type ParcelAnalysis } from '@/lib/arcgis-client';
import { SANTA_MONICA_BOUNDS } from '@/lib/gis-config';
import { transformParcelGeometry, getPolygonCenter } from '@/lib/coordinate-transform';

// Fix Leaflet default icon issue with Next.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface ParcelMapProps {
  onParcelSelected?: (data: ParcelAnalysis) => void;
  onLoadingChange?: (isLoading: boolean) => void;
  height?: string;
}

// Map click handler component
function MapClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => {
      onClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function ParcelMap({ onParcelSelected, onLoadingChange, height = '500px' }: ParcelMapProps) {
  const [selectedParcel, setSelectedParcel] = useState<{
    geometry: [number, number][][];
    apn: string;
    address: string;
    units?: number;
    sqft?: number;
    yearBuilt?: string;
  } | null>(null);
  const [clickLocation, setClickLocation] = useState<[number, number] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overlayInfo, setOverlayInfo] = useState<string | null>(null);

  // Handle map click
  const handleMapClick = async (lat: number, lng: number) => {
    // Immediately show click location for instant feedback
    setClickLocation([lat, lng]);
    setIsLoading(true);
    onLoadingChange?.(true);
    setError(null);
    setOverlayInfo(null);
    setSelectedParcel(null);

    try {
      console.log(`Clicked at: ${lat}, ${lng}`);

      // Try comprehensive analysis first
      let analysis = null;
      try {
        analysis = await analyzeParcel(lng, lat);
        console.log('✓ Comprehensive analysis succeeded:', analysis?.zoning);
      } catch (error) {
        console.error('✗ Comprehensive analysis error:', error);
      }

      // If comprehensive fails, fall back to simple client for parcel data
      if (!analysis) {
        console.log('⚠ Comprehensive analysis failed, trying simple client fallback...');
        const { getParcelNearPoint } = await import('@/lib/arcgis-client-simple');
        const parcelData = await getParcelNearPoint(lng, lat);

        if (!parcelData) {
          setError('No parcel found at this location. Try clicking closer to a building.');
          return;
        }

        // Get zoning separately if we have geometry
        let zoningData = null;
        if (parcelData.geometry) {
          try {
            const { getZoningForParcel } = await import('@/lib/arcgis-client');
            zoningData = await getZoningForParcel(parcelData.geometry);
          } catch (err) {
            console.error('Error getting zoning:', err);
          }
        }

        // Build a minimal analysis object
        analysis = {
          parcel: {
            apn: parcelData.apn,
            ain: '',
            address: parcelData.address,
            situsFullAddress: parcelData.address,
            city: parcelData.city,
            zip: parcelData.zip,
            useCode: parcelData.useCode,
            useDescription: parcelData.useDescription,
            yearBuilt: parcelData.yearBuilt,
            units: parcelData.units,
            sqft: parcelData.sqft,
            lotSizeSqft: parcelData.lotSizeSqft,
            lotWidth: parcelData.lotWidth,
            lotDepth: parcelData.lotDepth,
            geometry: parcelData.geometry,
            latitude: undefined,
            longitude: undefined,
          },
          zoning: zoningData || { zoneCode: '', zoneDescription: '', majorCategory: '' },
          historic: { isHistoric: false },
          coastal: { inCoastalZone: false },
          flood: { inFloodZone: false },
          transit: { withinHalfMile: false },
          parking: { unbundledParkingRequired: false },
          setbacks: {},
          hazards: {
            faultZone: false,
            liquefactionZone: false,
            landslideZone: false,
            seismicHazardZone: false,
          },
          overlays: [],
          environmental: {
            inWetlands: false,
            inConservationArea: false,
            fireHazardZone: null,
            nearHazardousWaste: false,
            inEarthquakeFaultZone: false,
          },
          street: {
            rowWidth: null,
            streetName: null,
            streetType: null,
            dataSource: 'estimated' as const,
          },
        };
      }

      console.log('Parcel analysis:', analysis);

      // Transform the parcel geometry from State Plane to WGS84
      let transformedGeometry: [number, number][][] = [];

      if (analysis.parcel.geometry) {
        try {
          console.log('Raw geometry from service:', analysis.parcel.geometry);
          console.log('First ring first point:', analysis.parcel.geometry.rings?.[0]?.[0]);
          transformedGeometry = transformParcelGeometry(analysis.parcel.geometry);
          console.log('Transformed geometry:', transformedGeometry);
          console.log('First transformed point:', transformedGeometry[0]?.[0]);

          // Calculate and add centroid to parcel data
          const [centerLat, centerLng] = getPolygonCenter(transformedGeometry);
          analysis.parcel.latitude = centerLat;
          analysis.parcel.longitude = centerLng;
        } catch (error) {
          console.error('Error transforming geometry:', error);
        }
      }

      setSelectedParcel({
        geometry: transformedGeometry,
        apn: analysis.parcel.apn,
        address: analysis.parcel.address,
        units: analysis.parcel.units,
        sqft: analysis.parcel.sqft,
        yearBuilt: analysis.parcel.yearBuilt,
      });

      // Display parcel info with zoning
      const infoText = `APN: ${analysis.parcel.apn} • ${analysis.parcel.address}${analysis.parcel.lotSizeSqft ? ` • ${analysis.parcel.lotSizeSqft.toLocaleString()} sq ft` : ''}${analysis.zoning.zoneCode ? ` • ${analysis.zoning.zoneCode}` : ''}`;
      setOverlayInfo(infoText);

      // Callback to parent component with full analysis
      if (onParcelSelected) {
        onParcelSelected(analysis);
      }

    } catch (err) {
      console.error('Error querying parcel:', err);
      setError(err instanceof Error ? err.message : 'Failed to query parcel data');
      setSelectedParcel(null);
    } finally {
      setIsLoading(false);
      onLoadingChange?.(false);
    }
  };

  return (
    <div className="relative">
      {/* Map Container */}
      <div style={{ height }} className="rounded-lg overflow-hidden border border-gray-200">
        <MapContainer
          center={SANTA_MONICA_BOUNDS.center}
          zoom={SANTA_MONICA_BOUNDS.zoom}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onClick={handleMapClick} />

          {/* Instant click indicator - shows immediately on click */}
          {clickLocation && !selectedParcel && (
            <CircleMarker
              center={clickLocation}
              radius={8}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.6,
                weight: 2
              }}
            />
          )}

          {/* Display selected parcel polygon */}
          {selectedParcel && selectedParcel.geometry && selectedParcel.geometry.length > 0 && (
            <Polygon
              positions={selectedParcel.geometry}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.2,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-sm min-w-[200px]">
                  <div className="font-bold text-gray-900 mb-1">{selectedParcel.apn}</div>
                  <div className="text-gray-700 mb-2">{selectedParcel.address}</div>

                  {(selectedParcel.units !== undefined || selectedParcel.sqft !== undefined || selectedParcel.yearBuilt) && (
                    <div className="border-t border-gray-200 pt-2 mt-2">
                      <div className="text-xs font-semibold text-gray-600 mb-1">Current Use</div>
                      {selectedParcel.units !== undefined && selectedParcel.units > 0 && (
                        <div className="text-gray-700">{selectedParcel.units} {selectedParcel.units === 1 ? 'unit' : 'units'}</div>
                      )}
                      {selectedParcel.sqft !== undefined && selectedParcel.sqft > 0 && (
                        <div className="text-gray-700">{selectedParcel.sqft.toLocaleString()} sq ft</div>
                      )}
                      {selectedParcel.yearBuilt && (
                        <div className="text-gray-700">Built {selectedParcel.yearBuilt}</div>
                      )}
                    </div>
                  )}
                </div>
              </Popup>
            </Polygon>
          )}
        </MapContainer>
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
          <span className="text-sm font-medium text-gray-700">Querying GIS data...</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="absolute top-4 right-4 bg-red-50 border-l-4 border-red-500 rounded-lg p-3 flex items-start gap-2 max-w-sm">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-red-900">Error</h4>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Overlay Info */}
      {overlayInfo && !isLoading && (
        <div className="absolute bottom-4 left-4 right-4 bg-white rounded-lg shadow-lg p-3 flex items-start gap-2">
          <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-gray-700">{overlayInfo}</p>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-3 flex items-start gap-2 text-sm text-gray-600">
        <MapPin className="w-4 h-4 mt-0.5 text-blue-600" />
        <p>Click anywhere on the map to select a parcel and view its zoning, overlays, and development potential</p>
      </div>
    </div>
  );
}
