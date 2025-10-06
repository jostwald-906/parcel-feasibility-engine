"""
Example usage of Bergamot Area Plan scenarios module.

This demonstrates how to analyze a Bergamot parcel and interpret results.
"""

from app.models.parcel import Parcel
from app.rules.bergamot_scenarios import (
    is_in_bergamot_area,
    get_bergamot_district,
    generate_all_bergamot_scenarios
)


def example_btv_analysis():
    """Example: Analyzing a Transit Village parcel."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Transit Village (BTV) Parcel Analysis")
    print("="*80)

    # Create a parcel in the Bergamot Transit Village district
    parcel = Parcel(
        id=1,
        apn="4293-012-034",
        address="2525 Michigan Ave, Santa Monica, CA 90404",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="BTV",
        lot_size_sqft=25000,
        existing_units=0,
        overlay_codes=["BERGAMOT"]
    )

    print(f"\nParcel Information:")
    print(f"  APN: {parcel.apn}")
    print(f"  Address: {parcel.address}")
    print(f"  Zoning: {parcel.zoning_code}")
    print(f"  Lot Size: {parcel.lot_size_sqft:,} sqft")

    # Check if parcel is in Bergamot area
    if not is_in_bergamot_area(parcel):
        print("\n⚠ Parcel is NOT in Bergamot Area Plan")
        return

    # Get district
    district = get_bergamot_district(parcel)
    district_names = {
        'BTV': 'Transit Village',
        'MUC': 'Mixed-Use Creative',
        'CAC': 'Conservation Art Center'
    }
    print(f"\n✓ Bergamot District: {district_names.get(district, district)}")

    # Generate scenarios
    scenarios = generate_all_bergamot_scenarios(parcel)
    print(f"\n✓ Generated {len(scenarios)} development scenarios:")

    # Display each scenario
    for i, scenario in enumerate(scenarios, 1):
        far = scenario.max_building_sqft / parcel.lot_size_sqft
        parking_ratio = scenario.parking_spaces_required / scenario.max_units if scenario.max_units > 0 else 0

        print(f"\n--- Scenario {i}: {scenario.scenario_name} ---")
        print(f"Legal Basis: {scenario.legal_basis}")
        print(f"\nDevelopment Potential:")
        print(f"  • Max Units: {scenario.max_units}")
        print(f"  • Max Building Area: {scenario.max_building_sqft:,} sqft")
        print(f"  • FAR: {far:.2f}")
        print(f"  • Max Height: {scenario.max_height_ft} ft ({scenario.max_stories} stories)")
        print(f"\nRequirements:")
        print(f"  • Parking: {scenario.parking_spaces_required} spaces ({parking_ratio:.2f} per unit)")
        print(f"  • Affordable Units: {scenario.affordable_units_required}")
        print(f"  • Lot Coverage: {scenario.lot_coverage_pct}%")
        print(f"\nSetbacks:")
        print(f"  • Front: {scenario.setbacks['front']} ft")
        print(f"  • Rear: {scenario.setbacks['rear']} ft")
        print(f"  • Side: {scenario.setbacks['side']} ft")
        print(f"\nKey Notes:")
        for note in scenario.notes[:4]:
            print(f"  • {note}")

    # Analysis summary
    print("\n" + "-"*80)
    print("ANALYSIS SUMMARY")
    print("-"*80)
    print(f"Development Range: {scenarios[0].max_units} - {scenarios[-1].max_units} units")
    print(f"FAR Range: {scenarios[0].max_building_sqft / parcel.lot_size_sqft:.2f} - {scenarios[-1].max_building_sqft / parcel.lot_size_sqft:.2f}")
    print(f"Height Range: {scenarios[0].max_height_ft} - {scenarios[-1].max_height_ft} ft")
    print("\nRecommendation:")
    print(f"  • Tier 1 provides {scenarios[0].max_units} units as-of-right (no community benefits)")
    print(f"  • Tier 2 adds {scenarios[1].max_units - scenarios[0].max_units} units with community benefits")
    print(f"  • Tier 3 adds {scenarios[2].max_units - scenarios[1].max_units} more units with substantial benefits")
    print("\nNext Steps:")
    print("  1. Confirm current tier designation with Planning Department")
    print("  2. Evaluate community benefit options for tier upgrade")
    print("  3. Consider combining with State Density Bonus for additional units")
    print("  4. Review Expo Line integration requirements")


def example_cac_comparison():
    """Example: Comparing CAC small vs large site standards."""
    print("\n" + "="*80)
    print("EXAMPLE 2: CAC Small Site vs Large Site Comparison")
    print("="*80)

    # Small site
    small_site = Parcel(
        id=2,
        apn="CAC-SMALL-001",
        address="Small CAC Site",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="CAC",
        lot_size_sqft=50000,  # < 100,000 sqft
        existing_units=0
    )

    # Large site
    large_site = Parcel(
        id=3,
        apn="CAC-LARGE-001",
        address="Large CAC Site",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="CAC",
        lot_size_sqft=125000,  # >= 100,000 sqft
        existing_units=0
    )

    print("\nComparing CAC development standards:\n")
    print(f"{'Tier':<15} {'Small Site (50k sqft)':<30} {'Large Site (125k sqft)':<30}")
    print("-" * 75)

    small_scenarios = generate_all_bergamot_scenarios(small_site)
    large_scenarios = generate_all_bergamot_scenarios(large_site)

    for i in range(3):
        small = small_scenarios[i]
        large = large_scenarios[i]

        small_far = small.max_building_sqft / small_site.lot_size_sqft
        large_far = large.max_building_sqft / large_site.lot_size_sqft

        tier_name = f"Tier {i+1}"
        small_info = f"FAR {small_far:.1f}, {small.max_height_ft:.0f} ft, {small.max_units} units"
        large_info = f"FAR {large_far:.1f}, {large.max_height_ft:.0f} ft, {large.max_units} units"

        print(f"{tier_name:<15} {small_info:<30} {large_info:<30}")

    print("\nKey Differences:")
    print("  • Small sites: FAR increases dramatically at Tier 3 (2.5)")
    print("  • Large sites: FAR constant (1.0), height increases for cultural facilities")
    print("  • Small sites: More generous setbacks and lower lot coverage")
    print("  • Both: Emphasis on arts, cultural uses, and museum-quality character")


def example_district_comparison():
    """Example: Compare all three districts at same lot size."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Cross-District Comparison (10,000 sqft lot)")
    print("="*80)

    lot_size = 10000
    districts = [
        ('BTV', 'Transit Village'),
        ('MUC', 'Mixed-Use Creative'),
        ('CAC', 'Conservation Art Center')
    ]

    print(f"\nAll parcels: {lot_size:,} sqft lot size\n")

    for district_code, district_name in districts:
        print(f"\n{district_name} ({district_code}):")
        print("-" * 60)

        parcel = Parcel(
            id=100,
            apn=f"{district_code}-TEST",
            address=f"Test {district_name}",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90404",
            zoning_code=district_code,
            lot_size_sqft=lot_size,
            existing_units=0
        )

        scenarios = generate_all_bergamot_scenarios(parcel)

        for scenario in scenarios:
            far = scenario.max_building_sqft / lot_size
            tier = "Tier 1" if "Tier 1" in scenario.scenario_name else \
                  "Tier 2" if "Tier 2" in scenario.scenario_name else "Tier 3"

            print(f"  {tier}: {scenario.max_units:2d} units | FAR {far:.2f} | "
                  f"{scenario.max_height_ft:3.0f} ft | "
                  f"{scenario.parking_spaces_required:2d} parking")

    print("\nDistrict Characteristics:")
    print("  • BTV: Highest density, transit-oriented, urban character")
    print("  • MUC: Moderate density, creative/arts focus, flexible uses")
    print("  • CAC: Cultural focus, museum quality, more open space")


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# BERGAMOT AREA PLAN - USAGE EXAMPLES")
    print("#"*80)

    example_btv_analysis()
    example_cac_comparison()
    example_district_comparison()

    print("\n" + "#"*80)
    print("# EXAMPLES COMPLETE")
    print("#"*80)
    print("\nFor more information:")
    print("  • Module: app/rules/bergamot_scenarios.py")
    print("  • Tests: test_bergamot_scenarios.py")
    print("  • Integration: test_bergamot_integration.py")
    print("  • Documentation: BERGAMOT_IMPLEMENTATION_SUMMARY.md")
    print()
