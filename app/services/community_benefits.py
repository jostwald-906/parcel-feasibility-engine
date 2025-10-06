"""
Community Benefits Analysis Module

Analyzes opportunities for community benefits that enable higher development tiers
in Santa Monica's Downtown Community Plan (DCP) and other overlay districts.

CITE: SMMC § 9.23.030 (Community Benefits)
CITE: Downtown Community Plan (2017, amended 2023) - Tier System
CITE: Santa Monica General Plan Land Use and Circulation Element (LUCE)

Community benefits allow projects to achieve Tier 2 or Tier 3 development standards
in exchange for public amenities, affordable housing, or other community contributions.
"""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel


class BenefitCategory(str, Enum):
    """Categories of community benefits per Santa Monica standards"""
    AFFORDABLE_HOUSING = "AFFORDABLE_HOUSING"
    OPEN_SPACE = "OPEN_SPACE"
    CULTURAL_ARTS = "CULTURAL_ARTS"
    CHILDCARE = "CHILDCARE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    TRANSPORTATION = "TRANSPORTATION"
    PUBLIC_SERVICES = "PUBLIC_SERVICES"


class CommunityBenefit(BaseModel):
    """Definition of a specific community benefit"""
    category: BenefitCategory
    name: str
    description: str
    tier_eligibility: List[int]  # Which tiers this benefit enables (2, 3)
    quantifiable: bool  # Can this be measured objectively?
    typical_provision: Optional[str]  # Example of how benefit is typically provided
    notes: List[str]


class CommunityBenefitsAnalysis(BaseModel):
    """Analysis of community benefits opportunities for a parcel"""
    available_benefits: List[CommunityBenefit]
    recommended_benefits: List[str]  # Benefit names recommended for this parcel
    tier_2_requirements: List[str]
    tier_3_requirements: List[str]
    notes: List[str]


# CITE: SMMC § 9.23.030 and DCP Implementation Guidelines
COMMUNITY_BENEFITS_CATALOG = [
    CommunityBenefit(
        category=BenefitCategory.AFFORDABLE_HOUSING,
        name="Above-Minimum Affordable Housing",
        description="Provide affordable units beyond minimum requirements",
        tier_eligibility=[2, 3],
        quantifiable=True,
        typical_provision="Tier 2: 15-20% affordable units (very low to moderate income)\nTier 3: 25%+ affordable units or 100% affordable projects",
        notes=[
            "Most commonly used benefit for tier upgrades",
            "Income targeting: Very Low (≤50% AMI), Low (≤80% AMI), Moderate (≤120% AMI)",
            "Deed restrictions required (55 years minimum)",
            "Can combine with State Density Bonus Law for additional benefits"
        ]
    ),
    CommunityBenefit(
        category=BenefitCategory.OPEN_SPACE,
        name="Public Open Space or Plaza",
        description="Provide publicly accessible open space beyond minimum requirements",
        tier_eligibility=[2, 3],
        quantifiable=True,
        typical_provision="Tier 2: 10-15% of lot area as public plaza\nTier 3: 20%+ of lot area or rooftop gardens accessible to public",
        notes=[
            "Must be truly public (no gates, open during business hours minimum)",
            "Quality matters: landscaping, seating, art, pedestrian amenities required",
            "Maintenance agreement required with City",
            "Pedestrian through-block connections highly valued"
        ]
    ),
    CommunityBenefit(
        category=BenefitCategory.CULTURAL_ARTS,
        name="Arts and Cultural Space",
        description="Provide dedicated space for arts, performance, or cultural activities",
        tier_eligibility=[2, 3],
        quantifiable=True,
        typical_provision="Tier 2: 2,000-3,000 sqft gallery or performance space\nTier 3: 5,000+ sqft cultural venue or art studios",
        notes=[
            "Space must be provided at below-market rent or free",
            "Programming coordination with Santa Monica Cultural Affairs",
            "Public art installations (1% of project cost) may supplement",
            "Historic preservation and adaptive reuse can qualify"
        ]
    ),
    CommunityBenefit(
        category=BenefitCategory.CHILDCARE,
        name="Childcare Facility",
        description="Provide licensed childcare facility for community use",
        tier_eligibility=[2, 3],
        quantifiable=True,
        typical_provision="Tier 2: Childcare for 15-25 children\nTier 3: Childcare for 40+ children with subsidized spots",
        notes=[
            "Must meet California childcare licensing requirements",
            "Preference for subsidized spots for low-income families",
            "Long-term operational commitment required",
            "High demand in Downtown and Bergamot areas"
        ]
    ),
    CommunityBenefit(
        category=BenefitCategory.ENVIRONMENTAL,
        name="Sustainability Features (Above Code)",
        description="Exceed California Green Building Standards (CALGreen) and Title 24",
        tier_eligibility=[2, 3],
        quantifiable=True,
        typical_provision="Tier 2: LEED Silver or equivalent, 25% renewable energy\nTier 3: LEED Gold/Platinum, 50%+ renewable energy, net-zero ready",
        notes=[
            "All-electric buildings preferred (per Santa Monica's climate goals)",
            "Solar PV, battery storage, EV charging beyond minimums",
            "Greywater systems, green roofs, urban heat island mitigation",
            "Must exceed Title 24 by measurable amount"
        ]
    ),
    CommunityBenefit(
        category=BenefitCategory.TRANSPORTATION,
        name="Transportation Demand Management (TDM)",
        description="Reduce vehicle trips through enhanced TDM measures",
        tier_eligibility=[2, 3],
        quantifiable=True,
        typical_provision="Tier 2: Unbundled parking, bike facilities, transit passes\nTier 3: Car-share spaces, micro-mobility hub, no parking (if near transit)",
        notes=[
            "Especially valuable near Expo Line and Big Blue Bus corridors",
            "Bike parking and facilities beyond Title 24 minimums",
            "Transit pass subsidies for residents/employees",
            "AB 2097 allows zero parking near transit - can be structured as benefit"
        ]
    ),
    CommunityBenefit(
        category=BenefitCategory.PUBLIC_SERVICES,
        name="Community-Serving Retail/Services",
        description="Ground-floor space for neighborhood-serving businesses",
        tier_eligibility=[2, 3],
        quantifiable=True,
        typical_provision="Tier 2: 20-30% of ground floor as retail/restaurant\nTier 3: 40%+ ground floor activation with pedestrian amenities",
        notes=[
            "Preference for local businesses and community services",
            "Grocery stores, pharmacies, healthcare particularly valued",
            "Enhanced pedestrian realm (wider sidewalks, parklets, outdoor dining)",
            "Long-term affordability for small businesses"
        ]
    ),
]


def get_available_benefits(
    lot_size_sqft: float,
    base_tier: int,
    near_transit: bool,
    in_downtown: bool
) -> CommunityBenefitsAnalysis:
    """
    Determine which community benefits are feasible for a parcel.

    Args:
        lot_size_sqft: Parcel size in square feet
        base_tier: Current development tier (1, 2, or 3)
        near_transit: Within 0.5 mile of transit
        in_downtown: Within Downtown Community Plan area

    Returns:
        Analysis of available benefits and recommendations
    """
    available = []
    recommended = []
    tier_2_reqs = []
    tier_3_reqs = []
    notes = []

    # Filter benefits by parcel characteristics
    for benefit in COMMUNITY_BENEFITS_CATALOG:
        # Small lots (<5,000 sf) may struggle with open space or childcare
        if lot_size_sqft < 5000 and benefit.category in [BenefitCategory.OPEN_SPACE, BenefitCategory.CHILDCARE]:
            notes.append(f"{benefit.name} may be challenging on small lot (<5,000 sqft)")
            continue

        # All benefits potentially available
        available.append(benefit)

    # Tier 2 requirements (one or more benefits required)
    tier_2_reqs = [
        "Provide at least ONE community benefit from the approved list",
        "Affordable Housing: Typically 15-20% affordable units at very low to moderate income levels",
        "OR Public Open Space: 10-15% of lot area as publicly accessible plaza",
        "OR Arts/Cultural Space: 2,000-3,000 sqft at below-market rent",
        "OR Equivalent benefit as approved by Community Development Director"
    ]

    # Tier 3 requirements (multiple benefits or exceptional single benefit)
    tier_3_reqs = [
        "Provide MULTIPLE community benefits OR one exceptional benefit",
        "Affordable Housing: 25%+ affordable units OR 100% affordable project",
        "OR Combination: e.g., 15% affordable + public plaza + sustainability features",
        "Public benefits must be substantial and directly serve Santa Monica community",
        "Planning Commission approval required for Tier 3 designation"
    ]

    # Recommendations based on parcel characteristics
    if base_tier == 1:
        notes.append("Parcel currently at Tier 1 - community benefits can unlock Tier 2 or Tier 3")

        # Affordable housing is most straightforward path
        recommended.append("Above-Minimum Affordable Housing")

        # Transit-adjacent parcels: recommend TDM
        if near_transit:
            recommended.append("Transportation Demand Management (TDM)")
            notes.append("Near transit - reduced parking with enhanced TDM is highly feasible")

        # Downtown parcels: recommend ground-floor activation
        if in_downtown:
            recommended.append("Community-Serving Retail/Services")
            notes.append("Downtown location - ground-floor retail/services align with DCP goals")

        # Environmental features are universally applicable
        recommended.append("Sustainability Features (Above Code)")
        notes.append("All-electric construction with enhanced sustainability features recommended")

    elif base_tier == 2:
        notes.append("Parcel at Tier 2 - additional benefits can unlock Tier 3")
        recommended.append("Above-Minimum Affordable Housing")
        recommended.append("Public Open Space or Plaza")
        notes.append("Tier 3 requires multiple benefits - consider affordable housing + public space")

    else:  # Tier 3
        notes.append("Parcel already at maximum Tier 3 - community benefits may still be required")

    # General notes
    notes.append("Community benefits must be secured through Development Agreement")
    notes.append("Benefits are in addition to standard development requirements (setbacks, parking, etc.)")
    notes.append("Contact Santa Monica Planning Division for pre-application guidance")

    return CommunityBenefitsAnalysis(
        available_benefits=available,
        recommended_benefits=recommended,
        tier_2_requirements=tier_2_reqs,
        tier_3_requirements=tier_3_reqs,
        notes=notes
    )


def estimate_affordable_housing_benefit(
    base_units: int,
    affordability_pct: float,
    income_level: str = "very_low"
) -> Dict[str, any]:
    """
    Estimate the affordable housing component for tier upgrade.

    Args:
        base_units: Base number of units before tier upgrade
        affordability_pct: Percentage of units to be affordable (e.g., 0.15 = 15%)
        income_level: Target income level (very_low, low, moderate)

    Returns:
        Dictionary with affordable unit counts and revenue impact estimate
    """
    affordable_units = int(base_units * affordability_pct)

    # Santa Monica Area Median Income (AMI) estimates (2024)
    # CITE: HCD Income Limits (Los Angeles County)
    ami_thresholds = {
        "very_low": 0.50,    # ≤50% AMI (~$50,000 for 2-person household)
        "low": 0.80,         # ≤80% AMI (~$80,000 for 2-person household)
        "moderate": 1.20     # ≤120% AMI (~$120,000 for 2-person household)
    }

    # Rough market-rate vs affordable rent estimates (Santa Monica)
    market_rate_rent = 3500  # Average 1-2BR market rent in Santa Monica
    affordable_rents = {
        "very_low": 1400,    # ~30% of income at 50% AMI
        "low": 2200,         # ~30% of income at 80% AMI
        "moderate": 3000     # ~30% of income at 120% AMI
    }

    affordable_rent = affordable_rents.get(income_level, 1400)
    monthly_revenue_loss = (market_rate_rent - affordable_rent) * affordable_units
    annual_revenue_loss = monthly_revenue_loss * 12

    return {
        "affordable_units": affordable_units,
        "market_rate_units": base_units - affordable_units,
        "income_level": income_level,
        "ami_threshold": ami_thresholds.get(income_level, 0.5),
        "estimated_affordable_rent": affordable_rent,
        "estimated_market_rent": market_rate_rent,
        "monthly_revenue_impact": -monthly_revenue_loss,
        "annual_revenue_impact": -annual_revenue_loss,
        "notes": [
            "Revenue impact is approximate - actual rents vary by unit size and location",
            "Tax credits (LIHTC) and local subsidies may offset revenue loss",
            "Deed restrictions typically required for 55 years",
            f"Target households earning ≤{int(ami_thresholds.get(income_level, 0.5) * 100)}% Area Median Income"
        ]
    }


def format_benefits_for_display(analysis: CommunityBenefitsAnalysis) -> Dict[str, any]:
    """
    Format community benefits analysis for frontend display.

    Returns:
        Dictionary structured for UI consumption
    """
    return {
        "available_benefits": [
            {
                "category": benefit.category.value,
                "name": benefit.name,
                "description": benefit.description,
                "tier_eligibility": benefit.tier_eligibility,
                "typical_provision": benefit.typical_provision,
                "notes": benefit.notes
            }
            for benefit in analysis.available_benefits
        ],
        "recommended": analysis.recommended_benefits,
        "tier_2_path": {
            "title": "Path to Tier 2",
            "requirements": analysis.tier_2_requirements
        },
        "tier_3_path": {
            "title": "Path to Tier 3",
            "requirements": analysis.tier_3_requirements
        },
        "notes": analysis.notes
    }


def get_benefit_by_name(benefit_name: str) -> Optional[CommunityBenefit]:
    """
    Retrieve a specific community benefit definition by name.

    Args:
        benefit_name: Name of the benefit

    Returns:
        CommunityBenefit object or None if not found
    """
    for benefit in COMMUNITY_BENEFITS_CATALOG:
        if benefit.name.lower() == benefit_name.lower():
            return benefit
    return None


def get_benefits_by_category(category: BenefitCategory) -> List[CommunityBenefit]:
    """
    Get all benefits in a specific category.

    Args:
        category: Benefit category

    Returns:
        List of CommunityBenefit objects
    """
    return [b for b in COMMUNITY_BENEFITS_CATALOG if b.category == category]
