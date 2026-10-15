"""Boundary coverage, CRS, destination setup, cancellation and saved placement."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer, QgsVectorFileWriter)
from qgis.PyQt.QtWidgets import QMainWindow, QDialog
from qgis.PyQt.QtCore import Qt
from ag_tech_tooling import import_placement as routing, hierarchy as store
from ag_tech_tooling.import_destination import DestinationDialog
from ag_tech_tooling.import_dialog import ImportDialog
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling.import_sources import scan_local


app = QgsApplication([], False)
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
    project.setFileName(str(root / "Farm.qgz"))
    project.writeEntry("AgTechTooling", "farm_id", store.workspace_id(root))
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
    # hierarchy, while a cancelled batch does not place even its earlier matches.
    polygon = memory("POLYGON((10 10,12 10,12 12,10 12,10 10))", "Polygon")
    path = Path(temporary) / "South.shp"
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    assert QgsVectorFileWriter.writeAsVectorFormatV3(polygon, str(path), project.transformContext(), options)[0] == QgsVectorFileWriter.NoError
    del polygon
    loose = QgsVectorLayer(str(path), "South", "ogr")
    project.addMapLayer(loose)
    point_path = Path(temporary) / "Known.geojson"
    options.driverName = "GeoJSON"
    assert QgsVectorFileWriter.writeAsVectorFormatV3(incoming, str(point_path), project.transformContext(), options)[0] == QgsVectorFileWriter.NoError
    point_result, shape_result = scan_local(point_path), scan_local(path)
    result = dict(shape_result, items=point_result["items"] + shape_result["items"])
    class Interface:
        def mainWindow(self): return parent
        def mapCanvas(self): return self
        def refresh(self): pass
        def zoomToFullExtent(self): pass
    importer = ImportDialog(Interface())
    importer.show_result(result)
    original_ids, original_rows = set(project.mapLayers()), store.records(root)
    with patch.object(DestinationDialog, "exec", return_value=QDialog.Rejected):
        importer.add_selected()
    assert set(project.mapLayers()) == original_ids and store.records(root) == original_rows
    assert project.layerTreeRoot().findLayer(loose.id()).parent() is project.layerTreeRoot()
    target = dict(organisation="Co-op", client="O'Brien", farm="East", field="South")
    def choose_new(dialog):
        for kind, name in target.items():
            dialog.combos[kind].setEditText(name)
        dialog.role.setCurrentIndex(1)
        dialog.accept()
        return dialog.result()
    with patch.object(DestinationDialog, "exec", choose_new):
        importer.add_selected()
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
    del chooser, importer, parent, incoming, outline, edge, crossing, mercator, missing_crs, loose, later
    app.exitQgis()
print("Field matching, complete coverage, ambiguity, CRS transforms, atomic setup and saved placement checks passed")
