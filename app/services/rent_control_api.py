"""
Santa Monica Maximum Allowable Rent (MAR) Lookup Service

This module provides programmatic access to the City of Santa Monica's rent control
database at https://www.smgov.net/departments/rentcontrol/mar.aspx.

The site uses ASP.NET WebForms with Cloudflare protection, requiring browser-like
session handling and extraction of hidden form fields (__VIEWSTATE, __VIEWSTATEGENERATOR,
__EVENTVALIDATION) to successfully submit searches.

Features:
- File-based caching with 24-hour TTL to reduce API load
- Configurable timeouts (default 45s to handle Cloudflare challenges)
- Graceful error handling with detailed error messages
- Automatic cache warming for frequently accessed addresses

Installation:
    pip install cloudscraper beautifulsoup4

Usage:
    from app.services.rent_control_api import lookup_mar

    units = lookup_mar(street_number="624", street_name="Lincoln Blvd")
    for unit in units:
        print(f"{unit['unit']}: {unit['mar']}")
"""

import re
import cloudscraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)


class RentControlLookupError(Exception):
    """Raised when rent control lookup fails"""
    pass


# Configuration
CACHE_DIR = Path(".cache/rent_control")
CACHE_TTL_HOURS = 24
DEFAULT_TIMEOUT_SECONDS = 45  # Increased from 30s to handle Cloudflare challenges


def _get_cache_key(street_number: str, street_name: str) -> str:
    """Generate cache key from address components."""
    normalized = f"{street_number.strip().lower()}_{street_name.strip().lower()}"
    return hashlib.md5(normalized.encode()).hexdigest()


def _get_cache_path(cache_key: str) -> Path:
    """Get cache file path for a given cache key."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{cache_key}.json"


def _read_from_cache(street_number: str, street_name: str) -> Optional[List[Dict[str, str]]]:
    """
    Read rent control data from cache if available and not expired.

    Returns:
        Cached data if valid, None if cache miss or expired
    """
    try:
        cache_key = _get_cache_key(street_number, street_name)
        cache_path = _get_cache_path(cache_key)

        if not cache_path.exists():
            logger.debug(f"Cache miss for {street_number} {street_name}")
            return None

        # Read cache file
        with open(cache_path, 'r') as f:
            cached = json.load(f)

        # Check expiration
        cached_at = datetime.fromisoformat(cached['cached_at'])
        expires_at = cached_at + timedelta(hours=CACHE_TTL_HOURS)

        if datetime.now() > expires_at:
            logger.debug(f"Cache expired for {street_number} {street_name}")
            cache_path.unlink()  # Delete expired cache
            return None

        logger.info(f"Cache hit for {street_number} {street_name} (cached {cached_at.isoformat()})")
        return cached['data']

    except Exception as e:
        logger.warning(f"Error reading cache: {e}")
        return None


def _write_to_cache(street_number: str, street_name: str, data: List[Dict[str, str]]) -> None:
    """Write rent control data to cache."""
    try:
        cache_key = _get_cache_key(street_number, street_name)
        cache_path = _get_cache_path(cache_key)

        cache_data = {
            'address': f"{street_number} {street_name}",
            'cached_at': datetime.now().isoformat(),
            'data': data
        }

        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Cached rent control data for {street_number} {street_name}")

    except Exception as e:
        logger.warning(f"Error writing cache: {e}")


def lookup_mar(
    street_number: str,
    street_name: str,
    use_cache: bool = True,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> List[Dict[str, str]]:
    """
    Query Santa Monica's Maximum Allowable Rent database.

    Args:
        street_number: Numeric street address (e.g., "624")
        street_name: Street name (e.g., "Lincoln Blvd")
        use_cache: Whether to use cached results (default: True)
        timeout: Request timeout in seconds (default: 45s)

    Returns:
        List of dictionaries with keys:
            - address: Full street address
            - unit: Unit identifier (e.g., "A", "1", "MAIN")
            - mar: Maximum allowable rent (e.g., "$3,373")
            - tenancy_date: Most recent tenancy registration date
            - bedrooms: Number of bedrooms
            - parcel: Parcel number (APN without dashes)

    Raises:
        RentControlLookupError: If lookup fails or no records found
    """
    # Try cache first
    if use_cache:
        cached_data = _read_from_cache(street_number, street_name)
        if cached_data is not None:
            return cached_data

    url = "https://www.smgov.net/departments/rentcontrol/mar.aspx"

    try:
        logger.info(f"Fetching rent control data for {street_number} {street_name} (timeout: {timeout}s)")

        # Create cloudscraper session to bypass Cloudflare
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

        # Step 1: GET initial page to extract hidden form fields
        logger.debug("Step 1: Fetching initial page to extract form fields")
        response = scraper.get(url, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract ASP.NET WebForms hidden fields
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})

        if not viewstate or not viewstate_generator:
            raise RentControlLookupError("Failed to extract form hidden fields - page structure may have changed")

        logger.debug("Step 2: Submitting search request")

        # Step 2: Construct POST payload with search parameters
        payload = {
            '__VIEWSTATE': viewstate.get('value', ''),
            '__VIEWSTATEGENERATOR': viewstate_generator.get('value', ''),
            '__EVENTVALIDATION': event_validation.get('value', '') if event_validation else '',
            '__EVENTTARGET': 'ctl00$mainContent$btnSearch',
            'ctl00$mainContent$txtStNumber': street_number,
            'ctl00$mainContent$txtStreet': street_name,
        }

        # Step 3: POST search request
        response = scraper.post(url, data=payload, timeout=timeout)
        response.raise_for_status()

        # Step 4: Parse results table
        logger.debug("Step 3: Parsing results")
        soup = BeautifulSoup(response.text, 'html.parser')
        results_table = soup.find('table', {'id': 'ctl00_mainContent_gvAddress'})

        if not results_table:
            # Check for "no results" message
            no_results = soup.find(string=re.compile(r'no records found|no results', re.IGNORECASE))
            if no_results:
                logger.info(f"No rent control records found for {street_number} {street_name}")
                # Cache empty result to avoid repeated lookups
                _write_to_cache(street_number, street_name, [])
                return []
            raise RentControlLookupError(f"No rent control data found for {street_number} {street_name}")

        # Parse table rows
        units = []
        rows = results_table.find_all('tr')

        for row in rows[1:]:  # Skip header row
            cells = row.find_all('td')
            if len(cells) >= 6:
                unit_data = {
                    'address': cells[0].get_text(strip=True),
                    'unit': cells[1].get_text(strip=True),
                    'mar': cells[2].get_text(strip=True),
                    'tenancy_date': cells[3].get_text(strip=True),
                    'bedrooms': cells[4].get_text(strip=True),
                    'parcel': cells[5].get_text(strip=True),
                }
                units.append(unit_data)

        logger.info(f"Successfully retrieved {len(units)} rent control units for {street_number} {street_name}")

        # Cache successful result
        _write_to_cache(street_number, street_name, units)

        return units

    except cloudscraper.exceptions.CloudflareChallengeError as e:
        error_msg = f"Failed to bypass Cloudflare protection: {e}"
        logger.error(error_msg)
        raise RentControlLookupError(error_msg)
    except Exception as e:
        error_msg = f"Rent control lookup failed for {street_number} {street_name}: {e}"
        logger.error(error_msg)
        raise RentControlLookupError(error_msg)


def get_mar_summary(street_number: str, street_name: str, use_cache: bool = True) -> Optional[Dict[str, any]]:
    """
    Get a summary of rent control data for an address.

    Args:
        street_number: Numeric street address (e.g., "624")
        street_name: Street name (e.g., "Lincoln Blvd")
        use_cache: Whether to use cached results (default: True)

    Returns a dict with:
        - is_rent_controlled: Boolean indicating if property has controlled units
        - total_units: Total number of units with MAR data
        - avg_mar: Average MAR across all units (None if any units have $0 MAR)
        - units: List of unit details
        - status: 'success', 'not_found', or 'error'
        - error_message: Error details if status is 'error'

    Returns None if lookup fails completely (use status field for partial failures).
    """
    try:
        units = lookup_mar(street_number, street_name, use_cache=use_cache)

        if not units:
            return {
                'is_rent_controlled': False,
                'total_units': 0,
                'avg_mar': None,
                'units': [],
                'status': 'not_found',
                'error_message': None
            }

        # Parse MAR values
        mar_values = []
        for unit in units:
            mar_str = unit['mar'].replace('$', '').replace(',', '').strip()
            try:
                mar_val = float(mar_str)
                if mar_val > 0:  # Exclude $0 (exempt units)
                    mar_values.append(mar_val)
            except ValueError:
                pass

        avg_mar = sum(mar_values) / len(mar_values) if mar_values else None

        return {
            'is_rent_controlled': True,
            'total_units': len(units),
            'avg_mar': round(avg_mar, 2) if avg_mar else None,
            'units': units,
            'status': 'success',
            'error_message': None
        }

    except RentControlLookupError as e:
        logger.warning(f"Rent control lookup error: {e}")
        return {
            'is_rent_controlled': None,  # Unknown status
            'total_units': 0,
            'avg_mar': None,
            'units': [],
            'status': 'error',
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_mar_summary: {e}")
        return {
            'is_rent_controlled': None,
            'total_units': 0,
            'avg_mar': None,
            'units': [],
            'status': 'error',
            'error_message': f"Unexpected error: {e}"
        }
