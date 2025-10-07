'use client';

import { useState } from 'react';
import {
  Building,
  Home,
  Ruler,
  Car,
  TrendingUp,
  Download,
  ArrowUpDown,
  Eye,
  EyeOff,
  Check,
  AlertCircle,
} from 'lucide-react';
import type { DevelopmentScenario, Parcel } from '@/lib/types';
import { formatNumber } from '@/lib/utils';

/**
 * ScenarioComparisonMatrix Component
 *
 * Interactive comparison table that shows all development scenarios with key metrics
 * side-by-side for easy decision-making.
 *
 * Features:
 * - Scenarios as columns, metrics as rows
 * - Highlight best value in each row
 * - Color-code ministerial (green) vs. discretionary (yellow) approval types
 * - Sortable columns (click header to reorder)
 * - Show/hide metrics (user preference checkboxes)
 * - Mobile responsive (stack vertically on small screens)
 * - Export to CSV functionality
 * - "Recommended" badge on best overall scenario
 */

interface ScenarioComparisonMatrixProps {
  scenarios: DevelopmentScenario[];
  parcel: Parcel;
  onScenarioSelect?: (scenario: DevelopmentScenario) => void;
  recommendedScenario?: string;
}

type MetricKey =
  | 'legal_basis'
  | 'max_units'
  | 'max_building_sqft'
  | 'max_height_ft'
  | 'max_stories'
  | 'parking_spaces_required'
  | 'affordable_units_required'
  | 'lot_coverage_pct'
  | 'approval_type';

interface MetricConfig {
  key: MetricKey;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  format: (scenario: DevelopmentScenario) => string;
  highlightBest?: (scenarios: DevelopmentScenario[]) => number; // Returns index of best scenario
  description?: string;
}

export default function ScenarioComparisonMatrix({
  scenarios,
  parcel,
  onScenarioSelect,
  recommendedScenario,
}: ScenarioComparisonMatrixProps) {
  const [sortedScenarios, setSortedScenarios] = useState<DevelopmentScenario[]>(scenarios);
  const [visibleMetrics, setVisibleMetrics] = useState<Set<MetricKey>>(
    new Set([
      'legal_basis',
      'max_units',
      'max_building_sqft',
      'max_height_ft',
      'max_stories',
      'parking_spaces_required',
      'affordable_units_required',
      'lot_coverage_pct',
      'approval_type',
    ])
  );
  const [showMetricSelector, setShowMetricSelector] = useState(false);

  // Define metrics configuration
  const metrics: MetricConfig[] = [
    {
      key: 'legal_basis',
      label: 'Legal Basis',
      format: (s) => s.legal_basis,
      description: 'State law or local zoning basis for development',
    },
    {
      key: 'max_units',
      label: 'Max Units',
      icon: Home,
      format: (s) => formatNumber(s.max_units),
      highlightBest: (scenarios) => {
        const maxUnits = Math.max(...scenarios.map((s) => s.max_units));
        return scenarios.findIndex((s) => s.max_units === maxUnits);
      },
      description: 'Maximum number of residential units allowed',
    },
    {
      key: 'max_building_sqft',
      label: 'Building Square Footage',
      icon: Building,
      format: (s) => `${formatNumber(s.max_building_sqft)} sq ft`,
      highlightBest: (scenarios) => {
        const maxSqft = Math.max(...scenarios.map((s) => s.max_building_sqft));
        return scenarios.findIndex((s) => s.max_building_sqft === maxSqft);
      },
      description: 'Maximum building square footage',
    },
    {
      key: 'max_height_ft',
      label: 'Height (ft)',
      icon: Ruler,
      format: (s) => `${s.max_height_ft} ft`,
      highlightBest: (scenarios) => {
        const maxHeight = Math.max(...scenarios.map((s) => s.max_height_ft));
        return scenarios.findIndex((s) => s.max_height_ft === maxHeight);
      },
      description: 'Maximum building height in feet',
    },
    {
      key: 'max_stories',
      label: 'Stories',
      format: (s) => s.max_stories.toString(),
      highlightBest: (scenarios) => {
        const maxStories = Math.max(...scenarios.map((s) => s.max_stories));
        return scenarios.findIndex((s) => s.max_stories === maxStories);
      },
      description: 'Maximum number of stories',
    },
    {
      key: 'parking_spaces_required',
      label: 'Parking Spaces Required',
      icon: Car,
      format: (s) => `${formatNumber(s.parking_spaces_required)} spaces`,
      highlightBest: (scenarios) => {
        // Lower is better for parking (less requirement)
        const minParking = Math.min(...scenarios.map((s) => s.parking_spaces_required));
        return scenarios.findIndex((s) => s.parking_spaces_required === minParking);
      },
      description: 'Minimum parking spaces required',
    },
    {
      key: 'affordable_units_required',
      label: 'Affordable Units Required',
      format: (s) => {
        const count = formatNumber(s.affordable_units_required);
        const pct =
          s.max_units > 0
            ? ` (${((s.affordable_units_required / s.max_units) * 100).toFixed(0)}%)`
            : '';
        return `${count}${pct}`;
      },
      description: 'Number of affordable units required',
    },
    {
      key: 'lot_coverage_pct',
      label: 'Lot Coverage (%)',
      format: (s) => `${Math.round(s.lot_coverage_pct)}%`,
      description: 'Percentage of lot covered by building',
    },
    {
      key: 'approval_type',
      label: 'Approval Type',
      format: (s) => {
        // Infer approval type from legal basis and notes
        const ministerialKeywords = ['ministerial', 'by-right', 'SB 9', 'SB 35', 'AB 2011'];
        const isMinisterial = ministerialKeywords.some(
          (keyword) =>
            s.legal_basis.toLowerCase().includes(keyword.toLowerCase()) ||
            s.notes.some((note) => note.toLowerCase().includes(keyword.toLowerCase()))
        );
        return isMinisterial ? 'Ministerial' : 'Discretionary';
      },
      description: 'Type of approval process required',
    },
  ];

  // Filter visible metrics
  const displayedMetrics = metrics.filter((m) => visibleMetrics.has(m.key));

  // Toggle metric visibility
  const toggleMetric = (key: MetricKey) => {
    setVisibleMetrics((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  // Sort scenarios by a specific metric
  const sortByMetric = (metricKey: MetricKey) => {
    const sorted = [...sortedScenarios].sort((a, b) => {
      if (metricKey === 'legal_basis' || metricKey === 'approval_type') {
        const aVal = metrics.find((m) => m.key === metricKey)?.format(a) || '';
        const bVal = metrics.find((m) => m.key === metricKey)?.format(b) || '';
        return aVal.localeCompare(bVal);
      }

      // Numeric sorting
      const getValue = (s: DevelopmentScenario) => {
        switch (metricKey) {
          case 'max_units':
            return s.max_units;
          case 'max_building_sqft':
            return s.max_building_sqft;
          case 'max_height_ft':
            return s.max_height_ft;
          case 'max_stories':
            return s.max_stories;
          case 'parking_spaces_required':
            return s.parking_spaces_required;
          case 'affordable_units_required':
            return s.affordable_units_required;
          case 'lot_coverage_pct':
            return s.lot_coverage_pct;
          default:
            return 0;
        }
      };

      return getValue(b) - getValue(a); // Descending by default
    });

    setSortedScenarios(sorted);
  };

  // Export to CSV
  const exportToCSV = () => {
    // Build CSV header
    const header = ['Metric', ...sortedScenarios.map((s) => s.scenario_name)].join(',');

    // Build CSV rows
    const rows = displayedMetrics.map((metric) => {
      const values = sortedScenarios.map((s) => {
        const value = metric.format(s);
        // Escape commas and quotes
        return value.includes(',') || value.includes('"') ? `"${value.replace(/"/g, '""')}"` : value;
      });
      return [metric.label, ...values].join(',');
    });

    // Combine header and rows
    const csv = [header, ...rows].join('\n');

    // Download CSV
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `scenario_comparison_${parcel.apn}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Determine approval type for badge styling
  const getApprovalType = (scenario: DevelopmentScenario): 'ministerial' | 'discretionary' => {
    const ministerialKeywords = ['ministerial', 'by-right', 'SB 9', 'SB 35', 'AB 2011'];
    const isMinisterial = ministerialKeywords.some(
      (keyword) =>
        scenario.legal_basis.toLowerCase().includes(keyword.toLowerCase()) ||
        scenario.notes.some((note) => note.toLowerCase().includes(keyword.toLowerCase()))
    );
    return isMinisterial ? 'ministerial' : 'discretionary';
  };

  if (scenarios.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Scenario Comparison Matrix</h3>
            <p className="text-sm text-gray-600 mt-1">
              Side-by-side comparison of {sortedScenarios.length} development{' '}
              {sortedScenarios.length === 1 ? 'scenario' : 'scenarios'}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowMetricSelector(!showMetricSelector)}
              className="px-3 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium flex items-center gap-2"
              aria-label="Toggle metric selector"
            >
              {showMetricSelector ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Metrics</span>
            </button>

            <button
              onClick={exportToCSV}
              className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2"
              aria-label="Export to CSV"
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Export CSV</span>
            </button>
          </div>
        </div>

        {/* Metric Selector */}
        {showMetricSelector && (
          <div className="mt-4 p-4 bg-white border border-gray-200 rounded-lg">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Show/Hide Metrics</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {metrics.map((metric) => (
                <label
                  key={metric.key}
                  className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={visibleMetrics.has(metric.key)}
                    onChange={() => toggleMetric(metric.key)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm text-gray-700">{metric.label}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Desktop Table View */}
      <div className="hidden lg:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                Metric
              </th>
              {sortedScenarios.map((scenario, idx) => {
                const approvalType = getApprovalType(scenario);
                const isRecommended = scenario.scenario_name === recommendedScenario;

                return (
                  <th
                    key={idx}
                    className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors ${
                      isRecommended ? 'bg-green-50' : ''
                    }`}
                    onClick={() => onScenarioSelect?.(scenario)}
                  >
                    <div className="flex flex-col gap-2">
                      <span className="text-gray-900 font-semibold">{scenario.scenario_name}</span>

                      {/* Badges */}
                      <div className="flex flex-wrap gap-1">
                        {isRecommended && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
                            <TrendingUp className="w-3 h-3" />
                            Recommended
                          </span>
                        )}
                        <span
                          className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded ${
                            approvalType === 'ministerial'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {approvalType === 'ministerial' ? 'Ministerial' : 'Discretionary'}
                        </span>
                      </div>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayedMetrics.map((metric) => {
              const bestIdx = metric.highlightBest?.(sortedScenarios);

              return (
                <tr key={metric.key} className="hover:bg-gray-50">
                  <td
                    className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white cursor-pointer hover:bg-blue-50 transition-colors"
                    onClick={() => sortByMetric(metric.key)}
                    title={`Click to sort by ${metric.label}`}
                  >
                    <div className="flex items-center gap-2">
                      {metric.icon && <metric.icon className="w-4 h-4 text-blue-600 flex-shrink-0" />}
                      <span>{metric.label}</span>
                      <ArrowUpDown className="w-3 h-3 text-gray-400" />
                    </div>
                    {metric.description && (
                      <p className="text-xs text-gray-500 mt-1 font-normal">{metric.description}</p>
                    )}
                  </td>
                  {sortedScenarios.map((scenario, scenarioIdx) => {
                    const isBest = bestIdx !== undefined && bestIdx === scenarioIdx;
                    const isRecommended = scenario.scenario_name === recommendedScenario;

                    return (
                      <td
                        key={scenarioIdx}
                        className={`px-6 py-4 text-sm ${
                          isBest
                            ? 'bg-green-50 text-green-900 font-semibold'
                            : isRecommended
                            ? 'text-gray-900 font-medium'
                            : 'text-gray-700'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {isBest && <Check className="w-4 h-4 text-green-600 flex-shrink-0" />}
                          <span>{metric.format(scenario)}</span>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="lg:hidden">
        <div className="p-4 space-y-4">
          {sortedScenarios.map((scenario, scenarioIdx) => {
            const approvalType = getApprovalType(scenario);
            const isRecommended = scenario.scenario_name === recommendedScenario;

            return (
              <div
                key={scenarioIdx}
                className={`border rounded-lg overflow-hidden ${
                  isRecommended ? 'border-green-500 ring-2 ring-green-200' : 'border-gray-200'
                }`}
                onClick={() => onScenarioSelect?.(scenario)}
              >
                {/* Card Header */}
                <div className={`px-4 py-3 ${isRecommended ? 'bg-green-50' : 'bg-gray-50'} border-b border-gray-200`}>
                  <h4 className="font-semibold text-gray-900 mb-2">{scenario.scenario_name}</h4>
                  <div className="flex flex-wrap gap-1">
                    {isRecommended && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
                        <TrendingUp className="w-3 h-3" />
                        Recommended
                      </span>
                    )}
                    <span
                      className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded ${
                        approvalType === 'ministerial'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {approvalType === 'ministerial' ? 'Ministerial' : 'Discretionary'}
                    </span>
                  </div>
                </div>

                {/* Card Metrics */}
                <div className="px-4 py-3 space-y-3">
                  {displayedMetrics.map((metric) => {
                    const bestIdx = metric.highlightBest?.(sortedScenarios);
                    const isBest = bestIdx !== undefined && bestIdx === scenarioIdx;

                    return (
                      <div key={metric.key} className="flex items-start justify-between">
                        <div className="flex items-center gap-2 flex-1">
                          {metric.icon && <metric.icon className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />}
                          <span className="text-sm font-medium text-gray-700">{metric.label}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {isBest && <Check className="w-4 h-4 text-green-600 flex-shrink-0" />}
                          <span
                            className={`text-sm ${
                              isBest ? 'text-green-900 font-semibold' : 'text-gray-900'
                            }`}
                          >
                            {metric.format(scenario)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer Info */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-start gap-2 text-xs text-gray-600">
          <AlertCircle className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
          <p>
            Best values are highlighted in green with a checkmark. Click column headers to sort. Ministerial approvals
            (green badge) are by-right and faster than discretionary approvals (yellow badge).
          </p>
        </div>
      </div>
    </div>
  );
}
