'use client';

import { useState } from 'react';
import { Heart, ChevronDown, ChevronUp, ExternalLink, CheckCircle, TrendingUp, Zap } from 'lucide-react';
import type { CommunityBenefitsAnalysis, CommunityBenefit } from '@/lib/types';

interface CommunityBenefitsCardProps {
  benefits: CommunityBenefitsAnalysis;
}

export default function CommunityBenefitsCard({ benefits }: CommunityBenefitsCardProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [showTierPaths, setShowTierPaths] = useState(false);

  // Group benefits by category
  const benefitsByCategory = benefits.available_benefits.reduce((acc, benefit) => {
    if (!acc[benefit.category]) {
      acc[benefit.category] = [];
    }
    acc[benefit.category].push(benefit);
    return acc;
  }, {} as Record<string, CommunityBenefit[]>);

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const isRecommended = (benefitName: string) => {
    return benefits.recommended.includes(benefitName);
  };

  // Get tier badge color
  const getTierBadge = (tiers: number[]) => {
    const maxTier = Math.max(...tiers);
    if (maxTier === 1) {
      return 'bg-blue-100 text-blue-800 border-blue-200';
    } else if (maxTier === 2) {
      return 'bg-purple-100 text-purple-800 border-purple-200';
    } else {
      return 'bg-amber-100 text-amber-800 border-amber-200';
    }
  };

  const getTierLabel = (tiers: number[]) => {
    if (tiers.length === 1) {
      return `Tier ${tiers[0]}`;
    } else {
      return `Tiers ${tiers.join(', ')}`;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-gray-200">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-purple-100 flex-shrink-0">
            <Heart className="w-6 h-6 text-purple-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-purple-900 mb-1">
              Community Benefits Program
            </h3>
            <p className="text-sm text-purple-700">
              Available incentives under Santa Monica Downtown Community Plan
            </p>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="px-6 py-4 bg-purple-50 border-b border-gray-200">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-5 h-5 text-amber-600" />
          <p className="text-sm font-semibold text-gray-900">
            {benefits.available_benefits.length} Benefits Available
          </p>
        </div>
        {benefits.recommended.length > 0 && (
          <p className="text-sm text-gray-700 ml-7">
            <span className="font-medium">{benefits.recommended.length} recommended</span> for this parcel
          </p>
        )}
      </div>

      {/* Tier Upgrade Paths */}
      <div className="px-6 py-4 border-b border-gray-200">
        <button
          onClick={() => setShowTierPaths(!showTierPaths)}
          className="w-full flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <h4 className="text-sm font-semibold text-gray-900">
              Tier Upgrade Paths
            </h4>
          </div>
          {showTierPaths ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </button>

        {showTierPaths && (
          <div className="mt-4 space-y-4">
            {/* Tier 2 Path */}
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <h5 className="text-sm font-semibold text-purple-900 mb-2">
                {benefits.tier_2_path.title}
              </h5>
              <ul className="space-y-1">
                {benefits.tier_2_path.requirements.map((req, idx) => (
                  <li key={idx} className="text-sm text-purple-800 flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                    <span>{req}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Tier 3 Path */}
            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <h5 className="text-sm font-semibold text-amber-900 mb-2">
                {benefits.tier_3_path.title}
              </h5>
              <ul className="space-y-1">
                {benefits.tier_3_path.requirements.map((req, idx) => (
                  <li key={idx} className="text-sm text-amber-800 flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                    <span>{req}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Benefits by Category */}
      <div className="divide-y divide-gray-200">
        {Object.entries(benefitsByCategory).map(([category, categoryBenefits]) => (
          <div key={category}>
            {/* Category Header */}
            <button
              onClick={() => toggleCategory(category)}
              className="w-full px-6 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-gray-900">
                  {category}
                </span>
                <span className="text-xs text-gray-500">
                  ({categoryBenefits.length} {categoryBenefits.length === 1 ? 'benefit' : 'benefits'})
                </span>
              </div>
              {expandedCategories.has(category) ? (
                <ChevronUp className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              )}
            </button>

            {/* Category Benefits */}
            {expandedCategories.has(category) && (
              <div className="px-6 py-4 space-y-3 bg-white">
                {categoryBenefits.map((benefit, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border ${
                      isRecommended(benefit.name)
                        ? 'bg-green-50 border-green-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    {/* Benefit Header */}
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-start gap-2 flex-1 min-w-0">
                        {isRecommended(benefit.name) && (
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1 min-w-0">
                          <h5 className={`text-sm font-semibold ${
                            isRecommended(benefit.name) ? 'text-green-900' : 'text-gray-900'
                          }`}>
                            {benefit.name}
                            {isRecommended(benefit.name) && (
                              <span className="ml-2 text-xs font-medium text-green-700">
                                (Recommended)
                              </span>
                            )}
                          </h5>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium border flex-shrink-0 ${getTierBadge(benefit.tier_eligibility)}`}>
                        {getTierLabel(benefit.tier_eligibility)}
                      </span>
                    </div>

                    {/* Benefit Description */}
                    <p className={`text-sm mb-2 ${
                      isRecommended(benefit.name) ? 'text-green-800' : 'text-gray-700'
                    }`}>
                      {benefit.description}
                    </p>

                    {/* Typical Provision */}
                    {benefit.typical_provision && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <p className="text-xs font-medium text-gray-600 mb-1">
                          Typical Provision:
                        </p>
                        <p className="text-xs text-gray-700">
                          {benefit.typical_provision}
                        </p>
                      </div>
                    )}

                    {/* Notes */}
                    {benefit.notes && benefit.notes.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <p className="text-xs font-medium text-gray-600 mb-1">
                          Notes:
                        </p>
                        <ul className="space-y-0.5">
                          {benefit.notes.map((note, noteIdx) => (
                            <li key={noteIdx} className="text-xs text-gray-600 flex items-start gap-1">
                              <span className="text-gray-400">•</span>
                              <span>{note}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* General Notes */}
      {benefits.notes && benefits.notes.length > 0 && (
        <div className="px-6 py-4 bg-blue-50 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">
            Important Information
          </h4>
          <ul className="space-y-1">
            {benefits.notes.map((note, idx) => (
              <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-blue-600 mt-1 flex-shrink-0">•</span>
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer Link */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <a
          href="https://library.municode.com/ca/santa_monica/codes/code_of_ordinances?nodeId=SMMC_TIT9ZO_CH9.23DOCOPL_9.23.030DETIBOPR"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          View SMMC § 9.23.030 - Community Benefits
        </a>
      </div>
    </div>
  );
}
