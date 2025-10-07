"""
Revenue Projection Service

Projects annual revenue and Net Operating Income (NOI) for residential developments
using market-rate and affordable housing rent assumptions.

Data Sources:
- Market Rents: HUD Fair Market Rent (FMR) API with quality adjustments
- Affordable Rents: HCD Income Limits via AMI Calculator (30% of income standard)
- Operating Expenses: Industry-standard ratios and California-specific costs

Key Formulas:
- Gross Potential Income (GPI): Sum of all units × monthly rent × 12
- Effective Gross Income (EGI): GPI × (1 - vacancy_rate)
- Net Operating Income (NOI): EGI - Operating Expenses

Operating Expense Components:
- Property Tax: Assessed value × tax_rate (Prop 13: 1% base + local add-ons)
- Insurance: Replacement cost × 0.006 (0.6% of replacement cost)
- Management: EGI × 0.05 (5% of effective gross income)
- Utilities: $800/unit/year (if landlord-paid)
- Maintenance & Repairs: $1,200/unit/year
- Reserves: $500/unit/year
- Marketing & Leasing: $200/unit/year

References:
- 24 CFR Part 888: Fair Market Rent methodology (40th percentile)
- Gov. Code § 50053: Affordable housing income standards
- Prop 13 (Art. XIII A): Property tax assessment (1% + voter-approved)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
from app.clients.hud_fmr_client import HudFMRClient, FMRData
from app.services.ami_calculator import AMICalculator
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RevenueInputs(BaseModel):
    """Revenue calculation inputs."""

    # Location
    zip_code: str = Field(..., description="ZIP code for FMR lookup")
    county: str = Field(..., description="County for AMI limits")

    # Unit mix
    market_unit_mix: Dict[int, int] = Field(
        default_factory=dict,
        description="Market-rate units by bedroom count {bedrooms: count}"
    )
    affordable_unit_mix: Dict[int, int] = Field(
        default_factory=dict,
        description="Affordable units by bedroom count {bedrooms: count}"
    )

    # Affordability levels for affordable units
    ami_percentages: List[float] = Field(
        default=[50.0, 60.0, 80.0],
        description="AMI percentages for affordable units"
    )

    # Market-rate quality adjustment
    quality_factor: float = Field(
        1.0,
        ge=0.8,
        le=1.2,
        description="Quality adjustment factor (0.8-1.2): 0.8-0.9=Class C, 0.9-1.0=Class B, 1.0-1.2=Class A"
    )

    # Operating parameters
    utility_allowance: float = Field(
        150.0,
        ge=0,
        description="Monthly utility allowance for affordable units"
    )

    @property
    def total_units(self) -> int:
        """Total units in development."""
        return sum(self.market_unit_mix.values()) + sum(self.affordable_unit_mix.values())

    @property
    def market_units(self) -> int:
        """Total market-rate units."""
        return sum(self.market_unit_mix.values())

    @property
    def affordable_units(self) -> int:
        """Total affordable units."""
        return sum(self.affordable_unit_mix.values())


class EconomicAssumptions(BaseModel):
    """Economic assumptions for revenue projections."""

    # Vacancy and collection
    vacancy_rate: float = Field(
        0.05,
        ge=0,
        le=0.20,
        description="Vacancy and collection loss rate (typical: 5%)"
    )

    # Property tax (California Prop 13)
    property_tax_rate: float = Field(
        0.0125,
        ge=0.01,
        le=0.03,
        description="Property tax rate (Prop 13: 1% base + local add-ons, typical: 1.25%)"
    )

    # Operating expense ratios
    insurance_rate: float = Field(
        0.006,
        ge=0,
        description="Insurance rate as % of replacement cost (typical: 0.6%)"
    )
    management_rate: float = Field(
        0.05,
        ge=0,
        le=0.10,
        description="Management rate as % of EGI (typical: 5%)"
    )

    # Per-unit annual costs
    utilities_per_unit_annual: float = Field(
        800.0,
        ge=0,
        description="Annual utilities per unit if landlord-paid"
    )
    maintenance_per_unit_annual: float = Field(
        1200.0,
        ge=0,
        description="Annual maintenance and repairs per unit"
    )
    reserves_per_unit_annual: float = Field(
        500.0,
        ge=0,
        description="Annual reserves for replacement per unit"
    )
    marketing_per_unit_annual: float = Field(
        200.0,
        ge=0,
        description="Annual marketing and leasing per unit"
    )

    # Construction cost for insurance calculation
    construction_cost_per_sqft: float = Field(
        350.0,
        ge=0,
        description="Construction cost per sq ft for insurance basis"
    )

    # Growth rates for multi-year projections
    rent_growth_rate: float = Field(
        0.03,
        ge=0,
        le=0.10,
        description="Annual rent growth rate (typical: 3%)"
    )
    expense_growth_rate: float = Field(
        0.025,
        ge=0,
        le=0.10,
        description="Annual expense growth rate (typical: 2.5%)"
    )


class OperatingExpenses(BaseModel):
    """Operating expense breakdown."""

    property_tax: float = Field(..., description="Annual property tax")
    insurance: float = Field(..., description="Annual insurance")
    management: float = Field(..., description="Annual management fees")
    utilities: float = Field(..., description="Annual utilities (if landlord-paid)")
    maintenance: float = Field(..., description="Annual maintenance and repairs")
    reserves: float = Field(..., description="Annual reserves for replacement")
    marketing: float = Field(..., description="Annual marketing and leasing")

    @property
    def total(self) -> float:
        """Total annual operating expenses."""
        return (
            self.property_tax +
            self.insurance +
            self.management +
            self.utilities +
            self.maintenance +
            self.reserves +
            self.marketing
        )


class RevenueProjection(BaseModel):
    """Revenue projection result."""

    # Income
    gross_potential_income: float = Field(..., description="Annual gross potential income")
    vacancy_loss: float = Field(..., description="Annual vacancy loss")
    effective_gross_income: float = Field(..., description="Annual effective gross income")

    # Expenses
    operating_expenses: OperatingExpenses = Field(..., description="Operating expense breakdown")
    total_operating_expenses: float = Field(..., description="Total annual operating expenses")

    # NOI
    net_operating_income: float = Field(..., description="Annual net operating income")

    # Per-unit metrics
    gpi_per_unit: float = Field(..., description="GPI per unit")
    noi_per_unit: float = Field(..., description="NOI per unit")

    # Rent breakdown
    market_rents: Dict[str, float] = Field(
        ...,
        description="Market rents by bedroom type (studio, 1br, 2br, etc.)"
    )
    affordable_rents: Dict[str, float] = Field(
        ...,
        description="Affordable rents by bedroom type"
    )

    # Multi-year projections (optional)
    projections: Optional[List[Dict[str, float]]] = Field(
        None,
        description="Multi-year NOI projections with growth"
    )

    # Source documentation
    source_notes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Source documentation for all assumptions"
    )


async def calculate_market_rents(
    zip_code: str,
    unit_mix: Dict[int, int],
    quality_factor: float,
    hud_client: HudFMRClient
) -> tuple[Dict[str, float], FMRData]:
    """
    Calculate market rents using HUD FMR data with quality adjustments.

    Quality Factor Ranges:
    - 0.8-0.9: Class C (below market, older construction)
    - 0.9-1.0: Class B (market average)
    - 1.0-1.2: Class A (above market, new construction)

    Args:
        zip_code: ZIP code for FMR lookup
        unit_mix: Units by bedroom count {bedrooms: count}
        quality_factor: Quality adjustment (0.8-1.2)
        hud_client: HUD FMR API client

    Returns:
        Tuple of (market_rents_dict, fmr_data)
        market_rents_dict: {"studio": rent, "1br": rent, ...}

    Examples:
        >>> market_rents, fmr_data = await calculate_market_rents(
        ...     "90401", {0: 5, 1: 10, 2: 15}, 1.0, client
        ... )
        >>> print(f"2BR rent: ${market_rents['2br']}")
        2BR rent: $2815
    """
    logger.info(
        "Calculating market rents",
        extra={"zip_code": zip_code, "quality_factor": quality_factor}
    )

    # Fetch FMR data
    fmr_data = await hud_client.get_fmr_by_zip(zip_code)

    # Calculate rents by bedroom type with quality adjustment
    market_rents = {}
    bedroom_labels = {
        0: "studio",
        1: "1br",
        2: "2br",
        3: "3br",
        4: "4br"
    }

    for bedrooms, count in unit_mix.items():
        if count > 0:
            # Get base FMR
            base_fmr = hud_client.get_fmr_for_bedroom(fmr_data, bedrooms)

            # Apply quality factor
            adjusted_rent = base_fmr * quality_factor

            # Store with label
            label = bedroom_labels.get(bedrooms, f"{bedrooms}br")
            market_rents[label] = adjusted_rent

            logger.info(
                f"Market rent calculated for {label}",
                extra={
                    "bedrooms": bedrooms,
                    "base_fmr": base_fmr,
                    "quality_factor": quality_factor,
                    "adjusted_rent": adjusted_rent,
                    "is_safmr": fmr_data.smallarea_status == 1
                }
            )

    return market_rents, fmr_data


def calculate_affordable_rents(
    county: str,
    unit_mix_affordable: Dict[int, int],
    ami_percentages: List[float],
    utility_allowance: float,
    ami_calculator: AMICalculator
) -> Dict[str, float]:
    """
    Calculate affordable rents using AMI calculator.

    Uses weighted average if multiple AMI levels provided.
    Applies 30% of income standard (rent burden threshold).

    Args:
        county: County for AMI limits
        unit_mix_affordable: Affordable units by bedroom {bedrooms: count}
        ami_percentages: AMI percentages (e.g., [50, 60, 80])
        utility_allowance: Monthly utility allowance
        ami_calculator: AMI calculator instance

    Returns:
        Dict of affordable rents by bedroom type

    Examples:
        >>> affordable_rents = calculate_affordable_rents(
        ...     "Los Angeles", {0: 2, 1: 5, 2: 8}, [50.0, 80.0], 150.0, calc
        ... )
        >>> print(f"2BR affordable rent: ${affordable_rents['2br']}")
        2BR affordable rent: $1182
    """
    logger.info(
        "Calculating affordable rents",
        extra={
            "county": county,
            "ami_percentages": ami_percentages,
            "utility_allowance": utility_allowance
        }
    )

    affordable_rents = {}
    bedroom_labels = {
        0: "studio",
        1: "1br",
        2: "2br",
        3: "3br",
        4: "4br"
    }

    for bedrooms, count in unit_mix_affordable.items():
        if count > 0:
            # Calculate rent for each AMI level
            rents = []
            for ami_pct in ami_percentages:
                rent_result = ami_calculator.calculate_max_rent(
                    county=county,
                    ami_pct=ami_pct,
                    bedrooms=bedrooms,
                    utility_allowance=utility_allowance
                )
                rents.append(rent_result.max_rent_no_utilities)

            # Use weighted average (or median) of AMI levels
            avg_rent = sum(rents) / len(rents)

            # Store with label
            label = bedroom_labels.get(bedrooms, f"{bedrooms}br")
            affordable_rents[label] = avg_rent

            logger.info(
                f"Affordable rent calculated for {label}",
                extra={
                    "bedrooms": bedrooms,
                    "ami_percentages": ami_percentages,
                    "rents_by_ami": rents,
                    "avg_rent": avg_rent
                }
            )

    return affordable_rents


def calculate_gross_income(
    market_rents: Dict[str, float],
    affordable_rents: Dict[str, float],
    market_unit_mix: Dict[int, int],
    affordable_unit_mix: Dict[int, int]
) -> float:
    """
    Calculate annual Gross Potential Income (GPI).

    GPI = Sum of all units × monthly rent × 12 months

    Args:
        market_rents: Market rents by bedroom label
        affordable_rents: Affordable rents by bedroom label
        market_unit_mix: Market units by bedroom count
        affordable_unit_mix: Affordable units by bedroom count

    Returns:
        Annual gross potential income

    Examples:
        >>> gpi = calculate_gross_income(
        ...     {"1br": 2500, "2br": 3000}, {"1br": 1200, "2br": 1500},
        ...     {1: 10, 2: 15}, {1: 5, 2: 3}
        ... )
        >>> print(f"Annual GPI: ${gpi:,.0f}")
        Annual GPI: $876,000
    """
    bedroom_labels = {0: "studio", 1: "1br", 2: "2br", 3: "3br", 4: "4br"}
    gpi = 0.0

    # Market-rate income
    for bedrooms, count in market_unit_mix.items():
        label = bedroom_labels.get(bedrooms, f"{bedrooms}br")
        if label in market_rents:
            monthly_rent = market_rents[label]
            annual_income = monthly_rent * count * 12
            gpi += annual_income

    # Affordable income
    for bedrooms, count in affordable_unit_mix.items():
        label = bedroom_labels.get(bedrooms, f"{bedrooms}br")
        if label in affordable_rents:
            monthly_rent = affordable_rents[label]
            annual_income = monthly_rent * count * 12
            gpi += annual_income

    return gpi


def calculate_property_tax(
    assessed_value: float,
    tax_rate: float
) -> float:
    """
    Calculate annual property tax (California Prop 13).

    Prop 13 (Article XIII A, California Constitution):
    - Base rate: 1% of assessed value
    - Local voter-approved add-ons: typically 0.1-0.5%
    - Total typical rate: 1.1-1.5%
    - Assessed value = acquisition cost + improvements
    - Annual increase capped at 2% (or inflation, whichever is less)

    Args:
        assessed_value: Property assessed value (land + improvements)
        tax_rate: Combined tax rate (base 1% + local add-ons)

    Returns:
        Annual property tax

    Examples:
        >>> tax = calculate_property_tax(10_000_000, 0.0125)
        >>> print(f"Annual property tax: ${tax:,.0f}")
        Annual property tax: $125,000
    """
    return assessed_value * tax_rate


def calculate_operating_expenses(
    num_units: int,
    total_buildable_sqft: float,
    assessed_value: float,
    effective_gross_income: float,
    assumptions: EconomicAssumptions
) -> OperatingExpenses:
    """
    Calculate annual operating expenses.

    Components:
    - Property Tax: assessed_value × tax_rate (Prop 13)
    - Insurance: replacement_cost × insurance_rate (0.6% typical)
    - Management: EGI × management_rate (5% typical)
    - Utilities: per_unit × num_units (if landlord-paid)
    - Maintenance & Repairs: per_unit × num_units
    - Reserves: per_unit × num_units
    - Marketing & Leasing: per_unit × num_units

    Args:
        num_units: Total number of units
        total_buildable_sqft: Total building square footage
        assessed_value: Property assessed value
        effective_gross_income: Annual effective gross income
        assumptions: Economic assumptions

    Returns:
        OperatingExpenses breakdown

    Examples:
        >>> expenses = calculate_operating_expenses(
        ...     50, 50000, 10_000_000, 1_500_000, assumptions
        ... )
        >>> print(f"Total expenses: ${expenses.total:,.0f}")
        Total expenses: $425,000
    """
    # Property tax (Prop 13)
    property_tax = calculate_property_tax(assessed_value, assumptions.property_tax_rate)

    # Insurance (based on replacement cost)
    replacement_cost = total_buildable_sqft * assumptions.construction_cost_per_sqft
    insurance = replacement_cost * assumptions.insurance_rate

    # Management (% of EGI)
    management = effective_gross_income * assumptions.management_rate

    # Per-unit expenses
    utilities = assumptions.utilities_per_unit_annual * num_units
    maintenance = assumptions.maintenance_per_unit_annual * num_units
    reserves = assumptions.reserves_per_unit_annual * num_units
    marketing = assumptions.marketing_per_unit_annual * num_units

    return OperatingExpenses(
        property_tax=property_tax,
        insurance=insurance,
        management=management,
        utilities=utilities,
        maintenance=maintenance,
        reserves=reserves,
        marketing=marketing
    )


def calculate_noi(
    gross_potential_income: float,
    vacancy_rate: float,
    operating_expenses: OperatingExpenses
) -> tuple[float, float, float]:
    """
    Calculate Net Operating Income (NOI).

    Steps:
    1. Calculate vacancy loss: GPI × vacancy_rate
    2. Calculate EGI: GPI - vacancy_loss
    3. Calculate NOI: EGI - operating_expenses

    Args:
        gross_potential_income: Annual GPI
        vacancy_rate: Vacancy and collection loss rate
        operating_expenses: Operating expense breakdown

    Returns:
        Tuple of (vacancy_loss, effective_gross_income, noi)

    Examples:
        >>> vacancy, egi, noi = calculate_noi(1_500_000, 0.05, expenses)
        >>> print(f"NOI: ${noi:,.0f}")
        NOI: $1,000,000
    """
    vacancy_loss = gross_potential_income * vacancy_rate
    effective_gross_income = gross_potential_income - vacancy_loss
    noi = effective_gross_income - operating_expenses.total

    return vacancy_loss, effective_gross_income, noi


def project_revenue_stream(
    base_noi: float,
    base_gpi: float,
    base_expenses: float,
    rent_growth_rate: float,
    expense_growth_rate: float,
    years: int = 10
) -> List[Dict[str, float]]:
    """
    Project NOI over multiple years with growth rates.

    Formula:
    - Year 1: Base values
    - Year N: GPI × (1 + rent_growth)^(N-1) - Expenses × (1 + expense_growth)^(N-1)

    Args:
        base_noi: Year 1 NOI
        base_gpi: Year 1 GPI
        base_expenses: Year 1 operating expenses
        rent_growth_rate: Annual rent growth rate (e.g., 0.03 for 3%)
        expense_growth_rate: Annual expense growth rate (e.g., 0.025 for 2.5%)
        years: Number of years to project

    Returns:
        List of year projections with GPI, expenses, and NOI

    Examples:
        >>> projections = project_revenue_stream(
        ...     1_000_000, 1_500_000, 425_000, 0.03, 0.025, 10
        ... )
        >>> year_10 = projections[9]
        >>> print(f"Year 10 NOI: ${year_10['noi']:,.0f}")
        Year 10 NOI: $1,250,000
    """
    projections = []

    for year in range(1, years + 1):
        # Apply growth rates
        gpi = base_gpi * ((1 + rent_growth_rate) ** (year - 1))
        expenses = base_expenses * ((1 + expense_growth_rate) ** (year - 1))
        noi = gpi - expenses

        projections.append({
            "year": year,
            "gpi": gpi,
            "operating_expenses": expenses,
            "noi": noi
        })

    return projections


async def estimate_revenue(
    inputs: RevenueInputs,
    total_buildable_sqft: float,
    assessed_value: float,
    assumptions: EconomicAssumptions,
    hud_client: Optional[HudFMRClient] = None,
    ami_calculator: Optional[AMICalculator] = None,
    include_projections: bool = False,
    projection_years: int = 10
) -> RevenueProjection:
    """
    Estimate annual revenue and NOI for residential development.

    Main entry point for revenue estimation. Combines market-rate and
    affordable housing revenue with comprehensive operating expenses.

    Args:
        inputs: Revenue calculation inputs (units, location, quality)
        total_buildable_sqft: Total building square footage
        assessed_value: Property assessed value (for property tax)
        assumptions: Economic assumptions (vacancy, expenses, growth)
        hud_client: HUD FMR API client (optional, creates if None)
        ami_calculator: AMI calculator (optional, uses singleton if None)
        include_projections: Include multi-year projections
        projection_years: Number of years to project (default: 10)

    Returns:
        RevenueProjection with GPI, EGI, NOI, and expense breakdown

    Examples:
        >>> inputs = RevenueInputs(
        ...     zip_code="90401",
        ...     county="Los Angeles",
        ...     market_unit_mix={1: 20, 2: 30},
        ...     affordable_unit_mix={1: 5, 2: 5},
        ...     quality_factor=1.1
        ... )
        >>> projection = await estimate_revenue(
        ...     inputs, 50000, 10_000_000, EconomicAssumptions()
        ... )
        >>> print(f"Annual NOI: ${projection.net_operating_income:,.0f}")
        Annual NOI: $1,250,000
    """
    logger.info("Starting revenue estimation", extra={"inputs": inputs.model_dump()})

    # Initialize clients if not provided
    if hud_client is None:
        from app.clients.hud_fmr_client import get_hud_fmr_client
        hud_client = get_hud_fmr_client()

    if ami_calculator is None:
        from app.services.ami_calculator import get_ami_calculator
        ami_calculator = get_ami_calculator()

    # Calculate market rents
    market_rents, fmr_data = await calculate_market_rents(
        inputs.zip_code,
        inputs.market_unit_mix,
        inputs.quality_factor,
        hud_client
    )

    # Calculate affordable rents
    affordable_rents = calculate_affordable_rents(
        inputs.county,
        inputs.affordable_unit_mix,
        inputs.ami_percentages,
        inputs.utility_allowance,
        ami_calculator
    )

    # Calculate GPI
    gpi = calculate_gross_income(
        market_rents,
        affordable_rents,
        inputs.market_unit_mix,
        inputs.affordable_unit_mix
    )

    # Calculate vacancy loss and EGI
    vacancy_loss = gpi * assumptions.vacancy_rate
    egi = gpi - vacancy_loss

    # Calculate operating expenses
    operating_expenses = calculate_operating_expenses(
        inputs.total_units,
        total_buildable_sqft,
        assessed_value,
        egi,
        assumptions
    )

    # Calculate NOI
    _, _, noi = calculate_noi(gpi, assumptions.vacancy_rate, operating_expenses)

    # Per-unit metrics
    gpi_per_unit = gpi / inputs.total_units if inputs.total_units > 0 else 0
    noi_per_unit = noi / inputs.total_units if inputs.total_units > 0 else 0

    # Multi-year projections (optional)
    projections = None
    if include_projections:
        projections = project_revenue_stream(
            noi,
            gpi,
            operating_expenses.total,
            assumptions.rent_growth_rate,
            assumptions.expense_growth_rate,
            projection_years
        )

    # Build source notes
    quality_description = (
        "Class C (below market)" if inputs.quality_factor < 0.9
        else "Class B (market average)" if inputs.quality_factor < 1.0
        else "Class A (above market)"
    )

    source_notes = {
        "fmr_source": f"HUD FMR API: {fmr_data.metro_name} ({fmr_data.metro_code}), year={fmr_data.year}",
        "fmr_methodology": "24 CFR Part 888 - 40th percentile gross rent",
        "safmr_used": fmr_data.smallarea_status == 1,
        "quality_factor": f"{inputs.quality_factor} ({quality_description})",
        "ami_source": "HCD 2025 Income Limits via AMI Calculator (30% of income standard)",
        "vacancy_assumption": f"{assumptions.vacancy_rate:.1%}",
        "tax_rate": f"{assumptions.property_tax_rate:.2%} (Prop 13: 1% base + local add-ons)",
        "expense_assumptions": {
            "management": f"{assumptions.management_rate:.1%} of EGI",
            "maintenance": f"${assumptions.maintenance_per_unit_annual}/unit/year",
            "insurance": f"{assumptions.insurance_rate:.2%} of replacement cost",
            "utilities": f"${assumptions.utilities_per_unit_annual}/unit/year (landlord-paid)",
            "reserves": f"${assumptions.reserves_per_unit_annual}/unit/year",
            "marketing": f"${assumptions.marketing_per_unit_annual}/unit/year"
        },
        "growth_rates": {
            "rent_growth": f"{assumptions.rent_growth_rate:.1%}",
            "expense_growth": f"{assumptions.expense_growth_rate:.1%}"
        }
    }

    logger.info(
        "Revenue estimation completed",
        extra={
            "gpi": gpi,
            "egi": egi,
            "noi": noi,
            "noi_per_unit": noi_per_unit,
            "is_safmr": fmr_data.smallarea_status == 1
        }
    )

    return RevenueProjection(
        gross_potential_income=gpi,
        vacancy_loss=vacancy_loss,
        effective_gross_income=egi,
        operating_expenses=operating_expenses,
        total_operating_expenses=operating_expenses.total,
        net_operating_income=noi,
        gpi_per_unit=gpi_per_unit,
        noi_per_unit=noi_per_unit,
        market_rents=market_rents,
        affordable_rents=affordable_rents,
        projections=projections,
        source_notes=source_notes
    )
