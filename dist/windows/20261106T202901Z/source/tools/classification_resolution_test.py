# SPDX-License-Identifier: GPL-2.0-or-later
"""Assert database rule isolation, historical resolution and source preservation."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(Path(__file__).resolve().parents[1] / 'plugins')))
from ag_tech_tooling import classification_registry as registry


class ResolutionTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        registry.ensure_classification_tables(self.conn)
        self.addCleanup(self.conn.close)

    def test_rules_are_append_only_per_vendor(self):
        first = {'SEED': {'operation_family': 'planting', 'operation_subtype': 'planting'}}
        second = {'SEED': {'operation_family': 'application', 'operation_subtype': 'spreading'}}
        registry.register_vendor_mapping(self.conn, 'reviewed', 'vendor-a', first)
        registry.register_vendor_mapping(self.conn, 'reviewed', 'vendor-a', second)
        rows = self.conn.execute('SELECT version,rules_json FROM agtech_vendor_mappings ORDER BY version').fetchall()
        self.assertEqual([r[0] for r in rows], [1, 2])
        self.assertEqual(json.loads(rows[0][1]), first)
        registry.register_vendor_mapping(self.conn, 'reviewed', 'vendor-b', first)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM agtech_vendor_mappings').fetchone()[0], 3)

    def test_database_lookup_is_exact_versioned_and_vendor_isolated(self):
        first = {'SEED': {'operation_family': 'planting', 'operation_subtype': 'planting'}}
        registry.register_vendor_mapping(self.conn, 'reviewed', 'vendor-a', first)
        found = registry.lookup_vendor_mapping('SEED', 'vendor-a', conn=self.conn, name='reviewed')
        self.assertEqual(found['operation_subtype'], 'planting')
        self.assertEqual((found['mapping_name'], found['mapping_version'], found['vendor_source']), ('reviewed', 1, 'vendor-a'))
        registry.register_vendor_mapping(self.conn, 'reviewed', 'vendor-a', {'OTHER': first['SEED']})
        self.assertIsNone(registry.lookup_vendor_mapping('SEED', 'vendor-a', conn=self.conn, name='reviewed'))
        self.assertEqual(registry.lookup_vendor_mapping('SEED', 'vendor-a', conn=self.conn, name='reviewed', version=1), found)
        for token, vendor in [('seed', 'vendor-a'), ('SEED', 'vendor-b'), ('tillage', 'vendor-a'), (None, 'vendor-a')]:
            self.assertIsNone(registry.lookup_vendor_mapping(token, vendor, conn=self.conn, name='reviewed'))
        self.assertIsNone(registry.lookup_vendor_mapping('tillage', 'deere-gs3'))
        self.assertIsNone(registry.lookup_vendor_mapping('tillage', 'deere-gs3', conn=sqlite3.connect(':memory:')))

    def test_units_are_versioned_isolated_without_conversion(self):
        registry.register_unit(self.conn, 'vendor-a', 'l1ha-1', 'litre_per_hectare', 'rate', 'L/ha')
        registry.register_unit(self.conn, 'vendor-a', 'l1ha-1', 'reviewed_litre_per_hectare', 'rate', 'review')
        self.assertEqual(self.conn.execute('SELECT version FROM agtech_unit_registry ORDER BY version').fetchall(), [(1,), (2,)])
        latest = registry.lookup_unit('l1ha-1', 'vendor-a', conn=self.conn)
        self.assertEqual(latest['standard'], 'reviewed_litre_per_hectare')
        self.assertEqual(latest['mapping_version'], 2)
        self.assertEqual(registry.lookup_unit('l1ha-1', 'vendor-a', conn=self.conn, version=1)['standard'], 'litre_per_hectare')
        self.assertIsNone(registry.lookup_unit('l1ha-1', 'vendor-b', conn=self.conn))
        self.assertIsNone(registry.lookup_unit('gal1ac-1', 'vendor-a', conn=self.conn))
        self.assertIsNone(registry.lookup_unit('gal1ac-1', 'vendor-a'))
        self.assertNotIn('factor', latest)

    def test_history_cannot_be_rewritten(self):
        registry.register_vendor_mapping(self.conn, 'default', 'vendor-a', {'x': {'operation_family': 'tillage', 'operation_subtype': 'tillage'}})
        registry.register_unit(self.conn, 'vendor-a', 'u', 'unit')
        for table in ('agtech_vendor_mappings', 'agtech_unit_registry'):
            for sql in (f'UPDATE {table} SET version=9', f'DELETE FROM {table}'):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.conn.execute(sql)

    def test_resolved_classification_preserves_snapshot_and_unknown_source(self):
        source = {'id': 'vendor-ID', 'operation_type': 'SEED', 'unit': 'u', 'unknown': {'raw': ' Keep CASE '}, 'value': 5.5}
        registry.register_vendor_mapping(self.conn, 'default', 'vendor-a', {'SEED': {'operation_family': 'planting', 'operation_subtype': 'planting'}})
        registry.register_unit(self.conn, 'vendor-a', 'u', 'litre_per_hectare')
        registry.classify_source_with_storage(self.conn, 'dataset', 'vendor-a', source,
            operation_token=source['operation_type'], unit_token=source['unit'])
        saved = registry.get_latest_classification_for_dataset(self.conn, 'dataset')
        snapshot = json.loads(saved['source_value'])
        self.assertEqual(snapshot['source'], source)
        self.assertEqual(snapshot['operation_mapping']['mapping_version'], 1)
        self.assertEqual(snapshot['unit_mapping']['mapping_version'], 1)
        self.assertEqual((saved['operation_family'], saved['unit'], saved['mapping_version']), ('planting', 'litre_per_hectare', 1))
        registry.register_vendor_mapping(self.conn, 'default', 'vendor-a', {'SEED': {'operation_family': 'other', 'operation_subtype': 'other'}})
        self.assertEqual(registry.get_latest_classification_for_dataset(self.conn, 'dataset')['source_value'], saved['source_value'])
        self.assertEqual(source['unknown']['raw'], ' Keep CASE ')
        registry.classify_source_with_storage(self.conn, 'unknown', 'vendor-b', source, operation_token='SEED', unit_token='gal1ac-1')
        unknown = registry.get_latest_classification_for_dataset(self.conn, 'unknown')
        self.assertEqual((unknown['operation_family'], unknown['operation_subtype'], unknown['unit'], unknown['mapping_version']), ('unknown', 'SEED', 'gal1ac-1', 0))
        self.assertIsNone(json.loads(unknown['source_value'])['unit_mapping'])
        registry.classify_source_with_storage(self.conn, 'missing', 'vendor-a', {})
        missing = registry.get_latest_classification_for_dataset(self.conn, 'missing')
        self.assertEqual((missing['operation_family'], missing['unit'], missing['mapping_version']), ('unknown', '', 0))

    def test_invalid_rules_are_rejected_without_storing_partial_versions(self):
        for rules in ([], {'x': 'planting'}, {'x': {'operation_family': 'planting'}}, {'x': {'operation_family': '', 'operation_subtype': 'planting'}}):
            with self.assertRaises(ValueError):
                registry.register_vendor_mapping(self.conn, 'default', 'vendor-a', rules)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM agtech_vendor_mappings').fetchone()[0], 0)
        with self.assertRaises(ValueError):
            registry.register_unit(self.conn, 'vendor-a', '', '')


if __name__ == '__main__':
    unittest.main()
