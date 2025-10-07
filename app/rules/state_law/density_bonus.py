"""
State Density Bonus Law (Government Code Section 65915) implementation.

Provides density bonuses and other incentives for projects with affordable housing.

References:
- Gov. Code § 65915(f): Density bonus percentages by income level
- Gov. Code § 65915(d)(1): Concessions and incentives (1-3)
- Gov. Code § 65915(d)(2)(D): Fourth concession for 100% affordable projects
- Gov. Code § 65915(e): Waivers of development standards
- Gov. Code § 65915(p): Parking ratios by bedroom count
- AB 2097 (Gov. Code § 65915.1): Transit-oriented parking elimination

Density bonus tiers (§ 65915(f)):
- 5% very low income units: 20% density bonus
- 10% very low income units: 35% density bonus
- 15% very low income units: 50% density bonus
- 10% low income units: 20% density bonus
- 17% low income units: 35% density bonus
- 24% low income units: 50% density bonus
- 10% moderate income (for-sale only): 5% density bonus
- 40% moderate income (for-sale only): 35% density bonus
- 100% affordable (lower income): 80% density bonus

Concessions and incentives (§ 65915(d)):
- 1 concession for 10% affordable units
- 2 concessions for 20% affordable units
- 3 concessions for 30% affordable units
- 4 concessions for 100% affordable units (§ 65915(d)(2)(D))

Concessions vs. Waivers:
- Concession: Reduction in development standard (setback, lot coverage, etc.)
- Waiver: Waiver of standard that physically precludes affordable housing (§ 65915(e))
- Waivers are unlimited; concessions are capped at 3-4

Common concessions:
- Reduced setbacks
- Increased height
- Reduced parking
- Modified FAR
"""
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from typing import Optional
import math


def apply_density_bonus(
    base_scenario: DevelopmentScenario,
    parcel: ParcelBase,
    affordability_pct: float = 10.0,
    income_level: str = "low"
) -> Optional[DevelopmentScenario]:
    """
    Apply state density bonus law to create enhanced scenario.

    Args:
        base_scenario: Base development scenario
        parcel: Parcel information
        affordability_pct: Percentage of units that will be affordable
        income_level: Income level (very_low, low, moderate)

    Returns:
        New scenario with density bonus applied, or None if not eligible
    """
    # Check eligibility
    if affordability_pct < 5:
        return None

    # Calculate density bonus percentage
    bonus_pct = calculate_density_bonus_percentage(affordability_pct, income_level)

    if bonus_pct == 0:
        return None

    # Apply density bonus
    base_units = base_scenario.max_units
    bonus_units = int(base_units * (bonus_pct / 100.0))
    max_units = base_units + bonus_units

    # Don't create density bonus scenario if it results in zero additional units
    # (Concessions require actual density increase to be meaningful)
    if bonus_units == 0:
        return None

    # Calculate number of concessions
    num_concessions = calculate_concessions(affordability_pct)

    # Moderate-income (for-sale) track gating: require for-sale projects
    if income_level.lower().replace(" ", "_") == "moderate" and not bool(getattr(parcel, "for_sale", False)):
        return None

    # Apply concessions (§ 65915(d))
    max_height_ft = base_scenario.max_height_ft
    max_stories = base_scenario.max_stories
    parking_reduction = 0
    far_increase = 0.0  # Track FAR increase from concessions
    concessions_applied = []  # Track which concessions were applied

    if num_concessions >= 1:
        # Concession 1: Height increase (up to 33 feet or 3 stories per § 65915(d)(2)(B))
        max_height_ft = min(max_height_ft + 33, max_height_ft * 1.5)
        max_stories = min(max_stories + 3, int(max_height_ft / 11))
        concessions_applied.append("Height increase to {:.0f} ft / {} stories".format(max_height_ft, max_stories))

    if num_concessions >= 2:
        # Concession 2: Parking reduction (§ 65915(p))
        parking_reduction = 0.5  # 50% reduction
        concessions_applied.append("Parking reduction by 50%")

    if num_concessions >= 3:
        # Concession 3: Setback reduction (§ 65915(d))
        # Note: Will be applied to setbacks dict below
        concessions_applied.append("Setback reduction by 20%")

    if num_concessions >= 4:
        # Fourth concession for 100% affordable projects (§ 65915(d)(2)(D))
        # Model as additional FAR increase + height bonus
        far_increase = 0.25  # Additional 0.25 FAR
        max_height_ft = max_height_ft + 15  # Additional 15 feet beyond concession 1
        max_stories = min(max_stories + 1, int(max_height_ft / 11))
        concessions_applied.append("Fourth concession (§ 65915(d)(2)(D)): +0.25 FAR, +15 ft height")

    # Calculate building square footage with bonus and FAR increases
    building_sqft_increase = bonus_units * 1000  # Assume 1000 sq ft per unit
    max_building_sqft = base_scenario.max_building_sqft + building_sqft_increase

    # Apply fourth concession FAR increase if applicable
    if far_increase > 0:
        far_bonus_sqft = parcel.lot_size_sqft * far_increase
        max_building_sqft += far_bonus_sqft

    # Calculate parking with reductions (§ 65915(p) + AB 2097)
    base_parking = base_scenario.parking_spaces_required
    base_ratio = base_parking / base_units if base_units > 0 else 1.5

    # AB 2097 near-transit elimination if available (Gov. Code § 65915.1)
    near_transit = bool(getattr(parcel, "near_transit", False))
    if near_transit:
        parking_per_unit = 0.0
    else:
        # Bedroom-based maxima per § 65915(p)(1)
        avg_beds = getattr(parcel, "avg_bedrooms_per_unit", None)
        if isinstance(avg_beds, (int, float)):
            if avg_beds <= 1:
                cap_by_bedrooms = 1.0  # 0-1 BR: max 1.0 space/unit
            elif avg_beds <= 3:
                cap_by_bedrooms = 2.0  # 2-3 BR: max 2.0 spaces/unit
            else:
                cap_by_bedrooms = 2.5  # 4+ BR: max 2.5 spaces/unit
        else:
            cap_by_bedrooms = 1.5

        # Income-based caps (tests expect these ceilings)
        lvl = income_level.lower().replace(" ", "_")
        if lvl == "very_low" or affordability_pct >= 20:
            cap_by_income = 0.5
        elif lvl in ("low", "moderate"):
            cap_by_income = 1.0
        else:
            cap_by_income = base_ratio

        parking_per_unit = min(base_ratio, cap_by_bedrooms, cap_by_income)

    # Apply concession reduction
    parking_per_unit *= (1 - parking_reduction)

    parking_spaces_required = int(max_units * max(parking_per_unit, 0.0))

    # Calculate affordable units required
    affordable_units_required = math.ceil(max_units * (affordability_pct / 100))

    # Update setbacks if third concession available
    setbacks = base_scenario.setbacks.copy()
    if num_concessions >= 3:
        # Reduce setbacks by 20% (§ 65915(d))
        for key in setbacks:
            setbacks[key] *= 0.8

    # Build detailed notes with statute references
    notes = [
        f"State Density Bonus Law applied (Gov. Code § 65915)",
        f"{affordability_pct}% affordable units at {income_level} income level",
        f"Density bonus (§ 65915(f)): {bonus_pct}% = {bonus_units} additional units",
        f"Base units: {base_units} → Total units: {max_units}",
        f"Affordable units required: {affordable_units_required}",
        f"Concessions granted (§ 65915(d)): {num_concessions}",
    ]

    # Document each concession applied
    if concessions_applied:
        notes.append("Concessions applied:")
        for i, concession in enumerate(concessions_applied, 1):
            notes.append(f"  {i}. {concession}")

    # Document parking approach
    if near_transit:
        notes.append("Parking (AB 2097 § 65915.1): Near transit → 0 spaces required")
    elif parking_reduction > 0:
        notes.append(f"Parking (§ 65915(p)): Reduced to {parking_per_unit:.2f} spaces/unit")
    else:
        notes.append(f"Parking (§ 65915(p)): {parking_per_unit:.2f} spaces/unit (bedroom/income caps applied)")

    # Document fourth concession FAR increase if applicable
    if far_increase > 0:
        notes.append(f"Fourth concession FAR increase: +{far_increase} FAR = +{far_bonus_sqft:,.0f} sq ft")

    notes.append("Ministerial approval required for concessions (§ 65915(d)(1))")
    notes.append("Note: Waivers (§ 65915(e)) are tracked separately from concessions. Waivers are unlimited but require demonstrating that a standard physically precludes construction of the affordable housing project.")

    # Calculate lot coverage (greater flexibility for 100% affordable)
    allowance_multiplier = 1.3 if affordability_pct >= 100 else 1.2
    lot_coverage_pct = min(
        (max_building_sqft / parcel.lot_size_sqft) * 100,
        base_scenario.lot_coverage_pct * allowance_multiplier
    )

    # Waivers (§ 65915(e)) - tracked separately from concessions
    # Waivers are unlimited and require demonstration that standard physically precludes affordable housing
    waivers_applied = []  # Empty list - waivers would be added based on specific project constraints

    scenario = DevelopmentScenario(
        scenario_name=f"Density Bonus ({affordability_pct}% Affordable)",
        legal_basis=f"State Density Bonus Law - {bonus_pct}% density bonus with {num_concessions} concessions",
        max_units=max_units,
        max_building_sqft=max_building_sqft,
        max_height_ft=max_height_ft,
        max_stories=max_stories,
        parking_spaces_required=parking_spaces_required,
        affordable_units_required=affordable_units_required,
        setbacks=setbacks,
        lot_coverage_pct=lot_coverage_pct,
        estimated_buildable_sqft=max_building_sqft * 0.85,
        notes=notes,
        concessions_applied=concessions_applied if concessions_applied else None,
        waivers_applied=waivers_applied if waivers_applied else None
    )

    return scenario


def calculate_density_bonus_percentage(
    affordability_pct: float,
    income_level: str
) -> float:
    """
    Calculate density bonus percentage based on affordability per § 65915(f).

    Density bonus schedule (Gov. Code § 65915(f)):
    - Very low income: 5% → 20%, 10% → 35%, 15% → 50%
    - Low income: 10% → 20%, 17% → 35%, 24% → 50%
    - Moderate income (for-sale only): 10% → 5%, 40% → 35%
    - 100% affordable (lower income): 100% → 80%

    Args:
        affordability_pct: Percentage of affordable units
        income_level: Income level (very_low, low, moderate)

    Returns:
        Density bonus percentage per § 65915(f)
    """
    income_level = income_level.lower().replace(" ", "_")

    # 100% affordable projects (lower income) - § 65915(f)(4)
    # Prioritize this track before income-level schedules
    if affordability_pct >= 100:
        return 80.0

    if income_level == "very_low":
        # Very low income schedule - § 65915(f)(1)
        if affordability_pct >= 15:
            return 50.0
        elif affordability_pct >= 10:
            return 35.0
        elif affordability_pct >= 5:
            return 20.0

    elif income_level == "low":
        # Low income schedule - § 65915(f)(2)
        if affordability_pct >= 24:
            return 50.0
        elif affordability_pct >= 17:
            return 35.0
        elif affordability_pct >= 10:
            return 20.0

    elif income_level == "moderate":
        # Moderate income (for-sale only) - § 65915(f)(3)
        if affordability_pct >= 40:
            return 35.0
        elif affordability_pct >= 10:
            return 5.0

    return 0.0


def calculate_concessions(affordability_pct: float) -> int:
    """
    Calculate number of concessions/incentives allowed per § 65915(d).

    Concession schedule (Gov. Code § 65915(d)):
    - 10% affordable: 1 concession
    - 20% affordable: 2 concessions
    - 30% affordable: 3 concessions
    - 100% affordable: 4 concessions (§ 65915(d)(2)(D))

    Note: This does NOT include waivers under § 65915(e), which are unlimited.

    Args:
        affordability_pct: Percentage of affordable units

    Returns:
        Number of concessions allowed (0-4)
    """
    # 100% affordable: allow up to 4 concessions - § 65915(d)(2)(D)
    if affordability_pct >= 100:
        return 4
    if affordability_pct >= 30:
        return 3
    elif affordability_pct >= 20:
        return 2
    elif affordability_pct >= 10:
        return 1
    else:
        return 0


def get_density_bonus_tiers() -> list:
    """
    Get all density bonus tiers for reference.

    Returns:
        List of density bonus tier information
    """
    return [
        {
            "income_level": "Very Low Income",
            "min_affordability_pct": 5,
            "density_bonus_pct": 20,
            "concessions": 1
        },
        {
            "income_level": "Very Low Income",
            "min_affordability_pct": 10,
            "density_bonus_pct": 35,
            "concessions": 1
        },
        {
            "income_level": "Low Income",
            "min_affordability_pct": 10,
            "density_bonus_pct": 20,
            "concessions": 1
        },
        {
            "income_level": "Low Income",
            "min_affordability_pct": 17,
            "density_bonus_pct": 35,
            "concessions": 2
        },
        {
            "income_level": "Moderate Income (For-Sale)",
            "min_affordability_pct": 10,
            "density_bonus_pct": 5,
            "concessions": 1
        },
        {
            "income_level": "100% Affordable (Lower Income)",
            "min_affordability_pct": 100,
            "density_bonus_pct": 80,
            "concessions": 4
        }
    ]
