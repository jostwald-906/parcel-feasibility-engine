# Economic Feasibility Models Summary

## Overview

Comprehensive Pydantic v2 models created for the economic feasibility module in `/app/models/economic_feasibility.py`.

**File**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/app/models/economic_feasibility.py`
**Tests**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/tests/test_economic_feasibility_models.py`
**Test Results**: 27 tests, all passing ✓

## Models Created (15 total)

### 1. Input Models - Economic Assumptions

#### `EconomicAssumptions`
**Purpose**: User-customizable assumptions for NPV/IRR calculations

**Key Fields**:
- `discount_rate`: Annual discount rate (default 12%, range 1-30%)
- `risk_free_rate`: Optional 10-year Treasury from FRED DGS10
- `market_risk_premium`: Market risk premium for CAPM (default 6%)
- `project_risk_premium`: Project-specific risk (default 2.5%)
- `cap_rate`: Exit capitalization rate (default 4.5%, range 3-8%)
- `location_factor`: RAND Corporation cost multiplier (default 1.0, range 0.5-2.0)
- `quality_factor`: Construction quality adjustment (default 1.0, range 0.8-1.2)
- `vacancy_rate`: Expected vacancy/collection loss (default 7%)
- `tax_rate`: Property tax rate (default 1.2% = Prop 13 base + local)
- `rent_growth_rate`: Annual rent growth (default 3%)
- `expense_growth_rate`: Annual expense growth (default 2.5%)
- `use_ccci`: Boolean to apply CCCI escalation (default False)
- `source_references`: Dict of data source citations

**Validation**:
- All rates use decimal format (0.12 = 12%)
- Range constraints: `ge=`, `le=` for all numeric fields
- Default values from industry standards

**Design Decision**: Used RAND Corporation location factors instead of city-specific indices for broader applicability across California.

---

### 2. Construction Cost Models

#### `ConstructionInputs`
**Purpose**: Inputs for cost estimator service

**Key Fields**:
- `total_buildable_sf`: Buildable square footage (gt=0)
- `num_units`: Number of units (gt=0)
- `construction_type`: "wood_frame", "concrete", or "steel"
- `construction_duration_months`: Construction timeline (gt=0, le=60)
- `predevelopment_duration_months`: Entitlement/design timeline (gt=0, le=48)
- `location_factor`: Cost multiplier (from EconomicAssumptions)
- `permit_fees_per_unit`: Municipal fees (default $15k)
- `use_wage_adjustment`: Apply prevailing wage premium (default False)

**Validation**:
- Custom validator for `construction_type` (must be in valid set)
- Positive value constraints on SF and units
- Reasonable duration limits (max 60 months construction, 48 predevelopment)

#### `ConstructionCostEstimate`
**Purpose**: Output from cost estimator with detailed breakdown

**Key Fields**:
- `hard_costs`: Direct construction costs
- `soft_costs`: Total soft costs (A&E + permits + financing + legal + contingency)
- Detailed soft cost breakdown:
  - `architecture_engineering`: ~5-8% of hard costs
  - `permits_and_fees`: Municipal fees
  - `construction_financing`: Loan interest during construction
  - `legal_consulting`: Legal, environmental, consulting
  - `contingency`: ~5-10% of hard costs
- `total_cost`: Hard + soft costs
- `cost_per_unit`: Total ÷ units
- `cost_per_sf`: Total ÷ buildable SF
- `escalation_factors`: Dict of applied adjustments (materials, labor, wage, location)
- `source_notes`: Audit trail with data sources and assumptions

**Design Decision**: Used simple float types instead of Decimal for ease of integration with numpy/pandas in downstream services.

---

### 3. Revenue Projection Models

#### `RevenueInputs`
**Purpose**: Inputs for revenue estimator (HUD FMR/SAFMR + AMI-based rents)

**Key Fields**:
- `parcel_zip`: 5-digit ZIP for SAFMR lookup (regex validated)
- `county`: County name for AMI limits
- `market_units`: Number of market-rate units (ge=0)
- `affordable_units`: Number of affordable units (ge=0)
- `unit_mix`: Dict[int, int] of {bedrooms: count} (0=studio through 5BR)
- `use_safmr`: Use Small Area FMR vs metro-wide (default True)
- `quality_factor`: Rent quality adjustment (default 1.0, range 0.8-1.3)

**Validation**:
- ZIP code regex: `^\d{5}$`
- Unit mix validator: bedroom counts must be 0-5
- Non-negative unit counts

#### `RevenueProjection`
**Purpose**: Annual revenue and NOI output from estimator

**Key Fields**:
- `annual_gross_income`: Total gross rental income
- `vacancy_loss`: Vacancy and collection loss
- `effective_gross_income`: Gross - vacancy
- `operating_expenses`: Annual OpEx
- `annual_noi`: Net Operating Income (EGI - OpEx)
- `noi_per_unit`: NOI ÷ units
- `market_rent_roll`: Dict of market rents by unit type ("0BR", "1BR", etc.)
- `affordable_rent_roll`: Dict of affordable rents ("0BR_50AMI", "1BR_60AMI", etc.)
- `expense_breakdown`: Dict of OpEx by category (management, maintenance, utilities, insurance, tax, reserves, other)
- `source_notes`: FMR/AMI sources, OpEx basis, date

**Design Decision**: Separated market and affordable rent rolls for clarity. Affordable rent keys include AMI percentage for transparency.

---

### 4. Timeline and Cash Flow Models

#### `TimelineInputs`
**Purpose**: Development timeline for cash flow projection

**Key Fields**:
- `predevelopment_months`: Entitlements, design, permitting (gt=0, le=48)
- `construction_months`: Construction duration (gt=0, le=60)
- `lease_up_months`: Lease-up to stabilized occupancy (gt=0, le=24)
- `operating_years`: Operating period for projection (default 10, gt=0, le=30)

#### `CashFlow`
**Purpose**: Period-by-period cash flow

**Key Fields**:
- `period`: Period number (0 = start)
- `period_type`: "predevelopment", "construction", "lease_up", or "operations"
- `revenue`: Revenue in period
- `operating_expenses`: OpEx in period (ge=0)
- `capital_expenditure`: CapEx in period (ge=0)
- `net_cash_flow`: Revenue - OpEx - CapEx
- `cumulative_cash_flow`: Running total from period 0

**Validation**:
- Custom validator for `period_type` (must be in valid set)

---

### 5. Financial Metrics Models

#### `FinancialMetrics`
**Purpose**: Core financial analysis outputs (NPV, IRR, payback, exit value)

**Key Fields**:
- `npv`: Net Present Value at discount rate (NPV > 0 = feasible)
- `irr`: Internal Rate of Return (decimal, e.g., 0.15 = 15%)
- `payback_period_years`: Years to cumulative CF > 0 (ge=0)
- `profitability_index`: NPV ÷ initial investment (PI > 1.0 = positive NPV)
- `return_on_cost`: Year 1 NOI ÷ total cost (compare to cap_rate)
- `exit_value`: Exit value = Year N NOI ÷ cap_rate (ge=0)
- `total_cash_flows`: List[CashFlow] complete schedule

**Design Decision**: Included both NPV/IRR (time-adjusted) and RoC/exit value (direct metrics) for comprehensive decision support.

---

### 6. Sensitivity Analysis Models

#### `SensitivityInput`
**Purpose**: Define variables to test in one-way sensitivity

**Key Fields**:
- `variable_name`: Variable to test (e.g., "cost_per_sf", "rent_per_sf", "cap_rate")
- `base_value`: Base case value
- `delta_percent`: % change to test (default 0.20 = ±20%, range 0-100%)

#### `TornadoResult`
**Purpose**: One-way sensitivity result for tornado chart

**Key Fields**:
- `variable`: Variable name
- `downside_npv`: NPV with -delta% change
- `upside_npv`: NPV with +delta% change
- `impact`: Absolute NPV impact = |upside - downside| (for sorting)

**Design Decision**: Impact calculation enables automatic sorting of tornado chart by sensitivity magnitude.

#### `MonteCarloInputs`
**Purpose**: Monte Carlo simulation parameters

**Key Fields**:
- `iterations`: Number of iterations (default 10k, range 1k-100k)
- `cost_per_sf_std`: Standard deviation of cost/SF (normal distribution)
- `rent_growth_std`: Standard deviation of rent growth (normal distribution)
- `cap_rate_min`, `cap_rate_mode`, `cap_rate_max`: Triangular distribution parameters
- `delay_months_mean`, `delay_months_std`: Construction delay (normal distribution)
- `random_seed`: Optional seed for reproducible testing

**Validation**:
- Iteration bounds: 1,000-100,000
- Cap rate ordering validated in downstream service

#### `MonteCarloResult`
**Purpose**: Monte Carlo simulation output

**Key Fields**:
- `probability_npv_positive`: P(NPV > 0) (range 0-1)
- `mean_npv`: Mean NPV across iterations
- `std_npv`: Standard deviation of NPV (ge=0)
- `percentiles`: Dict with p10, p25, p50 (median), p75, p90
- `histogram_bins`: List[float] for NPV distribution visualization
- `histogram_counts`: List[int] counts per bin

**Design Decision**: Used percentiles instead of confidence intervals for easier interpretation by non-statisticians.

#### `SensitivityAnalysis`
**Purpose**: Combined sensitivity results

**Key Fields**:
- `tornado`: List[TornadoResult] sorted by impact (descending)
- `monte_carlo`: MonteCarloResult

---

### 7. Complete Feasibility Models

#### `FeasibilityAnalysis`
**Purpose**: Complete analysis output integrating all components

**Key Fields**:
- `scenario_name`: Development scenario name
- `parcel_apn`: Parcel APN
- `construction_cost_estimate`: ConstructionCostEstimate
- `revenue_projection`: RevenueProjection
- `financial_metrics`: FinancialMetrics
- `sensitivity_analysis`: SensitivityAnalysis
- `decision_recommendation`: String recommendation ("Recommended - Strong Feasibility", "Recommended with Caution", "Not Recommended", "Further Analysis Required")
- `source_notes`: Comprehensive audit trail (cost_sources, revenue_sources, assumptions, caveats)
- `analysis_timestamp`: datetime (default=now)

**JSON Encoding**:
- Custom encoder for datetime → ISO string

#### `FeasibilityRequest`
**Purpose**: API request model

**Key Fields**:
- `parcel_apn`: Parcel APN
- `scenario_name`: Scenario name
- `units`: Number of units (gt=0)
- `buildable_sf`: Buildable SF (gt=0)
- `timeline`: TimelineInputs
- `assumptions`: EconomicAssumptions (uses defaults if not provided)
- `revenue_inputs`: Optional[RevenueInputs] (derived from parcel if not provided)
- `run_sensitivity`: Boolean (default True)
- `run_monte_carlo`: Boolean (default True)

**Design Decision**: Made revenue_inputs optional to allow automatic derivation from parcel location data.

---

## Validation Rules Implemented

### Range Constraints
- **Discount rate**: 1-30% (ge=0.01, le=0.30)
- **Location factor**: 0.5-2.0 (ge=0.5, le=2.0)
- **Quality factor**: 0.8-1.2 (ge=0.8, le=1.2)
- **Vacancy rate**: 0-20% (ge=0.0, le=0.20)
- **Cap rate**: 3-8% (ge=0.03, le=0.08)
- **Construction duration**: Max 60 months (le=60)
- **Predevelopment duration**: Max 48 months (le=48)
- **Monte Carlo iterations**: 1,000-100,000 (ge=1000, le=100000)

### Pattern Validation
- **ZIP code**: `^\d{5}$` (exactly 5 digits)

### Custom Validators
- **construction_type**: Must be in {"wood_frame", "concrete", "steel"}
- **period_type**: Must be in {"predevelopment", "construction", "lease_up", "operations"}
- **unit_mix bedrooms**: Must be 0-5 (studio through 5BR)

### Positive/Non-Negative Constraints
- All costs: `ge=0`
- Units, SF: `gt=0` (strictly positive)
- Durations: `gt=0` (strictly positive)
- Standard deviations: `ge=0`

---

## Example JSON

### FeasibilityRequest Example
**File**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/examples/feasibility_request_example.json`

```json
{
  "parcel_apn": "4293-021-012",
  "scenario_name": "SB 9 Lot Split + Density Bonus (35% Affordable)",
  "units": 30,
  "buildable_sf": 25000.0,
  "timeline": {
    "predevelopment_months": 12,
    "construction_months": 18,
    "lease_up_months": 6,
    "operating_years": 10
  },
  "assumptions": {
    "discount_rate": 0.12,
    "location_factor": 1.3,
    "cap_rate": 0.045
  },
  "revenue_inputs": {
    "parcel_zip": "90401",
    "county": "Los Angeles",
    "market_units": 20,
    "affordable_units": 10,
    "unit_mix": {
      "0": 5,
      "1": 15,
      "2": 8,
      "3": 2
    }
  },
  "run_sensitivity": true
}
```

### FeasibilityAnalysis Example
**File**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/examples/feasibility_analysis_example.json`

**Key Highlights**:
- Total cost: $7.5M ($250k/unit, $300/SF)
- Annual NOI: $502k ($16,740/unit)
- NPV: $2.156M (positive = feasible)
- IRR: 16.5% (exceeds 12% hurdle rate)
- Payback: 8.2 years
- Return on Cost: 6.7% (vs. 4.5% cap rate = value creation)
- Exit value: $11.16M (Year 10 NOI ÷ 4.5% cap)
- Monte Carlo: 87% probability NPV > 0
- Decision: "Recommended with Caution - Moderate Feasibility"

**Tornado Chart** (sensitivity ranked by impact):
1. Cost per SF: ±$3M impact
2. Rent per SF: ±$2.2M impact
3. Cap rate: ±$1.7M impact
4. Vacancy rate: ±$1M impact
5. Construction duration: ±$700k impact
6. Discount rate: ±$600k impact

---

## Design Decisions and Trade-offs

### 1. Float vs Decimal
**Decision**: Used `float` instead of `Decimal` for all monetary values.

**Rationale**:
- Simpler integration with numpy/pandas in downstream services
- FastAPI JSON serialization easier with float
- Precision adequate for planning-level feasibility (not penny-exact accounting)

**Trade-off**: Potential for floating-point precision issues in very large calculations (mitigated by using dollars, not cents).

### 2. Separate Market/Affordable Rent Rolls
**Decision**: Split rent rolls into `market_rent_roll` and `affordable_rent_roll`.

**Rationale**:
- Clarity for users (explicitly shows market vs affordable units)
- Supports reporting/compliance (e.g., density bonus verification)
- Affordable rent keys include AMI % (e.g., "1BR_50AMI") for transparency

**Trade-off**: Slightly more complex data structure, but worth it for clarity.

### 3. Percentiles over Confidence Intervals
**Decision**: Used percentiles (p10, p25, p50, p75, p90) instead of 95% CI in Monte Carlo.

**Rationale**:
- More intuitive for non-statisticians
- Provides richer distribution view (5 points vs 2)
- Industry standard in real estate pro formas

### 4. Optional revenue_inputs
**Decision**: Made `revenue_inputs` optional in `FeasibilityRequest`.

**Rationale**:
- Allows automatic derivation from parcel ZIP/county if not provided
- Reduces user input burden for simple analyses
- Advanced users can override with custom assumptions

**Trade-off**: Requires downstream service to handle None case.

### 5. source_notes in Every Output Model
**Decision**: Included `source_notes: Dict[str, Any]` in all output models.

**Rationale**:
- Transparency and auditability critical for financial analysis
- Enables users to verify assumptions and data sources
- Supports documentation for lenders, investors, regulators

**Trade-off**: Larger JSON payloads, but essential for credibility.

### 6. RAND Location Factors
**Decision**: Used RAND Corporation location factors instead of city-specific indices.

**Rationale**:
- RAND provides peer-reviewed, publicly available data
- Covers all California regions consistently
- Simpler to maintain than custom city indices

**Trade-off**: May be less precise than hyperlocal data, but acceptable for feasibility-level analysis.

### 7. Default Values from Industry Standards
**Decision**: Provided extensive defaults (12% discount rate, 4.5% cap rate, 7% vacancy, etc.).

**Rationale**:
- Reduces input burden for users
- Defaults based on industry standards (CBRE, NCREIF, RAND)
- Users can override any default with custom values

**Trade-off**: Risk of users accepting defaults without thinking, but well-documented sources mitigate this.

### 8. Triangular Distribution for Cap Rate
**Decision**: Used triangular distribution (min/mode/max) for cap rate in Monte Carlo.

**Rationale**:
- Matches real estate underwriting practice (base/likely/worst case)
- Simpler to parameterize than normal distribution (no negative cap rates)
- Industry-standard approach (ARGUS, RealPage)

**Trade-off**: Less flexible than full distribution specification, but appropriate for feasibility stage.

---

## Integration Points

### Services to Build Next
1. **Cost Estimator Service** (`app/services/cost_estimator.py`):
   - Input: `ConstructionInputs`
   - Output: `ConstructionCostEstimate`
   - Uses RSMeans data + RAND factors + CCCI

2. **Revenue Estimator Service** (`app/services/revenue_estimator.py`):
   - Input: `RevenueInputs`
   - Output: `RevenueProjection`
   - Uses HUD FMR/SAFMR + HCD AMI calculator

3. **Financial Analysis Service** (`app/services/financial_analyzer.py`):
   - Inputs: `ConstructionCostEstimate`, `RevenueProjection`, `TimelineInputs`, `EconomicAssumptions`
   - Output: `FinancialMetrics`
   - Calculates NPV, IRR, payback, cash flows

4. **Sensitivity Analysis Service** (`app/services/sensitivity_analyzer.py`):
   - Inputs: Base case + `List[SensitivityInput]` + `MonteCarloInputs`
   - Output: `SensitivityAnalysis`
   - Runs tornado chart + Monte Carlo

5. **Feasibility Orchestrator** (`app/services/feasibility_orchestrator.py`):
   - Input: `FeasibilityRequest`
   - Output: `FeasibilityAnalysis`
   - Orchestrates all services + generates decision recommendation

### API Endpoint
**POST /api/v1/feasibility/analyze**
- Request: `FeasibilityRequest`
- Response: `FeasibilityAnalysis`
- 200 OK: Analysis complete
- 422 Unprocessable Entity: Validation errors
- 500 Internal Server Error: Calculation failures

---

## Model Summary Table

| Model | Purpose | Key Validations | Example Use Case |
|-------|---------|-----------------|------------------|
| `EconomicAssumptions` | User inputs for NPV/IRR | Discount rate 1-30%, location factor 0.5-2.0 | Set 12% hurdle rate, 1.3 Santa Monica factor |
| `ConstructionInputs` | Cost estimator inputs | Construction type enum, positive SF/units | 30 units, 25k SF, wood frame, 18mo construction |
| `ConstructionCostEstimate` | Cost estimator output | All costs ≥ 0 | $7.5M total, $250k/unit, $300/SF |
| `RevenueInputs` | Revenue estimator inputs | ZIP regex, unit mix 0-5BR | 90401 ZIP, LA County, 20 market + 10 affordable |
| `RevenueProjection` | Revenue estimator output | NOI can be negative | $502k NOI, $16.7k/unit |
| `TimelineInputs` | Development timeline | Positive months, max 60/48 | 12mo predevelopment, 18mo construction, 6mo lease-up |
| `CashFlow` | Period cash flow | Period type enum | Period 0: -$750k predevelopment spend |
| `FinancialMetrics` | NPV/IRR results | Positive exit value, payback ≥ 0 | NPV $2.156M, IRR 16.5%, payback 8.2yr |
| `SensitivityInput` | Tornado chart variable | Delta % 0-100% | Cost/SF ±20% |
| `TornadoResult` | Tornado chart bar | Impact = max - min NPV | Cost/SF: $3M impact (highest) |
| `MonteCarloInputs` | Monte Carlo parameters | Iterations 1k-100k | 10k iterations, cost std $30/SF |
| `MonteCarloResult` | Monte Carlo output | Probability 0-1 | 87% P(NPV>0), p50 $2.1M |
| `SensitivityAnalysis` | Combined sensitivity | Tornado + Monte Carlo | 6 tornado bars + histogram |
| `FeasibilityAnalysis` | Complete analysis | All nested validations | Full output with recommendation |
| `FeasibilityRequest` | API request | All nested validations | POST /api/v1/feasibility/analyze |

---

## Test Coverage

**File**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/tests/test_economic_feasibility_models.py`

**Test Classes** (27 tests total):
- `TestEconomicAssumptions`: 5 tests (defaults, custom values, validations)
- `TestConstructionInputs`: 3 tests (valid inputs, type validation, positive values)
- `TestRevenueInputs`: 3 tests (valid inputs, ZIP validation, unit mix validation)
- `TestTimelineInputs`: 2 tests (valid timeline, positive values)
- `TestCashFlow`: 2 tests (valid flow, period type validation)
- `TestMonteCarloInputs`: 2 tests (valid inputs, iteration bounds)
- `TestFeasibilityRequest`: 3 tests (valid request, default assumptions, custom assumptions)
- `TestJSONSerialization`: 3 tests (assumptions, request, analysis datetime)
- `TestModelExamples`: 4 tests (validate all json_schema_extra examples)

**Results**: ✓ 27 passed, 0 failed

**Coverage**: 100% of `app/models/economic_feasibility.py`

---

## Next Steps

1. **Build Cost Estimator Service**:
   - Implement RSMeans base costs by construction type
   - Apply RAND location factors
   - Calculate soft costs (5-8% A&E, permit fees, financing, contingency)
   - Apply CCCI escalation if enabled
   - Apply prevailing wage adjustment if required

2. **Build Revenue Estimator Service**:
   - Integrate HUD FMR/SAFMR client
   - Use existing AMI calculator for affordable rents
   - Calculate OpEx (40% of EGI industry standard)
   - Break down expenses by category
   - Apply quality factor to market rents

3. **Build Financial Analyzer Service**:
   - Generate period-by-period cash flows
   - Calculate NPV using discount rate
   - Calculate IRR via Newton-Raphson or numpy.irr
   - Calculate payback period
   - Calculate profitability index and RoC
   - Calculate exit value using cap rate

4. **Build Sensitivity Analyzer Service**:
   - Implement one-way sensitivity (tornado chart)
   - Implement Monte Carlo with triangular/normal distributions
   - Calculate percentiles and histogram
   - Sort tornado by impact

5. **Build Feasibility Orchestrator**:
   - Orchestrate all services
   - Generate decision recommendation based on thresholds:
     - NPV > $1M + P(NPV>0) > 85% = "Strong Feasibility"
     - NPV > $0 + P(NPV>0) > 70% = "Recommended with Caution"
     - NPV < $0 or P(NPV>0) < 50% = "Not Recommended"
     - Otherwise = "Further Analysis Required"
   - Populate comprehensive source_notes

6. **Create API Endpoint**:
   - POST /api/v1/feasibility/analyze
   - Validate FeasibilityRequest
   - Call orchestrator
   - Return FeasibilityAnalysis
   - Add to FastAPI app with appropriate tags

7. **Frontend Integration**:
   - Create TypeScript interfaces matching Pydantic models
   - Build feasibility analysis UI component
   - Visualize tornado chart (horizontal bars sorted by impact)
   - Visualize Monte Carlo histogram
   - Display cash flow table
   - Display decision recommendation with color coding

---

## Files Created

1. **Models**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/app/models/economic_feasibility.py`
2. **Tests**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/tests/test_economic_feasibility_models.py`
3. **Examples**:
   - `/Users/Jordan_Ostwald/Parcel Feasibility Engine/examples/feasibility_request_example.json`
   - `/Users/Jordan_Ostwald/Parcel Feasibility Engine/examples/feasibility_analysis_example.json`
4. **Updated**: `/Users/Jordan_Ostwald/Parcel Feasibility Engine/app/models/__init__.py` (exports)

---

## References

**Data Sources**:
- FRED DGS10: https://fred.stlouisfed.org/series/DGS10
- RAND Corporation: California construction cost indices
- California Proposition 13 (1978): Property tax limits
- HCD Income Limits: https://www.hcd.ca.gov/grants-and-funding/income-limits
- HUD FMR: https://www.huduser.gov/portal/datasets/fmr.html
- RSMeans: Commercial construction cost data

**Industry Standards**:
- 12% discount rate: Typical real estate developer hurdle
- 4.5% cap rate: CBRE/CoStar 2025 multifamily Class A metros
- 7% vacancy: NCREIF multifamily historical average
- 40% OpEx: Industry rule of thumb for Class A multifamily
- 30% of income: HUD/HCD affordable rent standard

**Statutory References**:
- Gov. Code § 65915: Density Bonus Law (concessions, parking)
- Gov. Code § 65852.21: SB 9 (ministerial approval, timeline)
- Gov. Code § 65913.4: SB 35 (streamlining, affordability)
- Gov. Code § 65913.5: AB 2011 (corridors, labor standards)
