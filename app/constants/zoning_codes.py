"""
Santa Monica Zoning Codes

Complete list of zoning codes from Santa Monica GIS Zoning service.
Data source: https://gis.santamonica.gov/server/rest/services/Zoning_Update/FeatureServer/0

Last updated: 2025-01-06
"""

from typing import Dict, List


# Complete list of Santa Monica zoning codes with descriptions
SANTA_MONICA_ZONING_CODES: Dict[str, str] = {
    # Residential Zones
    "R1": "Single-Unit Residential",
    "R2": "Low Density Residential",
    "R3": "Medium Density Residential",
    "R4": "Medium Density Residential",
    "RMH": "Residential Mobile Home Park",
    "OP1": "Ocean Park Single-Unit Residential",
    "OP2": "Ocean Park Low Density Residential",
    "OP3": "Ocean Park Medium Density Residential",
    "OP4": "Ocean Park High Density Residential",
    "OPD": "Ocean Park Duplex",

    # Commercial & Mixed-Use Zones
    "NC": "Neighborhood Commercial",
    "GC": "General Commercial",
    "MUB": "Mixed-Use Boulevard",
    "MUBL": "Mixed-Use Boulevard Low",
    "HMU": "Healthcare Mixed-Use",
    "OC": "Office Campus",
    "LT": "Lincoln Transition",
    "WT": "Wilshire Transition",
    "OT": "Ocean Transition",

    # Downtown Community Plan
    "TA": "Transit Adjacent",
    "NV": "Neighborhood Village",

    # Bergamot Area Plan
    "BTV": "Bergamot Transit Village",
    "MUC": "Mixed Use Creative",
    "CAC": "Conservation: Art Center",

    # Special Districts
    "OF": "Oceanfront",
    "BC": "Bayside Conservation",
    "CCS": "Conservation: Creative Sector",
    "IC": "Industrial Conservation",
    "CC": "Civic Center",
    "OS": "Parks and Open Space",
    "PL": "Institutional/Public Lands",
}


# Zoning categories for organization
ZONING_CATEGORIES: Dict[str, List[str]] = {
    "Residential": ["R1", "R2", "R3", "R4", "RMH", "OP1", "OP2", "OP3", "OP4", "OPD"],
    "Commercial & Mixed-Use": ["NC", "GC", "MUB", "MUBL", "HMU", "OC", "LT", "WT", "OT"],
    "Downtown Community Plan": ["TA", "NV"],
    "Bergamot Area Plan": ["BTV", "MUC", "CAC"],
    "Special Districts": ["OF", "BC", "CCS", "IC", "CC", "OS", "PL"],
}


# Residential zones (for SB9 and other residential-specific rules)
RESIDENTIAL_ZONES = ["R1", "R2", "R3", "R4", "RMH", "OP1", "OP2", "OP3", "OP4", "OPD"]

# Single-family zones (for SB9 eligibility)
SINGLE_FAMILY_ZONES = ["R1", "OP1"]

# Commercial zones (for AB2011 eligibility)
COMMERCIAL_ZONES = ["NC", "GC", "MUB", "MUBL", "HMU", "OC", "LT", "WT", "OT"]

# Downtown zones (for DCP scenarios)
DOWNTOWN_ZONES = ["TA", "NV"]

# Bergamot zones (for Bergamot scenarios)
BERGAMOT_ZONES = ["BTV", "MUC", "CAC"]


def get_zoning_description(zoning_code: str) -> str:
    """
    Get the full description for a zoning code.

    Args:
        zoning_code: Zoning code (e.g., "R1", "TA")

    Returns:
        Full description or "Unknown Zone" if not found
    """
    return SANTA_MONICA_ZONING_CODES.get(zoning_code.upper(), "Unknown Zone")


def get_zoning_category(zoning_code: str) -> str:
    """
    Get the category for a zoning code.

    Args:
        zoning_code: Zoning code (e.g., "R1", "TA")

    Returns:
        Category name or "Other" if not found
    """
    code = zoning_code.upper()
    for category, codes in ZONING_CATEGORIES.items():
        if code in codes:
            return category
    return "Other"


def is_residential_zone(zoning_code: str) -> bool:
    """Check if zoning code is residential."""
    return zoning_code.upper() in RESIDENTIAL_ZONES


def is_single_family_zone(zoning_code: str) -> bool:
    """Check if zoning code is single-family (for SB9)."""
    return zoning_code.upper() in SINGLE_FAMILY_ZONES


def is_commercial_zone(zoning_code: str) -> bool:
    """Check if zoning code is commercial (for AB2011)."""
    return zoning_code.upper() in COMMERCIAL_ZONES


def is_downtown_zone(zoning_code: str) -> bool:
    """Check if zoning code is in Downtown Community Plan area."""
    return zoning_code.upper() in DOWNTOWN_ZONES


def is_bergamot_zone(zoning_code: str) -> bool:
    """Check if zoning code is in Bergamot Area Plan."""
    return zoning_code.upper() in BERGAMOT_ZONES


def get_all_zoning_codes_for_dropdown() -> List[Dict[str, str]]:
    """
    Get all zoning codes formatted for dropdown display.

    Returns:
        List of dicts with 'value' (code) and 'label' (code + description)
    """
    return [
        {
            "value": code,
            "label": f"{code} - {description}"
        }
        for code, description in sorted(SANTA_MONICA_ZONING_CODES.items())
    ]


def get_categorized_zoning_codes() -> Dict[str, List[Dict[str, str]]]:
    """
    Get zoning codes organized by category for grouped dropdown.

    Returns:
        Dict with category names as keys and lists of {value, label} dicts as values
    """
    result = {}
    for category, codes in ZONING_CATEGORIES.items():
        result[category] = [
            {
                "value": code,
                "label": f"{code} - {SANTA_MONICA_ZONING_CODES[code]}"
            }
            for code in codes
        ]
    return result
