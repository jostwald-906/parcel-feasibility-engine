"""
Tiered development standards for overlay zones.

Santa Monica uses tiered FAR and height standards in several areas:
- Downtown Community Plan (DCP): Tier 1/2/3 with increasing intensity
- Bergamot Area Plan: District-specific standards
- Affordable Housing Overlay (AHO): Enhanced standards for qualifying projects
- Some Mixed-Use corridors: Variable standards by location

This module provides tier-aware FAR and height resolution.

IMPORTANT: All tier multipliers and overlay standards are placeholders.
See docs/tier_standards_citations_needed.md for required SMMC citations.
"""
from app.models.parcel import ParcelBase
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# SANTA MONICA DOWNTOWN COMMUNITY PLAN TIER STANDARDS
# =============================================================================

# CITE: SMMC Chapter 9.10 (Downtown Districts)
# CITE: Downtown Community Plan (adopted July 25, 2017, amended 2023)
# CITE: SMMC § 9.23.030 (Community Benefits)
# STATUS: Confirmed standards from research (October 2025)

# Downtown Community Plan (DCP) - Transit Adjacent (TA) District
# CITE: DCP Table 4.2 (Development Standards by Tier)
DCP_TA_STANDARDS = {
    '1': {'far': 2.25, 'height': 45.0},  # Tier 1 Base (estimated - see note below)
    '2_nonres': {'far': 3.0, 'height': 60.0},  # Tier 2 non-residential
    '2_housing': {'far': 3.5, 'height': 60.0},  # Tier 2 with housing (+0.5 FAR bonus)
    '3': {'far': 4.0, 'height': 84.0},  # Tier 3 maximum
    '3_large_site': {'far': 4.0, 'height': 130.0}  # Special provisions for large sites
}

# Downtown Community Plan (DCP) - Neighborhood Village (NV) District
# CITE: DCP Table 4.2, Downtown Santa Monica Inc. recommendations
DCP_NV_STANDARDS = {
    '1': {'far': 2.0, 'height': 35.0},  # Tier 1 Base (estimated)
    '2_nonres': {'far': 2.75, 'height': 45.0},  # Tier 2 non-residential
    '2_housing': {'far': 3.25, 'height': 45.0},  # Tier 2 with housing (+0.5 FAR bonus)
    '3': None,  # Tier 3 NOT ALLOWED in NV district
    '100pct_affordable': {'far': 4.5, 'height': 94.0}  # 100% affordable special provision
}

# Note: Tier 1 base standards estimated from research. For precise values, consult:
# - Santa Monica Planning Division: (310) 458-8341
# - DCP Chapter 4 complete document (Table 4.2 not fully accessible online)
# - SMMC § 9.10 codified standards

# =============================================================================
# BERGAMOT AREA PLAN DISTRICT STANDARDS
# =============================================================================

# CITE: SMMC Chapter 9.04.090 and Chapter 9.12 (Bergamot Districts)
# CITE: Bergamot Area Plan (adopted September 2013, amended October 2023)
# STATUS: Confirmed standards from research (October 2025)

# Bergamot Transit Village (BTV) District
# CITE: SMMC § 9.12.030 Table A/B
BERGAMOT_BTV_STANDARDS = {
    '1': {'far': 1.75, 'height': 32.0},  # Tier 1 Base
    '2': {'far': 2.0, 'height': 60.0},   # Tier 2 with community benefits
    '3': {'far': 2.5, 'height': 75.0}    # Tier 3 with development agreement
}

# Bergamot Mixed-Use Creative (MUC) District
# CITE: SMMC § 9.12.030 Table A/B
BERGAMOT_MUC_STANDARDS = {
    '1': {'far': 1.5, 'height': 32.0},   # Tier 1 Base
    '2': {'far': 1.7, 'height': 47.0},   # Tier 2 with community benefits
    '3': {'far': 2.2, 'height': 57.0}    # Tier 3 with development agreement
}

# Bergamot Conservation Art Center (CAC) District
# CITE: SMMC § 9.12.030 Table A/B
# Note: Standards vary by parcel size
BERGAMOT_CAC_STANDARDS = {
    '1_large': {'far': 1.0, 'height': 32.0},   # ≥100,000 sf (City-owned)
    '2_large': {'far': 1.0, 'height': 60.0},
    '3_large': {'far': 1.0, 'height': 75.0},
    '1_small': {'far': 1.0, 'height': 32.0},   # <100,000 sf (Private)
    '2_small': {'far': 1.5, 'height': 60.0},
    '3_small': {'far': 2.5, 'height': 86.0}
}

# Special provisions:
# - Buildings >90 feet have additional design standards
# - Maximum podium height: 35 feet
# - Expo Light Rail integration required

# =============================================================================
# MODERATE INCOME HOUSING OVERLAY & DENSITY BONUS STANDARDS
# =============================================================================

# CITE: SMMC Chapter 9.17 (Moderate Income Overlay - MHO)
# CITE: SMMC Chapter 9.22 (Density Bonus Law)
# STATUS: Confirmed standards from research (October 2025)

# Note: The "Affordable Housing Overlay (AHO)" concept has been superseded by:
# 1. State Density Bonus Law (SMMC § 9.22) - handled in density_bonus.py
# 2. Moderate Income Housing Overlay (SMMC § 9.17) - specific to 80-120% AMI

# Moderate Income Housing Overlay (MHO) Bonuses
# CITE: SMMC § 9.17
MHO_DENSITY_BONUS = 0.5  # Up to 50% density increase
MHO_HEIGHT_BONUS = 33.0  # Up to +33 feet above maximum
MHO_PARKING_MINIMUM = 0  # No minimum off-street parking required

# State Density Bonus Height Bonuses (by zone type)
# CITE: SMMC § 9.22.060
DENSITY_BONUS_HEIGHT = {
    'residential': {'stories': 1, 'feet': 6},  # Up to 1 story AND 6 feet
    'residential_100pct_transit': {'stories': 3, 'feet': 33},  # 100% affordable near transit
    'nonresidential': {'feet': 11}  # Up to 11 feet in non-residential zones
}

# Density Bonus Percentages by Affordability
# CITE: SMMC § 9.22.050
DENSITY_BONUS_TABLE = {
    '5pct_very_low': 20,      # 5% very low income (≤50% AMI) = 20% bonus
    '10pct_low': 20,          # 10% low income (≤80% AMI) = 20% bonus
    '10pct_moderate': 5,      # 10% moderate (≤120% AMI, for-sale) = 5% bonus
    '100pct_affordable': 80   # 100% affordable = up to 80% bonus
}

# Income Level Definitions (California HCD standards)
INCOME_LEVELS = {
    'extremely_low': 0.30,  # <30% AMI
    'very_low': 0.50,       # <50% AMI
    'low': 0.80,            # 50-80% AMI
    'moderate': 1.20,       # 80-120% AMI
    'above_moderate': 1.21  # >120% AMI (market rate)
}


# TODO(SM): Verify all base zone FAR and height standards from SMMC
# CITE: SMMC Article 9 - Zoning Districts and Allowed Land Uses
# CITE: SMMC § 9.04 - Residential Zones (R1, R2, R3, R4)
# CITE: SMMC § 9.12 - Mixed-Use Zones (MUBL, MUBM, MUBH, MUB, MUCR, NV, WT)
# CITE: SMMC § 9.14 - Commercial Zones (C1, C2, C3, OC, OP)
# CITE: SMMC § 9.16 - Industrial Zones (I)
# CITE: SMMC § 9.28 - Development Standards (FAR, height, setbacks by zone)
# STATUS: Placeholder values - verify each zone against current SMMC
# NOTE: Some zones may have been updated or renamed since implementation

# Base zone FAR standards (from base_zoning.py)
BASE_ZONE_FAR = {
    'R1': 0.5,      # PLACEHOLDER - CITE: SMMC § [TBD]
    'R2': 0.75,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'R3': 1.5,      # PLACEHOLDER - CITE: SMMC § [TBD]
    'R4': 2.5,      # PLACEHOLDER - CITE: SMMC § [TBD]
    'NV': 1.0,      # Neighborhood Village - PLACEHOLDER - CITE: SMMC § [TBD]
    'WT': 1.75,     # Wilshire Transition - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUBL': 1.5,    # Mixed-Use Boulevard Low - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUBM': 2.0,    # Mixed-Use Boulevard Medium - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUBH': 3.0,    # Mixed-Use Boulevard High - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUB': 2.0,     # Mixed-Use Boulevard - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUCR': 2.0,    # Mixed-Use Creative - PLACEHOLDER - CITE: SMMC § [TBD]
    'C1': 2.0,      # PLACEHOLDER - CITE: SMMC § [TBD]
    'C2': 2.0,      # PLACEHOLDER - CITE: SMMC § [TBD]
    'C3': 2.0,      # PLACEHOLDER - CITE: SMMC § [TBD]
    'OC': 2.0,      # Office Commercial - PLACEHOLDER - CITE: SMMC § [TBD]
    'OP': 1.5,      # Office Professional - PLACEHOLDER - CITE: SMMC § [TBD]
    'I': 1.5,       # Industrial - PLACEHOLDER - CITE: SMMC § [TBD]
}

BASE_ZONE_HEIGHT = {
    'R1': 35.0,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'R2': 40.0,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'R3': 55.0,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'R4': 75.0,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'NV': 35.0,     # Neighborhood Village - PLACEHOLDER - CITE: SMMC § [TBD]
    'WT': 50.0,     # Wilshire Transition - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUBL': 45.0,   # Mixed-Use Boulevard Low - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUBM': 55.0,   # Mixed-Use Boulevard Medium - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUBH': 84.0,   # Mixed-Use Boulevard High - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUB': 65.0,    # Mixed-Use Boulevard - PLACEHOLDER - CITE: SMMC § [TBD]
    'MUCR': 65.0,   # Mixed-Use Creative - PLACEHOLDER - CITE: SMMC § [TBD]
    'C1': 65.0,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'C2': 65.0,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'C3': 65.0,     # PLACEHOLDER - CITE: SMMC § [TBD]
    'OC': 65.0,     # Office Commercial - PLACEHOLDER - CITE: SMMC § [TBD]
    'OP': 55.0,     # Office Professional - PLACEHOLDER - CITE: SMMC § [TBD]
    'I': 45.0,      # Industrial - PLACEHOLDER - CITE: SMMC § [TBD]
}


def get_base_far(zoning_code: str) -> float:
    """Get base FAR for a zoning code."""
    code = zoning_code.upper()

    # Try exact match first
    if code in BASE_ZONE_FAR:
        return BASE_ZONE_FAR[code]

    # Try partial match for codes like "R2A" -> "R2"
    for key in BASE_ZONE_FAR:
        if code.startswith(key):
            return BASE_ZONE_FAR[key]

    # Default fallback
    return 1.0


def get_base_height(zoning_code: str) -> float:
    """Get base height for a zoning code."""
    code = zoning_code.upper()

    # Try exact match first
    if code in BASE_ZONE_HEIGHT:
        return BASE_ZONE_HEIGHT[code]

    # Try partial match
    for key in BASE_ZONE_HEIGHT:
        if code.startswith(key):
            return BASE_ZONE_HEIGHT[key]

    # Default fallback
    return 35.0


def compute_max_far(parcel: ParcelBase) -> Tuple[float, str]:
    """
    Compute maximum FAR considering base zoning and overlays.

    This function applies tier-aware FAR resolution with the following precedence:
    1. DCP tier multipliers (if DCP overlay and tier specified)
    2. Bergamot fixed FAR (if Bergamot overlay)
    3. Base zoning FAR (fallback)
    4. AHO bonus (additive, applied on top of base/tier/bergamot)

    Args:
        parcel: Parcel with zoning and overlay information

    Returns:
        Tuple of (max_far, source_description)

    Logs:
        WARNING if using placeholder values
        INFO for tier resolution logic
    """
    base_far = get_base_far(parcel.zoning_code)
    max_far = base_far
    source = f"Base zoning ({parcel.zoning_code})"

    overlay_codes = parcel.overlay_codes or []
    tier = parcel.development_tier

    # Log placeholder value warning
    logger.warning(
        f"compute_max_far using PLACEHOLDER values for parcel {parcel.apn}. "
        "See docs/tier_standards_citations_needed.md for required SMMC citations."
    )

    # Check for DCP tier
    if 'DCP' in overlay_codes and tier and tier in DCP_TIER_FAR_MULTIPLIER:
        multiplier = DCP_TIER_FAR_MULTIPLIER[tier]
        max_far = base_far * multiplier
        source = f"DCP Tier {tier}"
        logger.info(
            f"Applied DCP Tier {tier} multiplier ({multiplier}x) to {parcel.zoning_code} "
            f"base FAR ({base_far}) = {max_far}"
        )

    # Check for Bergamot
    elif 'Bergamot' in overlay_codes:
        # TODO(SM): Map parcel to specific Bergamot district
        # For now, use default
        max_far = BERGAMOT_FAR['default']
        source = "Bergamot Area Plan"
        logger.info(
            f"Applied Bergamot default FAR ({max_far}) overriding {parcel.zoning_code} "
            f"base FAR ({base_far})"
        )

    # Check for AHO bonus (additive)
    if 'AHO' in overlay_codes:
        pre_aho_far = max_far
        max_far += AHO_FAR_BONUS
        source = f"{source} + AHO bonus"
        logger.info(
            f"Applied AHO bonus (+{AHO_FAR_BONUS}) to FAR: {pre_aho_far} -> {max_far}"
        )

    logger.info(f"Final FAR for parcel {parcel.apn}: {max_far} (source: {source})")
    return max_far, source


def compute_max_height(parcel: ParcelBase) -> Tuple[float, str]:
    """
    Compute maximum height considering base zoning and overlays.

    This function applies tier-aware height resolution with the following precedence:
    1. DCP tier bonuses (if DCP overlay and tier specified) - additive
    2. Bergamot fixed height (if Bergamot overlay) - replaces base
    3. Base zoning height (fallback)
    4. AHO bonus (additive, applied on top of base/tier/bergamot)

    Args:
        parcel: Parcel with zoning and overlay information

    Returns:
        Tuple of (max_height_ft, source_description)

    Logs:
        WARNING if using placeholder values
        INFO for tier resolution logic
    """
    base_height = get_base_height(parcel.zoning_code)
    max_height = base_height
    source = f"Base zoning ({parcel.zoning_code})"

    overlay_codes = parcel.overlay_codes or []
    tier = parcel.development_tier

    # Log placeholder value warning
    logger.warning(
        f"compute_max_height using PLACEHOLDER values for parcel {parcel.apn}. "
        "See docs/tier_standards_citations_needed.md for required SMMC citations."
    )

    # Check for DCP tier
    if 'DCP' in overlay_codes and tier and tier in DCP_TIER_HEIGHT_BONUS:
        bonus = DCP_TIER_HEIGHT_BONUS[tier]
        max_height = base_height + bonus
        source = f"DCP Tier {tier}"
        logger.info(
            f"Applied DCP Tier {tier} bonus (+{bonus} ft) to {parcel.zoning_code} "
            f"base height ({base_height} ft) = {max_height} ft"
        )

    # Check for Bergamot
    elif 'Bergamot' in overlay_codes:
        # TODO(SM): Map parcel to specific Bergamot district
        max_height = BERGAMOT_HEIGHT['default']
        source = "Bergamot Area Plan"
        logger.info(
            f"Applied Bergamot default height ({max_height} ft) overriding {parcel.zoning_code} "
            f"base height ({base_height} ft)"
        )

    # Check for AHO bonus (additive)
    if 'AHO' in overlay_codes:
        pre_aho_height = max_height
        max_height += AHO_HEIGHT_BONUS
        source = f"{source} + AHO bonus"
        logger.info(
            f"Applied AHO bonus (+{AHO_HEIGHT_BONUS} ft) to height: {pre_aho_height} -> {max_height} ft"
        )

    logger.info(f"Final height for parcel {parcel.apn}: {max_height} ft (source: {source})")
    return max_height, source


def get_tier_info(parcel: ParcelBase) -> Optional[str]:
    """
    Get a human-readable description of applicable tiers/overlays.

    Args:
        parcel: Parcel with overlay information

    Returns:
        Description string or None if no special tiers apply
    """
    overlay_codes = parcel.overlay_codes or []
    tier = parcel.development_tier

    parts = []

    if 'DCP' in overlay_codes and tier:
        parts.append(f"Downtown Community Plan Tier {tier}")

    if 'Bergamot' in overlay_codes:
        parts.append("Bergamot Area Plan")

    if 'AHO' in overlay_codes:
        parts.append("Affordable Housing Overlay")

    return ", ".join(parts) if parts else None
