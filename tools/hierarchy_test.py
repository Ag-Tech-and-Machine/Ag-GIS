"""Exercise hierarchy persistence, native map filtering, icons and copy upgrades."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QDialog, QMainWindow, QPushButton, QTreeWidgetItemIterator
from qgis.PyQt.QtCore import Qt
from ag_tech_tooling.farm_project import create_farm, upgrade_copy, validate_farm
from ag_tech_tooling import hierarchy as store
from ag_tech_tooling.hierarchy_dialog import HierarchyDialog, show_field, NameDialog
from ag_tech_tooling.farm_dialog import NewFarmDialog
from ag_tech_tooling.ui_icons import icon


def reject(callback):
    try:
        callback()
    except (ValueError, OSError, RuntimeError):
        return
    raise AssertionError("Expected rejection")


def hashes(root):
    return {str(file.relative_to(root)): hashlib.sha256(file.read_bytes()).hexdigest()
            for file in root.rglob("*") if file.is_file()}


app = QgsApplication([], False)
app.initQgis()
with tempfile.TemporaryDirectory(prefix="agtech-hierarchy-test-") as temporary:
    parent = Path(temporary)
    crs = QgsCoordinateReferenceSystem("EPSG:7855")
    root = create_farm(parent, "Workspace", crs, organisation="Ag Tech", client="Smith", farm="Home", field="North")
    assert validate_farm(root)["version"] == 2
    rows = store.validate(root)
    organisation = rows["organisation"][0]["id"]
    smith = rows["client"][0]["id"]
    farm = rows["farm"][0]["id"]
    north = rows["field"][0]["id"]
    jones = store.add_record(root, "client", "Jones", organisation)
    other_farm = store.add_record(root, "farm", "Home", jones)
    other_field = store.add_record(root, "field", "North", other_farm)
    reject(lambda: store.add_record(root, "field", "north", farm))
    reject(lambda: store.add_record(root, "farm", "Orphan", "missing"))
    season = store.add_record(root, "season", "2026 Winter", north, start="2026-04-01", end="2026-12-31")
    crop = store.add_record(root, "crop", "Wheat", season)
    store.add_record(root, "crop", "Canola trial", season)
    reject(lambda: store.add_record(root, "season", "Wrong dates", north, start="2026-12-31", end="2026-01-01"))
    store.rename_record(root, "field", north, "North Paddock")
    assert store.records(root)["season"][0]["field_id"] == north
    assert len(store.validate(root)["crop"]) == 2

    # Reject orphan rows even through an external native provider write.
    clients = QgsVectorLayer(f"{store.database(root)}|layername=agtech_clients", "clients", "ogr")
    bad = QgsFeature(clients.fields())
    bad["id"], bad["name"], bad["organisation_id"] = "bad", "Orphan", "missing"
    assert not clients.dataProvider().addFeatures([bad])[0]
    del clients, bad

    class Interface:
        def __init__(self):
            self.window = QMainWindow()
        def mainWindow(self):
            return self.window

    iface = Interface()
    dialog = HierarchyDialog(root, iface)
    iterator = QTreeWidgetItemIterator(dialog.tree)
    field_item = None
    while iterator.value():
        item = iterator.value()
        assert not item.icon(0).isNull(), item.text(0)
        if item.data(0, Qt.UserRole) == ("field", north):
            field_item = item
        iterator += 1
    assert field_item is not None
    dialog.tree.setCurrentItem(field_item)
    assert dialog.add_buttons["season"].isEnabled() and not dialog.add_buttons["crop"].isEnabled()
    assert dialog.show_button.isEnabled()
    assert all(not button.icon().isNull() for button in dialog.findChildren(QPushButton))
    class AcceptedName(NameDialog):
        def exec(self):
            self.name.setText("2027 Summer")
            self.start.setText("2027-01-01")
            self.end.setText("2027-03-01")
            return QDialog.Accepted
    with patch("ag_tech_tooling.hierarchy_dialog.NameDialog", AcceptedName):
        dialog.add("season")
    assert len(store.records(root)["season"]) == 2
    assert dialog.tree.currentItem().data(0, Qt.UserRole)[0] == "season"
    assert dialog.add_buttons["crop"].isEnabled()
    before_cancel = store.records(root)
    with patch.object(NameDialog, "exec", return_value=QDialog.Rejected):
        dialog.add("crop")
    assert store.records(root) == before_cancel
    new_dialog = NewFarmDialog(iface.window)
    assert all(not button.icon().isNull() for button in new_dialog.findChildren(QPushButton))
    assert all(not icon(kind).isNull() for kind in store.ENTITIES)
    new_dialog.close()
    dialog.close()

    project = QgsProject.instance()
    project.clear()
    assert project.read(str(root / "Farm.qgz"))
    outsider = QgsVectorLayer("Point?crs=EPSG:7855", "User data", "memory")
    project.addMapLayer(outsider)
    show_field(root, north)
    assert len(project.mapLayers()) == 4
    guidance = next(layer for layer in project.mapLayers().values() if layer.name() == "Guidance Lines")
    feature = QgsFeature(guidance.fields())
    feature["field_id"], feature["id"], feature["name"], feature["revision"] = north, "line1", "AB 1", "1"
    feature.setGeometry(QgsGeometry.fromWkt("MULTILINESTRING ((350000 6000000,350100 6000100))"))
    assert guidance.dataProvider().addFeatures([feature])[0]
    assert guidance.featureCount() == 1
    show_field(root, other_field)
    assert len(project.mapLayers()) == 4 and guidance.featureCount() == 0
    show_field(root, north)
    assert guidance.featureCount() == 1 and outsider.id() in project.mapLayers()
    assert project.readEntry("AgTechTooling", "selected_field")[0] == north
    project.removeMapLayer(outsider.id())
    assert project.write()
    project.clear()
    del feature, guidance, outsider
    moved_root = parent / "Moved hierarchy"
    root.rename(moved_root)
    root = moved_root
    assert validate_farm(root)["version"] == 2
    assert project.read(str(root / "Farm.qgz"))
    show_field(root, north)
    assert len(project.mapLayers()) == 3, "Moving/reopening must not duplicate managed layers"
    project.clear()

    legacy = create_farm(parent, "Legacy", crs)
    (legacy / "notes.txt").write_text("Keep me", encoding="utf-8")
    before = hashes(legacy)
    upgraded = upgrade_copy(legacy, parent, "Upgraded", "My Organisation", "My Client")
    assert hashes(legacy) == before
    assert validate_farm(legacy)["version"] == 1 and validate_farm(upgraded)["version"] == 2
    assert store.records(upgraded)["farm"][0]["id"] == validate_farm(legacy)["farm_id"]
    assert (upgraded / "notes.txt").read_text() == "Keep me"
    reject(lambda: upgrade_copy(legacy, parent, "Upgraded", "Org", "Client"))
    reject(lambda: upgrade_copy(legacy, legacy, "Nested", "Org", "Client"))
    with patch("ag_tech_tooling.hierarchy.initialise", side_effect=ValueError("Simulated failure")):
        reject(lambda: upgrade_copy(legacy, parent, "Failed upgrade", "Org", "Client"))
    assert not (parent / "Failed upgrade").exists() and hashes(legacy) == before
    assert not list(parent.glob(".agtech-upgrade-*"))
    iface.window.close()
print("Hierarchy, duplicate/orphan protection, season/crop records, icons, native map filtering and copy upgrade checks passed")
app.exitQgis()
