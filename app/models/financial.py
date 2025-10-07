"""
Financial analysis models.

Models for construction cost estimation, economic assumptions, and financial inputs.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal


class ConstructionInputs(BaseModel):
    """Construction project inputs for cost estimation."""

    buildable_sqft: float = Field(..., gt=0, description="Total buildable square feet")
    num_units: int = Field(..., gt=0, description="Number of residential units")
    construction_type: Literal["wood_frame", "concrete", "steel"] = Field(
        "wood_frame", description="Construction type (determines cost multiplier)"
    )
    location_factor: float = Field(
        2.3, gt=0, description="Location cost multiplier (default 2.3 = CA avg per RAND study)"
    )
    permit_fees_per_unit: float = Field(
        5000.0, ge=0, description="Municipal permit fees per unit (dollars)"
    )
    construction_duration_months: int = Field(
        18, gt=0, description="Expected construction duration in months"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "buildable_sqft": 10000.0,
                "num_units": 10,
                "construction_type": "wood_frame",
                "location_factor": 2.3,
                "permit_fees_per_unit": 5000.0,
                "construction_duration_months": 18,
            }
        }


class EconomicAssumptions(BaseModel):
    """Economic assumptions for cost estimation."""

    use_wage_adjustment: bool = Field(
        False, description="Apply wage escalation factor (FRED ECICONWAG)"
    )
    use_ccci: bool = Field(
        False, description="Use CCCI escalation instead of FRED PPI (if available)"
    )
    architecture_pct: Optional[float] = Field(
        None, ge=0, le=1, description="Architecture/Engineering as % of hard cost (default from settings)"
    )
    legal_pct: Optional[float] = Field(
        None, ge=0, le=1, description="Legal/Consulting as % of hard cost (default from settings)"
    )
    developer_fee_pct: Optional[float] = Field(
        None, ge=0, le=1, description="Developer fee as % of total cost (default from settings)"
    )
    contingency_pct: Optional[float] = Field(
        None, ge=0, le=1, description="Contingency as % of hard+soft (default from settings)"
    )
    construction_loan_spread: Optional[float] = Field(
        None, ge=0, description="Construction loan spread over 10Y Treasury (default 2.5%)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "use_wage_adjustment": False,
                "use_ccci": False,
                "architecture_pct": 0.10,
                "legal_pct": 0.04,
                "developer_fee_pct": 0.15,
                "contingency_pct": 0.12,
                "construction_loan_spread": 0.025,
            }
        }


class HardCostBreakdown(BaseModel):
    """Hard construction costs breakdown."""

    base_cost_per_sf: float = Field(..., description="Reference base cost per SF (2025 baseline)")
    materials_escalation_factor: float = Field(..., description="PPI-based materials escalation")
    wage_escalation_factor: float = Field(1.0, description="Wage escalation factor (if enabled)")
    construction_type_factor: float = Field(..., description="Construction type multiplier")
    location_factor: float = Field(..., description="Location cost multiplier")
    common_area_factor: float = Field(..., description="Common area addition (e.g., 1.15 = +15%)")
    total_sf: float = Field(..., description="Total SF including common area")
    total_hard_cost: float = Field(..., description="Total hard construction cost")


class SoftCostBreakdown(BaseModel):
    """Soft costs breakdown."""

    architecture_engineering: float = Field(..., description="Architecture & Engineering fees")
    permits_fees: float = Field(..., description="Permits & municipal fees")
    construction_financing: float = Field(..., description="Construction loan interest")
    legal_consulting: float = Field(..., description="Legal & consulting fees")
    developer_fee: float = Field(..., description="Developer fee")
    total_soft_cost: float = Field(..., description="Total soft costs")


class ConstructionCostEstimate(BaseModel):
    """Comprehensive construction cost estimate with detailed breakdown."""

    # Summary
    total_cost: float = Field(..., description="Total construction cost (hard + soft + contingency)")
    cost_per_unit: float = Field(..., description="Cost per residential unit")
    cost_per_buildable_sf: float = Field(..., description="Cost per buildable square foot")

    # Breakdowns
    hard_costs: HardCostBreakdown = Field(..., description="Hard costs breakdown")
    soft_costs: SoftCostBreakdown = Field(..., description="Soft costs breakdown")

    # Contingency
    contingency_amount: float = Field(..., description="Contingency reserve")
    contingency_pct: float = Field(..., description="Contingency percentage applied")

    # Source notes for transparency
    source_notes: Dict[str, str] = Field(..., description="Data source notes with dates/references")

    class Config:
        json_schema_extra = {
            "example": {
                "total_cost": 4500000.0,
                "cost_per_unit": 450000.0,
                "cost_per_buildable_sf": 450.0,
                "hard_costs": {
                    "base_cost_per_sf": 350.0,
                    "materials_escalation_factor": 1.12,
                    "wage_escalation_factor": 1.0,
                    "construction_type_factor": 1.0,
                    "location_factor": 2.3,
                    "common_area_factor": 1.15,
                    "total_sf": 11500.0,
                    "total_hard_cost": 3220000.0,
                },
                "soft_costs": {
                    "architecture_engineering": 322000.0,
                    "permits_fees": 50000.0,
                    "construction_financing": 104000.0,
                    "legal_consulting": 128800.0,
                    "developer_fee": 572580.0,
                    "total_soft_cost": 1177380.0,
                },
                "contingency_amount": 527686.0,
                "contingency_pct": 0.12,
                "source_notes": {
                    "materials_ppi_series": "WPUSI012011 @ 140.5 (FRED 2025-01-15)",
                    "base_cost_per_sf": "$350 (2025 US baseline)",
                    "location_factor": "2.3 (user input, RAND CA avg 2.3x)",
                },
            }
        }
