"""
Rules information API endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()


class RuleInfo(BaseModel):
    """Model for rule information."""

    name: str
    code: str
    description: str
    year_enacted: int
    applies_to: List[str]
    key_provisions: List[str]
    eligibility_criteria: List[str]


@router.get("/rules", response_model=List[RuleInfo])
async def get_all_rules() -> List[RuleInfo]:
    """
    Get information about all implemented California housing rules.

    Returns details about SB9, SB35, AB2011, AB2097, and density bonus programs.
    """
    rules = [
        RuleInfo(
            name="Senate Bill 9",
            code="SB9",
            description="Allows lot splits and up to two units per lot on parcels zoned for single-family",
            year_enacted=2021,
            applies_to=["Single-family residential zones", "Urban areas"],
            key_provisions=[
                "Allows lot split creating two parcels minimum 1,200 sq ft each",
                "Allows up to 2 units per parcel (4 total with split)",
                "Ministerial approval required",
                "Maximum 800 sq ft per unit if lot < 5,000 sq ft"
            ],
            eligibility_criteria=[
                "Not in high fire hazard zone",
                "Not in flood zone",
                "Not historic property",
                "Not prime farmland",
                "Must be in urban area"
            ]
        ),
        RuleInfo(
            name="Senate Bill 35",
            code="SB35",
            description="Streamlined ministerial approval for multifamily housing in localities that haven't met housing goals",
            year_enacted=2017,
            applies_to=["Multifamily developments", "Localities behind on RHNA"],
            key_provisions=[
                "Ministerial approval (no discretionary review)",
                "Must meet objective standards",
                "10% affordable for > 50% RHNA met, 50% affordable otherwise",
                "Prevailing wage requirements for projects 10+ units"
            ],
            eligibility_criteria=[
                "In locality that hasn't met RHNA targets",
                "Multifamily development",
                "Meets local objective standards",
                "Includes required affordable housing percentage"
            ]
        ),
        RuleInfo(
            name="Assembly Bill 2011",
            code="AB2011",
            description="Allows conversion of commercial/office buildings to residential",
            year_enacted=2022,
            applies_to=["Commercial office buildings", "Retail structures"],
            key_provisions=[
                "Ministerial approval for office-to-residential conversions",
                "Must meet affordability requirements",
                "Reduced parking requirements",
                "Streamlined CEQA review"
            ],
            eligibility_criteria=[
                "Existing commercial or office building",
                "At least 15 years old preferred",
                "Includes affordable housing component",
                "Meets health and safety codes"
            ]
        ),
        RuleInfo(
            name="Assembly Bill 2097",
            code="AB2097",
            description="Prohibits minimum parking requirements near quality transit",
            year_enacted=2022,
            applies_to=["Developments within 0.5 miles of transit"],
            key_provisions=[
                "No minimum parking requirements within 0.5 mile of transit",
                "Applies to all residential and mixed-use",
                "Transit includes bus stops with 15-min peak service",
                "Effective January 1, 2023"
            ],
            eligibility_criteria=[
                "Within 0.5 mile of major transit stop",
                "Or within 0.25 mile of high-quality bus corridor"
            ]
        ),
        RuleInfo(
            name="State Density Bonus Law",
            code="Density Bonus",
            description="Provides density increases and concessions for affordable housing",
            year_enacted=1979,
            applies_to=["Residential developments with affordable units"],
            key_provisions=[
                "Up to 50% density increase for affordable housing",
                "Up to 80% increase for 100% affordable",
                "Up to 3 development concessions",
                "Height increases up to 3 stories/33 feet",
                "Parking reductions available"
            ],
            eligibility_criteria=[
                "Minimum 5% very low income, OR",
                "Minimum 10% lower income, OR",
                "Minimum 10% moderate income (for sale), OR",
                "Senior housing, OR",
                "100% affordable (lower income)"
            ]
        )
    ]

    return rules


@router.get("/rules/{rule_code}", response_model=RuleInfo)
async def get_rule_details(rule_code: str) -> RuleInfo:
    """
    Get detailed information about a specific rule.

    Args:
        rule_code: The rule code (SB9, SB35, AB2011, AB2097, or DensityBonus)
    """
    all_rules = await get_all_rules()

    for rule in all_rules:
        if rule.code.upper() == rule_code.upper():
            return rule

    raise HTTPException(status_code=404, detail=f"Rule {rule_code} not found")


@router.get("/rules/check-eligibility/{rule_code}")
async def check_rule_eligibility(
    rule_code: str,
    lot_size_sqft: float,
    zoning_code: str,
    transit_distance_miles: float = 999.0
) -> Dict[str, Any]:
    """
    Quick eligibility check for a specific rule.

    Args:
        rule_code: The rule code to check
        lot_size_sqft: Lot size in square feet
        zoning_code: Current zoning code
        transit_distance_miles: Distance to nearest transit (for AB2097)

    Returns:
        Dictionary with eligibility status and reasoning
    """
    eligible = False
    reasons = []

    rule_code = rule_code.upper()

    if rule_code == "SB9":
        if "R1" in zoning_code.upper() or "RS" in zoning_code.upper():
            if lot_size_sqft >= 2400:
                eligible = True
                reasons.append("Meets minimum lot size for SB9 lot split")
            else:
                reasons.append("Lot too small for SB9 lot split (need 2,400 sq ft minimum)")
        else:
            reasons.append("Not zoned for single-family residential")

    elif rule_code == "AB2097":
        if transit_distance_miles <= 0.5:
            eligible = True
            reasons.append("Within 0.5 miles of transit - no parking minimums required")
        else:
            reasons.append("Not within 0.5 miles of qualifying transit")

    elif rule_code == "SB35":
        eligible = True  # Requires city-specific RHNA data
        reasons.append("Eligibility depends on jurisdiction's RHNA progress")
        reasons.append("Contact local planning department for RHNA status")

    elif rule_code == "AB2011":
        reasons.append("Requires existing commercial/office building")
        reasons.append("Manual review needed for conversion eligibility")

    elif rule_code == "DENSITYBONUS":
        eligible = True
        reasons.append("Available for projects with affordable housing component")
        reasons.append("Requires minimum 5-10% affordable units depending on income level")

    else:
        raise HTTPException(status_code=404, detail=f"Rule {rule_code} not found")

    return {
        "rule_code": rule_code,
        "eligible": eligible,
        "reasons": reasons,
        "note": "This is a preliminary check. Full analysis recommended."
    }
