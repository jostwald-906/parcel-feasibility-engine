"""
RHNA Data Service for SB35 Affordability Determinations.

This service manages California HCD RHNA (Regional Housing Needs Allocation)
progress data to determine SB35 affordability requirements for jurisdictions.

Data Source: California HCD SB35 Determination Dataset
URL: https://data.ca.gov/dataset/sb-35-data

The service loads official HCD determinations showing which jurisdictions
require 10% vs 50% affordable housing under SB35 streamlining.
"""

from typing import Optional, Dict
import csv
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RHNADataService:
    """
    Service for looking up jurisdiction RHNA performance and SB35 affordability requirements.

    This service provides access to official HCD determinations of which jurisdictions
    are subject to SB35 streamlining and their required affordability percentages.

    Attributes:
        data_file: Path to the SB35 determination CSV file
        cache: Dictionary mapping jurisdiction names to their determination data
        last_updated: Timestamp of when data was last loaded
        cache_duration: How long to keep data before refreshing (default: 7 days)
    """

    def __init__(self, data_file: str = "data/sb35_determinations.csv"):
        """
        Initialize the RHNA data service.

        Args:
            data_file: Path to SB35 determination CSV file (relative to project root)
        """
        # Handle both relative and absolute paths
        self.data_file = Path(data_file)
        if not self.data_file.is_absolute():
            # Assume relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.data_file = project_root / data_file

        self.cache: Dict[str, dict] = {}
        self.last_updated: Optional[datetime] = None
        self.cache_duration = timedelta(days=7)  # Refresh weekly
        self._load_data()

    def _load_data(self):
        """
        Load RHNA determination data from CSV.

        The CSV contains columns:
        - County: County name
        - Jurisdiction: City/county name
        - 10%: "Yes" if 10% affordability applies
        - 50%: "Yes" if 50% affordability applies
        - Exempt: "Yes" if jurisdiction is exempt (met RHNA targets)
        - Above MOD % Complete: Percentage of above-moderate RHNA achieved
        - Planning Period Progress: Overall RHNA progress percentage
        """
        if not self.data_file.exists():
            logger.warning(f"RHNA data file not found: {self.data_file}")
            logger.warning("Service will use fallback logic for all jurisdictions")
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8-sig') as f:  # Handle BOM
                reader = csv.DictReader(f)
                for row in reader:
                    jurisdiction = row['Jurisdiction'].strip().upper()
                    county = row['County'].strip().upper()

                    # Determine affordability percentage from HCD determination
                    requires_10_pct = row.get('10%', '').strip().upper() == 'YES'
                    requires_50_pct = row.get('50%', '').strip().upper() == 'YES'
                    is_exempt = row.get('Exempt', '').strip().upper() == 'YES'

                    # Parse above-moderate progress percentage
                    above_mod_str = row.get('Above MOD % Complete', '').strip()
                    try:
                        # Remove % sign if present and convert to float
                        above_mod_progress = float(above_mod_str.replace('%', ''))
                    except (ValueError, AttributeError):
                        above_mod_progress = None

                    # Determine affordability requirement
                    if is_exempt:
                        affordability_pct = 0.0  # Exempt - no SB35 streamlining applies
                    elif requires_10_pct:
                        affordability_pct = 10.0
                    elif requires_50_pct:
                        affordability_pct = 50.0
                    else:
                        # Shouldn't happen, but be conservative
                        affordability_pct = 50.0

                    # Store jurisdiction data (indexed by jurisdiction name)
                    self.cache[jurisdiction] = {
                        'jurisdiction': row['Jurisdiction'].strip(),
                        'county': row['County'].strip(),
                        'affordability_pct': affordability_pct,
                        'above_moderate_progress': above_mod_progress,
                        'is_exempt': is_exempt,
                        'requires_10_pct': requires_10_pct,
                        'requires_50_pct': requires_50_pct,
                        'planning_period': row.get('Planning Period Progress', '').strip(),
                        'last_apr': row.get('Last APR', '').strip()
                    }

                    # Also store by "COUNTY - JURISDICTION" format for disambiguation
                    full_key = f"{county} - {jurisdiction}"
                    self.cache[full_key] = self.cache[jurisdiction]

            self.last_updated = datetime.now()
            logger.info(f"Loaded RHNA data for {len(self.cache) // 2} jurisdictions from {self.data_file}")
            logger.info(f"Data last updated: {self.last_updated}")

        except Exception as e:
            logger.error(f"Failed to load RHNA data: {e}")
            logger.warning("Service will use fallback logic for all jurisdictions")

    def get_sb35_affordability(self, jurisdiction: str, county: Optional[str] = None) -> dict:
        """
        Get SB35 affordability requirement for a jurisdiction.

        Args:
            jurisdiction: City or county name (case-insensitive)
            county: Optional county name for disambiguation

        Returns:
            Dictionary with:
            {
                'percentage': 0.0, 10.0, or 50.0 - Required affordable percentage
                'income_levels': List of income categories required
                'source': Data source description
                'last_updated': Date of data
                'notes': List of explanatory notes
                'is_exempt': Whether jurisdiction is exempt from SB35
                'above_moderate_progress': Percentage of above-moderate RHNA met
            }
        """
        jurisdiction_upper = jurisdiction.upper().strip()

        # Try exact match first
        if jurisdiction_upper in self.cache:
            return self._format_determination(self.cache[jurisdiction_upper])

        # Try with county if provided
        if county:
            county_upper = county.upper().strip()
            full_key = f"{county_upper} - {jurisdiction_upper}"
            if full_key in self.cache:
                return self._format_determination(self.cache[full_key])

        # Try partial match (e.g., "Los Angeles" matches "LOS ANGELES")
        for key, data in self.cache.items():
            if ' - ' in key:  # Skip the "COUNTY - JURISDICTION" entries
                continue
            if jurisdiction_upper in key or key in jurisdiction_upper:
                logger.info(f"Partial match found: '{jurisdiction}' matched to '{data['jurisdiction']}'")
                return self._format_determination(data)

        # No match found - use fallback logic
        logger.warning(f"No RHNA data found for '{jurisdiction}', using fallback logic")
        return self._fallback_determination(jurisdiction)

    def _format_determination(self, data: dict) -> dict:
        """
        Format jurisdiction data into standardized response.

        Args:
            data: Raw jurisdiction data from cache

        Returns:
            Formatted determination dictionary
        """
        affordability_pct = data['affordability_pct']
        above_mod_progress = data['above_moderate_progress']

        # Determine income levels based on affordability percentage
        if affordability_pct == 0.0:
            income_levels = []
            income_desc = "None (jurisdiction exempt from SB35)"
        elif affordability_pct == 10.0:
            income_levels = ['Lower Income']
            income_desc = "Lower Income (≤80% AMI)"
        else:  # 50%
            income_levels = ['Very Low Income', 'Lower Income']
            income_desc = "Mix of Very Low Income (≤50% AMI) and Lower Income (≤80% AMI)"

        # Build notes
        notes = []

        if data['is_exempt']:
            notes.append(f"JURISDICTION STATUS: {data['jurisdiction']} is EXEMPT from SB35 streamlining")
            notes.append(f"Reason: Jurisdiction has met or exceeded RHNA housing targets")
            if above_mod_progress is not None:
                notes.append(f"Above-moderate RHNA progress: {above_mod_progress:.1f}%")
            notes.append("SB35 streamlined ministerial approval does NOT apply")
            notes.append("Project must follow standard discretionary review process")
        else:
            notes.append(f"AFFORDABILITY REQUIREMENT: {affordability_pct}% affordable units required")
            notes.append(f"Income targeting: {income_desc}")

            if above_mod_progress is not None:
                notes.append(f"Above-moderate RHNA progress: {above_mod_progress:.1f}%")
                if affordability_pct == 10.0:
                    notes.append("Jurisdiction met >50% of above-moderate RHNA target")
                else:
                    notes.append("Jurisdiction did NOT meet >50% of above-moderate RHNA target")

            if affordability_pct == 50.0:
                notes.append("Income mix requirements:")
                notes.append("  - If jurisdiction met ≤10% of above-moderate: 50% Very Low + 50% Lower")
                notes.append("  - If >10% but ≤50%: Mix varies by RHNA category shortfall")

            notes.append(f"Planning period: {data['planning_period']}")
            notes.append(f"Last Annual Progress Report (APR): {data['last_apr']}")

        notes.append("")
        notes.append("Data source: California HCD SB35 Determination Dataset")
        notes.append("URL: https://data.ca.gov/dataset/sb-35-data")
        notes.append(f"Data loaded: {self.last_updated.strftime('%Y-%m-%d') if self.last_updated else 'Unknown'}")
        notes.append("")
        notes.append("IMPORTANT: Always verify current RHNA status with local planning department")
        notes.append("HCD determination data may not reflect most recent Annual Progress Reports")

        return {
            'percentage': affordability_pct,
            'income_levels': income_levels,
            'source': 'HCD SB35 Determination Dataset',
            'last_updated': data['last_apr'],
            'notes': notes,
            'is_exempt': data['is_exempt'],
            'above_moderate_progress': above_mod_progress,
            'jurisdiction': data['jurisdiction'],
            'county': data['county']
        }

    def _fallback_determination(self, jurisdiction: str) -> dict:
        """
        Conservative fallback determination when no RHNA data is available.

        Uses basic heuristics based on historically high-performing cities.
        This is a last resort and should be verified with planning department.

        Args:
            jurisdiction: City name

        Returns:
            Fallback determination with conservative 50% default
        """
        # Known high-performing cities (historical data)
        # These cities have historically met >50% of above-moderate RHNA
        high_performing_cities = [
            "SAN FRANCISCO",
            "SAN JOSE",
            "SACRAMENTO",
            "OAKLAND",
            "FREMONT",
            "DALY CITY"
        ]

        is_high_performing = any(
            city in jurisdiction.upper()
            for city in high_performing_cities
        )

        if is_high_performing:
            # Likely 10% requirement (but still needs verification)
            percentage = 10.0
            income_levels = ['Lower Income']
            reason = f"Estimated 10% (historically {jurisdiction} met RHNA targets)"
        else:
            # Conservative default: assume 50% requirement
            percentage = 50.0
            income_levels = ['Very Low Income', 'Lower Income']
            reason = f"Estimated 50% (conservative default - no HCD data available)"

        return {
            'percentage': percentage,
            'income_levels': income_levels,
            'source': 'Estimated (no official HCD data)',
            'last_updated': 'Unknown',
            'notes': [
                f"WARNING: {reason}",
                "",
                f"AFFORDABILITY: {percentage}% affordable (ESTIMATED - NOT VERIFIED)",
                "",
                "CRITICAL: No official RHNA data found for this jurisdiction",
                "This is a conservative estimate based on historical patterns",
                "",
                "YOU MUST verify actual RHNA performance with:",
                "  1. Local planning department",
                "  2. HCD SMAP Dashboard: https://www.hcd.ca.gov/planning-and-community-development/streamlined-ministerial-approval-process-dashboard",
                "  3. Latest Annual Progress Report (APR)",
                "",
                "DO NOT rely on this estimate for legal or regulatory purposes",
                "Actual affordability requirement may differ significantly"
            ],
            'is_exempt': False,  # Assume not exempt (conservative)
            'above_moderate_progress': None,
            'jurisdiction': jurisdiction,
            'county': 'Unknown'
        }

    def list_jurisdictions(self, county: Optional[str] = None) -> list:
        """
        List all jurisdictions with available RHNA data.

        Args:
            county: Optional county filter

        Returns:
            List of jurisdiction names
        """
        jurisdictions = []
        seen = set()

        for key, data in self.cache.items():
            if ' - ' in key:  # Skip combined keys
                continue

            if county and data['county'].upper() != county.upper():
                continue

            juris_name = data['jurisdiction']
            if juris_name not in seen:
                jurisdictions.append({
                    'jurisdiction': juris_name,
                    'county': data['county'],
                    'affordability_pct': data['affordability_pct'],
                    'is_exempt': data['is_exempt']
                })
                seen.add(juris_name)

        return sorted(jurisdictions, key=lambda x: (x['county'], x['jurisdiction']))

    def get_summary_stats(self) -> dict:
        """
        Get summary statistics about loaded RHNA data.

        Returns:
            Dictionary with counts and percentages
        """
        if not self.cache:
            return {
                'total_jurisdictions': 0,
                'exempt_count': 0,
                'requires_10_pct_count': 0,
                'requires_50_pct_count': 0
            }

        # Count unique jurisdictions (skip combined keys)
        unique_jurisdictions = [
            data for key, data in self.cache.items()
            if ' - ' not in key
        ]

        exempt_count = sum(1 for d in unique_jurisdictions if d['is_exempt'])
        requires_10 = sum(1 for d in unique_jurisdictions if d['requires_10_pct'])
        requires_50 = sum(1 for d in unique_jurisdictions if d['requires_50_pct'])

        return {
            'total_jurisdictions': len(unique_jurisdictions),
            'exempt_count': exempt_count,
            'requires_10_pct_count': requires_10,
            'requires_50_pct_count': requires_50,
            'data_file': str(self.data_file),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


# Global service instance
# This is initialized once and reused across the application
rhna_service = RHNADataService()
