'use client';

import { Bar } from 'react-chartjs-2';
import type { MonteCarloResult } from '@/lib/types/economic-feasibility';
import '../lib/chart-config';

interface MonteCarloChartProps {
  monteCarlo: MonteCarloResult;
}

export default function MonteCarloChart({ monteCarlo }: MonteCarloChartProps) {
  const chartData = {
    labels: monteCarlo.histogram_bins.map(bin =>
      `$${(bin / 1000000).toFixed(1)}M`
    ),
    datasets: [
      {
        label: 'Frequency',
        data: monteCarlo.histogram_counts,
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Monte Carlo Simulation (10,000 Scenarios)
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Distribution of possible NPV outcomes based on variable uncertainty
        </p>
      </div>

      {/* Key Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <p className="text-xs font-medium text-blue-700 mb-1">
            Probability NPV &gt; 0
          </p>
          <p className="text-2xl font-bold text-blue-900">
            {(monteCarlo.probability_npv_positive * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-600 mb-1">Mean NPV</p>
          <p className="text-xl font-semibold text-gray-900">
            ${(monteCarlo.mean_npv / 1000000).toFixed(2)}M
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-600 mb-1">Std. Dev.</p>
          <p className="text-xl font-semibold text-gray-900">
            ${(monteCarlo.std_npv / 1000000).toFixed(2)}M
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-600 mb-1">Median (P50)</p>
          <p className="text-xl font-semibold text-gray-900">
            ${(monteCarlo.percentiles.p50 / 1000000).toFixed(2)}M
          </p>
        </div>
      </div>

      {/* Histogram */}
      <div style={{ height: '300px' }}>
        <Bar
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false,
              },
              tooltip: {
                callbacks: {
                  label: (context) => `Count: ${context.parsed.y} scenarios`,
                },
              },
            },
            scales: {
              y: {
                title: {
                  display: true,
                  text: 'Frequency (# of Scenarios)',
                },
              },
              x: {
                title: {
                  display: true,
                  text: 'NPV Range',
                },
              },
            },
          }}
        />
      </div>

      {/* Percentiles */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">
          Percentile Analysis
        </h4>
        <div className="grid grid-cols-5 gap-3 text-center">
          <div>
            <p className="text-xs text-gray-600 mb-1">P10 (Worst Case)</p>
            <p className="text-sm font-semibold text-red-600">
              ${(monteCarlo.percentiles.p10 / 1000000).toFixed(2)}M
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">P25</p>
            <p className="text-sm font-semibold text-gray-900">
              ${(monteCarlo.percentiles.p25 / 1000000).toFixed(2)}M
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">P50 (Median)</p>
            <p className="text-sm font-semibold text-blue-600">
              ${(monteCarlo.percentiles.p50 / 1000000).toFixed(2)}M
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">P75</p>
            <p className="text-sm font-semibold text-gray-900">
              ${(monteCarlo.percentiles.p75 / 1000000).toFixed(2)}M
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">P90 (Best Case)</p>
            <p className="text-sm font-semibold text-green-600">
              ${(monteCarlo.percentiles.p90 / 1000000).toFixed(2)}M
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-900">
          <strong>Interpretation:</strong> Based on 10,000 simulations with randomized
          assumptions, there is a {(monteCarlo.probability_npv_positive * 100).toFixed(1)}%
          chance this project will generate a positive NPV. The P10 value represents the
          worst-case scenario (10% chance of being lower), while P90 represents the
          best-case scenario (10% chance of being higher).
        </p>
      </div>
    </div>
  );
}
