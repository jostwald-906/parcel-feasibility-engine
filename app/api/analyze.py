"""
Analysis API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.analysis import AnalysisRequest, AnalysisResponse, DevelopmentScenario  # RentControlData, RentControlUnit - DISABLED
from app.models.parcel import Parcel
from app.rules.base_zoning import analyze_base_zoning
from app.rules.state_law.sb9 import analyze_sb9
from app.rules.state_law.sb35 import analyze_sb35
from app.rules.state_law.ab2011 import analyze_ab2011
from app.rules.state_law.density_bonus import apply_density_bonus
from app.rules.state_law.ab2097 import apply_ab2097_parking_reduction
from app.rules.bergamot_scenarios import is_in_bergamot_area, generate_all_bergamot_scenarios
from app.rules.dcp_scenarios import is_in_dcp_area, generate_all_dcp_scenarios
from app.services.comprehensive_analysis import generate_comprehensive_scenarios
from app.utils.logging import get_logger, DecisionLogger
from app.core.config import settings
from app.services.rent_control_api import get_mar_summary
from app.services.cnel_analyzer import classify_cnel, format_cnel_for_display, check_santa_monica_compliance
from app.services.community_benefits import get_available_benefits, format_benefits_for_display
from app.rules.proposed_validation import validate_proposed_vs_allowed, format_warnings_for_response
from app.services.ami_calculator import get_ami_calculator, AffordableRent, AffordableSalesPrice, AMILookup
from datetime import datetime
import re

router = APIRouter()
logger = get_logger(__name__)


def add_existing_units_context(scenario: DevelopmentScenario, parcel: Parcel) -> None:
    """
    Add notes about existing units and net new units to a scenario.

    This helps clarify the relationship between zoning entitlement capacity
    and what's currently on the parcel (especially for nonconforming sites).
    """
    existing_units = parcel.existing_units
    max_units = scenario.max_units
    net_new_units = max(0, max_units - existing_units)

    # Add existing units note
    if existing_units > 0:
        scenario.notes.insert(0, f"Existing units on parcel: {existing_units}")

    # Add net new units note
    if existing_units > 0:
        if net_new_units > 0:
            scenario.notes.insert(1, f"Net new units under this scenario: {net_new_units}")
        elif net_new_units == 0:
            scenario.notes.insert(1, f"Net new units under this scenario: 0 (existing exceeds or equals zoning capacity)")
        else:
            scenario.notes.insert(1, f"Net new units under this scenario: 0")

    # Add nonconforming warning if existing exceeds capacity
    if existing_units > max_units:
        scenario.notes.insert(2, f"⚠️ Legal nonconforming: Existing {existing_units} units exceed current zoning capacity ({max_units} units). Replacement development would likely reduce unit count unless other programs apply.")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_parcel(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze a parcel for development feasibility.

    This endpoint evaluates a parcel under:
    - Base zoning regulations
    - SB9 lot split and unit provisions (if applicable)
    - SB35 streamlining (if applicable)
    - AB2011 office conversion (if applicable)
    - Density bonus programs
    - AB2097 parking reductions

    Returns all viable development scenarios with recommendations.

    Set debug=True in request to include detailed decision logging.
    """
    try:
        parcel = request.parcel
        scenarios: List[DevelopmentScenario] = []
        applicable_laws: List[str] = []
        potential_incentives: List[str] = []
        warnings: List[str] = []

        # Initialize decision logger if debug mode is enabled
        decision_logger = None
        if request.debug or settings.API_DEBUG_MODE:
            decision_logger = DecisionLogger(parcel.apn, logger)
            logger.info(f"Starting analysis for parcel {parcel.apn} in DEBUG mode")

        # 1. Analyze base zoning
        base_scenario = analyze_base_zoning(parcel)
        applicable_laws.append("Local Zoning Code")
        if decision_logger:
            decision_logger.log_decision(
                rule_name="Base Zoning",
                decision="applied",
                reason=f"Applied base {parcel.zoning_code} zoning standards",
                details={
                    "zoning_code": parcel.zoning_code,
                    "max_units": base_scenario.max_units,
                    "max_height": base_scenario.max_height_ft
                }
            )

        # 2. Check SB9 eligibility
        if request.include_sb9 and settings.ENABLE_SB9:
            sb9_scenarios = analyze_sb9(parcel)
            if sb9_scenarios:
                scenarios.extend(sb9_scenarios)
                applicable_laws.append("SB9 (2021)")
                potential_incentives.append("SB9 lot split and duplex development")
                if decision_logger:
                    decision_logger.log_eligibility_check(
                        rule_name="SB9",
                        eligible=True,
                        reason="Parcel eligible for SB9 provisions",
                        criteria={"scenarios_generated": len(sb9_scenarios)}
                    )
            else:
                # SB9 not eligible - determine reason
                from app.rules.state_law.sb9 import is_sb9_eligible
                zoning = parcel.zoning_code.upper()
                if not ("R1" in zoning or "RS" in zoning or "SINGLE" in zoning):
                    ineligibility_reason = f"SB9 only applies to single-family (R1) zones. This parcel is zoned {parcel.zoning_code}."
                elif parcel.lot_size_sqft < 2000:
                    ineligibility_reason = f"Lot too small for SB9 ({parcel.lot_size_sqft:,} sq ft < 2,000 sq ft minimum)."
                else:
                    ineligibility_reason = "Parcel does not meet SB9 eligibility requirements (check fire hazard, flood, historic, or environmental constraints)."

                warnings.append(f"SB9 Not Applicable: {ineligibility_reason}")
                if decision_logger:
                    decision_logger.log_eligibility_check(
                        rule_name="SB9",
                        eligible=False,
                        reason=ineligibility_reason
                    )

        # 3. Check SB35 eligibility
        if request.include_sb35 and settings.ENABLE_SB35:
            sb35_scenario = analyze_sb35(parcel)
            if sb35_scenario:
                scenarios.append(sb35_scenario)
                applicable_laws.append("SB35 (2017)")
                potential_incentives.append("SB35 streamlined ministerial approval")
                if decision_logger:
                    decision_logger.log_eligibility_check(
                        rule_name="SB35",
                        eligible=True,
                        reason="Parcel eligible for SB35 streamlining"
                    )
            else:
                # SB35 not eligible - get detailed reasons
                from app.rules.state_law.sb35 import can_apply_sb35
                eligibility = can_apply_sb35(parcel)

                if not eligibility['eligible']:
                    # Extract key reasons
                    reason_summary = eligibility['reasons'][0] if eligibility['reasons'] else "Does not meet SB35 requirements"
                    exclusions = eligibility.get('exclusions', [])

                    if exclusions:
                        ineligibility_reason = f"SB35 Not Applicable: {', '.join(exclusions[:2])}"
                    else:
                        ineligibility_reason = f"SB35 Not Applicable: {reason_summary}"

                    warnings.append(ineligibility_reason)
                    if decision_logger:
                        decision_logger.log_eligibility_check(
                            rule_name="SB35",
                            eligible=False,
                            reason=ineligibility_reason,
                            criteria=eligibility
                        )

        # 4. Check AB2011 eligibility (office conversion)
        if request.include_ab2011 and settings.ENABLE_AB2011:
            ab2011_scenario = analyze_ab2011(parcel)
            if ab2011_scenario:
                scenarios.append(ab2011_scenario)
                applicable_laws.append("AB2011 (2022)")
                potential_incentives.append("AB2011 office-to-residential conversion")
                if decision_logger:
                    decision_logger.log_eligibility_check(
                        rule_name="AB2011",
                        eligible=True,
                        reason="Parcel eligible for AB2011 conversion"
                    )
            else:
                # AB2011 not eligible - get detailed reasons
                from app.rules.state_law.ab2011 import can_apply_ab2011
                eligibility = can_apply_ab2011(parcel)

                if not eligibility['eligible']:
                    reason_summary = eligibility['reasons'][0] if eligibility['reasons'] else "Does not meet AB2011 requirements"
                    ineligibility_reason = f"AB2011 Not Applicable: {reason_summary}"
                    warnings.append(ineligibility_reason)
                    if decision_logger:
                        decision_logger.log_eligibility_check(
                            rule_name="AB2011",
                            eligible=False,
                            reason=ineligibility_reason,
                            criteria=eligibility
                        )

        # 4a. Check Bergamot Area Plan
        if is_in_bergamot_area(parcel):
            bergamot_scenarios = generate_all_bergamot_scenarios(parcel)
            if bergamot_scenarios:
                scenarios.extend(bergamot_scenarios)
                applicable_laws.append("Bergamot Area Plan (SMMC Chapter 9.12)")
                potential_incentives.append("Bergamot tiered development standards")
                if decision_logger:
                    decision_logger.log_eligibility_check(
                        rule_name="Bergamot Area Plan",
                        eligible=True,
                        reason=f"Parcel eligible for Bergamot development standards",
                        criteria={"scenarios_generated": len(bergamot_scenarios)}
                    )

        # 4b. Check Downtown Community Plan
        if is_in_dcp_area(parcel):
            dcp_scenarios = generate_all_dcp_scenarios(parcel)
            if dcp_scenarios:
                scenarios.extend(dcp_scenarios)
                applicable_laws.append("Downtown Community Plan (SMMC Chapter 9.10)")
                potential_incentives.append("Downtown tiered development standards with community benefits")
                if decision_logger:
                    decision_logger.log_eligibility_check(
                        rule_name="Downtown Community Plan",
                        eligible=True,
                        reason=f"Parcel eligible for DCP development standards",
                        criteria={"scenarios_generated": len(dcp_scenarios)}
                    )

        # 5. Apply density bonus
        if request.include_density_bonus and request.target_affordability_pct and settings.ENABLE_DENSITY_BONUS:
            density_bonus_scenario = apply_density_bonus(
                base_scenario,
                parcel,
                affordability_pct=request.target_affordability_pct
            )
            if density_bonus_scenario:
                scenarios.append(density_bonus_scenario)
                applicable_laws.append("State Density Bonus Law (Gov Code 65915)")
                potential_incentives.append("Density bonus with concessions")
                if decision_logger:
                    decision_logger.log_decision(
                        rule_name="Density Bonus",
                        decision="applied",
                        reason=f"Applied {request.target_affordability_pct}% affordable housing density bonus",
                        details={
                            "affordability_pct": request.target_affordability_pct,
                            "bonus_units": density_bonus_scenario.max_units - base_scenario.max_units
                        }
                    )

        # 6. Apply AB2097 parking reductions to all scenarios
        if settings.ENABLE_AB2097:
            for scenario in scenarios:
                apply_ab2097_parking_reduction(scenario, parcel)
                if decision_logger:
                    decision_logger.log_decision(
                        rule_name="AB2097",
                        decision="checked",
                        reason=f"AB2097 parking reduction checked for {scenario.scenario_name}"
                    )

            # Apply to base scenario as well
            apply_ab2097_parking_reduction(base_scenario, parcel)

        # 7. Add existing units context to all scenarios
        add_existing_units_context(base_scenario, parcel)
        for scenario in scenarios:
            add_existing_units_context(scenario, parcel)

        # 8. Analyze CNEL (noise) exposure if data available
        cnel_analysis = None
        if hasattr(parcel, 'cnel_db') and parcel.cnel_db:
            try:
                cnel_result = classify_cnel(parcel.cnel_db)
                cnel_compliance = check_santa_monica_compliance(cnel_result)
                cnel_analysis = {
                    **format_cnel_for_display(cnel_result),
                    "santa_monica_compliance": cnel_compliance
                }

                # Add warning if noise level is problematic
                if not cnel_result.residential_suitable:
                    warnings.append(f"Noise Level Concern: {cnel_result.cnel_db} dB CNEL - {cnel_result.category.value.replace('_', ' ').title()}")

                if decision_logger:
                    decision_logger.log_decision(
                        rule_name="CNEL Analysis",
                        decision="analyzed",
                        reason=f"Noise level: {cnel_result.cnel_db} dB CNEL - {cnel_result.category.value}",
                        details={"residential_suitable": cnel_result.residential_suitable}
                    )
            except Exception as e:
                logger.warning(f"CNEL analysis failed: {str(e)}")

        # 9. Analyze community benefits opportunities if parcel has tier/overlay data
        benefits_analysis = None
        if hasattr(parcel, 'development_tier') and parcel.development_tier:
            try:
                # Extract tier number from string (e.g., "Tier 2" -> 2)
                tier_match = re.search(r'\d+', str(parcel.development_tier))
                base_tier = int(tier_match.group()) if tier_match else 1

                # Check if in downtown (based on zoning or overlay codes)
                in_downtown = False
                if hasattr(parcel, 'overlay_codes') and parcel.overlay_codes:
                    in_downtown = any('DCP' in code or 'DOWNTOWN' in code.upper() for code in parcel.overlay_codes)

                # Check if near transit
                near_transit = getattr(parcel, 'near_transit', False)

                benefits_result = get_available_benefits(
                    lot_size_sqft=parcel.lot_size_sqft,
                    base_tier=base_tier,
                    near_transit=near_transit,
                    in_downtown=in_downtown
                )
                benefits_analysis = format_benefits_for_display(benefits_result)

                # Add incentive notes
                if base_tier < 3:
                    potential_incentives.append(f"Community benefits can unlock Tier {base_tier + 1} development standards")

                if decision_logger:
                    decision_logger.log_decision(
                        rule_name="Community Benefits",
                        decision="analyzed",
                        reason=f"Identified {len(benefits_result.available_benefits)} available community benefits",
                        details={"base_tier": base_tier, "recommended": benefits_result.recommended_benefits}
                    )
            except Exception as e:
                logger.warning(f"Community benefits analysis failed: {str(e)}")

        # Determine recommended scenario
        recommended_scenario = base_scenario
        max_units = base_scenario.max_units

        for scenario in scenarios:
            if scenario.max_units > max_units:
                max_units = scenario.max_units
                recommended_scenario = scenario

        # Add warnings
        if parcel.lot_size_sqft < 5000:
            warnings.append("Small lot size may limit development options")

        if parcel.existing_units > 0:
            warnings.append(f"Existing {parcel.existing_units} unit(s) may need to be demolished or incorporated")

        # 8. Query rent control data if address is available
        rent_control_data = None

        # Check for manual override first
        if hasattr(parcel, 'rent_control_status') and parcel.rent_control_status:
            status_lower = parcel.rent_control_status.lower()
            if status_lower == 'yes':
                rent_control_data = {
                    'is_rent_controlled': True,
                    'total_units': 0,
                    'avg_mar': None,
                    'units': [],
                    'status': 'manual_override',
                    'error_message': None
                }
                warnings.append("Rent control status: MANUAL OVERRIDE - Property marked as rent-controlled. Verify with Santa Monica Rent Control Board.")
            elif status_lower == 'no':
                rent_control_data = {
                    'is_rent_controlled': False,
                    'total_units': 0,
                    'avg_mar': None,
                    'units': [],
                    'status': 'manual_override',
                    'error_message': None
                }
            elif status_lower == 'unknown':
                rent_control_data = {
                    'is_rent_controlled': None,
                    'total_units': 0,
                    'avg_mar': None,
                    'units': [],
                    'status': 'manual_override_unknown',
                    'error_message': None
                }
                warnings.append("Rent control status: UNKNOWN - Manual verification required with Santa Monica Rent Control Board.")

        # If no manual override, attempt API lookup
        if rent_control_data is None and parcel.address:
            try:
                # Parse address to extract street number and street name
                import re
                address_match = re.match(r'^(\d+)\s+(.+)$', parcel.address.strip())

                if address_match:
                    street_number = address_match.group(1)
                    street_name = address_match.group(2)

                    logger.info(f"Attempting rent control lookup for {street_number} {street_name}")

                    # Call with increased timeout and caching enabled
                    rent_control_data = get_mar_summary(street_number, street_name, use_cache=True)

                    if rent_control_data:
                        status = rent_control_data.get('status', 'unknown')

                        if status == 'success':
                            if rent_control_data['is_rent_controlled']:
                                warnings.append(
                                    f"Rent Control: Property has {rent_control_data['total_units']} "
                                    f"rent-controlled unit(s). May affect AB2011 and SB35 eligibility."
                                )
                        elif status == 'error':
                            error_msg = rent_control_data.get('error_message', 'Unknown error')
                            logger.warning(f"Rent control lookup failed: {error_msg}")
                            warnings.append(
                                "Rent Control: Lookup failed. Status unknown - manual verification required "
                                "with Santa Monica Rent Control Board (https://www.smgov.net/rentcontrol)."
                            )
                        elif status == 'not_found':
                            # Property not in rent control database
                            logger.info(f"Property {parcel.address} not found in rent control database")
                    else:
                        logger.warning("Rent control lookup returned None")
                        warnings.append(
                            "Rent Control: Unable to determine status - manual verification required."
                        )
                else:
                    logger.warning(f"Could not parse address format: {parcel.address}")
                    warnings.append(
                        "Rent Control: Could not parse address for lookup - manual verification required."
                    )

            except Exception as e:
                logger.error(f"Rent control lookup error: {str(e)}", exc_info=True)
                warnings.append(
                    f"Rent Control: Lookup error - {str(e)[:100]}. Manual verification required."
                )

        # Build debug information if enabled
        debug_info = None
        if decision_logger:
            debug_info = {
                "decisions": decision_logger.get_decisions(),
                "decision_summary": decision_logger.get_decision_summary(),
                "feature_flags": {
                    "ab2011": settings.ENABLE_AB2011,
                    "sb35": settings.ENABLE_SB35,
                    "density_bonus": settings.ENABLE_DENSITY_BONUS,
                    "sb9": settings.ENABLE_SB9,
                    "ab2097": settings.ENABLE_AB2097,
                },
                "parcel_info": {
                    "apn": parcel.apn,
                    "zoning_code": parcel.zoning_code,
                    "lot_size_sqft": parcel.lot_size_sqft,
                }
            }
            logger.info(f"Analysis completed for parcel {parcel.apn} with {len(scenarios)} alternative scenarios")

        # Ensure rent_control_data has valid boolean for is_rent_controlled
        if rent_control_data and rent_control_data.get('is_rent_controlled') is None:
            rent_control_data['is_rent_controlled'] = False

        # Validate proposed project against recommended scenario (if provided)
        proposed_validation = None
        if request.proposed_project:
            validation_warnings = validate_proposed_vs_allowed(
                request.proposed_project,
                recommended_scenario,
                parcel.lot_size_sqft
            )
            proposed_validation = format_warnings_for_response(validation_warnings)

        # Build response
        response = AnalysisResponse(
            parcel_apn=parcel.apn,
            analysis_date=datetime.now(),
            base_scenario=base_scenario,
            alternative_scenarios=scenarios,
            recommended_scenario=recommended_scenario.scenario_name,
            recommendation_reason=f"Maximizes unit count with {recommended_scenario.max_units} units under {recommended_scenario.legal_basis}",
            applicable_laws=applicable_laws,
            potential_incentives=potential_incentives,
            warnings=warnings,
            rent_control=rent_control_data,
            cnel_analysis=cnel_analysis,
            community_benefits=benefits_analysis,
            proposed_validation=proposed_validation,
            debug=debug_info
        )

        return response

    except Exception as e:
        logger.error(f"Analysis failed for parcel: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/quick-analysis")
async def quick_analysis(request: AnalysisRequest) -> dict:
    """
    Quick analysis returning only key metrics.

    Faster endpoint that returns essential information without full scenario details.
    """
    try:
        full_analysis = await analyze_parcel(request)

        return {
            "parcel_apn": full_analysis.parcel_apn,
            "max_units_base": full_analysis.base_scenario.max_units,
            "max_units_optimized": max(
                [s.max_units for s in full_analysis.alternative_scenarios] +
                [full_analysis.base_scenario.max_units]
            ),
            "recommended_scenario": full_analysis.recommended_scenario,
            "applicable_laws": full_analysis.applicable_laws,
            "key_opportunities": full_analysis.potential_incentives[:3]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick analysis failed: {str(e)}")


@router.post("/comprehensive-analysis")
async def comprehensive_analysis(request: AnalysisRequest) -> dict:
    """
    Comprehensive analysis integrating all special plan areas and state law programs.

    This endpoint intelligently combines:
    - Base zoning OR Bergamot OR Downtown Community Plan (whichever applies)
    - State law programs (SB35, AB2011) with interaction warnings
    - Density bonus scenarios for all applicable base scenarios
    - Program interaction analysis and warnings

    Returns a simplified response focused on viable development paths,
    with clear guidance on how different programs interact.
    """
    try:
        parcel = request.parcel

        # Use comprehensive analysis service
        result = generate_comprehensive_scenarios(
            parcel,
            include_sb35=request.include_sb35 if hasattr(request, 'include_sb35') else True,
            include_ab2011=request.include_ab2011 if hasattr(request, 'include_ab2011') else True,
            include_density_bonus=request.include_density_bonus if hasattr(request, 'include_density_bonus') else True,
            target_affordability_pct=request.target_affordability_pct if hasattr(request, 'target_affordability_pct') else 15.0
        )

        # Apply AB2097 parking reductions to all scenarios
        if settings.ENABLE_AB2097:
            for scenario in result['scenarios']:
                apply_ab2097_parking_reduction(scenario, parcel)

        # Add existing units context
        for scenario in result['scenarios']:
            add_existing_units_context(scenario, parcel)

        # Find recommended scenario (highest unit count)
        recommended_scenario = None
        max_units = 0
        for scenario in result['scenarios']:
            if scenario.max_units > max_units:
                max_units = scenario.max_units
                recommended_scenario = scenario

        # Build response
        return {
            "parcel_apn": parcel.apn,
            "analysis_date": datetime.now(),
            "analysis_type": result['analysis_type'],
            "in_special_plan_area": result['in_bergamot'] or result['in_dcp'],
            "special_plan": {
                "bergamot": result['in_bergamot'],
                "downtown_community_plan": result['in_dcp']
            },
            "scenarios": [
                {
                    "name": s.scenario_name,
                    "legal_basis": s.legal_basis,
                    "max_units": s.max_units,
                    "max_building_sqft": s.max_building_sqft,
                    "max_height_ft": s.max_height_ft,
                    "max_stories": s.max_stories,
                    "parking_required": s.parking_spaces_required,
                    "affordable_units_required": s.affordable_units_required,
                    "notes": s.notes
                }
                for s in result['scenarios']
            ],
            "recommended_scenario": recommended_scenario.scenario_name if recommended_scenario else None,
            "applicable_programs": result['applicable_programs'],
            "warnings": result['warnings'],
            "program_interactions": {
                "has_density_bonus_variants": any('Density Bonus' in s.scenario_name for s in result['scenarios']),
                "state_law_may_preempt": any('SB35' in s.scenario_name for s in result['scenarios']) and (result['in_bergamot'] or result['in_dcp']),
                "can_stack_programs": result['in_dcp'] or result['in_bergamot']
            }
        }

    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comprehensive analysis failed: {str(e)}")


@router.get("/ami/rent", response_model=AffordableRent)
def get_affordable_rent(
    county: str,
    ami_pct: float,
    bedrooms: int,
    utility_allowance: float = 150.0
) -> AffordableRent:
    """
    Get maximum affordable rent for given parameters.

    Calculates affordable rent using the 30% of income standard.

    Args:
        county: County name (e.g., "Los Angeles")
        ami_pct: AMI percentage (e.g., 50.0 for 50% AMI)
        bedrooms: Number of bedrooms (0-4+)
        utility_allowance: Monthly utility allowance (default: $150)

    Returns:
        AffordableRent model with rent calculations

    Examples:
        GET /api/v1/ami/rent?county=Los Angeles&ami_pct=50&bedrooms=2
        {
            "county": "Los Angeles",
            "ami_pct": 50.0,
            "bedrooms": 2,
            "household_size": 3,
            "income_limit": 47970.0,
            "max_rent_with_utilities": 1199.25,
            "max_rent_no_utilities": 1049.25,
            "utility_allowance": 150.0
        }
    """
    try:
        calculator = get_ami_calculator()
        return calculator.calculate_max_rent(county, ami_pct, bedrooms, utility_allowance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Affordable rent calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get("/ami/sales-price", response_model=AffordableSalesPrice)
def get_affordable_sales_price(
    county: str,
    ami_pct: float,
    household_size: int,
    interest_rate_pct: float = 6.5,
    loan_term_years: int = 30,
    down_payment_pct: float = 10.0,
    property_tax_rate_pct: float = 1.25,
    insurance_rate_pct: float = 0.5,
    hoa_monthly: float = 0.0
) -> AffordableSalesPrice:
    """
    Get maximum affordable sales price.

    Calculates affordable home price using 30% of income for PITI + HOA.

    Args:
        county: County name
        ami_pct: AMI percentage
        household_size: Household size (1-8 persons)
        interest_rate_pct: Annual interest rate (default: 6.5%)
        loan_term_years: Loan term in years (default: 30)
        down_payment_pct: Down payment percentage (default: 10%)
        property_tax_rate_pct: Annual property tax rate (default: 1.25%)
        insurance_rate_pct: Annual insurance rate (default: 0.5%)
        hoa_monthly: Monthly HOA fees (default: $0)

    Returns:
        AffordableSalesPrice model with price and assumptions

    Examples:
        GET /api/v1/ami/sales-price?county=Los Angeles&ami_pct=80&household_size=4
        {
            "county": "Los Angeles",
            "ami_pct": 80.0,
            "household_size": 4,
            "income_limit": 85280.0,
            "max_sales_price": 425000.0,
            "assumptions": {
                "interest_rate_pct": 6.5,
                "loan_term_years": 30,
                "down_payment_pct": 10.0,
                "property_tax_rate_pct": 1.25,
                "insurance_rate_pct": 0.5,
                "hoa_monthly": 0.0
            }
        }
    """
    try:
        calculator = get_ami_calculator()
        return calculator.calculate_max_sales_price(
            county=county,
            ami_pct=ami_pct,
            household_size=household_size,
            interest_rate_pct=interest_rate_pct,
            loan_term_years=loan_term_years,
            down_payment_pct=down_payment_pct,
            property_tax_rate_pct=property_tax_rate_pct,
            insurance_rate_pct=insurance_rate_pct,
            hoa_monthly=hoa_monthly
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Affordable sales price calculation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get("/ami/income-limit", response_model=AMILookup)
def get_income_limit(
    county: str,
    ami_pct: float,
    household_size: int
) -> AMILookup:
    """
    Get income limit for given county, AMI percentage, and household size.

    Data source: HCD 2025 State Income Limits (Effective April 23, 2025)

    Args:
        county: County name (e.g., "Los Angeles")
        ami_pct: AMI percentage (e.g., 50.0 for 50% AMI, 80.0 for 80% AMI)
        household_size: Household size (1-8 persons)

    Returns:
        AMILookup model with income limit data

    Examples:
        GET /api/v1/ami/income-limit?county=Los Angeles&ami_pct=50&household_size=2
        {
            "county": "Los Angeles",
            "ami_pct": 50.0,
            "household_size": 2,
            "income_limit": 42640.0
        }
    """
    try:
        calculator = get_ami_calculator()
        return calculator.get_ami_lookup(county, ami_pct, household_size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Income limit lookup failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")


@router.get("/ami/counties")
def get_available_counties() -> dict:
    """
    Get list of available counties in the AMI dataset.

    Returns:
        Dictionary with list of county names

    Examples:
        GET /api/v1/ami/counties
        {
            "counties": ["Alameda", "Fresno", "Kern", "Los Angeles", ...]
        }
    """
    try:
        calculator = get_ami_calculator()
        return {"counties": calculator.get_available_counties()}
    except Exception as e:
        logger.error(f"Failed to get counties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get counties: {str(e)}")


@router.get("/ami/percentages")
def get_available_ami_percentages() -> dict:
    """
    Get list of available AMI percentages.

    Returns:
        Dictionary with list of AMI percentages and their descriptions

    Examples:
        GET /api/v1/ami/percentages
        {
            "ami_percentages": [
                {"value": 30, "label": "30% AMI (Extremely Low Income)"},
                {"value": 50, "label": "50% AMI (Very Low Income)"},
                ...
            ]
        }
    """
    try:
        calculator = get_ami_calculator()
        percentages = calculator.get_available_ami_percentages()

        # Add labels for common AMI categories
        labels = {
            30: "Extremely Low Income",
            50: "Very Low Income",
            60: "Low Income",
            80: "Low Income",
            100: "Median Income",
            120: "Moderate Income"
        }

        return {
            "ami_percentages": [
                {
                    "value": pct,
                    "label": f"{int(pct)}% AMI ({labels.get(pct, 'Income Category')})"
                }
                for pct in percentages
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get AMI percentages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get AMI percentages: {str(e)}")
