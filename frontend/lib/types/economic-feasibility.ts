/**
 * TypeScript types for Economic Feasibility Analysis
 * Mirrors backend Pydantic models in app/models/economic_feasibility.py
 */

export interface FeasibilityAnalysis {
  scenario_name: string;
  parcel_apn: string;
  construction_cost_estimate: ConstructionCostEstimate;
  revenue_projection: RevenueProjection;
  financial_metrics: FinancialMetrics;
  sensitivity_analysis: SensitivityAnalysis;
  decision_recommendation: string;
  source_notes: Record<string, any>;
  analysis_timestamp: string;
}

export interface ConstructionCostEstimate {
  hard_costs: number;
  soft_costs: number;
  total_cost: number;
  cost_per_unit: number;
  cost_per_sf: number;
  hard_cost_breakdown: {
    site_work: number;
    structure: number;
    exterior_closure: number;
    interior_construction: number;
    mep_systems: number;
    equipment: number;
    sitework_utilities: number;
  };
  soft_cost_breakdown: {
    architectural_engineering: number;
    permits_fees: number;
    insurance_bonds: number;
    construction_loan_interest: number;
    marketing_leasing: number;
    developer_fee: number;
    contingency: number;
  };
  cost_assumptions: {
    base_cost_per_sf: number;
    construction_type: string;
    location_multiplier: number;
    complexity_factor: number;
    soft_cost_percentage: number;
  };
}

export interface RevenueProjection {
  annual_gross_income: number;
  annual_noi: number;
  noi_per_unit: number;
  revenue_breakdown: {
    market_rate_rent: number;
    affordable_rent: number;
    parking_income: number;
    other_income: number;
  };
  operating_expense_breakdown: {
    property_management: number;
    utilities: number;
    maintenance_repairs: number;
    property_tax: number;
    insurance: number;
    reserves: number;
  };
  unit_economics: {
    avg_market_rent_per_unit: number;
    avg_affordable_rent_per_unit: number;
    operating_expense_per_unit: number;
  };
  revenue_assumptions: {
    market_rent_per_sf: number;
    affordable_rent_discount: number;
    vacancy_rate: number;
    operating_expense_ratio: number;
    annual_rent_growth: number;
  };
  // Additional fields from backend integration
  gross_scheduled_income?: number;
  vacancy_loss?: number;
  effective_gross_income?: number;
  operating_expenses?: number;
  net_operating_income?: number;
  market_rate_units?: number;
  affordable_units?: number;
  // Detailed rent rolls by bedroom type
  market_rent_roll?: Record<string, number>;  // e.g., {"0BR": 2200, "1BR": 2800, "2BR": 3600}
  affordable_rent_roll?: Record<string, number>;  // e.g., {"1BR_50AMI": 1200, "2BR_60AMI": 1450}
  // AMI percentages used for affordable units
  ami_percentages?: number[];  // e.g., [50, 60, 80] for 50%, 60%, 80% AMI
  source_notes?: Record<string, any>;
}

export interface FinancialMetrics {
  npv: number;
  irr: number;
  payback_period_years: number;
  profitability_index: number;
  return_on_cost: number;
  debt_service_coverage_ratio: number;
  loan_to_value_ratio: number;
  exit_value: number;
  total_cash_flows: CashFlow[];
  financing_assumptions: {
    loan_amount: number;
    loan_to_cost: number;
    interest_rate: number;
    loan_term_years: number;
    amortization_years: number;
    discount_rate: number;
  };
}

export interface CashFlow {
  period: number;
  period_type: string;
  revenue: number;
  operating_expenses: number;
  debt_service: number;
  capital_expenditure: number;
  net_cash_flow: number;
  cumulative_cash_flow: number;
}

export interface TornadoResult {
  variable: string;
  downside_npv: number;
  upside_npv: number;
  impact: number;
}

export interface MonteCarloResult {
  probability_npv_positive: number;
  mean_npv: number;
  std_npv: number;
  percentiles: {
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
  };
  histogram_bins: number[];
  histogram_counts: number[];
}

export interface SensitivityAnalysis {
  tornado: TornadoResult[];
  monte_carlo: MonteCarloResult;
}

export interface FeasibilityRequest {
  scenario_name: string;
  parcel_apn: string;
  total_units: number;
  total_building_sqft: number;
  affordable_units: number;
  construction_type?: string;
  county?: string;
  zip_code?: string;  // Added for HUD FMR lookup
  near_transit?: boolean;
  include_parking?: boolean;
  parking_spaces?: number;
  discount_rate?: number;
  hold_period_years?: number;
  // Timeline fields
  predevelopment_months?: number;
  construction_months?: number;
  lease_up_months?: number;
  // Revenue configuration (optional)
  revenue_inputs?: {
    market_unit_mix?: Record<number, number>;  // {0: studios, 1: 1BR, 2: 2BR, 3: 3BR}
    affordable_unit_mix?: Record<number, number>;
    quality_factor?: number;  // 0.8-1.2 for rent adjustments
  };
}

export interface CostIndices {
  rsmeans_indices: Record<string, number>;
  hcd_income_limits: Record<string, any>;
  last_updated: string;
}
