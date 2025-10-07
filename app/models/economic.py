"""
Pydantic models for economic feasibility analysis.

This module defines request/response models for the economic feasibility API,
including construction cost estimates, revenue projections, and financial metrics.

References:
- Real Estate Finance and Investment Manual
- Appraisal Institute methodology
- California Department of Housing and Community Development guidelines
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


# ============================================================================
# Economic Assumptions and Inputs
# ============================================================================


class EconomicAssumptions(BaseModel):
    """
    Economic assumptions for feasibility analysis.

    All default values are conservative for multifamily residential development
    in California coastal markets (2025 baseline).
    """

    # Discount rate and hurdle rate
    discount_rate: float = Field(
        0.12,
        ge=0,
        le=1.0,
        description="Annual discount rate for NPV calculation (e.g., 0.12 for 12%)"
    )
    hurdle_rate: float = Field(
        0.15,
        ge=0,
        le=1.0,
        description="Minimum acceptable IRR (e.g., 0.15 for 15%)"
    )

    # Construction costs
    base_cost_per_sf: float = Field(
        400.0,
        gt=0,
        description="Base construction cost per square foot (2025 baseline)"
    )
    quality_factor: float = Field(
        1.0,
        ge=0.5,
        le=2.0,
        description="Quality multiplier (0.5=low, 1.0=standard, 1.5=high, 2.0=luxury)"
    )
    soft_cost_pct: float = Field(
        0.20,
        ge=0,
        le=0.50,
        description="Soft costs as % of hard costs (architecture, engineering, legal)"
    )
    contingency_pct: float = Field(
        0.10,
        ge=0,
        le=0.30,
        description="Construction contingency as % of total costs"
    )

    # Revenue assumptions
    avg_rent_per_sf_month: float = Field(
        3.50,
        gt=0,
        description="Average market rent per SF per month"
    )
    vacancy_rate: float = Field(
        0.05,
        ge=0,
        le=0.30,
        description="Stabilized vacancy rate (e.g., 0.05 for 5%)"
    )
    rent_growth_rate: float = Field(
        0.03,
        ge=-0.10,
        le=0.20,
        description="Annual rent growth rate (e.g., 0.03 for 3%)"
    )

    # Operating expenses
    opex_per_unit_annual: float = Field(
        8000.0,
        ge=0,
        description="Operating expenses per unit per year (property mgmt, utilities, maintenance)"
    )
    property_tax_rate: float = Field(
        0.0125,
        ge=0,
        le=0.05,
        description="Property tax rate as % of assessed value (CA Prop 13: ~1.25%)"
    )
    insurance_rate: float = Field(
        0.005,
        ge=0,
        le=0.03,
        description="Insurance as % of property value"
    )

    # Exit assumptions
    exit_cap_rate: float = Field(
        0.05,
        gt=0,
        le=0.15,
        description="Exit cap rate for property sale (e.g., 0.05 for 5%)"
    )
    holding_period_years: int = Field(
        10,
        ge=1,
        le=30,
        description="Holding period before sale (years)"
    )

    # Development timeline
    predevelopment_months: int = Field(
        6,
        ge=0,
        le=36,
        description="Predevelopment phase duration (months)"
    )
    construction_months: int = Field(
        18,
        ge=6,
        le=60,
        description="Construction phase duration (months)"
    )
    lease_up_months: int = Field(
        6,
        ge=0,
        le=24,
        description="Lease-up phase duration (months)"
    )

    # Financing (optional for future enhancement)
    loan_to_cost: Optional[float] = Field(
        None,
        ge=0,
        le=1.0,
        description="Loan-to-cost ratio (e.g., 0.70 for 70% LTC)"
    )
    interest_rate: Optional[float] = Field(
        None,
        ge=0,
        le=0.20,
        description="Construction loan interest rate"
    )


class TimelineInputs(BaseModel):
    """Development timeline configuration."""

    predevelopment_months: int = Field(6, ge=0, description="Predevelopment duration")
    construction_months: int = Field(18, ge=6, description="Construction duration")
    lease_up_months: int = Field(6, ge=0, description="Lease-up duration")
    operations_years: int = Field(10, ge=1, description="Stabilized operations before sale")


class SensitivityVariable(BaseModel):
    """Configuration for sensitivity analysis variable."""

    variable_name: str = Field(..., description="Parameter name (e.g., 'cost_per_sf')")
    label: str = Field(..., description="Display label (e.g., 'Construction Cost per SF')")
    delta_pct: float = Field(
        0.15,
        gt=0,
        le=1.0,
        description="Percentage change to test (e.g., 0.15 for ±15%)"
    )


class MonteCarloConfig(BaseModel):
    """Configuration for Monte Carlo simulation."""

    iterations: int = Field(
        10000,
        ge=100,
        le=100000,
        description="Number of Monte Carlo iterations"
    )
    seed: int = Field(
        42,
        description="Random seed for reproducibility"
    )
    cost_per_sf_std: float = Field(
        25.0,
        ge=0,
        description="Standard deviation for cost per SF (normal distribution)"
    )
    rent_growth_std: float = Field(
        0.015,
        ge=0,
        description="Standard deviation for rent growth rate (normal distribution)"
    )
    cap_rate_min: float = Field(
        0.04,
        gt=0,
        description="Minimum exit cap rate (triangular distribution)"
    )
    cap_rate_mode: float = Field(
        0.05,
        gt=0,
        description="Most likely exit cap rate (triangular distribution)"
    )
    cap_rate_max: float = Field(
        0.07,
        gt=0,
        description="Maximum exit cap rate (triangular distribution)"
    )
    construction_delay_mean: float = Field(
        0.0,
        ge=0,
        description="Mean construction delay in months"
    )
    construction_delay_std: float = Field(
        3.0,
        ge=0,
        description="Standard deviation of construction delay (months)"
    )


# ============================================================================
# Cost Estimation Models
# ============================================================================


class ConstructionCostBreakdown(BaseModel):
    """Detailed construction cost breakdown."""

    hard_costs: float = Field(..., description="Hard construction costs")
    soft_costs: float = Field(..., description="Soft costs (A&E, legal, etc.)")
    contingency: float = Field(..., description="Construction contingency")
    total_cost: float = Field(..., description="Total development cost")

    # Breakdown details
    cost_per_sf: float = Field(..., description="Effective cost per buildable SF")
    buildable_sf: float = Field(..., description="Total buildable square footage")

    # Source notes
    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data sources and calculation methodology"
    )


class ConstructionCostEstimate(BaseModel):
    """Complete construction cost estimate."""

    total_cost: float = Field(..., description="Total estimated development cost")
    cost_per_sf: float = Field(..., description="Average cost per buildable SF")
    cost_per_unit: float = Field(..., description="Average cost per unit")

    breakdown: ConstructionCostBreakdown = Field(..., description="Detailed cost breakdown")

    # Escalation info
    escalation_applied: bool = Field(False, description="Whether cost escalation was applied")
    ppi_escalation_factor: Optional[float] = Field(None, description="PPI escalation factor")
    target_completion_date: Optional[date] = Field(None, description="Target project completion")

    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data sources for cost estimation"
    )


# ============================================================================
# Revenue Projection Models
# ============================================================================


class RevenueProjection(BaseModel):
    """Revenue and NOI projection."""

    # Rent projections
    gross_scheduled_income: float = Field(..., description="Gross scheduled rental income (100% occupied)")
    vacancy_loss: float = Field(..., description="Estimated vacancy and collection loss")
    effective_gross_income: float = Field(..., description="EGI = GSI - vacancy")

    # Operating expenses
    operating_expenses: float = Field(..., description="Total annual operating expenses")
    property_taxes: float = Field(..., description="Annual property taxes")
    insurance: float = Field(..., description="Annual insurance")

    # Net operating income
    net_operating_income: float = Field(..., description="NOI = EGI - OpEx - Taxes - Insurance")

    # Metrics
    noi_per_unit: float = Field(..., description="NOI per unit")
    operating_expense_ratio: float = Field(..., description="OpEx ratio (OpEx / EGI)")

    # Affordability mix impact
    affordable_rent_discount: Optional[float] = Field(
        None,
        description="Revenue reduction due to affordable units"
    )
    market_rate_units: int = Field(..., description="Number of market-rate units")
    affordable_units: int = Field(0, description="Number of affordable units")

    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data sources for revenue assumptions"
    )


# ============================================================================
# Financial Metrics Models
# ============================================================================


class CashFlowPeriod(BaseModel):
    """Single period cash flow."""

    period: int = Field(..., description="Period number (0 = initial, 1 = year 1, etc.)")
    description: str = Field(..., description="Period description")
    amount: float = Field(..., description="Cash flow amount (+ inflow, - outflow)")
    cumulative: float = Field(..., description="Cumulative cash flow to date")
    phase: str = Field(..., description="Development phase (predevelopment, construction, etc.)")


class FinancialMetrics(BaseModel):
    """Core financial performance metrics."""

    # NPV and IRR
    npv: float = Field(..., description="Net Present Value")
    irr: Optional[float] = Field(None, description="Internal Rate of Return (decimal)")
    irr_pct: Optional[str] = Field(None, description="IRR formatted as percentage")

    # Other metrics
    payback_period_years: float = Field(..., description="Payback period in years")
    profitability_index: float = Field(..., description="Profitability Index (PV/Initial Investment)")

    # Investment summary
    initial_investment: float = Field(..., description="Total initial capital required")
    total_cash_returned: float = Field(..., description="Total cash returned over holding period")

    # Discount rate used
    discount_rate: float = Field(..., description="Discount rate used for NPV")


# ============================================================================
# Sensitivity Analysis Models
# ============================================================================


class TornadoVariable(BaseModel):
    """Single variable result from tornado sensitivity analysis."""

    variable_name: str = Field(..., description="Variable identifier")
    label: str = Field(..., description="Display label")

    base_value: float = Field(..., description="Base case value")
    base_npv: float = Field(..., description="Base case NPV")

    downside_value: float = Field(..., description="Downside scenario value")
    downside_npv: float = Field(..., description="Downside NPV")

    upside_value: float = Field(..., description="Upside scenario value")
    upside_npv: float = Field(..., description="Upside NPV")

    impact: float = Field(..., description="Total impact (|upside - downside|)")
    rank: int = Field(..., description="Sensitivity rank (1 = most sensitive)")


class MonteCarloStatistics(BaseModel):
    """Monte Carlo simulation statistics."""

    iterations: int = Field(..., description="Number of iterations run")

    # Probability metrics
    probability_positive_npv: float = Field(
        ...,
        ge=0,
        le=1.0,
        description="Probability of NPV > 0"
    )

    # Central tendency
    mean_npv: float = Field(..., description="Mean NPV")
    median_npv: float = Field(..., description="Median NPV")
    std_npv: float = Field(..., description="Standard deviation of NPV")

    # Percentiles (for risk assessment)
    percentile_5: float = Field(..., description="5th percentile (downside)")
    percentile_25: float = Field(..., description="25th percentile")
    percentile_75: float = Field(..., description="75th percentile")
    percentile_95: float = Field(..., description="95th percentile (upside)")

    # Distribution data for visualization
    histogram_bins: List[float] = Field(..., description="Histogram bin edges")
    histogram_counts: List[int] = Field(..., description="Histogram counts per bin")


class SensitivityAnalysis(BaseModel):
    """Complete sensitivity analysis results."""

    # Tornado analysis (one-way sensitivity)
    tornado_results: List[TornadoVariable] = Field(
        default_factory=list,
        description="Tornado chart data (sorted by impact)"
    )

    # Monte Carlo simulation (multi-way sensitivity)
    monte_carlo: Optional[MonteCarloStatistics] = Field(
        None,
        description="Monte Carlo simulation results"
    )


# ============================================================================
# Main Request/Response Models
# ============================================================================


class FeasibilityRequest(BaseModel):
    """Request for economic feasibility analysis."""

    # Project parameters
    num_units: int = Field(..., gt=0, description="Number of residential units")
    avg_unit_size_sf: float = Field(..., gt=0, description="Average unit size (SF)")
    affordable_pct: float = Field(
        0.0,
        ge=0,
        le=1.0,
        description="Percentage of affordable units (e.g., 0.15 for 15%)"
    )

    # Economic assumptions
    assumptions: EconomicAssumptions = Field(
        default_factory=EconomicAssumptions,
        description="Economic assumptions (uses defaults if not provided)"
    )

    # Optional parcel-specific data
    parcel_apn: Optional[str] = Field(None, description="Assessor's Parcel Number")
    parcel_county: Optional[str] = Field(None, description="County for AMI lookups")
    existing_improvements_value: Optional[float] = Field(
        None,
        description="Value of existing improvements (if any)"
    )

    # Analysis options
    run_tornado_sensitivity: bool = Field(
        True,
        description="Include tornado sensitivity analysis"
    )
    tornado_variables: Optional[List[SensitivityVariable]] = Field(
        None,
        description="Variables to test (uses defaults if not provided)"
    )

    run_monte_carlo: bool = Field(
        False,
        description="Include Monte Carlo simulation (adds ~2 seconds)"
    )
    monte_carlo_config: Optional[MonteCarloConfig] = Field(
        None,
        description="Monte Carlo configuration (uses defaults if not provided)"
    )


class FeasibilityAnalysis(BaseModel):
    """Complete feasibility analysis response."""

    # Request echo
    request_summary: Dict[str, Any] = Field(..., description="Summary of request parameters")

    # Cost and revenue estimates
    cost_estimate: ConstructionCostEstimate = Field(..., description="Construction cost estimate")
    revenue_projection: RevenueProjection = Field(..., description="Revenue and NOI projection")

    # Cash flows
    cash_flows: List[CashFlowPeriod] = Field(..., description="Period-by-period cash flows")

    # Financial metrics
    financial_metrics: FinancialMetrics = Field(..., description="NPV, IRR, payback, PI")

    # Sensitivity analysis
    sensitivity_analysis: Optional[SensitivityAnalysis] = Field(
        None,
        description="Sensitivity analysis results (if requested)"
    )

    # Decision recommendation
    recommendation: str = Field(
        ...,
        description="Investment recommendation (PROCEED / MARGINAL / DO NOT PROCEED)"
    )
    recommendation_rationale: List[str] = Field(
        ...,
        description="Bullet points explaining recommendation"
    )

    # Audit trail
    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete audit trail of data sources and methodology"
    )

    # Metadata
    analysis_date: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


# ============================================================================
# Settings Model
# ============================================================================


class EconomicFeasibilitySettings(BaseModel):
    """Configuration settings for economic feasibility service."""

    # FRED (Federal Reserve Economic Data) API
    fred_api_key: Optional[str] = Field(None, description="FRED API key")
    fred_enabled: bool = Field(False, description="Enable live FRED data fetching")

    # Cost parameters (from config)
    ref_cost_per_sf: float = Field(350.0, description="Reference cost per SF (2025 baseline)")
    ref_ppi_date: str = Field("2025-01-01", description="Reference PPI date")
    ref_ppi_value: float = Field(140.0, description="Reference PPI value")

    # Soft cost defaults
    architecture_pct: float = Field(0.10, description="Architecture/Engineering %")
    legal_pct: float = Field(0.04, description="Legal/Consulting %")
    developer_fee_pct: float = Field(0.15, description="Developer fee %")
    contingency_pct: float = Field(0.12, description="Contingency %")

    # Financing
    construction_loan_spread: float = Field(0.025, description="Spread over 10Y Treasury")

    # Common area factor
    common_area_factor: float = Field(1.15, description="Common area multiplier (1.15 = 15% extra)")

    class Config:
        frozen = True  # Immutable
