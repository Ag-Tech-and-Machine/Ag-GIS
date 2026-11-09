"""Test lookup_vendor_mapping and lookup_unit functions."""
import sys
import os
import sqlite3
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path

# Set the environment variable for the test plugin root
os.environ['AGTECH_TEST_PLUGIN_ROOT'] = r'C:\Users\Michael\AppData\Local\hermes\ag-gis\plugins\ag_tech_tooling'

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
    """Ensure classification tables exist with correct schema and initial data."""
    cursor = conn.cursor()
    
    # Create vendor mappings table (matching the actual schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agtech_vendor_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            source_type TEXT NOT NULL,  -- 'deere-gs3', 'adapt-standard', 'custom'
            rules_json TEXT NOT NULL,
            created_utc TEXT NOT NULL,
            UNIQUE(name, version, source_type)
        )
    ''')
    
    # Create unit registry table (matching the actual schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agtech_unit_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            vendor_source TEXT NOT NULL,
            unit_token TEXT NOT NULL,
            standard_name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            created_utc TEXT NOT NULL,
            UNIQUE(name, version, vendor_source, unit_token)
        )
    ''')
    
    # Populate with initial data for vendor mappings
    cursor.execute("SELECT COUNT(*) FROM agtech_vendor_mappings WHERE name='default' AND source_type='deere-gs3'")
    if cursor.fetchone()[0] == 0:
        created_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            INSERT INTO agtech_vendor_mappings (name, version, source_type, rules_json, created_utc)
            VALUES (?, 1, ?, ?, ?)
        ''', ('default', 'deere-gs3', json.dumps({
            "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
            "planting": {"operation_family": "planting", "operation_subtype": "planting"},
            "spraying": {"operation_family": "application", "operation_subtype": "spraying"}
        }), created_utc))
    
    # Populate with initial data for units
    cursor.execute("SELECT COUNT(*) FROM agtech_unit_registry WHERE name='default' AND vendor_source='deere-gs3'")
    if cursor.fetchone()[0] == 0:
        created_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            INSERT INTO agtech_unit_registry (name, version, vendor_source, unit_token, standard_name, category, description, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('default', 1, 'deere-gs3', 'l1ha-1', 'litre_per_hectare', 'rate', 'litres per hectare', created_utc))
        cursor.execute('''
            INSERT INTO agtech_unit_registry (name, version, vendor_source, unit_token, standard_name, category, description, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('default', 1, 'deere-gs3', 'gal1ac-1', 'gallon_per_acre', 'rate', 'gallons per acre', created_utc))
        cursor.execute('''
            INSERT INTO agtech_unit_registry (name, version, vendor_source, unit_token, standard_name, category, description, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('default', 1, 'deere-gs3', 'kg1ha-1', 'kilogram_per_hectare', 'rate', 'kilograms per hectare', created_utc))
    
    conn.commit()


def setup_test_db():
    """Create a temporary database for testing with initial data."""
    temp_dir = Path(tempfile.mkdtemp(prefix='aggis-test-'))
    db_path = temp_dir / 'test.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create vendor mappings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agtech_vendor_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            source_type TEXT NOT NULL,
            rules_json TEXT NOT NULL,
            created_utc TEXT NOT NULL,
            UNIQUE(name, version, source_type)
        )
    ''')
    
    # Create unit registry table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agtech_unit_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            vendor_source TEXT NOT NULL,
            unit_token TEXT NOT NULL,
            standard_name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            created_utc TEXT NOT NULL,
            UNIQUE(name, version, vendor_source, unit_token)
        )
    ''')
    
    # Populate with initial data for vendor mappings
    cursor.execute("SELECT COUNT(*) FROM agtech_vendor_mappings WHERE name='default' AND source_type='deere-gs3'")
    if cursor.fetchone()[0] == 0:
        created_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            INSERT INTO agtech_vendor_mappings (name, version, source_type, rules_json, created_utc)
            VALUES (?, 1, ?, ?, ?)
        ''', ('default', 'deere-gs3', json.dumps({
            "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
            "planting": {"operation_family": "planting", "operation_subtype": "planting"},
            "spraying": {"operation_family": "application", "operation_subtype": "spraying"}
        }), created_utc))
    
    # Populate with initial data for units
    cursor.execute("SELECT COUNT(*) FROM agtech_unit_registry WHERE name='default' AND vendor_source='deere-gs3'")
    if cursor.fetchone()[0] == 0:
        created_utc = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            INSERT INTO agtech_unit_registry (name, version, vendor_source, unit_token, standard_name, category, description, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('default', 1, 'deere-gs3', 'l1ha-1', 'litre_per_hectare', 'rate', 'litres per hectare', created_utc))
        cursor.execute('''
            INSERT INTO agtech_unit_registry (name, version, vendor_source, unit_token, standard_name, category, description, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('default', 1, 'deere-gs3', 'gal1ac-1', 'gallon_per_acre', 'rate', 'gallons per acre', created_utc))
        cursor.execute('''
            INSERT INTO agtech_unit_registry (name, version, vendor_source, unit_token, standard_name, category, description, created_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('default', 1, 'deere-gs3', 'kg1ha-1', 'kilogram_per_hectare', 'rate', 'kilograms per hectare', created_utc))
    
    conn.commit()
    return conn, db_path


def test_lookup_vendor_mapping():
    """Test vendor mapping lookup."""
    print("=== Testing lookup_vendor_mapping ===")
    
    conn, _ = setup_test_db()
    
    # Test known operation types
    test_cases = [
        ("tillage", "deere-gs3", {"operation_family": "tillage", "operation_subtype": "tillage"}),
        ("planting", "deere-gs3", {"operation_family": "planting", "operation_subtype": "planting"}),
        ("spraying", "deere-gs3", {"operation_family": "application", "operation_subtype": "spraying"}),
        ("unknown_op", "deere-gs3", None),
    ]
    
    all_passed = True
    for op_token, source_type, expected in test_cases:
        result = lookup_vendor_mapping(op_token, source_type, conn=conn)
        # Check that result is either None or has the expected operation_family and operation_subtype
        if expected is None:
            passed = result is None
            status = "✓" if passed else "✗"
            print(f"  {status} {op_token} -> {'None' if result is None else f'{result[\"operation_family\"]}/{result[\"operation_subtype\"]}'}")
        else:
            passed = (result is not None and 
                     result['operation_family'] == expected['operation_family'] and
                     result['operation_subtype'] == expected['operation_subtype'])
            status = "✓" if passed else "✗"
            print(f"  {status} {op_token} -> {result['operation_family']}/{result['operation_subtype']}")
        
        if not passed:
            print(f"  ✗ {op_token} -> expected {expected}, got {result}")
            all_passed = False
    
    conn.close()
    return all_passed


def test_lookup_unit():
    """Test unit lookup."""
    print("\n=== Testing lookup_unit ===")
    
    conn, _ = setup_test_db()
    
    # Test known unit tokens
    test_cases = [
        ("l1ha-1", "deere-gs3", {"standard": "litre_per_hectare", "category": "rate"}),
        ("gal1ac-1", "deere-gs3", {"standard": "gallon_per_acre", "category": "rate"}),
        ("kg1ha-1", "deere-gs3", {"standard": "kilogram_per_hectare", "category": "rate"}),
        ("unknown_unit", "deere-gs3", None),
    ]
    
    all_passed = True
    for unit_token, source_type, expected in test_cases:
        result = lookup_unit(unit_token, source_type, conn=conn)
        if expected is None:
            passed = result is None
        else:
            passed = (result is not None and 
                     result['standard'] == expected['standard'] and
                     result['category'] == expected['category'])
        
        if passed:
            print(f"  ✓ {unit_token} -> {result['standard']} ({result['category']})")
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
