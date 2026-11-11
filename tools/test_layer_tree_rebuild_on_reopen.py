"""Test that layer tree hierarchy is rebuilt on project reopen (Issue #3 fix).



This test verifies that when a Farm.qgz project is opened, the layer tree

hierarchy (organisations, clients, farms, fields, etc.) is properly rebuilt

by calling sync_tree, which was previously missing from the project_read handler.

"""

import os

import sys

import tempfile

import json

from pathlib import Path

from contextlib import ExitStack



os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))



    pass  # QGIS not available, skip this test

except ImportError:

    from qgis.gui import QgsLayerTreeView

    from qgis.core import QgsApplication, QgsLayerTreeModel, QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem

    from qgis.PyQt.QtTest import QTest

    from qgis.PyQt.QtWidgets import QDockWidget, QMainWindow, QStyle, QStyleOptionViewItem, QLineEdit, QWidget, QVBoxLayout, QToolBar

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtCore import Qt
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

from ag_tech_tooling.workspace_defaults import create_default

from ag_tech_tooling.hierarchy_dialog import sync_tree

from ag_tech_tooling.farm_browser import FarmBrowser, KINDS

from ag_tech_tooling.background_maps import PROVIDERS

from ag_tech_tooling.ui_icons import icon

from ag_tech_tooling import hierarchy as store



# Initialize QGIS application

app = QgsApplication([], False)

app.initQgis()

project = QgsProject.instance()



# Create a temporary workspace with farm data

with tempfile.TemporaryDirectory(prefix="agtech-layer-tree-rebuild-test-") as temp_dir, ExitStack() as cleanup:

    cleanup.callback(project.clear)

    temp_path = Path(temp_dir)

    root = create_default(parent=temp_path)

    

    # Add some hierarchy data

    rows = store.records(root)

    season_id = rows["season"][0]["id"]

    farm_id = rows["farm"][0]["id"]

    field_id = rows["field"][0]["id"]

    

    # Create additional hierarchy levels

    org_id = store.add_record(root, "organisation", "Test Org", start="2026-01-01", end="2026-12-31")

    client_id = store.add_record(root, "client", "Test Client", org_id)

    farm_id2 = store.add_record(root, "farm", "Test Farm", client_id)

    

    # Create a layer tree group for testing

    test_layer = QgsVectorLayer("Point?crs=EPSG:4326", "Test layer", "memory")

    project.addMapLayer(test_layer)

    

    # Create an interface for the FarmBrowser

    class Interface:

        def __init__(self):

            self.window = QMainWindow()

            self.dock = QDockWidget("Layers", self.window)

            self.view = QgsLayerTreeView()

            self.model = QgsLayerTreeModel(project.layerTreeRoot())

            self.model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility, True)

            self.model.setFlag(QgsLayerTreeModel.AllowNodeRename, True)

            self.view.setModel(self.model)

            self.contents = QWidget()

            layout = QVBoxLayout(self.contents)

            layout.setContentsMargins(0, 0, 0, 0)

            layout.setSpacing(0)

            self.toolbar = QToolBar()

            self.toolbar.addAction("Add Group")

            layout.addWidget(self.toolbar)

            layout.addWidget(self.view)

            self.dock.setWidget(self.contents)

            self.window.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

            self.window.resize(440, 740)

        def layerTreeView(self):

            return self.view

    

    iface = Interface()

    view = iface.view

    

    # Save the project

    farm_qgz = root / "Farm.qgz"

    iface.window.show()

    view.expandAllNodes()

    app.processEvents()

    

    # Verify initial state has the Farm Data group

    found_kinds = set()

    def count_kinds(node):

        kind = browser.delegate.kind(view.node2index(node)) if browser and view.node2index(node) else None

        if kind:

            found_kinds.add(kind)

        for child in node.children():

            count_kinds(child)

    

    # Create and configure FarmBrowser

    browser = FarmBrowser(iface)

    browser.refresh_title()

    

    app.processEvents()

    

    # Check that we have the expected kinds in the tree

    group = project.layerTreeRoot().findGroup("Farm Data")

    assert group is not None, "Farm Data group should exist"

    

    # Count all kinds in the tree

    count_kinds(group)

    

    print(f"Found kinds in initial tree: {found_kinds}")

    print(f"Expected kinds: {set(KINDS.keys())}")

    

    # Verify we have at least some of the expected kinds

    assert len(found_kinds) > 0, "Should have at least some kinds in the tree"

    

    # Close the browser

    browser.close()

    browser.close()

    

    # Verify the restore

    assert view.itemDelegate() is view.itemDelegate().native, "Restore must not nest wrappers"

    

    # Reopen the project (simulates cold start)

    project.clear()

    project.read(str(farm_qgz))

    

    # Create a new FarmBrowser instance

    browser2 = FarmBrowser(iface)

    browser2.refresh_title()

    

    app.processEvents()

    

    # Count kinds after reopen

    found_kinds_after = set()

    count_kinds(group)

    

    print(f"Found kinds after reopen: {found_kinds_after}")

    

    # Verify the layer tree hierarchy is still there after reopen

    assert len(found_kinds_after) > 0, "Layer tree hierarchy should be rebuilt on reopen"

    

    # Verify the delegate is not double-wrapped (restore must not nest wrappers)

    # After the restore cycle, the delegate should be the original native delegate,

    # not a wrapped FarmTreeDelegate. A FarmTreeDelegate has a .native attribute,

    # so we check that the current delegate does NOT have this attribute.

    current_delegate = view.itemDelegate()

    if current_delegate is not None:

        # FarmTreeDelegate has a .native attribute; the original delegate doesn't

        # If current_delegate doesn't have .native, it's the original delegate (good)

        assert not hasattr(current_delegate, 'native'), "Delegate should be the original native delegate, not a wrapped FarmTreeDelegate"

    

    # Clean up

    browser2.close()

    iface.window.close()

    project.clear()



print("Layer tree rebuild on reopen test passed")

app.exitQgis()


