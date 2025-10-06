#!/usr/bin/env python3
"""
POC Demo Script for Santa Monica Parcel Feasibility Engine

This script demonstrates the key features of the API by analyzing
several different parcel scenarios.
"""

import requests
import json
from typing import Dict, Any

API_BASE = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_health():
    """Test the health check endpoint."""
    print_section("1. Health Check")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200


def analyze_r1_parcel():
    """Analyze a single-family residential parcel."""
    print_section("2. Single-Family Residential (R1) Parcel Analysis")

    parcel_data = {
        "apn": "4276-019-030",
        "address": "123 Main Street",
        "city": "Santa Monica",
        "county": "Los Angeles",
        "zip_code": "90401",
        "lot_area_sqft": 5000,
        "zone_code": "R1",
        "existing_units": 1,
        "existing_building_sqft": 1800,
        "year_built": 1955,
        "latitude": 34.0195,
        "longitude": -118.4912
    }

    print("\nInput Parcel Data:")
    print(json.dumps(parcel_data, indent=2))

    response = requests.post(f"{API_BASE}/api/v1/analyze", json=parcel_data)
    print(f"\nResponse Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\nAnalysis Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

    return response.status_code == 200


def analyze_r2_parcel_near_transit():
    """Analyze a multi-family parcel near transit (AB 2097 applicable)."""
    print_section("3. Multi-Family (R2) Parcel Near Transit - AB 2097 Analysis")

    parcel_data = {
        "apn": "234-567-890",
        "address": "456 Colorado Avenue",
        "city": "Santa Monica",
        "county": "Los Angeles",
        "zip_code": "90401",
        "lot_area_sqft": 8000,
        "zone_code": "R2",
        "existing_units": 2,
        "existing_building_sqft": 2400,
        "year_built": 1978,
        "latitude": 34.0195,
        "longitude": -118.4912,
        "distance_to_transit_m": 300  # Within 0.5 miles - AB 2097 applies
    }

    print("\nInput Parcel Data:")
    print(json.dumps(parcel_data, indent=2))
    print("\n📍 NOTE: Parcel is 300m from transit - AB 2097 parking removal should apply")

    response = requests.post(f"{API_BASE}/api/v1/analyze", json=parcel_data)
    print(f"\nResponse Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\nAnalysis Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

    return response.status_code == 200


def analyze_commercial_conversion():
    """Analyze a commercial property for AB 2011 conversion."""
    print_section("4. Commercial Property - AB 2011 Conversion Analysis")

    parcel_data = {
        "apn": "789-012-345",
        "address": "789 Wilshire Blvd",
        "city": "Santa Monica",
        "county": "Los Angeles",
        "zip_code": "90401",
        "lot_area_sqft": 15000,
        "zone_code": "C-2",
        "existing_units": 0,
        "existing_building_sqft": 20000,
        "year_built": 1985,
        "latitude": 34.0195,
        "longitude": -118.4912,
        "land_use": "Commercial"
    }

    print("\nInput Parcel Data:")
    print(json.dumps(parcel_data, indent=2))
    print("\n🏢 NOTE: Commercial property - AB 2011 conversion opportunity")

    response = requests.post(f"{API_BASE}/api/v1/analyze", json=parcel_data)
    print(f"\nResponse Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\nAnalysis Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

    return response.status_code == 200


def get_state_law_info():
    """Retrieve information about California state housing laws."""
    print_section("5. State Housing Law Information")

    laws = ["sb9", "sb35", "ab2011", "ab2097", "density_bonus"]

    for law in laws:
        response = requests.get(f"{API_BASE}/api/v1/rules/{law}")
        if response.status_code == 200:
            info = response.json()
            print(f"\n{law.upper()}:")
            print(f"  Name: {info.get('name', 'N/A')}")
            print(f"  Description: {info.get('description', 'N/A')[:100]}...")
        else:
            print(f"\n{law.upper()}: Error retrieving information")


def main():
    """Run the complete POC demonstration."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "   Santa Monica Parcel Feasibility Engine - POC Demonstration".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    results = []

    # Test 1: Health Check
    try:
        results.append(("Health Check", test_health()))
    except Exception as e:
        print(f"\n❌ Health Check Failed: {e}")
        results.append(("Health Check", False))
        return

    # Test 2: R1 Parcel
    try:
        results.append(("R1 Parcel Analysis", analyze_r1_parcel()))
    except Exception as e:
        print(f"\n❌ R1 Parcel Analysis Failed: {e}")
        results.append(("R1 Parcel Analysis", False))

    # Test 3: R2 Parcel near Transit
    try:
        results.append(("R2 Transit Parcel", analyze_r2_parcel_near_transit()))
    except Exception as e:
        print(f"\n❌ R2 Transit Parcel Analysis Failed: {e}")
        results.append(("R2 Transit Parcel", False))

    # Test 4: Commercial Conversion
    try:
        results.append(("Commercial Conversion", analyze_commercial_conversion()))
    except Exception as e:
        print(f"\n❌ Commercial Conversion Analysis Failed: {e}")
        results.append(("Commercial Conversion", False))

    # Test 5: State Law Info
    try:
        get_state_law_info()
        results.append(("State Law Info", True))
    except Exception as e:
        print(f"\n❌ State Law Info Failed: {e}")
        results.append(("State Law Info", False))

    # Summary
    print_section("POC Demonstration Summary")
    print("\nTest Results:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\nOverall: {passed_count}/{total_count} tests passed ({100*passed_count//total_count}%)")

    print("\n" + "=" * 80)
    print("\n🎉 POC Demonstration Complete!")
    print(f"📚 API Documentation: {API_BASE}/docs")
    print(f"🔍 ReDoc Documentation: {API_BASE}/redoc")
    print("\n")


if __name__ == "__main__":
    main()
