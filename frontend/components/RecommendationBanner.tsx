'use client';

import { CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';

interface RecommendationBannerProps {
  recommendation: string;
  probability?: number;
}

export default function RecommendationBanner({
  recommendation,
  probability
}: RecommendationBannerProps) {
  const getRecommendationType = (): 'proceed' | 'caution' | 'reconsider' => {
    const lower = recommendation.toLowerCase();

    if (lower.includes('proceed') || lower.includes('favorable') || lower.includes('recommended')) {
      return 'proceed';
    } else if (lower.includes('reconsider') || lower.includes('not recommended') || lower.includes('unfavorable')) {
      return 'reconsider';
    }
    return 'caution';
  };

  const type = getRecommendationType();

  const styles = {
    proceed: {
      bg: 'bg-green-50',
      border: 'border-green-500',
      text: 'text-green-900',
      icon: CheckCircle2,
      iconColor: 'text-green-600',
    },
    caution: {
      bg: 'bg-amber-50',
      border: 'border-amber-500',
      text: 'text-amber-900',
      icon: AlertTriangle,
      iconColor: 'text-amber-600',
    },
    reconsider: {
      bg: 'bg-red-50',
      border: 'border-red-500',
      text: 'text-red-900',
      icon: AlertCircle,
      iconColor: 'text-red-600',
    },
  };

  const style = styles[type];
  const Icon = style.icon;

  return (
    <div className={`${style.bg} border-l-4 ${style.border} rounded-lg p-6`}>
      <div className="flex items-start gap-4">
        <Icon className={`w-6 h-6 ${style.iconColor} flex-shrink-0 mt-1`} />
        <div className="flex-1">
          <h3 className={`text-lg font-semibold ${style.text} mb-2`}>
            Decision Recommendation
          </h3>
          <p className={`${style.text}`}>{recommendation}</p>
          {probability !== undefined && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Probability of Positive NPV
                </span>
                <span className={`text-2xl font-bold ${style.text}`}>
                  {(probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    probability >= 0.7
                      ? 'bg-green-600'
                      : probability >= 0.5
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${probability * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
