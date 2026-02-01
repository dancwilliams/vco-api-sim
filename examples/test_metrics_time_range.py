#!/usr/bin/env python3
"""
Test script to verify custom time range support for metrics endpoints.

Note: This script tests the spec-compliant response format where:
- healthStats/timeSeries returns {_href, series: [{metric, data: [...]}]}
- linkStats/timeSeries returns array of [{link, series: [...]}]
"""
import httpx
from datetime import datetime, timedelta
import json
import argparse


BASE_URL = "http://localhost:8000"
ENTERPRISE_ID = None  # Will be populated dynamically
EDGE_ID = None  # Will be populated dynamically


def get_test_ids(base_url: str) -> tuple:
    """Get enterprise and edge IDs from the API."""
    resp = httpx.get(f"{base_url}/api/sdwan/v2/enterprises/", timeout=10)
    enterprises = resp.json().get("data", [])
    if not enterprises:
        raise RuntimeError("No enterprises found")

    ent_id = enterprises[0].get("logicalId")

    resp = httpx.get(f"{base_url}/api/sdwan/v2/enterprises/{ent_id}/edges/?limit=1", timeout=10)
    edges = resp.json().get("data", [])
    if not edges:
        raise RuntimeError("No edges found")

    edge_id = edges[0].get("logicalId")
    return ent_id, edge_id


def test_default_time_range():
    """Test default behavior (last 1 hour, 5-minute intervals)."""
    print("\n1. Testing default time range (last 1 hour)...")
    url = f"{BASE_URL}/api/sdwan/v2/enterprises/{ENTERPRISE_ID}/edges/{EDGE_ID}/healthStats/timeSeries"

    response = httpx.get(url, timeout=10)
    data = response.json()

    print(f"   Status: {response.status_code}")

    # New format: {_href, series: [{metric, data: [...]}]}
    series = data.get('series', [])
    print(f"   Number of metrics: {len(series)}")

    if series:
        # Check first metric's data points
        first_metric = series[0]
        data_points = first_metric.get('data', [])
        print(f"   First metric: {first_metric.get('metric')}")
        print(f"   Data points: {len(data_points)}")
        print(f"   Expected: ~12-13 points (60 min / 5 min intervals)")

    return response.status_code == 200 and len(series) > 0


def test_custom_time_range_6_hours():
    """Test 6-hour time range with Unix timestamps."""
    print("\n2. Testing 6-hour time range (Unix milliseconds)...")

    end = datetime.utcnow()
    start = end - timedelta(hours=6)

    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    url = f"{BASE_URL}/api/sdwan/v2/enterprises/{ENTERPRISE_ID}/edges/{EDGE_ID}/healthStats/timeSeries"
    params = {"start": start_ms, "end": end_ms}

    response = httpx.get(url, params=params, timeout=10)
    data = response.json()

    print(f"   Status: {response.status_code}")

    series = data.get('series', [])
    if series:
        data_points = series[0].get('data', [])
        print(f"   Data points: {len(data_points)}")
        print(f"   Expected: ~72-73 points (360 min / 5 min intervals)")

    return response.status_code == 200


def test_custom_time_range_iso8601():
    """Test time range with ISO 8601 format."""
    print("\n3. Testing time range with ISO 8601 format...")

    end = datetime.utcnow()
    start = end - timedelta(hours=3)

    start_iso = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"{BASE_URL}/api/sdwan/v2/enterprises/{ENTERPRISE_ID}/edges/{EDGE_ID}/linkStats/timeSeries"
    params = {"start": start_iso, "end": end_iso}

    response = httpx.get(url, params=params, timeout=10)
    data = response.json()

    print(f"   Status: {response.status_code}")
    print(f"   Response type: {type(data).__name__}")

    # New format: array of [{link, series: [...]}]
    if isinstance(data, list) and len(data) > 0:
        first_link = data[0]
        series = first_link.get('series', [])
        print(f"   Number of links: {len(data)}")
        print(f"   Series per link: {len(series)}")
        if series:
            print(f"   Expected: ~36-37 data points per metric (180 min / 5 min intervals)")

    return response.status_code == 200


def test_custom_interval():
    """Test custom interval (10 minutes)."""
    print("\n4. Testing custom interval (10 minutes)...")

    url = f"{BASE_URL}/api/sdwan/v2/enterprises/{ENTERPRISE_ID}/edges/{EDGE_ID}/healthStats/timeSeries"
    params = {"interval": 10}

    response = httpx.get(url, params=params, timeout=10)
    data = response.json()

    print(f"   Status: {response.status_code}")

    series = data.get('series', [])
    if series:
        data_points = series[0].get('data', [])
        print(f"   Data points: {len(data_points)}")
        print(f"   Expected: ~6-7 points (60 min / 10 min intervals)")

    return response.status_code == 200


def test_combined_time_and_interval():
    """Test custom time range + custom interval."""
    print("\n5. Testing 12-hour range with 15-minute intervals...")

    end = datetime.utcnow()
    start = end - timedelta(hours=12)

    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    url = f"{BASE_URL}/api/sdwan/v2/enterprises/{ENTERPRISE_ID}/edges/{EDGE_ID}/linkStats/timeSeries"
    params = {"start": start_ms, "end": end_ms, "interval": 15}

    response = httpx.get(url, params=params, timeout=10)
    data = response.json()

    print(f"   Status: {response.status_code}")

    if isinstance(data, list) and len(data) > 0:
        first_link = data[0]
        series = first_link.get('series', [])
        if series:
            data_points = series[0].get('data', [])
            print(f"   Data points per metric: {len(data_points)}")
            print(f"   Expected: ~48-49 points (720 min / 15 min intervals)")

    return response.status_code == 200


def test_only_end_specified():
    """Test with only end time specified (should default to 1 hour before end)."""
    print("\n6. Testing with only end time specified...")

    end = datetime.utcnow() - timedelta(hours=2)
    end_ms = int(end.timestamp() * 1000)

    url = f"{BASE_URL}/api/sdwan/v2/enterprises/{ENTERPRISE_ID}/edges/{EDGE_ID}/healthStats/timeSeries"
    params = {"end": end_ms}

    response = httpx.get(url, params=params, timeout=10)
    data = response.json()

    print(f"   Status: {response.status_code}")

    series = data.get('series', [])
    if series:
        data_points = series[0].get('data', [])
        print(f"   Data points: {len(data_points)}")
        print(f"   Expected: ~12-13 points (defaults to 1 hour before end)")

    return response.status_code == 200


def main():
    global BASE_URL, ENTERPRISE_ID, EDGE_ID

    parser = argparse.ArgumentParser(description="Test metrics time range endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    BASE_URL = args.base_url

    print("=" * 60)
    print("VCO API Simulator - Metrics Time Range Tests")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")

    # Get dynamic IDs
    try:
        ENTERPRISE_ID, EDGE_ID = get_test_ids(BASE_URL)
        print(f"Enterprise: {ENTERPRISE_ID}")
        print(f"Edge: {EDGE_ID}")
    except Exception as e:
        print(f"ERROR getting test IDs: {e}")
        return False

    tests = [
        ("Default time range", test_default_time_range),
        ("6-hour range (Unix ms)", test_custom_time_range_6_hours),
        ("ISO 8601 format", test_custom_time_range_iso8601),
        ("Custom interval", test_custom_interval),
        ("Combined params", test_combined_time_and_interval),
        ("Only end specified", test_only_end_specified),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"   ERROR: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
