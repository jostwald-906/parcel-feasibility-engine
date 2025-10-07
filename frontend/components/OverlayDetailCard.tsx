'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Maximize2, ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface OverlayDetail {
  name: string;
  description: string;
  impact: {
    far_multiplier?: number;
    height_bonus_ft?: number;
    density_bonus_pct?: number;
    impact_type: 'opportunity' | 'neutral' | 'constraint';
  };
  requirements?: string[];
  eligibility?: string[];
  municipal_code_section?: string;
  notes?: string[];
}

interface OverlayDetailCardProps {
  overlay: OverlayDetail;
}

export default function OverlayDetailCard({ overlay }: OverlayDetailCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine color scheme based on impact type
  const colorScheme = {
    opportunity: {
      border: 'border-green-500',
      bg: 'bg-green-50',
      text: 'text-green-900',
      subtext: 'text-green-700',
      icon: 'text-green-600',
      iconBg: 'bg-green-100',
    },
    neutral: {
      border: 'border-yellow-500',
      bg: 'bg-yellow-50',
      text: 'text-yellow-900',
      subtext: 'text-yellow-700',
      icon: 'text-yellow-600',
      iconBg: 'bg-yellow-100',
    },
    constraint: {
      border: 'border-red-500',
      bg: 'bg-red-50',
      text: 'text-red-900',
      subtext: 'text-red-700',
      icon: 'text-red-600',
      iconBg: 'bg-red-100',
    },
  }[overlay.impact.impact_type];

  // Format impact summary
  const impactSummary: string[] = [];
  if (overlay.impact.far_multiplier) {
    const sign = overlay.impact.far_multiplier > 1 ? '+' : '';
    impactSummary.push(`${sign}${((overlay.impact.far_multiplier - 1) * 100).toFixed(0)}% FAR`);
  }
  if (overlay.impact.height_bonus_ft) {
    impactSummary.push(`+${overlay.impact.height_bonus_ft} ft height`);
  }
  if (overlay.impact.density_bonus_pct) {
    impactSummary.push(`+${overlay.impact.density_bonus_pct}% density`);
  }

  // Get icon based on impact type
  const ImpactIcon = overlay.impact.impact_type === 'opportunity'
    ? TrendingUp
    : overlay.impact.impact_type === 'constraint'
    ? TrendingDown
    : Minus;

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 ${colorScheme.border} border-r border-t border-b border-gray-200 overflow-hidden`}>
      {/* Header - Always Visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full px-6 py-4 ${colorScheme.bg} hover:opacity-90 transition-opacity`}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className={`p-2 rounded-lg ${colorScheme.iconBg} flex-shrink-0`}>
              <Maximize2 className={`w-5 h-5 ${colorScheme.icon}`} />
            </div>
            <div className="flex-1 min-w-0 text-left">
              <h3 className={`text-base font-semibold ${colorScheme.text} mb-1`}>
                {overlay.name}
              </h3>
              {impactSummary.length > 0 && (
                <div className="flex items-center gap-2 mb-1">
                  <ImpactIcon className={`w-4 h-4 ${colorScheme.icon}`} />
                  <p className={`text-sm font-medium ${colorScheme.subtext}`}>
                    {impactSummary.join(', ')}
                  </p>
                </div>
              )}
              <p className={`text-sm ${colorScheme.subtext} line-clamp-2`}>
                {overlay.description}
              </p>
            </div>
          </div>
          <div className={`flex-shrink-0 ${colorScheme.icon}`}>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </div>
        </div>
      </button>

      {/* Expandable Body */}
      {isExpanded && (
        <div className="px-6 py-4 space-y-4 bg-white border-t border-gray-200">
          {/* Full Description */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">
              Description
            </h4>
            <p className="text-sm text-gray-900">{overlay.description}</p>
          </div>

          {/* Requirements */}
          {overlay.requirements && overlay.requirements.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">
                Requirements
              </h4>
              <ul className="space-y-1">
                {overlay.requirements.map((req, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className={`${colorScheme.icon} mt-1 flex-shrink-0`}>•</span>
                    <span>{req}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Eligibility */}
          {overlay.eligibility && overlay.eligibility.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">
                Eligibility Criteria
              </h4>
              <ul className="space-y-1">
                {overlay.eligibility.map((criterion, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className={`${colorScheme.icon} mt-1 flex-shrink-0`}>•</span>
                    <span>{criterion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Impact Details */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">
              Development Impact
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {overlay.impact.far_multiplier && (
                <div className={`p-3 rounded-lg ${colorScheme.bg}`}>
                  <p className="text-xs text-gray-600 mb-1">FAR Multiplier</p>
                  <p className={`text-lg font-bold ${colorScheme.text}`}>
                    {overlay.impact.far_multiplier.toFixed(2)}x
                  </p>
                </div>
              )}
              {overlay.impact.height_bonus_ft && (
                <div className={`p-3 rounded-lg ${colorScheme.bg}`}>
                  <p className="text-xs text-gray-600 mb-1">Height Bonus</p>
                  <p className={`text-lg font-bold ${colorScheme.text}`}>
                    +{overlay.impact.height_bonus_ft} ft
                  </p>
                </div>
              )}
              {overlay.impact.density_bonus_pct && (
                <div className={`p-3 rounded-lg ${colorScheme.bg}`}>
                  <p className="text-xs text-gray-600 mb-1">Density Bonus</p>
                  <p className={`text-lg font-bold ${colorScheme.text}`}>
                    +{overlay.impact.density_bonus_pct}%
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Notes */}
          {overlay.notes && overlay.notes.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">
                Additional Notes
              </h4>
              <ul className="space-y-1">
                {overlay.notes.map((note, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-gray-400 mt-1 flex-shrink-0">•</span>
                    <span>{note}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Footer - Municipal Code Link */}
          {overlay.municipal_code_section && (
            <div className="pt-3 border-t border-gray-200">
              <a
                href={`https://library.municode.com/ca/santa_monica/codes/code_of_ordinances?nodeId=${overlay.municipal_code_section}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                View Municipal Code {overlay.municipal_code_section}
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
