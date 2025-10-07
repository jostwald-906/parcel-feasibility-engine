'use client';

import { Bar } from 'react-chartjs-2';
import type { TornadoResult } from '@/lib/types/economic-feasibility';
import '../lib/chart-config';

interface TornadoChartProps {
  tornado: TornadoResult[];
}

// Format variable names for display
function formatVariableName(variable: string): string {
  return variable
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default function TornadoChart({ tornado }: TornadoChartProps) {
  // Sort by impact (already sorted from backend) and take top 8
  const sortedTornado = [...tornado].slice(0, 8);

  const chartData = {
    labels: sortedTornado.map(t => formatVariableName(t.variable)),
    datasets: [
      {
        label: 'Downside (-20%)',
        data: sortedTornado.map(t => t.downside_npv),
        backgroundColor: 'rgba(239, 68, 68, 0.7)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 1,
      },
      {
        label: 'Upside (+20%)',
        data: sortedTornado.map(t => t.upside_npv),
        backgroundColor: 'rgba(34, 197, 94, 0.7)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Tornado Sensitivity Analysis
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Impact of ±20% change in key variables on NPV (sorted by impact)
        </p>
      </div>
      <div style={{ height: '400px' }}>
        <Bar
          data={chartData}
          options={{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const value = context.parsed.x;
                    return `${context.dataset.label}: $${(value / 1000000).toFixed(2)}M`;
                  },
                },
              },
            },
            scales: {
              x: {
                title: {
                  display: true,
                  text: 'NPV ($)',
                },
                ticks: {
                  callback: (value) => {
                    const num = value as number;
                    return `$${(num / 1000000).toFixed(1)}M`;
                  },
                },
              },
              y: {
                ticks: {
                  autoSkip: false,
                },
              },
            },
          }}
        />
      </div>
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-start gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-sm mt-1 flex-shrink-0" />
          <p className="text-sm text-gray-600">
            <strong className="text-gray-900">Downside:</strong> NPV if variable decreases by 20%
          </p>
        </div>
        <div className="flex items-start gap-2 mt-2">
          <div className="w-3 h-3 bg-green-500 rounded-sm mt-1 flex-shrink-0" />
          <p className="text-sm text-gray-600">
            <strong className="text-gray-900">Upside:</strong> NPV if variable increases by 20%
          </p>
        </div>
      </div>
    </div>
  );
}
