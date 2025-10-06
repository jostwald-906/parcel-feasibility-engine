# Testing Guide

## Table of Contents

1. [Overview](#overview)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [Running Tests](#running-tests)
5. [Writing Tests](#writing-tests)
6. [Coverage Requirements](#coverage-requirements)
7. [Continuous Integration](#continuous-integration)

## Overview

The Santa Monica Parcel Feasibility Engine uses comprehensive testing to ensure reliability and correctness of zoning calculations and state law applications.

### Testing Stack

**Backend:**
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support

**Frontend:**
- `Jest` - Testing framework
- `React Testing Library` - Component testing
- `@testing-library/user-event` - User interaction simulation

## Backend Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_base_zoning.py      # Base zoning calculations
├── test_sb9_phase1.py       # SB9 eligibility tests
├── test_sb9_phase2.py       # SB9 scenarios
├── test_sb9_apply_api.py    # SB9 API integration
├── test_sb35.py             # SB35 streamlining
├── test_ab2011_standards.py # AB2011 conversions
├── test_ab2097.py           # AB2097 parking
├── test_density_bonus.py    # Density bonus calculations
└── test_overlays.py         # Overlay districts
```

### Running Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_sb9_phase1.py

# Run with coverage report
pytest --cov=app --cov-report=html

# Run tests matching a pattern
pytest -k "sb9"

# Run specific markers
pytest -m "unit"
pytest -m "integration"

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Markers

Tests are organized with markers for targeted execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.sb9` - SB9 related tests
- `@pytest.mark.sb35` - SB35 related tests
- `@pytest.mark.ab2011` - AB2011 related tests
- `@pytest.mark.density_bonus` - Density bonus tests

Example:
```python
@pytest.mark.sb9
@pytest.mark.unit
def test_sb9_eligibility(r1_parcel):
    result = check_sb9_eligibility(r1_parcel)
    assert result.eligible is True
```

### Fixtures

Common test fixtures are defined in `conftest.py`:

```python
# Standard parcel fixtures
- r1_parcel              # Single-family residential
- r2_parcel              # Low-density multi-family
- dcp_parcel             # Downtown Community Plan
- coastal_parcel         # Coastal zone
- historic_parcel        # Historic district
- transit_adjacent_parcel # Near major transit
- commercial_parcel      # Commercial zone
- small_r1_parcel        # Below minimum lot size
- large_r4_parcel        # High-density residential
```

## Frontend Testing

### Test Structure

```
frontend/
├── __tests__/
│   ├── lib/
│   │   ├── api-client.test.ts
│   │   └── gis-utils.test.ts
│   └── components/
│       ├── ParcelForm.test.tsx
│       ├── ParcelMap.test.tsx
│       └── ScenarioComparison.test.tsx
├── jest.config.js
└── jest.setup.js
```

### Running Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Type checking
npm run type-check
```

### Writing Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { ParcelForm } from '@/components/ParcelForm'

describe('ParcelForm', () => {
  test('renders form fields', () => {
    render(<ParcelForm />)

    expect(screen.getByLabelText(/APN/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Lot Size/i)).toBeInTheDocument()
  })

  test('validates APN format', async () => {
    const { user } = render(<ParcelForm />)

    const apnInput = screen.getByLabelText(/APN/i)
    await user.type(apnInput, 'invalid')

    expect(screen.getByText(/Invalid APN format/i)).toBeInTheDocument()
  })
})
```

## Running Tests

### Local Development

**Backend:**
```bash
# From project root
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Fast mode (skip slow tests)
pytest -m "not slow"
```

**Frontend:**
```bash
# From frontend directory
cd frontend
npm test

# Or from project root
npm --prefix frontend test
```

### CI/CD Pipeline

Tests run automatically on:
- Pull requests to `main` or `develop` branches
- Pushes to `main` or `develop` branches

See `.github/workflows/ci.yml` for pipeline configuration.

## Writing Tests

### Backend Test Example

```python
import pytest
from app.rules.sb9 import check_sb9_eligibility, apply_sb9_standards
from app.models.parcel import ParcelBase

def test_sb9_eligible_r1_parcel(r1_parcel):
    """Test SB9 eligibility for standard R1 parcel."""
    result = check_sb9_eligibility(r1_parcel)

    assert result.eligible is True
    assert "urban lot split" in result.reason.lower()

def test_sb9_ineligible_small_lot():
    """Test SB9 ineligibility for undersized lot."""
    parcel = ParcelBase(
        apn="123-456-789",
        lot_size_sqft=2000,  # Too small
        zoning_code="R1",
        # ... other required fields
    )

    result = check_sb9_eligibility(parcel)

    assert result.eligible is False
    assert "lot size" in result.reason.lower()

@pytest.mark.integration
def test_sb9_api_endpoint(client, r1_parcel):
    """Test SB9 via API endpoint."""
    response = client.post("/api/v1/analyze", json={
        "parcel": r1_parcel.dict(),
        "include_sb9": True
    })

    assert response.status_code == 200
    data = response.json()
    assert any(s["legal_basis"] == "SB9" for s in data["alternative_scenarios"])
```

### Frontend Test Example

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ParcelAnalysis } from '@/components/ParcelAnalysis'

describe('ParcelAnalysis', () => {
  test('displays analysis results', async () => {
    const mockParcel = {
      apn: '123-456-789',
      zoning_code: 'R1',
      lot_size_sqft: 6000
    }

    render(<ParcelAnalysis parcel={mockParcel} />)

    await waitFor(() => {
      expect(screen.getByText(/Base Scenario/i)).toBeInTheDocument()
    })
  })

  test('shows SB9 scenario when eligible', async () => {
    const eligibleParcel = {
      apn: '123-456-789',
      zoning_code: 'R1',
      lot_size_sqft: 6000
    }

    render(<ParcelAnalysis parcel={eligibleParcel} />)

    await waitFor(() => {
      expect(screen.getByText(/SB9/i)).toBeInTheDocument()
    })
  })
})
```

## Coverage Requirements

### Backend Coverage

- **Minimum:** 80% overall coverage
- **Critical modules:** 100% coverage required
  - `app/rules/` - All rule modules
  - `app/api/` - API endpoints
  - `app/models/` - Data models

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### Frontend Coverage

- **Minimum:** 70% overall coverage
- **Component tests:** Focus on user interactions
- **Utility tests:** 100% for calculation utilities

```bash
# Generate coverage report
cd frontend
npm run test:coverage

# View report
open coverage/lcov-report/index.html
```

## Continuous Integration

### GitHub Actions Workflows

**CI Pipeline (`.github/workflows/ci.yml`):**
- Backend tests with Python 3.11 and 3.12
- Frontend tests with Node 18
- Integration tests with PostgreSQL/PostGIS
- Coverage reporting to Codecov

**Linting (`.github/workflows/lint.yml`):**
- Python: Black, Ruff, mypy
- Frontend: ESLint, TypeScript compiler
- Security scanning with Trivy
- Dependency audits

### Running CI Locally

```bash
# Backend tests (simulating CI)
python -m pip install -r requirements.txt
pytest --cov=app --cov-report=xml --cov-fail-under=80

# Frontend tests (simulating CI)
cd frontend
npm ci
npm run type-check
npm run lint
npm test -- --coverage --passWithNoTests
npm run build
```

## Best Practices

### Backend Testing

1. **Use fixtures** for common test data
2. **Mark tests** with appropriate markers
3. **Test edge cases** - zero values, negative numbers, boundary conditions
4. **Mock external services** - GIS endpoints, geocoding APIs
5. **Document test purpose** in docstrings
6. **Test both success and failure** paths

### Frontend Testing

1. **Query by accessibility** - Use `getByRole`, `getByLabelText`
2. **User-centric tests** - Test from user perspective
3. **Avoid implementation details** - Don't test internal state
4. **Mock API calls** - Use MSW or jest mocks
5. **Test loading states** - Async operations
6. **Test error handling** - Network failures, validation errors

### General Guidelines

- **Keep tests isolated** - No shared state
- **Make tests deterministic** - Same result every time
- **Write readable tests** - Clear assertions, good naming
- **Test one thing** - Single responsibility per test
- **Fast execution** - Tests should run quickly
- **Meaningful assertions** - Not just `expect(true).toBe(true)`

## Troubleshooting

### Common Issues

**Backend:**

```bash
# Import errors
# Solution: Install package in editable mode
pip install -e .

# Database connection errors
# Solution: Start PostgreSQL container
docker-compose up -d postgres

# Coverage not collected
# Solution: Ensure pytest-cov is installed
pip install pytest-cov
```

**Frontend:**

```bash
# Module resolution errors
# Solution: Check jest.config.js moduleNameMapper

# Async test timeouts
# Solution: Increase timeout or use waitFor

# DOM not available
# Solution: Use jest-environment-jsdom
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Jest Documentation](https://jestjs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
