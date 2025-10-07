# Economic Feasibility Module

**PhD-level economic analysis for California housing development projects**

## Overview

The Economic Feasibility Module provides institutional-grade financial analysis for residential development projects, integrating free public data sources with rigorous economic methodologies.

### Key Features

✅ **Construction Cost Estimation** - FRED PPI-based escalation with CA location factors
✅ **Revenue Projection** - HUD FMR + HCD AMI affordable housing integration
✅ **NPV/IRR Analysis** - Discounted cash flow with timeline modeling
✅ **Sensitivity Analysis** - Tornado diagrams + Monte Carlo simulation (10k draws)
✅ **Investment Recommendations** - Automated decision logic with risk assessment
✅ **Complete Audit Trail** - Source citations for all data points

---

## Architecture

### Components

```
app/
├── clients/                    # API integrations
│   ├── fred_client.py         # Federal Reserve Economic Data
│   ├── hud_fmr_client.py      # HUD Fair Market Rents
│   ├── census_c30_client.py   # Census Construction Spending
│   └── ccci_client.py         # CA Construction Cost Index
│
├── services/                   # Business logic
│   ├── cost_estimator.py      # Construction cost calculation
│   ├── revenue_estimator.py   # Revenue & NOI projection
│   └── economic_feasibility.py # Main feasibility orchestrator
│
├── models/                     # Data models
│   └── economic_feasibility.py # Pydantic v2 models
│
├── api/                        # FastAPI endpoints
│   └── economic_feasibility.py # 5 REST endpoints
│
└── core/
    ├── cache.py               # TTL-based caching
    ├── financial_math.py      # NPV/IRR/MC algorithms
    └── dependencies.py        # Dependency injection
```

---

## Data Sources (All Free)

### 1. FRED API (Federal Reserve Economic Data)
- **Series WPUSI012011**: Construction Materials PPI
- **Series ECICONWAG**: Construction Wages ECI
- **Series DGS10**: 10-Year Treasury (risk-free rate)
- **API Key**: Free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html)

### 2. HUD Fair Market Rents API
- Market rent benchmarks by ZIP code
- SAFMR (Small Area FMR) when available
- FMR = 40th percentile per 24 CFR 888
- **API Token**: Free at [HUD USER](https://www.huduser.gov/portal/dataset/fmr-api.html)

### 3. HCD AMI Limits (Already Integrated)
- Affordable rent calculations
- AMI-based income limits by county
- Integrated via existing `ami_calculator.py`

### 4. Census Construction Spending (Optional)
- National trends for validation
- Monthly construction spending data
- **API Key**: [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html)

---

## API Endpoints

### POST `/api/v1/economic-feasibility/compute`

**Complete feasibility analysis**

**Request:**
```json
{
  "parcel_apn": "4293-001-015",
  "scenario_name": "Base Zoning + Density Bonus",
  "units": 32,
  "buildable_sf": 28000,
  "zip_code": "90401",
  "county": "Los Angeles",
  "timeline": {
    "predevelopment_months": 12,
    "construction_months": 24,
    "lease_up_months": 6,
    "operating_years": 10
  },
  "assumptions": {
    "discount_rate": 0.12,
    "cap_rate": 0.045,
    "quality_factor": 1.05,
    "location_factor": 2.1,
    "run_sensitivity": true,
    "run_monte_carlo": true
  }
}
```

**Response:**
```json
{
  "npv": 2450000,
  "irr": 0.185,
  "profitability_index": 1.45,
  "payback_years": 6.2,
  "recommendation": "STRONG PROCEED - IRR 18.5% exceeds hurdle rate",
  "construction_costs": {
    "hard_costs": 9800000,
    "soft_costs": 1372000,
    "total_costs": 11172000
  },
  "revenue_projection": {
    "annual_noi": 1092000,
    "noi_per_unit": 34125
  },
  "sensitivity_analysis": {
    "tornado": [...],
    "monte_carlo": {
      "probability_npv_positive": 0.87,
      "p10_npv": 1200000,
      "p90_npv": 3600000
    }
  },
  "source_notes": {
    "construction_costs": "FRED PPI WPUSI012011 @ 142.3 (2025-08-01)",
    "market_rents": "HUD SAFMR 2025 Los Angeles ZIP 90401",
    "risk_free_rate": "FRED DGS10 @ 4.15% (2025-09-30)"
  }
}
```

### GET `/api/v1/economic-feasibility/cost-indices`

Get current construction cost indices from FRED.

### GET `/api/v1/economic-feasibility/market-rents/{zip_code}`

Get HUD Fair Market Rents for a ZIP code.

### POST `/api/v1/economic-feasibility/assumptions/validate`

Validate economic assumptions against reasonable bounds.

### GET `/api/v1/economic-feasibility/defaults`

Get smart defaults with current market data (auto-populates FRED rates).

---

## Economic Methodology

### Cost Estimation

**Formula:**
```
Hard_Cost = ref_cost_per_sf
          × (latest_PPI / base_PPI)           # Materials escalation
          × [wage_factor if enabled]          # Optional wage adjustment
          × location_factor                   # User input (CA avg 2.3x)
          × construction_type_factor          # Wood/concrete/steel
          × total_buildable_sf               # Units × avg_sf × 1.15
```

**Soft Costs:**
- Architecture/Engineering: 8-12% of hard costs
- Permits & Fees: $/unit by jurisdiction (CA avg $29k/unit)
- Construction Financing: `hard_cost × (rate × duration / 2)`
- Legal/Consulting: 3-5%
- Developer Fee: 15%
- Contingency: 10-15%

**Data Sources:**
- FRED WPUSI012011 (Materials PPI)
- FRED ECICONWAG (Wages, optional)
- FRED DGS10 (Interest rates)

### Revenue Estimation

**Market Rents:**
```
Market_Rent = HUD_FMR × quality_factor
```
- HUD FMR = 40th percentile (24 CFR 888)
- Quality factor: 0.8-1.2 (Class C to Class A)
- SAFMR used when `smallarea_status=1`

**Affordable Rents:**
- AMI-based from existing `ami_calculator.py`
- HCD income limits by county
- 30% of income standard

**Operating Expenses:**
- Property Tax: Prop 13 compliant (1% base + local adders)
- Insurance: 0.5-0.8% of replacement cost
- Management: 4-6% of EGI
- Utilities, Maintenance, Reserves: $3,500-5,000/unit/year

**NOI Calculation:**
```
EGI = GPI × (1 - vacancy_rate)
NOI = EGI - Operating Expenses
```

### Financial Analysis

**NPV (Net Present Value):**
```
NPV = -Initial_Investment + Σ(CFt / (1+r)^t)
```

**IRR (Internal Rate of Return):**
```
IRR = r where NPV = 0
```
- Newton-Raphson method
- Convergence tolerance: 1e-6

**Payback Period:**
```
Years until cumulative cash flow > 0
```

**Profitability Index:**
```
PI = (NPV + Initial Investment) / Initial Investment
```

**Discount Rate:**
```
r = risk_free_rate + market_risk_premium + project_risk_premium
r = DGS10 (4.15%) + MRP (6%) + Project (2-4%) = 12-14%
```

### Sensitivity Analysis

**Tornado Diagram (One-Way):**
- Test each variable independently at ±20%
- Calculate impact on NPV
- Sort by absolute impact (largest first)
- Top variables: construction cost, cap rate, market rent

**Monte Carlo Simulation:**
- 10,000 iterations (vectorized NumPy)
- Distributions:
  - Cost per SF: `Normal(μ=base, σ=input)`
  - Rent growth: `Normal(μ=3%, σ=1.5%)` clipped at 0
  - Cap rate: `Triangular(min=4%, mode=5%, max=6.5%)`
  - Construction delay: `Lognormal(μ, σ)`
- Output: P(NPV>0), percentiles (P10, P50, P90), histogram

**Performance:** <2 seconds for 10k iterations

### Investment Recommendations

**Decision Logic:**
```python
if npv <= 0:
    "DO NOT PROCEED - Negative NPV"
elif irr < 0.15:
    "MARGINAL - IRR below 15% hurdle rate"
elif prob_positive < 0.70:
    "HIGH RISK - <70% probability of positive NPV"
elif irr >= 0.18 and prob_positive >= 0.80:
    "STRONG PROCEED - Excellent risk-adjusted returns"
else:
    "PROCEED - Positive NPV with {prob}% success probability"
```

---

## Configuration

### Environment Variables

```bash
# Required
FRED_API_KEY=your_fred_api_key_here
HUD_API_TOKEN=your_hud_api_token_here

# Optional
CENSUS_API_KEY=

# Cost Settings
REF_COST_PER_SF=350.0
REF_PPI_DATE=2025-01-01
REF_PPI_VALUE=140.0

# Soft Cost %
ARCHITECTURE_PCT=0.10
LEGAL_PCT=0.04
DEVELOPER_FEE_PCT=0.15
CONTINGENCY_PCT=0.12
CONSTRUCTION_LOAN_SPREAD=0.025
COMMON_AREA_FACTOR=1.15
```

### Smart Defaults

The `/defaults` endpoint auto-populates:
- **Risk-free rate**: Live FRED DGS10
- **Discount rate**: DGS10 + 6% MRP + 2% project = 12.15%
- **Cap rate**: 4-6% guidance (multifamily)
- **Location factor**: County-specific (1.5-2.3)
- **Tax rate**: County Prop 13 rate (1.0-1.25%)
- **Operating assumptions**: 35% OpEx, 5% vacancy, 3% rent growth

---

## Usage Examples

### Python Client

```python
import httpx

# Get smart defaults
defaults = httpx.get(
    "http://localhost:8000/api/v1/economic-feasibility/defaults",
    params={"county": "Los Angeles"}
).json()

# Run analysis
response = httpx.post(
    "http://localhost:8000/api/v1/economic-feasibility/compute",
    json={
        "parcel_apn": "4293-001-015",
        "scenario_name": "Test Scenario",
        "units": 32,
        "buildable_sf": 28000,
        "zip_code": "90401",
        "county": "Los Angeles",
        "timeline": {
            "predevelopment_months": 12,
            "construction_months": 24,
            "lease_up_months": 6,
            "operating_years": 10
        },
        "assumptions": defaults,
        "run_sensitivity": True,
        "run_monte_carlo": True
    }
)

result = response.json()
print(f"NPV: ${result['npv']:,.0f}")
print(f"IRR: {result['irr']:.1%}")
print(f"Recommendation: {result['recommendation']}")
```

### cURL

```bash
# Get cost indices
curl http://localhost:8000/api/v1/economic-feasibility/cost-indices

# Get market rents
curl http://localhost:8000/api/v1/economic-feasibility/market-rents/90401

# Validate assumptions
curl -X POST http://localhost:8000/api/v1/economic-feasibility/assumptions/validate \
  -H "Content-Type: application/json" \
  -d '{"discount_rate": 0.12, "cap_rate": 0.045}'
```

---

## Testing

### Run Tests

```bash
# All tests
pytest tests/test_economic_*.py -v

# With coverage
pytest tests/test_economic_*.py --cov=app/services --cov=app/clients --cov-report=html

# Specific module
pytest tests/test_cost_estimator.py -v --tb=short
```

### Test Structure

```
tests/
├── test_clients_fred.py          # FRED API integration
├── test_clients_hud.py            # HUD FMR integration
├── test_cost_estimator.py         # Cost calculation logic
├── test_revenue_estimator.py      # Revenue projection logic
├── test_financial_math.py         # NPV/IRR/MC algorithms
├── test_economic_feasibility.py   # Integration tests
└── fixtures/                      # Test data
    ├── fred_ppi.json
    ├── hud_fmr_90401.json
    └── sample_scenarios.json
```

---

## Performance

- **API Response Time**: <5 seconds (full analysis with sensitivity)
- **Monte Carlo**: <2 seconds (10,000 iterations, vectorized)
- **Cache Hit Rate**: >80% (24-hour TTL)
- **Memory Usage**: <100MB per request

---

## References

### Data Sources
- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/)
- [HUD FMR API](https://www.huduser.gov/portal/dataset/fmr-api.html)
- [Census Construction Spending](https://api.census.gov/data/timeseries/eits/resconst.html)
- [HCD AMI Limits](https://www.hcd.ca.gov/grants-and-funding/income-limits)

### Methodologies
- [RAND: CA Construction Costs Study (2025)](https://www.rand.org/pubs/research_reports/RRA3743-1.html)
- [24 CFR 888 - FMR Methodology](https://www.ecfr.gov/current/title-24/subtitle-B/chapter-VIII/part-888)
- [CA Prop 13 Tax Rates](https://www.boe.ca.gov/proptaxes/)
- [Appraisal Institute: Income Approach](https://www.appraisalinstitute.org/)

### Academic References
- Real Estate Finance and Investment Manual (Wiedemer et al.)
- Urban Land Institute: Dollars & Cents of Development
- Real Options Theory (Black-Scholes-Merton adapted for real estate)

---

## Troubleshooting

### Common Issues

**FRED API Rate Limit:**
- Limit: 120 requests/minute (free tier)
- Solution: Caching enabled (24hr TTL)
- Fallback: Use cached values when limit exceeded

**HUD FMR ZIP Not Found:**
- Some ZIPs use metro-wide FMR (not SAFMR)
- Check `smallarea_status` in response
- Fallback to county-level FMR

**NPV/IRR Calculation Errors:**
- Ensure cash flows have both negative (investment) and positive (returns)
- IRR may not converge for complex cash flow patterns
- Use NPV as primary metric if IRR fails

---

## Roadmap

### Planned Enhancements

- [ ] Real options valuation (binomial lattice)
- [ ] Multi-phase development modeling
- [ ] Leverage analysis (debt/equity optimization)
- [ ] LIHTC equity integration
- [ ] Portfolio-level analysis
- [ ] Export to Excel pro forma

---

## Support

**Documentation:** See `/docs` endpoint when server running
**GitHub Issues:** [parcel-feasibility-engine/issues](https://github.com/jostwald-906/parcel-feasibility-engine/issues)
**API Docs:** http://localhost:8000/docs (Swagger UI)

---

*Built with FastAPI, Pydantic v2, NumPy, and SciPy*
