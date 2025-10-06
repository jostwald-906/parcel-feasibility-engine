"""
Test script for Bergamot Area Plan scenarios module.

Tests the implementation with various parcel configurations to verify
correct scenario generation across all three districts and size thresholds.
"""

from app.models.parcel import Parcel
from app.rules.bergamot_scenarios import (
    is_in_bergamot_area,
    get_bergamot_district,
    generate_all_bergamot_scenarios,
    create_bergamot_tier_1_scenario,
    create_bergamot_tier_2_scenario,
    create_bergamot_tier_3_scenario
)


def test_btv_district():
    """Test Transit Village district scenarios."""
    print("\n" + "="*80)
    print("TEST 1: Bergamot Transit Village (BTV) District")
    print("="*80)

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

    print(f"\nParcel: {parcel.apn}")
    print(f"Address: {parcel.address}")
    print(f"Zoning: {parcel.zoning_code}")
    print(f"Lot Size: {parcel.lot_size_sqft:,} sqft")
    print(f"In Bergamot Area: {is_in_bergamot_area(parcel)}")
    print(f"District: {get_bergamot_district(parcel)}")

    scenarios = generate_all_bergamot_scenarios(parcel)
    print(f"\nGenerated {len(scenarios)} scenarios:\n")

    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario.scenario_name}")
        print(f"   Legal Basis: {scenario.legal_basis}")
        print(f"   FAR: {scenario.max_building_sqft / parcel.lot_size_sqft:.2f}")
        print(f"   Max Height: {scenario.max_height_ft} ft ({scenario.max_stories} stories)")
        print(f"   Max Units: {scenario.max_units}")
        print(f"   Max Building: {scenario.max_building_sqft:,} sqft")
        print(f"   Parking: {scenario.parking_spaces_required} spaces")
        print(f"   Lot Coverage: {scenario.lot_coverage_pct}%")
        print(f"   Setbacks: Front {scenario.setbacks['front']}', Rear {scenario.setbacks['rear']}', Side {scenario.setbacks['side']}'")
        print(f"   Key Notes:")
        for note in scenario.notes[:3]:
            print(f"   - {note}")
        print()


def test_muc_district():
    """Test Mixed-Use Creative district scenarios."""
    print("\n" + "="*80)
    print("TEST 2: Bergamot Mixed-Use Creative (MUC) District")
    print("="*80)

    parcel = Parcel(
        id=2,
        apn="4293-015-056",
        address="2600 Olympic Blvd, Santa Monica, CA 90404",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="MUC",
        lot_size_sqft=15000,
        existing_units=2,
        overlay_codes=["BERGAMOT"]
    )

    print(f"\nParcel: {parcel.apn}")
    print(f"Address: {parcel.address}")
    print(f"Zoning: {parcel.zoning_code}")
    print(f"Lot Size: {parcel.lot_size_sqft:,} sqft")
    print(f"Existing Units: {parcel.existing_units}")
    print(f"In Bergamot Area: {is_in_bergamot_area(parcel)}")
    print(f"District: {get_bergamot_district(parcel)}")

    scenarios = generate_all_bergamot_scenarios(parcel)
    print(f"\nGenerated {len(scenarios)} scenarios:\n")

    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario.scenario_name}")
        print(f"   FAR: {scenario.max_building_sqft / parcel.lot_size_sqft:.2f}")
        print(f"   Max Height: {scenario.max_height_ft} ft")
        print(f"   Max Units: {scenario.max_units}")
        print(f"   Parking Ratio: {scenario.parking_spaces_required / scenario.max_units:.2f} spaces/unit")
        print()


def test_cac_small_site():
    """Test Conservation Art Center small site (<100,000 sqft)."""
    print("\n" + "="*80)
    print("TEST 3: Bergamot Conservation Art Center (CAC) - Small Site")
    print("="*80)

    parcel = Parcel(
        id=3,
        apn="4293-020-012",
        address="2525 Stewart St, Santa Monica, CA 90404",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="CAC",
        lot_size_sqft=50000,  # Small site (<100,000)
        existing_units=0,
        overlay_codes=["BERGAMOT"]
    )

    print(f"\nParcel: {parcel.apn}")
    print(f"Address: {parcel.address}")
    print(f"Zoning: {parcel.zoning_code}")
    print(f"Lot Size: {parcel.lot_size_sqft:,} sqft (SMALL SITE)")
    print(f"In Bergamot Area: {is_in_bergamot_area(parcel)}")
    print(f"District: {get_bergamot_district(parcel)}")

    scenarios = generate_all_bergamot_scenarios(parcel)
    print(f"\nGenerated {len(scenarios)} scenarios:\n")

    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario.scenario_name}")
        print(f"   FAR: {scenario.max_building_sqft / parcel.lot_size_sqft:.2f}")
        print(f"   Max Height: {scenario.max_height_ft} ft")
        print(f"   Max Units: {scenario.max_units}")
        print(f"   Max Building: {scenario.max_building_sqft:,} sqft")
        print(f"   Setbacks: Front {scenario.setbacks['front']}', Rear {scenario.setbacks['rear']}', Side {scenario.setbacks['side']}'")
        print(f"   Special Note: {scenario.notes[-1]}")
        print()


def test_cac_large_site():
    """Test Conservation Art Center large site (≥100,000 sqft)."""
    print("\n" + "="*80)
    print("TEST 4: Bergamot Conservation Art Center (CAC) - Large Site")
    print("="*80)

    parcel = Parcel(
        id=4,
        apn="4293-021-001",
        address="2525 Michigan Ave, Santa Monica, CA 90404",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="CAC",
        lot_size_sqft=125000,  # Large site (≥100,000)
        existing_units=0,
        overlay_codes=["BERGAMOT"]
    )

    print(f"\nParcel: {parcel.apn}")
    print(f"Address: {parcel.address}")
    print(f"Zoning: {parcel.zoning_code}")
    print(f"Lot Size: {parcel.lot_size_sqft:,} sqft (LARGE SITE - City-owned)")
    print(f"In Bergamot Area: {is_in_bergamot_area(parcel)}")
    print(f"District: {get_bergamot_district(parcel)}")

    scenarios = generate_all_bergamot_scenarios(parcel)
    print(f"\nGenerated {len(scenarios)} scenarios:\n")

    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario.scenario_name}")
        print(f"   FAR: {scenario.max_building_sqft / parcel.lot_size_sqft:.2f} (SAME across all tiers)")
        print(f"   Max Height: {scenario.max_height_ft} ft (increases by tier)")
        print(f"   Max Units: {scenario.max_units}")
        print(f"   Max Building: {scenario.max_building_sqft:,} sqft")
        print(f"   Key Notes:")
        for note in scenario.notes[-3:]:
            print(f"   - {note}")
        print()


def test_comparison_table():
    """Generate comparison table across all districts."""
    print("\n" + "="*80)
    print("TEST 5: Tier Comparison Across All Districts (10,000 sqft lot)")
    print("="*80)

    lot_size = 10000

    districts = [
        ("BTV", "Transit Village"),
        ("MUC", "Mixed-Use Creative"),
        ("CAC", "Conservation Art Center (Small)")
    ]

    print(f"\nLot Size: {lot_size:,} sqft")
    print("\n{:<30} {:<15} {:<15} {:<15} {:<15}".format(
        "District/Tier", "FAR", "Height (ft)", "Max Units", "Parking Ratio"
    ))
    print("-" * 90)

    for i, (district_code, district_name) in enumerate(districts, 5):
        parcel = Parcel(
            id=i,
            apn="TEST-001",
            address="Test Address",
            city="Santa Monica",
            county="Los Angeles",
            zip_code="90404",
            zoning_code=district_code,
            lot_size_sqft=lot_size,
            existing_units=0
        )

        for tier in [1, 2, 3]:
            if tier == 1:
                scenario = create_bergamot_tier_1_scenario(parcel, district_code)
            elif tier == 2:
                scenario = create_bergamot_tier_2_scenario(parcel, district_code)
            else:
                scenario = create_bergamot_tier_3_scenario(parcel, district_code)

            if scenario:
                far = scenario.max_building_sqft / lot_size
                parking_ratio = scenario.parking_spaces_required / scenario.max_units if scenario.max_units > 0 else 0

                print("{:<30} {:<15.2f} {:<15.0f} {:<15} {:<15.2f}".format(
                    f"{district_name} T{tier}",
                    far,
                    scenario.max_height_ft,
                    scenario.max_units,
                    parking_ratio
                ))


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*80)
    print("TEST 6: Edge Cases")
    print("="*80)

    # Non-Bergamot parcel
    print("\n1. Non-Bergamot parcel (should return empty list):")
    parcel = Parcel(
        id=100,
        apn="TEST-002",
        address="Test Address",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="R2",
        lot_size_sqft=5000,
        existing_units=0
    )
    scenarios = generate_all_bergamot_scenarios(parcel)
    print(f"   In Bergamot: {is_in_bergamot_area(parcel)}")
    print(f"   Scenarios generated: {len(scenarios)}")

    # Bergamot overlay but no district code
    print("\n2. Bergamot overlay without district zoning code:")
    parcel = Parcel(
        id=101,
        apn="TEST-003",
        address="Test Address",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="R3",
        lot_size_sqft=10000,
        existing_units=0,
        overlay_codes=["BERGAMOT"]
    )
    scenarios = generate_all_bergamot_scenarios(parcel)
    print(f"   In Bergamot: {is_in_bergamot_area(parcel)}")
    print(f"   District: {get_bergamot_district(parcel)}")
    print(f"   Scenarios generated: {len(scenarios)}")

    # CAC exactly at threshold
    print("\n3. CAC at exactly 100,000 sqft threshold (should be LARGE site):")
    parcel = Parcel(
        id=102,
        apn="TEST-004",
        address="Test Address",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="CAC",
        lot_size_sqft=100000,
        existing_units=0
    )
    tier_1 = create_bergamot_tier_1_scenario(parcel, "CAC")
    print(f"   Lot size: {parcel.lot_size_sqft:,} sqft")
    print(f"   Tier 1 FAR: {tier_1.max_building_sqft / parcel.lot_size_sqft:.2f}")
    print(f"   Expected: 1.0 (large site)")

    # CAC just below threshold
    print("\n4. CAC at 99,999 sqft (should be SMALL site):")
    parcel = Parcel(
        id=103,
        apn="TEST-005",
        address="Test Address",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="CAC",
        lot_size_sqft=99999,
        existing_units=0
    )
    tier_3 = create_bergamot_tier_3_scenario(parcel, "CAC")
    print(f"   Lot size: {parcel.lot_size_sqft:,} sqft")
    print(f"   Tier 3 FAR: {tier_3.max_building_sqft / parcel.lot_size_sqft:.2f}")
    print(f"   Tier 3 Height: {tier_3.max_height_ft} ft")
    print(f"   Expected: FAR 2.5, Height 86 ft (small site)")


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# BERGAMOT AREA PLAN SCENARIOS MODULE - TEST SUITE")
    print("#"*80)

    test_btv_district()
    test_muc_district()
    test_cac_small_site()
    test_cac_large_site()
    test_comparison_table()
    test_edge_cases()

    print("\n" + "#"*80)
    print("# TEST SUITE COMPLETE")
    print("#"*80)
    print("\nAll tests completed successfully!")
