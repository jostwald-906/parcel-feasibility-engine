"""
Core financial mathematics functions for real estate feasibility analysis.

This module provides pure financial calculation functions including:
- Net Present Value (NPV)
- Internal Rate of Return (IRR)
- Payback Period
- Profitability Index (PI)
- Sensitivity Analysis (Tornado diagrams)
- Monte Carlo Simulation
- Development Cash Flow Generation

All functions are stateless and side-effect free for easy testing and composition.

References:
- Real Estate Finance textbooks for standard formulas
- Financial modeling best practices
- NumPy Financial documentation
"""

import numpy as np
from scipy import stats, optimize
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes for Type Safety
# ============================================================================


@dataclass
class CashFlow:
    """
    Represents a single period cash flow.

    Attributes:
        period: Period number (0 = initial, 1 = year 1, etc.)
        description: Description of the cash flow (e.g., "Construction Draw Year 1")
        amount: Cash flow amount (positive = inflow, negative = outflow)
        cumulative: Cumulative cash flow to date
        phase: Development phase (predevelopment, construction, lease_up, operations, exit)
    """
    period: int
    description: str
    amount: float
    cumulative: float
    phase: str


@dataclass
class SensitivityInput:
    """
    Input for one-way sensitivity analysis.

    Attributes:
        variable_name: Name of the variable to test (e.g., "cost_per_sf")
        base_value: Base case value
        delta_pct: Percentage change to test (e.g., 0.15 for ±15%)
        label: Human-readable label for display
    """
    variable_name: str
    base_value: float
    delta_pct: float
    label: str


@dataclass
class TornadoResult:
    """
    Result from tornado sensitivity analysis.

    Attributes:
        variable_name: Variable tested
        label: Display label
        base_npv: Base case NPV
        downside_npv: NPV with negative change
        upside_npv: NPV with positive change
        impact: Absolute impact (|upside - downside|)
        downside_value: Variable value for downside case
        upside_value: Variable value for upside case
    """
    variable_name: str
    label: str
    base_npv: float
    downside_npv: float
    upside_npv: float
    impact: float
    downside_value: float
    upside_value: float


@dataclass
class MonteCarloInputs:
    """
    Inputs for Monte Carlo simulation.

    Attributes:
        iterations: Number of Monte Carlo iterations (default 10,000)
        seed: Random seed for reproducibility
        cost_per_sf_std: Standard deviation for cost per SF (normal distribution)
        rent_growth_std: Standard deviation for rent growth rate (normal distribution)
        cap_rate_min: Minimum exit cap rate (triangular distribution)
        cap_rate_mode: Most likely exit cap rate (triangular distribution)
        cap_rate_max: Maximum exit cap rate (triangular distribution)
        construction_delay_mean: Mean construction delay in months (lognormal)
        construction_delay_std: Std dev of construction delay (lognormal)
    """
    iterations: int = 10000
    seed: int = 42
    cost_per_sf_std: float = 25.0  # ±$25/SF typical variation
    rent_growth_std: float = 0.015  # ±1.5% variation in growth rate
    cap_rate_min: float = 0.04
    cap_rate_mode: float = 0.05
    cap_rate_max: float = 0.07
    construction_delay_mean: float = 0.0  # Mean delay in months
    construction_delay_std: float = 3.0  # Std dev in months


@dataclass
class MonteCarloResult:
    """
    Results from Monte Carlo simulation.

    Attributes:
        iterations: Number of iterations run
        npv_array: Array of NPV results
        probability_positive: Probability of NPV > 0
        mean_npv: Mean NPV
        median_npv: Median NPV (50th percentile)
        std_npv: Standard deviation of NPV
        percentile_5: 5th percentile (downside case)
        percentile_25: 25th percentile
        percentile_75: 75th percentile
        percentile_95: 95th percentile (upside case)
        histogram_bins: Histogram bin edges for visualization
        histogram_counts: Histogram counts per bin
    """
    iterations: int
    npv_array: np.ndarray
    probability_positive: float
    mean_npv: float
    median_npv: float
    std_npv: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    histogram_bins: np.ndarray
    histogram_counts: np.ndarray


@dataclass
class TimelineInputs:
    """
    Development timeline inputs for cash flow generation.

    Attributes:
        predevelopment_months: Predevelopment phase duration
        construction_months: Construction phase duration
        lease_up_months: Lease-up phase duration
        operations_years: Stabilized operations years before sale
    """
    predevelopment_months: int = 6
    construction_months: int = 18
    lease_up_months: int = 6
    operations_years: int = 10


# ============================================================================
# Core Financial Calculation Functions
# ============================================================================


def calculate_npv(
    cash_flows: List[float],
    discount_rate: float,
    initial_investment: float
) -> float:
    """
    Calculate Net Present Value (NPV).

    Formula:
        NPV = -Initial Investment + Σ(CFt / (1+r)^t)

    where:
        CFt = cash flow in period t
        r = discount rate (annual)
        t = time period (years)

    Args:
        cash_flows: Annual cash flows starting from Year 1
        discount_rate: Annual discount rate (e.g., 0.12 for 12%)
        initial_investment: Initial capital outlay (positive number)

    Returns:
        NPV in dollars (positive = profitable, negative = unprofitable)

    Examples:
        >>> calculate_npv([100, 100, 100], 0.10, 200)
        48.68518518518519
        >>> calculate_npv([50, 50, 50], 0.10, 200)
        -75.6574074074074
    """
    if not cash_flows:
        return -initial_investment

    # Convert to numpy array for vectorized calculation
    cf_array = np.array(cash_flows, dtype=float)
    periods = np.arange(1, len(cf_array) + 1)

    # Calculate present value of each cash flow
    discount_factors = (1 + discount_rate) ** periods
    present_values = cf_array / discount_factors

    # NPV = -Initial Investment + Sum of PVs
    npv = -initial_investment + np.sum(present_values)

    return float(npv)


def calculate_irr(
    cash_flows: List[float],
    initial_investment: float,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> Optional[float]:
    """
    Calculate Internal Rate of Return (IRR) using Newton-Raphson method.

    IRR is the discount rate where NPV = 0. Solved iteratively using:
        r_{n+1} = r_n - f(r_n) / f'(r_n)

    where:
        f(r) = NPV function
        f'(r) = derivative of NPV function

    Args:
        cash_flows: Annual cash flows starting from Year 1
        initial_investment: Initial capital outlay (positive number)
        max_iterations: Maximum iterations for convergence
        tolerance: Convergence tolerance

    Returns:
        IRR as decimal (e.g., 0.185 for 18.5%) or None if no solution

    Examples:
        >>> calculate_irr([100, 100, 100], 200)
        0.2311...
    """
    if not cash_flows:
        return None

    # Construct full cash flow array including initial investment
    full_cf = np.array([-initial_investment] + cash_flows, dtype=float)

    # Use numpy_financial.irr if available, otherwise scipy.optimize
    try:
        # Try using numpy.irr (deprecated but still available in some versions)
        # More robust: use scipy.optimize.newton

        def npv_func(rate):
            """NPV as a function of discount rate."""
            periods = np.arange(len(full_cf))
            discount_factors = (1 + rate) ** periods
            return np.sum(full_cf / discount_factors)

        def npv_derivative(rate):
            """Derivative of NPV with respect to discount rate."""
            periods = np.arange(len(full_cf))
            discount_factors = (1 + rate) ** (periods + 1)
            return -np.sum(periods * full_cf / discount_factors)

        # Initial guess: 10% IRR
        irr = optimize.newton(
            npv_func,
            x0=0.10,
            fprime=npv_derivative,
            maxiter=max_iterations,
            tol=tolerance,
        )

        # Validate result
        if np.isnan(irr) or np.isinf(irr):
            return None

        return float(irr)

    except (RuntimeError, ValueError) as e:
        # Newton's method failed to converge
        logger.warning(f"IRR calculation failed to converge: {e}")
        return None


def calculate_payback_period(
    cash_flows: List[float],
    initial_investment: float
) -> float:
    """
    Calculate payback period in years (with fractional year interpolation).

    Payback period is the time it takes for cumulative cash flows to equal
    the initial investment. Uses linear interpolation for fractional year.

    Args:
        cash_flows: Annual cash flows starting from Year 1
        initial_investment: Initial capital outlay (positive number)

    Returns:
        Payback period in years (e.g., 7.3 years). Returns inf if never paid back.

    Examples:
        >>> calculate_payback_period([50, 50, 50, 50, 50], 200)
        4.0
        >>> calculate_payback_period([50, 50, 100, 100], 175)
        2.75
    """
    if not cash_flows:
        return float('inf')

    cumulative = 0.0
    for i, cf in enumerate(cash_flows):
        previous_cumulative = cumulative
        cumulative += cf

        # Check if we've crossed the payback threshold
        if cumulative >= initial_investment:
            # Linear interpolation for fractional year
            # How much of this year's cash flow was needed?
            remaining = initial_investment - previous_cumulative
            fraction = remaining / cf if cf > 0 else 0

            return float(i + fraction)

    # Never paid back
    return float('inf')


def calculate_profitability_index(
    npv: float,
    initial_investment: float
) -> float:
    """
    Calculate Profitability Index (PI).

    Formula:
        PI = (NPV + Initial Investment) / Initial Investment

    Equivalently:
        PI = PV of future cash flows / Initial Investment

    Interpretation:
        PI > 1.0: Project adds value
        PI = 1.0: Breakeven
        PI < 1.0: Project destroys value

    Args:
        npv: Net Present Value
        initial_investment: Initial capital outlay (positive number)

    Returns:
        Profitability Index (e.g., 1.25 = $1.25 return per $1 invested)

    Examples:
        >>> calculate_profitability_index(100, 400)
        1.25
        >>> calculate_profitability_index(0, 400)
        1.0
    """
    if initial_investment <= 0:
        raise ValueError("Initial investment must be positive")

    pi = (npv + initial_investment) / initial_investment
    return float(pi)


# ============================================================================
# Sensitivity Analysis Functions
# ============================================================================


def calculate_tornado_sensitivity(
    base_scenario: Dict[str, Any],
    variables_to_test: List[SensitivityInput],
    npv_function: Callable[[Dict[str, Any]], float]
) -> List[TornadoResult]:
    """
    Perform one-way sensitivity analysis (Tornado diagram).

    For each variable:
    1. Calculate NPV at base_value - delta
    2. Calculate NPV at base_value + delta
    3. Compute impact = |upside_npv - downside_npv|
    4. Sort results by impact (largest first)

    Args:
        base_scenario: Base case parameters as dict
        variables_to_test: List of variables to test with delta percentages
        npv_function: Function that takes scenario dict and returns NPV

    Returns:
        List of TornadoResult sorted by impact (descending)

    Example:
        >>> def simple_npv(params):
        ...     return params['revenue'] - params['cost']
        >>> base = {'revenue': 1000, 'cost': 800}
        >>> variables = [
        ...     SensitivityInput('revenue', 1000, 0.10, 'Revenue'),
        ...     SensitivityInput('cost', 800, 0.10, 'Cost')
        ... ]
        >>> results = calculate_tornado_sensitivity(base, variables, simple_npv)
        >>> len(results)
        2
    """
    results = []

    # Calculate base NPV
    base_npv = npv_function(base_scenario)

    for variable in variables_to_test:
        # Create scenario copies for testing
        downside_scenario = base_scenario.copy()
        upside_scenario = base_scenario.copy()

        # Calculate downside and upside values
        downside_value = variable.base_value * (1 - variable.delta_pct)
        upside_value = variable.base_value * (1 + variable.delta_pct)

        # Update scenarios
        downside_scenario[variable.variable_name] = downside_value
        upside_scenario[variable.variable_name] = upside_value

        # Calculate NPVs
        downside_npv = npv_function(downside_scenario)
        upside_npv = npv_function(upside_scenario)

        # Calculate impact
        impact = abs(upside_npv - downside_npv)

        results.append(TornadoResult(
            variable_name=variable.variable_name,
            label=variable.label,
            base_npv=base_npv,
            downside_npv=downside_npv,
            upside_npv=upside_npv,
            impact=impact,
            downside_value=downside_value,
            upside_value=upside_value
        ))

    # Sort by impact (descending)
    results.sort(key=lambda x: x.impact, reverse=True)

    return results


def run_monte_carlo_simulation(
    base_params: Dict[str, Any],
    monte_carlo_inputs: MonteCarloInputs,
    npv_function: Callable[[Dict[str, Any]], float]
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation with vectorized NumPy operations.

    Distributions used:
    - cost_per_sf: Normal(μ=base, σ=cost_per_sf_std)
    - rent_growth: Normal(μ=base, σ=rent_growth_std), clipped at 0
    - cap_rate: Triangular(min, mode, max)
    - construction_delay: Lognormal(μ=delay_mean, σ=delay_std)

    Args:
        base_params: Base case parameters
        monte_carlo_inputs: Monte Carlo configuration
        npv_function: Function that takes params dict and returns NPV

    Returns:
        MonteCarloResult with statistics and distribution

    Performance:
        Must complete 10,000 iterations in <2 seconds (vectorized NumPy).
    """
    # Set random seed for reproducibility
    np.random.seed(monte_carlo_inputs.seed)

    n = monte_carlo_inputs.iterations
    npv_results = np.zeros(n)

    # Pre-generate all random samples (vectorized)
    # Cost per SF: Normal distribution
    cost_per_sf_base = base_params.get('cost_per_sf', 400)
    cost_samples = np.random.normal(
        loc=cost_per_sf_base,
        scale=monte_carlo_inputs.cost_per_sf_std,
        size=n
    )

    # Rent growth: Normal distribution, clipped at 0
    rent_growth_base = base_params.get('rent_growth_rate', 0.03)
    rent_growth_samples = np.clip(
        np.random.normal(
            loc=rent_growth_base,
            scale=monte_carlo_inputs.rent_growth_std,
            size=n
        ),
        a_min=0,  # Can't have negative rent growth
        a_max=None
    )

    # Exit cap rate: Triangular distribution
    cap_rate_samples = np.random.triangular(
        left=monte_carlo_inputs.cap_rate_min,
        mode=monte_carlo_inputs.cap_rate_mode,
        right=monte_carlo_inputs.cap_rate_max,
        size=n
    )

    # Construction delay: Lognormal distribution (in months)
    # Lognormal is used because delays are always positive and right-skewed
    if monte_carlo_inputs.construction_delay_std > 0:
        # Convert mean and std to lognormal parameters
        mu = monte_carlo_inputs.construction_delay_mean
        sigma = monte_carlo_inputs.construction_delay_std

        # For lognormal, if X ~ Lognormal(μ, σ²), then:
        # E[X] = exp(μ + σ²/2)
        # Var[X] = (exp(σ²) - 1) * exp(2μ + σ²)
        # We want to parameterize by mean and std of the delay
        # For small delays, approximate with normal clamped at 0
        delay_samples = np.maximum(
            np.random.normal(loc=mu, scale=sigma, size=n),
            0
        )
    else:
        delay_samples = np.zeros(n)

    # Run iterations (can't fully vectorize NPV calculation due to complex logic)
    # However, we can batch process to minimize overhead
    for i in range(n):
        # Create scenario with sampled parameters
        scenario = base_params.copy()
        scenario['cost_per_sf'] = cost_samples[i]
        scenario['rent_growth_rate'] = rent_growth_samples[i]
        scenario['exit_cap_rate'] = cap_rate_samples[i]
        scenario['construction_delay_months'] = delay_samples[i]

        # Calculate NPV for this scenario
        npv_results[i] = npv_function(scenario)

    # Calculate statistics
    probability_positive = float(np.mean(npv_results > 0))
    mean_npv = float(np.mean(npv_results))
    median_npv = float(np.median(npv_results))
    std_npv = float(np.std(npv_results))

    # Calculate percentiles
    percentile_5 = float(np.percentile(npv_results, 5))
    percentile_25 = float(np.percentile(npv_results, 25))
    percentile_75 = float(np.percentile(npv_results, 75))
    percentile_95 = float(np.percentile(npv_results, 95))

    # Generate histogram for visualization
    # Use 50 bins for good granularity
    histogram_counts, histogram_bins = np.histogram(npv_results, bins=50)

    return MonteCarloResult(
        iterations=n,
        npv_array=npv_results,
        probability_positive=probability_positive,
        mean_npv=mean_npv,
        median_npv=median_npv,
        std_npv=std_npv,
        percentile_5=percentile_5,
        percentile_25=percentile_25,
        percentile_75=percentile_75,
        percentile_95=percentile_95,
        histogram_bins=histogram_bins,
        histogram_counts=histogram_counts
    )


# ============================================================================
# Development Cash Flow Functions
# ============================================================================


def generate_development_cash_flows(
    total_construction_cost: float,
    annual_noi: float,
    timeline: TimelineInputs,
    exit_cap_rate: float,
    soft_cost_pct: float = 0.20,
    predevelopment_spend_pct: float = 0.50
) -> List[CashFlow]:
    """
    Generate period-by-period cash flows for a development project.

    Timeline phases:
    1. Predevelopment: negative cash flow (soft costs × predevelopment_spend_pct)
    2. Construction: negative cash flow (hard costs + remaining soft costs, linear draws)
    3. Lease-up: partial revenue (ramp from 0% to 100%), full expenses
    4. Operations: stabilized NOI for N years
    5. Exit: sale proceeds (NOI / cap_rate)

    Args:
        total_construction_cost: Total development cost (hard + soft)
        annual_noi: Stabilized annual Net Operating Income
        timeline: Development timeline parameters
        exit_cap_rate: Exit cap rate for sale valuation
        soft_cost_pct: Soft costs as % of total cost (default 20%)
        predevelopment_spend_pct: % of soft costs spent in predevelopment (default 50%)

    Returns:
        List of CashFlow objects with period-by-period breakdown

    Example:
        >>> timeline = TimelineInputs(6, 18, 6, 10)
        >>> cfs = generate_development_cash_flows(5_000_000, 500_000, timeline, 0.05)
        >>> len(cfs) > 0
        True
    """
    cash_flows = []
    cumulative = 0.0
    period = 0

    # Calculate cost components
    soft_costs = total_construction_cost * soft_cost_pct
    hard_costs = total_construction_cost - soft_costs
    predevelopment_costs = soft_costs * predevelopment_spend_pct
    construction_soft_costs = soft_costs - predevelopment_costs

    # Phase 1: Predevelopment
    predevelopment_years = timeline.predevelopment_months / 12.0
    if predevelopment_years > 0:
        cash_flows.append(CashFlow(
            period=period,
            description=f"Predevelopment ({timeline.predevelopment_months} months)",
            amount=-predevelopment_costs,
            cumulative=cumulative - predevelopment_costs,
            phase="predevelopment"
        ))
        cumulative -= predevelopment_costs
        period += 1

    # Phase 2: Construction
    construction_years = timeline.construction_months / 12.0
    construction_periods = int(np.ceil(construction_years))

    total_construction_outlay = hard_costs + construction_soft_costs
    construction_draw_per_period = total_construction_outlay / construction_periods

    for i in range(construction_periods):
        cash_flows.append(CashFlow(
            period=period,
            description=f"Construction Year {i+1}",
            amount=-construction_draw_per_period,
            cumulative=cumulative - construction_draw_per_period,
            phase="construction"
        ))
        cumulative -= construction_draw_per_period
        period += 1

    # Phase 3: Lease-up
    lease_up_years = timeline.lease_up_months / 12.0
    lease_up_periods = int(np.ceil(lease_up_years))

    for i in range(lease_up_periods):
        # Linear ramp from 0% to 100% occupancy
        occupancy_pct = (i + 1) / lease_up_periods
        lease_up_noi = annual_noi * occupancy_pct

        cash_flows.append(CashFlow(
            period=period,
            description=f"Lease-up Year {i+1} ({occupancy_pct*100:.0f}% occupied)",
            amount=lease_up_noi,
            cumulative=cumulative + lease_up_noi,
            phase="lease_up"
        ))
        cumulative += lease_up_noi
        period += 1

    # Phase 4: Stabilized Operations
    for i in range(timeline.operations_years):
        cash_flows.append(CashFlow(
            period=period,
            description=f"Operations Year {i+1}",
            amount=annual_noi,
            cumulative=cumulative + annual_noi,
            phase="operations"
        ))
        cumulative += annual_noi
        period += 1

    # Phase 5: Exit (Sale)
    exit_value = calculate_exit_value(annual_noi, exit_cap_rate)

    cash_flows.append(CashFlow(
        period=period,
        description=f"Exit (Sale at {exit_cap_rate*100:.1f}% cap rate)",
        amount=exit_value,
        cumulative=cumulative + exit_value,
        phase="exit"
    ))

    return cash_flows


def calculate_exit_value(
    stabilized_noi: float,
    exit_cap_rate: float
) -> float:
    """
    Calculate exit value using direct capitalization.

    Formula:
        Exit Value = Stabilized Annual NOI / Cap Rate

    This is the standard direct capitalization method used in real estate.

    Args:
        stabilized_noi: Stabilized annual Net Operating Income
        exit_cap_rate: Exit cap rate (e.g., 0.05 for 5%)

    Returns:
        Exit value (property sale price)

    Examples:
        >>> calculate_exit_value(500_000, 0.05)
        10000000.0
        >>> calculate_exit_value(100_000, 0.06)
        1666666.6666666667
    """
    if exit_cap_rate <= 0:
        raise ValueError("Exit cap rate must be positive")

    return stabilized_noi / exit_cap_rate


# ============================================================================
# Utility Functions
# ============================================================================


def format_currency(amount: float) -> str:
    """
    Format number as currency string.

    Args:
        amount: Dollar amount

    Returns:
        Formatted string (e.g., "$1,234,567")

    Examples:
        >>> format_currency(1234567.89)
        '$1,234,568'
        >>> format_currency(-5000)
        '-$5,000'
    """
    sign = '-' if amount < 0 else ''
    abs_amount = abs(amount)
    return f"{sign}${abs_amount:,.0f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format decimal as percentage string.

    Args:
        value: Decimal value (e.g., 0.185)
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "18.5%")

    Examples:
        >>> format_percentage(0.185)
        '18.5%'
        >>> format_percentage(0.185, 2)
        '18.50%'
    """
    pct = value * 100
    return f"{pct:.{decimals}f}%"
