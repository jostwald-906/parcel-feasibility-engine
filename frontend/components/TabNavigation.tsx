'use client';

import { BarChart3, TrendingUp, FileText } from 'lucide-react';

interface TabNavigationProps {
  selected: 'overview' | 'sensitivity' | 'details';
  onChange: (tab: 'overview' | 'sensitivity' | 'details') => void;
}

export default function TabNavigation({ selected, onChange }: TabNavigationProps) {
  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: BarChart3 },
    { id: 'sensitivity' as const, label: 'Sensitivity Analysis', icon: TrendingUp },
    { id: 'details' as const, label: 'Details & Sources', icon: FileText },
  ];

  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isSelected = selected === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`
                group inline-flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${
                  isSelected
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <Icon
                className={`w-5 h-5 ${
                  isSelected ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'
                }`}
              />
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
