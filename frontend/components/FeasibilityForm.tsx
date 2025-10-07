'use client';

import { useState } from 'react';
import type { FeasibilityRequest } from '@/lib/types/economic-feasibility';
import { Calculator, Building2, DollarSign, Percent } from 'lucide-react';

interface FeasibilityFormProps {
  onSubmit: (request: FeasibilityRequest) => void;
  loading?: boolean;
  defaultValues?: Partial<FeasibilityRequest>;
}

export default function FeasibilityForm({
  onSubmit,
  loading = false,
  defaultValues,
}: FeasibilityFormProps) {
  const [formData, setFormData] = useState<Partial<FeasibilityRequest>>({
    scenario_name: defaultValues?.scenario_name || 'Development Scenario',
    parcel_apn: defaultValues?.parcel_apn || '',
    total_units: defaultValues?.total_units || undefined,
    total_building_sqft: defaultValues?.total_building_sqft || undefined,
    affordable_units: defaultValues?.affordable_units || 0,
    construction_type: defaultValues?.construction_type || 'Type V',
    county: defaultValues?.county || 'Los Angeles',
    near_transit: defaultValues?.near_transit ?? false,
    include_parking: defaultValues?.include_parking ?? true,
    parking_spaces: defaultValues?.parking_spaces || undefined,
    discount_rate: defaultValues?.discount_rate || 0.08,
    hold_period_years: defaultValues?.hold_period_years || 10,
  });

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;

    let parsedValue: any = value;

    if (type === 'number') {
      parsedValue = value === '' ? undefined : parseFloat(value);
    } else if (type === 'checkbox') {
      parsedValue = (e.target as HTMLInputElement).checked;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: parsedValue,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (
      !formData.parcel_apn ||
      !formData.total_units ||
      !formData.total_building_sqft
    ) {
      alert('Please fill in all required fields');
      return;
    }

    onSubmit(formData as FeasibilityRequest);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Calculator className="w-6 h-6 text-blue-600" />
          Economic Feasibility Input
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Enter project details to compute financial feasibility
        </p>
      </div>

      <div className="space-y-6">
        {/* Basic Information */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
            <Building2 className="w-5 h-5 text-gray-700" />
            Project Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Scenario Name
              </label>
              <input
                type="text"
                name="scenario_name"
                value={formData.scenario_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Parcel APN <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="parcel_apn"
                value={formData.parcel_apn}
                onChange={handleInputChange}
                placeholder="4276-019-030"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Total Units <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                name="total_units"
                value={formData.total_units || ''}
                onChange={handleInputChange}
                min="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Total Building SF <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                name="total_building_sqft"
                value={formData.total_building_sqft || ''}
                onChange={handleInputChange}
                min="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Affordable Units
              </label>
              <input
                type="number"
                name="affordable_units"
                value={formData.affordable_units || 0}
                onChange={handleInputChange}
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Construction Type
              </label>
              <select
                name="construction_type"
                value={formData.construction_type}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="Type I">Type I (Fire-resistant)</option>
                <option value="Type II">Type II (Non-combustible)</option>
                <option value="Type III">Type III (Ordinary)</option>
                <option value="Type IV">Type IV (Heavy timber)</option>
                <option value="Type V">Type V (Wood frame)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                County
              </label>
              <select
                name="county"
                value={formData.county}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              >
                <option value="Los Angeles">Los Angeles</option>
                <option value="San Francisco">San Francisco</option>
                <option value="San Diego">San Diego</option>
                <option value="Orange">Orange</option>
                <option value="Santa Clara">Santa Clara</option>
              </select>
            </div>
          </div>
        </div>

        {/* Site Characteristics */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
            <DollarSign className="w-5 h-5 text-gray-700" />
            Site & Parking
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                name="near_transit"
                checked={formData.near_transit || false}
                onChange={handleInputChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label className="text-sm font-medium text-gray-700">
                Near Major Transit (within 0.5 miles)
              </label>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                name="include_parking"
                checked={formData.include_parking || false}
                onChange={handleInputChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label className="text-sm font-medium text-gray-700">
                Include Parking Costs
              </label>
            </div>
            {formData.include_parking && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Parking Spaces
                </label>
                <input
                  type="number"
                  name="parking_spaces"
                  value={formData.parking_spaces || ''}
                  onChange={handleInputChange}
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                />
              </div>
            )}
          </div>
        </div>

        {/* Financial Assumptions */}
        <div>
          <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2 mb-4">
            <Percent className="w-5 h-5 text-gray-700" />
            Financial Assumptions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Discount Rate (%)
              </label>
              <input
                type="number"
                name="discount_rate"
                value={(formData.discount_rate || 0.08) * 100}
                onChange={(e) => {
                  const value = e.target.value === '' ? 0.08 : parseFloat(e.target.value) / 100;
                  setFormData((prev) => ({ ...prev, discount_rate: value }));
                }}
                min="0"
                max="100"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              />
              <p className="text-xs text-gray-500 mt-1">
                Typical range: 7-12%
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hold Period (years)
              </label>
              <input
                type="number"
                name="hold_period_years"
                value={formData.hold_period_years || 10}
                onChange={handleInputChange}
                min="1"
                max="30"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
              />
              <p className="text-xs text-gray-500 mt-1">
                Typical range: 5-15 years
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <button
          type="submit"
          disabled={loading}
          className="w-full px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Computing Feasibility...
            </span>
          ) : (
            'Compute Economic Feasibility'
          )}
        </button>
      </div>
    </form>
  );
}
