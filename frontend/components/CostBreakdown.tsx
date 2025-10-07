'use client';

import { Building2, Wrench, DollarSign } from 'lucide-react';
import type { ConstructionCostEstimate } from '@/lib/types/economic-feasibility';

interface CostBreakdownProps {
  estimate: ConstructionCostEstimate;
}

export default function CostBreakdown({ estimate }: CostBreakdownProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-blue-600" />
          Construction Cost Breakdown
        </h3>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-xs font-medium text-blue-700 mb-1">Total Cost</p>
          <p className="text-2xl font-bold text-blue-900">
            ${(estimate.total_cost / 1000000).toFixed(2)}M
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-600 mb-1">Cost per Unit</p>
          <p className="text-xl font-semibold text-gray-900">
            ${estimate.cost_per_unit.toLocaleString()}
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-600 mb-1">Cost per SF</p>
          <p className="text-xl font-semibold text-gray-900">
            ${estimate.cost_per_sf.toFixed(0)}/SF
          </p>
        </div>
      </div>

      {/* Hard Costs */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Building2 className="w-5 h-5 text-gray-700" />
          <h4 className="text-base font-semibold text-gray-900">Hard Costs</h4>
          <span className="ml-auto text-lg font-bold text-gray-900">
            ${(estimate.hard_costs / 1000000).toFixed(2)}M
          </span>
        </div>
        <div className="space-y-2">
          {Object.entries(estimate.hard_cost_breakdown).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-gray-700 capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <div className="flex items-center gap-3">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{
                      width: `${(value / estimate.hard_costs) * 100}%`,
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

      {/* Soft Costs */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Wrench className="w-5 h-5 text-gray-700" />
          <h4 className="text-base font-semibold text-gray-900">Soft Costs</h4>
          <span className="ml-auto text-lg font-bold text-gray-900">
            ${(estimate.soft_costs / 1000000).toFixed(2)}M
          </span>
        </div>
        <div className="space-y-2">
          {Object.entries(estimate.soft_cost_breakdown).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-gray-700 capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <div className="flex items-center gap-3">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-amber-500 h-2 rounded-full"
                    style={{
                      width: `${(value / estimate.soft_costs) * 100}%`,
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

      {/* Cost Assumptions */}
      <div className="pt-4 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Cost Assumptions</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-600">Base Cost per SF:</span>
            <span className="ml-2 font-medium text-gray-900">
              ${estimate.cost_assumptions.base_cost_per_sf.toFixed(0)}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Construction Type:</span>
            <span className="ml-2 font-medium text-gray-900">
              {estimate.cost_assumptions.construction_type}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Location Multiplier:</span>
            <span className="ml-2 font-medium text-gray-900">
              {estimate.cost_assumptions.location_multiplier.toFixed(2)}x
            </span>
          </div>
          <div>
            <span className="text-gray-600">Complexity Factor:</span>
            <span className="ml-2 font-medium text-gray-900">
              {estimate.cost_assumptions.complexity_factor.toFixed(2)}x
            </span>
          </div>
          <div>
            <span className="text-gray-600">Soft Cost %:</span>
            <span className="ml-2 font-medium text-gray-900">
              {(estimate.cost_assumptions.soft_cost_percentage * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
