'use client';

import { Building, Home, Ruler, Car, TrendingUp } from 'lucide-react';
import type { DevelopmentScenario } from '@/lib/types';
import { formatNumber } from '@/lib/utils';

interface ScenarioComparisonProps {
  scenarios: DevelopmentScenario[];
  recommendedScenario?: string;
}

export default function ScenarioComparison({ scenarios, recommendedScenario }: ScenarioComparisonProps) {
  if (scenarios.length === 0) {
    return null;
  }

  // Helper to extract existing units from notes
  const getExistingUnits = (scenario: DevelopmentScenario): number | null => {
    const match = scenario.notes.find(n => n.startsWith('Existing units on parcel:'));
    if (match) {
      const num = match.match(/\d+/);
      return num ? parseInt(num[0]) : null;
    }
    return null;
  };

  // Helper to extract net new units from notes
  const getNetNewUnits = (scenario: DevelopmentScenario): number | null => {
    const match = scenario.notes.find(n => n.startsWith('Net new units under this scenario:'));
    if (match) {
      const num = match.match(/\d+/);
      return num ? parseInt(num[0]) : null;
    }
    return null;
  };

  // Check if any scenario has existing units info
  const hasExistingUnits = scenarios.some(s => getExistingUnits(s) !== null);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900">Development Scenarios Comparison</h3>
        <p className="text-sm text-gray-600 mt-1">
          Comparing {scenarios.length} development {scenarios.length === 1 ? 'scenario' : 'scenarios'}
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50">
                Metric
              </th>
              {scenarios.map((scenario, idx) => (
                <th
                  key={idx}
                  className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                    scenario.scenario_name === recommendedScenario
                      ? 'bg-green-50 text-green-700'
                      : 'text-gray-500'
                  }`}
                >
                  <div className="flex flex-col gap-1">
                    <span>{scenario.scenario_name}</span>
                    {scenario.scenario_name === recommendedScenario && (
                      <span className="inline-flex items-center gap-1 text-xs font-normal text-green-600">
                        <TrendingUp className="w-3 h-3" />
                        Recommended
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {/* Legal Basis */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                Legal Basis
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className="px-6 py-4 text-sm text-gray-700">
                  <div className="max-w-xs">
                    {scenario.legal_basis}
                  </div>
                </td>
              ))}
            </tr>

            {/* Max Units */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                <div className="flex items-center gap-2">
                  <Home className="w-4 h-4 text-blue-600" />
                  Max Units
                </div>
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className={`px-6 py-4 text-sm font-semibold ${
                  scenario.scenario_name === recommendedScenario ? 'text-green-600' : 'text-gray-900'
                }`}>
                  {formatNumber(scenario.max_units)}
                </td>
              ))}
            </tr>

            {/* Existing Units (if applicable) */}
            {hasExistingUnits && (
              <tr className="bg-amber-50 hover:bg-amber-100">
                <td className="px-6 py-3 text-sm font-medium text-gray-700 sticky left-0 bg-amber-50">
                  <div className="flex items-center gap-2">
                    <Building className="w-4 h-4 text-amber-600" />
                    Existing Units
                  </div>
                </td>
                {scenarios.map((scenario, idx) => {
                  const existing = getExistingUnits(scenario);
                  return (
                    <td key={idx} className="px-6 py-3 text-sm text-amber-700 font-medium">
                      {existing !== null ? formatNumber(existing) : '-'}
                    </td>
                  );
                })}
              </tr>
            )}

            {/* Net New Units (if applicable) */}
            {hasExistingUnits && (
              <tr className="bg-blue-50 hover:bg-blue-100">
                <td className="px-6 py-3 text-sm font-medium text-gray-700 sticky left-0 bg-blue-50">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-600" />
                    Net New Units
                  </div>
                </td>
                {scenarios.map((scenario, idx) => {
                  const netNew = getNetNewUnits(scenario);
                  const existing = getExistingUnits(scenario);
                  const isNonconforming = existing !== null && existing > scenario.max_units;

                  return (
                    <td key={idx} className={`px-6 py-3 text-sm font-semibold ${
                      isNonconforming ? 'text-red-600' :
                      netNew && netNew > 0 ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {netNew !== null ? (
                        <div>
                          {formatNumber(netNew)}
                          {isNonconforming && (
                            <span className="ml-1 text-xs">(nonconforming)</span>
                          )}
                        </div>
                      ) : '-'}
                    </td>
                  );
                })}
              </tr>
            )}

            {/* Max Building Size */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                <div className="flex items-center gap-2">
                  <Building className="w-4 h-4 text-blue-600" />
                  Max Building (sq ft)
                </div>
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className="px-6 py-4 text-sm text-gray-700">
                  {formatNumber(scenario.max_building_sqft)}
                </td>
              ))}
            </tr>

            {/* Height */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                <div className="flex items-center gap-2">
                  <Ruler className="w-4 h-4 text-blue-600" />
                  Max Height
                </div>
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className="px-6 py-4 text-sm text-gray-700">
                  {scenario.max_height_ft} ft / {scenario.max_stories} stories
                </td>
              ))}
            </tr>

            {/* Parking */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                <div className="flex items-center gap-2">
                  <Car className="w-4 h-4 text-blue-600" />
                  Parking Required
                </div>
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className="px-6 py-4 text-sm text-gray-700">
                  {formatNumber(scenario.parking_spaces_required)} spaces
                </td>
              ))}
            </tr>

            {/* Affordable Units */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                Affordable Units Required
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className="px-6 py-4 text-sm text-gray-700">
                  {formatNumber(scenario.affordable_units_required)}
                  {scenario.affordable_units_required > 0 && scenario.max_units > 0 && (
                    <span className="text-xs text-gray-500 ml-1">
                      ({((scenario.affordable_units_required / scenario.max_units) * 100).toFixed(0)}%)
                    </span>
                  )}
                </td>
              ))}
            </tr>

            {/* Lot Coverage */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                Lot Coverage
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className="px-6 py-4 text-sm text-gray-700">
                  {Math.round(scenario.lot_coverage_pct)}%
                </td>
              ))}
            </tr>

            {/* Setbacks */}
            <tr className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                Setbacks (ft)
              </td>
              {scenarios.map((scenario, idx) => (
                <td key={idx} className="px-6 py-4 text-sm text-gray-700">
                  <div className="space-y-1">
                    {scenario.setbacks.front && <div>Front: {scenario.setbacks.front}</div>}
                    {scenario.setbacks.rear && <div>Rear: {scenario.setbacks.rear}</div>}
                    {scenario.setbacks.side && <div>Side: {scenario.setbacks.side}</div>}
                    {!scenario.setbacks.front && !scenario.setbacks.rear && !scenario.setbacks.side && '-'}
                  </div>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Scenario Details */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Scenario Details</h4>
        <div className="grid grid-cols-1 gap-4">
          {scenarios.map((scenario, idx) => {
            // Categorize notes
            const existingUnitsNote = scenario.notes.find(n => n.startsWith('Existing units on parcel:'));
            const netNewUnitsNote = scenario.notes.find(n => n.startsWith('Net new units under this scenario:'));
            const nonconformingNote = scenario.notes.find(n => n.includes('Legal nonconforming'));

            // Filter out the categorized notes from the general notes list
            const generalNotes = scenario.notes.filter(n =>
              !n.startsWith('Existing units on parcel:') &&
              !n.startsWith('Net new units under this scenario:') &&
              !n.includes('Legal nonconforming')
            );

            return (
              <div
                key={idx}
                className={`p-4 rounded-lg border ${
                  scenario.scenario_name === recommendedScenario
                    ? 'bg-green-50 border-green-200'
                    : 'bg-white border-gray-200'
                }`}
              >
                <h5 className="font-semibold text-gray-900 mb-3">{scenario.scenario_name}</h5>

                {/* Existing Units Info */}
                {(existingUnitsNote || netNewUnitsNote || nonconformingNote) && (
                  <div className="mb-3 p-2 bg-blue-50 rounded border border-blue-200">
                    <div className="text-xs font-medium text-blue-900 mb-1">Unit Count</div>
                    <div className="space-y-0.5 text-sm text-blue-800">
                      {existingUnitsNote && <div>• {existingUnitsNote}</div>}
                      {netNewUnitsNote && <div>• {netNewUnitsNote}</div>}
                      {nonconformingNote && (
                        <div className="text-red-600 font-medium">⚠️ {nonconformingNote}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* General Notes */}
                {generalNotes.length > 0 && (
                  <div className="space-y-1.5">
                    {generalNotes.map((note, noteIdx) => {
                      // Check if note starts with special indicators
                      const isRequirement = note.startsWith('✅ REQUIRES:') || note.includes('required');
                      const isWarning = note.startsWith('⚠️') || note.includes('Warning');
                      const isNote = note.startsWith('Note:');
                      const isCheckmark = note.startsWith('✅') && !note.startsWith('✅ REQUIRES:');

                      return (
                        <div
                          key={noteIdx}
                          className={`text-sm flex items-start gap-2 ${
                            isRequirement ? 'text-orange-700 font-medium' :
                            isWarning ? 'text-red-700' :
                            isCheckmark ? 'text-green-700' :
                            isNote ? 'text-gray-600 italic' :
                            'text-gray-700'
                          }`}
                        >
                          {!note.startsWith('✅') && !note.startsWith('⚠️') && !note.startsWith('💡') && (
                            <span className="text-gray-400 mt-0.5">•</span>
                          )}
                          <span className="flex-1">{note}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
