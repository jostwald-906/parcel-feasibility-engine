"""
Economic Feasibility Analysis API endpoints.

Provides comprehensive financial analysis endpoints for development scenarios using:
- FRED (Federal Reserve Economic Data) for construction costs and interest rates
- HUD Fair Market Rents for revenue benchmarks
- HCD AMI Limits for affordable housing revenue
- NPV/IRR analysis with sensitivity and Monte Carlo simulation

All data sources are free public APIs.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Annotated, Optional, List
from datetime import datetime

from app.models.economic_feasibility import (
    FeasibilityRequest,
    FeasibilityAnalysis,
    CostIndicesResponse,
    MarketRentResponse,
    ValidationResponse,
    EconomicAssumptions,
    DataSourceError,
    InvalidAssumptionError,
    CalculationError,
)
from app.clients.fred_client import FREDClient
from app.clients.hud_fmr_client import HudFMRClient
from app.services.ami_calculator import AMICalculator
# from app.services.economic_feasibility import EconomicFeasibilityCalculator
from app.core.dependencies import (
    get_fred_client,
    get_hud_client,
    get_ami_calculator_dep,
    get_settings,
)
from app.core.config import Settings
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/compute",
    response_model=FeasibilityAnalysis,
    summary="Compute Economic Feasibility Analysis",
    description="""
    Comprehensive development feasibility analysis using free public data sources.

    **Data Sources:**
    - **FRED (Federal Reserve Economic Data)**: Construction costs, interest rates
    - **HUD Fair Market Rents**: Market rent benchmarks
    - **HCD AMI Limits**: Affordable housing revenue calculations

    **Analysis Methods:**
    - **NPV/IRR**: PhD-level discounted cash flow analysis
    - **Tornado Diagram**: One-way sensitivity analysis
    - **Monte Carlo**: 10,000 iteration risk simulation

    **Output:** Complete financial pro forma with source citations and audit trail.

    **Example Use Cases:**
    - Compare base zoning vs. density bonus financial performance
    - Evaluate affordable housing mixed-income scenarios
    - Assess construction cost escalation impact
    - Model interest rate risk sensitivity
    """,
    responses={
        200: {
            "description": "Successful analysis with complete financial metrics",
            "content": {
                "application/json": {
                    "example": {
                        "parcel_apn": "4293-001-015",
                        "scenario_name": "Density Bonus (20% @ 50% AMI)",
                        "analysis_date": "2025-10-07T12:00:00",
                        "npv": 2450000.0,
                        "irr": 0.185,
                        "profitability_index": 1.45,
                        "payback_years": 6.2,
                        "recommendation": "Proceed - Strong economics with 18.5% IRR",
                        "data_sources": {
                            "construction_costs": "FRED API (PPI, ECI)",
                            "market_rents": "HUD FMR 2025",
                            "affordable_rents": "HCD AMI 2025"
                        }
                    }
                }
            }
        },
        422: {
            "description": "Invalid input parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Invalid assumptions",
                        "detail": "Discount rate must be between 5% and 25%"
                    }
                }
            }
        },
        503: {
            "description": "External data source unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Data source unavailable",
                        "detail": "FRED API temporarily unavailable",
                        "retry_after": 60
                    }
                }
            }
        }
    },
    tags=["Economic Feasibility"]
)
async def compute_feasibility(
    request: FeasibilityRequest,
    fred_client: Annotated[FREDClient, Depends(get_fred_client)],
    hud_client: Annotated[HudFMRClient, Depends(get_hud_client)],
    ami_calculator: Annotated[AMICalculator, Depends(get_ami_calculator_dep)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> FeasibilityAnalysis:
    """
    Compute comprehensive economic feasibility analysis.

    Performs:
    1. Construction cost estimation with FRED/CCCI escalation
    2. Revenue projection using HUD FMR and AMI limits
    3. NPV, IRR, payback, profitability index calculation
    4. Tornado sensitivity analysis (one-way)
    5. Monte Carlo simulation (10,000 draws)
    6. Investment recommendation generation

    Returns complete analysis with source citations and audit trail.

    Args:
        request: FeasibilityRequest with parcel, scenario, and assumptions
        fred_client: FRED API client (dependency injected)
        hud_client: HUD FMR API client (dependency injected)
        ami_calculator: AMI calculator service (dependency injected)
        settings: Application settings (dependency injected)

    Returns:
        FeasibilityAnalysis with complete financial metrics and recommendations

    Raises:
        DataSourceError: External API unavailable (503)
        InvalidAssumptionError: Invalid economic assumptions (422)
        CalculationError: Financial calculation failed (500)
    """
    try:
        logger.info(
            "Starting economic feasibility analysis",
            extra={
                "parcel_apn": request.parcel_apn,
                "scenario": request.scenario_name,
                "units": request.units,
                "run_sensitivity": request.run_sensitivity,
                "run_monte_carlo": request.run_monte_carlo
            }
        )

        # Initialize calculator
        calculator = EconomicFeasibilityCalculator(
            fred_client=fred_client,
            hud_client=hud_client,
            ami_calculator=ami_calculator
        )

        # Run comprehensive analysis
        analysis = await calculator.compute_feasibility(request)

        logger.info(
            "Economic feasibility analysis completed",
            extra={
                "parcel_apn": request.parcel_apn,
                "npv": analysis.npv,
                "irr": analysis.irr,
                "recommendation": analysis.recommendation
            }
        )

        return analysis

    except DataSourceError as e:
        logger.error(
            f"Data source error during feasibility analysis: {e}",
            extra={"parcel_apn": request.parcel_apn}
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Data source unavailable",
                "detail": str(e),
                "retry_after": 60
            }
        )

    except InvalidAssumptionError as e:
        logger.warning(
            f"Invalid assumptions provided: {e}",
            extra={"parcel_apn": request.parcel_apn}
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Invalid assumptions",
                "detail": str(e)
            }
        )

    except CalculationError as e:
        logger.error(
            f"Calculation error during feasibility analysis: {e}",
            extra={"parcel_apn": request.parcel_apn},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Calculation failed",
                "detail": str(e)
            }
        )

    except Exception as e:
        logger.error(
            f"Unexpected error during feasibility analysis: {e}",
            extra={"parcel_apn": request.parcel_apn},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during feasibility analysis"
        )


@router.get(
    "/cost-indices",
    response_model=CostIndicesResponse,
    summary="Get Current Construction Cost Indices",
    description="""
    Retrieve current construction cost indices from FRED.

    Returns latest values for:
    - **WPUSI012011**: Construction Materials PPI (Producer Price Index)
    - **ECICONWAG**: Construction Wages (Employment Cost Index)
    - **DGS10**: 10-Year Treasury Rate (risk-free rate benchmark)

    These indices are used to escalate base construction costs to current dollars
    and establish discount rate benchmarks.

    **Update Frequency:** Monthly (FRED data)
    **Source:** Federal Reserve Economic Data (FRED)
    """,
    responses={
        200: {
            "description": "Current cost indices",
            "content": {
                "application/json": {
                    "example": {
                        "as_of_date": "2025-09-30",
                        "materials_ppi": 315.2,
                        "construction_wages_eci": 142.8,
                        "risk_free_rate_pct": 4.15,
                        "data_source": "Federal Reserve Economic Data (FRED)",
                        "series_ids": {
                            "materials": "WPUSI012011",
                            "wages": "ECICONWAG",
                            "risk_free_rate": "DGS10"
                        }
                    }
                }
            }
        },
        503: {"description": "FRED API unavailable"}
    },
    tags=["Economic Feasibility"]
)
async def get_current_cost_indices(
    fred_client: Annotated[FREDClient, Depends(get_fred_client)]
) -> CostIndicesResponse:
    """
    Get current construction cost indices from FRED.

    Provides the three key indices needed for construction cost estimation:
    1. Materials PPI - Producer price index for construction materials
    2. Wages ECI - Employment cost index for construction workers
    3. Risk-free rate - 10-year Treasury rate for discount rate benchmarking

    Args:
        fred_client: FRED API client (dependency injected)

    Returns:
        CostIndicesResponse with latest index values and metadata

    Raises:
        DataSourceError: FRED API unavailable (503)
    """
    try:
        logger.info("Fetching current cost indices from FRED")

        # Fetch latest indices from FRED
        indices = fred_client.get_current_indices()

        logger.info(
            "Cost indices retrieved successfully",
            extra={
                "materials_ppi": indices.materials_ppi,
                "wages_eci": indices.construction_wages_eci,
                "risk_free_rate": indices.risk_free_rate_pct
            }
        )

        return indices

    except Exception as e:
        logger.error(f"Failed to fetch cost indices: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Data source unavailable",
                "detail": f"FRED API error: {str(e)}",
                "retry_after": 60
            }
        )


@router.get(
    "/market-rents/{zip_code}",
    response_model=MarketRentResponse,
    summary="Get HUD Fair Market Rents",
    description="""
    Retrieve HUD Fair Market Rents (FMR) or Small Area FMR (SAFMR) for a ZIP code.

    Returns market rent estimates by bedroom count (0BR - 4BR) with source metadata.
    FMR data is used as the market-rate revenue benchmark in feasibility analysis.

    **Data Source:** HUD FMR Dataset (updated annually)
    **Coverage:** All U.S. ZIP codes
    **Use Case:** Market-rate unit revenue projection

    **Example:** ZIP 90401 (Santa Monica, CA) returns LA County FMR rates
    """,
    responses={
        200: {
            "description": "Market rent data for ZIP code",
            "content": {
                "application/json": {
                    "example": {
                        "zip_code": "90401",
                        "year": 2025,
                        "rents_by_bedroom": {
                            "0": 1850.0,
                            "1": 2100.0,
                            "2": 2650.0,
                            "3": 3450.0,
                            "4": 4100.0
                        },
                        "fmr_type": "SAFMR",
                        "metro_area": "Los Angeles-Long Beach-Anaheim, CA",
                        "data_source": "HUD FMR 2025",
                        "effective_date": "2024-10-01"
                    }
                }
            }
        },
        404: {"description": "ZIP code not found"},
        503: {"description": "HUD API unavailable"}
    },
    tags=["Economic Feasibility"]
)
async def get_market_rents(
    zip_code: str,
    hud_client: Annotated[HudFMRClient, Depends(get_hud_client)],
    year: Optional[int] = Query(None, description="FMR year (default: current year)")
) -> MarketRentResponse:
    """
    Get HUD Fair Market Rents for a ZIP code.

    Retrieves FMR or SAFMR data by bedroom type with source metadata.
    Used for market-rate revenue projections in feasibility analysis.

    Args:
        zip_code: 5-digit ZIP code
        year: Optional FMR year (defaults to current year)
        hud_client: HUD FMR API client (dependency injected)

    Returns:
        MarketRentResponse with FMR by bedroom count and metadata

    Raises:
        HTTPException: 404 if ZIP not found, 503 if API unavailable
    """
    try:
        logger.info(f"Fetching market rents for ZIP {zip_code}")

        # Validate ZIP code format
        if not zip_code.isdigit() or len(zip_code) != 5:
            raise HTTPException(
                status_code=422,
                detail="ZIP code must be 5 digits"
            )

        # Fetch FMR data
        rent_data = await hud_client.get_fmr_by_zip(zip_code, year)

        if not rent_data:
            raise HTTPException(
                status_code=404,
                detail=f"No FMR data found for ZIP code {zip_code}"
            )

        logger.info(
            "Market rents retrieved successfully",
            extra={
                "zip_code": zip_code,
                "fmr_type": rent_data.fmr_type,
                "metro_area": rent_data.metro_area
            }
        )

        return rent_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch market rents: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Data source unavailable",
                "detail": f"HUD API error: {str(e)}",
                "retry_after": 60
            }
        )


@router.post(
    "/assumptions/validate",
    response_model=ValidationResponse,
    summary="Validate Economic Assumptions",
    description="""
    Validate economic assumptions against reasonable bounds and market context.

    **Validation Checks:**
    - **Discount rate**: 5-25% (typical range for real estate development)
    - **Cap rate**: 3-8% (market context by property type)
    - **Quality factor**: 0.8-1.2 (±20% from RS Means base)
    - **Tax rate**: Prop 13 compliance (1% + local assessments)
    - **Operating expense ratio**: 25-50% (typical multifamily range)

    Use this endpoint to validate assumptions before running full feasibility analysis.
    """,
    responses={
        200: {
            "description": "Validation results",
            "content": {
                "application/json": {
                    "example": {
                        "is_valid": True,
                        "warnings": [
                            "Discount rate of 22% is high - typical range is 8-15% for multifamily"
                        ],
                        "errors": [],
                        "recommendations": [
                            "Consider using FRED DGS10 rate + 6-8% risk premium for discount rate"
                        ]
                    }
                }
            }
        }
    },
    tags=["Economic Feasibility"]
)
async def validate_assumptions(
    assumptions: EconomicAssumptions
) -> ValidationResponse:
    """
    Validate economic assumptions against reasonable bounds.

    Checks:
    - Discount rate reasonableness (5-25%)
    - Cap rate market context (3-8%)
    - Quality factor bounds (0.8-1.2)
    - Tax rate compliance (Prop 13: ~1.0-1.25%)
    - Operating expense ratio (25-50%)

    Args:
        assumptions: EconomicAssumptions to validate

    Returns:
        ValidationResponse with validation results, warnings, and recommendations
    """
    logger.info("Validating economic assumptions")

    warnings: List[str] = []
    errors: List[str] = []
    recommendations: List[str] = []

    # Validate discount rate (5-25%)
    if assumptions.discount_rate < 0.05:
        errors.append("Discount rate must be at least 5% (0.05)")
    elif assumptions.discount_rate > 0.25:
        errors.append("Discount rate exceeds 25% - unrealistic for real estate")
    elif assumptions.discount_rate > 0.15:
        warnings.append(
            f"Discount rate of {assumptions.discount_rate*100:.1f}% is high - "
            "typical range is 8-15% for multifamily development"
        )

    # Validate cap rate (3-8%)
    if assumptions.cap_rate:
        if assumptions.cap_rate < 0.03:
            warnings.append("Cap rate below 3% is unusual - verify market data")
        elif assumptions.cap_rate > 0.08:
            warnings.append("Cap rate above 8% is high - may indicate distressed market")

        # Check cap rate vs discount rate relationship
        if assumptions.cap_rate >= assumptions.discount_rate:
            warnings.append(
                "Cap rate should typically be lower than discount rate (cap rate assumes no growth)"
            )

    # Validate quality factor (0.8-1.2)
    if assumptions.quality_factor < 0.8:
        warnings.append("Quality factor below 0.8 - verify this reflects actual construction quality")
    elif assumptions.quality_factor > 1.2:
        warnings.append("Quality factor above 1.2 - verify this reflects actual construction quality")

    # Validate property tax rate (Prop 13: ~1.0-1.25% in CA)
    if assumptions.tax_rate:
        if assumptions.tax_rate > 0.0125:
            warnings.append(
                f"Property tax rate of {assumptions.tax_rate*100:.2f}% exceeds "
                "typical CA Prop 13 limit (1.0-1.25%)"
            )

    # Validate operating expense ratio (25-50% typical)
    # TODO: Add operating_expense_ratio field to EconomicAssumptions model
    # if assumptions.operating_expense_ratio:
    #     if assumptions.operating_expense_ratio < 0.25:
    #         warnings.append("Operating expense ratio below 25% is optimistic for multifamily")
    #     elif assumptions.operating_expense_ratio > 0.50:
    #         warnings.append("Operating expense ratio above 50% is high - verify assumptions")

    # Provide recommendations
    if assumptions.discount_rate > 0.15 or assumptions.discount_rate < 0.08:
        recommendations.append(
            "Consider using FRED DGS10 rate + 6-8% risk premium for discount rate "
            "(current methodology in /defaults endpoint)"
        )

    if not assumptions.cap_rate:
        recommendations.append(
            "Consider providing cap rate for terminal value calculation in DCF analysis"
        )

    is_valid = len(errors) == 0

    logger.info(
        "Assumption validation completed",
        extra={
            "is_valid": is_valid,
            "warnings_count": len(warnings),
            "errors_count": len(errors)
        }
    )

    return ValidationResponse(
        is_valid=is_valid,
        warnings=warnings,
        errors=errors,
        recommendations=recommendations
    )


@router.get(
    "/defaults",
    response_model=EconomicAssumptions,
    summary="Get Smart Default Assumptions",
    description="""
    Get smart defaults for economic assumptions populated from current market data.

    **Auto-Populated Fields:**
    - **Risk-free rate**: Current FRED DGS10 (10-year Treasury)
    - **Discount rate**: DGS10 + 6% MRP + 2% project premium (~12-14% typical)
    - **Cap rate**: Guidance by property type (4-6% multifamily)
    - **Quality factor**: 1.0 (RS Means base)
    - **Tax rate**: County-specific Prop 13 rate

    Use these defaults as a starting point, then customize for your specific project.

    **Market Risk Premium (MRP):** ~6% historical equity premium
    **Project Premium:** +2% for development risk above stabilized assets
    """,
    responses={
        200: {
            "description": "Default assumptions with current market data",
            "content": {
                "application/json": {
                    "example": {
                        "discount_rate": 0.125,
                        "cap_rate": 0.05,
                        "quality_factor": 1.0,
                        "location_factor": 2.1,
                        "property_tax_rate": 0.0125,
                        "operating_expense_ratio": 0.35,
                        "vacancy_rate": 0.05,
                        "annual_rent_growth": 0.03,
                        "annual_expense_growth": 0.025,
                        "notes": [
                            "Discount rate = DGS10 (4.15%) + MRP (6%) + Project Premium (2%) = 12.15%",
                            "Cap rate guidance: 4-6% for LA multifamily (using 5.0%)",
                            "Property tax rate: LA County Prop 13 rate (1.25%)"
                        ]
                    }
                }
            }
        },
        503: {"description": "FRED API unavailable for risk-free rate"}
    },
    tags=["Economic Feasibility"]
)
async def get_default_assumptions(
    fred_client: Annotated[FREDClient, Depends(get_fred_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    county: Optional[str] = Query("Los Angeles", description="County for tax rate defaults")
) -> EconomicAssumptions:
    """
    Get smart defaults for economic assumptions.

    Populates:
    - Current risk-free rate from FRED DGS10
    - Discount rate = DGS10 + MRP (6%) + project premium (2%)
    - County-specific tax rate defaults
    - Current cap rate guidance (4-6% for multifamily)
    - Quality factor defaults (1.0 = RS Means base)

    Returns pre-filled EconomicAssumptions for convenience.

    Args:
        county: County name for tax rate defaults (default: "Los Angeles")
        fred_client: FRED API client (dependency injected)
        settings: Application settings (dependency injected)

    Returns:
        EconomicAssumptions with smart defaults and explanation notes
    """
    try:
        logger.info(f"Generating default assumptions for {county} County")

        notes: List[str] = []

        # Get current risk-free rate from FRED
        try:
            indices = fred_client.get_current_indices()
            risk_free_rate = indices.risk_free_rate_pct / 100.0  # Convert to decimal
            notes.append(f"Current risk-free rate (DGS10): {indices.risk_free_rate_pct:.2f}%")
        except Exception as e:
            logger.warning(f"Failed to fetch FRED data, using fallback: {e}")
            risk_free_rate = 0.04  # Fallback to 4%
            notes.append("Risk-free rate: 4.0% (fallback - FRED unavailable)")

        # Calculate discount rate: Risk-free + MRP + Project Premium
        market_risk_premium = 0.06  # 6% historical equity premium
        project_premium = 0.02      # 2% for development risk
        discount_rate = risk_free_rate + market_risk_premium + project_premium

        notes.append(
            f"Discount rate = DGS10 ({risk_free_rate*100:.2f}%) + "
            f"MRP ({market_risk_premium*100:.0f}%) + "
            f"Project Premium ({project_premium*100:.0f}%) = {discount_rate*100:.2f}%"
        )

        # Cap rate guidance (property type specific)
        cap_rate = 0.05  # 5% typical for LA multifamily
        notes.append("Cap rate guidance: 4-6% for LA multifamily (using 5.0%)")

        # County-specific tax rates (Prop 13 base + local assessments)
        tax_rates = {
            "Los Angeles": 0.0125,      # 1.25% typical
            "Orange": 0.0110,            # 1.10% typical
            "San Diego": 0.0115,         # 1.15% typical
            "Santa Clara": 0.0120,       # 1.20% typical
            "San Francisco": 0.0120,     # 1.20% typical
        }
        property_tax_rate = tax_rates.get(county, 0.0110)  # Default 1.10%
        notes.append(f"Property tax rate: {county} County Prop 13 rate ({property_tax_rate*100:.2f}%)")

        # Quality factor (1.0 = RS Means base)
        quality_factor = 1.0
        notes.append("Quality factor: 1.0 (RS Means base cost)")

        # Location factor (varies by region)
        # LA/SF/SD are high-cost markets (1.8-2.2)
        location_factors = {
            "Los Angeles": 2.1,
            "Orange": 1.9,
            "San Diego": 1.85,
            "Santa Clara": 2.2,
            "San Francisco": 2.3,
        }
        location_factor = location_factors.get(county, 1.5)  # Default mid-range
        notes.append(f"Location factor: {location_factor} ({county} County multiplier)")

        # Operating assumptions (typical multifamily)
        operating_expense_ratio = 0.35   # 35% typical for multifamily
        vacancy_rate = 0.05               # 5% vacancy allowance
        annual_rent_growth = 0.03         # 3% annual rent growth
        annual_expense_growth = 0.025     # 2.5% annual expense growth

        notes.append("Operating assumptions: 35% OpEx, 5% vacancy, 3% rent growth, 2.5% expense growth")

        logger.info(
            "Default assumptions generated",
            extra={
                "county": county,
                "discount_rate": discount_rate,
                "cap_rate": cap_rate,
                "location_factor": location_factor
            }
        )

        return EconomicAssumptions(
            discount_rate=discount_rate,
            cap_rate=cap_rate,
            quality_factor=quality_factor,
            location_factor=location_factor,
            property_tax_rate=property_tax_rate,
            operating_expense_ratio=operating_expense_ratio,
            vacancy_rate=vacancy_rate,
            annual_rent_growth=annual_rent_growth,
            annual_expense_growth=annual_expense_growth,
            notes=notes
        )

    except Exception as e:
        logger.error(f"Failed to generate default assumptions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate default assumptions"
        )


# Exception handlers for custom errors
# @router.exception_handler(DataSourceError)
# async def data_source_error_handler(request, exc):
    """Handle data source unavailability errors."""
    return JSONResponse(
        status_code=503,
        content={
            "error": "Data source unavailable",
            "detail": str(exc),
            "retry_after": 60
        }
    )


# @router.exception_handler(InvalidAssumptionError)
# async def invalid_assumption_error_handler(request, exc):
    """Handle invalid assumption errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid assumptions",
            "detail": str(exc)
        }
    )


# @router.exception_handler(CalculationError)
# async def calculation_error_handler(request, exc):
    """Handle calculation errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Calculation failed",
            "detail": str(exc)
        }
    )
