"""Native operation-style foundation: explicit opt-in, editable, non-destructive."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys

import tempfile

from pathlib import Path

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

    pass  # QGIS not available, skip this test

except ImportError:

                layer.renderer().symbol().setColor(__import__('qgis.PyQt.QtGui', fromlist=['QColor']).QColor("#123456"))

                assert layer.renderer().symbol().color().name() == COLOURS["spraying"]

                assert apply_operation_style(layer)

                layer.setCustomProperty(CLASSIFICATION_KEY, json.dumps(classification))

                classification = classify({"code": "vendor:42"}, operation="spraying", purpose="operation")

                before = [(f.attributes(), f.geometry().asWkt()) for f in layer.getFeatures()]

                layer.setCustomProperty("AgTechTooling/workspace", "synthetic")

                feature.setGeometry(QgsGeometry.fromWkt(wkt)); layer.dataProvider().addFeatures([feature])

                feature = QgsFeature(layer.fields()); feature["vendor_code"] = "vendor:42"

                layer = QgsVectorLayer(geometry + "?crs=EPSG:4326&field=vendor_code:string", geometry, "memory")

                                  ("Polygon", "POLYGON((0 0,1 0,1 1,0 0))")):

            for geometry, wkt in (("Point", "POINT(1 1)"), ("LineString", "LINESTRING(0 0,1 1)"),

            import json

            from ag_tech_tooling.operation_style import apply_operation_style, CLASSIFICATION_KEY, COLOURS

            from ag_tech_tooling.classification import classify

        try:

        project = QgsProject.instance()

    def test_check_styles():

    

    app.initQgis()

    app = QgsApplication([], False)

    

    

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication, QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

            assert not apply_operation_style(layer), "Automatic repeat must preserve native edits"

            project.addMapLayer(layer)

            with tempfile.TemporaryDirectory(prefix="aggis-operation-style-") as directory:

                path = str(Path(directory) / "style.qgz")

                assert project.write(path)

                restored = QgsProject(); assert restored.read(path)

                reopened = next(iter(restored.mapLayers().values()))

                assert reopened.renderer().symbol().color().name() == "#123456"

                assert json.loads(reopened.customProperty(CLASSIFICATION_KEY)) == classification

                restored.clear()

            assert apply_operation_style(layer, reset=True)

            assert layer.renderer().symbol().color().name() == COLOURS["spraying"]

            assert before == [(f.attributes(), f.geometry().asWkt()) for f in layer.getFeatures()]

            project.clear()

        plain = QgsVectorLayer("Point?crs=EPSG:4326", "legacy", "memory")

        assert not apply_operation_style(plain)

        plain.setCustomProperty("AgTechTooling/workspace", "synthetic")

        plain.setCustomProperty(CLASSIFICATION_KEY, '{"version":99}')

        assert not apply_operation_style(plain)

        plain.setCustomProperty(CLASSIFICATION_KEY, '{"version":1,"purpose":"operation","operation_subtype":[]}')

        assert not apply_operation_style(plain), "Malformed metadata must not change a renderer"

        print("Operation style: point/line/polygon defaults, native edits, save/reopen, reset, source preservation and legacy refusal passed")

    finally:

        project.clear()





try:

    test_check_styles()

    # Destroy test-owned native projects/layers before shutting down QGIS providers.

    import gc

    gc.collect()

finally:

    app.exitQgis()


