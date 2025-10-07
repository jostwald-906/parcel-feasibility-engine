"""
Area Median Income (AMI) Calculator Service

Calculates affordable rents and sales prices based on HCD/HUD income limits.

Data Source: HCD Income Limits (https://www.hcd.ca.gov/grants-and-funding/income-limits)
Updated: Annually (April)

Formulas:
- Affordable Rent: 30% of income standard (rent burden threshold)
- Affordable Sales Price: 30% of income for PITI (Principal, Interest, Taxes, Insurance)

Income Categories (AMI %):
- Extremely Low Income: 30% AMI
- Very Low Income: 50% AMI
- Low Income: 60% and 80% AMI
- Median Income: 100% AMI
- Moderate Income: 120% AMI

References:
- Gov. Code § 50053 (very low income definition)
- Gov. Code § 50052.5 (lower income definition)
- HUD Fair Market Rent methodology
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
import pandas as pd
from pathlib import Path
import math


class AMILookup(BaseModel):
    """AMI income limit lookup result."""

    county: str = Field(..., description="County name")
    ami_pct: float = Field(..., description="AMI percentage (e.g., 50.0 for 50% AMI)")
    household_size: int = Field(..., ge=1, le=8, description="Household size (1-8 persons)")
    income_limit: float = Field(..., description="Annual income limit in dollars")

    class Config:
        json_schema_extra = {
            "example": {
                "county": "Los Angeles",
                "ami_pct": 50.0,
                "household_size": 2,
                "income_limit": 42640.0
            }
        }


class AffordableRent(BaseModel):
    """Affordable rent calculation result."""

    county: str = Field(..., description="County name")
    ami_pct: float = Field(..., description="AMI percentage")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    household_size: int = Field(..., ge=1, description="Assumed household size")
    income_limit: float = Field(..., description="Annual income limit")
    max_rent_with_utilities: float = Field(..., description="Max monthly rent including utilities")
    max_rent_no_utilities: float = Field(..., description="Max monthly rent without utilities")
    utility_allowance: float = Field(default=150.0, description="Monthly utility allowance")

    class Config:
        json_schema_extra = {
            "example": {
                "county": "Los Angeles",
                "ami_pct": 50.0,
                "bedrooms": 2,
                "household_size": 3,
                "income_limit": 47970.0,
                "max_rent_with_utilities": 1199.25,
                "max_rent_no_utilities": 1049.25,
                "utility_allowance": 150.0
            }
        }


class AffordableSalesPrice(BaseModel):
    """Affordable sales price calculation result."""

    county: str = Field(..., description="County name")
    ami_pct: float = Field(..., description="AMI percentage")
    household_size: int = Field(..., ge=1, description="Household size")
    income_limit: float = Field(..., description="Annual income limit")
    max_sales_price: float = Field(..., description="Maximum affordable sales price")
    assumptions: Dict[str, float] = Field(..., description="Calculation assumptions")

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class AMICalculator:
    """
    Calculate affordable housing limits based on HCD/HUD income data.

    This service provides:
    1. Income limit lookups by county/AMI%/household size
    2. Affordable rent calculations (30% of income)
    3. Affordable sales price calculations (mortgage affordability)
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize AMI Calculator.

        Args:
            data_path: Optional path to AMI data CSV. If None, uses default location.
        """
        if data_path is None:
            # Default to project data directory
            project_root = Path(__file__).parent.parent.parent
            data_path = project_root / "data" / "ami_limits_2025.csv"

        self.data_path = Path(data_path)

        # Load AMI data from CSV
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"AMI data file not found: {self.data_path}\n"
                "Run 'python scripts/import_ami_limits.py' to generate data."
            )

        self.ami_data = pd.read_csv(self.data_path)

        # Validate required columns
        required_cols = {"county", "household_size", "ami_pct", "income_limit"}
        if not required_cols.issubset(self.ami_data.columns):
            raise ValueError(
                f"AMI data missing required columns. Expected: {required_cols}, "
                f"Found: {set(self.ami_data.columns)}"
            )

        # Cache available counties for validation
        self.available_counties = set(self.ami_data["county"].unique())

    def get_income_limit(
        self,
        county: str,
        ami_pct: float,
        household_size: int
    ) -> float:
        """
        Get income limit for county/AMI%/household size.

        Args:
            county: County name (e.g., "Los Angeles")
            ami_pct: AMI percentage (e.g., 50.0 for 50% AMI)
            household_size: Household size (1-8 persons)

        Returns:
            Annual income limit in dollars

        Raises:
            ValueError: If county not found or no matching data
        """
        # Validate county
        if county not in self.available_counties:
            raise ValueError(
                f"County '{county}' not found in AMI data. "
                f"Available counties: {sorted(self.available_counties)}"
            )

        # Query DataFrame
        result = self.ami_data[
            (self.ami_data["county"] == county) &
            (self.ami_data["ami_pct"] == ami_pct) &
            (self.ami_data["household_size"] == household_size)
        ]

        if result.empty:
            raise ValueError(
                f"No income limit found for county={county}, "
                f"ami_pct={ami_pct}, household_size={household_size}"
            )

        return float(result.iloc[0]["income_limit"])

    def get_ami_lookup(
        self,
        county: str,
        ami_pct: float,
        household_size: int
    ) -> AMILookup:
        """
        Get AMI lookup with metadata.

        Args:
            county: County name
            ami_pct: AMI percentage
            household_size: Household size

        Returns:
            AMILookup model with income limit data
        """
        income_limit = self.get_income_limit(county, ami_pct, household_size)

        return AMILookup(
            county=county,
            ami_pct=ami_pct,
            household_size=household_size,
            income_limit=income_limit
        )

    def calculate_max_rent(
        self,
        county: str,
        ami_pct: float,
        bedrooms: int,
        utility_allowance: float = 150.0
    ) -> AffordableRent:
        """
        Calculate maximum affordable rent (30% of income standard).

        Household size assumption: bedrooms + 1.5 (HUD occupancy standard),
        rounded up to nearest integer.

        Formula:
        - Max monthly rent with utilities = (Annual Income × 0.30) / 12
        - Max monthly rent without utilities = Max rent with utilities - Utility allowance

        Args:
            county: County name
            ami_pct: AMI percentage (e.g., 50.0 for 50% AMI)
            bedrooms: Number of bedrooms (0-4+)
            utility_allowance: Monthly utility allowance estimate (default: $150)

        Returns:
            AffordableRent model with rent calculations

        Examples:
            >>> calc = AMICalculator()
            >>> rent = calc.calculate_max_rent("Los Angeles", 50.0, 2)
            >>> print(f"Max rent: ${rent.max_rent_no_utilities:.2f}/month")
            Max rent: $1049.25/month
        """
        # HUD occupancy standard: bedrooms + 1.5 persons
        # Round up to ensure adequate space
        household_size = bedrooms + 2  # bedrooms + 1.5, rounded up

        # Cap at 8 (maximum household size in HCD data)
        household_size = min(household_size, 8)

        # Get income limit
        income_limit = self.get_income_limit(county, ami_pct, household_size)

        # 30% of income standard for housing cost
        max_rent_with_utilities = (income_limit * 0.30) / 12

        # Subtract utility allowance for contract rent
        max_rent_no_utilities = max_rent_with_utilities - utility_allowance

        return AffordableRent(
            county=county,
            ami_pct=ami_pct,
            bedrooms=bedrooms,
            household_size=household_size,
            income_limit=income_limit,
            max_rent_with_utilities=max_rent_with_utilities,
            max_rent_no_utilities=max_rent_no_utilities,
            utility_allowance=utility_allowance
        )

    def calculate_max_sales_price(
        self,
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
        Calculate maximum affordable sales price.

        Assumes 30% of income for total housing cost (PITI + HOA):
        - P: Principal (mortgage payment)
        - I: Interest
        - T: Property taxes
        - I: Insurance
        - HOA: Homeowners association fees

        Formula:
        1. Max monthly housing cost = (Annual Income × 0.30) / 12
        2. Monthly PITI + HOA ≤ Max housing cost
        3. Solve for maximum sales price

        Args:
            county: County name
            ami_pct: AMI percentage
            household_size: Household size (1-8)
            interest_rate_pct: Annual interest rate percentage (default: 6.5%)
            loan_term_years: Loan term in years (default: 30)
            down_payment_pct: Down payment percentage (default: 10%)
            property_tax_rate_pct: Annual property tax rate (default: 1.25% in CA)
            insurance_rate_pct: Annual insurance rate (default: 0.5%)
            hoa_monthly: Monthly HOA fees (default: $0)

        Returns:
            AffordableSalesPrice model with price and assumptions

        Examples:
            >>> calc = AMICalculator()
            >>> price = calc.calculate_max_sales_price("Los Angeles", 80.0, 4)
            >>> print(f"Max price: ${price.max_sales_price:,.0f}")
            Max price: $425,000
        """
        # Get income limit
        income_limit = self.get_income_limit(county, ami_pct, household_size)

        # 30% of income for housing
        max_monthly_housing = (income_limit * 0.30) / 12

        # Subtract HOA from available housing payment
        max_monthly_piti = max_monthly_housing - hoa_monthly

        # Convert rates to decimal
        monthly_interest_rate = (interest_rate_pct / 100.0) / 12
        loan_term_months = loan_term_years * 12
        annual_tax_rate = property_tax_rate_pct / 100.0
        annual_insurance_rate = insurance_rate_pct / 100.0

        # Iteratively solve for sales price
        # We'll use a simplified approach: estimate and refine

        # Start with rough estimate assuming 90% LTV (10% down)
        # Monthly payment factor for mortgage
        if monthly_interest_rate > 0:
            # Standard mortgage payment formula
            mortgage_factor = monthly_interest_rate * (1 + monthly_interest_rate) ** loan_term_months / \
                            ((1 + monthly_interest_rate) ** loan_term_months - 1)
        else:
            # No interest case
            mortgage_factor = 1.0 / loan_term_months

        # Estimate max price through iteration
        # PITI = Mortgage Payment + (Price × Tax Rate / 12) + (Price × Insurance Rate / 12)

        # Use algebraic solution:
        # Let P = sales price, L = loan amount = P × (1 - down_payment_pct/100)
        # Monthly Payment = L × mortgage_factor + P × (tax_rate + ins_rate) / 12
        # Solve for P

        loan_to_value = 1.0 - (down_payment_pct / 100.0)
        monthly_ti_rate = (annual_tax_rate + annual_insurance_rate) / 12

        # P × [LTV × mortgage_factor + monthly_TI_rate] = max_monthly_piti
        # P = max_monthly_piti / [LTV × mortgage_factor + monthly_TI_rate]

        combined_factor = loan_to_value * mortgage_factor + monthly_ti_rate

        if combined_factor > 0:
            max_sales_price = max_monthly_piti / combined_factor
        else:
            max_sales_price = 0.0

        # Round to nearest $1,000
        max_sales_price = round(max_sales_price / 1000) * 1000

        # Store assumptions
        assumptions = {
            "interest_rate_pct": interest_rate_pct,
            "loan_term_years": loan_term_years,
            "down_payment_pct": down_payment_pct,
            "property_tax_rate_pct": property_tax_rate_pct,
            "insurance_rate_pct": insurance_rate_pct,
            "hoa_monthly": hoa_monthly
        }

        return AffordableSalesPrice(
            county=county,
            ami_pct=ami_pct,
            household_size=household_size,
            income_limit=income_limit,
            max_sales_price=max_sales_price,
            assumptions=assumptions
        )

    def get_available_counties(self) -> List[str]:
        """
        Get list of available counties in the dataset.

        Returns:
            Sorted list of county names
        """
        return sorted(self.available_counties)

    def get_available_ami_percentages(self) -> List[float]:
        """
        Get list of available AMI percentages.

        Returns:
            Sorted list of AMI percentages (e.g., [30.0, 50.0, 60.0, 80.0, 100.0, 120.0])
        """
        return sorted(self.ami_data["ami_pct"].unique())


# Singleton instance for easy access
_calculator_instance: Optional[AMICalculator] = None


def get_ami_calculator() -> AMICalculator:
    """
    Get singleton AMI calculator instance.

    Returns:
        AMICalculator instance

    Examples:
        >>> calc = get_ami_calculator()
        >>> income_limit = calc.get_income_limit("Los Angeles", 50.0, 2)
    """
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = AMICalculator()
    return _calculator_instance
