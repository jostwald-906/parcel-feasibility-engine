"""
Economic Feasibility Analysis Service

Main orchestrator for comprehensive financial feasibility analysis of residential
development projects. Integrates construction cost estimation, revenue projection,
cash flow modeling, and sensitivity analysis.

Workflow:
1. Estimate construction costs (via cost_estimator)
2. Project revenue and NOI (via revenue_estimator)
3. Generate development cash flows
4. Calculate financial metrics (NPV, IRR, payback, PI)
5. Run sensitivity analysis (tornado and/or Monte Carlo)
6. Generate investment recommendation
7. Compile comprehensive source notes

References:
- Real Estate Finance and Investment Manual (Wiedemer et al.)
- Appraisal Institute: The Appraisal of Real Estate
- Urban Land Institute: Dollars & Cents of Development
"""

from app.core.financial_math import (
    calculate_npv,
    calculate_irr,
    calculate_payback_period,
    calculate_profitability_index,
    calculate_tornado_sensitivity,
    run_monte_carlo_simulation,
    generate_development_cash_flows,
    calculate_exit_value,
    SensitivityInput,
    MonteCarloInputs,
    TimelineInputs,
    CashFlow,
    TornadoResult,
    MonteCarloResult,
    format_currency,
    format_percentage,
)

from app.models.economic_feasibility import (
    FeasibilityRequest,
    FeasibilityAnalysis,
    EconomicAssumptions,
    FinancialMetrics,
    SensitivityAnalysis,
    ConstructionInputs,
    ConstructionCostEstimate,
    RevenueProjection,
    TimelineInputs,
    RevenueInputs
)

from app.services.cost_estimator import estimate_construction_cost
from app.clients.fred_client import FREDClient
from app.services.ami_calculator import AMICalculator, get_ami_calculator

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================


def _calculate_buildable_sf(num_units: int, avg_unit_size_sf: float) -> float:
    """
    Calculate total buildable square footage.

    Args:
        num_units: Number of residential units
        avg_unit_size_sf: Average unit size in SF

    Returns:
        Total buildable SF
    """
    return num_units * avg_unit_size_sf


def _estimate_revenue_simple(
    num_units: int,
    buildable_sf: float,
    assumptions: EconomicAssumptions,
    affordable_pct: float = 0.0
) -> float:
    """
    Simplified revenue estimate for NPV calculation.

    Uses average rent per SF and vacancy rate from assumptions.
    Accounts for affordable unit discount if applicable.

    Args:
        num_units: Number of units
        buildable_sf: Total buildable SF
        assumptions: Economic assumptions
        affordable_pct: Percentage of affordable units (0-1)

    Returns:
        Annual Net Operating Income (NOI)
    """
    # Gross Scheduled Income (100% market rate)
    monthly_rent = buildable_sf * assumptions.avg_rent_per_sf_month
    annual_gsi = monthly_rent * 12

    # Apply affordable discount if applicable
    # Assume affordable rents are 60% of market rate on average
    if affordable_pct > 0:
        affordable_discount_factor = 1 - (affordable_pct * 0.40)  # 40% discount
        annual_gsi *= affordable_discount_factor

    # Effective Gross Income (account for vacancy)
    egi = annual_gsi * (1 - assumptions.vacancy_rate)

    # Operating Expenses
    annual_opex = num_units * assumptions.opex_per_unit_annual

    # Property Taxes (estimated as % of construction cost)
    # Conservative estimate: use 1.5x construction cost as assessed value
    # This will be refined in full revenue projection

    # Insurance (estimated)
    # Will be refined in full revenue projection

    # For simplified calculation, OpEx includes taxes and insurance
    # NOI = EGI - OpEx
    noi = egi - annual_opex

    # Apply property tax and insurance as additional % of revenue
    # Rough estimate: 15% of EGI for taxes + insurance
    noi -= egi * (assumptions.property_tax_rate + assumptions.insurance_rate)

    return noi


def _create_npv_function(
    base_params: Dict[str, Any],
    num_units: int,
    buildable_sf: float,
    affordable_pct: float
) -> Callable[[Dict[str, Any]], float]:
    """
    Create NPV calculation function for sensitivity analysis.

    Returns a function that takes parameter overrides and returns NPV.

    Args:
        base_params: Base case parameters (includes assumptions)
        num_units: Number of units
        buildable_sf: Buildable square footage
        affordable_pct: Affordable percentage

    Returns:
        Function that calculates NPV given parameters
    """
    def calculate_scenario_npv(params: Dict[str, Any]) -> float:
        """Calculate NPV for a given parameter set."""
        # Extract assumptions from params
        assumptions = params.get('assumptions', base_params['assumptions'])

        # Calculate costs
        cost_per_sf = params.get('cost_per_sf', base_params['cost_per_sf'])
        quality_factor = params.get('quality_factor', base_params.get('quality_factor', 1.0))
        total_cost = buildable_sf * cost_per_sf * quality_factor

        # Calculate revenue (NOI)
        rent_per_sf = params.get('avg_rent_per_sf_month', assumptions.avg_rent_per_sf_month)

        # Create modified assumptions
        modified_assumptions = EconomicAssumptions(**assumptions.model_dump())
        modified_assumptions.avg_rent_per_sf_month = rent_per_sf
        modified_assumptions.exit_cap_rate = params.get('exit_cap_rate', assumptions.exit_cap_rate)
        modified_assumptions.rent_growth_rate = params.get('rent_growth_rate', assumptions.rent_growth_rate)

        # Calculate NOI
        annual_noi = _estimate_revenue_simple(
            num_units, buildable_sf, modified_assumptions, affordable_pct
        )

        # Adjust for construction delay
        construction_delay_months = params.get('construction_delay_months', 0)
        construction_months = assumptions.construction_months + construction_delay_months

        # Generate cash flows
        timeline = TimelineInputs(
            predevelopment_months=assumptions.predevelopment_months,
            construction_months=int(construction_months),
            lease_up_months=assumptions.lease_up_months,
            operations_years=assumptions.holding_period_years
        )

        cash_flows_data = generate_development_cash_flows(
            total_construction_cost=total_cost,
            annual_noi=annual_noi,
            timeline=timeline,
            exit_cap_rate=modified_assumptions.exit_cap_rate,
            soft_cost_pct=assumptions.soft_cost_pct
        )

        # Extract cash flow amounts (skip period 0 which is initial investment)
        cf_amounts = [cf.amount for cf in cash_flows_data[1:]]

        # Calculate NPV
        npv = calculate_npv(
            cash_flows=cf_amounts,
            discount_rate=assumptions.discount_rate,
            initial_investment=total_cost
        )

        return npv

    return calculate_scenario_npv


# ============================================================================
# Main Feasibility Analysis Function
# ============================================================================


async def analyze_economic_feasibility(
    request: FeasibilityRequest,
    fred_client: Optional[FREDClient] = None,
    ami_calculator: Optional[AMICalculator] = None,
) -> FeasibilityAnalysis:
    """
    Main orchestrator for economic feasibility analysis.

    Workflow:
    1. Estimate construction costs (cost_estimator)
    2. Project revenue (simplified for now, full revenue_estimator integration later)
    3. Generate cash flows (financial_math)
    4. Calculate NPV, IRR, PI, payback
    5. Run tornado sensitivity (if requested)
    6. Run Monte Carlo (if requested)
    7. Generate decision recommendation
    8. Compile comprehensive source_notes

    Args:
        request: Feasibility analysis request
        fred_client: FRED client for economic data (optional, uses default if None)
        ami_calculator: AMI calculator for affordable housing (optional)

    Returns:
        Complete FeasibilityAnalysis with metrics, sensitivity, and recommendation
    """
    logger.info(
        f"Starting feasibility analysis for {request.num_units} units, "
        f"{request.affordable_pct*100:.1f}% affordable"
    )

    # Initialize clients if not provided
    if fred_client is None:
        fred_client = get_fred_client()

    if ami_calculator is None:
        ami_calculator = get_ami_calculator()

    assumptions = request.assumptions

    # Step 1: Estimate construction costs
    logger.info("Estimating construction costs...")

    buildable_sf = _calculate_buildable_sf(request.num_units, request.avg_unit_size_sf)

    construction_inputs = ConstructionInputs(
        buildable_sqft=buildable_sf,
        num_units=request.num_units,
        construction_type="wood_frame",  # Default, could be parameterized
        location_factor=2.3,  # California coastal market
        permit_fees_per_unit=5000.0,
        construction_duration_months=assumptions.construction_months
    )

    cost_assumptions = CostAssumptions(
        use_wage_adjustment=False,
        architecture_pct=assumptions.soft_cost_pct * 0.50,  # 50% of soft costs is A&E
        legal_pct=assumptions.soft_cost_pct * 0.20,  # 20% of soft costs is legal
        developer_fee_pct=assumptions.soft_cost_pct * 0.30,  # 30% of soft costs is dev fee
        contingency_pct=assumptions.contingency_pct
    )

    cost_estimate = await estimate_construction_cost(
        inputs=construction_inputs,
        assumptions=cost_assumptions,
        fred_client=fred_client
    )

    # Step 2: Project revenue (simplified)
    logger.info("Projecting revenue and NOI...")

    annual_noi = _estimate_revenue_simple(
        request.num_units,
        buildable_sf,
        assumptions,
        request.affordable_pct
    )

    # Create simple revenue projection model (to be enhanced with full revenue_estimator)
    from app.models.economic import RevenueProjection

    gross_scheduled_income = buildable_sf * assumptions.avg_rent_per_sf_month * 12
    vacancy_loss = gross_scheduled_income * assumptions.vacancy_rate
    egi = gross_scheduled_income - vacancy_loss

    operating_expenses = request.num_units * assumptions.opex_per_unit_annual

    # Estimate property taxes and insurance
    # Use 1.5x construction cost as assessed value (conservative)
    assessed_value = cost_estimate.total_cost * 1.5
    property_taxes = assessed_value * assumptions.property_tax_rate
    insurance = assessed_value * assumptions.insurance_rate

    affordable_units = int(request.num_units * request.affordable_pct)
    market_units = request.num_units - affordable_units

    affordable_rent_discount = None
    if affordable_units > 0:
        # Affordable discount estimate: 40% below market
        affordable_rent_discount = affordable_units * request.avg_unit_size_sf * assumptions.avg_rent_per_sf_month * 12 * 0.40

    revenue_projection = RevenueProjection(
        gross_scheduled_income=gross_scheduled_income,
        vacancy_loss=vacancy_loss,
        effective_gross_income=egi,
        operating_expenses=operating_expenses,
        property_taxes=property_taxes,
        insurance=insurance,
        net_operating_income=annual_noi,
        noi_per_unit=annual_noi / request.num_units,
        operating_expense_ratio=operating_expenses / egi if egi > 0 else 0,
        affordable_rent_discount=affordable_rent_discount,
        market_rate_units=market_units,
        affordable_units=affordable_units,
        source_notes={
            "methodology": "Simplified revenue projection using average rent per SF",
            "market_rent_assumption": f"${assumptions.avg_rent_per_sf_month:.2f}/SF/month",
            "vacancy_rate": f"{assumptions.vacancy_rate*100:.1f}%",
            "opex_per_unit": f"${assumptions.opex_per_unit_annual:,.0f}/year"
        }
    )

    # Step 3: Generate cash flows
    logger.info("Generating development cash flows...")

    timeline = TimelineInputs(
        predevelopment_months=assumptions.predevelopment_months,
        construction_months=assumptions.construction_months,
        lease_up_months=assumptions.lease_up_months,
        operations_years=assumptions.holding_period_years
    )

    cash_flows_data = generate_development_cash_flows(
        total_construction_cost=cost_estimate.total_cost,
        annual_noi=annual_noi,
        timeline=timeline,
        exit_cap_rate=assumptions.exit_cap_rate,
        soft_cost_pct=assumptions.soft_cost_pct
    )

    # Convert to API model
    cash_flows = [
        CashFlowPeriod(
            period=cf.period,
            description=cf.description,
            amount=cf.amount,
            cumulative=cf.cumulative,
            phase=cf.phase
        )
        for cf in cash_flows_data
    ]

    # Step 4: Calculate financial metrics
    logger.info("Calculating financial metrics (NPV, IRR, payback, PI)...")

    # Extract cash flow amounts (skip period 0)
    cf_amounts = [cf.amount for cf in cash_flows_data[1:]]

    npv = calculate_npv(
        cash_flows=cf_amounts,
        discount_rate=assumptions.discount_rate,
        initial_investment=cost_estimate.total_cost
    )

    irr = calculate_irr(
        cash_flows=cf_amounts,
        initial_investment=cost_estimate.total_cost
    )

    payback = calculate_payback_period(
        cash_flows=cf_amounts,
        initial_investment=cost_estimate.total_cost
    )

    pi = calculate_profitability_index(npv, cost_estimate.total_cost)

    # Calculate total cash returned
    total_cash_returned = sum(cf_amounts)

    financial_metrics = FinancialMetrics(
        npv=npv,
        irr=irr,
        irr_pct=format_percentage(irr, 2) if irr is not None else None,
        payback_period_years=payback,
        profitability_index=pi,
        initial_investment=cost_estimate.total_cost,
        total_cash_returned=total_cash_returned,
        discount_rate=assumptions.discount_rate
    )

    logger.info(f"NPV: {format_currency(npv)}, IRR: {format_percentage(irr) if irr else 'N/A'}")

    # Step 5: Run sensitivity analysis
    sensitivity_analysis = None

    if request.run_tornado_sensitivity or request.run_monte_carlo:
        logger.info("Running sensitivity analysis...")

        sensitivity_analysis = await _run_sensitivity_analysis(
            request=request,
            base_npv=npv,
            buildable_sf=buildable_sf,
            cost_per_sf=cost_estimate.cost_per_buildable_sf,
            assumptions=assumptions
        )

    # Step 6: Generate recommendation
    logger.info("Generating investment recommendation...")

    recommendation, rationale = _generate_recommendation(
        npv=npv,
        irr=irr,
        probability_positive=sensitivity_analysis.monte_carlo.probability_positive_npv if sensitivity_analysis and sensitivity_analysis.monte_carlo else None,
        hurdle_rate=assumptions.hurdle_rate
    )

    # Step 7: Compile source notes
    source_notes = _compile_source_notes(
        cost_estimate=cost_estimate,
        revenue_projection=revenue_projection,
        assumptions=assumptions,
        fred_client=fred_client
    )

    # Create request summary
    request_summary = {
        "num_units": request.num_units,
        "avg_unit_size_sf": request.avg_unit_size_sf,
        "total_buildable_sf": buildable_sf,
        "affordable_pct": request.affordable_pct,
        "affordable_units": affordable_units,
        "market_units": market_units,
        "parcel_apn": request.parcel_apn,
        "parcel_county": request.parcel_county
    }

    # Build final response
    analysis = FeasibilityAnalysis(
        request_summary=request_summary,
        cost_estimate=cost_estimate,
        revenue_projection=revenue_projection,
        cash_flows=cash_flows,
        financial_metrics=financial_metrics,
        sensitivity_analysis=sensitivity_analysis,
        recommendation=recommendation,
        recommendation_rationale=rationale,
        source_notes=source_notes,
        analysis_date=datetime.now()
    )

    logger.info(f"Feasibility analysis complete. Recommendation: {recommendation}")

    return analysis


async def _run_sensitivity_analysis(
    request: FeasibilityRequest,
    base_npv: float,
    buildable_sf: float,
    cost_per_sf: float,
    assumptions: EconomicAssumptions
) -> SensitivityAnalysis:
    """
    Run tornado and/or Monte Carlo sensitivity analysis.

    Args:
        request: Feasibility request
        base_npv: Base case NPV
        buildable_sf: Buildable square footage
        cost_per_sf: Cost per SF
        assumptions: Economic assumptions

    Returns:
        SensitivityAnalysis with tornado and/or Monte Carlo results
    """
    tornado_results = []
    monte_carlo_stats = None

    # Create base scenario parameters
    base_params = {
        'assumptions': assumptions,
        'cost_per_sf': cost_per_sf,
        'quality_factor': assumptions.quality_factor,
        'avg_rent_per_sf_month': assumptions.avg_rent_per_sf_month,
        'exit_cap_rate': assumptions.exit_cap_rate,
        'rent_growth_rate': assumptions.rent_growth_rate,
        'construction_delay_months': 0
    }

    # Create NPV function
    npv_function = _create_npv_function(
        base_params=base_params,
        num_units=request.num_units,
        buildable_sf=buildable_sf,
        affordable_pct=request.affordable_pct
    )

    # Tornado sensitivity analysis
    if request.run_tornado_sensitivity:
        logger.info("Running tornado sensitivity analysis...")

        # Define variables to test (use request variables or defaults)
        variables_to_test = request.tornado_variables
        if not variables_to_test:
            # Use default variables
            from app.models.economic import SensitivityVariable
            variables_to_test = [
                SensitivityVariable(
                    variable_name='cost_per_sf',
                    label='Construction Cost per SF',
                    delta_pct=0.15
                ),
                SensitivityVariable(
                    variable_name='avg_rent_per_sf_month',
                    label='Market Rent per SF',
                    delta_pct=0.15
                ),
                SensitivityVariable(
                    variable_name='exit_cap_rate',
                    label='Exit Cap Rate',
                    delta_pct=0.20
                ),
                SensitivityVariable(
                    variable_name='rent_growth_rate',
                    label='Rent Growth Rate',
                    delta_pct=0.33
                ),
                SensitivityVariable(
                    variable_name='construction_delay_months',
                    label='Construction Delay (months)',
                    delta_pct=0.50
                ),
            ]

        # Convert to SensitivityInput for financial_math
        sensitivity_inputs = [
            SensitivityInput(
                variable_name=var.variable_name,
                base_value=base_params[var.variable_name],
                delta_pct=var.delta_pct,
                label=var.label
            )
            for var in variables_to_test
        ]

        tornado_results_raw = calculate_tornado_sensitivity(
            base_scenario=base_params,
            variables_to_test=sensitivity_inputs,
            npv_function=npv_function
        )

        # Convert to API model
        tornado_results = [
            TornadoVariable(
                variable_name=result.variable_name,
                label=result.label,
                base_value=result.base_npv,  # Store base NPV
                base_npv=result.base_npv,
                downside_value=result.downside_value,
                downside_npv=result.downside_npv,
                upside_value=result.upside_value,
                upside_npv=result.upside_npv,
                impact=result.impact,
                rank=i + 1
            )
            for i, result in enumerate(tornado_results_raw)
        ]

        logger.info(f"Tornado analysis complete. Most sensitive: {tornado_results[0].label if tornado_results else 'N/A'}")

    # Monte Carlo simulation
    if request.run_monte_carlo:
        logger.info("Running Monte Carlo simulation...")

        # Use request config or defaults
        mc_config = request.monte_carlo_config
        if not mc_config:
            from app.models.economic import MonteCarloConfig
            mc_config = MonteCarloConfig()

        # Convert to MonteCarloInputs for financial_math
        mc_inputs = MonteCarloInputs(
            iterations=mc_config.iterations,
            seed=mc_config.seed,
            cost_per_sf_std=mc_config.cost_per_sf_std,
            rent_growth_std=mc_config.rent_growth_std,
            cap_rate_min=mc_config.cap_rate_min,
            cap_rate_mode=mc_config.cap_rate_mode,
            cap_rate_max=mc_config.cap_rate_max,
            construction_delay_mean=mc_config.construction_delay_mean,
            construction_delay_std=mc_config.construction_delay_std
        )

        mc_result = run_monte_carlo_simulation(
            base_params=base_params,
            monte_carlo_inputs=mc_inputs,
            npv_function=npv_function
        )

        # Convert to API model
        monte_carlo_stats = MonteCarloStatistics(
            iterations=mc_result.iterations,
            probability_positive_npv=mc_result.probability_positive,
            mean_npv=mc_result.mean_npv,
            median_npv=mc_result.median_npv,
            std_npv=mc_result.std_npv,
            percentile_5=mc_result.percentile_5,
            percentile_25=mc_result.percentile_25,
            percentile_75=mc_result.percentile_75,
            percentile_95=mc_result.percentile_95,
            histogram_bins=mc_result.histogram_bins.tolist(),
            histogram_counts=mc_result.histogram_counts.tolist()
        )

        logger.info(
            f"Monte Carlo complete. P(NPV>0) = {mc_result.probability_positive*100:.1f}%, "
            f"Mean NPV = {format_currency(mc_result.mean_npv)}"
        )

    return SensitivityAnalysis(
        tornado_results=tornado_results,
        monte_carlo=monte_carlo_stats
    )


def _generate_recommendation(
    npv: float,
    irr: Optional[float],
    probability_positive: Optional[float],
    hurdle_rate: float = 0.15
) -> tuple[str, List[str]]:
    """
    Generate investment recommendation based on financial metrics.

    Decision logic:
    - NPV ≤ 0: DO NOT PROCEED
    - IRR < hurdle_rate: MARGINAL
    - Prob(NPV>0) < 70%: HIGH RISK
    - IRR ≥ 18% and Prob ≥ 80%: STRONG PROCEED
    - Otherwise: PROCEED with caveats

    Args:
        npv: Net Present Value
        irr: Internal Rate of Return (optional)
        probability_positive: Probability of positive NPV from Monte Carlo (optional)
        hurdle_rate: Minimum acceptable IRR

    Returns:
        Tuple of (recommendation string, rationale bullet points)
    """
    rationale = []

    # NPV check (most important)
    if npv <= 0:
        return "DO NOT PROCEED", [
            f"Negative NPV of {format_currency(npv)} indicates project destroys value",
            "Project does not meet minimum financial viability threshold",
            "Consider alternative development strategies or site uses"
        ]

    # Add positive NPV to rationale
    rationale.append(f"Positive NPV of {format_currency(npv)} indicates value creation")

    # IRR check
    if irr is not None:
        if irr < hurdle_rate:
            return "MARGINAL", [
                *rationale,
                f"IRR of {format_percentage(irr, 2)} is below hurdle rate of {format_percentage(hurdle_rate, 2)}",
                "Returns may not adequately compensate for development risk",
                "Consider value engineering or alternative revenue strategies"
            ]
        else:
            rationale.append(f"IRR of {format_percentage(irr, 2)} exceeds hurdle rate of {format_percentage(hurdle_rate, 2)}")

    # Monte Carlo risk check
    if probability_positive is not None:
        if probability_positive < 0.70:
            return "HIGH RISK", [
                *rationale,
                f"Monte Carlo analysis shows only {probability_positive*100:.1f}% probability of positive NPV",
                "High uncertainty suggests significant downside risk",
                "Recommend additional due diligence and risk mitigation strategies"
            ]
        else:
            rationale.append(f"Monte Carlo analysis shows {probability_positive*100:.1f}% probability of positive returns")

    # Strong proceed conditions
    if irr is not None and probability_positive is not None:
        if irr >= 0.18 and probability_positive >= 0.80:
            return "STRONG PROCEED", [
                *rationale,
                "Excellent risk-adjusted returns with high probability of success",
                "Project demonstrates strong financial feasibility",
                "Recommend proceeding with development"
            ]

    # Default: Proceed with caveats
    return "PROCEED", [
        *rationale,
        "Project demonstrates financial viability under base case assumptions",
        "Monitor key sensitivities (construction cost, market rents, cap rates)",
        "Recommend detailed market study and ongoing feasibility updates"
    ]


def _compile_source_notes(
    cost_estimate: ConstructionCostEstimate,
    revenue_projection: RevenueProjection,
    assumptions: EconomicAssumptions,
    fred_client: FREDClient
) -> Dict[str, Any]:
    """
    Compile comprehensive source notes for audit trail.

    Aggregates all data sources, methodology notes, and assumptions
    into a master source documentation dict.

    Args:
        cost_estimate: Construction cost estimate with source notes
        revenue_projection: Revenue projection with source notes
        assumptions: Economic assumptions
        fred_client: FRED client for economic data dates

    Returns:
        Master source notes dictionary
    """
    source_notes = {
        "analysis_methodology": "Discounted Cash Flow (DCF) analysis with sensitivity testing",
        "analysis_date": datetime.now().isoformat(),

        # Cost sources
        "construction_costs": cost_estimate.source_notes,

        # Revenue sources
        "revenue_projections": revenue_projection.source_notes,

        # Assumptions documentation
        "economic_assumptions": {
            "discount_rate": f"{assumptions.discount_rate*100:.1f}% (WACC proxy)",
            "hurdle_rate": f"{assumptions.hurdle_rate*100:.1f}% (minimum acceptable IRR)",
            "base_cost_per_sf": f"${assumptions.base_cost_per_sf:.2f}/SF (2025 baseline)",
            "soft_cost_pct": f"{assumptions.soft_cost_pct*100:.1f}% of hard costs",
            "contingency_pct": f"{assumptions.contingency_pct*100:.1f}% of hard+soft costs",
            "market_rent": f"${assumptions.avg_rent_per_sf_month:.2f}/SF/month",
            "vacancy_rate": f"{assumptions.vacancy_rate*100:.1f}%",
            "opex_per_unit": f"${assumptions.opex_per_unit_annual:,.0f}/year",
            "property_tax_rate": f"{assumptions.property_tax_rate*100:.2f}% (Prop 13)",
            "exit_cap_rate": f"{assumptions.exit_cap_rate*100:.1f}%",
            "holding_period": f"{assumptions.holding_period_years} years"
        },

        # Timeline
        "development_timeline": {
            "predevelopment": f"{assumptions.predevelopment_months} months",
            "construction": f"{assumptions.construction_months} months",
            "lease_up": f"{assumptions.lease_up_months} months",
            "operations": f"{assumptions.holding_period_years} years before sale"
        },

        # Data sources
        "data_sources": [
            "FRED (Federal Reserve Economic Data) for PPI and interest rates",
            "Industry-standard cost estimating databases (RSMeans proxy)",
            "HUD Fair Market Rent data for revenue assumptions",
            "California HCD Income Limits for affordable housing calculations",
            "Real Estate Finance and Investment Manual (methodology)",
            "Urban Land Institute Dollars & Cents of Development (benchmarks)"
        ],

        # Disclaimers
        "disclaimers": [
            "This analysis is a preliminary feasibility estimate based on assumed inputs",
            "Actual costs and revenues will vary based on market conditions, design, and execution",
            "Recommend detailed market study, architectural programming, and cost estimating",
            "Financial projections are not guarantees of future performance",
            "This analysis does not constitute investment advice"
        ]
    }

    return source_notes


# ============================================================================
# Service Initialization
# ============================================================================


# def get_feasibility_settings() -> EconomicFeasibilitySettings:
#     """
#     Get economic feasibility settings from app config.
#
#     Returns:
#         EconomicFeasibilitySettings with current configuration
#     """
#     from app.core.config import settings
#
#     return EconomicFeasibilitySettings(
#         fred_api_key=settings.FRED_API_KEY,
#         fred_enabled=settings.FRED_API_ENABLED,
#         ref_cost_per_sf=settings.REF_COST_PER_SF,
#         ref_ppi_date=settings.REF_PPI_DATE,
#         ref_ppi_value=settings.REF_PPI_VALUE,
#         architecture_pct=settings.ARCHITECTURE_PCT,
#         legal_pct=settings.LEGAL_PCT,
#         developer_fee_pct=settings.DEVELOPER_FEE_PCT,
#         contingency_pct=settings.CONTINGENCY_PCT,
#         construction_loan_spread=settings.CONSTRUCTION_LOAN_SPREAD,
#         common_area_factor=settings.COMMON_AREA_FACTOR
#     )
