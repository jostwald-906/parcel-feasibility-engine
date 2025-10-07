"""
Entitlement Timeline Estimator

Estimates approval timelines based on pathway type and statutory requirements.

Ministerial Timelines (State Law Mandates):
- SB 9: 60 days (Gov. Code § 65852.21(k))
- SB 35: 90 days if complete (Gov. Code § 65913.4(b))
- ADU: 60 days (Gov. Code § 65852.2(a)(3))

Discretionary Timelines (Santa Monica Practice):
- CUP: 6-9 months (hearings + CEQA)
- DRP: 3-6 months (Design Review Process)
- Variance: 4-8 months

References:
- Gov. Code § 65852.21(k): SB 9 60-day approval deadline
- Gov. Code § 65913.4(b): SB 35 streamlined review timeline
- Gov. Code § 65852.2(a)(3): ADU 60-day approval deadline
- Santa Monica Municipal Code Chapter 9.04: Administrative procedures
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.parcel import ParcelBase


class TimelineStep(BaseModel):
    """Timeline step with estimated duration."""

    step_name: str = Field(..., description="Name of the step")
    days_min: int = Field(..., ge=0, description="Minimum days for this step")
    days_max: int = Field(..., ge=0, description="Maximum days for this step")
    description: str = Field(..., description="Description of what happens in this step")
    required_submittals: List[str] = Field(
        default_factory=list, description="Required documents/submittals for this step"
    )


class EntitlementTimeline(BaseModel):
    """Complete entitlement timeline estimate."""

    pathway_type: str = Field(
        ..., description="Ministerial, Administrative, or Discretionary"
    )
    total_days_min: int = Field(..., ge=0, description="Minimum total days")
    total_days_max: int = Field(..., ge=0, description="Maximum total days")
    steps: List[TimelineStep] = Field(..., description="Timeline steps in order")
    statutory_deadline: Optional[int] = Field(
        None, description="Statutory deadline in days (if applicable)"
    )
    notes: List[str] = Field(default_factory=list, description="Important notes")


def detect_pathway_type(legal_basis: str) -> str:
    """
    Detect approval pathway type from legal basis.

    Args:
        legal_basis: Legal basis string from scenario

    Returns:
        "Ministerial", "Administrative", or "Discretionary"
    """
    legal_basis_lower = legal_basis.lower()

    # Ministerial pathways (state-mandated by-right approval)
    ministerial_keywords = [
        "sb 9",
        "sb9",
        "sb 35",
        "sb35",
        "ab 2011",
        "ab2011",
        "adu",
        "jadu",
        "ministerial",
        "by-right",
        "by right",
    ]

    if any(keyword in legal_basis_lower for keyword in ministerial_keywords):
        return "Ministerial"

    # Administrative pathways (staff-level approval)
    administrative_keywords = [
        "administrative",
        "arp",
        "director approval",
        "staff approval",
    ]

    if any(keyword in legal_basis_lower for keyword in administrative_keywords):
        return "Administrative"

    # Default to discretionary (requires public hearing)
    return "Discretionary"


def estimate_timeline(
    scenario_name: str, legal_basis: str, max_units: int, parcel: Optional[ParcelBase] = None
) -> EntitlementTimeline:
    """
    Estimate entitlement timeline for development scenario.

    Args:
        scenario_name: Name of the scenario
        legal_basis: Legal basis for the scenario
        max_units: Maximum units in the scenario
        parcel: Optional parcel data for additional context

    Returns:
        EntitlementTimeline with estimated steps and duration
    """
    pathway_type = detect_pathway_type(legal_basis)
    legal_basis_lower = legal_basis.lower()

    # SB 9 Timeline
    if "sb 9" in legal_basis_lower or "sb9" in legal_basis_lower:
        return _sb9_timeline()

    # SB 35 Timeline
    if "sb 35" in legal_basis_lower or "sb35" in legal_basis_lower:
        return _sb35_timeline()

    # AB 2011 Timeline
    if "ab 2011" in legal_basis_lower or "ab2011" in legal_basis_lower:
        return _ab2011_timeline()

    # ADU/JADU Timeline
    if "adu" in legal_basis_lower or "jadu" in legal_basis_lower:
        return _adu_timeline()

    # Ministerial Timeline (general)
    if pathway_type == "Ministerial":
        return _ministerial_timeline()

    # Administrative Timeline
    if pathway_type == "Administrative":
        return _administrative_timeline(max_units)

    # Discretionary Timeline (default)
    return _discretionary_timeline(max_units)


def _sb9_timeline() -> EntitlementTimeline:
    """SB 9 ministerial timeline (60 days)."""
    steps = [
        TimelineStep(
            step_name="Application Submittal",
            days_min=1,
            days_max=1,
            description="Submit complete SB 9 application package",
            required_submittals=[
                "SB 9 application form",
                "Site plan",
                "Floor plans",
                "Elevations",
                "Utility plan",
                "Landscape plan",
            ],
        ),
        TimelineStep(
            step_name="Completeness Check",
            days_min=7,
            days_max=14,
            description="City reviews application for completeness",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Ministerial Review",
            days_min=21,
            days_max=35,
            description="Staff reviews for objective standards compliance",
            required_submittals=[
                "Any requested corrections or clarifications"
            ],
        ),
        TimelineStep(
            step_name="Approval & Permit Issuance",
            days_min=7,
            days_max=10,
            description="Final approval and building permit issuance",
            required_submittals=[],
        ),
    ]

    total_min = sum(s.days_min for s in steps)
    total_max = sum(s.days_max for s in steps)

    return EntitlementTimeline(
        pathway_type="Ministerial",
        total_days_min=total_min,
        total_days_max=total_max,
        steps=steps,
        statutory_deadline=60,
        notes=[
            "SB 9 requires ministerial approval within 60 days (Gov. Code § 65852.21(k))",
            "No public hearing or CEQA review required",
            "Must meet all objective design standards",
            "Timeline may be extended if application is incomplete",
        ],
    )


def _sb35_timeline() -> EntitlementTimeline:
    """SB 35 streamlined ministerial timeline (90 days)."""
    steps = [
        TimelineStep(
            step_name="Application Submittal",
            days_min=1,
            days_max=1,
            description="Submit complete SB 35 application package (optional pre-app consultation recommended)",
            required_submittals=[
                "SB 35 application form",
                "Site plan",
                "Architectural plans",
                "Affordability covenant",
                "Skilled & trained workforce certification",
                "Prevailing wage commitment",
            ],
        ),
        TimelineStep(
            step_name="Completeness Determination",
            days_min=14,
            days_max=21,
            description="City reviews application for completeness",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Streamlined Review",
            days_min=30,
            days_max=45,
            description="Staff reviews for objective standards and affordability compliance",
            required_submittals=["Response to any staff comments"],
        ),
        TimelineStep(
            step_name="Final Approval",
            days_min=7,
            days_max=14,
            description="Ministerial approval and permit issuance",
            required_submittals=[],
        ),
    ]

    total_min = sum(s.days_min for s in steps)
    total_max = sum(s.days_max for s in steps)

    return EntitlementTimeline(
        pathway_type="Ministerial",
        total_days_min=total_min,
        total_days_max=total_max,
        steps=steps,
        statutory_deadline=90,
        notes=[
            "SB 35 requires approval within 90 days for complete applications (Gov. Code § 65913.4(b))",
            "Ministerial approval - no discretionary review or public hearing",
            "CEQA-exempt for qualifying projects",
            "Must meet objective zoning and design standards",
            "Requires minimum 10% affordable units",
            "Optional pre-application consultation not included in statutory timeline",
        ],
    )


def _ab2011_timeline() -> EntitlementTimeline:
    """AB 2011 office-to-residential conversion timeline."""
    steps = [
        TimelineStep(
            step_name="Pre-Application Meeting",
            days_min=14,
            days_max=30,
            description="Meet with planning staff to discuss conversion feasibility",
            required_submittals=["Existing building plans", "Conversion concept"],
        ),
        TimelineStep(
            step_name="Application Submittal",
            days_min=1,
            days_max=1,
            description="Submit complete AB 2011 application",
            required_submittals=[
                "AB 2011 application form",
                "Conversion plans",
                "Affordability plan (if applicable)",
                "Labor compliance documentation",
                "Building code analysis",
            ],
        ),
        TimelineStep(
            step_name="Completeness Review",
            days_min=14,
            days_max=21,
            description="City determines application completeness",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Ministerial Review",
            days_min=30,
            days_max=60,
            description="Staff reviews for compliance with AB 2011 standards",
            required_submittals=["Building code compliance documentation"],
        ),
        TimelineStep(
            step_name="Building Code Review",
            days_min=21,
            days_max=30,
            description="Building division reviews conversion for code compliance",
            required_submittals=["Updated plans addressing any code issues"],
        ),
        TimelineStep(
            step_name="Approval & Permit",
            days_min=7,
            days_max=14,
            description="Final approval and conversion permit issuance",
            required_submittals=[],
        ),
    ]

    total_min = sum(s.days_min for s in steps)
    total_max = sum(s.days_max for s in steps)

    return EntitlementTimeline(
        pathway_type="Ministerial",
        total_days_min=total_min,
        total_days_max=total_max,
        steps=steps,
        statutory_deadline=None,
        notes=[
            "AB 2011 provides ministerial approval for office-to-residential conversions (Gov. Code § 65912.100)",
            "No public hearing or CEQA review required",
            "Must meet building code requirements for residential use",
            "Prevailing wage required for all projects",
            "Building code compliance may add time to timeline",
        ],
    )


def _adu_timeline() -> EntitlementTimeline:
    """ADU/JADU ministerial timeline (60 days)."""
    steps = [
        TimelineStep(
            step_name="Application Submittal",
            days_min=1,
            days_max=1,
            description="Submit ADU/JADU application",
            required_submittals=[
                "ADU application form",
                "Site plan",
                "Floor plans",
                "Elevations",
                "Utility connections plan",
            ],
        ),
        TimelineStep(
            step_name="Completeness Check",
            days_min=7,
            days_max=14,
            description="City reviews for completeness",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Ministerial Review",
            days_min=21,
            days_max=35,
            description="Staff reviews for ADU standards compliance",
            required_submittals=["Corrections if needed"],
        ),
        TimelineStep(
            step_name="Approval & Permit",
            days_min=7,
            days_max=10,
            description="Final approval and building permit",
            required_submittals=[],
        ),
    ]

    total_min = sum(s.days_min for s in steps)
    total_max = sum(s.days_max for s in steps)

    return EntitlementTimeline(
        pathway_type="Ministerial",
        total_days_min=total_min,
        total_days_max=total_max,
        steps=steps,
        statutory_deadline=60,
        notes=[
            "ADU applications must be approved within 60 days (Gov. Code § 65852.2(a)(3))",
            "Ministerial approval - no public hearing",
            "Must meet state ADU standards",
            "No owner-occupancy requirement under current law",
        ],
    )


def _ministerial_timeline() -> EntitlementTimeline:
    """General ministerial timeline."""
    steps = [
        TimelineStep(
            step_name="Application Submittal",
            days_min=1,
            days_max=1,
            description="Submit complete ministerial application",
            required_submittals=[
                "Application form",
                "Site plan",
                "Architectural plans",
            ],
        ),
        TimelineStep(
            step_name="Completeness Review",
            days_min=7,
            days_max=14,
            description="Staff reviews for completeness",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Staff Review",
            days_min=30,
            days_max=60,
            description="Review for objective standards compliance",
            required_submittals=["Corrections if needed"],
        ),
        TimelineStep(
            step_name="Approval",
            days_min=7,
            days_max=15,
            description="Final approval and permit issuance",
            required_submittals=[],
        ),
    ]

    total_min = sum(s.days_min for s in steps)
    total_max = sum(s.days_max for s in steps)

    return EntitlementTimeline(
        pathway_type="Ministerial",
        total_days_min=total_min,
        total_days_max=total_max,
        steps=steps,
        statutory_deadline=None,
        notes=[
            "Ministerial approval - no public hearing required",
            "Must meet all objective standards",
            "Timeline varies based on application completeness",
        ],
    )


def _administrative_timeline(max_units: int) -> EntitlementTimeline:
    """Administrative review timeline (staff-level approval)."""
    steps = [
        TimelineStep(
            step_name="Pre-Application Meeting",
            days_min=14,
            days_max=30,
            description="Optional meeting with planning staff",
            required_submittals=["Conceptual plans"],
        ),
        TimelineStep(
            step_name="Application Submittal",
            days_min=1,
            days_max=1,
            description="Submit complete application package",
            required_submittals=[
                "Application form",
                "Site plan",
                "Architectural plans",
                "Landscape plan",
            ],
        ),
        TimelineStep(
            step_name="Completeness Review",
            days_min=14,
            days_max=21,
            description="Staff determines application completeness",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Staff Review",
            days_min=30,
            days_max=60,
            description="Detailed staff review of plans and compliance",
            required_submittals=["Response to staff comments"],
        ),
        TimelineStep(
            step_name="Design Review (if applicable)",
            days_min=21,
            days_max=45,
            description="Architectural Review Board or staff design review",
            required_submittals=["Revised plans incorporating design feedback"],
        ),
        TimelineStep(
            step_name="Director Decision",
            days_min=14,
            days_max=21,
            description="Planning Director issues decision",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Appeal Period",
            days_min=15,
            days_max=15,
            description="Public appeal period (if no appeal filed)",
            required_submittals=[],
        ),
    ]

    total_min = sum(s.days_min for s in steps)
    total_max = sum(s.days_max for s in steps)

    return EntitlementTimeline(
        pathway_type="Administrative",
        total_days_min=total_min,
        total_days_max=total_max,
        steps=steps,
        statutory_deadline=None,
        notes=[
            "Administrative approval by Planning Director or Architectural Review Board",
            "No public hearing required for administrative permits",
            "Subject to 15-day appeal period",
            "May require design review for projects over certain thresholds",
        ],
    )


def _discretionary_timeline(max_units: int) -> EntitlementTimeline:
    """Discretionary review timeline (requires public hearing)."""
    # Larger projects require more extensive review
    is_large_project = max_units >= 10

    steps = [
        TimelineStep(
            step_name="Pre-Application Meeting",
            days_min=30,
            days_max=60,
            description="Initial consultation with planning staff",
            required_submittals=["Conceptual plans", "Project description"],
        ),
        TimelineStep(
            step_name="Application Submittal",
            days_min=1,
            days_max=1,
            description="Submit complete entitlement application",
            required_submittals=[
                "Application form",
                "Site plan",
                "Architectural plans",
                "Landscape plan",
                "Environmental assessment",
            ],
        ),
        TimelineStep(
            step_name="Completeness Review",
            days_min=21,
            days_max=30,
            description="Staff determines application completeness",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="CEQA Review",
            days_min=60 if not is_large_project else 90,
            days_max=120 if not is_large_project else 180,
            description="Environmental review under California Environmental Quality Act",
            required_submittals=[
                "Environmental documentation",
                "Response to environmental comments",
            ],
        ),
        TimelineStep(
            step_name="Staff Report Preparation",
            days_min=30,
            days_max=45,
            description="Staff prepares comprehensive analysis and recommendation",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Design Review",
            days_min=30,
            days_max=60,
            description="Architectural Review Board or Design Review Board hearing",
            required_submittals=["Revised plans from design review"],
        ),
        TimelineStep(
            step_name="Public Notice",
            days_min=21,
            days_max=21,
            description="Required public notice period before hearing",
            required_submittals=[],
        ),
        TimelineStep(
            step_name="Planning Commission Hearing",
            days_min=30,
            days_max=60,
            description="Public hearing before Planning Commission",
            required_submittals=["Responses to public comments"],
        ),
        TimelineStep(
            step_name="City Council Hearing (if applicable)",
            days_min=30,
            days_max=60,
            description="City Council hearing for large projects or appeals",
            required_submittals=["Additional information if requested"],
        ),
        TimelineStep(
            step_name="Appeal Period & Final Decision",
            days_min=15,
            days_max=30,
            description="Appeal period and final decision become effective",
            required_submittals=[],
        ),
    ]

    total_min = sum(s.days_min for s in steps)
    total_max = sum(s.days_max for s in steps)

    return EntitlementTimeline(
        pathway_type="Discretionary",
        total_days_min=total_min,
        total_days_max=total_max,
        steps=steps,
        statutory_deadline=None,
        notes=[
            "Discretionary approval requires public hearing(s)",
            "CEQA environmental review typically required",
            "Timeline includes Planning Commission and may include City Council",
            "Large or controversial projects may take longer",
            "Community input and design revisions can extend timeline",
            f"Estimated total: {total_min // 30}-{total_max // 30} months",
        ],
    )
