# Services - AI Agent Context

## Overview

Service layer for business logic that doesn't fit into rules or models. Services provide reusable functionality for analysis, calculation, and external integrations.

## Directory Structure

```
app/services/
├── report_generator.py         # PDF report generation (ReportLab)
├── ami_calculator.py            # AMI/affordability calculations
├── timeline_estimator.py        # Entitlement timeline estimates
├── community_benefits.py        # Community benefits analysis
├── cnel_analyzer.py             # Noise level analysis
├── rent_control_api.py          # Santa Monica rent control API
├── comprehensive_analysis.py    # Comprehensive scenario generation
├── rhna_service.py              # RHNA allocation service
└── arcgis_client.py             # ArcGIS REST API client
```

## PDF Report Generator (report_generator.py)

### Overview

Generates professional PDF feasibility reports using ReportLab. Provides comprehensive multi-section reports with tabular comparisons, statute citations, and timeline estimates.

**Key Features**:
- Professional formatting with headers/footers
- Multi-section report structure
- Tabular scenario comparisons
- Statute citations and references
- Timeline estimates for each scenario
- Automatic page numbering

### Usage

```python
from app.services.report_generator import generate_pdf_report
from app.models.analysis import AnalysisResponse
from app.models.parcel import ParcelBase

# Generate PDF report
pdf_bytes = generate_pdf_report(analysis, parcel)

# Save to file
with open("report.pdf", "wb") as f:
    f.write(pdf_bytes)

# Or return in FastAPI endpoint
from fastapi.responses import Response

return Response(
    content=pdf_bytes,
    media_type="application/pdf",
    headers={
        "Content-Disposition": f'attachment; filename="report.pdf"'
    }
)
```

### Report Structure

1. **Title Page**: Property address, APN, report date
2. **Executive Summary**: 1-paragraph overview with key metrics
3. **Parcel Information**: APN, address, lot size, zoning, existing development
4. **Base Zoning Scenario**: Base development rights with detailed metrics
5. **Alternative Scenarios**: State law programs (SB 9, SB 35, AB 2011, Density Bonus)
6. **Scenario Comparison Matrix**: Tabular comparison of all scenarios
7. **Applicable Laws & Citations**: List of all applicable laws with statute references
8. **Timeline Estimates**: Approval timelines for each pathway
9. **Recommendations**: Recommended scenario with rationale

### API Integration

```python
# app/api/analyze.py

@router.post("/export/pdf")
async def export_feasibility_report(request: AnalysisRequest) -> Response:
    """Generate PDF report for parcel feasibility analysis."""
    from app.services.report_generator import generate_pdf_report

    # Run full analysis
    analysis = await analyze_parcel(request)

    # Generate PDF report
    pdf_bytes = generate_pdf_report(analysis, request.parcel)

    # Return PDF with appropriate headers
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="feasibility_report_{parcel.apn}.pdf"'
        }
    )
```

### Custom Styles

The report generator uses custom ReportLab styles for consistent formatting:

- **ReportTitle**: Large blue title for cover page (24pt)
- **SectionHeader**: Bold blue section headers (16pt)
- **SubsectionHeader**: Medium blue subsection headers (12pt)
- **BodyText**: Standard body text with justification (10pt)
- **Citation**: Gray indented citation text (9pt)
- **Footer**: Small gray footer text (8pt)

### PDFReportGenerator Class

```python
from app.services.report_generator import PDFReportGenerator

generator = PDFReportGenerator()

# Generate complete report
pdf_bytes = generator.generate_report(analysis, parcel)

# Or use individual section builders
title_elements = generator._build_title_page(analysis, parcel)
summary_elements = generator._build_executive_summary(analysis, parcel)
parcel_elements = generator._build_parcel_information(parcel)
# ...etc
```

### Section Builders

Each report section has a dedicated builder method:

- `_build_title_page()`: Title page with property info
- `_build_executive_summary()`: Executive summary paragraph
- `_build_parcel_information()`: Parcel details table
- `_build_base_scenario_section()`: Base zoning scenario
- `_build_alternative_scenarios_section()`: Alternative scenarios
- `_build_scenario_comparison()`: Comparison matrix table
- `_build_applicable_laws_section()`: Laws and citations
- `_build_timeline_section()`: Timeline estimates table
- `_build_recommendations_section()`: Recommendations

### Formatting Features

**Tables**: Professional tables with alternating row colors, grid lines, and header styling

```python
# Scenario comparison table
table = Table(data, colWidths=[...])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),  # Blue header
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
]))
```

**Page Footers**: Automatic page numbering and report identification

```python
def _add_page_footer(self, canvas, doc):
    """Add footer to each page with page number."""
    page_num = canvas.getPageNumber()
    canvas.drawRightString(doc.width + doc.leftMargin, 0.5 * inch, f"Page {page_num}")
    canvas.drawString(doc.leftMargin, 0.5 * inch, "Parcel Feasibility Analysis | Generated by Parcel Feasibility Engine")
```

### Testing

Comprehensive test coverage (99%):

```bash
# Run report generator tests
pytest tests/test_report_generator.py -v

# With coverage
pytest tests/test_report_generator.py --cov=app/services/report_generator --cov-report=term
```

**Test Categories**:
- PDF generation and structure validation
- Individual section building
- Content accuracy
- Error handling (missing optional fields)
- Edge cases (large parcels, many scenarios)

### Dependencies

- **reportlab==4.2.5**: PDF generation library
- Required by: `requirements.txt`

### Error Handling

The report generator handles missing optional fields gracefully:

```python
# Handles parcels with minimal data
minimal_parcel = ParcelBase(
    apn="TEST",
    address="Test",
    city="Test",
    county="Test",
    zip_code="00000",
    lot_size_sqft=5000.0,
    zoning_code="R1",
    existing_units=0,
    existing_building_sqft=0
)

# Will still generate valid PDF
pdf_bytes = generate_pdf_report(analysis, minimal_parcel)
```

### Performance

- Typical report: ~8-15 KB for 2-4 scenarios
- Generation time: <1 second for typical report
- Supports multiple scenarios without performance degradation

## AMI Calculator (ami_calculator.py)

See [Backend CLAUDE.md](../CLAUDE.md#ami-calculator-appservicesami_calculatorpy) for detailed documentation.

**Quick reference**:

```python
from app.services.ami_calculator import get_ami_calculator

calculator = get_ami_calculator()

# Income limit lookup
income_limit = calculator.get_income_limit("Los Angeles", 50.0, 2)

# Affordable rent
rent = calculator.calculate_max_rent("Los Angeles", 50.0, bedrooms=2)

# Affordable sales price
price = calculator.calculate_max_sales_price("Los Angeles", 80.0, household_size=4)
```

## Timeline Estimator (timeline_estimator.py)

See [Backend CLAUDE.md](../CLAUDE.md#entitlement-timeline-estimation-appservicestimeline_estimatorpy) for detailed documentation.

**Quick reference**:

```python
from app.services.timeline_estimator import estimate_timeline

timeline = estimate_timeline(
    scenario_name="SB 9 Lot Split",
    legal_basis="SB 9 (Gov. Code § 65852.21)",
    max_units=4
)

# Access timeline data
print(f"Pathway: {timeline.pathway_type}")  # "Ministerial"
print(f"Timeline: {timeline.total_days_min}-{timeline.total_days_max} days")
print(f"Statutory deadline: {timeline.statutory_deadline} days")  # 60
```

## Service Patterns

### Pattern 1: Singleton Service

```python
# Singleton pattern for stateless services
_calculator_instance: Optional[AMICalculator] = None

def get_ami_calculator() -> AMICalculator:
    """Get singleton AMI calculator instance."""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = AMICalculator()
    return _calculator_instance
```

### Pattern 2: Stateless Function Service

```python
# Direct function exports for stateless operations
def estimate_timeline(scenario_name: str, legal_basis: str, max_units: int) -> EntitlementTimeline:
    """Estimate entitlement timeline for development scenario."""
    pathway_type = detect_pathway_type(legal_basis)
    # ... build timeline
    return timeline
```

### Pattern 3: Class-Based Service

```python
# Class-based service with instance methods
class PDFReportGenerator:
    """Generate comprehensive PDF feasibility reports."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def generate_report(self, analysis: AnalysisResponse, parcel: ParcelBase) -> bytes:
        """Generate complete PDF feasibility report."""
        # ... build report
        return pdf_bytes
```

## Testing Services

### Test Structure

```python
# tests/test_service_name.py

"""Tests for Service Name."""
import pytest
from app.services.service_name import ServiceClass

class TestServiceInitialization:
    """Tests for service initialization."""

    def test_service_initializes(self):
        """Test service initializes successfully."""
        service = ServiceClass()
        assert service is not None

class TestServiceMethods:
    """Tests for service methods."""

    def test_method_returns_expected_result(self):
        """Test method returns expected result."""
        service = ServiceClass()
        result = service.method()
        assert result is not None
```

### Fixtures for Services

```python
# tests/conftest.py

@pytest.fixture
def sample_service_data():
    """Sample data for service testing."""
    return {...}
```

### Coverage Goals

- **Target**: 80%+ coverage for business logic
- **Priority**: Test core functionality and error handling
- **Lower priority**: Initialization code, simple getters/setters

## Integration with API Endpoints

Services are typically called from API endpoints:

```python
# app/api/analyze.py

from app.services.ami_calculator import get_ami_calculator
from app.services.timeline_estimator import estimate_timeline
from app.services.report_generator import generate_pdf_report

@router.post("/analyze")
async def analyze_parcel(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze parcel for development feasibility."""

    # Use services as needed
    calculator = get_ami_calculator()
    rent = calculator.calculate_max_rent(...)

    timeline = estimate_timeline(...)

    # Return response
    return AnalysisResponse(...)
```

## Best Practices

1. **Pydantic Models**: Use Pydantic models for all inputs/outputs
2. **Type Hints**: Comprehensive type hints for all methods
3. **Docstrings**: Document all public methods with examples
4. **Error Handling**: Graceful handling of missing/invalid data
5. **Testability**: Design services to be easily testable
6. **Stateless**: Prefer stateless functions when possible
7. **Caching**: Use caching for expensive operations (e.g., AMI data loading)
8. **Logging**: Use structured logging for debugging

## Related Documentation

- [Backend CLAUDE.md](../CLAUDE.md) - Overall backend patterns
- [Root CLAUDE.md](../../CLAUDE.md) - Project overview
- [Testing CLAUDE.md](../../tests/CLAUDE.md) - Testing patterns
