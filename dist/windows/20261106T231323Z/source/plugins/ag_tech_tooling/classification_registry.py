# SPDX-License-Identifier: GPL-2.0-or-later
"""Durable GeoPackage classification storage with vendor mapping/version/unit registry.

Additive storage: new tables appended to existing workspace. Original source data
and schema2/catalogue1 remain unchanged. Unknown/source values are preserved.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

def _get_workspace_db(workspace_dir: Path) -> Path:
    """Get the path to the workspace database (farm.gpkg or its SQLite backend)."""
    data_dir = workspace_dir / "Data"
    if (data_dir / "farm.gpkg").exists():
        return data_dir / "farm.gpkg"
    return workspace_dir / "farm.gpkg"


def ensure_classification_tables(conn: sqlite3.Connection) -> None:
    """Create classification storage tables if they don't exist.

    Additive: never drops/alters existing tables.
    """
    cursor = conn.cursor()
    
    # Classification operations table: durable storage for classification decisions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agtech_classifications (
        id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        purpose TEXT NOT NULL DEFAULT 'operation',
        operation_family TEXT NOT NULL,
        operation_subtype TEXT NOT NULL,
        measurement TEXT,
        unit TEXT,
        semantics TEXT NOT NULL DEFAULT 'unknown',
        field_id TEXT,
        season_id TEXT,
        source_value TEXT,
        created_utc TEXT NOT NULL,
        updated_utc TEXT,
        mapping_version INTEGER NOT NULL DEFAULT 1,
        vendor_source TEXT,
        FOREIGN KEY (dataset_id) REFERENCES agtech_datasets(id)
    )
    """)
    
    # Vendor mapping registry table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agtech_vendor_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        source_type TEXT NOT NULL,  -- 'deere-gs3', 'adapt-standard', 'custom'
        rules_json TEXT NOT NULL,
        created_utc TEXT NOT NULL,
        UNIQUE(name, version, source_type)
    )
    """)
    
    # Unit registry table
    cursor.execute("""
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
    """)
    
    # Registry identities are append-only. Corrections require a new version.
    for table in ("agtech_vendor_mappings", "agtech_unit_registry"):
        for action in ("UPDATE", "DELETE"):
            cursor.execute(f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{action.lower()}
                BEFORE {action} ON {table} BEGIN
                SELECT RAISE(ABORT, 'Registry history is immutable; register a new version'); END""")

    # Indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classifications_dataset ON agtech_classifications(dataset_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classifications_field ON agtech_classifications(field_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classifications_semantics ON agtech_classifications(semantics)")


def register_vendor_mapping(conn: sqlite3.Connection, name: str, source_type: str, rules: Dict[str, Dict]) -> str:
    """Register a vendor mapping rule set.

    Append a new version within (name, source_type). Returns the mapping name.
    """
    if not all(isinstance(value, str) and value for value in (name, source_type)):
        raise ValueError("Mapping name and vendor source must be nonempty strings")
    if not isinstance(rules, dict) or any(
        not isinstance(token, str) or not token or not isinstance(rule, dict)
        or not all(isinstance(rule.get(key), str) and rule[key]
                   for key in ("operation_family", "operation_subtype"))
        for token, rule in rules.items()
    ):
        raise ValueError("Rules require exact source tokens and nonempty operation family/subtype")
    cursor = conn.cursor()
    rules_json = json.dumps(rules, sort_keys=True, ensure_ascii=False, allow_nan=False)
    created_utc = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT INTO agtech_vendor_mappings (name, version, source_type, rules_json, created_utc)
    SELECT ?, COALESCE(MAX(version), 0) + 1, ?, ?, ?
    FROM agtech_vendor_mappings WHERE name = ? AND source_type = ?
    """, (name, source_type, rules_json, created_utc, name, source_type))
    
    conn.commit()
    return name


def register_unit(conn: sqlite3.Connection, vendor_source: str, unit_token: str, standard_name: str, 
                  category: str = None, description: str = None) -> str:
    """Register a unit interpretation.

    Append a new version within (default, vendor_source, unit_token).
    Returns the unit registry name, not a numeric conversion.
    """
    if not all(isinstance(value, str) and value for value in (vendor_source, unit_token, standard_name)):
        raise ValueError("Vendor, source unit token and standard label must be nonempty strings")
    cursor = conn.cursor()
    created_utc = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT INTO agtech_unit_registry (name, version, vendor_source, unit_token, standard_name, category, description, created_utc)
    SELECT 'default', COALESCE(MAX(version), 0) + 1, ?, ?, ?, ?, ?, ?
    FROM agtech_unit_registry WHERE name='default' AND vendor_source=? AND unit_token=?
    """, (vendor_source, unit_token, standard_name, category, description, created_utc, vendor_source, unit_token))
    
    conn.commit()
    return "default"


def classify_with_storage(conn: sqlite3.Connection, dataset_id: str, purpose: str = "operation",
                          operation_family: str = "unknown", operation_subtype: str = "unknown",
                          measurement: str = "", unit: str = "", semantics: str = "unknown",
                          field_id: str = "", season_id: str = "", source_value: str = None,
                          mapping_version: int = 1, vendor_source: str = "default") -> str:
    """Store a classification decision in the GeoPackage.

    Does NOT modify source data. Additive storage only.
    Returns the classification ID.
    """
    cursor = conn.cursor()
    id_val = str(uuid.uuid4())
    created_utc = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT OR REPLACE INTO agtech_classifications 
    (id, dataset_id, purpose, operation_family, operation_subtype, measurement, unit, semantics,
     field_id, season_id, source_value, created_utc, updated_utc, mapping_version, vendor_source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (id_val, dataset_id, purpose, operation_family, operation_subtype, measurement, unit, semantics,
          field_id or "", season_id or "", (source_value or ""), created_utc, None, mapping_version, vendor_source))
    
    conn.commit()
    return id_val


def classify_source_with_storage(conn, dataset_id, source_type, source, *,
                                 operation_token=None, unit_token=None, mapping_name="default",
                                 mapping_version=None, unit_version=None, purpose="operation",
                                 measurement="", semantics="unknown", field_id="", season_id=""):
    """Resolve caller-reviewed metadata and store exact source plus rule snapshots.

    This is not a manufacturer decoder or a destination/season inference engine.
    No numeric values are converted. Existing explicit classification API is retained.
    """
    operation = lookup_vendor_mapping(operation_token, source_type, conn=conn,
                                      name=mapping_name, version=mapping_version)
    unit = lookup_unit(unit_token, source_type, conn=conn, version=unit_version)
    snapshot = json.dumps({"contract": "registered-source-v1", "source": source,
                           "operation_token": operation_token, "unit_token": unit_token,
                           "operation_mapping": operation, "unit_mapping": unit},
                          ensure_ascii=False, allow_nan=False, sort_keys=True)
    return classify_with_storage(conn, dataset_id, purpose=purpose,
        operation_family=operation["operation_family"] if operation else "unknown",
        operation_subtype=operation["operation_subtype"] if operation else (operation_token or "unknown"),
        measurement=measurement, unit=unit["standard"] if unit else (unit_token or ""),
        semantics=semantics, field_id=field_id, season_id=season_id, source_value=snapshot,
        mapping_version=operation["mapping_version"] if operation else 0, vendor_source=source_type)


def get_classifications_for_dataset(conn: sqlite3.Connection, dataset_id: str) -> List[Dict[str, Any]]:
    """Retrieve all classifications for a dataset."""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, dataset_id, purpose, operation_family, operation_subtype, measurement, unit, 
           semantics, field_id, season_id, source_value, created_utc, updated_utc, 
           mapping_version, vendor_source
    FROM agtech_classifications
    WHERE dataset_id = ?
    ORDER BY created_utc DESC
    """, (dataset_id,))
    
    return [dict(zip(["id", "dataset_id", "purpose", "operation_family", "operation_subtype", "measurement", "unit", "semantics", "field_id", "season_id", "source_value", "created_utc", "updated_utc", "mapping_version", "vendor_source"], row)) for row in cursor.fetchall()]


def get_latest_classification_for_dataset(conn: sqlite3.Connection, dataset_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent classification for a dataset."""
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, dataset_id, purpose, operation_family, operation_subtype, measurement, unit, 
           semantics, field_id, season_id, source_value, created_utc, updated_utc, 
           mapping_version, vendor_source
    FROM agtech_classifications
    WHERE dataset_id = ?
    ORDER BY created_utc DESC
    LIMIT 1
    """, (dataset_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    return dict(zip(["id", "dataset_id", "purpose", "operation_family", "operation_subtype", "measurement", "unit", "semantics", "field_id", "season_id", "source_value", "created_utc", "updated_utc", "mapping_version", "vendor_source"], row))


def apply_classification_to_style(conn: sqlite3.Connection, layer_name: str, classification_id: str) -> bool:
    """Apply stored classification to a QGIS layer style.

    Must be called from QGIS context with QgsVectorLayer available.
    Returns False if connection has no active QGIS layer context.
    """
    # This function requires QGIS context; returns False if not available
    return False


# Migration helpers (safe, additive only)
def ensure_catalogue_has_classification_column(conn: sqlite3.Connection) -> bool:
    """Add classification_id column to agtech_datasets catalogue if missing.

    Safe additive migration: never drops existing data.
    Returns True if column was added, False if it already exists.
    """
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(agtech_datasets)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "classification_id" not in columns:
        # Add the column (nullable for backward compatibility)
        cursor.execute("ALTER TABLE agtech_datasets ADD COLUMN classification_id TEXT")
        cursor.execute("UPDATE agtech_datasets SET classification_id = NULL WHERE classification_id IS NULL")
        conn.commit()
        return True
    return False

# Lookups are read-only and fail closed for legacy workspaces without tables.
def lookup_vendor_mapping(operation_token, source_type, *, conn=None, name="default", version=None):
    """Resolve an exact token in one named vendor rule-set; never cross-vendor fallback."""
    if conn is None or not isinstance(operation_token, str):
        return None
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='agtech_vendor_mappings'").fetchone():
        return None
    query = "SELECT id, version, rules_json FROM agtech_vendor_mappings WHERE name=? AND source_type=?"
    args = [name, source_type]
    if version is not None:
        query += " AND version=?"
        args.append(version)
    row = conn.execute(query + " ORDER BY version DESC LIMIT 1", args).fetchone()
    if not row:
        return None
    rule = json.loads(row[2]).get(operation_token)
    if not isinstance(rule, dict) or not all(isinstance(rule.get(k), str) and rule[k] for k in ("operation_family", "operation_subtype")):
        return None
    return {"operation_family": rule["operation_family"], "operation_subtype": rule["operation_subtype"],
            "mapping_id": row[0], "mapping_name": name, "mapping_version": row[1],
            "vendor_source": source_type, "source_token": operation_token}


def lookup_unit(unit_token, source_type, *, conn=None, name="default", version=None):
    """Resolve a registered unit label only. No numeric conversion or inferred gallon basis."""
    if conn is None or not isinstance(unit_token, str):
        return None
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='agtech_unit_registry'").fetchone():
        return None
    query = "SELECT id,version,standard_name,category,description FROM agtech_unit_registry WHERE name=? AND vendor_source=? AND unit_token=?"
    args = [name, source_type, unit_token]
    if version is not None:
        query += " AND version=?"
        args.append(version)
    row = conn.execute(query + " ORDER BY version DESC LIMIT 1", args).fetchone()
    if not row:
        return None
    return {"standard": row[2], "category": row[3], "description": row[4],
            "mapping_id": row[0], "mapping_name": name, "mapping_version": row[1],
            "vendor_source": source_type, "source_token": unit_token}
