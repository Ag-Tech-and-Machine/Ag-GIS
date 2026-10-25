# SPDX-License-Identifier: GPL-2.0-or-later
"""Test durable GeoPackage classification storage with vendor mapping/version/unit registry.

Does not require QGIS. Tests additive storage, unknown value preservation, and
backward compatibility with existing catalogue.
"""
import json
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone
import sys

# Import path setup (match classification_test.py pattern)
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

from ag_tech_tooling.classification_registry import (
    ensure_classification_tables,
    register_vendor_mapping,
    register_unit,
    classify_with_storage,
    get_classifications_for_dataset,
    get_latest_classification_for_dataset,
    ensure_catalogue_has_classification_column,
)


def create_test_workspace() -> tuple:
    """Create a minimal test workspace with existing farm.gpkg."""
    # Create a temporary workspace
    workspace_dir = Path(tempfile.mkdtemp(prefix="aggis-class-test-"))
    data_dir = workspace_dir / "Data"
    data_dir.mkdir()
    
    # Create a minimal farm.gpkg with existing agtech_datasets table
    db_path = data_dir / "farm.gpkg"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create existing catalogue structure (without classification_id)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agtech_datasets (
        id TEXT PRIMARY KEY,
        field_id TEXT NOT NULL,
        name TEXT,
        role TEXT,
        layer_type TEXT,
        provider TEXT,
        uri TEXT,
        crs_wkt TEXT,
        source_uri TEXT,
        source_hash TEXT,
        created_utc TEXT,
        style_xml TEXT,
        catalog_version TEXT,
        UNIQUE(id)
    )
    """)
    
    # Insert a sample dataset
    cursor.execute("""
    INSERT OR REPLACE INTO agtech_datasets (id, field_id, name, role, created_utc, catalog_version)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ("abc123", "field_001", "test-layer", "operation",
          datetime.now(timezone.utc).isoformat(), "1"))
    
    conn.commit()
    conn.close()
    
    return workspace_dir, str(db_path)


def test_ensure_classification_tables():
    """Test that classification tables are created additively."""
    workspace_dir, db_path = create_test_workspace()
    
    conn = sqlite3.connect(db_path)
    ensure_classification_tables(conn)
    conn.close()
    
    # Verify tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert "agtech_classifications" in tables, "Classification table should exist"
    assert "agtech_vendor_mappings" in tables, "Vendor mappings table should exist"
    assert "agtech_unit_registry" in tables, "Unit registry table should exist"
    
    # Verify indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%classifications%'")
    indexes = [row[0] for row in cursor.fetchall()]
    assert "idx_classifications_dataset" in indexes, "Dataset index should exist"
    assert "idx_classifications_field" in indexes, "Field index should exist"
    
    conn.close()
    print("PASS: test_ensure_classification_tables")


def test_register_vendor_mapping():
    """Test vendor mapping registration."""
    workspace_dir, db_path = create_test_workspace()
    
    conn = sqlite3.connect(db_path)
    ensure_classification_tables(conn)
    
    # Register a mapping
    mapping_name = register_vendor_mapping(conn, "deere-gs3", "deere-gs3", {
        "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
        "planting": {"operation_family": "planting", "operation_subtype": "planting"},
        "spraying": {"operation_family": "application", "operation_subtype": "spraying"},
    })
    
    assert mapping_name == "deere-gs3", "Should return mapping name"
    
    # Verify it was stored
    cursor = conn.cursor()
    cursor.execute("SELECT name, version, source_type FROM agtech_vendor_mappings WHERE name='deere-gs3'")
    row = cursor.fetchone()
    assert row is not None, "Mapping should be stored"
    assert row[1] == 1, "Version should be 1"
    assert row[2] == "deere-gs3", "Source type should match"
    
    conn.close()
    print("PASS: test_register_vendor_mapping")


def test_register_unit():
    """Test unit registry registration."""
    workspace_dir, db_path = create_test_workspace()
    
    conn = sqlite3.connect(db_path)
    ensure_classification_tables(conn)
    
    unit_name = register_unit(conn, "deere-gs3", "l1ha-1", "litre_per_hectare", "rate", "litres per hectare")
    
    assert unit_name == "default", "Should return unit name"
    
    # Verify it was stored
    cursor = conn.cursor()
    cursor.execute("SELECT unit_token, standard_name, category FROM agtech_unit_registry WHERE unit_token='l1ha-1'")
    row = cursor.fetchone()
    assert row is not None, "Unit should be stored"
    assert row[1] == "litre_per_hectare", "Standard name should match"
    assert row[2] == "rate", "Category should match"
    
    conn.close()
    print("PASS: test_register_unit")


def test_classify_with_storage():
    """Test classification storage with unknown value preservation."""
    workspace_dir, db_path = create_test_workspace()
    
    conn = sqlite3.connect(db_path)
    ensure_classification_tables(conn)
    
    # Register a vendor mapping for vendor_source
    register_vendor_mapping(conn, "deere-gs3", "deere-gs3", {
        "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
    })
    
    # Create a classification with unknown values
    classification_id = classify_with_storage(
        conn,
        dataset_id="abc123",
        purpose="operation",
        operation_family="tillage",
        operation_subtype="primary-tillage",
        measurement="",  # Unknown
        unit="",  # Unknown
        semantics="result",
        field_id="field_001",
        season_id="season_001",
        source_value="TILLAGE_01",  # Original source value preserved
        vendor_source="deere-gs3"
    )
    
    assert classification_id is not None, "Should return classification ID"
    
    # Retrieve and verify
    classifications = get_classifications_for_dataset(conn, "abc123")
    assert len(classifications) == 1, "Should have one classification"
    
    c = classifications[0]
    assert c["dataset_id"] == "abc123", "Dataset ID should match"
    assert c["source_value"] == "TILLAGE_01", "Source value should be preserved"
    assert c["field_id"] == "field_001", "Field ID should match"
    assert c["semantics"] == "result", "Semantics should match"
    
    conn.close()
    print("PASS: test_classify_with_storage")


def test_get_latest_classification():
    """Test getting the latest classification."""
    workspace_dir, db_path = create_test_workspace()
    
    conn = sqlite3.connect(db_path)
    ensure_classification_tables(conn)
    
    # Register a vendor mapping
    register_vendor_mapping(conn, "deere-gs3", "deere-gs3", {
        "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
    })
    
    # Create multiple classifications
    for i in range(3):
        classify_with_storage(
            conn,
            dataset_id="abc123",
            purpose="operation",
            operation_family=f"family_{i}",
            operation_subtype=f"subtype_{i}",
            semantics="result"
        )
    
    latest = get_latest_classification_for_dataset(conn, "abc123")
    assert latest is not None, "Should return latest classification"
    assert latest["operation_family"] == "family_2", "Should be the latest"
    
    conn.close()
    print("PASS: test_get_latest_classification")


def test_catalogue_migration():
    """Test backward-compatible catalogue column addition."""
    workspace_dir, db_path = create_test_workspace()
    
    conn = sqlite3.connect(db_path)
    
    # First pass: column doesn't exist
    added = ensure_catalogue_has_classification_column(conn)
    assert added == True, "Should add column on first pass"
    
    # Second pass: column exists
    added_again = ensure_catalogue_has_classification_column(conn)
    assert added_again == False, "Should not add column on second pass"
    
    # Verify column exists and has NULL values (backward compatible)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(agtech_datasets)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "classification_id" in columns, "Column should exist"
    
    # Verify existing data is preserved
    cursor.execute("SELECT id, name FROM agtech_datasets")
    rows = cursor.fetchall()
    assert len(rows) == 1, "Original data should be preserved"
    assert rows[0][1] == "test-layer", "Name should match"
    
    conn.close()
    print("PASS: test_catalogue_migration")


def test_unknown_value_preservation():
    """Test that unknown source values are preserved in storage."""
    workspace_dir, db_path = create_test_workspace()
    
    conn = sqlite3.connect(db_path)
    ensure_classification_tables(conn)
    
    # Register a vendor mapping
    register_vendor_mapping(conn, "deere-gs3", "deere-gs3", {
        "tillage": {"operation_family": "tillage", "operation_subtype": "tillage"},
    })
    
    # Classify with various unknown/proprietary values
    classify_with_storage(
        conn,
        dataset_id="abc123",
        purpose="operation",
        operation_family="tillage",
        operation_subtype="proprietary-code-12345",
        measurement="5.5",  # Unknown unit
        unit="custom_unit_xyz",
        semantics="target",
        source_value="SEED_RATE_TARGET_001"
    )
    
    classifications = get_classifications_for_dataset(conn, "abc123")
    c = classifications[0]
    
    assert c["operation_subtype"] == "proprietary-code-12345", "Proprietary subtype should be preserved"
    assert c["measurement"] == "5.5", "Measurement should be preserved"
    assert c["unit"] == "custom_unit_xyz", "Unit should be preserved"
    assert c["source_value"] == "SEED_RATE_TARGET_001", "Source value should be preserved"
    assert c["semantics"] == "target", "Semantics should be preserved"
    
    conn.close()
    print("PASS: test_unknown_value_preservation")


if __name__ == "__main__":
    test_ensure_classification_tables()
    test_register_vendor_mapping()
    test_register_unit()
    test_classify_with_storage()
    test_get_latest_classification()
    test_catalogue_migration()
    test_unknown_value_preservation()
    print("\nAll tests passed!")
