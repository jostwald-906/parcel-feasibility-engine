'use client';

import { Bar } from 'react-chartjs-2';
import type { CashFlow } from '@/lib/types/economic-feasibility';
import '../lib/chart-config';

interface CashFlowWaterfallProps {
  cashFlows: CashFlow[];
}

export default function CashFlowWaterfall({ cashFlows }: CashFlowWaterfallProps) {
  const chartData = {
    labels: cashFlows.map(cf => {
      if (cf.period_type === 'construction') {
        return `Construction Y${cf.period}`;
      } else if (cf.period_type === 'stabilization') {
        return `Stabilization Y${cf.period}`;
      } else if (cf.period_type === 'exit') {
        return 'Exit';
      }
      return `Year ${cf.period}`;
    }),
    datasets: [
      {
        label: 'Net Cash Flow',
        data: cashFlows.map(cf => cf.net_cash_flow),
        backgroundColor: cashFlows.map(cf =>
          cf.net_cash_flow >= 0
            ? 'rgba(34, 197, 94, 0.7)'
            : 'rgba(239, 68, 68, 0.7)'
        ),
        borderColor: cashFlows.map(cf =>
          cf.net_cash_flow >= 0
            ? 'rgba(34, 197, 94, 1)'
            : 'rgba(239, 68, 68, 1)'
        ),
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Development Cash Flow Waterfall
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Net cash flows across construction, stabilization, and exit phases
        </p>
      </div>

      <div style={{ height: '350px' }}>
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
                  label: (context) => {
                    const cf = cashFlows[context.dataIndex];
                    return [
                      `Phase: ${cf.period_type}`,
                      `Net Cash Flow: $${(cf.net_cash_flow / 1000000).toFixed(2)}M`,
                      `Cumulative: $${(cf.cumulative_cash_flow / 1000000).toFixed(2)}M`,
                    ];
                  },
                },
              },
            },
            scales: {
              y: {
                title: {
                  display: true,
                  text: 'Cash Flow ($)',
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
                  text: 'Period',
                },
              },
            },
          }}
        />
      </div>

      {/* Summary table */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Cash Flow Summary</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-gray-700">Period</th>
                <th className="px-3 py-2 text-right font-medium text-gray-700">Phase</th>
                <th className="px-3 py-2 text-right font-medium text-gray-700">Revenue</th>
                <th className="px-3 py-2 text-right font-medium text-gray-700">OpEx</th>
                <th className="px-3 py-2 text-right font-medium text-gray-700">CapEx</th>
                <th className="px-3 py-2 text-right font-medium text-gray-700">Net CF</th>
                <th className="px-3 py-2 text-right font-medium text-gray-700">Cumulative</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {cashFlows.map((cf, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-900">{cf.period}</td>
                  <td className="px-3 py-2 text-right text-gray-600 capitalize">
                    {cf.period_type}
                  </td>
                  <td className="px-3 py-2 text-right text-gray-900">
                    ${(cf.revenue / 1000).toFixed(0)}K
                  </td>
                  <td className="px-3 py-2 text-right text-gray-900">
                    ${(cf.operating_expenses / 1000).toFixed(0)}K
                  </td>
                  <td className="px-3 py-2 text-right text-gray-900">
                    ${(cf.capital_expenditure / 1000).toFixed(0)}K
                  </td>
                  <td
                    className={`px-3 py-2 text-right font-semibold ${
                      cf.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    ${(cf.net_cash_flow / 1000).toFixed(0)}K
                  </td>
                  <td
                    className={`px-3 py-2 text-right font-medium ${
                      cf.cumulative_cash_flow >= 0 ? 'text-green-700' : 'text-red-700'
                    }`}
                  >
                    ${(cf.cumulative_cash_flow / 1000).toFixed(0)}K
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
