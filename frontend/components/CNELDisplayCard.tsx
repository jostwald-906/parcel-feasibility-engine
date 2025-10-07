'use client';

import { useState } from 'react';
import { Volume2, ChevronDown, ChevronUp, ExternalLink, CheckCircle, AlertTriangle, XCircle, Shield } from 'lucide-react';
import type { CNELAnalysis } from '@/lib/types';

interface CNELDisplayCardProps {
  cnel: CNELAnalysis;
}

export default function CNELDisplayCard({ cnel }: CNELDisplayCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine color scheme based on CNEL category
  const getColorScheme = () => {
    if (cnel.cnel_db < 60) {
      return {
        border: 'border-green-500',
        bg: 'bg-green-50',
        text: 'text-green-900',
        subtext: 'text-green-700',
        icon: 'text-green-600',
        iconBg: 'bg-green-100',
        badge: 'bg-green-100 text-green-800',
      };
    } else if (cnel.cnel_db < 70) {
      return {
        border: 'border-yellow-500',
        bg: 'bg-yellow-50',
        text: 'text-yellow-900',
        subtext: 'text-yellow-700',
        icon: 'text-yellow-600',
        iconBg: 'bg-yellow-100',
        badge: 'bg-yellow-100 text-yellow-800',
      };
    } else if (cnel.cnel_db < 75) {
      return {
        border: 'border-orange-500',
        bg: 'bg-orange-50',
        text: 'text-orange-900',
        subtext: 'text-orange-700',
        icon: 'text-orange-600',
        iconBg: 'bg-orange-100',
        badge: 'bg-orange-100 text-orange-800',
      };
    } else {
      return {
        border: 'border-red-500',
        bg: 'bg-red-50',
        text: 'text-red-900',
        subtext: 'text-red-700',
        icon: 'text-red-600',
        iconBg: 'bg-red-100',
        badge: 'bg-red-100 text-red-800',
      };
    }
  };

  const colorScheme = getColorScheme();

  // Get status icon
  const StatusIcon = cnel.suitable_for_residential
    ? CheckCircle
    : cnel.requires_study
    ? AlertTriangle
    : XCircle;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className={`px-6 py-4 ${colorScheme.bg} border-b border-gray-200`}>
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${colorScheme.iconBg} flex-shrink-0`}>
            <Volume2 className={`w-6 h-6 ${colorScheme.icon}`} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className={`text-lg font-semibold ${colorScheme.text} mb-1`}>
              Noise Analysis (CNEL)
            </h3>
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-baseline gap-2">
                <span className={`text-3xl font-bold ${colorScheme.text}`}>
                  {cnel.cnel_db}
                </span>
                <span className={`text-lg ${colorScheme.subtext}`}>dB</span>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${colorScheme.badge}`}>
                {cnel.category_label}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Status */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-start gap-3">
          <StatusIcon
            className={`w-5 h-5 ${
              cnel.suitable_for_residential
                ? 'text-green-600'
                : cnel.requires_study
                ? 'text-yellow-600'
                : 'text-red-600'
            } flex-shrink-0 mt-0.5`}
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900">
              {cnel.suitable_for_residential
                ? 'Suitable for residential development'
                : cnel.requires_study
                ? 'May require noise study and mitigation'
                : 'Not recommended for residential without extensive mitigation'}
            </p>
            {cnel.window_requirement && (
              <p className="text-sm text-gray-700 mt-1">
                <span className="font-semibold">Window Requirement:</span> {cnel.window_requirement}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Expandable Details */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
      >
        <span className="text-sm font-medium text-gray-700">
          {isExpanded ? 'Hide' : 'Show'} Mitigation Measures & Details
        </span>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>

      {isExpanded && (
        <div className="px-6 py-4 space-y-4 bg-white">
          {/* Mitigation Measures */}
          {cnel.mitigation_measures && cnel.mitigation_measures.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-600" />
                Required Mitigation Measures
              </h4>
              <ul className="space-y-2">
                {cnel.mitigation_measures.map((measure, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-gray-700 pl-4 border-l-2 border-blue-200 py-1"
                  >
                    {measure}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Santa Monica Compliance */}
          {cnel.santa_monica_compliance && (
            <div className={`p-4 rounded-lg ${
              cnel.santa_monica_compliance.compliant
                ? 'bg-green-50 border border-green-200'
                : 'bg-amber-50 border border-amber-200'
            }`}>
              <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                {cnel.santa_monica_compliance.compliant ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                )}
                <span className={
                  cnel.santa_monica_compliance.compliant
                    ? 'text-green-900'
                    : 'text-amber-900'
                }>
                  Santa Monica Compliance
                </span>
              </h4>
              <p className={`text-sm mb-2 ${
                cnel.santa_monica_compliance.compliant
                  ? 'text-green-800'
                  : 'text-amber-800'
              }`}>
                {cnel.santa_monica_compliance.compliant
                  ? 'Compliant with Santa Monica noise standards'
                  : cnel.santa_monica_compliance.requires_variance
                  ? 'Variance may be required for residential development'
                  : 'Additional review required'}
              </p>
              {cnel.santa_monica_compliance.notes && cnel.santa_monica_compliance.notes.length > 0 && (
                <ul className="space-y-1 mt-2">
                  {cnel.santa_monica_compliance.notes.map((note, idx) => (
                    <li
                      key={idx}
                      className={`text-xs flex items-start gap-2 ${
                        cnel.santa_monica_compliance?.compliant
                          ? 'text-green-700'
                          : 'text-amber-700'
                      }`}
                    >
                      <span className="mt-1">•</span>
                      <span>{note}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Additional Notes */}
          {cnel.notes && cnel.notes.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                Additional Information
              </h4>
              <ul className="space-y-1">
                {cnel.notes.map((note, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-gray-400 mt-1 flex-shrink-0">•</span>
                    <span>{note}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* CNEL Scale Reference */}
          <div className="pt-4 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">
              CNEL Scale Reference
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2 p-2 bg-green-50 rounded border-l-2 border-green-500">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-gray-700">&lt;60 dB - Normally Acceptable</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-yellow-50 rounded border-l-2 border-yellow-500">
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <span className="text-gray-700">60-70 dB - Conditionally Acceptable</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-orange-50 rounded border-l-2 border-orange-500">
                <div className="w-3 h-3 rounded-full bg-orange-500" />
                <span className="text-gray-700">70-75 dB - Normally Unacceptable</span>
              </div>
              <div className="flex items-center gap-2 p-2 bg-red-50 rounded border-l-2 border-red-500">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <span className="text-gray-700">&gt;75 dB - Clearly Unacceptable</span>
              </div>
            </div>
          </div>

          {/* Link to Standards */}
          <div className="pt-3 border-t border-gray-200">
            <a
              href="https://codes.iccsafe.org/content/CBC2022P3/chapter-12-interior-environment#CBC2022P3_Ch12_Sec1207"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              View California Title 24 Standards
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
