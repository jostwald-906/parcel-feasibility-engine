"""
PDF Report Generator Service

Generates professional PDF feasibility reports using ReportLab.

Report Structure:
1. Executive Summary
2. Parcel Information
3. Base Zoning Scenario
4. Alternative Scenarios
5. Scenario Comparison Matrix
6. Applicable Laws & Citations
7. Timeline Estimates
8. Recommendations

References:
- ReportLab User Guide: https://www.reportlab.com/docs/reportlab-userguide.pdf
- PDF/A compliance for archival purposes
"""

from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from app.models.analysis import AnalysisResponse, DevelopmentScenario
from app.models.parcel import ParcelBase


class PDFReportGenerator:
    """
    Generate comprehensive PDF feasibility reports.

    Features:
    - Professional formatting with headers/footers
    - Multi-section report structure
    - Tabular scenario comparisons
    - Statute citations and references
    - Timeline estimates for each scenario
    """

    def __init__(self):
        """Initialize PDF generator with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for report."""
        # Only add styles if they don't exist
        if "ReportTitle" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    name="ReportTitle",
                    parent=self.styles["Title"],
                    fontSize=24,
                    textColor=colors.HexColor("#1e3a8a"),  # Dark blue
                    spaceAfter=12,
                    alignment=TA_CENTER,
                )
            )

        if "SectionHeader" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    name="SectionHeader",
                    parent=self.styles["Heading1"],
                    fontSize=16,
                    textColor=colors.HexColor("#1e3a8a"),
                    spaceAfter=12,
                    spaceBefore=12,
                    borderWidth=0,
                    borderColor=colors.HexColor("#1e3a8a"),
                    borderPadding=0,
                    leftIndent=0,
                )
            )

        if "SubsectionHeader" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    name="SubsectionHeader",
                    parent=self.styles["Heading2"],
                    fontSize=12,
                    textColor=colors.HexColor("#3b82f6"),  # Medium blue
                    spaceAfter=6,
                    spaceBefore=6,
                )
            )

        if "BodyText" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    name="BodyText",
                    parent=self.styles["Normal"],
                    fontSize=10,
                    spaceAfter=6,
                    alignment=TA_JUSTIFY,
                )
            )

        if "Citation" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    name="Citation",
                    parent=self.styles["Normal"],
                    fontSize=9,
                    textColor=colors.HexColor("#64748b"),  # Gray
                    leftIndent=20,
                    spaceAfter=4,
                )
            )

        if "Footer" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    name="Footer",
                    parent=self.styles["Normal"],
                    fontSize=8,
                    textColor=colors.HexColor("#64748b"),
                    alignment=TA_CENTER,
                )
            )

    def generate_report(
        self,
        analysis: AnalysisResponse,
        parcel: ParcelBase,
    ) -> bytes:
        """
        Generate complete PDF feasibility report.

        Args:
            analysis: Analysis response with scenarios
            parcel: Parcel data

        Returns:
            PDF file as bytes
        """
        buffer = BytesIO()

        # Create document with custom page template
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build document content
        story = []

        # Title page
        story.extend(self._build_title_page(analysis, parcel))
        story.append(PageBreak())

        # Executive Summary
        story.extend(self._build_executive_summary(analysis, parcel))
        story.append(Spacer(1, 0.3 * inch))

        # Parcel Information
        story.extend(self._build_parcel_information(parcel))
        story.append(Spacer(1, 0.3 * inch))

        # Base Zoning Scenario
        story.extend(self._build_base_scenario_section(analysis.base_scenario))
        story.append(Spacer(1, 0.3 * inch))

        # Alternative Scenarios
        if analysis.alternative_scenarios:
            story.extend(
                self._build_alternative_scenarios_section(analysis.alternative_scenarios)
            )
            story.append(Spacer(1, 0.3 * inch))

        # Scenario Comparison Matrix
        story.extend(self._build_scenario_comparison(analysis))
        story.append(PageBreak())

        # Applicable Laws & Citations
        story.extend(self._build_applicable_laws_section(analysis))
        story.append(Spacer(1, 0.3 * inch))

        # Timeline Estimates
        story.extend(self._build_timeline_section(analysis))
        story.append(Spacer(1, 0.3 * inch))

        # Recommendations
        story.extend(self._build_recommendations_section(analysis))

        # Report Metadata
        story.append(Spacer(1, 0.3 * inch))
        story.extend(self._build_report_metadata_section(analysis))

        # Build PDF with page numbers
        doc.build(story, onFirstPage=self._add_page_footer, onLaterPages=self._add_page_footer)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _build_title_page(
        self, analysis: AnalysisResponse, parcel: ParcelBase
    ) -> List[Any]:
        """Build title page content."""
        elements = []

        # Title
        elements.append(Spacer(1, 2 * inch))
        elements.append(
            Paragraph("Parcel Feasibility Analysis Report", self.styles["ReportTitle"])
        )
        elements.append(Spacer(1, 0.5 * inch))

        # Property address
        elements.append(
            Paragraph(
                f"<b>{parcel.address}</b><br/>{parcel.city}, CA {parcel.zip_code}",
                self.styles["BodyText"],
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # APN
        elements.append(
            Paragraph(f"APN: {parcel.apn}", self.styles["BodyText"])
        )
        elements.append(Spacer(1, 0.5 * inch))

        # Report date
        elements.append(
            Paragraph(
                f"Report Date: {analysis.analysis_date.strftime('%B %d, %Y')}",
                self.styles["BodyText"],
            )
        )

        return elements

    def _build_executive_summary(
        self, analysis: AnalysisResponse, parcel: ParcelBase
    ) -> List[Any]:
        """Build executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))

        # Extract actual lot size from base_scenario notes
        # The parcel object passed in has placeholder data (1.0 sq ft)
        # Real lot size is in the base_scenario data
        lot_size_sqft = parcel.lot_size_sqft

        # Try to extract from base_scenario notes if placeholder detected
        if lot_size_sqft <= 1.0:
            # Look for lot size in base scenario notes
            for note in analysis.base_scenario.notes:
                if "lot size" in note.lower() or "sq ft" in note.lower():
                    # Try to extract number
                    import re
                    match = re.search(r'([\d,]+)\s*sq\s*ft', note, re.IGNORECASE)
                    if match:
                        lot_size_sqft = float(match.group(1).replace(',', ''))
                        break

        # If still not found, calculate from FAR and building size
        if lot_size_sqft <= 1.0:
            # Approximate from max_building_sqft and typical FAR
            # This is a fallback - real lot size should be in parcel data
            lot_size_sqft = analysis.base_scenario.max_building_sqft / 0.5  # Assume 0.5 FAR

        # Calculate key metrics
        base_units = analysis.base_scenario.max_units
        max_units = max(
            [s.max_units for s in analysis.alternative_scenarios] + [base_units]
        )
        num_scenarios = len(analysis.alternative_scenarios) + 1  # +1 for base

        # Get actual property address (not "APN {apn}")
        # If address is just the APN, use alternative format
        if parcel.address and not parcel.address.startswith("APN"):
            property_location = f"{parcel.address}, {parcel.city}, CA"
        else:
            property_location = f"APN {parcel.apn}, {parcel.city}, CA"

        # Build summary paragraph
        summary_text = (
            f"This feasibility analysis evaluates development potential for the parcel located at "
            f"{property_location}. The {lot_size_sqft:,.0f} sq ft parcel "
            f"is zoned {analysis.base_scenario.legal_basis.split('-')[-1].strip() if '-' in analysis.base_scenario.legal_basis else parcel.zoning_code} "
            f"and permits up to {base_units} units under base zoning. "
        )

        if analysis.alternative_scenarios:
            summary_text += (
                f"Analysis of {num_scenarios} development scenarios (including {len(analysis.applicable_laws)} "
                f"applicable housing programs) identifies a maximum potential of {max_units} units "
                f"under {analysis.recommended_scenario}. "
            )
        else:
            summary_text += (
                f"No alternative state housing programs are applicable to this parcel. "
            )

        if analysis.warnings:
            summary_text += (
                f"Please note {len(analysis.warnings)} important constraint(s) identified in this analysis."
            )

        elements.append(Paragraph(summary_text, self.styles["BodyText"]))
        elements.append(Spacer(1, 0.2 * inch))

        # Add legal disclaimer
        disclaimer_text = (
            "<b>IMPORTANT NOTICE:</b> This is a preliminary feasibility analysis for planning purposes only. "
            "This report does not constitute legal advice, professional planning services, or a "
            "guarantee of project approval. Actual development potential may vary based on: "
            "(1) Site-specific conditions and constraints not evaluated in this analysis; "
            "(2) Discretionary review and approval requirements; "
            "(3) Changes in applicable laws, regulations, or local policies; "
            "(4) Environmental review (CEQA) findings; "
            "(5) Public hearing outcomes and community input. "
            "<br/><br/>"
            "Users should consult with qualified professionals including licensed architects, "
            "land use attorneys, and city planning staff before making development decisions or "
            "property investments based on this analysis."
        )

        # Create a style for disclaimers
        if "Disclaimer" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    name="Disclaimer",
                    parent=self.styles["Normal"],
                    fontSize=8,
                    textColor=colors.HexColor("#991b1b"),  # Dark red
                    leftIndent=10,
                    rightIndent=10,
                    spaceAfter=6,
                    spaceBefore=6,
                    borderWidth=1,
                    borderColor=colors.HexColor("#ef4444"),  # Red border
                    borderPadding=8,
                    backColor=colors.HexColor("#fef2f2"),  # Light red background
                )
            )

        elements.append(Paragraph(disclaimer_text, self.styles["Disclaimer"]))

        return elements

    def _build_parcel_information(self, parcel: ParcelBase) -> List[Any]:
        """Build parcel information section."""
        elements = []

        elements.append(Paragraph("Parcel Information", self.styles["SectionHeader"]))

        # Build parcel info table
        data = [
            ["<b>Property</b>", ""],
            ["Address:", parcel.address],
            ["APN:", parcel.apn],
            ["City:", parcel.city],
            ["County:", parcel.county],
            ["Zip Code:", parcel.zip_code],
            ["", ""],
            ["<b>Site Characteristics</b>", ""],
            ["Lot Size:", f"{parcel.lot_size_sqft:,.0f} sq ft ({parcel.lot_size_sqft / 43560:.3f} acres)"],
            ["Zoning:", parcel.zoning_code],
        ]

        if parcel.general_plan:
            data.append(["General Plan:", parcel.general_plan])

        if parcel.existing_units > 0:
            data.extend([
                ["", ""],
                ["<b>Existing Development</b>", ""],
                ["Existing Units:", str(parcel.existing_units)],
                ["Existing Building Sq Ft:", f"{parcel.existing_building_sqft:,.0f}"],
            ])

        if parcel.use_description:
            data.append(["Current Use:", parcel.use_description])

        if parcel.year_built:
            data.append(["Year Built:", str(parcel.year_built)])

        # Tier and overlay information
        if parcel.development_tier or parcel.overlay_codes:
            data.extend([
                ["", ""],
                ["<b>Special Plan Areas</b>", ""],
            ])
            if parcel.development_tier:
                data.append(["Development Tier:", f"Tier {parcel.development_tier}"])
            if parcel.overlay_codes:
                data.append(["Overlay Codes:", ", ".join(parcel.overlay_codes)])

        table = Table(data, colWidths=[2.5 * inch, 4 * inch])
        table.setStyle(
            TableStyle([
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )

        elements.append(table)

        return elements

    def _build_base_scenario_section(self, scenario: DevelopmentScenario) -> List[Any]:
        """Build base zoning scenario section."""
        elements = []

        elements.append(Paragraph("Base Zoning Scenario", self.styles["SectionHeader"]))

        # Scenario details
        elements.append(
            Paragraph(
                f"<b>{scenario.scenario_name}</b> - {scenario.legal_basis}",
                self.styles["SubsectionHeader"],
            )
        )

        # Key metrics table
        data = [
            ["Maximum Units:", str(scenario.max_units)],
            ["Maximum Building Sq Ft:", f"{scenario.max_building_sqft:,.0f}"],
            ["Maximum Height:", f"{scenario.max_height_ft:.0f} ft ({scenario.max_stories} stories)"],
            ["Parking Required:", f"{scenario.parking_spaces_required} spaces"],
        ]

        if scenario.affordable_units_required > 0:
            data.append(
                ["Affordable Units Required:", str(scenario.affordable_units_required)]
            )

        if scenario.setbacks:
            setback_str = ", ".join(
                [f"{k}: {v} ft" for k, v in scenario.setbacks.items()]
            )
            data.append(["Setbacks:", setback_str])

        data.append(["Lot Coverage:", f"{scenario.lot_coverage_pct:.0f}%"])

        table = Table(data, colWidths=[2 * inch, 4.5 * inch])
        table.setStyle(
            TableStyle([
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))

        # Notes
        if scenario.notes:
            elements.append(
                Paragraph("<b>Notes:</b>", self.styles["SubsectionHeader"])
            )
            for note in scenario.notes:
                elements.append(Paragraph(f"• {note}", self.styles["Citation"]))

        return elements

    def _build_alternative_scenarios_section(
        self, scenarios: List[DevelopmentScenario]
    ) -> List[Any]:
        """Build alternative scenarios section."""
        elements = []

        elements.append(
            Paragraph("Alternative Development Scenarios", self.styles["SectionHeader"])
        )

        for i, scenario in enumerate(scenarios, 1):
            elements.append(
                Paragraph(
                    f"{i}. <b>{scenario.scenario_name}</b> - {scenario.legal_basis}",
                    self.styles["SubsectionHeader"],
                )
            )

            # Scenario metrics
            data = [
                ["Maximum Units:", str(scenario.max_units)],
                ["Maximum Building Sq Ft:", f"{scenario.max_building_sqft:,.0f}"],
                ["Maximum Height:", f"{scenario.max_height_ft:.0f} ft ({scenario.max_stories} stories)"],
                ["Parking Required:", f"{scenario.parking_spaces_required} spaces"],
            ]

            if scenario.affordable_units_required > 0:
                data.append(
                    ["Affordable Units Required:", str(scenario.affordable_units_required)]
                )

            # Concessions and waivers (density bonus)
            if scenario.concessions_applied:
                data.append(
                    ["Concessions:", f"{len(scenario.concessions_applied)} granted"]
                )

            if scenario.waivers_applied:
                data.append(
                    ["Waivers:", f"{len(scenario.waivers_applied)} granted"]
                )

            table = Table(data, colWidths=[2 * inch, 4.5 * inch])
            table.setStyle(
                TableStyle([
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )

            elements.append(table)
            elements.append(Spacer(1, 0.1 * inch))

            # Notes
            if scenario.notes:
                key_notes = scenario.notes[:5]  # Limit to first 5 notes
                for note in key_notes:
                    elements.append(Paragraph(f"• {note}", self.styles["Citation"]))

            elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _build_scenario_comparison(self, analysis: AnalysisResponse) -> List[Any]:
        """Build scenario comparison matrix."""
        elements = []

        elements.append(
            Paragraph("Scenario Comparison Matrix", self.styles["SectionHeader"])
        )

        # Build comparison table
        all_scenarios = [analysis.base_scenario] + analysis.alternative_scenarios

        # Table headers
        headers = ["Scenario", "Max Units", "Building Sq Ft", "Height (ft)", "Parking", "Affordable"]

        # Table data
        data = [headers]

        for scenario in all_scenarios:
            row = [
                scenario.scenario_name,
                str(scenario.max_units),
                f"{scenario.max_building_sqft:,.0f}",
                f"{scenario.max_height_ft:.0f}",
                str(scenario.parking_spaces_required),
                str(scenario.affordable_units_required) if scenario.affordable_units_required > 0 else "-",
            ]
            data.append(row)

        # Create table with appropriate column widths
        col_widths = [2.2 * inch, 0.8 * inch, 1.1 * inch, 0.8 * inch, 0.7 * inch, 0.9 * inch]
        table = Table(data, colWidths=col_widths)

        # Style table
        table.setStyle(
            TableStyle([
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                # Data rows
                ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                # Alternating row colors
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                # Padding
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )

        elements.append(table)

        return elements

    def _build_applicable_laws_section(self, analysis: AnalysisResponse) -> List[Any]:
        """Build applicable laws and citations section."""
        elements = []

        elements.append(
            Paragraph("Applicable Laws & Citations", self.styles["SectionHeader"])
        )

        if not analysis.applicable_laws:
            elements.append(
                Paragraph("No state housing programs applicable.", self.styles["BodyText"])
            )
            # Add statutory caveat even if no state programs
            elements.append(Spacer(1, 0.2 * inch))
            caveat_text = (
                "<b>NOTE:</b> Statutory citations are current as of "
                f"{analysis.analysis_date.strftime('%B %d, %Y')} and are subject to change "
                "through legislative amendments, court decisions, or local ordinance updates. Users should "
                "verify current law with qualified legal counsel before relying on this analysis."
            )
            elements.append(Paragraph(caveat_text, self.styles["Citation"]))
            return elements

        # List applicable laws
        elements.append(
            Paragraph("<b>Applicable Housing Programs:</b>", self.styles["SubsectionHeader"])
        )

        for law in analysis.applicable_laws:
            elements.append(Paragraph(f"• {law}", self.styles["BodyText"]))

        elements.append(Spacer(1, 0.2 * inch))

        # Extract statute references from scenario notes
        all_citations = set()
        for scenario in [analysis.base_scenario] + analysis.alternative_scenarios:
            for note in scenario.notes:
                # Extract citations like "Gov. Code § 12345" or "SMMC § 9.04.12"
                if "§" in note or "Code" in note:
                    all_citations.add(note)

        if all_citations:
            elements.append(
                Paragraph("<b>Key Statute References:</b>", self.styles["SubsectionHeader"])
            )
            for citation in sorted(all_citations)[:10]:  # Limit to 10 most important
                elements.append(Paragraph(f"• {citation}", self.styles["Citation"]))

        elements.append(Spacer(1, 0.2 * inch))

        # Add statutory caveat
        caveat_text = (
            "<b>NOTE:</b> Statutory citations are current as of "
            f"{analysis.analysis_date.strftime('%B %d, %Y')} and are subject to change "
            "through legislative amendments, court decisions, or local ordinance updates. Users should "
            "verify current law with qualified legal counsel before relying on this analysis. "
            "All statute references can be verified at leginfo.legislature.ca.gov for California state law "
            "and with the Santa Monica City Clerk for local municipal code provisions."
        )

        elements.append(Paragraph(caveat_text, self.styles["Citation"]))

        return elements

    def _build_timeline_section(self, analysis: AnalysisResponse) -> List[Any]:
        """Build timeline estimates section."""
        elements = []

        elements.append(
            Paragraph("Timeline Estimates", self.styles["SectionHeader"])
        )

        # Collect scenarios with timeline data
        scenarios_with_timelines = []
        for scenario in [analysis.base_scenario] + analysis.alternative_scenarios:
            if scenario.estimated_timeline:
                scenarios_with_timelines.append(scenario)

        if not scenarios_with_timelines:
            elements.append(
                Paragraph(
                    "Timeline estimates not available for analyzed scenarios.",
                    self.styles["BodyText"],
                )
            )
            return elements

        # Build timeline table
        headers = ["Scenario", "Pathway Type", "Timeline (days)", "Statutory Deadline"]
        data = [headers]

        for scenario in scenarios_with_timelines:
            timeline = scenario.estimated_timeline
            days_range = f"{timeline.get('total_days_min', 'N/A')} - {timeline.get('total_days_max', 'N/A')}"
            statutory = f"{timeline.get('statutory_deadline', 'None')} days" if timeline.get('statutory_deadline') else "-"

            row = [
                scenario.scenario_name,
                timeline.get("pathway_type", "Unknown"),
                days_range,
                statutory,
            ]
            data.append(row)

        table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.3 * inch, 1.2 * inch])
        table.setStyle(
            TableStyle([
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                # Data
                ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                # Padding
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )

        elements.append(table)
        elements.append(Spacer(1, 0.1 * inch))

        # Timeline caveat
        caveat_text = (
            "<b>NOTICE:</b> Timeline estimates are based on typical processing times and assume complete "
            "applications with no appeals or litigation. Actual timelines may be significantly longer "
            "due to factors including: (1) Incomplete applications requiring resubmittal; "
            "(2) Staff workload and resource constraints; (3) Public opposition or community concerns; "
            "(4) Environmental review requirements beyond initial assessment; (5) Discretionary approvals "
            "requiring multiple hearings; (6) Design revisions requested by planning staff or commissions; "
            "(7) Appeals to Planning Commission or City Council. "
            "<br/><br/>"
            "Ministerial pathways (SB 9, SB 35, ADU) have statutory deadlines but may still experience delays "
            "if applications are deemed incomplete. Discretionary projects requiring CEQA review should expect "
            "12-24 months minimum. Consult with city planning staff for project-specific timeline guidance."
        )

        elements.append(Paragraph(caveat_text, self.styles["Disclaimer"]))

        return elements

    def _build_recommendations_section(self, analysis: AnalysisResponse) -> List[Any]:
        """Build recommendations section."""
        elements = []

        elements.append(Paragraph("Recommendations", self.styles["SectionHeader"]))

        # Recommended scenario
        elements.append(
            Paragraph(
                f"<b>Recommended Development Pathway:</b> {analysis.recommended_scenario}",
                self.styles["SubsectionHeader"],
            )
        )

        elements.append(
            Paragraph(analysis.recommendation_reason, self.styles["BodyText"])
        )

        elements.append(Spacer(1, 0.2 * inch))

        # Potential incentives
        if analysis.potential_incentives:
            elements.append(
                Paragraph("<b>Available Incentives:</b>", self.styles["SubsectionHeader"])
            )
            for incentive in analysis.potential_incentives:
                elements.append(Paragraph(f"• {incentive}", self.styles["BodyText"]))

            elements.append(Spacer(1, 0.2 * inch))

        # Warnings and constraints
        if analysis.warnings:
            elements.append(
                Paragraph("<b>Important Considerations:</b>", self.styles["SubsectionHeader"])
            )
            for warning in analysis.warnings:
                elements.append(Paragraph(f"• {warning}", self.styles["BodyText"]))

        return elements

    def _build_report_metadata_section(self, analysis: AnalysisResponse) -> List[Any]:
        """Build report metadata section."""
        elements = []

        elements.append(
            Paragraph("Report Metadata", self.styles["SectionHeader"])
        )

        # Get version from settings
        from app.core.config import settings
        version = getattr(settings, 'VERSION', '1.0.0')

        # Build metadata table
        metadata = [
            ["<b>Report Information</b>", ""],
            ["Generated:", analysis.analysis_date.strftime('%B %d, %Y at %I:%M %p')],
            ["Analysis Engine:", f"Santa Monica Parcel Feasibility Engine v{version}"],
            ["Report Type:", "Automated Feasibility Analysis"],
            ["", ""],
            ["<b>Data Sources</b>", ""],
            ["Zoning Standards:", "Santa Monica Municipal Code (SMMC)"],
            ["State Law Citations:", "California Government Code, leginfo.legislature.ca.gov"],
            ["Income Limits:", "HCD 2025 State Income Limits (Effective April 23, 2025)"],
            ["GIS Data:", "Santa Monica GIS, California HCD, State Databases"],
            ["", ""],
            ["<b>Report Limitations</b>", ""],
            ["Analysis Type:", "Automated desktop analysis - no site inspection performed"],
            ["Not Included:", "Site-specific engineering, environmental assessment, title review"],
            ["Not Included:", "Detailed CEQA analysis, traffic study, utility capacity analysis"],
            ["Not Included:", "Market feasibility, financial pro forma, construction cost estimate"],
            ["", ""],
            ["<b>Validity</b>", ""],
            ["Valid As Of:", analysis.analysis_date.strftime('%B %d, %Y')],
            ["Note:", "Zoning and regulations are subject to change without notice"],
            ["Recommendation:", "Verify current standards with Santa Monica Planning Division"],
            ["Contact:", "planning@smgov.net | (310) 458-8341"],
        ]

        table = Table(metadata, colWidths=[2.5 * inch, 4 * inch])
        table.setStyle(
            TableStyle([
                ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                # Add subtle background to section headers
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (0, 11), (-1, 11), colors.HexColor("#f1f5f9")),
                ("BACKGROUND", (0, 17), (-1, 17), colors.HexColor("#f1f5f9")),
            ])
        )

        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))

        # Add final disclaimer
        final_disclaimer = (
            "<b>PROFESSIONAL SERVICES DISCLAIMER:</b> This automated analysis tool provides preliminary "
            "feasibility information only. It does not replace professional services from licensed "
            "architects, engineers, land use attorneys, or other qualified consultants. Development "
            "applicants should engage appropriate professionals and consult directly with City of Santa Monica "
            "planning staff before proceeding with property transactions or development applications."
        )

        elements.append(Paragraph(final_disclaimer, self.styles["Disclaimer"]))

        return elements

    def _add_page_footer(self, canvas, doc):
        """Add footer to each page with page number."""
        canvas.saveState()

        # Page number
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawRightString(
            doc.width + doc.leftMargin,
            0.5 * inch,
            text,
        )

        # Report footer
        footer_text = "Parcel Feasibility Analysis | Generated by Parcel Feasibility Engine"
        canvas.drawString(
            doc.leftMargin,
            0.5 * inch,
            footer_text,
        )

        canvas.restoreState()


# Module-level function for easy access
def generate_pdf_report(analysis: AnalysisResponse, parcel: ParcelBase) -> bytes:
    """
    Generate PDF feasibility report.

    Args:
        analysis: Analysis response with scenarios
        parcel: Parcel data

    Returns:
        PDF file as bytes

    Example:
        >>> pdf_bytes = generate_pdf_report(analysis, parcel)
        >>> with open("report.pdf", "wb") as f:
        ...     f.write(pdf_bytes)
    """
    generator = PDFReportGenerator()
    return generator.generate_report(analysis, parcel)
