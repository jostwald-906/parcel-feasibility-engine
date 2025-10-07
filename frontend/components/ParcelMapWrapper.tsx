'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import type { ParcelAnalysis } from '@/lib/arcgis-client';

// Dynamically import the map component to avoid SSR issues
const ParcelMap = dynamic(() => import('./ParcelMap'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-[500px] bg-gray-100 rounded-lg border border-gray-200">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-sm text-gray-600">Loading map...</p>
      </div>
    </div>
  ),
});

interface ParcelMapWrapperProps {
  onParcelSelected?: (data: ParcelAnalysis) => void;
  onLoadingChange?: (isLoading: boolean) => void;
  height?: string;
}

export default function ParcelMapWrapper({ onParcelSelected, onLoadingChange, height }: ParcelMapWrapperProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return (
      <div className="flex items-center justify-center h-[500px] bg-gray-100 rounded-lg border border-gray-200">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading map...</p>
        </div>
      </div>
    );
  }

  return <ParcelMap onParcelSelected={onParcelSelected} onLoadingChange={onLoadingChange} height={height} />;
}
