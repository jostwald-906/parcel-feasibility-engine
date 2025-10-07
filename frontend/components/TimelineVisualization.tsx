'use client';

import { Clock, Calendar, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface TimelineStep {
  step_name: string;
  days_min: number;
  days_max: number;
  description: string;
  required_submittals: string[];
}

interface EntitlementTimeline {
  pathway_type: string; // "Ministerial", "Administrative", "Discretionary"
  total_days_min: number;
  total_days_max: number;
  steps: TimelineStep[];
  statutory_deadline: number | null;
  notes: string[];
}

interface TimelineVisualizationProps {
  timeline: EntitlementTimeline;
  scenarioName: string;
}

export default function TimelineVisualization({ timeline, scenarioName }: TimelineVisualizationProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (index: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSteps(newExpanded);
  };

  // Calculate estimated months
  const monthsMin = Math.ceil(timeline.total_days_min / 30);
  const monthsMax = Math.ceil(timeline.total_days_max / 30);

  // Determine pathway color scheme
  const getPathwayColors = (pathway: string) => {
    switch (pathway) {
      case 'Ministerial':
        return {
          badge: 'bg-green-100 text-green-800 border-green-300',
          header: 'from-green-50 to-green-100 border-green-200',
          icon: 'text-green-600',
          bar: 'bg-green-500',
        };
      case 'Administrative':
        return {
          badge: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          header: 'from-yellow-50 to-yellow-100 border-yellow-200',
          icon: 'text-yellow-600',
          bar: 'bg-yellow-500',
        };
      case 'Discretionary':
        return {
          badge: 'bg-red-100 text-red-800 border-red-300',
          header: 'from-red-50 to-red-100 border-red-200',
          icon: 'text-red-600',
          bar: 'bg-red-500',
        };
      default:
        return {
          badge: 'bg-gray-100 text-gray-800 border-gray-300',
          header: 'from-gray-50 to-gray-100 border-gray-200',
          icon: 'text-gray-600',
          bar: 'bg-gray-500',
        };
    }
  };

  const colors = getPathwayColors(timeline.pathway_type);

  // Calculate cumulative progress for each step
  const cumulativeDays: { min: number; max: number }[] = [];
  let cumulativeMin = 0;
  let cumulativeMax = 0;

  timeline.steps.forEach((step) => {
    cumulativeMin += step.days_min;
    cumulativeMax += step.days_max;
    cumulativeDays.push({ min: cumulativeMin, max: cumulativeMax });
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className={`px-6 py-4 bg-gradient-to-r ${colors.header} border-b`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Entitlement Timeline</h3>
            <p className="text-sm text-gray-700">{scenarioName}</p>
          </div>
          <span className={`px-3 py-1 border rounded-full text-xs font-semibold ${colors.badge}`}>
            {timeline.pathway_type}
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3">
            <Clock className={`w-5 h-5 ${colors.icon}`} />
            <div>
              <div className="text-xs text-gray-600">Estimated Timeline</div>
              <div className="text-lg font-bold text-gray-900">
                {timeline.total_days_min}-{timeline.total_days_max} days
              </div>
              <div className="text-xs text-gray-500">
                ({monthsMin}-{monthsMax} {monthsMax === 1 ? 'month' : 'months'})
              </div>
            </div>
          </div>

          {timeline.statutory_deadline && (
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-blue-600" />
              <div>
                <div className="text-xs text-gray-600">Statutory Deadline</div>
                <div className="text-lg font-bold text-blue-600">
                  {timeline.statutory_deadline} days
                </div>
                <div className="text-xs text-gray-500">State-mandated maximum</div>
              </div>
            </div>
          )}

          <div className="flex items-center gap-3">
            <Calendar className={`w-5 h-5 ${colors.icon}`} />
            <div>
              <div className="text-xs text-gray-600">Process Steps</div>
              <div className="text-lg font-bold text-gray-900">
                {timeline.steps.length}
              </div>
              <div className="text-xs text-gray-500">Required milestones</div>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline Steps */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-4">Timeline Breakdown</h4>
        <div className="space-y-3">
          {timeline.steps.map((step, index) => {
            const isExpanded = expandedSteps.has(index);
            const isLast = index === timeline.steps.length - 1;
            const cumulative = cumulativeDays[index];

            return (
              <div key={index} className="relative">
                {/* Connecting line */}
                {!isLast && (
                  <div className="absolute left-5 top-10 bottom-0 w-0.5 bg-gray-300" />
                )}

                {/* Step card */}
                <div className="bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
                  <button
                    onClick={() => toggleStep(index)}
                    className="w-full px-4 py-3 flex items-start gap-3 text-left"
                  >
                    {/* Step number */}
                    <div className={`flex-shrink-0 w-10 h-10 rounded-full ${colors.bar} bg-opacity-10 border-2 border-current flex items-center justify-center font-bold text-sm ${colors.icon}`}>
                      {index + 1}
                    </div>

                    {/* Step content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <h5 className="font-semibold text-gray-900 mb-1">
                            {step.step_name}
                          </h5>
                          <p className="text-sm text-gray-600">{step.description}</p>
                        </div>
                        <div className="flex items-center gap-3 flex-shrink-0">
                          <div className="text-right">
                            <div className="text-sm font-semibold text-gray-900">
                              {step.days_min}-{step.days_max} days
                            </div>
                            <div className="text-xs text-gray-500">
                              Day {cumulative.min}-{cumulative.max}
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                      </div>

                      {/* Expanded content */}
                      {isExpanded && step.required_submittals.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="text-xs font-medium text-gray-700 mb-2">
                            Required Submittals:
                          </div>
                          <ul className="space-y-1">
                            {step.required_submittals.map((submittal, idx) => (
                              <li
                                key={idx}
                                className="flex items-start gap-2 text-xs text-gray-600"
                              >
                                <CheckCircle className="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" />
                                <span>{submittal}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Visual Timeline Bar */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs font-medium text-gray-700 mb-2">Visual Timeline</div>
        <div className="relative h-8 bg-gray-200 rounded-full overflow-hidden">
          {timeline.steps.map((step, index) => {
            const cumulative = cumulativeDays[index];
            const previousCumulative = index > 0 ? cumulativeDays[index - 1] : { min: 0, max: 0 };

            // Calculate width as percentage of total
            const widthPercent =
              ((cumulative.max - previousCumulative.max) / timeline.total_days_max) * 100;
            const leftPercent = (previousCumulative.max / timeline.total_days_max) * 100;

            // Alternate colors for visual distinction
            const stepColors = [
              'bg-blue-500',
              'bg-purple-500',
              'bg-pink-500',
              'bg-indigo-500',
              'bg-cyan-500',
            ];
            const bgColor = stepColors[index % stepColors.length];

            return (
              <div
                key={index}
                className={`absolute h-full ${bgColor} border-r-2 border-white transition-all hover:opacity-80 cursor-pointer group`}
                style={{
                  left: `${leftPercent}%`,
                  width: `${widthPercent}%`,
                }}
                title={`${step.step_name}: ${step.days_min}-${step.days_max} days`}
              >
                <div className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white opacity-0 group-hover:opacity-100 transition-opacity">
                  {step.days_min}-{step.days_max}d
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>Day 0</span>
          <span>Day {timeline.total_days_max}</span>
        </div>
      </div>

      {/* Notes */}
      {timeline.notes.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Important Notes</h4>
          <ul className="space-y-1.5">
            {timeline.notes.map((note, index) => (
              <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-gray-400 mt-0.5">•</span>
                <span className="flex-1">{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
