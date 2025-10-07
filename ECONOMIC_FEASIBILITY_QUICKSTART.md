# Economic Feasibility Module - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine"
./venv/bin/pip install fredapi tenacity numpy scipy numpy-financial
```

✅ **Already done!** Dependencies are installed.

### Step 2: Get Free API Keys

#### FRED API Key (Required)
1. Visit: https://fred.stlouisfed.org/docs/api/api_key.html
2. Create free account
3. Copy API key
4. Add to `.env`: `FRED_API_KEY=your_key_here`

#### HUD FMR API Token (Required)
1. Visit: https://www.huduser.gov/portal/dataset/fmr-api.html
2. Register for free token
3. Copy token
4. Add to `.env`: `HUD_API_TOKEN=your_token_here`

#### Census API Key (Optional)
1. Visit: https://api.census.gov/data/key_signup.html
2. Request key
3. Add to `.env`: `CENSUS_API_KEY=your_key_here`

### Step 3: Configure Environment

Copy `.env.example` to `.env` and add your keys:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Minimum required in `.env`:**
```
FRED_API_KEY=your_fred_api_key_here
HUD_API_TOKEN=your_hud_api_token_here
```

### Step 4: Start the Server

```bash
./venv/bin/uvicorn app.main:app --reload --port 8000
```

### Step 5: Test the API

Open your browser: http://localhost:8000/docs

Or use curl:

```bash
# Test health check
curl http://localhost:8000/health

# Get current cost indices
curl http://localhost:8000/api/v1/economic-feasibility/cost-indices

# Get market rents for Santa Monica
curl http://localhost:8000/api/v1/economic-feasibility/market-rents/90401

# Get smart defaults
curl http://localhost:8000/api/v1/economic-feasibility/defaults?county=Los%20Angeles
```

---

## 📊 Run Your First Analysis

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/economic-feasibility/compute \
  -H "Content-Type: application/json" \
  -d '{
    "parcel_apn": "4293-001-015",
    "scenario_name": "Test Development",
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
      "quality_factor": 1.0,
      "location_factor": 2.1
    },
    "run_sensitivity": true,
    "run_monte_carlo": true
  }'
```

### Python Example

```python
import httpx

# Get defaults
defaults_response = httpx.get(
    "http://localhost:8000/api/v1/economic-feasibility/defaults",
    params={"county": "Los Angeles"}
)
defaults = defaults_response.json()

# Run analysis
analysis_response = httpx.post(
    "http://localhost:8000/api/v1/economic-feasibility/compute",
    json={
        "parcel_apn": "4293-001-015",
        "scenario_name": "32-Unit Development",
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

result = analysis_response.json()

# Print results
print(f"NPV: ${result['npv']:,.0f}")
print(f"IRR: {result['irr']:.1%}")
print(f"Payback: {result['payback_years']:.1f} years")
print(f"Recommendation: {result['recommendation']}")

# Monte Carlo results
mc = result['sensitivity_analysis']['monte_carlo']
print(f"\nMonte Carlo (10k simulations):")
print(f"  Probability NPV > 0: {mc['probability_npv_positive']:.1%}")
print(f"  P10 NPV: ${mc['percentiles']['p10']:,.0f}")
print(f"  P90 NPV: ${mc['percentiles']['p90']:,.0f}")
```

---

## 🔍 Available Endpoints

### 1. **POST /api/v1/economic-feasibility/compute**
   - Full feasibility analysis
   - NPV, IRR, sensitivity analysis
   - Returns: Complete pro forma

### 2. **GET /api/v1/economic-feasibility/cost-indices**
   - Current FRED construction indices
   - Materials PPI, wages, interest rates
   - Returns: Latest index values

### 3. **GET /api/v1/economic-feasibility/market-rents/{zip_code}**
   - HUD Fair Market Rents
   - By bedroom count (0-4BR)
   - Returns: FMR or SAFMR data

### 4. **POST /api/v1/economic-feasibility/assumptions/validate**
   - Validate input assumptions
   - Check reasonableness bounds
   - Returns: Warnings & recommendations

### 5. **GET /api/v1/economic-feasibility/defaults**
   - Smart defaults with live data
   - Auto-populated from FRED
   - Returns: Pre-configured assumptions

---

## 📈 Understanding the Results

### NPV (Net Present Value)
- **Positive NPV**: Project adds value, proceed
- **Negative NPV**: Project destroys value, do not proceed
- **Formula**: NPV = Σ(Cash Flows / (1+discount_rate)^t) - Initial Investment

### IRR (Internal Rate of Return)
- **Above 15%**: Good risk-adjusted return
- **15-20%**: Typical for development
- **Above 20%**: Excellent opportunity
- **Formula**: Discount rate where NPV = 0

### Monte Carlo Simulation
- **10,000 iterations** testing variable ranges
- **Probability NPV > 0**: Risk assessment
- **P10/P90**: Downside/upside scenarios
- **Use case**: Understanding project risk

### Decision Recommendations

| Condition | Recommendation |
|-----------|---------------|
| NPV ≤ 0 | **DO NOT PROCEED** |
| IRR < 15% | **MARGINAL** - Below hurdle rate |
| Prob(NPV>0) < 70% | **HIGH RISK** - Low success probability |
| IRR ≥ 18% AND Prob ≥ 80% | **STRONG PROCEED** - Excellent returns |
| Otherwise | **PROCEED** - Positive with caveats |

---

## 🛠 Troubleshooting

### API Key Issues

**Error**: "FRED API unavailable"
- **Fix**: Check `FRED_API_KEY` in `.env`
- **Test**: `curl "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=YOUR_KEY"`

**Error**: "HUD API unavailable"
- **Fix**: Check `HUD_API_TOKEN` in `.env`
- **Test**: Visit `https://www.huduser.gov/hudapi/public/fmr/data/METRO41940?year=2025` with Bearer token

### Rate Limiting

**FRED**: 120 requests/minute (free tier)
- Caching enabled (24hr TTL)
- Retry logic with exponential backoff

**HUD**: No published limit
- Conservative rate limiting recommended
- Caching enabled

### Data Issues

**ZIP code not found**:
- Some ZIPs use metro-wide FMR
- Try nearby ZIP or use county defaults

**IRR doesn't converge**:
- Complex cash flow patterns
- Use NPV as primary metric
- Check timeline assumptions

---

## 📚 Next Steps

1. **Read Full Documentation**: See `ECONOMIC_FEASIBILITY.md`
2. **Explore Swagger UI**: http://localhost:8000/docs
3. **Run Tests**: `pytest tests/test_economic_*.py -v`
4. **Integrate with Frontend**: Build dashboard components
5. **Customize**: Adjust defaults in `.env`

---

## 💡 Pro Tips

### Optimize for Your Use Case

**For Quick Screening:**
- Skip Monte Carlo: `"run_monte_carlo": false`
- Use defaults endpoint for fast setup
- Focus on NPV and IRR

**For Detailed Analysis:**
- Enable all sensitivity: `"run_sensitivity": true, "run_monte_carlo": true`
- Customize all assumptions
- Review source_notes for data provenance

**For Multiple Scenarios:**
- Cache defaults once
- Reuse assumptions across requests
- Compare NPV/IRR side-by-side

### Best Practices

✅ **Always validate assumptions** before compute
✅ **Use smart defaults** as starting point
✅ **Check source_notes** for data recency
✅ **Run Monte Carlo** for risk assessment on large projects
✅ **Compare scenarios** using same discount rate

---

## 🎯 Success Checklist

- [ ] API keys configured in `.env`
- [ ] Server starts without errors
- [ ] `/health` endpoint returns 200
- [ ] `/cost-indices` returns FRED data
- [ ] `/market-rents/90401` returns HUD data
- [ ] `/compute` returns feasibility analysis
- [ ] Monte Carlo completes in <2 seconds
- [ ] Source notes include all data citations

**Once all checked ✅ — You're ready to go!**

---

*For full methodology, see ECONOMIC_FEASIBILITY.md*
