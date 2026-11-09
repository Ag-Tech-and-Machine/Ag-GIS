"""Exercise real native checkbox pixels after background name/indicator clicks.

AGTECH_CHECKBOX_REAL_APP is only for a fresh isolated QGIS --code harness.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import sys
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.PyQt.QtCore import Qt, QEvent
from qgis.PyQt.QtGui import QImage, QPainter
from qgis.PyQt.QtWidgets import QMainWindow, QDockWidget, QStyle, QStyleOptionViewItem, QStyledItemDelegate
from qgis.PyQt.QtTest import QTest
from qgis.core import QgsApplication, QgsProject, QgsLayerTreeModel
from qgis.gui import QgsMapCanvas, QgsLayerTreeView, QgsLayerTreeMapCanvasBridge
from ag_tech_tooling.background_maps import ensure_background, background_layers, BackgroundMaps
from ag_tech_tooling.farm_browser import FarmBrowser

real_app = bool(os.environ.get("AGTECH_CHECKBOX_REAL_APP"))
app = QgsApplication.instance() if real_app else QgsApplication([], False)
if not real_app:
    app.initQgis()
project = QgsProject.instance()
if real_app and (project.fileName() or project.mapLayers() or project.isDirty()):
    raise RuntimeError("Paint check requires an empty project in an isolated QGIS process")
project.writeEntry("AgTechTooling", "schema_version", 2)
project.writeEntry("AgTechTooling", "view/background", "osm")
ensure_background()

class PaintedChecks(QStyledItemDelegate):
    """Capture actual viewport checkbox pixels without replacing QGIS's style.

    Do not grab/repaint in assertions: that would hide stale notifications.
    """
    def __init__(self, view, wrapped):
        super().__init__(view)
        self.view, self.wrapped = view, wrapped
        self.painted = {}
        self.dirty = view.viewport().rect()
        view.viewport().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Paint:
            self.dirty = event.region()
        return False

    def initStyleOption(self, option, index):
        self.wrapped.initStyleOption(option, index)

    def sizeHint(self, option, index):
        return self.wrapped.sizeHint(option, index)

    def editorEvent(self, event, model, option, index):
        return self.wrapped.editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        image = QImage(option.rect.size(), QImage.Format_ARGB32_Premultiplied)
        image.fill(option.palette.base().color())
        capture = QPainter(image)
        capture.translate(-option.rect.topLeft())
        self.wrapped.paint(capture, option, index)
        capture.end()
        painter.drawImage(option.rect.topLeft(), image)
        name = index.data(Qt.DisplayRole)
        old = self.painted.get(name)
        visible = QImage(image.size(), image.format())
        visible.fill(Qt.transparent)
        composite = QPainter(visible)
        if old:
            composite.drawImage(0, 0, old[0])
        composite.setClipRegion(self.dirty.translated(-option.rect.topLeft()))
        composite.drawImage(0, 0, image)
        composite.end()
        self.painted[name] = visible, QStyleOptionViewItem(option), index

    def assert_painted(self, layer, expected):
        image, option, index = self.painted[layer.name()]
        self.initStyleOption(option, index)
        check = self.view.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, self.view)
        check.translate(-option.rect.topLeft())
        reference = QImage(image.size(), image.format())
        reference.fill(option.palette.base().color())
        option.checkState = expected
        capture = QPainter(reference)
        capture.translate(-option.rect.topLeft())
        self.view.style().drawControl(QStyle.CE_ItemViewItem, option, capture, self.view)
        capture.end()
        assert not check.isEmpty(), (layer.name(), "missing painted check indicator")
        assert self.view.viewport().rect().contains(check.translated(option.rect.topLeft())), (layer.name(), "test checkbox must be fully on screen")
        if image.copy(check) != reference.copy(check) and os.environ.get("AGTECH_TEST_ARTIFACTS"):
            directory = Path(os.environ["AGTECH_TEST_ARTIFACTS"])
            directory.mkdir(parents=True, exist_ok=True)
            image.copy(check).save(str(directory / "checkbox-actual.png"))
            reference.copy(check).save(str(directory / "checkbox-expected.png"))
            print("Checkbox paint diagnostics:", layer.name(), option.rect, check, self.dirty.boundingRect(), flush=True)
        assert image.copy(check) == reference.copy(check), (layer.name(), "painted checkbox differs", expected, index.data(Qt.CheckStateRole))

class Interface:
    def __init__(self):
        self.window = QMainWindow()
        self.canvas = QgsMapCanvas()
        self.canvas.setRenderFlag(False)
        self.window.setCentralWidget(self.canvas)
        self.view = QgsLayerTreeView()
        self.model = QgsLayerTreeModel(project.layerTreeRoot())
        self.model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility, True)
        self.view.setModel(self.model)
        self.dock = QDockWidget("Layers", self.window)
        self.dock.setWidget(self.view)
        self.window.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.window.resize(1000, 600)
        self.bridge = QgsLayerTreeMapCanvasBridge(project.layerTreeRoot(), self.canvas)
    def layerTreeView(self): return self.view
    def mapCanvas(self): return self.canvas

if real_app:
    from qgis.utils import iface as actual_iface
    iface = type("ActualInterface", (), {})()
    iface.view, iface.window, iface.canvas = actual_iface.layerTreeView(), actual_iface.mainWindow(), actual_iface.mapCanvas()
    iface.layerTreeView, iface.mapCanvas = actual_iface.layerTreeView, actual_iface.mapCanvas
    iface.canvas.setRenderFlag(False)
    iface.window.resize(1200, 800)
    for dock in iface.window.findChildren(QDockWidget):
        if not dock.isAncestorOf(iface.view):
            dock.hide()
else:
    iface = Interface()
browser = FarmBrowser(iface)
probe = PaintedChecks(iface.view, browser.delegate)
iface.view.setItemDelegate(probe)
controller = BackgroundMaps(iface)
iface.window.show()
QTest.qWait(30)
layers = background_layers()

def click(key, label):
    node = project.layerTreeRoot().findLayer(layers[key].id())
    index = iface.view.node2index(node)
    iface.view.scrollTo(index)
    app.processEvents()
    option = QStyleOptionViewItem()
    iface.view.itemDelegate().initStyleOption(option, index)
    option.rect = iface.view.visualRect(index)
    option.widget = iface.view
    check = iface.view.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, iface.view)
    text = iface.view.style().subElementRect(QStyle.SE_ItemViewItemText, option, iface.view)
    position = text.intersected(iface.view.viewport().rect()).center() if label else check.center()
    assert iface.view.viewport().rect().contains(position)
    QTest.mouseClick(iface.view.viewport(), Qt.LeftButton, Qt.NoModifier, position)
    QTest.qWait(30)

def assert_painted(selected):
    for key, layer in layers.items():
        probe.assert_painted(layer, Qt.Checked if key == selected else Qt.Unchecked)
    assert controller.visible_providers() == ([selected] if selected else [])

try:
    assert_painted("osm")
    for key in ("satellite_world", "satellite_au", "esri_world", "osm") * 3:
        click(key, label=True)
        assert_painted(key)
    click("osm", label=False)
    assert_painted(None)
    for key in ("satellite_world", "satellite_au", "esri_world", "osm") * 3:
        click(key, label=False)
        assert_painted(key)
    print("Background checkbox paint after name and indicator clicks passed")
finally:
    controller.close()
    iface.view.viewport().removeEventFilter(probe)
    iface.view.setItemDelegate(browser.delegate)
    browser.close()
    if not real_app:
        iface.window.close()
    project.clear()
if not real_app:
    app.exitQgis()
