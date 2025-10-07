"""
Comprehensive Parcel Analysis Service

Integrates base zoning, special plan areas (Bergamot, Downtown Community Plan),
and state law incentives (AB 2011, SB 35, Density Bonus) to provide a complete
picture of development potential with all applicable interactions.

This service handles complex scenarios like:
- DCP Tier 2 + State Density Bonus
- Bergamot BTV + AB 2011 conversion
- State law preemption vs. local overlay standards
"""

from typing import List, Dict, Optional, Tuple
from app.models.analysis import DevelopmentScenario
from app.models.parcel import ParcelBase
from app.rules.base_zoning import analyze_base_zoning
from app.rules.dcp_scenarios import is_in_dcp_area, get_dcp_district, generate_all_dcp_scenarios
from app.rules.bergamot_scenarios import is_in_bergamot_area, generate_all_bergamot_scenarios
from app.rules.state_law.sb35 import analyze_sb35, can_apply_sb35
from app.rules.state_law.ab2011 import analyze_ab2011, can_apply_ab2011
from app.rules.state_law.density_bonus import apply_density_bonus
from app.rules.state_law.adu import analyze_adu
from app.services.timeline_estimator import estimate_timeline
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ComprehensiveAnalysis:
    """
    Comprehensive analysis engine that generates all viable development scenarios
    including interactions between local and state regulations.
    """

    def __init__(self, parcel: ParcelBase):
        self.parcel = parcel
        self.scenarios: List[DevelopmentScenario] = []
        self.applicable_programs: List[str] = []
        self.warnings: List[str] = []

    def analyze(
        self,
        include_sb35: bool = True,
        include_ab2011: bool = True,
        include_density_bonus: bool = True,
        include_adu: bool = True,
        target_affordability_pct: Optional[float] = None,
        include_timeline: bool = True
    ) -> Dict:
        """
        Run comprehensive analysis combining all applicable programs.

        Returns:
            Dict with scenarios, programs, warnings, and analysis metadata
        """
        # 1. Determine which special plan area applies (if any)
        in_bergamot = is_in_bergamot_area(self.parcel)
        in_dcp = is_in_dcp_area(self.parcel)

        # 2. Generate base scenarios
        if in_bergamot:
            self._analyze_bergamot()
        elif in_dcp:
            self._analyze_dcp()
        else:
            self._analyze_base_zoning()

        # 3. Apply state law programs
        if include_sb35:
            self._analyze_sb35()

        if include_ab2011:
            self._analyze_ab2011()

        if include_adu:
            self._analyze_adu()

        # 4. Generate density bonus variants for applicable scenarios
        if include_density_bonus and target_affordability_pct:
            self._apply_density_bonus_to_scenarios(target_affordability_pct)

        # 5. Analyze interactions and add warnings
        self._analyze_interactions()

        # 6. Add timeline estimates to all scenarios
        if include_timeline:
            self._add_timeline_estimates()

        return {
            "scenarios": self.scenarios,
            "applicable_programs": self.applicable_programs,
            "warnings": self.warnings,
            "analysis_type": self._get_analysis_type(),
            "in_bergamot": in_bergamot,
            "in_dcp": in_dcp,
        }

    def _analyze_base_zoning(self):
        """Generate base zoning scenario for parcels outside special plan areas."""
        base_scenario = analyze_base_zoning(self.parcel)
        if base_scenario:
            self.scenarios.append(base_scenario)
            self.applicable_programs.append("Local Zoning Code")

    def _analyze_bergamot(self):
        """Generate Bergamot Area Plan scenarios."""
        bergamot_scenarios = generate_all_bergamot_scenarios(self.parcel)
        if bergamot_scenarios:
            self.scenarios.extend(bergamot_scenarios)
            self.applicable_programs.append("Bergamot Area Plan (SMMC Chapter 9.12)")
            logger.info(f"Generated {len(bergamot_scenarios)} Bergamot scenarios for {self.parcel.apn}")

    def _analyze_dcp(self):
        """Generate Downtown Community Plan scenarios."""
        dcp_scenarios = generate_all_dcp_scenarios(self.parcel)
        if dcp_scenarios:
            self.scenarios.extend(dcp_scenarios)
            district = get_dcp_district(self.parcel)
            self.applicable_programs.append(f"Downtown Community Plan - {district} District (SMMC Chapter 9.10)")
            logger.info(f"Generated {len(dcp_scenarios)} DCP scenarios for {self.parcel.apn}")

    def _analyze_sb35(self):
        """Check SB35 eligibility and generate scenario if applicable."""
        eligibility = can_apply_sb35(self.parcel)

        if eligibility['eligible']:
            sb35_scenario = analyze_sb35(self.parcel)
            if sb35_scenario:
                self.scenarios.append(sb35_scenario)
                self.applicable_programs.append("SB35 Streamlined Ministerial Approval (Gov Code § 65913.4)")
                logger.info(f"SB35 applicable for {self.parcel.apn}")
        else:
            # Log first exclusion reason
            if eligibility.get('exclusions'):
                self.warnings.append(f"SB35 not applicable: {eligibility['exclusions'][0]}")

    def _analyze_ab2011(self):
        """Check AB 2011 eligibility and generate scenario if applicable."""
        eligibility = can_apply_ab2011(self.parcel)

        if eligibility['eligible']:
            ab2011_scenario = analyze_ab2011(self.parcel)
            if ab2011_scenario:
                self.scenarios.append(ab2011_scenario)
                self.applicable_programs.append("AB 2011 Office-to-Residential Conversion (Gov Code § 65912.100)")
                logger.info(f"AB 2011 applicable for {self.parcel.apn}")
        else:
            # Only warn if parcel is in commercial/office zone (where AB2011 might be relevant)
            if 'commercial' in self.parcel.zoning_code.lower() or 'office' in self.parcel.zoning_code.lower():
                if eligibility.get('reasons'):
                    self.warnings.append(f"AB 2011 not applicable: {eligibility['reasons'][0]}")

    def _analyze_adu(self):
        """
        Generate ADU/JADU scenarios (Gov Code § 65852.2 & § 65852.22).

        ADUs are allowed on ALL residential parcels per state law.
        State law preempts local restrictions.
        """
        adu_scenarios = analyze_adu(self.parcel)

        if adu_scenarios:
            self.scenarios.extend(adu_scenarios)
            self.applicable_programs.append("ADU/JADU - Accessory Dwelling Units (Gov Code § 65852.2 & § 65852.22)")
            logger.info(f"Generated {len(adu_scenarios)} ADU/JADU scenarios for {self.parcel.apn}")

    def _apply_density_bonus_to_scenarios(self, affordability_pct: float):
        """
        Apply density bonus to base, Bergamot, and DCP scenarios.

        Creates new scenarios showing how density bonus can enhance local entitlements.
        State Density Bonus Law (Gov Code § 65915) can stack with local programs.
        """
        scenarios_to_enhance = []

        for scenario in self.scenarios:
            # Apply density bonus to base zoning, Bergamot, and DCP scenarios
            # Skip if already a density bonus variant or state law scenario
            if 'Density Bonus' not in scenario.scenario_name and \
               'SB35' not in scenario.scenario_name and \
               'AB2011' not in scenario.scenario_name:
                scenarios_to_enhance.append(scenario)

        for base_scenario in scenarios_to_enhance:
            db_scenario = apply_density_bonus(
                base_scenario,
                self.parcel,
                affordability_pct=affordability_pct
            )
            if db_scenario:
                # Enhance scenario name to show base + density bonus
                original_name = base_scenario.scenario_name
                db_scenario.scenario_name = f"{original_name} + Density Bonus"
                db_scenario.notes.insert(0, f"Stacks with {original_name} entitlements")
                self.scenarios.append(db_scenario)

        if scenarios_to_enhance:
            self.applicable_programs.append("State Density Bonus Law (Gov Code § 65915)")

    def _analyze_interactions(self):
        """
        Analyze interactions between programs and add relevant warnings/notes.

        Handles cases like:
        - State law preemption of local standards
        - Combining DCP tiers with density bonus
        - Bergamot + AB 2011 conflicts
        """
        in_bergamot = is_in_bergamot_area(self.parcel)
        in_dcp = is_in_dcp_area(self.parcel)

        # Check for state law preemption scenarios
        has_sb35 = any('SB35' in s.scenario_name for s in self.scenarios)
        has_ab2011 = any('AB2011' in s.scenario_name for s in self.scenarios)

        if has_sb35 and (in_bergamot or in_dcp):
            self.warnings.append(
                "⚠️ SB35 may preempt some local development standards. "
                "Consult with planning staff regarding community benefits requirements."
            )

        if has_ab2011 and in_bergamot:
            self.warnings.append(
                "⚠️ AB 2011 conversion in Bergamot Area: Confirm creative/arts use requirements "
                "can be satisfied with residential conversion."
            )

        # Check for density bonus + DCP tier interaction
        has_density_bonus = any('Density Bonus' in s.scenario_name for s in self.scenarios)
        if has_density_bonus and in_dcp:
            # Add helpful note about combining programs
            for scenario in self.scenarios:
                if 'DCP Tier' in scenario.scenario_name and 'Density Bonus' in scenario.scenario_name:
                    scenario.notes.append(
                        "💡 Combining DCP tier standards with State Density Bonus can maximize development potential"
                    )
                    scenario.notes.append(
                        "Consider: DCP Tier 2/3 community benefits + density bonus affordable units = dual public benefit"
                    )

        # Check for coastal zone + height restrictions
        if hasattr(self.parcel, 'coastal') and getattr(self.parcel.coastal, 'in_coastal_zone', False):
            max_height = max((s.max_height_ft for s in self.scenarios), default=0)
            if max_height > 50:
                self.warnings.append(
                    "⚠️ Coastal Zone: Heights over 50 ft may require Coastal Development Permit and "
                    "view impact analysis. State law density bonus may not override coastal height limits."
                )

    def _add_timeline_estimates(self):
        """Add timeline estimates to all scenarios."""
        for scenario in self.scenarios:
            try:
                timeline = estimate_timeline(
                    scenario_name=scenario.scenario_name,
                    legal_basis=scenario.legal_basis,
                    max_units=scenario.max_units,
                    parcel=self.parcel
                )
                # Convert to dict for JSON serialization
                scenario.estimated_timeline = timeline.model_dump()
                logger.info(
                    f"Added timeline estimate for {scenario.scenario_name}: "
                    f"{timeline.total_days_min}-{timeline.total_days_max} days ({timeline.pathway_type})"
                )
            except Exception as e:
                logger.error(f"Failed to estimate timeline for {scenario.scenario_name}: {e}")
                # Continue without timeline for this scenario
                pass

    def _get_analysis_type(self) -> str:
        """Return a description of the analysis type performed."""
        if is_in_bergamot_area(self.parcel):
            return "Bergamot Area Plan Analysis"
        elif is_in_dcp_area(self.parcel):
            district = get_dcp_district(self.parcel)
            return f"Downtown Community Plan Analysis ({district} District)"
        else:
            return "Base Zoning Analysis"


def generate_comprehensive_scenarios(
    parcel: ParcelBase,
    include_sb35: bool = True,
    include_ab2011: bool = True,
    include_density_bonus: bool = True,
    include_adu: bool = True,
    target_affordability_pct: Optional[float] = 15.0,
    include_timeline: bool = True
) -> Dict:
    """
    Convenience function to generate comprehensive development scenarios.

    Args:
        parcel: Parcel to analyze
        include_sb35: Include SB35 streamlining if applicable
        include_ab2011: Include AB2011 office conversion if applicable
        include_density_bonus: Generate density bonus scenarios
        include_adu: Include ADU/JADU scenarios (default True)
        target_affordability_pct: Affordability % for density bonus (default 15%)
        include_timeline: Include timeline estimates for each scenario (default True)

    Returns:
        Dict with scenarios, programs, warnings, and analysis metadata
    """
    analyzer = ComprehensiveAnalysis(parcel)
    return analyzer.analyze(
        include_sb35=include_sb35,
        include_ab2011=include_ab2011,
        include_density_bonus=include_density_bonus,
        include_adu=include_adu,
        target_affordability_pct=target_affordability_pct,
        include_timeline=include_timeline
    )
