"""Inspect actual synthetic GeoPackage storage, not a hand-built SQL fixture."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsVectorLayer
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling import hierarchy as store
from ag_tech_tooling.managed_data import save_dataset, FIELDS
from ag_tech_tooling import classification_registry as registry

app = QgsApplication([], False); app.initQgis()
try:
    with tempfile.TemporaryDirectory(prefix="aggis-dictionary-") as directory:
        root = create_farm(directory, "Synthetic", QgsCoordinateReferenceSystem("EPSG:3857"),
                           organisation="Organisation", client="Client", field="Field")
        field_id = store.records(root)["field"][0]["id"]
        source = QgsVectorLayer("Point?crs=EPSG:3857&field=vendor_code:string", "Source", "memory")
        record, saved, created = save_dataset(root, source, field_id)
        saved = None
        expected = {"agtech_farm": ["farm_id", "farm_name", "schema_version", "crs_authid", "created_utc"]}
        for kind, (table, _, parent_key) in store.ENTITIES.items():
            expected[table] = ["id", "name"] + ([parent_key] if parent_key else [])
            if kind == "season": expected[table] += ["start_date", "end_date"]
        for table, _ in store.SPATIAL.values():
            expected[table] = ["id", "field_id", "name", "revision"]
        expected["agtech_datasets"] = list(FIELDS)
        report = {}
        with closing(sqlite3.connect(store.database(root))) as connection:
            for table, fields in expected.items():
                columns = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
                assert {row[1] for row in columns} == {"fid", *fields} | ({"geom"} if table in {t for t, _ in store.SPATIAL.values()} else set())
                assert all(row[2] == "TEXT" for row in columns if row[1] in fields)
                report[table] = {"columns": [dict(zip(("cid", "name", "type", "notnull", "default", "pk"), row)) for row in columns],
                                 "triggers": connection.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=? ORDER BY name", (table,)).fetchall()}
            assert connection.execute("SELECT schema_version FROM agtech_farm").fetchone() == ("2",)
            assert connection.execute("SELECT catalog_version FROM agtech_datasets").fetchone() == ("1",)
            dynamic = record["uri"].split("layername=")[1].split("|")[0]
            report[dynamic] = connection.execute(f'PRAGMA table_info("{dynamic}")').fetchall()
            # Exercise additive classification against the REAL native writer catalogue.
            connection.execute('PRAGMA foreign_keys=ON')
            registry.ensure_classification_tables(connection)
            assert registry.ensure_catalogue_has_classification_column(connection)
            assert not registry.ensure_catalogue_has_classification_column(connection)
            registry.register_vendor_mapping(connection, 'reviewed', 'synthetic-vendor', {
                'SOW': {'operation_family': 'planting', 'operation_subtype': 'planting'}})
            registry.register_unit(connection, 'synthetic-vendor', 'custom-L/ha', 'litre_per_hectare', 'rate')
            raw = {'operation': 'SOW', 'unit': 'custom-L/ha', 'value': 5.5, 'unknown': 'untouched'}
            classification_id = registry.classify_source_with_storage(connection, record['id'], 'synthetic-vendor', raw,
                operation_token='SOW', unit_token='custom-L/ha', mapping_name='reviewed', field_id=field_id)
            assert registry.get_latest_classification_for_dataset(connection, record['id'])['id'] == classification_id
            for table in ('agtech_classifications', 'agtech_vendor_mappings', 'agtech_unit_registry'):
                report[table] = {
                    'columns': connection.execute(f'PRAGMA table_info("{table}")').fetchall(),
                    'triggers': connection.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,)).fetchall()}
            assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
            assert connection.execute('SELECT catalog_version,classification_id FROM agtech_datasets').fetchone() == ('1', None)
            assert connection.execute('SELECT schema_version FROM agtech_farm').fetchone() == ('2',)
        with closing(sqlite3.connect(store.database(root))) as reopened:
            stored = registry.get_latest_classification_for_dataset(reopened, record['id'])
            assert json.loads(stored['source_value'])['source'] == raw
            assert stored['unit'] == 'litre_per_hectare' and stored['mapping_version'] == 1
        assert source.fields().names() == ['vendor_code']
        if os.environ.get("AGTECH_DICTIONARY_REPORT"):
            Path(os.environ["AGTECH_DICTIONARY_REPORT"]).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Actual synthetic GeoPackage: all core/catalogue column sets, TEXT declarations, versions and managed vector table inspected")
finally:
    app.exitQgis()
