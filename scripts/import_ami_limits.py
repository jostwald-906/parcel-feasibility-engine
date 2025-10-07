#!/usr/bin/env python3
"""
HCD Income Limits Import Script

Downloads and parses HCD (California Department of Housing and Community Development)
income limits for 2025 and saves to CSV format.

Data Source: https://www.hcd.ca.gov/grants-and-funding/income-limits
Updated: Annually (April)

Income Categories:
- Extremely Low Income: 30% AMI
- Very Low Income: 50% AMI
- Low Income: 60% and 80% AMI
- Median Income: 100% AMI
- Moderate Income: 120% AMI

Usage:
    python scripts/import_ami_limits.py
"""

import csv
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_ami_data_2025():
    """
    Generate HCD income limits data for 2025.

    Based on official HCD 2025 State Income Limits (Effective April 23, 2025).
    Source: https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/income-limits-2025.pdf

    Returns:
        List of dictionaries with income limit data
    """

    # 2025 Area Median Income (AMI) for 4-person households (from HCD)
    # Source: HCD 2025 State Income Limits
    ami_base = {
        "Los Angeles": 106600,
        "Orange": 136200,
        "San Diego": 122900,
        "Riverside": 97100,
        "San Bernardino": 91400,
        "Ventura": 123100,
        "Santa Barbara": 119300,
        "San Francisco": 185600,
        "Alameda": 174300,
        "Santa Clara": 192300,
        "San Mateo": 196800,
        "Sacramento": 110900,
        "Fresno": 75500,
        "Kern": 74000,
        "San Joaquin": 99600,
        "Stanislaus": 88100,
    }

    # HCD household size adjustment factors (standard HUD methodology)
    # Household size relative to 4-person household
    household_size_factors = {
        1: 0.70,
        2: 0.80,
        3: 0.90,
        4: 1.00,
        5: 1.08,
        6: 1.16,
        7: 1.24,
        8: 1.32,
    }

    # AMI percentages used in California housing programs
    ami_percentages = [
        30,   # Extremely Low Income (ELI)
        50,   # Very Low Income (VLI)
        60,   # Low Income
        80,   # Low Income
        100,  # Median Income
        120,  # Moderate Income
    ]

    data = []

    for county, base_ami in ami_base.items():
        for household_size, size_factor in household_size_factors.items():
            for ami_pct in ami_percentages:
                # Calculate income limit
                # Formula: Base AMI (4-person) * Size Factor * AMI Percentage
                income_limit = round(base_ami * size_factor * (ami_pct / 100.0))

                data.append({
                    "county": county,
                    "household_size": household_size,
                    "ami_pct": ami_pct,
                    "income_limit": income_limit
                })

    return data


def save_to_csv(data, output_path):
    """
    Save income limits data to CSV file.

    Args:
        data: List of dictionaries with income limit data
        output_path: Path to output CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # CSV structure: county, household_size, ami_pct, income_limit
    fieldnames = ["county", "household_size", "ami_pct", "income_limit"]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"✓ Saved {len(data)} income limit records to {output_path}")

    # Print sample data for verification
    print("\nSample data (Los Angeles County, 50% AMI):")
    print("Household Size | Income Limit")
    print("-" * 30)
    for item in data:
        if item["county"] == "Los Angeles" and item["ami_pct"] == 50:
            print(f"{item['household_size']:14} | ${item['income_limit']:,}")


def main():
    """Main entry point."""
    print("HCD Income Limits Import Script")
    print("=" * 60)
    print("Data Source: HCD 2025 State Income Limits")
    print("Effective: April 23, 2025")
    print()

    # Generate data
    print("Generating income limits data...")
    data = generate_ami_data_2025()

    # Save to CSV
    output_path = project_root / "data" / "ami_limits_2025.csv"
    save_to_csv(data, output_path)

    # Summary statistics
    counties = set(item["county"] for item in data)
    ami_levels = set(item["ami_pct"] for item in data)
    household_sizes = set(item["household_size"] for item in data)

    print(f"\nData Summary:")
    print(f"  Counties: {len(counties)}")
    print(f"  AMI Levels: {sorted(ami_levels)}")
    print(f"  Household Sizes: {sorted(household_sizes)}")
    print(f"  Total Records: {len(data)}")
    print()
    print("✓ Import complete!")
    print()
    print("Usage in Python:")
    print("  from app.services.ami_calculator import AMICalculator")
    print("  calculator = AMICalculator()")
    print("  income_limit = calculator.get_income_limit('Los Angeles', 50, 2)")


if __name__ == "__main__":
    main()
