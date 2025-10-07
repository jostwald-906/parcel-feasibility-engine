'use client';

import { TrendingUp, Home, Percent } from 'lucide-react';
import type { RevenueProjection } from '@/lib/types/economic-feasibility';

interface RevenueBreakdownProps {
  projection: RevenueProjection;
}

export default function RevenueBreakdown({ projection }: RevenueBreakdownProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-green-600" />
          Revenue & Operating Income Projection
        </h3>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-xs font-medium text-green-700 mb-1">Annual NOI</p>
          <p className="text-2xl font-bold text-green-900">
            ${(projection.annual_noi / 1000000).toFixed(2)}M
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-600 mb-1">Gross Income</p>
          <p className="text-xl font-semibold text-gray-900">
            ${(projection.annual_gross_income / 1000000).toFixed(2)}M
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-600 mb-1">NOI per Unit</p>
          <p className="text-xl font-semibold text-gray-900">
            ${projection.noi_per_unit.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Revenue Breakdown */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Home className="w-5 h-5 text-gray-700" />
          <h4 className="text-base font-semibold text-gray-900">Revenue Sources</h4>
          <span className="ml-auto text-lg font-bold text-gray-900">
            ${(projection.annual_gross_income / 1000000).toFixed(2)}M
          </span>
        </div>
        <div className="space-y-2">
          {Object.entries(projection.revenue_breakdown).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-gray-700 capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <div className="flex items-center gap-3">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{
                      width: `${(value / projection.annual_gross_income) * 100}%`,
                    }}
                  />
                </div>
                <span className="font-semibold text-gray-900 w-24 text-right">
                  ${(value / 1000).toFixed(0)}K
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Operating Expenses */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Percent className="w-5 h-5 text-gray-700" />
          <h4 className="text-base font-semibold text-gray-900">Operating Expenses</h4>
          <span className="ml-auto text-lg font-bold text-gray-900">
            ${((projection.annual_gross_income - projection.annual_noi) / 1000000).toFixed(2)}M
          </span>
        </div>
        <div className="space-y-2">
          {Object.entries(projection.operating_expense_breakdown).map(([key, value]) => {
            const totalOpEx = projection.annual_gross_income - projection.annual_noi;
            return (
              <div key={key} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center gap-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-500 h-2 rounded-full"
                      style={{
                        width: `${totalOpEx > 0 ? (value / totalOpEx) * 100 : 0}%`,
                      }}
                    />
                  </div>
                  <span className="font-semibold text-gray-900 w-24 text-right">
                    ${(value / 1000).toFixed(0)}K
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Unit Economics */}
      <div className="pt-4 border-t border-gray-200 mb-6">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Unit Economics</h4>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-600 block mb-1">Avg Market Rent</span>
            <span className="font-semibold text-gray-900 text-lg">
              ${projection.unit_economics.avg_market_rent_per_unit.toLocaleString()}/unit
            </span>
          </div>
          <div>
            <span className="text-gray-600 block mb-1">Avg Affordable Rent</span>
            <span className="font-semibold text-gray-900 text-lg">
              ${projection.unit_economics.avg_affordable_rent_per_unit.toLocaleString()}/unit
            </span>
          </div>
          <div>
            <span className="text-gray-600 block mb-1">OpEx per Unit</span>
            <span className="font-semibold text-gray-900 text-lg">
              ${projection.unit_economics.operating_expense_per_unit.toLocaleString()}/unit
            </span>
          </div>
        </div>
      </div>

      {/* Revenue Assumptions */}
      <div className="pt-4 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Revenue Assumptions</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-600">Market Rent per SF:</span>
            <span className="ml-2 font-medium text-gray-900">
              ${projection.revenue_assumptions.market_rent_per_sf.toFixed(2)}/SF
            </span>
          </div>
          <div>
            <span className="text-gray-600">Affordable Discount:</span>
            <span className="ml-2 font-medium text-gray-900">
              {(projection.revenue_assumptions.affordable_rent_discount * 100).toFixed(0)}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">Vacancy Rate:</span>
            <span className="ml-2 font-medium text-gray-900">
              {(projection.revenue_assumptions.vacancy_rate * 100).toFixed(0)}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">OpEx Ratio:</span>
            <span className="ml-2 font-medium text-gray-900">
              {(projection.revenue_assumptions.operating_expense_ratio * 100).toFixed(0)}%
            </span>
          </div>
          <div>
            <span className="text-gray-600">Annual Rent Growth:</span>
            <span className="ml-2 font-medium text-gray-900">
              {(projection.revenue_assumptions.annual_rent_growth * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
