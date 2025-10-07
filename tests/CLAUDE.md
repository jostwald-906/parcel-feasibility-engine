# Testing Patterns - AI Agent Context

## Overview

Testing strategy for the Parcel Feasibility Engine backend using pytest, pytest-cov, and parametrized testing patterns.

**Testing Philosophy**:
- Test behavior, not implementation
- Use fixtures for reusable test data
- Parametrize tests for multiple scenarios
- Clear, descriptive test names
- Document expected behavior in docstrings

## Technology Stack

- **pytest 7.4.4**: Test framework
- **pytest-cov 4.1.0**: Coverage reporting
- **pytest-asyncio 0.23.3**: Async test support

## Running Tests

```bash
# From project root: /Users/Jordan_Ostwald/Parcel Feasibility Engine/

# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_density_bonus.py -v

# Run specific test class
pytest tests/test_density_bonus.py::TestDensityBonusPercentages -v

# Run specific test
pytest tests/test_density_bonus.py::TestDensityBonusPercentages::test_bonus_percentages -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Coverage report in htmlcov/index.html
open htmlcov/index.html

# Run tests matching pattern
pytest tests/ -k "density" -v

# Run tests with output (show print statements)
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto
```

## Test Organization

```
tests/
├── conftest.py                 # Shared fixtures
├── test_base_zoning.py         # Base zoning calculations
├── test_density_bonus.py       # Density Bonus Law tests
├── test_sb9.py                 # SB 9 tests
├── test_sb35.py                # SB 35 tests
├── test_ab2011.py              # AB 2011 tests
├── test_tiered_standards.py    # Tier resolution tests
├── test_overlays.py            # Overlay handling tests
├── test_gis_integration.py     # GIS API integration tests
└── test_api_endpoints.py       # FastAPI endpoint tests
```

## Fixtures (conftest.py)

### Available Fixtures

```python
# tests/conftest.py

import pytest
from app.models.parcel import ParcelBase

@pytest.fixture
def r1_parcel() -> ParcelBase:
    """
    Single-family residential parcel.

    Suitable for testing:
    - Base R1 zoning
    - SB9 eligibility (lot splits and duplexes)
    - Dimensional standards
    """
    return ParcelBase(
        apn="123-456-789",
        address="123 Main Street",
        city="San Diego",
        county="San Diego",
        zip_code="92101",
        lot_size_sqft=6000.0,
        lot_width_ft=60.0,
        lot_depth_ft=100.0,
        zoning_code="R1",
        existing_units=1,
        existing_building_sqft=1800.0,
        year_built=1965,
        latitude=32.7157,
        longitude=-117.1611
    )

@pytest.fixture
def r2_parcel() -> ParcelBase:
    """Low-density multi-family residential parcel."""
    return ParcelBase(
        apn="234-567-890",
        address="456 Oak Avenue",
        city="Los Angeles",
        county="Los Angeles",
        zip_code="90012",
        lot_size_sqft=10000.0,
        zoning_code="R2",
        existing_units=2,
        existing_building_sqft=2400.0,
    )

# More fixtures: dcp_parcel, coastal_parcel, historic_parcel,
# transit_adjacent_parcel, commercial_parcel, small_r1_parcel, large_r4_parcel
```

### Using Fixtures

```python
def test_density_bonus_on_r2(r2_parcel):
    """Test density bonus on R2 parcel."""
    from app.rules.density_bonus import apply_density_bonus
    from app.rules.base_zoning import analyze_base_zoning

    base_scenario = analyze_base_zoning(r2_parcel)
    bonus_scenario = apply_density_bonus(
        base_scenario,
        r2_parcel,
        affordability_pct=10,
        income_level="low"
    )

    assert bonus_scenario.max_units > base_scenario.max_units
```

## Test Structure

### Test Class Organization

```python
# tests/test_density_bonus.py

"""
Tests for State Density Bonus Law (Government Code Section 65915).
"""
import pytest
from app.rules.state_law.density_bonus import (
    apply_density_bonus,
    calculate_density_bonus_percentage,
    calculate_concessions,
)
from app.rules.base_zoning import analyze_base_zoning


class TestDensityBonusPercentages:
    """Tests for density bonus percentage calculations."""

    def test_very_low_income_tiers(self):
        """Test very low income affordability tiers per § 65915(f)(1)."""
        assert calculate_density_bonus_percentage(5, "very_low") == 20
        assert calculate_density_bonus_percentage(10, "very_low") == 35
        assert calculate_density_bonus_percentage(15, "very_low") == 50

    def test_100_percent_affordable(self):
        """Test 100% affordable project gets 80% bonus per § 65915(f)(4)."""
        bonus = calculate_density_bonus_percentage(100, "very_low")
        assert bonus == 80


class TestConcessionCalculations:
    """Tests for concession/incentive calculations per § 65915(d)."""

    def test_10_percent_gets_1_concession(self):
        """Test 10% affordability gets 1 concession per § 65915(d)."""
        assert calculate_concessions(10) == 1

    def test_100_percent_gets_4_concessions(self):
        """Test 100% gets 4th concession per § 65915(d)(2)(D)."""
        assert calculate_concessions(100) == 4


class TestDensityBonusApplication:
    """Tests for applying density bonus to scenarios."""

    def test_density_bonus_increases_units(self, r2_parcel):
        """Test that density bonus increases unit count."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        assert bonus_scenario.max_units > base_units

    def test_20_percent_bonus_calculation(self, r2_parcel):
        """Test 20% density bonus calculation for 10% low income."""
        base_scenario = analyze_base_zoning(r2_parcel)
        base_units = base_scenario.max_units

        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        # 10% low income = 20% density bonus
        expected_units = base_units + int(base_units * 0.20)
        assert bonus_scenario.max_units == expected_units
```

## Parametrized Testing

### Basic Parametrization

```python
@pytest.mark.parametrize("affordability,income,expected_bonus", [
    (5, "very_low", 20),
    (10, "very_low", 35),
    (15, "very_low", 50),
    (10, "low", 20),
    (17, "low", 35),
    (24, "low", 50),
    (10, "moderate", 5),
    (40, "moderate", 35),
    (100, "very_low", 80),
])
def test_bonus_percentages(affordability, income, expected_bonus):
    """Test density bonus percentage calculations per § 65915(f)."""
    bonus = calculate_density_bonus_percentage(affordability, income)
    assert bonus == expected_bonus
```

### Parametrized with IDs

```python
@pytest.mark.parametrize("affordability,expected_concessions", [
    pytest.param(5, 0, id="below_threshold"),
    pytest.param(10, 1, id="10_percent_1_concession"),
    pytest.param(20, 2, id="20_percent_2_concessions"),
    pytest.param(30, 3, id="30_percent_3_concessions"),
    pytest.param(100, 4, id="100_percent_4_concessions"),
])
def test_concession_tiers(affordability, expected_concessions):
    """Test concession tiers for various affordability percentages."""
    assert calculate_concessions(affordability) == expected_concessions
```

### Parametrized Fixtures

```python
@pytest.fixture(params=["very_low", "VERY_LOW", "Very Low", "very low"])
def income_level_variation(request):
    """Test various income level string formats."""
    return request.param

def test_income_level_string_variations(income_level_variation):
    """Test that income level handles various string formats."""
    bonus = calculate_density_bonus_percentage(10, income_level_variation)
    assert bonus == 35  # 10% very low = 35% bonus
```

## Testing Patterns

### Eligibility Testing

```python
class TestSB9Eligibility:
    """Tests for SB 9 eligibility checks per § 65852.21(j)."""

    def test_single_family_zoning_required(self, r1_parcel):
        """Test that single-family zoning is required."""
        scenario = analyze_sb9(r1_parcel)
        assert scenario is not None

    def test_historic_property_excluded(self, r1_parcel):
        """Test historic properties excluded per § 65852.21(j)(1)."""
        r1_parcel.is_historic_property = True
        scenario = analyze_sb9(r1_parcel)
        assert scenario is None

    def test_rent_controlled_excluded(self, r1_parcel):
        """Test rent-controlled units excluded per § 65852.21(j)(10)."""
        r1_parcel.has_rent_controlled_units = True
        scenario = analyze_sb9(r1_parcel)
        assert scenario is None

    def test_minimum_lot_size(self):
        """Test minimum lot size requirement (2400 sq ft for split)."""
        small_parcel = ParcelBase(
            apn="TEST",
            address="Test",
            city="Test",
            county="Test",
            zip_code="00000",
            lot_size_sqft=2000.0,  # Too small
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )
        scenario = analyze_sb9(small_parcel)
        assert scenario is None
```

### Calculation Testing

```python
class TestUnitCalculations:
    """Tests for unit count calculations."""

    def test_density_calculation_by_acreage(self, r2_parcel):
        """Test unit calculation based on density (units per acre)."""
        # R2 typically allows 17 units/acre
        # 10,000 sq ft = 0.2296 acres
        # 0.2296 × 17 ≈ 3.9 → 3 units (floor)
        scenario = analyze_base_zoning(r2_parcel)
        assert scenario.max_units >= 3

    def test_far_based_calculation(self, r2_parcel):
        """Test building size calculation based on FAR."""
        scenario = analyze_base_zoning(r2_parcel)

        # Max building size should be lot_size × FAR
        # R2 typical FAR: 0.5-0.75
        expected_min = r2_parcel.lot_size_sqft * 0.5
        expected_max = r2_parcel.lot_size_sqft * 1.0

        assert expected_min <= scenario.max_building_sqft <= expected_max
```

### Notes and Documentation Testing

```python
class TestScenarioDocumentation:
    """Tests for scenario notes and documentation."""

    def test_scenario_includes_statute_reference(self, r2_parcel):
        """Test that scenario notes include statute references."""
        base_scenario = analyze_base_zoning(r2_parcel)
        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=10,
            income_level="low"
        )

        notes_text = " ".join(bonus_scenario.notes)

        # Should mention Gov. Code § 65915
        assert "65915" in notes_text or "Density Bonus Law" in notes_text

    def test_concessions_documented(self, r2_parcel):
        """Test that concessions are documented in notes."""
        base_scenario = analyze_base_zoning(r2_parcel)
        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=20,  # 2 concessions
            income_level="low"
        )

        notes_text = " ".join(bonus_scenario.notes).lower()
        assert "concession" in notes_text

    def test_scenario_name_descriptive(self, r2_parcel):
        """Test that scenario name is descriptive."""
        base_scenario = analyze_base_zoning(r2_parcel)
        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=15,
            income_level="very_low"
        )

        # Should include affordability percentage
        assert "15%" in bonus_scenario.scenario_name
        assert "Density Bonus" in bonus_scenario.scenario_name
```

### Edge Case Testing

```python
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_exactly_at_threshold(self, r2_parcel):
        """Test exactly at 5% affordability threshold."""
        base_scenario = analyze_base_zoning(r2_parcel)
        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=5.0,
            income_level="very_low"
        )

        assert bonus_scenario is not None
        assert bonus_scenario.max_units > base_scenario.max_units

    def test_just_under_threshold(self, r2_parcel):
        """Test just under 5% affordability threshold."""
        base_scenario = analyze_base_zoning(r2_parcel)
        bonus_scenario = apply_density_bonus(
            base_scenario,
            r2_parcel,
            affordability_pct=4.9,
            income_level="very_low"
        )

        assert bonus_scenario is None

    def test_zero_base_units(self):
        """Test handling of zero base units."""
        # Create parcel that would result in 0 units
        tiny_parcel = ParcelBase(
            apn="TEST",
            address="Test",
            city="Test",
            county="Test",
            zip_code="00000",
            lot_size_sqft=100.0,  # Tiny lot
            zoning_code="R1",
            existing_units=0,
            existing_building_sqft=0
        )

        base_scenario = analyze_base_zoning(tiny_parcel)
        # Should gracefully handle zero or very low units
        assert base_scenario.max_units >= 0
```

## API Endpoint Testing

```python
# tests/test_api_endpoints.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAnalyzeEndpoint:
    """Tests for /api/v1/analyze endpoint."""

    def test_analyze_returns_scenarios(self):
        """Test that analyze endpoint returns base + alternative scenarios."""
        request_data = {
            "parcel": {
                "apn": "123-456-789",
                "address": "123 Main St",
                "city": "Santa Monica",
                "county": "Los Angeles",
                "zip_code": "90401",
                "lot_size_sqft": 5000,
                "zoning_code": "R1",
                "existing_units": 0,
                "existing_building_sqft": 0
            },
            "include_sb9": True,
            "include_density_bonus": True
        }

        response = client.post("/api/v1/analyze", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "base_scenario" in data
        assert "alternative_scenarios" in data
        assert "recommended_scenario" in data

    def test_validation_errors(self):
        """Test that invalid requests return validation errors."""
        request_data = {
            "parcel": {
                "apn": "123-456-789",
                # Missing required fields
            }
        }

        response = client.post("/api/v1/analyze", json=request_data)

        assert response.status_code == 422  # Validation error


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_returns_healthy(self):
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "version" in data
        assert "features" in data
```

## Coverage Best Practices

### Aiming for Coverage

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# View terminal summary
# Coverage report in htmlcov/index.html

# Target coverage: 80%+ for business logic
# Focus on:
# - State law implementations (app/rules/state_law/)
# - Base zoning calculations (app/rules/base_zoning.py)
# - API endpoints (app/api/)

# Lower priority for coverage:
# - Configuration (app/core/config.py)
# - Utilities (app/utils/)
# - Main entry point (app/main.py)
```

### Coverage Exclusions

```python
# Add pragma comments for intentionally uncovered code

def debug_only_function():
    """Debug function - not covered by tests."""
    pass  # pragma: no cover


if settings.DEBUG:  # pragma: no cover
    # Debug-only code
    print("Debug mode enabled")
```

## Test Data Patterns

### Creating Test Parcels

```python
def create_test_parcel(**overrides) -> ParcelBase:
    """
    Create test parcel with default values and overrides.

    Example:
        parcel = create_test_parcel(lot_size_sqft=10000, zoning_code="R2")
    """
    defaults = {
        "apn": "000-000-000",
        "address": "Test Address",
        "city": "Test City",
        "county": "Test County",
        "zip_code": "00000",
        "lot_size_sqft": 5000.0,
        "zoning_code": "R1",
        "existing_units": 0,
        "existing_building_sqft": 0,
    }
    defaults.update(overrides)
    return ParcelBase(**defaults)


def test_with_custom_parcel():
    """Test using custom parcel."""
    parcel = create_test_parcel(
        lot_size_sqft=15000,
        zoning_code="R4",
        is_historic_property=True
    )

    # Test logic
    assert parcel.lot_size_sqft == 15000
```

## Common Test Patterns

### Testing Optional Behavior

```python
def test_near_transit_eliminates_parking(self, r2_parcel):
    """Test AB 2097 near-transit parking elimination."""
    r2_parcel.near_transit = True

    base_scenario = analyze_base_zoning(r2_parcel)
    bonus_scenario = apply_density_bonus(
        base_scenario,
        r2_parcel,
        affordability_pct=10,
        income_level="low"
    )

    # Parking should be 0
    assert bonus_scenario.parking_spaces_required == 0


def test_not_near_transit_has_parking(self, r2_parcel):
    """Test parking required when not near transit."""
    r2_parcel.near_transit = False

    base_scenario = analyze_base_zoning(r2_parcel)
    bonus_scenario = apply_density_bonus(
        base_scenario,
        r2_parcel,
        affordability_pct=10,
        income_level="low"
    )

    # Parking should be > 0
    assert bonus_scenario.parking_spaces_required > 0
```

### Testing Calculations with Tolerance

```python
def test_acreage_calculation_with_tolerance(self, r2_parcel):
    """Test acreage-based calculation with floating point tolerance."""
    # Allow for floating point rounding
    acres = r2_parcel.lot_size_sqft / 43560
    expected_units = acres * 17  # 17 units/acre

    scenario = analyze_base_zoning(r2_parcel)

    # Use pytest.approx for floating point comparison
    assert scenario.max_units == pytest.approx(int(expected_units), abs=1)
```

## Debugging Tests

```bash
# Run with print statements visible
pytest tests/test_density_bonus.py -v -s

# Run with pdb (Python debugger)
pytest tests/test_density_bonus.py --pdb

# Drop into pdb on first failure
pytest tests/test_density_bonus.py -x --pdb

# Show local variables on failure
pytest tests/test_density_bonus.py -l

# Verbose output with extra test summary
pytest tests/test_density_bonus.py -vv

# Show slowest 10 tests
pytest tests/ --durations=10
```

## Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** that explain what's being tested
3. **Docstrings** on all test functions explaining the scenario
4. **Statute references** in test docstrings for law-specific tests
5. **Use fixtures** for reusable test data
6. **Parametrize** tests for multiple similar scenarios
7. **Test edge cases** (boundaries, thresholds, nulls)
8. **Test error conditions** (invalid inputs, exceptions)
9. **Keep tests independent** (no test depends on another)
10. **Fast tests** (avoid slow operations, use mocking for external APIs)

## Related Documentation

- [Backend CLAUDE.md](../app/CLAUDE.md) - Backend implementation patterns
- [Root CLAUDE.md](../CLAUDE.md) - Overall project context
- pytest documentation: https://docs.pytest.org/
