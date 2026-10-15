"""Exercise discovery, background cancellation and map opening with real QGIS."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsVectorFileWriter,
                       QgsFeedback, QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMainWindow, QPushButton
from osgeo import gdal
gdal.UseExceptions()
from ag_tech_tooling.import_sources import scan_local, ScanCancelled
from ag_tech_tooling.import_dialog import ImportDialog, ImportActions
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling import hierarchy as store


def wait_until(callback):
    deadline = time.monotonic() + 15
    while not callback() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert callback(), "Background task did not finish"


class Interface:
    def __init__(self):
        self.window = QMainWindow()
        self.refreshed, self.zoomed = 0, 0

    def mainWindow(self):
        return self.window

    def mapCanvas(self):
        return self

    def refresh(self):
        self.refreshed += 1

    def zoomToFullExtent(self):
        self.zoomed += 1


app = QgsApplication([], False)
app.initQgis()
with tempfile.TemporaryDirectory(prefix="agtech-data-in-") as temporary:
    root = Path(temporary)
    source = root / "Paddock.geojson"
    source.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"name": "North"},
         "geometry": {"type": "Point", "coordinates": [145, -36]}}]}))
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    # Real multi-layer container: discovery must expose each sublayer separately.
    database = root / "Farm.gpkg"
    layer = QgsVectorLayer(str(source), "North", "ogr")
    for index, name in enumerate(("Boundaries", "Guidance")):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName, options.layerName = "GPKG", name
        if index:
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        outcome = QgsVectorFileWriter.writeAsVectorFormatV3(layer, str(database), QgsProject.instance().transformContext(), options)
        assert outcome[0] == QgsVectorFileWriter.NoError, outcome
    del layer
    result = scan_local(root)
    assert len([item for item in result["items"] if item["kind"] == "layer"]) == 3, result
    assert len(scan_local(database)["items"]) == 2
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    raster = root / "Elevation.tif"
    dataset = gdal.GetDriverByName("GTiff").Create(str(raster), 2, 2, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform((145, .01, 0, -36, 0, -.01))
    dataset.SetProjection(QgsCoordinateReferenceSystem("EPSG:4326").toWkt())
    dataset.GetRasterBand(1).Fill(10)
    dataset = None
    raster_result = scan_local(raster)
    assert len(raster_result["items"]) == 1 and raster_result["items"][0]["layer_type"] == "raster"
    archive_path = root / "Maps.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(source, "Maps/Paddock.geojson")
    zip_result = scan_local(archive_path)
    assert len(zip_result["items"]) == 1, zip_result
    assert zip_result["items"][0]["uri"].startswith("/vsizip/")
    archived = zip_result["items"][0]
    zip_layer = QgsVectorLayer(archived["uri"], archived["name"], archived["provider"])
    assert zip_layer.isValid() and zip_layer.featureCount() == 1
    del zip_layer
    unsafe = root / "Unsafe.zip"
    with ZipFile(unsafe, "w") as archive:
        archive.writestr("../outside.geojson", source.read_text())
    assert not scan_local(unsafe)["items"]
    assert "Unsafe" in scan_local(unsafe)["warnings"][0]
    eic = root / "GS3_2630" / "default" / "RCD" / "EIC"
    eic.mkdir(parents=True)
    (eic / "setup.fds").write_text('''<SetupFile xmlns="urn:schemas-johndeere-com:RCD:Setup">
      <Setup><Client erid="client-1" name="Grower"/>
      <Farm erid="farm-1" name="Home" clientRef="client-1"/>
      <Field erid="field-1" name="North" farmRef="farm-1"/></Setup></SetupFile>''')
    machine_result = scan_local(root / "GS3_2630")
    assert len(machine_result["items"]) == 1
    assert len(machine_result["items"][0]["metadata"]["entities"]) == 3
    machine_zip = root / "Machine.zip"
    with ZipFile(machine_zip, "w") as archive:
        archive.write(eic / "setup.fds", "RCD/EIC/setup.fds")
    assert scan_local(machine_zip)["items"][0]["kind"] == "machine_archive"
    with patch("ag_tech_tooling.import_sources.MAX_FILES", 1):
        try:
            scan_local(root)
            raise AssertionError("Expected scan limit")
        except ValueError:
            pass
    feedback = QgsFeedback()
    feedback.cancel()
    try:
        scan_local(source, feedback)
        raise AssertionError("Expected cancellation")
    except ScanCancelled:
        pass
    iface = Interface()
    dialog = ImportDialog(iface)
    dialog.show()
    dialog.path.setText(str(source))
    dialog.start_scan()
    wait_until(lambda: dialog.task is None)
    assert dialog.tree.topLevelItemCount() == 1
    assert dialog.add_button.isEnabled()
    dialog.add_selected()
    assert not QgsProject.instance().mapLayers(), "No loose imports without a workspace"
    assert "Create or open" in dialog.status.text()
    farm_root = create_farm(root, "Workspace", QgsCoordinateReferenceSystem("EPSG:4326"),
                            organisation="Org", client="Grower", farm="Home", field="North")
    project = QgsProject.instance()
    project.setFileName(str(farm_root / "Farm.qgz"))
    project.writeEntry("AgTechTooling", "farm_id", store.workspace_id(farm_root))
    field_id = store.records(farm_root)["field"][0]["id"]
    boundary = QgsVectorLayer(store.layer_uri(farm_root, "agtech_boundaries"), "Boundary", "ogr")
    feature = QgsFeature(boundary.fields())
    feature["id"], feature["field_id"], feature["name"] = "test-boundary", field_id, "North"
    feature.setGeometry(QgsGeometry.fromWkt("MULTIPOLYGON(((144.9 -36.1,145.1 -36.1,145.1 -35.9,144.9 -35.9,144.9 -36.1)))"))
    assert boundary.dataProvider().addFeatures([feature])[0]
    del feature, boundary
    dialog.add_selected()
    assert len(QgsProject.instance().mapLayers()) == 1
    assert all(layer.readOnly() for layer in QgsProject.instance().mapLayers().values())
    assert iface.refreshed == 1 and iface.zoomed == 1
    dialog.tree.topLevelItem(0).setCheckState(0, Qt.Checked)
    dialog.add_selected()
    assert len(QgsProject.instance().mapLayers()) == 1, "Repeated add must not duplicate layers"
    assert "1 already assigned" in dialog.status.text()
    placed = next(iter(project.mapLayers().values()))
    assert placed.customProperty("AgTechTooling/import_field") == field_id
    node = project.layerTreeRoot().findLayer(placed.id())
    assert node.parent().name() == "Imported Data" and node.parent().parent().name() == "Whole Field"
    del node, placed
    assert all(not b.icon().isNull() for b in dialog.findChildren(QPushButton))
    dialog.show_result(machine_result)
    assert not dialog.add_button.isEnabled()
    assert dialog.tree.topLevelItem(0).child(0).child(0).child(0).text(0) == "North"
    dialog.show_result(raster_result)
    dialog.add_selected()
    assert len(QgsProject.instance().mapLayers()) == 2
    dialog.path.setText(str(root / "Missing"))
    dialog.start_scan()
    wait_until(lambda: dialog.task is None)
    assert "Could not scan" in dialog.status.text()
    assert not dialog.add_button.isEnabled(), "Failed rescan must discard stale selection"
    # Close during a task; queued completion must not touch a closed/deleted dialog.
    dialog.path.setText(str(source))
    dialog.start_scan()
    dialog.reject()
    assert dialog.path.isEnabled()
    wait_until(lambda: QgsApplication.taskManager().countActiveTasks() == 0)
    actions = ImportActions(iface)
    actions.open()
    opened = actions.dialog
    actions.open()
    assert actions.dialog is opened
    actions.close()
    assert actions.dialog is None
    dialog.deleteLater()
    app.processEvents()
    QgsProject.instance().clear()
    app.exitQgis()  # Release native provider pools before deleting Windows fixtures.
print("Data In native discovery, ZIP, source safety, async UI, map add and lifecycle checks passed")
