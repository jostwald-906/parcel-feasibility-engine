'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Building2, Home, Car, Trees } from 'lucide-react';
import { ProposedProject, UnitMix, AffordableHousing, Parking, SiteConfiguration, Setbacks } from '@/lib/types';

interface ProposedProjectFormProps {
  value: ProposedProject | undefined;
  onChange: (project: ProposedProject) => void;
}

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function CollapsibleSection({ title, icon, children, defaultOpen = false }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <h3 className="font-semibold text-gray-900">{title}</h3>
        </div>
        {isOpen ? <ChevronUp className="w-5 h-5 text-gray-600" /> : <ChevronDown className="w-5 h-5 text-gray-600" />}
      </button>
      {isOpen && (
        <div className="p-4 bg-white">
          {children}
        </div>
      )}
    </div>
  );
}

export default function ProposedProjectForm({ value, onChange }: ProposedProjectFormProps) {
  const project = value || {};

  const updateProject = (updates: Partial<ProposedProject>) => {
    onChange({ ...project, ...updates });
  };

  const updateUnitMix = (updates: Partial<UnitMix>) => {
    const unitMix = { ...project.unit_mix, ...updates } as UnitMix;
    updateProject({ unit_mix: unitMix });
  };

  const updateAffordableHousing = (updates: Partial<AffordableHousing>) => {
    const affordableHousing = { ...project.affordable_housing, ...updates } as AffordableHousing;
    updateProject({ affordable_housing: affordableHousing });
  };

  const updateParking = (updates: Partial<Parking>) => {
    const parking = { ...project.parking, ...updates } as Parking;
    updateProject({ parking: parking });
  };

  const updateSiteConfig = (updates: Partial<SiteConfiguration>) => {
    const siteConfiguration = { ...project.site_configuration, ...updates } as SiteConfiguration;
    updateProject({ site_configuration: siteConfiguration });
  };

  const updateSetbacks = (updates: Partial<Setbacks>) => {
    const setbacks = {
      ...project.site_configuration?.setbacks,
      ...updates
    } as Setbacks;
    updateSiteConfig({ setbacks });
  };

  // Calculate total units from unit mix
  const totalUnitsFromMix = (project.unit_mix?.studio || 0) +
    (project.unit_mix?.one_bedroom || 0) +
    (project.unit_mix?.two_bedroom || 0) +
    (project.unit_mix?.three_plus_bedroom || 0);

  // Calculate total affordable units
  const totalAffordableUnits = (project.affordable_housing?.very_low_income_units || 0) +
    (project.affordable_housing?.low_income_units || 0) +
    (project.affordable_housing?.moderate_income_units || 0);

  return (
    <div className="space-y-4">
      {/* Project Type & Use */}
      <CollapsibleSection title="Project Type & Use" icon={<Building2 className="w-5 h-5 text-blue-600" />} defaultOpen={true}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ownership Type
            </label>
            <select
              value={project.ownership_type || ''}
              onChange={(e) => {
                const val = e.target.value;
                updateProject({ ownership_type: val === '' ? undefined : val as 'for-sale' | 'rental' | 'mixed' });
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select...</option>
              <option value="for-sale">For-Sale</option>
              <option value="rental">Rental</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>

          <div className="flex items-center">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={project.mixed_use || false}
                onChange={(e) => updateProject({ mixed_use: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Mixed-Use Project</span>
            </label>
          </div>

          {project.mixed_use && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ground Floor Use
                </label>
                <select
                  value={project.ground_floor_use || ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    updateProject({ ground_floor_use: val === '' ? undefined : val as 'retail' | 'office' | 'commercial' | 'live-work' });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select...</option>
                  <option value="retail">Retail</option>
                  <option value="office">Office</option>
                  <option value="commercial">Commercial</option>
                  <option value="live-work">Live-Work</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Commercial Square Footage
                </label>
                <input
                  type="number"
                  value={project.commercial_sqft || ''}
                  onChange={(e) => updateProject({ commercial_sqft: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                  min="0"
                />
              </div>
            </>
          )}
        </div>
      </CollapsibleSection>

      {/* Building Specifications */}
      <CollapsibleSection title="Building Specifications" icon={<Building2 className="w-5 h-5 text-blue-600" />} defaultOpen={true}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proposed Stories
            </label>
            <input
              type="number"
              value={project.proposed_stories || ''}
              onChange={(e) => updateProject({ proposed_stories: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proposed Height (ft)
            </label>
            <input
              type="number"
              value={project.proposed_height_ft || ''}
              onChange={(e) => updateProject({ proposed_height_ft: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="0"
              step="0.1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proposed Units
            </label>
            <input
              type="number"
              value={project.proposed_units || ''}
              onChange={(e) => updateProject({ proposed_units: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Average Unit Size (sqft)
            </label>
            <input
              type="number"
              value={project.average_unit_size_sqft || ''}
              onChange={(e) => updateProject({ average_unit_size_sqft: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Total Building Sqft
            </label>
            <input
              type="number"
              value={project.total_building_sqft || ''}
              onChange={(e) => updateProject({ total_building_sqft: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Avg Bedrooms/Unit
            </label>
            <input
              type="number"
              value={project.average_bedrooms_per_unit || ''}
              onChange={(e) => updateProject({ average_bedrooms_per_unit: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="0"
              step="0.1"
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* Unit Mix */}
      <CollapsibleSection title="Unit Mix Breakdown" icon={<Home className="w-5 h-5 text-blue-600" />}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Studio Units
              </label>
              <input
                type="number"
                value={project.unit_mix?.studio || ''}
                onChange={(e) => updateUnitMix({ studio: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                1-Bedroom Units
              </label>
              <input
                type="number"
                value={project.unit_mix?.one_bedroom || ''}
                onChange={(e) => updateUnitMix({ one_bedroom: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                2-Bedroom Units
              </label>
              <input
                type="number"
                value={project.unit_mix?.two_bedroom || ''}
                onChange={(e) => updateUnitMix({ two_bedroom: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                3+ Bedroom Units
              </label>
              <input
                type="number"
                value={project.unit_mix?.three_plus_bedroom || ''}
                onChange={(e) => updateUnitMix({ three_plus_bedroom: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>
          </div>

          {totalUnitsFromMix > 0 && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Total units from mix:</strong> {totalUnitsFromMix}
                {project.proposed_units && totalUnitsFromMix !== project.proposed_units && (
                  <span className="ml-2 text-orange-600">
                    ⚠️ Does not match proposed units ({project.proposed_units})
                  </span>
                )}
              </p>
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* Affordable Housing */}
      <CollapsibleSection title="Affordable Housing Plan" icon={<Home className="w-5 h-5 text-blue-600" />}>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Very Low Income (&lt;50% AMI)
              </label>
              <input
                type="number"
                value={project.affordable_housing?.very_low_income_units || ''}
                onChange={(e) => updateAffordableHousing({ very_low_income_units: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Low Income (50-80% AMI)
              </label>
              <input
                type="number"
                value={project.affordable_housing?.low_income_units || ''}
                onChange={(e) => updateAffordableHousing({ low_income_units: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Moderate Income (80-120% AMI)
              </label>
              <input
                type="number"
                value={project.affordable_housing?.moderate_income_units || ''}
                onChange={(e) => updateAffordableHousing({ moderate_income_units: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Affordability Duration (years)
              </label>
              <input
                type="number"
                value={project.affordable_housing?.affordability_duration_years || 55}
                onChange={(e) => updateAffordableHousing({ affordability_duration_years: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="55"
                min="1"
              />
            </div>
          </div>

          {totalAffordableUnits > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                <strong>Total affordable units:</strong> {totalAffordableUnits}
                {project.proposed_units && (
                  <span className="ml-2">
                    ({((totalAffordableUnits / project.proposed_units) * 100).toFixed(1)}% of total)
                  </span>
                )}
              </p>
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* Parking */}
      <CollapsibleSection title="Parking & Access" icon={<Car className="w-5 h-5 text-blue-600" />}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proposed Parking Spaces
            </label>
            <input
              type="number"
              value={project.parking?.proposed_spaces || ''}
              onChange={(e) => updateParking({ proposed_spaces: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Parking Type
            </label>
            <select
              value={project.parking?.parking_type || 'surface'}
              onChange={(e) => updateParking({ parking_type: e.target.value as 'surface' | 'underground' | 'structured' | 'mixed' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="surface">Surface</option>
              <option value="underground">Underground</option>
              <option value="structured">Structured</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bicycle Parking Spaces
            </label>
            <input
              type="number"
              value={project.parking?.bicycle_spaces || ''}
              onChange={(e) => updateParking({ bicycle_spaces: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="0"
              min="0"
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* Site Configuration */}
      <CollapsibleSection title="Site Configuration" icon={<Trees className="w-5 h-5 text-blue-600" />}>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lot Coverage (%)
              </label>
              <input
                type="number"
                value={project.site_configuration?.lot_coverage_pct || ''}
                onChange={(e) => updateSiteConfig({ lot_coverage_pct: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
                max="100"
                step="0.1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Open Space (sqft)
              </label>
              <input
                type="number"
                value={project.site_configuration?.open_space_sqft || ''}
                onChange={(e) => updateSiteConfig({ open_space_sqft: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
                min="0"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Setbacks (ft)
            </label>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Front</label>
                <input
                  type="number"
                  value={project.site_configuration?.setbacks?.front_ft || ''}
                  onChange={(e) => updateSetbacks({ front_ft: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                  min="0"
                  step="0.1"
                />
              </div>

              <div>
                <label className="block text-xs text-gray-600 mb-1">Rear</label>
                <input
                  type="number"
                  value={project.site_configuration?.setbacks?.rear_ft || ''}
                  onChange={(e) => updateSetbacks({ rear_ft: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                  min="0"
                  step="0.1"
                />
              </div>

              <div>
                <label className="block text-xs text-gray-600 mb-1">Side</label>
                <input
                  type="number"
                  value={project.site_configuration?.setbacks?.side_ft || ''}
                  onChange={(e) => updateSetbacks({ side_ft: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                  min="0"
                  step="0.1"
                />
              </div>
            </div>
          </div>
        </div>
      </CollapsibleSection>

      {/* Legacy for-sale checkbox (for backward compatibility) */}
      <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={project.for_sale_project || false}
            onChange={(e) => updateProject({ for_sale_project: e.target.checked })}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">For-Sale Project (legacy field)</span>
        </label>
      </div>
    </div>
  );
}
