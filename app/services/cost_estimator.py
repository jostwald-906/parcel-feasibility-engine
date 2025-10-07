"""
Construction Cost Estimation Service

Rigorous, transparent construction cost estimation with detailed breakdown.

Cost Structure:
1. Hard Costs: Direct construction costs (materials + labor)
   - Base cost per SF escalated by PPI (materials)
   - Optional wage escalation (ECI)
   - Construction type multiplier
   - Location factor
   - Common area factor

2. Soft Costs: Indirect development costs
   - Architecture & Engineering
   - Permits & Fees
   - Construction Financing
   - Legal & Consulting
   - Developer Fee

3. Contingency: Reserve for unknowns

Formulas:
    Hard Cost = ref_cost_per_sf
                × (latest_PPI / base_PPI)
                × wage_factor (if enabled)
                × location_factor
                × construction_type_factor
                × total_buildable_sf
                × common_area_factor

    Soft Costs = Architecture + Permits + Financing + Legal + Developer Fee

    Total Cost = Hard Cost + Soft Cost + Contingency

References:
- FRED WPUSI012011: Construction Materials PPI
- FRED ECICONWAG: Construction Wages & Salaries ECI
- FRED DGS10: 10-Year Treasury Rate
- RAND Corporation: California construction cost study (2.3x national average)
"""
from app.models.financial import (
    ConstructionInputs,
    EconomicAssumptions,
    ConstructionCostEstimate,
    HardCostBreakdown,
    SoftCostBreakdown,
)
from app.services.fred_client import FredClient, get_fred_client
from app.core.config import settings
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_construction_type_factor(construction_type: str) -> float:
    """
    Return cost multiplier for construction type.

    Args:
        construction_type: One of 'wood_frame', 'concrete', 'steel'

    Returns:
        Cost multiplier (1.0 = baseline, >1.0 = more expensive)
    """
    factors = {
        "wood_frame": 1.0,  # Baseline (most common for multifamily)
        "concrete": 1.25,  # 25% more expensive (durability, fire resistance)
        "steel": 1.15,  # 15% more expensive (speed, strength)
    }
    return factors.get(construction_type, 1.0)


def calculate_construction_financing(
    principal: float,
    annual_rate: float,
    duration_years: float,
) -> float:
    """
    Calculate interest cost on construction loan.

    Uses average outstanding balance method (assumes linear drawdown).

    Formula:
        Interest = Principal × Rate × Duration / 2

    Args:
        principal: Total loan amount (hard cost)
        annual_rate: Annual interest rate (decimal, e.g., 0.065 for 6.5%)
        duration_years: Construction duration in years

    Returns:
        Total interest cost
    """
    # Average outstanding balance = half of principal (linear drawdown)
    avg_balance = principal / 2
    interest_cost = avg_balance * annual_rate * duration_years
    return interest_cost


async def get_escalation_factor(
    fred_client: FredClient,
    use_ccci: bool = False,
    ccci_client: Optional[any] = None,
) -> Tuple[float, str]:
    """
    Get cost escalation factor and source note.

    Args:
        fred_client: FRED API client for PPI data
        use_ccci: If True, use CCCI escalation (requires ccci_client)
        ccci_client: Optional CCCI client (not yet implemented)

    Returns:
        Tuple of (escalation_factor, source_note)
    """
    if use_ccci and ccci_client:
        # TODO: Implement CCCI escalation
        logger.warning("CCCI escalation not yet implemented, falling back to FRED PPI")

    # Get latest PPI observation
    try:
        ppi_obs = fred_client.get_latest_observation("WPUSI012011")
        latest_ppi = ppi_obs.value
        ppi_date = ppi_obs.date

        # Calculate escalation factor
        escalation_factor = latest_ppi / settings.REF_PPI_VALUE

        source_note = (
            f"WPUSI012011 @ {latest_ppi:.1f} (FRED {ppi_date.isoformat()}) "
            f"÷ {settings.REF_PPI_VALUE:.1f} baseline = {escalation_factor:.3f}x"
        )

        logger.info(
            f"Materials escalation: {escalation_factor:.3f}x",
            extra={"ppi_latest": latest_ppi, "ppi_base": settings.REF_PPI_VALUE},
        )

        return escalation_factor, source_note

    except Exception as e:
        logger.error(f"Failed to fetch FRED PPI data: {e}", exc_info=True)
        # Fallback to no escalation
        return 1.0, f"PPI data unavailable, using 1.0x baseline (error: {e})"


async def get_wage_escalation_factor(fred_client: FredClient) -> Tuple[float, str]:
    """
    Get wage escalation factor from FRED ECI data.

    Args:
        fred_client: FRED API client

    Returns:
        Tuple of (wage_escalation_factor, source_note)
    """
    try:
        eci_obs = fred_client.get_latest_observation("ECICONWAG")
        latest_eci = eci_obs.value
        eci_date = eci_obs.date

        # Use 2018 base (typical baseline year)
        base_eci = 125.0  # Approximate 2018 baseline
        wage_factor = latest_eci / base_eci

        source_note = (
            f"ECICONWAG @ {latest_eci:.1f} (FRED {eci_date.isoformat()}) "
            f"÷ {base_eci:.1f} baseline = {wage_factor:.3f}x"
        )

        logger.info(
            f"Wage escalation: {wage_factor:.3f}x",
            extra={"eci_latest": latest_eci, "eci_base": base_eci},
        )

        return wage_factor, source_note

    except Exception as e:
        logger.error(f"Failed to fetch FRED ECI data: {e}", exc_info=True)
        return 1.0, f"ECI data unavailable, using 1.0x baseline (error: {e})"


async def get_construction_financing_rate(fred_client: FredClient) -> Tuple[float, str]:
    """
    Get construction financing rate from FRED 10Y Treasury + spread.

    Args:
        fred_client: FRED API client

    Returns:
        Tuple of (annual_rate, source_note)
    """
    try:
        dgs10_obs = fred_client.get_latest_observation("DGS10")
        treasury_rate = dgs10_obs.value / 100  # Convert percent to decimal
        dgs10_date = dgs10_obs.date

        # Add construction loan spread
        spread = settings.CONSTRUCTION_LOAN_SPREAD
        construction_rate = treasury_rate + spread

        source_note = (
            f"DGS10 {dgs10_obs.value:.2f}% (FRED {dgs10_date.isoformat()}) "
            f"+ {spread*100:.1f}% spread = {construction_rate*100:.2f}%"
        )

        logger.info(
            f"Construction financing rate: {construction_rate*100:.2f}%",
            extra={"treasury_rate": treasury_rate, "spread": spread},
        )

        return construction_rate, source_note

    except Exception as e:
        logger.error(f"Failed to fetch FRED Treasury rate: {e}", exc_info=True)
        # Fallback to reasonable default
        default_rate = 0.065  # 6.5%
        return default_rate, f"Treasury rate unavailable, using {default_rate*100:.1f}% default"


async def estimate_construction_cost(
    inputs: ConstructionInputs,
    assumptions: EconomicAssumptions,
    fred_client: Optional[FredClient] = None,
) -> ConstructionCostEstimate:
    """
    Estimate total construction costs with detailed breakdown.

    Formula:
        Hard_Cost = ref_cost_per_sf
                    × (latest_PPI / base_PPI)
                    × wage_factor (if enabled)
                    × location_factor
                    × construction_type_factor
                    × total_buildable_sf
                    × common_area_factor

    Args:
        inputs: Construction project inputs
        assumptions: Economic assumptions
        fred_client: Optional FRED client (creates one if not provided)

    Returns:
        ConstructionCostEstimate with comprehensive breakdown

    Example:
        >>> inputs = ConstructionInputs(
        ...     buildable_sqft=10000,
        ...     num_units=10,
        ...     construction_type="wood_frame",
        ...     location_factor=2.3,
        ...     permit_fees_per_unit=5000,
        ...     construction_duration_months=18
        ... )
        >>> assumptions = EconomicAssumptions(use_wage_adjustment=False)
        >>> estimate = await estimate_construction_cost(inputs, assumptions)
        >>> print(f"Total cost: ${estimate.total_cost:,.0f}")
    """
    # Initialize FRED client if not provided
    if fred_client is None:
        fred_client = get_fred_client(
            api_key=settings.FRED_API_KEY,
            use_live_data=settings.FRED_API_ENABLED,
        )

    # Get cost parameters from settings or assumptions
    ref_cost_per_sf = settings.REF_COST_PER_SF
    architecture_pct = assumptions.architecture_pct or settings.ARCHITECTURE_PCT
    legal_pct = assumptions.legal_pct or settings.LEGAL_PCT
    developer_fee_pct = assumptions.developer_fee_pct or settings.DEVELOPER_FEE_PCT
    contingency_pct = assumptions.contingency_pct or settings.CONTINGENCY_PCT
    common_area_factor = settings.COMMON_AREA_FACTOR

    # Build source notes
    source_notes: Dict[str, str] = {}
    source_notes["base_cost_per_sf"] = f"${ref_cost_per_sf:.0f} (2025 US baseline)"
    source_notes["location_factor"] = f"{inputs.location_factor:.1f}x (user input, RAND CA avg 2.3x)"

    # =========================================================================
    # 1. HARD COSTS CALCULATION
    # =========================================================================

    # Get materials escalation factor (PPI)
    materials_escalation, materials_note = await get_escalation_factor(
        fred_client, use_ccci=assumptions.use_ccci
    )
    source_notes["materials_ppi_series"] = materials_note

    # Get wage escalation factor (optional)
    if assumptions.use_wage_adjustment:
        wage_escalation, wage_note = await get_wage_escalation_factor(fred_client)
        source_notes["wage_eci_series"] = wage_note
    else:
        wage_escalation = 1.0
        source_notes["wage_eci_series"] = "Not applied (use_wage_adjustment=False)"

    # Get construction type factor
    construction_type_factor = calculate_construction_type_factor(inputs.construction_type)
    source_notes["construction_type"] = (
        f"{inputs.construction_type} (factor: {construction_type_factor:.2f}x)"
    )

    # Calculate total SF with common area
    total_sf = inputs.buildable_sqft * common_area_factor
    source_notes["total_buildable_sf"] = (
        f"{inputs.buildable_sqft:,.0f} SF × {common_area_factor:.2f} common area = {total_sf:,.0f} SF"
    )

    # Calculate total hard cost
    hard_cost_per_sf = (
        ref_cost_per_sf
        * materials_escalation
        * wage_escalation
        * inputs.location_factor
        * construction_type_factor
    )
    total_hard_cost = hard_cost_per_sf * total_sf

    hard_costs = HardCostBreakdown(
        base_cost_per_sf=ref_cost_per_sf,
        materials_escalation_factor=materials_escalation,
        wage_escalation_factor=wage_escalation,
        construction_type_factor=construction_type_factor,
        location_factor=inputs.location_factor,
        common_area_factor=common_area_factor,
        total_sf=total_sf,
        total_hard_cost=total_hard_cost,
    )

    logger.info(
        f"Hard costs calculated: ${total_hard_cost:,.0f}",
        extra={
            "hard_cost_per_sf": hard_cost_per_sf,
            "total_sf": total_sf,
        },
    )

    # =========================================================================
    # 2. SOFT COSTS CALCULATION
    # =========================================================================

    # Architecture & Engineering
    architecture_cost = total_hard_cost * architecture_pct
    source_notes["architecture_engineering"] = f"{architecture_pct*100:.0f}% of hard cost"

    # Permits & Fees
    permits_cost = inputs.permit_fees_per_unit * inputs.num_units
    source_notes["permits_fees"] = f"${inputs.permit_fees_per_unit:,.0f}/unit × {inputs.num_units} units"

    # Construction Financing
    construction_rate, rate_note = await get_construction_financing_rate(fred_client)
    source_notes["interest_rate"] = rate_note

    construction_duration_years = inputs.construction_duration_months / 12
    financing_cost = calculate_construction_financing(
        principal=total_hard_cost,
        annual_rate=construction_rate,
        duration_years=construction_duration_years,
    )
    source_notes["construction_financing"] = (
        f"${total_hard_cost:,.0f} × {construction_rate*100:.2f}% × "
        f"{construction_duration_years:.2f} years ÷ 2 (avg outstanding)"
    )

    # Legal & Consulting
    legal_cost = total_hard_cost * legal_pct
    source_notes["legal_consulting"] = f"{legal_pct*100:.0f}% of hard cost"

    # Calculate subtotal before developer fee
    subtotal_before_dev_fee = (
        total_hard_cost + architecture_cost + permits_cost + financing_cost + legal_cost
    )

    # Developer Fee (on hard + soft)
    developer_fee = subtotal_before_dev_fee * developer_fee_pct
    source_notes["developer_fee"] = (
        f"{developer_fee_pct*100:.0f}% of (hard + soft before dev fee)"
    )

    # Total soft costs
    total_soft_cost = (
        architecture_cost + permits_cost + financing_cost + legal_cost + developer_fee
    )

    soft_costs = SoftCostBreakdown(
        architecture_engineering=architecture_cost,
        permits_fees=permits_cost,
        construction_financing=financing_cost,
        legal_consulting=legal_cost,
        developer_fee=developer_fee,
        total_soft_cost=total_soft_cost,
    )

    logger.info(
        f"Soft costs calculated: ${total_soft_cost:,.0f}",
        extra={
            "architecture": architecture_cost,
            "permits": permits_cost,
            "financing": financing_cost,
            "legal": legal_cost,
            "developer_fee": developer_fee,
        },
    )

    # =========================================================================
    # 3. CONTINGENCY
    # =========================================================================

    subtotal = total_hard_cost + total_soft_cost
    contingency_amount = subtotal * contingency_pct
    source_notes["contingency"] = f"{contingency_pct*100:.0f}% of (hard + soft)"

    # =========================================================================
    # 4. TOTAL COST
    # =========================================================================

    total_cost = subtotal + contingency_amount
    cost_per_unit = total_cost / inputs.num_units
    cost_per_buildable_sf = total_cost / inputs.buildable_sqft

    logger.info(
        f"Construction cost estimate complete: ${total_cost:,.0f}",
        extra={
            "cost_per_unit": cost_per_unit,
            "cost_per_sf": cost_per_buildable_sf,
            "num_units": inputs.num_units,
        },
    )

    return ConstructionCostEstimate(
        total_cost=total_cost,
        cost_per_unit=cost_per_unit,
        cost_per_buildable_sf=cost_per_buildable_sf,
        hard_costs=hard_costs,
        soft_costs=soft_costs,
        contingency_amount=contingency_amount,
        contingency_pct=contingency_pct,
        source_notes=source_notes,
    )
