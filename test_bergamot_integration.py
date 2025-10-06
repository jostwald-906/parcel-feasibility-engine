"""
Integration test for Bergamot scenarios with the analysis API.

This tests that Bergamot scenarios are properly generated through
the full analysis endpoint.
"""

from app.models.analysis import AnalysisRequest
from app.models.parcel import Parcel
from app.api.analyze import analyze_parcel
import asyncio


async def test_bergamot_btv_integration():
    """Test BTV district through full analysis."""
    print("\n" + "="*80)
    print("INTEGRATION TEST: Bergamot Transit Village via Analysis API")
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

    request = AnalysisRequest(
        parcel=parcel,
        include_sb9=False,
        include_sb35=False,
        include_ab2011=False,
        include_density_bonus=False,
        debug=False
    )

    print(f"\nAnalyzing parcel: {parcel.apn}")
    print(f"Zoning: {parcel.zoning_code}")
    print(f"Lot Size: {parcel.lot_size_sqft:,} sqft")

    response = await analyze_parcel(request)

    print(f"\n✓ Analysis completed")
    print(f"Applicable laws: {', '.join(response.applicable_laws)}")
    print(f"Potential incentives: {response.potential_incentives}")
    print(f"\nScenarios generated: {len(response.alternative_scenarios) + 1}")
    print(f"  - Base scenario: {response.base_scenario.scenario_name}")

    bergamot_scenarios = [s for s in response.alternative_scenarios if 'Bergamot' in s.scenario_name]
    print(f"  - Bergamot scenarios: {len(bergamot_scenarios)}")

    for scenario in bergamot_scenarios:
        print(f"    • {scenario.scenario_name}: {scenario.max_units} units, FAR {scenario.max_building_sqft / parcel.lot_size_sqft:.2f}")

    # Verify Bergamot scenarios were generated
    assert len(bergamot_scenarios) == 3, f"Expected 3 Bergamot scenarios, got {len(bergamot_scenarios)}"
    assert "Bergamot Area Plan (SMMC Chapter 9.12)" in response.applicable_laws
    assert any("Bergamot" in incentive for incentive in response.potential_incentives)

    print("\n✓ All assertions passed")
    return response


async def test_bergamot_cac_small_integration():
    """Test CAC small site through full analysis."""
    print("\n" + "="*80)
    print("INTEGRATION TEST: Bergamot CAC Small Site via Analysis API")
    print("="*80)

    parcel = Parcel(
        id=2,
        apn="4293-020-012",
        address="2525 Stewart St, Santa Monica, CA 90404",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="CAC",
        lot_size_sqft=50000,
        existing_units=0,
        overlay_codes=["BERGAMOT"]
    )

    request = AnalysisRequest(
        parcel=parcel,
        include_sb9=False,
        include_sb35=False,
        include_ab2011=False,
        include_density_bonus=False,
        debug=False
    )

    print(f"\nAnalyzing parcel: {parcel.apn}")
    print(f"Zoning: {parcel.zoning_code}")
    print(f"Lot Size: {parcel.lot_size_sqft:,} sqft (SMALL SITE)")

    response = await analyze_parcel(request)

    bergamot_scenarios = [s for s in response.alternative_scenarios if 'Bergamot' in s.scenario_name]

    print(f"\n✓ Analysis completed")
    print(f"Bergamot scenarios: {len(bergamot_scenarios)}")

    # Find Tier 3 scenario and verify it has exceptional FAR
    tier_3 = next((s for s in bergamot_scenarios if 'Tier 3' in s.scenario_name), None)
    assert tier_3 is not None, "Tier 3 scenario not found"

    tier_3_far = tier_3.max_building_sqft / parcel.lot_size_sqft
    print(f"Tier 3 FAR: {tier_3_far:.2f}")
    print(f"Tier 3 Height: {tier_3.max_height_ft} ft")
    print(f"Tier 3 Units: {tier_3.max_units}")

    assert tier_3_far == 2.5, f"Expected Tier 3 FAR 2.5 for small CAC, got {tier_3_far}"
    assert tier_3.max_height_ft == 86, f"Expected Tier 3 height 86 ft for small CAC, got {tier_3.max_height_ft}"

    print("\n✓ All assertions passed - CAC small site has exceptional Tier 3 standards")
    return response


async def test_non_bergamot_parcel():
    """Test that non-Bergamot parcels don't get Bergamot scenarios."""
    print("\n" + "="*80)
    print("INTEGRATION TEST: Non-Bergamot Parcel (should not generate scenarios)")
    print("="*80)

    parcel = Parcel(
        id=3,
        apn="1234-567-890",
        address="123 Main St, Santa Monica, CA 90404",
        city="Santa Monica",
        county="Los Angeles",
        zip_code="90404",
        zoning_code="R2",
        lot_size_sqft=5000,
        existing_units=0
    )

    request = AnalysisRequest(
        parcel=parcel,
        include_sb9=False,
        include_sb35=False,
        include_ab2011=False,
        include_density_bonus=False,
        debug=False
    )

    print(f"\nAnalyzing parcel: {parcel.apn}")
    print(f"Zoning: {parcel.zoning_code} (NOT Bergamot)")

    response = await analyze_parcel(request)

    bergamot_scenarios = [s for s in response.alternative_scenarios if 'Bergamot' in s.scenario_name]

    print(f"\n✓ Analysis completed")
    print(f"Bergamot scenarios: {len(bergamot_scenarios)}")

    assert len(bergamot_scenarios) == 0, f"Expected 0 Bergamot scenarios for R2 parcel, got {len(bergamot_scenarios)}"
    assert "Bergamot Area Plan (SMMC Chapter 9.12)" not in response.applicable_laws

    print("✓ Correctly did not generate Bergamot scenarios")
    return response


async def main():
    """Run all integration tests."""
    print("\n" + "#"*80)
    print("# BERGAMOT AREA PLAN - INTEGRATION TEST SUITE")
    print("#"*80)

    try:
        await test_bergamot_btv_integration()
        await test_bergamot_cac_small_integration()
        await test_non_bergamot_parcel()

        print("\n" + "#"*80)
        print("# ALL INTEGRATION TESTS PASSED")
        print("#"*80)
        print("\n✓ Bergamot scenarios module is fully integrated with the analysis API")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
