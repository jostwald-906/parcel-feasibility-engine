'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';

interface SourceNotesPanelProps {
  notes: Record<string, any>;
}

function formatKey(key: string): string {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatValue(value: any): string {
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  if (typeof value === 'number') {
    return value.toLocaleString();
  }
  return String(value);
}

export default function SourceNotesPanel({ notes }: SourceNotesPanelProps) {
  const [expanded, setExpanded] = useState(false);

  const noteEntries = Object.entries(notes);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-blue-600" />
          <div className="text-left">
            <div className="text-base font-semibold text-gray-900">
              Data Sources & Assumptions
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {noteEntries.length} data points used in this analysis
            </div>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>

      {expanded && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="space-y-4">
            {noteEntries.map(([key, value], idx) => (
              <div
                key={idx}
                className="flex flex-col sm:flex-row sm:items-start gap-2 p-3 bg-gray-50 rounded-lg"
              >
                <div className="sm:min-w-[240px]">
                  <span className="text-sm font-semibold text-gray-900">
                    {formatKey(key)}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="text-sm text-gray-700 font-mono bg-white px-3 py-2 rounded border border-gray-200 overflow-x-auto">
                    <pre className="whitespace-pre-wrap break-words">
                      {formatValue(value)}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-600">
              <strong className="text-gray-900">Note:</strong> All cost and revenue
              assumptions are based on RS Means data, HCD income limits, local market
              comparables, and industry-standard financial modeling practices. These
              estimates should be verified with detailed feasibility studies and local
              market research before making investment decisions.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
