'use client';

import { useState } from 'react';
import type { FeasibilityAnalysis } from '@/lib/types/economic-feasibility';
import MetricsCard from './MetricsCard';
import RecommendationBanner from './RecommendationBanner';
import TabNavigation from './TabNavigation';
import NPVChart from './NPVChart';
import TornadoChart from './TornadoChart';
import MonteCarloChart from './MonteCarloChart';
import CashFlowWaterfall from './CashFlowWaterfall';
import CostBreakdown from './CostBreakdown';
import RevenueBreakdown from './RevenueBreakdown';
import SourceNotesPanel from './SourceNotesPanel';
import { ArrowLeft, Download } from 'lucide-react';

interface FeasibilityDashboardProps {
  analysis: FeasibilityAnalysis;
  onBack?: () => void;
}

export default function FeasibilityDashboard({
  analysis,
  onBack,
}: FeasibilityDashboardProps) {
  const [selectedView, setSelectedView] = useState<'overview' | 'sensitivity' | 'details'>(
    'overview'
  );

  const handleExport = () => {
    const dataStr = JSON.stringify(analysis, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `feasibility-${analysis.parcel_apn}-${Date.now()}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              {onBack && (
                <button
                  onClick={onBack}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Go back"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-600" />
                </button>
              )}
              <h1 className="text-2xl font-bold text-gray-900">
                Economic Feasibility Analysis
              </h1>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm text-gray-600">
              <span>
                <strong className="text-gray-900">Scenario:</strong>{' '}
                {analysis.scenario_name}
              </span>
              <span className="hidden sm:inline">•</span>
              <span>
                <strong className="text-gray-900">Parcel:</strong>{' '}
                {analysis.parcel_apn}
              </span>
              <span className="hidden sm:inline">•</span>
              <span>
                {new Date(analysis.analysis_timestamp).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>
          </div>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          label="Net Present Value"
          value={analysis.financial_metrics.npv}
          format="currency"
          subtitle={`@ ${(analysis.financial_metrics.financing_assumptions.discount_rate * 100).toFixed(1)}% discount rate`}
        />
        <MetricsCard
          label="Internal Rate of Return"
          value={analysis.financial_metrics.irr}
          format="percent"
        />
        <MetricsCard
          label="Payback Period"
          value={analysis.financial_metrics.payback_period_years}
          format="years"
        />
        <MetricsCard
          label="Profitability Index"
          value={analysis.financial_metrics.profitability_index}
          format="decimal"
          subtitle="NPV / Initial Investment"
        />
      </div>

      {/* Additional Financial Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          label="Return on Cost"
          value={analysis.financial_metrics.return_on_cost}
          format="percent"
          subtitle="NOI / Total Development Cost"
        />
        <MetricsCard
          label="Exit Value"
          value={analysis.financial_metrics.exit_value}
          format="currency"
          subtitle="Projected sale price"
        />
        <MetricsCard
          label="Debt Service Coverage"
          value={analysis.financial_metrics.debt_service_coverage_ratio}
          format="decimal"
          subtitle="NOI / Annual Debt Service"
        />
        <MetricsCard
          label="Loan-to-Value Ratio"
          value={analysis.financial_metrics.loan_to_value_ratio}
          format="percent"
          subtitle="Loan Amount / Exit Value"
        />
      </div>

      {/* Recommendation Banner */}
      <RecommendationBanner
        recommendation={analysis.decision_recommendation}
        probability={analysis.sensitivity_analysis.monte_carlo.probability_npv_positive}
      />

      {/* Tab Navigation */}
      <TabNavigation selected={selectedView} onChange={setSelectedView} />

      {/* Content based on selected view */}
      {selectedView === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <NPVChart financialMetrics={analysis.financial_metrics} />
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Financing Structure
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Loan Amount</span>
                  <span className="text-base font-semibold text-gray-900">
                    $
                    {(
                      analysis.financial_metrics.financing_assumptions.loan_amount / 1000000
                    ).toFixed(2)}
                    M
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Loan-to-Cost</span>
                  <span className="text-base font-semibold text-gray-900">
                    {(
                      analysis.financial_metrics.financing_assumptions.loan_to_cost * 100
                    ).toFixed(0)}
                    %
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Interest Rate</span>
                  <span className="text-base font-semibold text-gray-900">
                    {(
                      analysis.financial_metrics.financing_assumptions.interest_rate * 100
                    ).toFixed(2)}
                    %
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Loan Term</span>
                  <span className="text-base font-semibold text-gray-900">
                    {analysis.financial_metrics.financing_assumptions.loan_term_years} years
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Amortization</span>
                  <span className="text-base font-semibold text-gray-900">
                    {analysis.financial_metrics.financing_assumptions.amortization_years}{' '}
                    years
                  </span>
                </div>
              </div>
            </div>
          </div>
          <CashFlowWaterfall cashFlows={analysis.financial_metrics.total_cash_flows} />
        </div>
      )}

      {selectedView === 'sensitivity' && (
        <div className="space-y-6">
          <MonteCarloChart monteCarlo={analysis.sensitivity_analysis.monte_carlo} />
          <TornadoChart tornado={analysis.sensitivity_analysis.tornado} />
        </div>
      )}

      {selectedView === 'details' && (
        <div className="space-y-6">
          <CostBreakdown estimate={analysis.construction_cost_estimate} />
          <RevenueBreakdown projection={analysis.revenue_projection} />
          <SourceNotesPanel notes={analysis.source_notes} />
        </div>
      )}
    </div>
  );
}
