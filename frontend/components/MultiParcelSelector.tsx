'use client';

import { useState } from 'react';
import { Layers, Plus, Trash2, Combine } from 'lucide-react';
import ParcelMapWrapper from './ParcelMapWrapper';
import type { ParcelAnalysis } from '@/lib/arcgis-client';

interface MultiParcelSelectorProps {
  onParcelsConfirmed: (parcels: ParcelAnalysis[]) => void;
}

export default function MultiParcelSelector({ onParcelsConfirmed }: MultiParcelSelectorProps) {
  const [selectedParcels, setSelectedParcels] = useState<ParcelAnalysis[]>([]);
  const [currentParcel, setCurrentParcel] = useState<ParcelAnalysis | null>(null);

  const handleParcelSelected = (analysis: ParcelAnalysis) => {
    setCurrentParcel(analysis);
  };

  const handleAddParcel = () => {
    if (!currentParcel) return;

    // Check if parcel already added
    const exists = selectedParcels.some(p => p.parcel.apn === currentParcel.parcel.apn);
    if (exists) {
      alert('This parcel has already been added');
      return;
    }

    setSelectedParcels([...selectedParcels, currentParcel]);
    setCurrentParcel(null);
  };

  const handleRemoveParcel = (apn: string) => {
    setSelectedParcels(selectedParcels.filter(p => p.parcel.apn !== apn));
  };

  const handleCombineAndContinue = () => {
    if (selectedParcels.length === 0) {
      alert('Please select at least one parcel');
      return;
    }
    onParcelsConfirmed(selectedParcels);
  };

  const totalLotSize = selectedParcels.reduce((sum, p) => sum + (p.parcel.lotSizeSqft || 0), 0);

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Layers className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-blue-900">Multi-Parcel Assembly</h3>
            <p className="text-sm text-blue-700 mt-1">
              Click on adjacent parcels you own to combine them into a single development site.
              This is useful for assemblage projects or lot consolidation analysis.
            </p>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <ParcelMapWrapper onParcelSelected={handleParcelSelected} height="500px" />
      </div>

      {/* Current Selection */}
      {currentParcel && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-900">
                Current Parcel: {currentParcel.parcel.apn}
              </p>
              <p className="text-sm text-green-700 mt-1">
                {currentParcel.parcel.address} • {currentParcel.parcel.lotSizeSqft?.toLocaleString()} sq ft
              </p>
            </div>
            <button
              onClick={handleAddParcel}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              <Plus className="w-4 h-4" />
              Add to Assembly
            </button>
          </div>
        </div>
      )}

      {/* Selected Parcels List */}
      {selectedParcels.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Selected Parcels ({selectedParcels.length})</h3>
              <p className="text-sm text-gray-600 mt-1">
                Combined Lot Size: {totalLotSize.toLocaleString()} sq ft
              </p>
            </div>
            <button
              onClick={handleCombineAndContinue}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              <Combine className="w-4 h-4" />
              Combine & Continue
            </button>
          </div>

          <div className="space-y-2">
            {selectedParcels.map((parcel) => (
              <div
                key={parcel.parcel.apn}
                className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{parcel.parcel.apn}</p>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {parcel.parcel.address} • {parcel.parcel.lotSizeSqft?.toLocaleString()} sq ft • {parcel.zoning.zoneCode}
                  </p>
                </div>
                <button
                  onClick={() => handleRemoveParcel(parcel.parcel.apn)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                  aria-label="Remove parcel"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
