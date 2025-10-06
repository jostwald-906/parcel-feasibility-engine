"""
Community Noise Equivalent Level (CNEL) Analysis Module

Analyzes noise exposure levels for residential development feasibility in California.
CNEL is a 24-hour noise metric that applies penalties for evening and nighttime noise.

CITE: California Government Code § 65302(f) - General Plan Noise Element
CITE: Title 24, Part 2 (California Building Code) - Acoustic Standards
CITE: Governor's Office of Planning and Research (OPR) General Plan Guidelines

Standards:
- NORMALLY ACCEPTABLE: <60 dB CNEL
- CONDITIONALLY ACCEPTABLE: 60-70 dB CNEL (with mitigation)
- NORMALLY UNACCEPTABLE: 70-75 dB CNEL (detailed analysis required)
- CLEARLY UNACCEPTABLE: >75 dB CNEL (residential discouraged)
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel


class CNELCategory(str, Enum):
    """CNEL exposure categories per California state standards"""
    NORMALLY_ACCEPTABLE = "NORMALLY_ACCEPTABLE"
    CONDITIONALLY_ACCEPTABLE = "CONDITIONALLY_ACCEPTABLE"
    NORMALLY_UNACCEPTABLE = "NORMALLY_UNACCEPTABLE"
    CLEARLY_UNACCEPTABLE = "CLEARLY_UNACCEPTABLE"


class CNELAnalysis(BaseModel):
    """Result of CNEL noise analysis"""
    cnel_db: float
    category: CNELCategory
    description: str
    residential_suitable: bool
    requires_acoustic_study: bool
    mitigation_measures: List[str]
    window_stc_requirement: Optional[int]  # Sound Transmission Class rating
    notes: List[str]


def classify_cnel(cnel_db: float) -> CNELAnalysis:
    """
    Classify CNEL noise exposure and determine mitigation requirements.

    CITE: California Code of Regulations Title 21 § 5014 (Noise Insulation Standards)
    CITE: Title 24, Part 2, Section 1207.4 (Interior Environment)

    Args:
        cnel_db: Community Noise Equivalent Level in decibels

    Returns:
        CNELAnalysis with category, requirements, and mitigation measures
    """
    if cnel_db < 60:
        # NORMALLY ACCEPTABLE: No special requirements
        return CNELAnalysis(
            cnel_db=cnel_db,
            category=CNELCategory.NORMALLY_ACCEPTABLE,
            description="Normally Acceptable - Suitable for residential development",
            residential_suitable=True,
            requires_acoustic_study=False,
            mitigation_measures=[],
            window_stc_requirement=None,
            notes=[
                "No special noise mitigation required",
                "Standard construction practices acceptable"
            ]
        )

    elif cnel_db < 65:
        # CONDITIONALLY ACCEPTABLE (Low): Standard construction
        return CNELAnalysis(
            cnel_db=cnel_db,
            category=CNELCategory.CONDITIONALLY_ACCEPTABLE,
            description="Conditionally Acceptable - New construction with standard noise insulation",
            residential_suitable=True,
            requires_acoustic_study=False,
            mitigation_measures=[
                "Standard construction noise insulation",
                "Interior noise level target: 45 dB CNEL or less",
                "Consider building orientation away from noise source"
            ],
            window_stc_requirement=28,  # Minimum STC 28 windows (standard dual-pane)
            notes=[
                "Residential development acceptable with standard mitigation",
                "Title 24 compliance ensures adequate interior noise levels"
            ]
        )

    elif cnel_db < 70:
        # CONDITIONALLY ACCEPTABLE (High): Enhanced mitigation required
        return CNELAnalysis(
            cnel_db=cnel_db,
            category=CNELCategory.CONDITIONALLY_ACCEPTABLE,
            description="Conditionally Acceptable - Detailed acoustic analysis required",
            residential_suitable=True,
            requires_acoustic_study=True,
            mitigation_measures=[
                "Detailed acoustic analysis by qualified professional required",
                "Enhanced window glazing (STC 30-35 minimum)",
                "Solid-core exterior doors with weather stripping",
                "Mechanical ventilation to allow closed windows",
                "Building orientation to shield outdoor spaces from noise",
                "Sound walls or berms where feasible",
                "Interior noise level: 45 dB CNEL max (bedrooms/living rooms)"
            ],
            window_stc_requirement=30,  # STC 30 minimum (laminated or triple-pane glass)
            notes=[
                "Residential development conditionally acceptable",
                "Title 24 Section 1207.4 compliance mandatory",
                "CEQA analysis may require noise impact report",
                "Outdoor living spaces should be designed away from noise source"
            ]
        )

    elif cnel_db < 75:
        # NORMALLY UNACCEPTABLE: Comprehensive mitigation
        return CNELAnalysis(
            cnel_db=cnel_db,
            category=CNELCategory.NORMALLY_UNACCEPTABLE,
            description="Normally Unacceptable - Comprehensive acoustic design required",
            residential_suitable=False,  # Development discouraged but possible with extensive mitigation
            requires_acoustic_study=True,
            mitigation_measures=[
                "Comprehensive acoustic design by certified acoustical engineer required",
                "High-performance window glazing (STC 35-40)",
                "Specialized wall and roof construction (higher mass, decoupled assemblies)",
                "All HVAC systems designed for noise isolation",
                "No operable windows on noise-exposed facades unless mechanically ventilated",
                "Sound walls (10-15 ft height minimum) with absorptive treatment",
                "Building setbacks maximized from noise source",
                "Interior noise target: 45 dB CNEL (strict compliance)",
                "Post-construction noise testing required"
            ],
            window_stc_requirement=38,  # STC 38+ (specialized acoustic windows)
            notes=[
                "New residential development normally unacceptable per OPR guidelines",
                "Development may proceed with City approval and comprehensive mitigation",
                "CEQA will likely require detailed noise impact study and mitigation monitoring",
                "Consider alternative land uses (commercial, industrial, parking)",
                "Financial feasibility affected by high mitigation costs"
            ]
        )

    else:  # >= 75 dB
        # CLEARLY UNACCEPTABLE: Residential strongly discouraged
        return CNELAnalysis(
            cnel_db=cnel_db,
            category=CNELCategory.CLEARLY_UNACCEPTABLE,
            description="Clearly Unacceptable - Residential development strongly discouraged",
            residential_suitable=False,
            requires_acoustic_study=True,
            mitigation_measures=[
                "Residential development strongly discouraged by State OPR",
                "If proceeding, all mitigation from 70-75 dB category required PLUS:",
                "Maximum-rated acoustic windows (STC 40+)",
                "Specialized construction with acoustic decoupling throughout",
                "Underground or heavily shielded parking structures",
                "No outdoor living spaces on noise-exposed sides",
                "Continuous noise monitoring during operation",
                "Noise easements and deed restrictions for future owners"
            ],
            window_stc_requirement=40,  # STC 40+ (maximum acoustic performance)
            notes=[
                "Clearly unacceptable for residential per California state standards",
                "Local jurisdiction may prohibit residential development at this noise level",
                "Extreme mitigation costs likely render project financially infeasible",
                "Consider non-residential uses: office, industrial, warehouse, parking",
                "CEQA compliance extremely difficult; significant unavoidable impacts likely",
                "Santa Monica may deny project based on General Plan Noise Element"
            ]
        )


def get_mitigation_cost_estimate(analysis: CNELAnalysis, building_sqft: float) -> Dict[str, float]:
    """
    Estimate additional construction costs for noise mitigation.

    NOTE: These are rough estimates. Actual costs vary by design, materials, and contractor.

    Args:
        analysis: CNEL analysis result
        building_sqft: Gross building square footage

    Returns:
        Dictionary with cost breakdown (acoustic_windows, hvac_upgrades, barriers, study_fees, total)
    """
    costs = {
        "acoustic_study": 0.0,
        "acoustic_windows": 0.0,
        "hvac_upgrades": 0.0,
        "sound_barriers": 0.0,
        "construction_upgrades": 0.0,
        "total": 0.0
    }

    if analysis.category == CNELCategory.NORMALLY_ACCEPTABLE:
        return costs  # No additional costs

    # Acoustic study fees
    if analysis.requires_acoustic_study:
        if analysis.category == CNELCategory.CONDITIONALLY_ACCEPTABLE:
            costs["acoustic_study"] = 15000  # Basic study
        elif analysis.category == CNELCategory.NORMALLY_UNACCEPTABLE:
            costs["acoustic_study"] = 35000  # Comprehensive study + monitoring plan
        else:  # CLEARLY_UNACCEPTABLE
            costs["acoustic_study"] = 50000  # Comprehensive study + EIR support + monitoring

    # Window upgrades (per sqft of building)
    # Assume ~15% of building sqft is windows
    window_sqft = building_sqft * 0.15

    if analysis.window_stc_requirement == 28:
        costs["acoustic_windows"] = window_sqft * 5  # $5/sqft upgrade for standard dual-pane
    elif analysis.window_stc_requirement == 30:
        costs["acoustic_windows"] = window_sqft * 15  # $15/sqft for laminated glass
    elif analysis.window_stc_requirement == 38:
        costs["acoustic_windows"] = window_sqft * 35  # $35/sqft for specialized acoustic windows
    elif analysis.window_stc_requirement == 40:
        costs["acoustic_windows"] = window_sqft * 50  # $50/sqft for maximum-rated systems

    # HVAC upgrades for mechanical ventilation (if needed)
    if analysis.category in [CNELCategory.CONDITIONALLY_ACCEPTABLE, CNELCategory.NORMALLY_UNACCEPTABLE]:
        costs["hvac_upgrades"] = building_sqft * 3  # $3/sqft for enhanced HVAC with noise isolation

    if analysis.category == CNELCategory.CLEARLY_UNACCEPTABLE:
        costs["hvac_upgrades"] = building_sqft * 6  # $6/sqft for specialized quiet HVAC

    # Sound barriers (if in 65+ dB zone)
    if analysis.cnel_db >= 65:
        # Rough estimate: $250/linear foot for 10-15 ft sound wall
        # Assume perimeter of lot, simplified as square root approach
        estimated_barrier_length = (building_sqft ** 0.5) * 2  # Two sides facing noise source
        cost_per_lf = 250 if analysis.cnel_db < 70 else 400  # Higher walls cost more
        costs["sound_barriers"] = estimated_barrier_length * cost_per_lf

    # Construction upgrades (enhanced wall/roof assemblies)
    if analysis.category == CNELCategory.NORMALLY_UNACCEPTABLE:
        costs["construction_upgrades"] = building_sqft * 8  # $8/sqft for specialized construction
    elif analysis.category == CNELCategory.CLEARLY_UNACCEPTABLE:
        costs["construction_upgrades"] = building_sqft * 15  # $15/sqft for maximum acoustic construction

    costs["total"] = sum(costs.values())

    return costs


def check_santa_monica_compliance(analysis: CNELAnalysis) -> Dict[str, any]:
    """
    Check compliance with Santa Monica General Plan Noise Element.

    CITE: City of Santa Monica General Plan, Noise Element (2010 Update)
    CITE: SMMC § 4.12.010 et seq. (Noise Ordinance)

    Args:
        analysis: CNEL analysis result

    Returns:
        Dictionary with compliance status and Santa Monica-specific notes
    """
    compliance = {
        "compliant": True,
        "requires_variance": False,
        "notes": []
    }

    if analysis.category == CNELCategory.NORMALLY_ACCEPTABLE:
        compliance["notes"].append("Compliant with Santa Monica Noise Element standards")

    elif analysis.category == CNELCategory.CONDITIONALLY_ACCEPTABLE:
        if analysis.cnel_db < 65:
            compliance["notes"].append("Compliant with standard noise insulation")
        else:
            compliance["notes"].append("Requires detailed acoustic analysis per Santa Monica standards")
            compliance["notes"].append("Community Development Director approval required for noise mitigation plan")

    elif analysis.category == CNELCategory.NORMALLY_UNACCEPTABLE:
        compliance["compliant"] = False
        compliance["requires_variance"] = True
        compliance["notes"].append("Normally unacceptable per Santa Monica General Plan")
        compliance["notes"].append("Planning Commission approval required for residential development")
        compliance["notes"].append("CEQA review will require noise impact analysis and mitigation measures")
        compliance["notes"].append("May require General Plan Amendment or variance")

    else:  # CLEARLY_UNACCEPTABLE
        compliance["compliant"] = False
        compliance["requires_variance"] = True
        compliance["notes"].append("Clearly unacceptable for residential per state and local standards")
        compliance["notes"].append("City Council approval required (or likely denial)")
        compliance["notes"].append("General Plan Amendment almost certainly required")
        compliance["notes"].append("Consider alternative land uses per Santa Monica General Plan Land Use Element")

    return compliance


def format_cnel_for_display(analysis: CNELAnalysis) -> Dict[str, any]:
    """
    Format CNEL analysis for frontend display.

    Returns:
        Dictionary structured for UI consumption
    """
    return {
        "cnel_db": round(analysis.cnel_db, 1),
        "category": analysis.category.value,
        "category_label": analysis.description,
        "suitable_for_residential": analysis.residential_suitable,
        "requires_study": analysis.requires_acoustic_study,
        "window_requirement": f"STC {analysis.window_stc_requirement} minimum" if analysis.window_stc_requirement else "No special requirements",
        "mitigation_measures": analysis.mitigation_measures,
        "notes": analysis.notes,
        "color": _get_category_color(analysis.category)
    }


def _get_category_color(category: CNELCategory) -> str:
    """Get color code for UI display (Tailwind CSS classes)"""
    color_map = {
        CNELCategory.NORMALLY_ACCEPTABLE: "green",
        CNELCategory.CONDITIONALLY_ACCEPTABLE: "yellow",
        CNELCategory.NORMALLY_UNACCEPTABLE: "orange",
        CNELCategory.CLEARLY_UNACCEPTABLE: "red"
    }
    return color_map.get(category, "gray")
