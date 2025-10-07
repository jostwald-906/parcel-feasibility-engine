'use client';

import { useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import type { AnalysisResponse } from '@/lib/types';
import ParcelAPI from '@/lib/api';
import { downloadPDF, generatePDFFilename } from '@/lib/download-utils';

/**
 * ExportButton Component
 *
 * Handles PDF export functionality for feasibility analysis reports.
 *
 * Features:
 * - Loading state with spinner
 * - Automatic download trigger
 * - Error handling with toast-style notifications
 * - Disabled state support
 * - Matches existing button patterns from codebase
 */

interface ExportButtonProps {
  analysis: AnalysisResponse;
  disabled?: boolean;
}

export default function ExportButton({ analysis, disabled = false }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    // Reset error state
    setError(null);
    setIsExporting(true);

    try {
      // Call API to generate PDF
      const blob = await ParcelAPI.exportFeasibilityPDF(analysis);

      // Generate filename based on APN
      const filename = generatePDFFilename(analysis.parcel_apn);

      // Trigger download
      downloadPDF(blob, filename);

      // Optional: Show success message (auto-dismiss after 3 seconds)
      // For now, success is indicated by the download itself
    } catch (err) {
      console.error('PDF export error:', err);

      // Extract error message
      const errorMessage =
        (err &&
          typeof err === 'object' &&
          'response' in err &&
          err.response &&
          typeof err.response === 'object' &&
          'data' in err.response &&
          err.response.data &&
          typeof err.response.data === 'object' &&
          'detail' in err.response.data)
          ? String(err.response.data.detail)
          : (err instanceof Error ? err.message : null) ||
            'Failed to export PDF. Please try again.';

      setError(errorMessage);

      // Auto-dismiss error after 5 seconds
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="relative">
      {/* Export Button */}
      <button
        onClick={handleExport}
        disabled={disabled || isExporting}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
        aria-label="Export to PDF"
      >
        {isExporting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Generating PDF...</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>Export PDF</span>
          </>
        )}
      </button>

      {/* Error Toast */}
      {error && (
        <div className="absolute top-full mt-2 right-0 z-50 w-80 bg-red-50 border-l-4 border-red-500 rounded-lg p-4 shadow-lg animate-slide-in">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <h4 className="font-semibold text-red-900 text-sm">Export Failed</h4>
              <p className="text-red-800 text-xs mt-1">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800 transition-colors"
              aria-label="Dismiss error"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
