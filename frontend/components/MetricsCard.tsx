'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricsCardProps {
  label: string;
  value: number;
  format: 'currency' | 'percent' | 'years' | 'decimal' | 'number';
  trend?: 'up' | 'down' | 'neutral';
  subtitle?: string;
}

export default function MetricsCard({
  label,
  value,
  format,
  trend,
  subtitle
}: MetricsCardProps) {
  const formatValue = (): string => {
    switch (format) {
      case 'currency':
        if (Math.abs(value) >= 1000000) {
          return `$${(value / 1000000).toFixed(2)}M`;
        } else if (Math.abs(value) >= 1000) {
          return `$${(value / 1000).toFixed(0)}K`;
        }
        return `$${value.toLocaleString()}`;

      case 'percent':
        return `${(value * 100).toFixed(1)}%`;

      case 'years':
        return `${value.toFixed(1)} years`;

      case 'decimal':
        return value.toFixed(2);

      case 'number':
        return value.toLocaleString();

      default:
        return value.toString();
    }
  };

  const getTrendColor = (): string => {
    if (!trend) return 'text-gray-900';

    // For NPV and IRR, up is good
    if (format === 'currency' || format === 'percent') {
      return trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-900';
    }

    // For payback period, down is good (shorter is better)
    if (format === 'years') {
      return trend === 'down' ? 'text-green-600' : trend === 'up' ? 'text-red-600' : 'text-gray-900';
    }

    return 'text-gray-900';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="text-sm font-medium text-gray-600 mb-1">{label}</div>
      <div className={`text-3xl font-bold ${getTrendColor()} flex items-center gap-2`}>
        {formatValue()}
        {trend === 'up' && <TrendingUp className="w-6 h-6" />}
        {trend === 'down' && <TrendingDown className="w-6 h-6" />}
      </div>
      {subtitle && (
        <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
      )}
    </div>
  );
}
