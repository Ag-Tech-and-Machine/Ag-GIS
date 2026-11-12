
"""Test lookup_vendor_mapping and lookup_unit functions."""
import sys
import os
import sqlite3
import tempfile
from pathlib import Path

# Set the environment variable for the test plugin root
# Use a generic path placeholder - replace with actual path before running tests
os.environ['AGTECH_TEST_PLUGIN_ROOT'] = r'C:\path\to\ag_tech_tooling\plugins'

# Add both the plugin directory and its parent to sys.path
plugins_parent = os.path.dirname(os.environ.get('AGTECH_TEST_PLUGIN_ROOT'))
sys.path.insert(0, plugins_parent)
sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT'))

from ag_tech_tooling.classification_registry import (
    lookup_vendor_mapping, lookup_unit, 
    register_vendor_mapping, register_unit
)


def get_test_db():
    """Create a temporary database for testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix='aggis-test-'))
    db_path = temp_dir / 'test.db'
    
    # Create the database and ensure tables exist
    conn = sqlite3.connect(db_path)
    ensure_classification_tables(conn)
    
    return conn, db_path


def ensure_classification_tables(conn):
    """Ensure classification tables exist."""
    # Create vendor mappings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS agtech_vendor_mappings (
            id INTEGER PRIMARY KEY,
            name TEXT,
            source_type TEXT,
            rules TEXT
        )
    ''')
    
    # Create unit registry table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS agtech_unit_registry (
            id INTEGER PRIMARY KEY,
            vendor_source TEXT,
            unit_token TEXT,
            standard_name TEXT,
            category TEXT,
            description TEXT
        )
    ''')

def test_lookup_vendor_mapping():
    """Test vendor mapping lookup."""
    print("=== Testing lookup_vendor_mapping ===")
    
    conn, db_path = get_test_db()
    
    # Test known operation types
    test_cases = [
        ("tillage", "deere-gs3", {"operation_family": "tillage", "operation_subtype": "tillage"}),
        ("planting", "deere-gs3", {"operation_family": "planting", "operation_subtype": "planting"}),
        ("spraying", "deere-gs3", {"operation_family": "application", "operation_subtype": "spraying"}),
        ("unknown_op", "deere-gs3", None),
    ]
    
    all_passed = True
    for op_token, source_type, expected in test_cases:
        result = lookup_vendor_mapping(op_token, source_type)
        if result == expected:
            print(f"  ✓ {op_token} -> {result}")
        else:
            print(f"  ✗ {op_token} -> expected {expected}, got {result}")
            all_passed = False
    
    conn.close()
    return all_passed

def test_lookup_unit():
    """Test unit lookup."""
    print("\n=== Testing lookup_unit ===")
    
    conn, db_path = get_test_db()
    
    # Test known unit tokens
    test_cases = [
        ("l1ha-1", "deere-gs3", {"standard": "litre_per_hectare", "category": "rate", "description": "litres per hectare"}),
        ("gal1ac-1", "deere-gs3", {"standard": "gallon_per_acre", "category": "rate", "description": "gallons per acre"}),
        ("kg1ha-1", "deere-gs3", {"standard": "kilogram_per_hectare", "category": "rate", "description": "kilograms per hectare"}),
        ("unknown_unit", "deere-gs3", None),
    ]
    
    all_passed = True
    for unit_token, source_type, expected in test_cases:
        result = lookup_unit(unit_token, source_type)
        if result == expected:
            print(f"  ✓ {unit_token} -> {result}")
        else:
            print(f"  ✗ {unit_token} -> expected {expected}, got {result}")
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
