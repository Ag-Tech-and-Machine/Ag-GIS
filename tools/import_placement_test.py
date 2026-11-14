"""Boundary coverage, CRS, destination setup, cancellation and saved placement."""
import os
import gc
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer, QgsVectorFileWriter)
from qgis.PyQt.QtWidgets import QMainWindow, QDialog
from qgis.PyQt.QtCore import Qt, QCoreApplication, QEvent
from ag_tech_tooling import import_placement as routing, hierarchy as store
from ag_tech_tooling.import_destination import DestinationDialog
from ag_tech_tooling.import_dialog import ImportDialog
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling.import_sources import scan_local


app = QgsApplication([], bool(os.environ.get("AGTECH_IMPORT_SCREENSHOT")))
app.initQgis()


def memory(wkt, geometry="Point", crs="EPSG:4326"):
    layer = QgsVectorLayer(f"{geometry}?crs={crs}", "Data", "memory")
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromWkt(wkt))
    assert layer.dataProvider().addFeatures([feature])[0]
    layer.updateExtents()
    return layer


with tempfile.TemporaryDirectory(prefix="agtech-placement-") as temporary:
    root = create_farm(Path(temporary), "Farm", QgsCoordinateReferenceSystem("EPSG:4326"),
                       organisation="Org", client="Grower", farm="Home", field="North")
    project = QgsProject.instance()
    assert project.read(str(root / "Farm.qgz"))
    field_id = store.records(root)["field"][0]["id"]
    incoming = memory("POINT(1 1)")
    assert routing.match_field(root, incoming)["field_id"] is None
    outline = memory("POLYGON((0 0,2 0,2 2,0 2,0 0))", "Polygon")
    routing.place_layer(root, outline, field_id, "boundary")
    assert routing.match_field(root, incoming)["field_id"] == field_id
    edge = memory("POINT(0 1)")
    assert routing.match_field(root, edge)["field_id"] == field_id
    crossing = memory("LINESTRING(1 1,3 1)", "LineString")
    assert routing.match_field(root, crossing)["field_id"] is None
    other_id = routing.ensure_field(root, dict(organisation="Org", client="Other", farm="Home", field="North"))
    assert other_id != field_id
    assert routing.field_path(root, other_id)["client"] == "Other"
    overlap = memory("POLYGON((0 0,2 0,2 2,0 2,0 0))", "Polygon")
    routing.place_layer(root, overlap, other_id, "boundary")
    assert routing.match_field(root, incoming)["field_id"] is None
    project.removeMapLayer(overlap.id())
    del overlap
    mercator = memory("POINT(1 1)")
    geometry = next(mercator.getFeatures()).geometry()
    geometry.transform(QgsCoordinateTransform(mercator.crs(), QgsCoordinateReferenceSystem("EPSG:3857"), project))
    fid = next(mercator.getFeatures()).id()
    mercator.dataProvider().changeGeometryValues({fid: geometry})
    mercator.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    assert routing.match_field(root, mercator)["field_id"] == field_id
    missing_crs = memory("POINT(1 1)")
    missing_crs.setCrs(QgsCoordinateReferenceSystem())
    assert routing.match_field(root, missing_crs)["field_id"] is None
    parent = QMainWindow()
    chooser = DestinationDialog(root, incoming, "Choose a field", parent)
    before = store.records(root)
    for kind, name in dict(organisation="New Org", client="New Client", farm="New Farm", field="New Field").items():
        chooser.combos[kind].setEditText(name)
    chooser.reject()
    assert store.records(root) == before, "Cancel must not create hierarchy records"
    chooser.accept()
    assert chooser.result() == QDialog.Accepted
    assert store.records(root) == before, "Accept produces a plan, not immediate writes"
    created = routing.ensure_field(root, chooser.names)
    assert routing.field_path(root, created) == chooser.names
    assert routing.ensure_field(root, chooser.names) == created
    # New hierarchy creation rolls back all levels on a database failure.
    before = store.records(root)
    connection = store._connection(store.database(root))
    connection.executeSql("CREATE TRIGGER reject_test_field BEFORE INSERT ON agtech_fields WHEN NEW.name='X' BEGIN SELECT RAISE(ABORT,'Simulated database failure'); END")
    try:
        routing.ensure_field(root, dict(organisation="Rollback", client="C", farm="F", field="X"))
        raise AssertionError("Expected database failure")
    except ValueError:
        pass
    connection.executeSql("DROP TRIGGER reject_test_field")
    del connection
    assert store.records(root) == before
    # Real generic shapefile: old loose layer is moved into an explicitly created
    # hierarchy, while an unresolved batch does not place even its earlier matches.
    polygon = memory("POLYGON((10 10,12 10,12 12,10 12,10 10))", "Polygon")
    path = Path(temporary) / "South.shp"
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    assert QgsVectorFileWriter.writeAsVectorFormatV3(polygon, str(path), project.transformContext(), options)[0] == QgsVectorFileWriter.NoError
    del polygon
    loose = QgsVectorLayer(str(path), "South", "ogr")
    project.addMapLayer(loose)
    loose_id = loose.id()
    point_path = Path(temporary) / "Known.geojson"
    options.driverName = "GeoJSON"
    assert QgsVectorFileWriter.writeAsVectorFormatV3(incoming, str(point_path), project.transformContext(), options)[0] == QgsVectorFileWriter.NoError
    point_result, shape_result = scan_local(point_path), scan_local(path)
    result = dict(shape_result, items=point_result["items"] + shape_result["items"])
    class Interface:
        def mainWindow(self): return None
        def mapCanvas(self): return self
        def refresh(self): pass
        def zoomToFullExtent(self): pass
    importer = ImportDialog(Interface())
    importer.show_result(result)
    original_ids, original_rows = set(project.mapLayers()), store.records(root)
    assert importer.tree.topLevelItem(0).text(3) == "Detected"
    assert importer.tree.topLevelItem(1).text(3) == "Please set"
    assert not importer.add_button.isEnabled()
    importer.add_selected()
    assert set(project.mapLayers()) == original_ids and store.records(root) == original_rows
    assert project.layerTreeRoot().findLayer(loose.id()).parent() is project.layerTreeRoot()
    target = dict(organisation="Co-op", client="O'Brien", farm="East", field="South")
    unknown_row = importer.tree.topLevelItem(1)
    destination = importer.tree.itemWidget(unknown_row, 2)
    assert destination is not None and destination.findText("Add new field…") >= 0
    detected = importer.tree.itemWidget(importer.tree.topLevelItem(0), 2)
    assert detected.currentData()["field_id"] == field_id
    def select_destination(selector, index):
        selector.setCurrentIndex(index)
        selector.activated.emit(index)
    # Existing fields apply directly from the row, retaining their actual IDs.
    index = next(i for i in range(destination.count())
                 if isinstance(destination.itemData(i), dict) and destination.itemData(i).get("field_id") == other_id)
    select_destination(destination, index)
    assert unknown_row.data(0, Qt.UserRole + 1)["field_id"] == other_id
    assert unknown_row.text(2) == "Org / Other / Home / North"
    assert unknown_row.text(3) == "Ready"
    unknown_row.setData(0, Qt.UserRole + 1, None)
    with patch.object(importer, "open_layer", return_value=missing_crs):
        select_destination(destination, index)
        assert not unknown_row.data(0, Qt.UserRole + 1), "A destination cannot establish missing coordinates"
        assert unknown_row.text(3) == "Please set coordinate system"
        assert not importer.add_button.isEnabled()
        importer.editor.crs.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
        importer.apply_destination()
        assert unknown_row.text(3) == "Ready"
    # Add is inline, blanks the new field name and never writes on selection.
    select_destination(destination, destination.findData("add"))
    assert importer.editor.combos["field"].currentText() == ""
    assert not importer.add_button.isEnabled()
    assert store.records(root) == original_rows
    importer.tree.setCurrentItem(unknown_row)
    importer.editor.set_names(target)
    importer.apply_destination()
    importer.tree.itemWidget(unknown_row, 1).setCurrentIndex(1)
    assert unknown_row.text(3) == "Ready"
    assert unknown_row.text(2) == "Co-op / O'Brien / East / South"
    assert store.records(root) == original_rows, "Inline setup only prepares plans"
    assert importer.add_button.isEnabled()
    pending = importer.tree.itemWidget(importer.tree.topLevelItem(0), 2)
    assert pending.findText("Co-op / O'Brien / East / South") >= 0
    select_destination(pending, pending.findText("Co-op / O'Brien / East / South"))
    assert importer.tree.topLevelItem(0).data(0, Qt.UserRole + 1)["names"] == target
    assert store.records(root) == original_rows
    importer.detect_destination(importer.tree.topLevelItem(0))
    importer.tree.setCurrentItem(unknown_row)
    # Batch assignment must never spread one file's CRS to an unidentified file.
    native_open = importer.open_layer
    with patch.object(importer, "open_layer", side_effect=lambda row:
                      missing_crs if row is importer.tree.topLevelItem(0) else native_open(row)):
        old_plan = importer.tree.topLevelItem(0).data(0, Qt.UserRole + 1)
        importer.apply_destination(True)
        assert "individually" in importer.editor.error.text()
        assert importer.tree.topLevelItem(0).data(0, Qt.UserRole + 1) == old_plan
        assert store.records(root) == original_rows
    # One explicit destination can be applied to the batch without changing types.
    importer.apply_destination(True)
    assert all(row.text(2) == unknown_row.text(2) for row in importer.rows())
    assert importer.tree.itemWidget(importer.tree.topLevelItem(0), 1).currentData() == "data"
    assert importer.tree.itemWidget(unknown_row, 1).currentData() == "boundary"
    assert store.records(root) == original_rows
    importer.detect_destination(importer.tree.topLevelItem(0))
    # Unapplied edits cannot silently use an older destination. Row switching
    # preserves drafts, while Import remains blocked until the draft is applied.
    importer.editor.combos["field"].setEditText("Draft")
    unknown_row.setCheckState(0, Qt.Unchecked)
    assert importer.add_button.isEnabled(), "Unchecked drafts must not block ready files"
    unknown_row.setCheckState(0, Qt.Checked)
    assert not importer.add_button.isEnabled()
    importer.tree.setCurrentItem(importer.tree.topLevelItem(0))
    assert not importer.add_button.isEnabled()
    importer.tree.setCurrentItem(unknown_row)
    assert importer.editor.combos["field"].currentText() == "Draft"
    importer.editor.set_names(target)
    importer.apply_destination()
    if os.environ.get("AGTECH_IMPORT_SCREENSHOT"):
        from qgis.PyQt.QtGui import QFont
        app.setFont(QFont("Segoe UI", 10))
        importer.setAttribute(Qt.WA_DontShowOnScreen)
        importer.show()
        app.processEvents()
        importer.grab().save(os.environ["AGTECH_IMPORT_SCREENSHOT"])
    with patch.object(DestinationDialog, "exec", side_effect=AssertionError("No destination popups")):
        importer.add_selected()
    assert loose_id not in project.mapLayers(), "The old source link must be replaced by the managed copy"
    loose = next(layer for layer in project.mapLayers().values()
                 if layer.customProperty("AgTechTooling/import_source") == str(path))
    new_id = loose.customProperty("AgTechTooling/import_field")
    assert routing.field_path(root, new_id) == target
    assert project.layerTreeRoot().findLayer(loose.id()).parent().name() == "Imported Data"
    assert loose.customProperty("AgTechTooling/import_role") == "boundary"
    later = memory("POINT(11 11)")
    assert routing.match_field(root, later)["field_id"] == new_id
    importer.reject()
    routing.place_layer(root, incoming, field_id)
    assert project.layerTreeRoot().findLayer(incoming.id()).parent().parent().customProperty("AgTechTooling/field") == field_id
    # Persist field assignment and its native group with QGIS's project writer.
    assert project.write()
    assert project.read(project.fileName())
    loaded = [layer for layer in project.mapLayers().values() if layer.customProperty("AgTechTooling/import_field") == field_id]
    assert len(loaded) == 3
    assert all(project.layerTreeRoot().findLayer(layer.id()).parent().name() == "Imported Data" for layer in loaded)
    assert routing.match_field(root, later)["field_id"] == new_id, "File-backed boundaries must still match after project reopen"
    del loaded
    project.clear()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    del chooser, importer, parent, incoming, outline, edge, crossing, mercator, missing_crs, loose, later
    gc.collect()
    app.exitQgis()
print("Field matching, complete coverage, ambiguity, CRS transforms, atomic setup and saved placement checks passed")
