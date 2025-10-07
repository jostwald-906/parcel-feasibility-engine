'use client';

import { useState } from 'react';
import { Building2, AlertCircle, Map, Layers } from 'lucide-react';
import ParcelForm from '@/components/ParcelForm';
import ResultsDashboard from '@/components/ResultsDashboard';
import ParcelMapWrapper from '@/components/ParcelMapWrapper';
import ParcelInfoPanel from '@/components/ParcelInfoPanel';
import MultiParcelSelector from '@/components/MultiParcelSelector';
import ParcelAPI from '@/lib/api';
import { combineParcels } from '@/lib/parcel-combiner';
import type { AnalysisRequest, AnalysisResponse } from '@/lib/types';
import type { ParcelAnalysis } from '@/lib/arcgis-client';

export default function Home() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMap, setShowMap] = useState(true);
  const [selectedParcelData, setSelectedParcelData] = useState<ParcelAnalysis | null>(null);
  const [multiSelectMode, setMultiSelectMode] = useState(false);
  const [mapLoading, setMapLoading] = useState(false);

  const handleAnalyze = async (request: AnalysisRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await ParcelAPI.analyzeParcel(request);
      setAnalysisResult(result);
    } catch (err) {
      console.error('Analysis error:', err);
      const errorMessage =
        (err && typeof err === 'object' && 'response' in err && err.response &&
         typeof err.response === 'object' && 'data' in err.response &&
         err.response.data && typeof err.response.data === 'object' &&
         'detail' in err.response.data) ? String(err.response.data.detail) :
        (err instanceof Error ? err.message : null) ||
        'Failed to analyze parcel. Please check your inputs and try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleParcelSelected = (analysis: ParcelAnalysis) => {
    console.log('Parcel selected from map:', analysis);

    // Store the parcel data (but keep map visible to show boundary)
    setSelectedParcelData(analysis);
  };

  const handleMultiParcelsConfirmed = (parcels: ParcelAnalysis[]) => {
    console.log('Multiple parcels selected:', parcels);

    // Combine parcels into single analysis
    const combinedAnalysis = combineParcels(parcels);
    setSelectedParcelData(combinedAnalysis);
    setMultiSelectMode(false);
    setShowMap(false);
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <Building2 className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Santa Monica Parcel Feasibility Engine
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                AI-powered development analysis with California housing law integration
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900 mb-1">Analysis Error</h3>
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {!analysisResult ? (
          <div className="max-w-7xl mx-auto">
            {/* Map or Form Toggle */}
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => { setShowMap(true); setMultiSelectMode(false); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  showMap && !multiSelectMode
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                <Map className="w-5 h-5" />
                Select from Map
              </button>
              <button
                onClick={() => { setShowMap(true); setMultiSelectMode(true); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  showMap && multiSelectMode
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                <Layers className="w-5 h-5" />
                Multiple Parcels
              </button>
              <button
                onClick={() => { setShowMap(false); setMultiSelectMode(false); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  !showMap
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                <Building2 className="w-5 h-5" />
                Enter Manually
              </button>
            </div>

            {showMap ? (
              multiSelectMode ? (
                <MultiParcelSelector onParcelsConfirmed={handleMultiParcelsConfirmed} />
              ) : (
                <>
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">
                      Select Parcel from Map
                    </h2>
                    <p className="text-gray-600 text-sm">
                      Click on any parcel in Santa Monica to view its zoning, overlays, and development potential.
                      The system will automatically query GIS data and populate the analysis form.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Map - Takes 2/3 width on large screens */}
                  <div className="lg:col-span-2">
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <ParcelMapWrapper
                        onParcelSelected={handleParcelSelected}
                        onLoadingChange={setMapLoading}
                        height="600px"
                      />
                    </div>
                    {selectedParcelData && (
                      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-blue-900">
                              Parcel Selected: {selectedParcelData.parcel.apn}
                            </p>
                            <p className="text-sm text-blue-700 mt-1">
                              {selectedParcelData.parcel.address}
                            </p>
                          </div>
                          <button
                            onClick={() => setShowMap(false)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                          >
                            Continue to Form
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Info Panel - Takes 1/3 width on large screens */}
                  <div className="lg:col-span-1">
                    <ParcelInfoPanel analysis={selectedParcelData} isLoading={mapLoading} />
                  </div>
                </div>
                </>
              )
            ) : (
              <>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Analyze Your Parcel
                  </h2>
                  <p className="text-gray-600 text-sm">
                    Enter your parcel details below to receive a comprehensive feasibility analysis
                    including base zoning, SB 9, SB 35, AB 2011, and Density Bonus scenarios.
                  </p>
                </div>
                <ParcelForm
                  onSubmit={handleAnalyze}
                  isLoading={isLoading}
                  initialData={selectedParcelData}
                />
              </>
            )}
          </div>
        ) : (
          <ResultsDashboard analysis={analysisResult} onReset={handleReset} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-600">
            <p>
              © 2025 Santa Monica Parcel Feasibility Engine. Built with FastAPI + Next.js.
            </p>
            <div className="flex gap-6">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700"
              >
                API Documentation
              </a>
              <a
                href="http://localhost:8000/health"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700"
              >
                API Health
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
