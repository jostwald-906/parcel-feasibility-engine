"""
Economic feasibility analysis models.

Pydantic v2 models for comprehensive financial analysis including:
- Construction cost estimation
- Revenue projection
- NPV/IRR calculation
- Sensitivity analysis (tornado charts, Monte Carlo)

References:
- FRED Economic Data: https://fred.stlouisfed.org/series/DGS10
- RAND Corporation location factors
- California Prop 13 tax rate limits (1%)
- HCD income limits (AMI-based affordable rents)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException


# ==============================================================================
# Input Models - Economic Assumptions
# ==============================================================================


class EconomicAssumptions(BaseModel):
    """
    Input assumptions for feasibility calculations.

    Provides default values from industry standards and allows user customization.
    All rates are decimal (e.g., 0.12 = 12%).
    """

    # Discount rates
    discount_rate: float = Field(
        default=0.12,
        ge=0.01,
        le=0.30,
        description=(
            "Annual discount rate for NPV calculation. "
            "Default 12% = typical real estate investor hurdle rate. "
            "Can be derived from CAPM: discount_rate = risk_free_rate + beta × market_risk_premium + project_risk_premium"
        )
    )

    risk_free_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=0.10,
        description=(
            "Risk-free rate (10-year Treasury yield from FRED DGS10). "
            "Optional: If provided, used for CAPM calculation. "
            "Current typical: 0.035 (3.5%). "
            "Source: https://fred.stlouisfed.org/series/DGS10"
        )
    )

    market_risk_premium: float = Field(
        default=0.06,
        ge=0.0,
        le=0.15,
        description=(
            "Market risk premium (equity premium above risk-free rate). "
            "Default 6% = historical US equity premium. "
            "Used in CAPM: Expected Return = Rf + β(Rm - Rf)"
        )
    )

    project_risk_premium: float = Field(
        default=0.025,
        ge=0.0,
        le=0.10,
        description=(
            "Project-specific risk premium above market. "
            "Default 2.5% accounts for development risk, local market risk. "
            "Higher for new markets, complex projects, uncertain approvals."
        )
    )

    # Capitalization rate
    cap_rate: float = Field(
        default=0.045,
        ge=0.03,
        le=0.08,
        description=(
            "Capitalization rate for exit value calculation. "
            "Default 4.5% = typical for Class A multifamily in major CA markets. "
            "Range: 3% (urban core) to 8% (tertiary markets). "
            "Exit Value = Year 10 NOI / cap_rate"
        )
    )

    # Location and quality adjustments
    location_factor: float = Field(
        default=1.0,
        ge=0.5,
        le=2.5,
        description=(
            "Location cost multiplier based on RAND Corporation factors. "
            "1.0 = regional average, >1.0 = high-cost area, <1.0 = low-cost area. "
            "Santa Monica/West LA: ~1.25-1.35, San Francisco: ~1.4-1.5, "
            "Inland Empire: ~0.85-0.95. "
            "Source: RAND Corporation California construction cost indices"
        )
    )

    quality_factor: float = Field(
        default=1.0,
        ge=0.8,
        le=1.2,
        description=(
            "Quality adjustment factor for construction costs. "
            "1.0 = standard quality, 1.1-1.2 = high-end finishes, "
            "0.8-0.9 = basic/affordable finishes"
        )
    )

    # Operating assumptions
    vacancy_rate: float = Field(
        default=0.07,
        ge=0.0,
        le=0.20,
        description=(
            "Expected vacancy and collection loss rate. "
            "Default 7% = typical stabilized multifamily. "
            "Lower in supply-constrained markets (3-5%), "
            "higher for new construction lease-up (10-15%)"
        )
    )

    tax_rate: float = Field(
        default=0.012,
        ge=0.0,
        le=0.03,
        description=(
            "Annual property tax rate as % of assessed value. "
            "Default 1.2% = CA Prop 13 base (1%) + typical local assessments (0.2%). "
            "Prop 13 limits base rate to 1% + voter-approved local bonds. "
            "New construction assessed at market value."
        )
    )

    rent_growth_rate: float = Field(
        default=0.03,
        ge=0.0,
        le=0.10,
        description=(
            "Annual rent growth rate. "
            "Default 3% = long-term inflation + real growth. "
            "CA metros historically 2-4%, supply-constrained markets higher"
        )
    )

    expense_growth_rate: float = Field(
        default=0.025,
        ge=0.0,
        le=0.10,
        description=(
            "Annual operating expense growth rate. "
            "Default 2.5% = slightly below rent growth (operating leverage). "
            "Common range: 2-3.5%"
        )
    )

    # Cost escalation
    use_ccci: bool = Field(
        default=False,
        description=(
            "Use Chemical Engineering Cost Construction Index (CCCI) for cost escalation. "
            "If True, applies recent construction cost inflation (2020-2025: ~25%). "
            "If False, uses quality_factor and location_factor only."
        )
    )

    # Documentation
    source_references: Dict[str, str] = Field(
        default_factory=lambda: {
            "risk_free_rate": "FRED DGS10 (10-Year Treasury)",
            "market_risk_premium": "Ibbotson SBBI historical equity premium",
            "location_factor": "RAND Corporation California cost indices",
            "tax_rate": "CA Proposition 13 (1978) + local assessments",
            "cap_rate": "CBRE/CoStar multifamily cap rate surveys",
        },
        description="Data source references for transparency and audit trail"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "discount_rate": 0.12,
                "risk_free_rate": 0.035,
                "market_risk_premium": 0.06,
                "project_risk_premium": 0.025,
                "cap_rate": 0.045,
                "location_factor": 1.3,
                "quality_factor": 1.0,
                "vacancy_rate": 0.07,
                "tax_rate": 0.012,
                "rent_growth_rate": 0.03,
                "expense_growth_rate": 0.025,
                "use_ccci": False,
                "source_references": {
                    "location_factor": "RAND Corporation (Santa Monica: 1.3)",
                    "cap_rate": "CBRE Q1 2025 LA multifamily cap rates (4.5%)"
                }
            }
        }


# ==============================================================================
# Construction Cost Models
# ==============================================================================


class ConstructionInputs(BaseModel):
    """
    Inputs for construction cost estimation.

    Used by cost estimator service to calculate total development cost.
    """

    total_buildable_sf: float = Field(
        ...,
        gt=0,
        description="Total buildable square footage"
    )

    num_units: int = Field(
        ...,
        gt=0,
        description="Number of residential units"
    )

    construction_type: str = Field(
        default="wood_frame",
        description=(
            "Construction type for cost estimation. "
            "Options: 'wood_frame' (Type V, <4 stories), "
            "'concrete' (Type I, podium/mid-rise), "
            "'steel' (Type II, high-rise). "
            "Affects base cost per SF."
        )
    )

    construction_duration_months: int = Field(
        ...,
        gt=0,
        le=60,
        description="Construction duration in months"
    )

    predevelopment_duration_months: int = Field(
        ...,
        gt=0,
        le=48,
        description="Predevelopment duration (entitlements, design, permitting) in months"
    )

    location_factor: float = Field(
        default=1.0,
        ge=0.5,
        le=2.5,
        description="Location cost multiplier (from EconomicAssumptions)"
    )

    permit_fees_per_unit: float = Field(
        default=15000.0,
        ge=0,
        description=(
            "Municipal permit and impact fees per unit. "
            "Varies widely: $5k-$50k+ per unit depending on city. "
            "Santa Monica/coastal cities: $20k-$40k typical"
        )
    )

    use_wage_adjustment: bool = Field(
        default=False,
        description=(
            "Apply wage adjustment for prevailing wage requirements. "
            "If True, adds 20-30% labor cost premium for AB 2011/SB 35 projects "
            "with skilled & trained workforce requirements."
        )
    )

    @field_validator("construction_type")
    @classmethod
    def validate_construction_type(cls, v: str) -> str:
        """Validate construction type is recognized."""
        valid_types = {"wood_frame", "concrete", "steel"}
        if v not in valid_types:
            raise ValueError(f"construction_type must be one of {valid_types}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "total_buildable_sf": 25000.0,
                "num_units": 30,
                "construction_type": "wood_frame",
                "construction_duration_months": 18,
                "predevelopment_duration_months": 12,
                "location_factor": 1.3,
                "permit_fees_per_unit": 25000.0,
                "use_wage_adjustment": True
            }
        }


class ConstructionCostEstimate(BaseModel):
    """
    Output from construction cost estimator.

    Provides detailed cost breakdown for development budget.
    """

    # Cost breakdown
    hard_costs: float = Field(..., ge=0, description="Direct construction costs (labor + materials)")
    soft_costs: float = Field(..., ge=0, description="Total soft costs (A&E + permits + financing + legal + contingency)")

    # Soft cost details
    architecture_engineering: float = Field(..., ge=0, description="Architecture and engineering fees (~5-8% of hard costs)")
    permits_and_fees: float = Field(..., ge=0, description="Permit fees and development impact fees")
    construction_financing: float = Field(..., ge=0, description="Construction loan interest and fees")
    legal_consulting: float = Field(..., ge=0, description="Legal, consulting, and environmental reports")
    contingency: float = Field(..., ge=0, description="Construction contingency (~5-10% of hard costs)")

    # Total costs
    total_cost: float = Field(..., ge=0, description="Total development cost (hard + soft)")
    cost_per_unit: float = Field(..., ge=0, description="Total cost per residential unit")
    cost_per_sf: float = Field(..., ge=0, description="Total cost per buildable square foot")

    # Escalation factors
    escalation_factors: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Cost escalation factors applied. "
            "Keys: 'materials_index', 'labor_index', 'wage_premium', 'location_factor'"
        )
    )

    # Source notes
    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Source notes for transparency. "
            "Keys: 'base_cost_source', 'construction_type', 'assumptions', 'date'"
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "hard_costs": 6000000.0,
                "soft_costs": 1500000.0,
                "architecture_engineering": 420000.0,
                "permits_and_fees": 450000.0,
                "construction_financing": 300000.0,
                "legal_consulting": 180000.0,
                "contingency": 450000.0,
                "total_cost": 7500000.0,
                "cost_per_unit": 250000.0,
                "cost_per_sf": 300.0,
                "escalation_factors": {
                    "materials_index": 1.15,
                    "labor_index": 1.10,
                    "wage_premium": 1.25,
                    "location_factor": 1.3
                },
                "source_notes": {
                    "base_cost_source": "RSMeans 2025 multifamily wood frame",
                    "construction_type": "wood_frame",
                    "assumptions": "30 units, Santa Monica location, prevailing wage",
                    "date": "2025-01-15"
                }
            }
        }


# ==============================================================================
# Revenue Projection Models
# ==============================================================================


class RevenueInputs(BaseModel):
    """
    Inputs for revenue estimation.

    Uses HUD Fair Market Rents (FMR) or Small Area FMR (SAFMR) + AMI limits.
    """

    parcel_zip: str = Field(
        ...,
        pattern=r"^\d{5}$",
        description="5-digit ZIP code for SAFMR lookup"
    )

    county: str = Field(
        ...,
        description="County name for AMI limit lookup (e.g., 'Los Angeles', 'San Francisco')"
    )

    market_units: int = Field(
        ...,
        ge=0,
        description="Number of market-rate units"
    )

    affordable_units: int = Field(
        ...,
        ge=0,
        description="Number of affordable units"
    )

    unit_mix: Dict[int, int] = Field(
        ...,
        description=(
            "Unit mix by bedroom count. "
            "Keys: bedrooms (0=studio, 1, 2, 3, 4), Values: unit count. "
            "Example: {0: 5, 1: 15, 2: 10} = 5 studios, 15 1BR, 10 2BR"
        )
    )

    use_safmr: bool = Field(
        default=True,
        description=(
            "Use Small Area Fair Market Rent (SAFMR) instead of metro-wide FMR. "
            "SAFMR provides ZIP-code level granularity (recommended for urban areas). "
            "Source: HUD FMR/SAFMR datasets"
        )
    )

    quality_factor: float = Field(
        default=1.0,
        ge=0.8,
        le=1.3,
        description=(
            "Rent quality adjustment. "
            "1.0 = market average, 1.1-1.3 = luxury/new construction premium, "
            "0.8-0.95 = workforce/moderate-quality"
        )
    )

    @field_validator("unit_mix")
    @classmethod
    def validate_unit_mix(cls, v: Dict[int, int]) -> Dict[int, int]:
        """Validate unit mix has valid bedroom counts."""
        for bedrooms in v.keys():
            if bedrooms < 0 or bedrooms > 5:
                raise ValueError(f"Bedroom count must be 0-5, got {bedrooms}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "parcel_zip": "90401",
                "county": "Los Angeles",
                "market_units": 25,
                "affordable_units": 5,
                "unit_mix": {
                    0: 5,
                    1: 15,
                    2: 8,
                    3: 2
                },
                "use_safmr": True,
                "quality_factor": 1.1
            }
        }


class RevenueProjection(BaseModel):
    """
    Output from revenue estimator.

    Provides annual revenue, expenses, and NOI projection.
    """

    # Gross income
    annual_gross_income: float = Field(..., ge=0, description="Total annual gross rental income")
    vacancy_loss: float = Field(..., ge=0, description="Vacancy and collection loss")
    effective_gross_income: float = Field(..., ge=0, description="Effective gross income (gross - vacancy)")

    # Expenses
    operating_expenses: float = Field(..., ge=0, description="Annual operating expenses")

    # Net operating income
    annual_noi: float = Field(..., description="Annual net operating income (EGI - OpEx)")
    noi_per_unit: float = Field(..., description="NOI per unit (annual)")

    # Detailed rent rolls
    market_rent_roll: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Market-rate rent roll by unit type. "
            "Keys: '0BR', '1BR', '2BR', etc. Values: monthly rent per unit"
        )
    )

    affordable_rent_roll: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Affordable rent roll by unit type and AMI %. "
            "Keys: '0BR_50AMI', '1BR_60AMI', etc. Values: monthly rent per unit"
        )
    )

    # Expense breakdown
    expense_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Operating expense breakdown. "
            "Keys: 'property_management', 'maintenance', 'utilities', 'insurance', "
            "'property_tax', 'reserves', 'other'. Values: annual cost"
        )
    )

    # Source notes
    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Source notes for transparency. "
            "Keys: 'fmr_source', 'ami_source', 'opex_basis', 'date'"
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "annual_gross_income": 900000.0,
                "vacancy_loss": 63000.0,
                "effective_gross_income": 837000.0,
                "operating_expenses": 270000.0,
                "annual_noi": 567000.0,
                "noi_per_unit": 18900.0,
                "market_rent_roll": {
                    "0BR": 2200.0,
                    "1BR": 2800.0,
                    "2BR": 3600.0,
                    "3BR": 4500.0
                },
                "affordable_rent_roll": {
                    "1BR_50AMI": 1200.0,
                    "2BR_60AMI": 1450.0
                },
                "expense_breakdown": {
                    "property_management": 45000.0,
                    "maintenance": 90000.0,
                    "utilities": 36000.0,
                    "insurance": 18000.0,
                    "property_tax": 72000.0,
                    "reserves": 9000.0
                },
                "source_notes": {
                    "fmr_source": "HUD SAFMR 2025 ZIP 90401",
                    "ami_source": "HCD 2025 Los Angeles County",
                    "opex_basis": "Industry standard 40% of EGI",
                    "date": "2025-01-15"
                }
            }
        }


# ==============================================================================
# Timeline and Cash Flow Models
# ==============================================================================


class TimelineInputs(BaseModel):
    """Development timeline for cash flow projection."""

    predevelopment_months: int = Field(
        ...,
        gt=0,
        le=48,
        description="Predevelopment duration (entitlements, design, permitting)"
    )

    construction_months: int = Field(
        ...,
        gt=0,
        le=60,
        description="Construction duration"
    )

    lease_up_months: int = Field(
        ...,
        gt=0,
        le=24,
        description="Lease-up period to reach stabilized occupancy"
    )

    operating_years: int = Field(
        default=10,
        gt=0,
        le=30,
        description="Operating period for cash flow projection (default 10 years for exit)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "predevelopment_months": 12,
                "construction_months": 18,
                "lease_up_months": 6,
                "operating_years": 10
            }
        }


class CashFlow(BaseModel):
    """Period-by-period cash flow."""

    period: int = Field(..., description="Period number (0 = start)")
    period_type: str = Field(
        ...,
        description="Period type: 'predevelopment', 'construction', 'lease_up', 'operations'"
    )

    revenue: float = Field(default=0.0, description="Revenue in period")
    operating_expenses: float = Field(default=0.0, ge=0, description="Operating expenses in period")
    capital_expenditure: float = Field(default=0.0, ge=0, description="Capital expenditure in period")

    net_cash_flow: float = Field(..., description="Net cash flow (revenue - opex - capex)")
    cumulative_cash_flow: float = Field(..., description="Cumulative cash flow from period 0")

    @field_validator("period_type")
    @classmethod
    def validate_period_type(cls, v: str) -> str:
        """Validate period type."""
        valid_types = {"predevelopment", "construction", "lease_up", "operations"}
        if v not in valid_types:
            raise ValueError(f"period_type must be one of {valid_types}")
        return v


# ==============================================================================
# Financial Metrics Models
# ==============================================================================


class FinancialMetrics(BaseModel):
    """
    Core financial analysis outputs.

    Includes NPV, IRR, payback period, and exit value.
    """

    npv: float = Field(
        ...,
        description=(
            "Net Present Value at discount rate. "
            "NPV > 0 indicates project is feasible. "
            "Higher NPV = better returns."
        )
    )

    irr: float = Field(
        ...,
        description=(
            "Internal Rate of Return (annualized). "
            "IRR > discount_rate indicates project exceeds hurdle. "
            "Expressed as decimal (0.15 = 15% IRR)"
        )
    )

    payback_period_years: float = Field(
        ...,
        ge=0,
        description=(
            "Payback period in years (when cumulative cash flow turns positive). "
            "Shorter is better for risk mitigation."
        )
    )

    profitability_index: float = Field(
        ...,
        description=(
            "Profitability Index (NPV / Initial Investment). "
            "PI > 1.0 indicates positive NPV. "
            "Useful for comparing projects of different scales."
        )
    )

    return_on_cost: float = Field(
        ...,
        description=(
            "Return on Cost (Stabilized Year 1 NOI / Total Development Cost). "
            "Expressed as decimal (0.06 = 6% RoC). "
            "Compare to cap_rate for value creation analysis."
        )
    )

    exit_value: float = Field(
        ...,
        ge=0,
        description=(
            "Exit value at end of holding period. "
            "Calculated as: Year N NOI / cap_rate. "
            "Assumes sale at stabilized operations."
        )
    )

    total_cash_flows: List[CashFlow] = Field(
        default_factory=list,
        description="Complete cash flow schedule by period"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npv": 2500000.0,
                "irr": 0.18,
                "payback_period_years": 7.5,
                "profitability_index": 1.33,
                "return_on_cost": 0.075,
                "exit_value": 12600000.0,
                "total_cash_flows": [
                    {
                        "period": 0,
                        "period_type": "predevelopment",
                        "revenue": 0.0,
                        "operating_expenses": 0.0,
                        "capital_expenditure": 500000.0,
                        "net_cash_flow": -500000.0,
                        "cumulative_cash_flow": -500000.0
                    }
                ]
            }
        }


# ==============================================================================
# Sensitivity Analysis Models
# ==============================================================================


class SensitivityInput(BaseModel):
    """Variables to test in sensitivity analysis."""

    variable_name: str = Field(
        ...,
        description=(
            "Variable to test. "
            "Options: 'cost_per_sf', 'rent_per_sf', 'cap_rate', 'vacancy_rate', "
            "'construction_duration', 'discount_rate'"
        )
    )

    base_value: float = Field(..., description="Base case value")

    delta_percent: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description=(
            "Percentage change to test (e.g., 0.20 = ±20%). "
            "Creates upside and downside scenarios."
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "variable_name": "cost_per_sf",
                "base_value": 300.0,
                "delta_percent": 0.20
            }
        }


class TornadoResult(BaseModel):
    """One-way sensitivity analysis result (tornado chart bar)."""

    variable: str = Field(..., description="Variable tested")
    downside_npv: float = Field(..., description="NPV with -delta_percent change")
    upside_npv: float = Field(..., description="NPV with +delta_percent change")
    impact: float = Field(
        ...,
        description=(
            "Absolute NPV impact (max NPV - min NPV). "
            "Larger impact = more sensitive variable. "
            "Used for sorting tornado chart."
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "variable": "cost_per_sf",
                "downside_npv": 3500000.0,
                "upside_npv": 1500000.0,
                "impact": 2000000.0
            }
        }


class MonteCarloInputs(BaseModel):
    """Monte Carlo simulation parameters."""

    iterations: int = Field(
        default=10000,
        ge=1000,
        le=100000,
        description="Number of Monte Carlo iterations"
    )

    # Cost uncertainty (normal distribution)
    cost_per_sf_std: float = Field(
        ...,
        ge=0,
        description="Standard deviation of cost per SF (e.g., 30 for ±$30/SF 1-sigma)"
    )

    # Revenue uncertainty (normal distribution)
    rent_growth_std: float = Field(
        ...,
        ge=0,
        le=0.10,
        description="Standard deviation of rent growth rate (e.g., 0.01 = ±1% 1-sigma)"
    )

    # Exit cap rate uncertainty (triangular distribution)
    cap_rate_min: float = Field(..., ge=0.01, le=0.15, description="Minimum cap rate")
    cap_rate_mode: float = Field(..., ge=0.01, le=0.15, description="Most likely cap rate")
    cap_rate_max: float = Field(..., ge=0.01, le=0.15, description="Maximum cap rate")

    # Timeline uncertainty (normal distribution)
    delay_months_mean: float = Field(
        default=0.0,
        ge=-12,
        le=24,
        description="Mean construction delay in months (0 = on schedule)"
    )

    delay_months_std: float = Field(
        default=3.0,
        ge=0,
        le=12,
        description="Standard deviation of construction delay"
    )

    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducible testing"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "iterations": 10000,
                "cost_per_sf_std": 30.0,
                "rent_growth_std": 0.01,
                "cap_rate_min": 0.04,
                "cap_rate_mode": 0.045,
                "cap_rate_max": 0.06,
                "delay_months_mean": 0.0,
                "delay_months_std": 3.0,
                "random_seed": 42
            }
        }


class MonteCarloResult(BaseModel):
    """Monte Carlo simulation output."""

    probability_npv_positive: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Probability of NPV > 0 (project is feasible). "
            "Expressed as decimal (0.85 = 85% probability)"
        )
    )

    mean_npv: float = Field(..., description="Mean NPV across all iterations")
    std_npv: float = Field(..., ge=0, description="Standard deviation of NPV")

    percentiles: Dict[str, float] = Field(
        ...,
        description=(
            "NPV percentiles for risk assessment. "
            "Keys: 'p10', 'p25', 'p50' (median), 'p75', 'p90'"
        )
    )

    histogram_bins: List[float] = Field(
        default_factory=list,
        description="Histogram bin edges for NPV distribution visualization"
    )

    histogram_counts: List[int] = Field(
        default_factory=list,
        description="Histogram counts per bin"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "probability_npv_positive": 0.87,
                "mean_npv": 2300000.0,
                "std_npv": 800000.0,
                "percentiles": {
                    "p10": 800000.0,
                    "p25": 1500000.0,
                    "p50": 2250000.0,
                    "p75": 3100000.0,
                    "p90": 3800000.0
                },
                "histogram_bins": [-1000000.0, 0.0, 1000000.0, 2000000.0, 3000000.0, 4000000.0],
                "histogram_counts": [130, 1200, 3500, 3800, 1370]
            }
        }


class SensitivityAnalysis(BaseModel):
    """Combined sensitivity analysis results."""

    tornado: List[TornadoResult] = Field(
        default_factory=list,
        description=(
            "Tornado chart results (one-way sensitivity). "
            "Sorted by impact (descending) for visualization."
        )
    )

    monte_carlo: MonteCarloResult = Field(
        ...,
        description="Monte Carlo simulation results"
    )


# ==============================================================================
# Complete Feasibility Analysis Models
# ==============================================================================


class FeasibilityAnalysis(BaseModel):
    """
    Complete feasibility analysis output.

    Integrates construction costs, revenue, financial metrics, and risk analysis.
    """

    scenario_name: str = Field(..., description="Development scenario name")
    parcel_apn: str = Field(..., description="Parcel APN")

    # Cost and revenue
    construction_cost_estimate: ConstructionCostEstimate = Field(
        ...,
        description="Construction cost breakdown"
    )

    revenue_projection: RevenueProjection = Field(
        ...,
        description="Annual revenue and NOI projection"
    )

    # Financial metrics
    financial_metrics: FinancialMetrics = Field(
        ...,
        description="NPV, IRR, payback, and cash flows"
    )

    # Risk analysis
    sensitivity_analysis: SensitivityAnalysis = Field(
        ...,
        description="Tornado chart and Monte Carlo results"
    )

    # Decision support
    decision_recommendation: str = Field(
        ...,
        description=(
            "Go/No-Go recommendation. "
            "Options: 'Recommended - Strong Feasibility', "
            "'Recommended with Caution', "
            "'Not Recommended', "
            "'Further Analysis Required'"
        )
    )

    # Audit trail
    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Comprehensive source notes and assumptions. "
            "Keys: 'cost_sources', 'revenue_sources', 'assumptions', 'caveats'"
        )
    )

    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

        json_schema_extra = {
            "example": {
                "scenario_name": "SB 9 Lot Split + Density Bonus",
                "parcel_apn": "4293-021-012",
                "construction_cost_estimate": {
                    "total_cost": 7500000.0,
                    "cost_per_unit": 250000.0,
                    "cost_per_sf": 300.0
                },
                "revenue_projection": {
                    "annual_noi": 567000.0,
                    "noi_per_unit": 18900.0
                },
                "financial_metrics": {
                    "npv": 2500000.0,
                    "irr": 0.18,
                    "payback_period_years": 7.5
                },
                "sensitivity_analysis": {
                    "monte_carlo": {
                        "probability_npv_positive": 0.87,
                        "mean_npv": 2300000.0
                    }
                },
                "decision_recommendation": "Recommended - Strong Feasibility",
                "source_notes": {
                    "cost_sources": ["RSMeans 2025", "RAND location factor"],
                    "revenue_sources": ["HUD SAFMR 2025", "HCD AMI limits"],
                    "assumptions": "Prevailing wage, 12-month entitlement, 18-month construction",
                    "caveats": "Subject to approvals, market conditions"
                },
                "analysis_timestamp": "2025-01-15T10:30:00"
            }
        }


class FeasibilityRequest(BaseModel):
    """
    API request model for feasibility analysis.

    Provides all inputs needed to run complete analysis.
    """

    parcel_apn: str = Field(..., description="Parcel APN")
    scenario_name: str = Field(..., description="Development scenario name")

    # Development parameters
    units: int = Field(..., gt=0, description="Number of units")
    buildable_sf: float = Field(..., gt=0, description="Buildable square footage")

    # Timeline
    timeline: TimelineInputs = Field(..., description="Development timeline")

    # Economic assumptions
    assumptions: EconomicAssumptions = Field(
        default_factory=EconomicAssumptions,
        description="Economic assumptions (uses defaults if not provided)"
    )

    # Revenue inputs (optional - will use defaults if not provided)
    revenue_inputs: Optional[RevenueInputs] = Field(
        None,
        description="Revenue inputs (if not provided, will be derived from parcel location)"
    )

    # Analysis options
    run_sensitivity: bool = Field(
        default=True,
        description="Run sensitivity analysis (tornado + Monte Carlo)"
    )

    run_monte_carlo: bool = Field(
        default=True,
        description="Run Monte Carlo simulation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "parcel_apn": "4293-021-012",
                "scenario_name": "SB 9 Lot Split + Density Bonus",
                "units": 30,
                "buildable_sf": 25000.0,
                "timeline": {
                    "predevelopment_months": 12,
                    "construction_months": 18,
                    "lease_up_months": 6,
                    "operating_years": 10
                },
                "assumptions": {
                    "discount_rate": 0.12,
                    "location_factor": 1.3
                },
                "run_sensitivity": True,
                "run_monte_carlo": True
            }
        }


# ==============================================================================
# API Response Models
# ==============================================================================


class CostIndicesResponse(BaseModel):
    """Response model for current cost indices endpoint."""

    as_of_date: str = Field(..., description="Date of latest data")
    materials_ppi: float = Field(..., description="Construction Materials PPI (WPUSI012011)")
    construction_wages_eci: Optional[float] = Field(None, description="Construction Wages ECI (ECICONWAG)")
    risk_free_rate_pct: float = Field(..., description="Risk-free rate percentage (DGS10)")
    data_source: str = Field(default="Federal Reserve Economic Data (FRED)", description="Data source")
    series_ids: Dict[str, str] = Field(..., description="FRED series IDs used")


class MarketRentResponse(BaseModel):
    """Response model for market rents endpoint."""

    zip_code: str = Field(..., description="ZIP code")
    year: int = Field(..., description="FMR year")
    rents_by_bedroom: Dict[str, float] = Field(..., description="Rents by bedroom count (0-4)")
    fmr_type: str = Field(..., description="FMR or SAFMR")
    metro_area: str = Field(..., description="Metro area name")
    data_source: str = Field(..., description="Data source (HUD FMR API)")
    effective_date: str = Field(..., description="Effective date of FMR data")


class ValidationResponse(BaseModel):
    """Response model for assumptions validation endpoint."""

    is_valid: bool = Field(..., description="Whether assumptions are valid")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    recommendations: List[str] = Field(default_factory=list, description="Recommended improvements")


# ==============================================================================
# Custom Exceptions
# ==============================================================================


class DataSourceError(HTTPException):
    """External API unavailable (FRED, HUD)."""

    def __init__(self, detail: str):
        super().__init__(status_code=503, detail=detail)


class InvalidAssumptionError(HTTPException):
    """Invalid economic assumptions."""

    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


class CalculationError(HTTPException):
    """Financial calculation failed."""

    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=detail)
