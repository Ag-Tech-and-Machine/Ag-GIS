"""Test lookup_vendor_mapping and lookup_unit functions."""
import sys
import os
import sqlite3
import tempfile
from pathlib import Path

# Set the environment variable for the test plugin root
plugin_root = Path(__file__).parent  # Go to worktrees/wip-2026-11-06-recovery
plugin_root = plugin_root / "plugins"
os.environ['AGTECH_TEST_PLUGIN_ROOT'] = str(plugin_root)

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT'))

from ag_tech_tooling.classification_registry import (
    lookup_vendor_mapping, lookup_unit,
    ensure_classification_tables, register_vendor_mapping, register_unit
)

_test_conn = None

def get_test_conn():
    """Get a test SQLite connection with sample data.
    
    Returns the same connection on subsequent calls to avoid creating new databases.
    If the connection is closed, it creates a new one.
    """
    global _test_conn
    if _test_conn is None:
        test_db = Path(tempfile.mkdtemp()) / "test.db"
        conn = sqlite3.connect(str(test_db))
        ensure_classification_tables(conn)

        vendor_rules = {
            "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
            "planting": {"operation_family": "planting", "operation_subtype": "planting"},
            "spraying": {"operation_family": "application", "operation_subtype": "spraying"},
        }
        register_vendor_mapping(conn, "default", "deere-gs3", vendor_rules)

        # Register test units (one at a time)
        register_unit(conn, "deere-gs3", "litre_per_hectare", "litre_per_hectare", "rate", "litres per hectare")
        register_unit(conn, "deere-gs3", "gallon_per_acre", "gallon_per_acre", "rate", "gallons per acre")
        register_unit(conn, "deere-gs3", "kilogram_per_hectare", "kilogram_per_hectare", "rate", "kilograms per hectare")

        _test_conn = conn
    else:
        # Check if the connection is still valid
        try:
            _test_conn.execute("SELECT 1")
        except sqlite3.Error:
            # Connection is closed, create a new one
            test_db = Path(tempfile.mkdtemp()) / "test.db"
            conn = sqlite3.connect(str(test_db))
            ensure_classification_tables(conn)

            vendor_rules = {
                "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
                "planting": {"operation_family": "planting", "operation_subtype": "planting"},
                "spraying": {"operation_family": "application", "operation_subtype": "spraying"},
            }
            register_vendor_mapping(conn, "default", "deere-gs3", vendor_rules)

            # Register test units (one at a time)
            register_unit(conn, "deere-gs3", "litre_per_hectare", "litre_per_hectare", "rate", "litres per hectare")
            register_unit(conn, "deere-gs3", "gallon_per_acre", "gallon_per_acre", "rate", "gallons per acre")
            register_unit(conn, "deere-gs3", "kilogram_per_hectare", "kilogram_per_hectare", "rate", "kilograms per hectare")

            _test_conn = conn

    return _test_conn

def test_lookup_vendor_mapping():
    """Test vendor mapping lookup."""
    print("=== Testing lookup_vendor_mapping ===")
    
    conn = get_test_conn()
    test_cases = [
        ("tillage", "deere-gs3", {"operation_family": "tillage", "operation_subtype": "tillage"}),
        ("planting", "deere-gs3", {"operation_family": "planting", "operation_subtype": "planting"}),
        ("spraying", "deere-gs3", {"operation_family": "application", "operation_subtype": "spraying"}),
        ("unknown_op", "deere-gs3", None),
    ]
    
    all_passed = True
    for op_token, source_type, expected_fields in test_cases:
        result = lookup_vendor_mapping(op_token, source_type, conn=conn)
        if result is None and expected_fields is None:
            print(f"  ✓ {op_token} -> None (as expected)")
        elif result is None:
            print(f"  ✗ {op_token} -> expected {expected_fields}, got None")
            all_passed = False
        else:
            # Check if expected fields are present in result
            match = all(result.get(key) == expected_fields.get(key) for key in expected_fields)
            if match:
                print(f"  ✓ {op_token} -> {result}")
            else:
                print(f"  ✗ {op_token} -> expected {expected_fields}, got {result}")
                all_passed = False
    
    conn.close()
    return all_passed


def test_lookup_unit():
    """Test unit lookup."""
    print("\n=== Testing lookup_unit ===")
    
    conn = get_test_conn()
    test_cases = [
        ("litre_per_hectare", "deere-gs3", {"standard": "litre_per_hectare", "category": "rate", "description": "litres per hectare"}),
        ("gallon_per_acre", "deere-gs3", {"standard": "gallon_per_acre", "category": "rate", "description": "gallons per acre"}),
        ("kilogram_per_hectare", "deere-gs3", {"standard": "kilogram_per_hectare", "category": "rate", "description": "kilograms per hectare"}),
        ("unknown_unit", "deere-gs3", None),
    ]
    
    all_passed = True
    for unit_token, source_type, expected_fields in test_cases:
        result = lookup_unit(unit_token, source_type, conn=conn)
        if result is None and expected_fields is None:
            print(f"  ✓ {unit_token} -> None (as expected)")
        elif result is None:
            print(f"  ✗ {unit_token} -> expected {expected_fields}, got None")
            all_passed = False
        else:
            # Check if expected fields are present in result
            match = all(result.get(key) == expected_fields.get(key) for key in expected_fields)
            if match:
                print(f"  ✓ {unit_token} -> {result}")
            else:
                print(f"  ✗ {unit_token} -> expected {expected_fields}, got {result}")
                all_passed = False
    
    # Test bug fix: lookup should work when unit_token != standard_name
    # This is a regression test for a bug where lookup_unit incorrectly required
    # unit_token == standard_name in the SQL query
    print("\n=== Regression test: unit_token != standard_name ===")
    # Register a unit with different token and standard_name
    register_unit(conn, "deere-gs3", "lph_internal", "litres_per_ha", "rate", "Internal token for litres per hectare")
    register_unit(conn, "deere-gs3", "gpa_internal", "gallons_per_acre", "rate", "Internal token for gallons per acre")
    
    # These should now work (before the fix, they would return None)
    result1 = lookup_unit("lph_internal", "deere-gs3", conn=conn)
    if result1 and result1["standard"] == "litres_per_ha":
        print(f"  ✓ lph_internal (token) != litres_per_ha (standard) -> {result1['standard']}")
    else:
        print(f"  ✗ lph_internal lookup failed: {result1}")
        all_passed = False
    
    result2 = lookup_unit("gpa_internal", "deere-gs3", conn=conn)
    if result2 and result2["standard"] == "gallons_per_acre":
        print(f"  ✓ gpa_internal (token) != gallons_per_acre (standard) -> {result2['standard']}")
    else:
        print(f"  ✗ gpa_internal lookup failed: {result2}")
        all_passed = False
    
    conn.close()
    return all_passed

if __name__ == "__main__":
    print("Testing classification_registry lookup functions")
    print("=" * 50)
    
    result1 = test_lookup_vendor_mapping()
    result2 = test_lookup_unit()
    
    print("\n" + "=" * 50)
    if result1 and result2:
        print("All tests passed!")
    else:
        print("Some tests failed!")
