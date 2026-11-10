
"""Test lookup_vendor_mapping and lookup_unit functions."""
import sys
import os
from pathlib import Path

# Set the environment variable for the test plugin root
os.environ['AGTECH_TEST_PLUGIN_ROOT'] = r'{USER_HOME}

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT'))

from ag_tech_tooling.classification_registry import lookup_vendor_mapping, lookup_unit

def test_lookup_vendor_mapping():
    """Test vendor mapping lookup."""
    print("=== Testing lookup_vendor_mapping ===")
    
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
    
    return all_passed

def test_lookup_unit():
    """Test unit lookup."""
    print("\n=== Testing lookup_unit ===")
    
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
