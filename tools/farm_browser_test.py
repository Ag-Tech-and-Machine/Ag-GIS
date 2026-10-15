"""Verify semantic icons, native tree interactions and reversible presentation."""
import os
from pathlib import Path
import sys
import tempfile
from contextlib import ExitStack
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDockWidget, QMainWindow, QStyle, QStyleOptionViewItem, QLineEdit
from qgis.PyQt.QtTest import QTest
from qgis.core import QgsApplication, QgsLayerTreeModel, QgsProject, QgsVectorLayer
from qgis.gui import QgsLayerTreeView
from ag_tech_tooling.workspace_defaults import create_default
from ag_tech_tooling.hierarchy_dialog import sync_tree
from ag_tech_tooling.farm_browser import FarmBrowser, KINDS
from ag_tech_tooling.ui_icons import icon
from ag_tech_tooling import hierarchy as store

app = QgsApplication([], False)
app.initQgis()
project = QgsProject.instance()
with tempfile.TemporaryDirectory(prefix="agtech-browser-test-") as temporary, ExitStack() as cleanup:
    cleanup.callback(project.clear)
    root = create_default(parent=temporary)
    assert project.read(str(root / "Farm.qgz"))
    rows = store.records(root)
    store.add_record(root, "crop", "Wheat", rows["season"][0]["id"])
    group, nodes = sync_tree(root)
    unrelated = project.layerTreeRoot().addGroup("Other map layers")
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Survey points", "memory")
    project.addMapLayer(layer)

    class Interface:
        def __init__(self):
            self.window = QMainWindow()
            self.dock = QDockWidget("Layers", self.window)
            self.view = QgsLayerTreeView()
            self.model = QgsLayerTreeModel(project.layerTreeRoot())
            self.model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility, True)
            self.model.setFlag(QgsLayerTreeModel.AllowNodeRename, True)
            self.view.setModel(self.model)
            self.dock.setWidget(self.view)
            self.window.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
            self.window.resize(440, 740)
        def layerTreeView(self):
            return self.view
    iface = Interface()
    view = iface.view
    native, indentation, icon_size = view.itemDelegate(), view.indentation(), view.iconSize()
    model, selection = view.model(), view.selectionModel()
    browser = FarmBrowser(iface)
    iface.window.show()
    view.expandAllNodes()
    app.processEvents()
    assert view.model() is model and view.selectionModel() is selection
    assert view.indentation() == 14 and view.iconSize().width() == 20
    assert iface.dock.windowTitle() == "Farm Data"
    found = set()
    def verify(node):
        index = view.node2index(node)
        kind = browser.delegate.kind(index)
        if kind:
            found.add(kind)
            option = QStyleOptionViewItem()
            browser.delegate.initStyleOption(option, index)
            assert option.icon.pixmap(20, 20).toImage() == icon(KINDS[kind][0]).pixmap(20, 20).toImage(), kind
            assert browser.delegate.sizeHint(option, index).height() >= 26
            assert option.font.bold() if kind in {"workspace", "organisation"} else True
        for child in node.children():
            verify(child)
    verify(group)
    assert found == set(KINDS), found
    branch_images = [icon(kind).pixmap(20, 20).toImage() for kind in ("plan", "job", "result")]
    assert all(first != second for index, first in enumerate(branch_images) for second in branch_images[index + 1:])
    assert browser.delegate.kind(view.node2index(unrelated)) is None
    assert browser.delegate.kind(view.node2index(project.layerTreeRoot().findLayer(layer.id()))) is None
    # Use actual delegate mouse handling, not a programmatic visibility change.
    index = view.node2index(nodes[rows["field"][0]["id"]])
    option = QStyleOptionViewItem()
    browser.delegate.initStyleOption(option, index)
    option.rect = view.visualRect(index)
    option.widget = view
    check = view.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, view)
    field = nodes[rows["field"][0]["id"]]
    assert field.itemVisibilityChecked()
    QTest.mouseClick(view.viewport(), Qt.LeftButton, Qt.NoModifier, check.center())
    assert not field.itemVisibilityChecked()
    QTest.mouseClick(view.viewport(), Qt.LeftButton, Qt.NoModifier, check.center())
    assert field.itemVisibilityChecked()
    # Native editor lifecycle must continue to commit through the wrapper.
    index = view.node2index(unrelated)
    view.setCurrentIndex(index)
    view.edit(index)
    app.processEvents()
    editor = view.findChild(QLineEdit)
    assert editor is not None
    editor.setText("Other data renamed")
    QTest.keyClick(editor, Qt.Key_Return)
    app.processEvents()
    assert unrelated.name() == "Other data renamed"
    assert len(project.mapLayers()) == 4 and layer.isValid()
    browser.close()
    browser.close()
    assert view.itemDelegate() is native
    assert view.indentation() == indentation and view.iconSize() == icon_size
    assert iface.dock.windowTitle() == "Layers"
    browser = FarmBrowser(iface)
    assert browser.delegate.native is native, "Reload must not nest wrappers"
    project.clear()
    assert iface.dock.windowTitle() == "Layers"
    assert project.read(str(root / "Farm.qgz"))
    assert iface.dock.windowTitle() == "Farm Data"
    browser.close()
    iface.window.close()
    project.clear()
print("Farm browser icons, native visibility/editing, unrelated layers and presentation restoration passed")
app.exitQgis()
