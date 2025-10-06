#!/usr/bin/env python3
"""
Example: RHNA Data Integration with SB35 Analysis

This script demonstrates how the RHNA service provides official HCD
affordability determinations for SB35 streamlined projects.
"""

from app.services.rhna_service import rhna_service
from app.models.parcel import ParcelBase
from app.rules.state_law.sb35 import analyze_sb35, get_affordability_requirement


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def example_1_rhna_service_basics():
    """Example 1: Basic RHNA service usage."""
    print_section("Example 1: RHNA Service Basics")

    # Get summary statistics
    stats = rhna_service.get_summary_stats()
    print("California RHNA Data Summary:")
    print(f"  Total jurisdictions: {stats['total_jurisdictions']}")
    print(f"  Exempt (met targets): {stats['exempt_count']} ({stats['exempt_count']/stats['total_jurisdictions']*100:.1f}%)")
    print(f"  Require 10% affordable: {stats['requires_10_pct_count']} ({stats['requires_10_pct_count']/stats['total_jurisdictions']*100:.1f}%)")
    print(f"  Require 50% affordable: {stats['requires_50_pct_count']} ({stats['requires_50_pct_count']/stats['total_jurisdictions']*100:.1f}%)")
    print(f"  Data source: {stats['data_file']}")


def example_2_jurisdiction_lookups():
    """Example 2: Look up specific jurisdictions."""
    print_section("Example 2: Jurisdiction Lookups")

    jurisdictions_to_test = [
        ("Santa Monica", "Los Angeles"),
        ("San Francisco", "San Francisco"),
        ("Los Angeles", "Los Angeles"),
        ("Adelanto", "San Bernardino"),
        ("Oakland", "Alameda"),
    ]

    for city, county in jurisdictions_to_test:
        result = rhna_service.get_sb35_affordability(city, county)

        print(f"{city}, {county}:")
        print(f"  Affordability: {result['percentage']}%")
        print(f"  Exempt: {result['is_exempt']}")
        print(f"  Above-moderate RHNA progress: {result['above_moderate_progress']}%")
        print(f"  Income levels: {', '.join(result['income_levels']) if result['income_levels'] else 'N/A (exempt)'}")
        print()


def example_3_sb35_integration():
    """Example 3: SB35 analysis with RHNA integration."""
    print_section("Example 3: SB35 Analysis Integration")

    # Create a test parcel in Santa Monica
    parcel = ParcelBase(
        apn="4293-001-012",
        address="1234 Ocean Ave",
        city="Santa Monica",
        county="Los Angeles",
        state="CA",
        zip_code="90401",
        lot_size_sqft=15000,
        zoning_code="R3",
        existing_units=0,
        existing_building_sqft=0,
        year_built=None
    )

    print(f"Parcel: {parcel.address}, {parcel.city}")
    print(f"Lot size: {parcel.lot_size_sqft:,} sq ft")
    print(f"Zoning: {parcel.zoning_code}")
    print()

    # Get affordability requirement using new RHNA service
    affordability = get_affordability_requirement(parcel)

    print(f"SB35 Affordability Determination:")
    print(f"  Percentage: {affordability['percentage']}%")
    print(f"  Exempt: {affordability['is_exempt']}")
    print(f"  Source: {affordability['source']}")
    print()

    # Run full SB35 analysis
    scenario = analyze_sb35(parcel)

    if scenario:
        print(f"SB35 Development Scenario:")
        print(f"  Max units: {scenario.max_units}")
        print(f"  Affordable units required: {scenario.affordable_units_required}")
        print(f"  Max building size: {scenario.max_building_sqft:,} sq ft")
        print(f"  Max height: {scenario.max_height_ft} ft ({scenario.max_stories} stories)")
        print(f"  Parking required: {scenario.parking_spaces_required} spaces")
        print()
        print("Key notes:")
        for note in scenario.notes[:10]:  # Show first 10 notes
            print(f"  • {note}")
    else:
        print("Parcel is NOT eligible for SB35 streamlining")


def example_4_compare_jurisdictions():
    """Example 4: Compare RHNA performance across jurisdictions."""
    print_section("Example 4: Compare Bay Area Jurisdictions")

    bay_area_cities = [
        ("San Francisco", "San Francisco"),
        ("Oakland", "Alameda"),
        ("San Jose", "Santa Clara"),
        ("Berkeley", "Alameda"),
        ("Palo Alto", "Santa Clara"),
        ("Santa Clara", "Santa Clara"),
    ]

    print(f"{'Jurisdiction':<20} {'Affordability':<15} {'Exempt':<10} {'Above-Mod %':<15}")
    print("-" * 70)

    for city, county in bay_area_cities:
        result = rhna_service.get_sb35_affordability(city, county)
        exempt_str = "Yes" if result['is_exempt'] else "No"
        progress = result['above_moderate_progress']
        progress_str = f"{progress:.1f}%" if progress is not None else "N/A"

        print(f"{city:<20} {result['percentage']}%{'':<11} {exempt_str:<10} {progress_str:<15}")


def example_5_list_by_county():
    """Example 5: List all jurisdictions in a county."""
    print_section("Example 5: Los Angeles County Jurisdictions")

    la_jurisdictions = rhna_service.list_jurisdictions(county="Los Angeles")

    print(f"Found {len(la_jurisdictions)} jurisdictions in Los Angeles County\n")

    # Group by affordability requirement
    exempt = [j for j in la_jurisdictions if j['is_exempt']]
    require_10 = [j for j in la_jurisdictions if j['affordability_pct'] == 10.0]
    require_50 = [j for j in la_jurisdictions if j['affordability_pct'] == 50.0]

    print(f"Exempt ({len(exempt)}):")
    for j in exempt[:5]:  # Show first 5
        print(f"  • {j['jurisdiction']}")
    if len(exempt) > 5:
        print(f"  ... and {len(exempt) - 5} more")

    print(f"\nRequire 10% affordable ({len(require_10)}):")
    for j in require_10[:5]:
        print(f"  • {j['jurisdiction']}")
    if len(require_10) > 5:
        print(f"  ... and {len(require_10) - 5} more")

    print(f"\nRequire 50% affordable ({len(require_50)}):")
    for j in require_50[:5]:
        print(f"  • {j['jurisdiction']}")
    if len(require_50) > 5:
        print(f"  ... and {len(require_50) - 5} more")


def example_6_fallback_behavior():
    """Example 6: Demonstrate fallback for unknown jurisdictions."""
    print_section("Example 6: Fallback Behavior")

    # Test with a fictional jurisdiction
    result = rhna_service.get_sb35_affordability("Fake City That Doesn't Exist")

    print("Lookup for unknown jurisdiction: 'Fake City That Doesn't Exist'")
    print()
    print(f"Affordability: {result['percentage']}% (estimated)")
    print(f"Source: {result['source']}")
    print()
    print("Warning notes:")
    for note in result['notes'][:6]:  # Show first few warning notes
        print(f"  • {note}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" RHNA Data Integration - Usage Examples")
    print("=" * 70)
    print("\nDemonstrating official HCD RHNA data integration for SB35")
    print("affordability determinations")

    example_1_rhna_service_basics()
    example_2_jurisdiction_lookups()
    example_3_sb35_integration()
    example_4_compare_jurisdictions()
    example_5_list_by_county()
    example_6_fallback_behavior()

    print("\n" + "=" * 70)
    print(" Examples Complete")
    print("=" * 70)
    print("\nFor more information:")
    print("  - Documentation: docs/RHNA_INTEGRATION.md")
    print("  - Research: docs/RHNA_API_RESEARCH.md")
    print("  - Service: app/services/rhna_service.py")
    print("  - Tests: tests/test_rhna_service.py")
    print()


if __name__ == "__main__":
    main()
