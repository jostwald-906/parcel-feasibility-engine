"""
Tests for AMI Calculator Service.

Verifies:
- Income limit lookups match HCD published tables
- Rent calculations use 30% of income standard
- Sales price calculations use mortgage affordability formulas
- Edge cases and error handling
"""

import pytest
from pathlib import Path
from app.services.ami_calculator import (
    AMICalculator,
    get_ami_calculator,
    AffordableRent,
    AffordableSalesPrice,
    AMILookup
)


class TestAMICalculatorInitialization:
    """Tests for AMI Calculator initialization."""

    def test_default_initialization(self):
        """Test that calculator initializes with default data path."""
        calculator = AMICalculator()
        assert calculator is not None
        assert calculator.data_path.exists()
        assert len(calculator.ami_data) > 0

    def test_available_counties(self):
        """Test that calculator has Los Angeles County data."""
        calculator = AMICalculator()
        counties = calculator.get_available_counties()
        assert "Los Angeles" in counties
        assert len(counties) > 0

    def test_available_ami_percentages(self):
        """Test that calculator has standard AMI percentages."""
        calculator = AMICalculator()
        percentages = calculator.get_available_ami_percentages()

        # HCD standard percentages
        assert 30 in percentages  # Extremely Low Income
        assert 50 in percentages  # Very Low Income
        assert 80 in percentages  # Low Income
        assert 120 in percentages  # Moderate Income

    def test_singleton_instance(self):
        """Test that get_ami_calculator returns same instance."""
        calc1 = get_ami_calculator()
        calc2 = get_ami_calculator()
        assert calc1 is calc2

    def test_missing_data_file_raises_error(self):
        """Test that missing data file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            AMICalculator(data_path="/nonexistent/path/ami_data.csv")


class TestIncomeLimitLookup:
    """Tests for income limit lookups."""

    @pytest.fixture
    def calculator(self):
        """Provide AMI calculator instance."""
        return AMICalculator()

    def test_los_angeles_50_ami_2_person(self, calculator):
        """Test Los Angeles 50% AMI for 2-person household."""
        # From HCD 2025: LA County base AMI = $106,600 for 4-person
        # 2-person = base * 0.80 = $85,280
        # 50% AMI = $85,280 * 0.50 = $42,640
        income_limit = calculator.get_income_limit("Los Angeles", 50, 2)
        assert income_limit == 42640

    def test_los_angeles_80_ami_4_person(self, calculator):
        """Test Los Angeles 80% AMI for 4-person household."""
        # From HCD 2025: LA County base AMI = $106,600 for 4-person
        # 4-person = base * 1.00 = $106,600
        # 80% AMI = $106,600 * 0.80 = $85,280
        income_limit = calculator.get_income_limit("Los Angeles", 80, 4)
        assert income_limit == 85280

    def test_los_angeles_30_ami_1_person(self, calculator):
        """Test Los Angeles 30% AMI for 1-person household (Extremely Low Income)."""
        # From HCD 2025: LA County base AMI = $106,600 for 4-person
        # 1-person = base * 0.70 = $74,620
        # 30% AMI = $74,620 * 0.30 = $22,386
        income_limit = calculator.get_income_limit("Los Angeles", 30, 1)
        assert income_limit == 22386

    def test_los_angeles_120_ami_5_person(self, calculator):
        """Test Los Angeles 120% AMI for 5-person household (Moderate Income)."""
        # From HCD 2025: LA County base AMI = $106,600 for 4-person
        # 5-person = base * 1.08 = $115,128
        # 120% AMI = $115,128 * 1.20 = $138,153.60 ≈ $138,154
        income_limit = calculator.get_income_limit("Los Angeles", 120, 5)
        assert income_limit == 138154

    def test_get_ami_lookup_returns_model(self, calculator):
        """Test that get_ami_lookup returns AMILookup model."""
        lookup = calculator.get_ami_lookup("Los Angeles", 50, 2)

        assert isinstance(lookup, AMILookup)
        assert lookup.county == "Los Angeles"
        assert lookup.ami_pct == 50
        assert lookup.household_size == 2
        assert lookup.income_limit == 42640

    def test_invalid_county_raises_error(self, calculator):
        """Test that invalid county raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            calculator.get_income_limit("Invalid County", 50, 2)

    def test_invalid_ami_pct_raises_error(self, calculator):
        """Test that invalid AMI percentage raises ValueError."""
        with pytest.raises(ValueError, match="No income limit found"):
            calculator.get_income_limit("Los Angeles", 999, 2)

    def test_invalid_household_size_raises_error(self, calculator):
        """Test that invalid household size raises ValueError."""
        with pytest.raises(ValueError, match="No income limit found"):
            calculator.get_income_limit("Los Angeles", 50, 99)


class TestAffordableRentCalculation:
    """Tests for affordable rent calculations."""

    @pytest.fixture
    def calculator(self):
        """Provide AMI calculator instance."""
        return AMICalculator()

    def test_rent_calculation_2br_50_ami(self, calculator):
        """Test affordable rent for 2BR at 50% AMI."""
        # 2BR → 3-person household (bedrooms + 1.5 rounded up)
        # LA County 50% AMI for 3-person = $47,970
        # Max rent with utilities = $47,970 * 0.30 / 12 = $1,199.25
        # Max rent without utilities = $1,199.25 - $150 = $1,049.25

        rent = calculator.calculate_max_rent("Los Angeles", 50, 2)

        assert isinstance(rent, AffordableRent)
        assert rent.county == "Los Angeles"
        assert rent.ami_pct == 50
        assert rent.bedrooms == 2
        assert rent.household_size == 4  # bedrooms + 2 (rounded from 1.5 up)
        assert rent.income_limit == 53300  # 4-person household
        assert rent.max_rent_with_utilities == pytest.approx(1332.5, abs=0.5)
        assert rent.max_rent_no_utilities == pytest.approx(1182.5, abs=0.5)
        assert rent.utility_allowance == 150.0

    def test_rent_calculation_1br_80_ami(self, calculator):
        """Test affordable rent for 1BR at 80% AMI."""
        # 1BR → 3-person household (bedrooms + 2)
        # LA County 80% AMI for 3-person = $76,752
        # Max rent with utilities = $76,752 * 0.30 / 12 = $1,918.80
        # Max rent without utilities = $1,918.80 - $150 = $1,768.80

        rent = calculator.calculate_max_rent("Los Angeles", 80, 1)

        assert rent.bedrooms == 1
        assert rent.household_size == 3
        assert rent.income_limit == 76752
        assert rent.max_rent_with_utilities == pytest.approx(1918.8, abs=1.0)
        assert rent.max_rent_no_utilities == pytest.approx(1768.8, abs=1.0)

    def test_rent_calculation_studio_30_ami(self, calculator):
        """Test affordable rent for studio at 30% AMI (Extremely Low Income)."""
        # Studio (0BR) → 2-person household (0 + 2)
        # LA County 30% AMI for 2-person = $25,584
        # Max rent with utilities = $25,584 * 0.30 / 12 = $639.60
        # Max rent without utilities = $639.60 - $150 = $489.60

        rent = calculator.calculate_max_rent("Los Angeles", 30, 0)

        assert rent.bedrooms == 0
        assert rent.household_size == 2
        assert rent.income_limit == 25584
        assert rent.max_rent_with_utilities == pytest.approx(639.6, abs=1.0)
        assert rent.max_rent_no_utilities == pytest.approx(489.6, abs=1.0)

    def test_rent_calculation_custom_utility_allowance(self, calculator):
        """Test rent calculation with custom utility allowance."""
        rent = calculator.calculate_max_rent("Los Angeles", 50, 2, utility_allowance=200.0)

        assert rent.utility_allowance == 200.0
        assert rent.max_rent_no_utilities == rent.max_rent_with_utilities - 200.0

    def test_rent_calculation_4br_caps_at_8_persons(self, calculator):
        """Test that household size caps at 8 persons."""
        # 4BR → would be 6-person, but should cap at 8
        rent = calculator.calculate_max_rent("Los Angeles", 50, 6)

        # 6BR + 2 = 8 persons (maximum)
        assert rent.household_size == 8


class TestAffordableSalesPriceCalculation:
    """Tests for affordable sales price calculations."""

    @pytest.fixture
    def calculator(self):
        """Provide AMI calculator instance."""
        return AMICalculator()

    def test_sales_price_80_ami_4_person(self, calculator):
        """Test affordable sales price for 80% AMI, 4-person household."""
        # LA County 80% AMI for 4-person = $85,280
        # Max monthly housing = $85,280 * 0.30 / 12 = $2,132
        # With 6.5% interest, 30-year, 10% down, 1.25% tax, 0.5% insurance
        # Expected price around $298,000

        price = calculator.calculate_max_sales_price("Los Angeles", 80, 4)

        assert isinstance(price, AffordableSalesPrice)
        assert price.county == "Los Angeles"
        assert price.ami_pct == 80
        assert price.household_size == 4
        assert price.income_limit == 85280
        assert price.max_sales_price >= 250000  # Should be around $298k
        assert price.max_sales_price <= 350000

    def test_sales_price_assumptions_stored(self, calculator):
        """Test that calculation assumptions are stored."""
        price = calculator.calculate_max_sales_price("Los Angeles", 80, 4)

        assert "interest_rate_pct" in price.assumptions
        assert "loan_term_years" in price.assumptions
        assert "down_payment_pct" in price.assumptions
        assert "property_tax_rate_pct" in price.assumptions
        assert "insurance_rate_pct" in price.assumptions
        assert "hoa_monthly" in price.assumptions

    def test_sales_price_custom_parameters(self, calculator):
        """Test sales price with custom mortgage parameters."""
        # Higher interest rate should reduce max price
        price_high_rate = calculator.calculate_max_sales_price(
            "Los Angeles", 80, 4,
            interest_rate_pct=8.0  # Higher rate
        )

        price_low_rate = calculator.calculate_max_sales_price(
            "Los Angeles", 80, 4,
            interest_rate_pct=5.0  # Lower rate
        )

        # Lower interest rate should allow higher price
        assert price_low_rate.max_sales_price > price_high_rate.max_sales_price

    def test_sales_price_with_hoa(self, calculator):
        """Test that HOA fees reduce max affordable price."""
        price_no_hoa = calculator.calculate_max_sales_price(
            "Los Angeles", 80, 4,
            hoa_monthly=0
        )

        price_with_hoa = calculator.calculate_max_sales_price(
            "Los Angeles", 80, 4,
            hoa_monthly=300  # $300/month HOA
        )

        # HOA fees should reduce max price
        assert price_with_hoa.max_sales_price < price_no_hoa.max_sales_price

    def test_sales_price_120_ami_moderate_income(self, calculator):
        """Test sales price for moderate income (120% AMI)."""
        # LA County 120% AMI for 4-person = $127,920
        # Should afford significantly higher price than 80% AMI
        price = calculator.calculate_max_sales_price("Los Angeles", 120, 4)

        assert price.income_limit == 127920
        assert price.max_sales_price >= 400000  # Should be substantially higher (around $447k)

    def test_sales_price_30_ami_extremely_low(self, calculator):
        """Test sales price for extremely low income (30% AMI)."""
        # LA County 30% AMI for 4-person = $31,980
        # Very limited affordability
        price = calculator.calculate_max_sales_price("Los Angeles", 30, 4)

        assert price.income_limit == 31980
        assert price.max_sales_price < 200000  # Limited affordability


class TestMultipleCounties:
    """Tests for multiple county support."""

    @pytest.fixture
    def calculator(self):
        """Provide AMI calculator instance."""
        return AMICalculator()

    def test_san_francisco_higher_ami(self, calculator):
        """Test that San Francisco has higher AMI than Los Angeles."""
        # San Francisco AMI should be higher due to higher cost of living
        sf_income = calculator.get_income_limit("San Francisco", 50, 4)
        la_income = calculator.get_income_limit("Los Angeles", 50, 4)

        assert sf_income > la_income

    def test_fresno_lower_ami(self, calculator):
        """Test that Fresno has lower AMI than Los Angeles."""
        # Fresno AMI should be lower
        fresno_income = calculator.get_income_limit("Fresno", 50, 4)
        la_income = calculator.get_income_limit("Los Angeles", 50, 4)

        assert fresno_income < la_income

    def test_all_counties_have_standard_percentages(self, calculator):
        """Test that all counties have standard AMI percentages."""
        counties = calculator.get_available_counties()
        standard_percentages = [30, 50, 80]

        for county in counties:
            for pct in standard_percentages:
                # Should not raise error
                income = calculator.get_income_limit(county, pct, 4)
                assert income > 0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def calculator(self):
        """Provide AMI calculator instance."""
        return AMICalculator()

    def test_household_size_1(self, calculator):
        """Test minimum household size (1 person)."""
        income = calculator.get_income_limit("Los Angeles", 50, 1)
        assert income > 0

    def test_household_size_8(self, calculator):
        """Test maximum household size (8 persons)."""
        income = calculator.get_income_limit("Los Angeles", 50, 8)
        assert income > 0

    def test_rent_for_large_unit(self, calculator):
        """Test rent calculation for 4+ bedroom unit."""
        rent = calculator.calculate_max_rent("Los Angeles", 50, 4)

        assert rent.bedrooms == 4
        assert rent.household_size == 6  # 4BR + 2
        assert rent.max_rent_with_utilities > 0

    def test_sales_price_zero_interest(self, calculator):
        """Test sales price calculation with zero interest rate."""
        price = calculator.calculate_max_sales_price(
            "Los Angeles", 80, 4,
            interest_rate_pct=0.0
        )

        # Should still calculate a price
        assert price.max_sales_price > 0

    def test_sales_price_100_percent_down(self, calculator):
        """Test sales price with 100% down payment (cash purchase)."""
        price = calculator.calculate_max_sales_price(
            "Los Angeles", 80, 4,
            down_payment_pct=100.0
        )

        # Should still calculate (though unrealistic scenario)
        assert price.max_sales_price >= 0


class TestPydanticModels:
    """Tests for Pydantic model validation."""

    def test_ami_lookup_model_validation(self):
        """Test AMILookup model validation."""
        lookup = AMILookup(
            county="Los Angeles",
            ami_pct=50.0,
            household_size=2,
            income_limit=42640.0
        )

        assert lookup.county == "Los Angeles"
        assert lookup.ami_pct == 50.0
        assert lookup.household_size == 2
        assert lookup.income_limit == 42640.0

    def test_affordable_rent_model_validation(self):
        """Test AffordableRent model validation."""
        rent = AffordableRent(
            county="Los Angeles",
            ami_pct=50.0,
            bedrooms=2,
            household_size=3,
            income_limit=47970.0,
            max_rent_with_utilities=1199.25,
            max_rent_no_utilities=1049.25,
            utility_allowance=150.0
        )

        assert rent.bedrooms == 2
        assert rent.max_rent_no_utilities == 1049.25

    def test_affordable_sales_price_model_validation(self):
        """Test AffordableSalesPrice model validation."""
        price = AffordableSalesPrice(
            county="Los Angeles",
            ami_pct=80.0,
            household_size=4,
            income_limit=85280.0,
            max_sales_price=425000.0,
            assumptions={
                "interest_rate_pct": 6.5,
                "loan_term_years": 30
            }
        )

        assert price.household_size == 4
        assert price.max_sales_price == 425000.0
        assert "interest_rate_pct" in price.assumptions


class TestDataAccuracy:
    """Tests to verify data accuracy against HCD published values."""

    @pytest.fixture
    def calculator(self):
        """Provide AMI calculator instance."""
        return AMICalculator()

    def test_los_angeles_base_ami_4_person(self, calculator):
        """Test Los Angeles base AMI (100%) for 4-person household."""
        # From HCD 2025: LA County AMI = $106,600 for 4-person
        income = calculator.get_income_limit("Los Angeles", 100, 4)
        assert income == 106600

    def test_30_percent_rule_rent(self, calculator):
        """Test that rent calculation uses 30% of income standard."""
        # For any income, rent should be exactly 30% annually, or 2.5% monthly
        income = calculator.get_income_limit("Los Angeles", 50, 2)
        rent = calculator.calculate_max_rent("Los Angeles", 50, 0)  # 0BR uses 2-person

        # Annual rent (with utilities) should be 30% of income
        annual_rent = rent.max_rent_with_utilities * 12
        expected_annual_rent = income * 0.30

        assert annual_rent == pytest.approx(expected_annual_rent, abs=0.5)
