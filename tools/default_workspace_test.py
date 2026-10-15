"""One-click setup, known-location paths and complete native tree navigation."""
import os
from pathlib import Path
import sys
import tempfile
from contextlib import ExitStack
from unittest.mock import patch
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.PyQt.QtCore import Qt, QObject, pyqtSignal
from qgis.PyQt.QtWidgets import QMainWindow, QDialog
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer
from qgis.gui import QgsLayerTreeView
from qgis.core import QgsLayerTreeModel
from ag_tech_tooling import hierarchy as store
from ag_tech_tooling.workspace_defaults import projects_directory, create_default
from ag_tech_tooling.farm_project import validate_farm
from ag_tech_tooling.hierarchy_dialog import sync_tree, show_field
from ag_tech_tooling.farm_dialog import FarmActions
from osgeo import gdal

app = QgsApplication([], False)
app.initQgis()
native_errors = []
gdal.PushErrorHandler(lambda severity, code, message: native_errors.append(message)
                      if severity >= gdal.CE_Failure else None)
with tempfile.TemporaryDirectory(prefix="agtech-default-test-") as temporary, ExitStack() as cleanup:
    cleanup.callback(QgsProject.instance().clear)
    docs = Path(temporary) / "Documents"
    with patch("ag_tech_tooling.workspace_defaults.QStandardPaths.writableLocation", return_value=str(docs)):
        base = projects_directory()
        assert base == docs / "Ag Tech Tooling/Projects"
        with patch("ag_tech_tooling.workspace_defaults.QStandardPaths.writableLocation", return_value=""):
            from ag_tech_tooling.farm_dialog import NewFarmDialog
            options = NewFarmDialog(None)
            assert not options.location.text(), "Explicit location entry must remain usable without Documents"
            options.close()
        singleton = QgsProject.instance()
        original_name = singleton.fileName()
        root = create_default()
        assert singleton.fileName() == original_name and not singleton.mapLayers(), "Creation must not replace current work"
        assert root == base / "My Farm Data"
        assert validate_farm(root)["version"] == 2
        rows = store.records(root)
        assert all(len(rows[kind]) == 1 for kind in ("organisation", "client", "farm", "field", "season"))
        assert not rows["crop"], "Do not invent a crop"
        before = (root / "Data/farm.gpkg").read_bytes()
        second = create_default()
        assert second.name == "My Farm Data 2" and (root / "Data/farm.gpkg").read_bytes() == before
        assert singleton.read(str(root / "Farm.qgz"))
        group, nodes = sync_tree(root)
        assert group.name() == "Farm Data"
        organisation, client, farm, field, season = (rows[kind][0] for kind in ("organisation", "client", "farm", "field", "season"))
        assert nodes[client["id"]].parent() is nodes[organisation["id"]]
        assert nodes[farm["id"]].parent() is nodes[client["id"]]
        assert nodes[field["id"]].parent() is nodes[farm["id"]]
        assert nodes[season["id"]].parent().name() == "Seasons"
        assert nodes[season["id"]].parent().parent() is nodes[field["id"]]
        assert len(singleton.mapLayers()) == 3
        assert all(layer.featureCount() == 0 for layer in singleton.mapLayers().values())
        other_client = store.add_record(root, "client", "Client 2", organisation["id"])
        other_farm = store.add_record(root, "farm", "Farm 1", other_client)
        other_field = store.add_record(root, "field", "Field 1", other_farm)
        other_season = store.add_record(root, "season", "Season 1", other_field)
        group, nodes = sync_tree(root)
        assert nodes[other_client].parent() is nodes[organisation["id"]]
        assert nodes[other_field].parent() is nodes[other_farm]
        show_field(root, other_field)
        assert len(singleton.mapLayers()) == 3, "Reuse three views across all fields"
        assert all(layer.featureCount() == 0 for layer in singleton.mapLayers().values())
        _, nodes = sync_tree(root)
        whole = nodes["whole:" + other_field]
        assert len(whole.findLayers()) == 3 and not nodes["whole:" + field["id"]].findLayers()
        store.rename_record(root, "client", other_client, "Second Client")
        assert sync_tree(root)[1][other_client].name() == "Second Client"
        assert all(layer.featureCount() == 0 for layer in singleton.mapLayers().values())
        assert singleton.write()
        singleton.clear()
        assert singleton.read(str(root / "Farm.qgz"))
        assert sync_tree(root)[1][other_season].parent().parent().name() == "Field 1"

        class Interface(QObject):
            projectRead = pyqtSignal()
            def __init__(self):
                super().__init__()
                self.window = QMainWindow()
                self.view = QgsLayerTreeView()
                self.model = QgsLayerTreeModel(singleton.layerTreeRoot())
                self.view.setModel(self.model)
                self.window.setCentralWidget(self.view)
                self.messages = []
            def mainWindow(self):
                return self.window
            def addProject(self, path):
                return singleton.read(path)
            def layerTreeView(self):
                return self.view
            def messageBar(self):
                return self
            def pushMessage(self, *args, **kwargs):
                self.messages.append(args)
        iface = Interface()
        actions = FarmActions(iface)
        singleton.clear()
        with patch.object(QDialog, "exec", side_effect=AssertionError("Quick New must not open a form")):
            actions.new()
        assert Path(singleton.fileName()).parent.name == "My Farm Data 3"
        assert len(singleton.mapLayers()) == 3
        third = Path(singleton.fileName()).parent
        third_rows = store.records(third)
        extra = store.add_record(third, "field", "Field 2", third_rows["farm"][0]["id"])
        _, third_nodes = sync_tree(third)
        actions.attach()
        app.processEvents()
        iface.view.setCurrentNode(third_nodes[extra])
        assert singleton.readEntry("AgTechTooling", "selected_field")[0] == extra, iface.messages
        assert len(singleton.mapLayers()) == 3
        assert all(layer.featureCount() == 0 for layer in singleton.mapLayers().values())
        guidance = next(layer for layer in singleton.mapLayers().values() if layer.name() == "Guidance Lines")
        assert guidance.startEditing()
        iface.view.setCurrentNode(third_nodes[third_rows["field"][0]["id"]])
        assert singleton.readEntry("AgTechTooling", "selected_field")[0] == extra, "Do not switch field during edits"
        guidance.rollBack()
        del guidance
        actions.detach()
        actions.attach()
        actions.attach()
        actions.detach()
        app.processEvents()
        assert not actions.attached and actions.view is None
        singleton.clear()
        singleton.setDirty(True)
        with patch.object(actions, "can_replace_project", return_value=False):
            actions.new()
        assert not (base / "My Farm Data 4").exists(), "Cancelled switch must not create a new workspace"
        singleton.clear()
        iface.window.close()
gdal.PopErrorHandler()
assert not native_errors, native_errors
print("Default Documents setup, collision protection, no-form New and complete multi-client native tree checks passed")
app.exitQgis()
