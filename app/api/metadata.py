"""
Metadata API endpoints.

Provides reference data like zoning codes, overlay types, cities, etc.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from app.constants.zoning_codes import (
    SANTA_MONICA_ZONING_CODES,
    ZONING_CATEGORIES,
    get_all_zoning_codes_for_dropdown,
    get_categorized_zoning_codes,
    get_zoning_description,
    get_zoning_category
)
from app.cities.registry import city_registry, get_city_config

router = APIRouter()


@router.get("/zoning-codes")
async def get_zoning_codes() -> List[Dict[str, str]]:
    """
    Get all Santa Monica zoning codes for dropdown/autocomplete.

    Returns list of {value, label} objects suitable for form dropdowns.
    """
    return get_all_zoning_codes_for_dropdown()


@router.get("/zoning-codes/categorized")
async def get_zoning_codes_categorized() -> Dict[str, List[Dict[str, str]]]:
    """
    Get zoning codes organized by category.

    Returns dict with category names as keys and lists of {value, label} as values.
    Useful for grouped dropdowns.
    """
    return get_categorized_zoning_codes()


@router.get("/zoning-codes/{code}")
async def get_zoning_code_info(code: str) -> Dict[str, str]:
    """
    Get information about a specific zoning code.

    Args:
        code: Zoning code (e.g., "R1", "TA")

    Returns:
        Dict with code, description, and category
    """
    return {
        "code": code.upper(),
        "description": get_zoning_description(code),
        "category": get_zoning_category(code)
    }


@router.get("/zoning-codes/raw/all")
async def get_all_zoning_codes_raw() -> Dict[str, str]:
    """
    Get raw zoning codes dictionary.

    Returns:
        Dict mapping zoning codes to descriptions
    """
    return SANTA_MONICA_ZONING_CODES


@router.get("/zoning-categories")
async def get_zoning_categories() -> Dict[str, List[str]]:
    """
    Get zoning categories with their member codes.

    Returns:
        Dict mapping category names to lists of zoning codes
    """
    return ZONING_CATEGORIES


# City Configuration Endpoints

@router.get("/cities")
async def list_cities() -> List[Dict[str, str]]:
    """
    Get list of all available cities.

    Returns:
        List of dicts with city code, name, and state
        Example: [{"code": "SM", "name": "Santa Monica", "state": "CA"}]
    """
    return city_registry.list_cities()


@router.get("/cities/{city_code}")
async def get_city_details(city_code: str) -> Dict:
    """
    Get detailed configuration for a specific city.

    Args:
        city_code: City code (e.g., 'SM', 'LA', 'SF')

    Returns:
        Complete city configuration including zoning codes, overlays, GIS services, etc.

    Raises:
        HTTPException: If city not found
    """
    try:
        city = get_city_config(city_code)
        return city.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/cities/{city_code}/zoning-codes")
async def get_city_zoning_codes(city_code: str) -> List[Dict[str, str]]:
    """
    Get zoning codes for a specific city.

    Args:
        city_code: City code (e.g., 'SM', 'LA', 'SF')

    Returns:
        List of zoning codes with code, description, and category
    """
    try:
        city = get_city_config(city_code)
        return [
            {
                "code": z.code,
                "description": z.description,
                "category": z.category
            }
            for z in city.get_zoning_codes()
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/cities/{city_code}/overlays")
async def get_city_overlays(city_code: str) -> List[Dict[str, str]]:
    """
    Get overlay zones and special plan areas for a specific city.

    Args:
        city_code: City code (e.g., 'SM', 'LA', 'SF')

    Returns:
        List of overlay zones with name, code, and description
    """
    try:
        city = get_city_config(city_code)
        return [
            {
                "name": o.name,
                "code": o.code,
                "description": o.description,
                "applies_by_zoning": o.applies_by_zoning,
                "affected_zones": o.affected_zones
            }
            for o in city.get_overlay_zones()
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
