"""Real GDAL/PyQGIS creation, portability and rejection checks on temporary data."""
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QMainWindow, QMessageBox, QDialog
from ag_tech_tooling.farm_project import create_farm, validate_farm, validate_name
from ag_tech_tooling.farm_dialog import FarmActions, NewFarmDialog
from osgeo import ogr, osr


def rejected(callback):
    try:
        callback()
    except (ValueError, OSError):
        return
    raise AssertionError("Expected rejection")


app = QgsApplication([], False)
app.initQgis()
with tempfile.TemporaryDirectory(prefix="agtech-farm-test-") as temporary:
    parent = Path(temporary)
    crs = QgsCoordinateReferenceSystem("EPSG:7855")
    for name in ("", "../escape", "CON", "Bad:name", "trailing."):
        rejected(lambda: validate_name(name))
    rejected(lambda: create_farm(parent, "Invalid", QgsCoordinateReferenceSystem()))
    assert not (parent / "Invalid").exists()
    root = create_farm(parent, "Test Farm", crs)
    info = validate_farm(root)
    assert info["name"] == "Test Farm" and info["crs"] == "EPSG:7855"
    original = (root / "Data/farm.gpkg").read_bytes()
    rejected(lambda: create_farm(parent, "Test Farm", crs))
    assert (root / "Data/farm.gpkg").read_bytes() == original
    assert not list(parent.glob(".agtech-create-*"))
    with patch("ag_tech_tooling.farm_project.validate_farm", side_effect=ValueError("Simulated validation failure")):
        rejected(lambda: create_farm(parent, "Failed farm", crs))
    assert not (parent / "Failed farm").exists()
    assert not list(parent.glob(".agtech-create-*"))

    # Add an actual spatial layer and save it with a relative source path.
    database = ogr.Open(str(root / "Data/farm.gpkg"), 1)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(7855)
    layer = database.CreateLayer("test_points", srs, ogr.wkbPoint)
    layer = None
    database = None
    project = QgsProject()
    assert project.read(info["project"])
    vector = QgsVectorLayer(str(root / "Data/farm.gpkg") + "|layername=test_points", "Sample points", "ogr")
    assert vector.isValid()
    project.addMapLayer(vector)
    assert project.write()
    project.clear()
    del vector, project
    moved = parent / "Moved Farm"
    root.rename(moved)
    moved_info = validate_farm(moved)
    assert moved_info["farm_id"] == info["farm_id"]

    class Interface:
        def __init__(self):
            self.window = QMainWindow()
            self.opened = []
        def mainWindow(self):
            return self.window
        def addProject(self, path):
            self.opened.append(path)
            return QgsProject.instance().read(path)
        def messageBar(self):
            return self
        def pushMessage(self, *args, **kwargs):
            pass

    iface = Interface()
    actions = FarmActions(iface)
    dialog = NewFarmDialog(iface.window)
    assert dialog.name.text() == "My Farm Data"
    assert isinstance(dialog, QDialog)
    dialog.close()
    assert actions.open_root(moved)
    assert len(QgsProject.instance().mapLayers()) == 1
    editable = next(iter(QgsProject.instance().mapLayers().values()))
    assert editable.startEditing()
    with patch.object(QMessageBox, "information"):
        assert not actions.open_root(moved)
    assert len(iface.opened) == 1 and editable.isEditable()
    editable.rollBack()
    del editable
    singleton = QgsProject.instance()
    singleton.setDirty(True)
    question = QMessageBox.question
    QMessageBox.question = lambda *args: QMessageBox.Cancel
    assert not actions.open_root(moved)
    assert len(iface.opened) == 1 and singleton.isDirty()
    QMessageBox.question = question
    singleton.clear()
    with closing(sqlite3.connect(moved / "Data/farm.gpkg")) as connection, connection:
        connection.execute("UPDATE agtech_farm SET schema_version='999'")
    before = (moved / "Data/farm.gpkg").read_bytes()
    rejected(lambda: validate_farm(moved))
    assert (moved / "Data/farm.gpkg").read_bytes() == before
    with closing(sqlite3.connect(moved / "Data/farm.gpkg")) as connection, connection:
        connection.execute("UPDATE agtech_farm SET schema_version='1'")
    (moved / "Farm.qgz").rename(moved / "Missing.qgz")
    rejected(lambda: validate_farm(moved))
    iface.window.close()
print("Farm creation, duplicate protection, schema rejection, move/reopen and cancel checks passed")
app.exitQgis()
