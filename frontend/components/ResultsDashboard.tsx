'use client';

import { AlertCircle, CheckCircle, Home, Building, Scale, FileText } from 'lucide-react';
import type { AnalysisResponse } from '@/lib/types';
import { formatDate, formatNumber } from '@/lib/utils';
import ScenarioComparison from './ScenarioComparison';
import CNELDisplayCard from './CNELDisplayCard';
import CommunityBenefitsCard from './CommunityBenefitsCard';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ResultsDashboardProps {
  analysis: AnalysisResponse;
  onReset: () => void;
}

export default function ResultsDashboard({ analysis, onReset }: ResultsDashboardProps) {
  // Prepare chart data
  const chartData = [
    {
      name: 'Base',
      units: analysis.base_scenario.max_units,
      building_sqft: analysis.base_scenario.max_building_sqft,
    },
    ...analysis.alternative_scenarios.map(s => ({
      name: s.scenario_name.replace(/SB9|SB35|AB2011/g, match => match).substring(0, 15),
      units: s.max_units,
      building_sqft: s.max_building_sqft,
    })),
  ];

  const maxUnits = Math.max(
    analysis.base_scenario.max_units,
    ...analysis.alternative_scenarios.map(s => s.max_units)
  );

  const unitIncrease = maxUnits - analysis.base_scenario.max_units;
  const increasePercentage = analysis.base_scenario.max_units > 0
    ? ((unitIncrease / analysis.base_scenario.max_units) * 100).toFixed(0)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold mb-2">Feasibility Analysis Results</h2>
            <p className="text-blue-100">APN: {analysis.parcel_apn}</p>
            <p className="text-blue-100 text-sm mt-1">
              Analyzed: {formatDate(analysis.analysis_date)}
            </p>
          </div>
          <button
            onClick={onReset}
            className="px-4 py-2 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors"
          >
            New Analysis
          </button>
        </div>
      </div>

      {/* Warnings Section */}
      {analysis.warnings && analysis.warnings.length > 0 && (
        <div className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-amber-900 mb-2">Important Notes</h3>
              <ul className="space-y-1">
                {analysis.warnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-amber-800">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Base Units</p>
              <p className="text-3xl font-bold text-gray-900">
                {formatNumber(analysis.base_scenario.max_units)}
              </p>
            </div>
            <Home className="w-10 h-10 text-blue-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Max Units Possible</p>
              <p className="text-3xl font-bold text-green-600">
                {formatNumber(maxUnits)}
              </p>
              {unitIncrease > 0 && (
                <p className="text-xs text-green-600 mt-1">
                  +{increasePercentage}% increase
                </p>
              )}
            </div>
            <Building className="w-10 h-10 text-green-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">State Laws Applicable</p>
              <p className="text-3xl font-bold text-blue-600">
                {analysis.applicable_laws.length}
              </p>
            </div>
            <Scale className="w-10 h-10 text-blue-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Scenarios Analyzed</p>
              <p className="text-3xl font-bold text-purple-600">
                {1 + analysis.alternative_scenarios.length}
              </p>
            </div>
            <FileText className="w-10 h-10 text-purple-600 opacity-20" />
          </div>
        </div>
      </div>

      {/* Recommendation */}
      <div className="bg-green-50 border-l-4 border-green-500 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-green-900 mb-1">Recommended Development Path</h3>
            <p className="text-green-800 font-medium">{analysis.recommended_scenario}</p>
            <p className="text-green-700 text-sm mt-2">{analysis.recommendation_reason}</p>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {analysis.warnings && analysis.warnings.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-900 mb-2">Warnings & Considerations</h3>
              <ul className="space-y-1">
                {analysis.warnings.map((warning, idx) => (
                  <li key={idx} className="text-yellow-800 text-sm flex items-start gap-2">
                    <span className="text-yellow-600 mt-1">•</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Unit Comparison by Scenario</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="units" fill="#3b82f6" name="Max Units" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Applicable Laws */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Applicable State Housing Laws</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {analysis.applicable_laws.map((law, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
              <Scale className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-900">{law}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Potential Incentives */}
      {analysis.potential_incentives.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Potential Incentives & Opportunities</h3>
          <div className="space-y-2">
            {analysis.potential_incentives.map((incentive, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-gray-900">{incentive}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rent Control Information */}
      {analysis.rent_control && analysis.rent_control.is_rent_controlled && (
        <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
          <div className="flex items-start gap-3 mb-4">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Rent Control Status</h3>
              <p className="text-sm text-red-700 mt-1">
                This property has {analysis.rent_control.total_units} rent-controlled unit{analysis.rent_control.total_units > 1 ? 's' : ''}.
                Development may require tenant protections and relocation assistance.
              </p>
              {analysis.rent_control.avg_mar && (
                <p className="text-sm text-gray-700 mt-2">
                  Average Maximum Allowable Rent: <span className="font-semibold">${analysis.rent_control.avg_mar.toFixed(2)}</span>
                </p>
              )}
            </div>
          </div>

          {/* Units Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">MAR</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bedrooms</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tenancy Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analysis.rent_control.units.map((unit, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{unit.unit}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{unit.mar}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{unit.bedrooms}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{unit.tenancy_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 p-4 bg-amber-50 border-l-4 border-amber-500 rounded">
            <p className="text-sm text-amber-900">
              <span className="font-semibold">Important:</span> Santa Monica has strict tenant protection laws.
              Consult with legal counsel regarding relocation requirements, just cause eviction protections,
              and tenant buyout agreements before proceeding with development.
            </p>
          </div>
        </div>
      )}

      {/* CNEL Analysis Section */}
      {analysis.cnel_analysis && (
        <CNELDisplayCard cnel={analysis.cnel_analysis} />
      )}

      {/* Community Benefits Section */}
      {analysis.community_benefits && (
        <CommunityBenefitsCard benefits={analysis.community_benefits} />
      )}

      {/* Scenario Comparison */}
      <ScenarioComparison
        scenarios={[analysis.base_scenario, ...analysis.alternative_scenarios]}
        recommendedScenario={analysis.recommended_scenario}
      />
    </div>
  );
}
