"""Synthetic classification contract tests; no QGIS runtime needed."""
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))


class ClassificationTest(unittest.TestCase):
    def test_explicit_classification_preserves_unknown_source_and_units(self):
        from ag_tech_tooling.classification import classify
        source = {"operation": "vendor:42", "unit": "bushel/acre", "extra": {"code": 7}}
        result = classify(source, operation="spraying", purpose="operation", measurement="rate",
                          unit="bushel/acre", semantics="actual", field_id="field-1", season_id="")
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["mapping_rule"], "explicit-selection-v1")
        self.assertEqual(result["operation_family"], "application")
        self.assertEqual(result["operation_subtype"], "spraying")
        self.assertEqual(result["measurement"], "rate")
        self.assertEqual(result["unit"], "bushel/acre")
        self.assertEqual(result["semantics"], "actual")
        self.assertEqual(result["source"], source)
        source["extra"]["code"] = 8
        self.assertEqual(result["source"]["extra"]["code"], 7)
        unknown = classify({"code": "unrecognised"}, operation="vendor:42")
        self.assertEqual(unknown["operation_family"], "unknown")
        self.assertEqual(unknown["operation_subtype"], "vendor:42")
        self.assertEqual(unknown["semantics"], "unknown")
        self.assertEqual(unknown["unit"], "")
        self.assertEqual(unknown["season_id"], "")
        self.assertEqual(classify({})["purpose"], "unknown")


if __name__ == "__main__":
    unittest.main()
