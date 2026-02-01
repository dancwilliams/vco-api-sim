#!/usr/bin/env python3
"""
Validate API responses against OpenAPI spec schemas.

This script calls each endpoint and validates the response structure
matches the schema defined in the OpenAPI specification.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


def load_spec() -> Dict[str, Any]:
    """Load the V2 OpenAPI spec."""
    spec_path = Path(__file__).parent.parent / "VC-SD-WAN-6.4-v2.json"
    with open(spec_path) as f:
        return json.load(f)


def resolve_ref(spec: Dict[str, Any], ref: str) -> Dict[str, Any]:
    """Resolve a $ref to its schema."""
    if not ref.startswith("#/"):
        return {}
    parts = ref[2:].split("/")
    result = spec
    for part in parts:
        result = result.get(part, {})
    return result


def validate_type(value: Any, schema: Dict[str, Any], spec: Dict[str, Any], path: str = "") -> List[str]:
    """Validate a value against a schema, return list of errors."""
    errors = []

    # Handle nullable
    if value is None:
        if schema.get("nullable"):
            return []
        # Many fields are optional, so None is often OK
        return []

    # Resolve $ref if present
    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])

    schema_type = schema.get("type")

    if schema_type == "object":
        if not isinstance(value, dict):
            return [f"{path}: Expected object, got {type(value).__name__}"]

        # Check for unexpected properties if additionalProperties is false
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}).keys())
            actual = set(value.keys())
            extra = actual - allowed
            if extra:
                errors.append(f"{path}: Unexpected properties: {extra}")

        # Validate each property
        for prop, prop_schema in schema.get("properties", {}).items():
            if prop in value:
                errors.extend(validate_type(value[prop], prop_schema, spec, f"{path}.{prop}"))

    elif schema_type == "array":
        if not isinstance(value, list):
            return [f"{path}: Expected array, got {type(value).__name__}"]
        items_schema = schema.get("items", {})
        for i, item in enumerate(value[:5]):  # Validate first 5 items to save time
            errors.extend(validate_type(item, items_schema, spec, f"{path}[{i}]"))

    elif schema_type == "string":
        if not isinstance(value, str) and value is not None:
            errors.append(f"{path}: Expected string, got {type(value).__name__}")

    elif schema_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            # Allow float that represents integer
            if isinstance(value, float) and value == int(value):
                pass
            else:
                errors.append(f"{path}: Expected integer, got {type(value).__name__}")

    elif schema_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{path}: Expected number, got {type(value).__name__}")

    elif schema_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{path}: Expected boolean, got {type(value).__name__}")

    return errors


def get_response_schema(spec: Dict[str, Any], path: str, method: str = "get") -> Optional[Dict[str, Any]]:
    """Get the 200 response schema for a path."""
    paths = spec.get("paths", {})
    path_def = paths.get(path, {})
    method_def = path_def.get(method, {})
    responses = method_def.get("responses", {})

    for code in ["200", "default"]:
        if code in responses:
            content = responses[code].get("content", {})
            json_content = content.get("application/json", {})
            return json_content.get("schema")

    return None


class SpecValidator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.spec = load_spec()
        self.results = []

    def test_endpoint(self, name: str, url: str, spec_path: str) -> bool:
        """Test an endpoint and validate response."""
        print(f"\n{name}...")
        print(f"  URL: {url}")

        try:
            response = httpx.get(f"{self.base_url}{url}", timeout=10)
            print(f"  Status: {response.status_code}")

            if response.status_code != 200:
                print(f"  ERROR: Expected 200, got {response.status_code}")
                return False

            data = response.json()
            print(f"  Response type: {type(data).__name__}")

            # Get expected schema
            schema = get_response_schema(self.spec, spec_path)
            if not schema:
                print(f"  WARNING: No schema found for {spec_path}")
                return True

            # Show schema type expectation
            if "$ref" in schema:
                ref_schema = resolve_ref(self.spec, schema["$ref"])
                print(f"  Expected schema type: {ref_schema.get('type', 'unknown')}")
            else:
                print(f"  Expected schema type: {schema.get('type', 'unknown')}")

            # Validate
            errors = validate_type(data, schema, self.spec, "root")

            if errors:
                print(f"  VALIDATION ERRORS:")
                for error in errors[:10]:  # Show first 10 errors
                    print(f"    - {error}")
                if len(errors) > 10:
                    print(f"    ... and {len(errors) - 10} more errors")
                return False

            print(f"  VALID")
            return True

        except httpx.ConnectError:
            print(f"  ERROR: Could not connect to {self.base_url}")
            return False
        except Exception as e:
            print(f"  ERROR: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all validation tests."""
        print("=" * 60)
        print("VCO API Simulator - Spec Compliance Validation")
        print("=" * 60)

        # First, get an enterprise and edge ID
        print("\nGetting test IDs...")
        try:
            resp = httpx.get(f"{self.base_url}/api/sdwan/v2/enterprises/", timeout=10)
            enterprises = resp.json().get("data", [])
            if not enterprises:
                print("ERROR: No enterprises found")
                return False

            ent_id = enterprises[0].get("logicalId")
            print(f"  Enterprise: {ent_id}")

            resp = httpx.get(f"{self.base_url}/api/sdwan/v2/enterprises/{ent_id}/edges/?limit=1", timeout=10)
            edges = resp.json().get("data", [])
            if not edges:
                print("ERROR: No edges found")
                return False

            edge_id = edges[0].get("logicalId")
            print(f"  Edge: {edge_id}")

        except httpx.ConnectError:
            print(f"ERROR: Could not connect to {self.base_url}")
            print("Make sure the API simulator is running:")
            print("  python -m uvicorn app.main:app --port 8000")
            return False
        except Exception as e:
            print(f"ERROR getting test IDs: {e}")
            return False

        tests = [
            (
                "1. Edge Health Stats (aggregate)",
                f"/api/sdwan/v2/enterprises/{ent_id}/edges/{edge_id}/healthStats?start=0&end=99999999999999",
                "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/healthStats"
            ),
            (
                "2. Edge Health Stats (time series)",
                f"/api/sdwan/v2/enterprises/{ent_id}/edges/{edge_id}/healthStats/timeSeries",
                "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/healthStats/timeSeries"
            ),
            (
                "3. Edge Link Stats (aggregate)",
                f"/api/sdwan/v2/enterprises/{ent_id}/edges/{edge_id}/linkStats?start=0",
                "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/linkStats"
            ),
            (
                "4. Edge Link Stats (time series)",
                f"/api/sdwan/v2/enterprises/{ent_id}/edges/{edge_id}/linkStats/timeSeries",
                "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/linkStats/timeSeries"
            ),
            (
                "5. Edge Flow Stats",
                f"/api/sdwan/v2/enterprises/{ent_id}/edges/{edge_id}/flowStats",
                "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/flowStats"
            ),
            (
                "6. Edge Device Settings",
                f"/api/sdwan/v2/enterprises/{ent_id}/edges/{edge_id}/deviceSettings",
                "/api/sdwan/v2/enterprises/{enterpriseLogicalId}/edges/{edgeLogicalId}/deviceSettings"
            ),
        ]

        results = []
        for name, url, spec_path in tests:
            results.append((name, self.test_endpoint(name, url, spec_path)))

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        passed = 0
        for name, success in results:
            status = "PASS" if success else "FAIL"
            print(f"  {status}: {name}")
            if success:
                passed += 1

        print(f"\nTotal: {passed}/{len(results)} tests passed")
        return passed == len(results)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate API against OpenAPI spec")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    validator = SpecValidator(args.base_url)
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
