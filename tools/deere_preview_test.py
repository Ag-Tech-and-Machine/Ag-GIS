"""Synthetic Deere metadata, source safety and packaged-module checks."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from ag_tech_tooling import deere_preview as preview


class PreviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "GS3_2630"
        self.eic = self.root / "default" / "RCD" / "EIC"
        self.eic.mkdir(parents=True)
        self.setup = self.eic / "setup.fds"
        self.setup.write_text(f'''<SetupFile xmlns="{preview.SETUP_NS}"><Setup>
          <Participant><Client erid="client-1" name="Grower"/></Participant>
          <Farm erid="farm-1" name="Home" clientRef="client-1"/>
          <Field erid="field-1" name="North" farmRef="farm-1"/>
          </Setup></SetupFile>''', encoding="utf-8")
        self.field = self.eic / "Fields" / "F1" / "field-1"
        self.field.mkdir(parents=True)
        self.catalog = self.field / "ImportExport.SpatialCatalog"
        self.catalog.write_text(f'''<SpatialCatalog xmlns="{preview.CATALOG_NS}">
          <SpatialItems eridFieldRef="field-1"><CurvedTrackLine erid="curve-1"
          fileName="CurveTrack1" name="Track"><Reference value="12" sourceUOM="arcdeg"/>
          </CurvedTrackLine></SpatialItems></SpatialCatalog>''', encoding="utf-8")
        (self.field / "CurveTrack1.fdShape").write_bytes(b"\0binary fixture\xff")

    def test_preserves_hierarchy_references_and_machine_properties(self):
        result = preview.inspect_export(self.root)
        self.assertEqual(result["format"], "deere_gs3_rcd")
        self.assertEqual([r["kind"] for r in result["entities"]], ["client", "farm", "field"])
        self.assertEqual(result["entities"][2]["parent_id"], "farm-1")
        item = result["spatial_items"][0]
        self.assertEqual(item["field_id"], "field-1")
        self.assertEqual(item["properties"][0]["attributes"]["sourceUOM"], "arcdeg")
        self.assertTrue(item["resource"].endswith("CurveTrack1.fdShape"))
        self.assertTrue(result["source_unchanged"])
        self.assertFalse(result["geometry_import_supported"])
        self.assertEqual(result["issues"], [])

    def test_profile_selection_and_multiple_profiles(self):
        import shutil
        shutil.copytree(self.root / "default", self.root / "other")
        result = preview.inspect_export(self.root)
        self.assertEqual(len(result["entities"]), 6)
        self.assertEqual(len(result["profiles"]), 2)
        self.assertEqual(len(preview.inspect_export(self.eic.parent)["entities"]), 3)

    def test_missing_or_unsafe_resource_and_parent(self):
        self.catalog.write_text(self.catalog.read_text().replace('fileName="CurveTrack1"', 'fileName="../../escape"').replace('eridFieldRef="field-1"', 'eridFieldRef="missing"'))
        result = preview.inspect_export(self.root)
        self.assertIsNone(result["spatial_items"][0]["resource"])
        self.assertEqual(len(result["issues"]), 2)
        self.catalog.write_text(self.catalog.read_text().replace('../../escape', 'Missing'))
        self.assertIn("missing", preview.inspect_export(self.root)["issues"][0]["message"])

    def test_dtd_and_unrelated_xml_are_not_parsed_as_setup(self):
        self.setup.write_text('<!DOCTYPE x [<!ENTITY e "x">]><x>&e;</x>')
        result = preview.inspect_export(self.root)
        self.assertTrue(any("DTD" in r["message"] for r in result["issues"]))
        self.setup.write_text('<SetupFile><Client erid="bad"/></SetupFile>')
        self.assertEqual(preview.inspect_export(self.root)["entities"], [])

    def test_catalog_duplicate_conflict_does_not_silently_replace_setup(self):
        data = self.catalog.read_text().replace('<SpatialItems',
            f'<Setup xmlns:s="{preview.SETUP_NS}"><s:Client erid="client-1" name="Other"/></Setup><SpatialItems')
        self.catalog.write_text(data)
        result = preview.inspect_export(self.root)
        self.assertEqual(len(result["entities"]), 3)
        self.assertTrue(any("Conflicting" in r["message"] for r in result["issues"]))

    def test_unresolved_hierarchy_parent_is_reported(self):
        self.setup.write_text(self.setup.read_text().replace('farmRef="farm-1"', 'farmRef="missing"'))
        self.assertTrue(any("unresolved parent" in r["message"]
                            for r in preview.inspect_export(self.root)["issues"]))

    def test_source_mutation_invalidates_preview(self):
        actual_hash = preview._hash
        calls = []
        def changed(path):
            calls.append(path)
            return actual_hash(path) if len(calls) <= 3 else "changed"
        with patch.object(preview, "_hash", side_effect=changed):
            with self.assertRaisesRegex(RuntimeError, "Source changed"):
                preview.inspect_export(self.root)

    def test_oversize_metadata_is_rejected(self):
        with patch.object(preview, "XML_LIMIT", 20):
            self.assertEqual(preview.inspect_export(self.root)["format"], "unrecognised")


if __name__ == "__main__":
    unittest.main()
