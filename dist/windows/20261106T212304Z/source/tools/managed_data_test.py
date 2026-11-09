"""Managed vector/raster copies, numeric fidelity, recovery, filtering and failure cleanup."""
import hashlib
import gc
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import (QgsApplication, QgsCoordinateReferenceSystem, QgsFeature, QgsField,
    QgsGeometry, QgsProject, QgsRasterLayer, QgsRasterBlockFeedback, QgsVectorLayer,
    QgsVectorFileWriter, QgsLayerTreeModel)
from qgis.PyQt.QtCore import QVariant, QEvent, QObject, pyqtSignal
from qgis.PyQt.QtWidgets import QMainWindow
from qgis.gui import QgsLayerTreeView
from osgeo import gdal
gdal.UseExceptions()
from ag_tech_tooling import managed_data as saved, hierarchy as store
from ag_tech_tooling.import_placement import place_layer
from ag_tech_tooling.hierarchy_dialog import show_field
from ag_tech_tooling.data_filter import DataFilterDialog
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling.farm_dialog import FarmActions
from ag_tech_tooling.hierarchy_dialog import sync_tree


def reopen(root):
    app = QgsApplication([], False)
    app.initQgis()
    project = QgsProject.instance()
    assert project.read(str(root / "Farm.qgz"))
    # Recover entirely from the catalogue, not just from saved layer-tree nodes.
    project.removeAllMapLayers()
    assert saved.restore_datasets(root) == []
    rows = saved.records(root)
    assert len(rows) == 5
    assert len(project.mapLayers()) == 5
    for layer in project.mapLayers().values():
        assert layer.isValid()
        path = str(layer.source()).split("|")[0]
        assert Path(path).resolve().is_relative_to(root.resolve())
        assert layer.customProperty("AgTechTooling/import_field")
    project.clear()
    app.exitQgis()


def exercise(root, originals):
    project = QgsProject.instance()
    first = store.records(root)["field"][0]["id"]
    second = store.add_record(root, "field", "South", store.records(root)["farm"][0]["id"])
    vector = QgsVectorLayer("PointZ?crs=EPSG:4326", "Samples", "memory")
    vector.dataProvider().addAttributes([QgsField("fid", QVariant.Int), QgsField("field_id", QVariant.String), QgsField("pH", QVariant.Double)])
    vector.updateFields()
    for x in (1, 2):
        feature = QgsFeature(vector.fields())
        feature.setAttributes([7, "source-field", 6.25 + x])
        feature.setGeometry(QgsGeometry.fromWkt(f"POINT Z({x} 1 12.125)"))
        assert vector.dataProvider().addFeatures([feature])[0]
    source_file = originals / "Samples.shp"
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName, options.includeZ = "ESRI Shapefile", True
    assert QgsVectorFileWriter.writeAsVectorFormatV3(vector, str(source_file), project.transformContext(), options)[0] == QgsVectorFileWriter.NoError
    vector = QgsVectorLayer(str(source_file), "Samples", "ogr")
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in originals.iterdir()}
    record, layer, created = saved.save_dataset(root, vector, first, "samples")
    assert created and layer.isValid() and layer.featureCount() == 2
    assert [f["fid"] for f in layer.getFeatures()] == [7, 7]
    assert {f["field_id"] for f in layer.getFeatures()} == {"source-field"}
    assert all(f.geometry().constGet().z() == 12.125 for f in layer.getFeatures())
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in originals.iterdir()}
    place_layer(root, layer, first, "samples")
    duplicate, duplicate_layer, created = saved.save_dataset(root, vector, first, "samples")
    assert not created and duplicate["id"] == record["id"] and len(saved.records(root)) == 1
    duplicate_layer = None
    # A second field/type remains independently addressable by the catalogue.
    other = QgsVectorLayer("LineStringM?crs=EPSG:4326", "Guidance", "memory")
    feature = QgsFeature(other.fields())
    feature.setGeometry(QgsGeometry.fromWkt("LINESTRING M(1 1 10,2 2 20)"))
    assert other.dataProvider().addFeatures([feature])[0]
    other_record, other_layer, _ = saved.save_dataset(root, other, second, "guidance")
    assert other_layer.wkbType() == other.wkbType()
    assert bytes(next(other_layer.getFeatures()).geometry().asWkb()) == bytes(next(other.getFeatures()).geometry().asWkb())
    place_layer(root, other_layer, second, "guidance")
    raster_file = originals / "Terrain.tif"
    dataset = gdal.GetDriverByName("GTiff").Create(str(raster_file), 2, 2, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform((1, .1, 0, 2, 0, -.1))
    dataset.SetProjection(QgsCoordinateReferenceSystem("EPSG:4326").toWkt())
    import struct
    band = dataset.GetRasterBand(1)
    band.WriteRaster(0, 0, 2, 2, struct.pack("ffff", 100.125, -9999, 101.75, 0.0))
    band.SetNoDataValue(-9999)
    band.SetScale(.01)
    band.SetOffset(100)
    band.SetUnitType("m")
    band.SetDescription("Measured elevation")
    band, dataset = None, None
    raster = QgsRasterLayer(str(raster_file), "Terrain", "gdal")
    raster_record, raster_layer, _ = saved.save_dataset(root, raster, first, "elevation")
    raster_saved = Path(saved.dataset_uri(root, raster_record))
    assert raster_saved.read_bytes() == raster_file.read_bytes(), "GeoTIFF must be a lossless complete copy"
    dataset = gdal.Open(str(raster_saved))
    band = dataset.GetRasterBand(1)
    assert band.GetUnitType() == "m" and band.GetScale() == .01 and band.GetOffset() == 100
    assert band.ReadRaster() == struct.pack("ffff", 100.125, -9999, 101.75, 0.0)
    band, dataset = None, None
    place_layer(root, raster_layer, first, "elevation")
    # Non-GeoTIFF numeric rasters use the native writer, not a rendered screenshot.
    ascii_file = originals / "Grid.asc"
    ascii_file.write_text("ncols 2\nnrows 2\nxllcorner 1\nyllcorner 1\ncellsize 0.5\nNODATA_value -9999\n100.125 101.75\n-9999 0\n")
    ascii_layer = QgsRasterLayer(str(ascii_file), "Grid", "gdal")
    ascii_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    ascii_record, ascii_saved, _ = saved.save_dataset(root, ascii_layer, second, "elevation")
    dataset = gdal.Open(saved.dataset_uri(root, ascii_record))
    assert dataset.GetRasterBand(1).ReadRaster(buf_type=gdal.GDT_Float64) == struct.pack("dddd", 100.125, 101.75, -9999, 0)
    dataset = None
    place_layer(root, ascii_saved, second, "elevation")
    virtual_file = originals / "Virtual.vrt"
    dataset = gdal.Translate(str(virtual_file), str(ascii_file), format="VRT", outputSRS="EPSG:4326")
    dataset = None
    virtual = QgsRasterLayer(str(virtual_file), "Virtual", "gdal")
    assert virtual.isValid() and saved.source_hash(virtual) == "", "VRT XML alone cannot establish pixel identity"
    # A WAL journal can change visible database data without changing its main file.
    state = originals / "Fingerprint.sqlite"
    state.write_bytes(b"unchanged main file")
    class DatabaseSource:
        def providerType(self): return "ogr"
        def source(self): return str(state)
        def crs(self): return QgsCoordinateReferenceSystem("EPSG:4326")
    identity = saved.source_hash(DatabaseSource())
    Path(str(state) + "-wal").write_bytes(b"new data waiting for checkpoint")
    assert saved.source_hash(DatabaseSource()) != identity
    # Classified rasters must retain their value-to-label/colour mapping too.
    palette_file = originals / "Zones.png"
    dataset = gdal.GetDriverByName("MEM").Create("", 2, 2, 1, gdal.GDT_Byte)
    dataset.SetGeoTransform((1, .1, 0, 2, 0, -.1))
    dataset.SetProjection(QgsCoordinateReferenceSystem("EPSG:4326").toWkt())
    colour = gdal.ColorTable()
    colour.SetColorEntry(0, (20, 60, 100, 255))
    colour.SetColorEntry(1, (200, 20, 10, 255))
    band = dataset.GetRasterBand(1)
    band.WriteRaster(0, 0, 2, 2, bytes([0, 1, 1, 0]))
    band.SetColorTable(colour)
    band.SetCategoryNames(["Low", "High"])
    png = gdal.GetDriverByName("PNG").CreateCopy(str(palette_file), dataset)
    png, band, dataset, colour = None, None, None, None
    classified = QgsRasterLayer(str(palette_file), "Zones", "gdal")
    zones_record, zones_layer, _ = saved.save_dataset(root, classified, first, "zones")
    dataset = gdal.Open(saved.dataset_uri(root, zones_record))
    band = dataset.GetRasterBand(1)
    assert band.ReadRaster() == bytes([0, 1, 1, 0])
    assert band.GetColorTable().GetColorEntry(1) == (200, 20, 10, 255)
    assert band.GetCategoryNames()[:2] == ["Low", "High"]
    band, dataset = None, None
    place_layer(root, zones_layer, first, "zones")
    unrelated = QgsVectorLayer("Point?crs=EPSG:4326", "Unrelated", "memory")
    project.addMapLayer(unrelated)
    saved.apply_filters(root, first, "*")
    nodes = {row["id"]: project.layerTreeRoot().findLayer(candidate.id()) for row in saved.records(root)
             for candidate in project.mapLayers().values() if candidate.customProperty("AgTechTooling/dataset_id") == row["id"]}
    assert nodes[record["id"]].itemVisibilityChecked()
    assert not nodes[other_record["id"]].itemVisibilityChecked()
    assert project.layerTreeRoot().findLayer(unrelated.id()).itemVisibilityChecked()
    saved.apply_filters(root, "*", "elevation")
    assert nodes[raster_record["id"]].itemVisibilityChecked() and not nodes[record["id"]].itemVisibilityChecked()
    saved.apply_filters(root, "*", "*")
    nodes[record["id"]].setItemVisibilityChecked(False)
    saved.apply_filters(root, second, "*")
    saved.apply_filters(root, "*", "*")
    assert not nodes[record["id"]].itemVisibilityChecked(), "Filters must preserve a manually hidden layer"
    show_field(root, second)
    assert not nodes[raster_record["id"]].itemVisibilityChecked()
    assert nodes[other_record["id"]].itemVisibilityChecked()
    # Exercise the real native selection model as well as filter predicates.
    class Interface(QObject):
        projectRead = pyqtSignal()
        def __init__(self):
            super().__init__()
            self.window = QMainWindow()
            self.view = QgsLayerTreeView(self.window)
            self.model = QgsLayerTreeModel(project.layerTreeRoot(), self.window)
            self.view.setModel(self.model)
            self.messages = []
        def mainWindow(self): return self.window
        def layerTreeView(self): return self.view
        def messageBar(self): return self
        def pushMessage(self, *args, **kwargs): self.messages.append(args)
    iface = Interface()
    farms = FarmActions(iface)
    farms.attach()
    QgsApplication.processEvents()
    _, branches = sync_tree(root)
    iface.view.setCurrentNode(branches[first])
    dialog = DataFilterDialog(root, iface.window, iface)
    dialog.field.setCurrentIndex(0)
    dialog.role.setCurrentIndex(dialog.role.findData("elevation"))
    dialog.apply()
    assert project.readEntry("AgTechTooling", "data_filter_role")[0] == "elevation"
    assert not iface.view.currentIndex().isValid(), "All fields must clear the old field highlight"
    before_navigation = {
        node.layerId(): (node.itemVisibilityChecked(),
                         node.layer().subsetString() if hasattr(node.layer(), "subsetString") else "")
        for node in project.layerTreeRoot().findLayers()
    }
    iface.view.setCurrentNode(branches[first])
    assert project.readEntry("AgTechTooling", "selected_field")[0] == first
    assert project.readEntry("AgTechTooling", "data_filter_field")[0] == "*", "Row navigation must not replace All fields"
    assert project.readEntry("AgTechTooling", "data_filter_role")[0] == "elevation"
    assert before_navigation == {
        node.layerId(): (node.itemVisibilityChecked(),
                         node.layer().subsetString() if hasattr(node.layer(), "subsetString") else "")
        for node in project.layerTreeRoot().findLayers()
    }, "Row navigation must preserve independent checks and provider subsets"
    assert not iface.messages
    dialog.reject()
    dialog.deleteLater()
    farms.detach()
    iface.window.deleteLater()
    QgsApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    QgsApplication.processEvents()
    # Shared native reference layers also support All Fields, and are read-only
    # there so new features cannot silently inherit the previous field.
    saved.apply_filters(root, "*", "*")
    core = [candidate for candidate in project.mapLayers().values() if candidate.customProperty("AgTechTooling/table")]
    assert len(core) == 3 and all(not candidate.subsetString() and candidate.readOnly() for candidate in core)
    saved.apply_filters(root, second, "*")
    assert all(second in candidate.subsetString() and not candidate.readOnly() for candidate in core)
    core = None
    # Cancellation and failed catalogue writes must not leave partial vector tables.
    count_before = len(saved.records(root))
    feedback = QgsRasterBlockFeedback()
    feedback.cancel()
    try:
        saved.save_dataset(root, vector, second, "samples", feedback)
        raise AssertionError("Cancelled copy accepted")
    except ValueError:
        pass
    with patch.object(saved, "_catalogue", side_effect=ValueError("Simulated catalogue failure")):
        try:
            saved.save_dataset(root, vector, second, "samples")
            raise AssertionError("Failed catalogue registration accepted")
        except ValueError:
            pass
    assert len(saved.records(root)) == count_before
    with patch.object(saved.uuid, "uuid4", return_value=SimpleNamespace(hex=record["id"])):
        try:
            saved.save_dataset(root, vector, second, "samples")
            raise AssertionError("Expected existing dataset name to be protected")
        except ValueError:
            pass
    assert layer.isValid() and layer.featureCount() == 2, "A failed import must never clean up an existing dataset"
    files_before = {p.name for p in raster_saved.parent.iterdir()}
    with patch.object(saved, "_catalogue", side_effect=ValueError("Simulated raster catalogue failure")):
        try:
            saved.save_dataset(root, raster, second, "elevation")
            raise AssertionError("Failed raster catalogue registration accepted")
        except ValueError:
            pass
    assert {p.name for p in raster_saved.parent.iterdir()} == files_before
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(store.database(root))) as connection:
        assert connection.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name LIKE 'agtech_data_%' AND name != 'agtech_datasets'").fetchone()[0] == 2
    assert project.write()
    project.clear()
    # Local wrappers die before provider pools and source folders are closed.


if len(sys.argv) == 3 and sys.argv[1] == "--reopen":
    reopen(Path(sys.argv[2]))
else:
    with tempfile.TemporaryDirectory(prefix="agtech-managed-") as temporary:
        parent = Path(temporary)
        originals = parent / "Originals"
        originals.mkdir()
        app = QgsApplication([], False)
        app.initQgis()
        root = create_farm(parent, "Workspace", QgsCoordinateReferenceSystem("EPSG:4326"),
                            organisation="Org", client="Grower", farm="Home", field="North")
        project = QgsProject.instance()
        assert project.read(str(root / "Farm.qgz"))
        exercise(root, originals)
        gc.collect()  # Release mocked-error traceback cycles before unloading native providers.
        app.exitQgis()
        assert originals.resolve().is_relative_to(parent.resolve())
        assert (parent / "Originals removed").resolve().is_relative_to(parent.resolve())
        originals.rename(parent / "Originals removed")
        # Move the entire saved farm, so both original paths and old workspace paths disappear.
        moved = parent / "Moved workspace"
        assert moved.resolve().is_relative_to(parent.resolve())
        root.rename(moved)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "--reopen", str(moved)], check=True)
    print("Managed copies, original removal, workspace move/recovery, numeric rasters, filters and failed-copy cleanup passed")
