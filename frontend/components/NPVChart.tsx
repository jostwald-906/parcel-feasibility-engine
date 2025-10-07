'use client';

import { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import type { FinancialMetrics, CashFlow } from '@/lib/types/economic-feasibility';
import '../lib/chart-config'; // Import to register Chart.js components

interface NPVChartProps {
  financialMetrics: FinancialMetrics;
}

// Calculate NPV for a given discount rate
function calculateNPV(cashFlows: CashFlow[], discountRate: number): number {
  return cashFlows.reduce((sum, cf) => {
    return sum + cf.net_cash_flow / Math.pow(1 + discountRate, cf.period);
  }, 0);
}

export default function NPVChart({ financialMetrics }: NPVChartProps) {
  const chartData = useMemo(() => {
    // Generate NPV curve for discount rates 5% to 25%
    const discountRates = Array.from({ length: 21 }, (_, i) => 0.05 + i * 0.01);
    const npvValues = discountRates.map(rate =>
      calculateNPV(financialMetrics.total_cash_flows, rate)
    );

    // Find IRR (where NPV crosses zero)
    const irrIndex = npvValues.findIndex((npv, i) =>
      i > 0 && npvValues[i - 1] > 0 && npv <= 0
    );

    return {
      labels: discountRates.map(r => `${(r * 100).toFixed(0)}%`),
      datasets: [
        {
          label: 'NPV',
          data: npvValues,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 2,
          pointHoverRadius: 6,
        },
        // Add horizontal line at NPV = 0
        {
          label: 'Break-even',
          data: Array(21).fill(0),
          borderColor: 'rgb(239, 68, 68)',
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
        },
      ],
    };
  }, [financialMetrics]);

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          NPV Sensitivity to Discount Rate
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          How the project's Net Present Value changes with different discount rates
        </p>
      </div>
      <div style={{ height: '300px' }}>
        <Line
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const label = context.dataset.label || '';
                    const value = context.parsed.y;
                    if (label === 'NPV') {
                      return `${label}: $${(value / 1000000).toFixed(2)}M`;
                    }
                    return label;
                  },
                },
              },
            },
            scales: {
              y: {
                title: {
                  display: true,
                  text: 'Net Present Value ($)',
                },
                ticks: {
                  callback: (value) => {
                    const num = value as number;
                    return `$${(num / 1000000).toFixed(1)}M`;
                  },
                },
              },
              x: {
                title: {
                  display: true,
                  text: 'Discount Rate',
                },
              },
            },
          }}
        />
      </div>
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Current Discount Rate:</span>
            <span className="ml-2 font-semibold text-gray-900">
              {(financialMetrics.financing_assumptions.discount_rate * 100).toFixed(1)}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">IRR:</span>
            <span className="ml-2 font-semibold text-gray-900">
              {(financialMetrics.irr * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
