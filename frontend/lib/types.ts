/**
 * TypeScript types for the Parcel Feasibility Engine API
 */

export interface Parcel {
  apn: string;
  address: string;
  city: string;
  county: string;
  zip_code: string;
  lot_size_sqft: number;
  lot_width_ft?: number;
  lot_depth_ft?: number;
  zoning_code: string;
  general_plan?: string;
  existing_units: number;
  existing_building_sqft: number;
  year_built?: number;
  latitude?: number;
  longitude?: number;
  // Density Bonus fields
  for_sale?: boolean;
  avg_bedrooms_per_unit?: number;
  near_transit?: boolean;
  street_row_width?: number;
  // Overlay and tier fields
  development_tier?: string;
  overlay_codes?: string[];
  // Environmental and hazard flags
  in_coastal_zone?: boolean;
  in_flood_zone?: boolean;
  is_historic_property?: boolean;
  // Environmental GIS fields for SB35/AB2011 exclusions
  in_wetlands?: boolean;
  in_conservation_area?: boolean;
  fire_hazard_zone?: string | null;
  near_hazardous_waste?: boolean;
  in_earthquake_fault_zone?: boolean;
}

export interface AnalysisRequest {
  parcel: Parcel;
  proposed_project?: ProposedProject;
  include_sb9?: boolean;
  include_sb35?: boolean;
  include_ab2011?: boolean;
  include_density_bonus?: boolean;
  target_affordability_pct?: number;
  prefer_max_density?: boolean;
}

export interface DevelopmentScenario {
  scenario_name: string;
  legal_basis: string;
  max_units: number;
  max_building_sqft: number;
  max_height_ft: number;
  max_stories: number;
  parking_spaces_required: number;
  affordable_units_required: number;
  setbacks: {
    front?: number;
    rear?: number;
    side?: number;
  };
  lot_coverage_pct: number;
  estimated_buildable_sqft?: number;
  notes: string[];
}

export interface RentControlUnit {
  unit: string;
  mar: string;
  tenancy_date: string;
  bedrooms: string;
  parcel: string;
}

export interface RentControlData {
  is_rent_controlled: boolean;
  total_units: number;
  avg_mar: number | null;
  units: RentControlUnit[];
}

export interface CNELAnalysis {
  cnel_db: number;
  category: string;
  category_label: string;
  suitable_for_residential: boolean;
  requires_study: boolean;
  window_requirement: string;
  mitigation_measures: string[];
  notes: string[];
  color: string;
  santa_monica_compliance?: {
    compliant: boolean;
    requires_variance: boolean;
    notes: string[];
  };
}

export interface CommunityBenefit {
  category: string;
  name: string;
  description: string;
  tier_eligibility: number[];
  typical_provision: string | null;
  notes: string[];
}

export interface CommunityBenefitsAnalysis {
  available_benefits: CommunityBenefit[];
  recommended: string[];
  tier_2_path: {
    title: string;
    requirements: string[];
  };
  tier_3_path: {
    title: string;
    requirements: string[];
  };
  notes: string[];
}

export interface AnalysisResponse {
  parcel_apn: string;
  analysis_date: string;
  base_scenario: DevelopmentScenario;
  alternative_scenarios: DevelopmentScenario[];
  recommended_scenario: string;
  recommendation_reason: string;
  applicable_laws: string[];
  potential_incentives: string[];
  warnings?: string[];
  rent_control?: RentControlData;
  cnel_analysis?: CNELAnalysis;
  community_benefits?: CommunityBenefitsAnalysis;
}

export interface StateLawInfo {
  name: string;
  code: string;
  description: string;
  year_enacted: number;
  applies_to: string[];
  key_provisions: string[];
  eligibility_criteria: string[];
}

export interface HealthCheck {
  status: string;
  version: string;
}

export interface UnitMix {
  studio: number;
  one_bedroom: number;
  two_bedroom: number;
  three_plus_bedroom: number;
}

export interface AffordableHousing {
  total_affordable_units: number;
  very_low_income_units: number;  // <50% AMI
  low_income_units: number;        // 50-80% AMI
  moderate_income_units: number;   // 80-120% AMI
  affordability_duration_years: number;
}

export interface Parking {
  proposed_spaces: number;
  parking_type: 'surface' | 'underground' | 'structured' | 'mixed';
  bicycle_spaces: number;
}

export interface Setbacks {
  front_ft: number;
  rear_ft: number;
  side_ft: number;
}

export interface SiteConfiguration {
  lot_coverage_pct: number;
  open_space_sqft: number;
  setbacks: Setbacks;
}

export interface ProposedProject {
  // Existing fields
  average_bedrooms_per_unit?: number;
  for_sale_project?: boolean;

  // Project Type & Use
  ownership_type?: 'for-sale' | 'rental' | 'mixed';
  mixed_use?: boolean;
  ground_floor_use?: 'retail' | 'office' | 'commercial' | 'live-work' | null;
  commercial_sqft?: number;

  // Building Specifications
  proposed_stories?: number;
  proposed_height_ft?: number;
  proposed_units?: number;
  average_unit_size_sqft?: number;
  total_building_sqft?: number;

  // Unit Mix
  unit_mix?: UnitMix;

  // Affordable Housing
  affordable_housing?: AffordableHousing;

  // Parking
  parking?: Parking;

  // Site Configuration
  site_configuration?: SiteConfiguration;
}
