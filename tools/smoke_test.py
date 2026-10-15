"""Exercise the starter action with real QGIS/Qt and a small interface adapter."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsProject
from qgis.PyQt.QtWidgets import QMainWindow
from qgis.PyQt.QtWidgets import QDockWidget, QToolBar, QLabel, QStackedWidget, QWidget
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import QAction, QToolButton
from ag_tech_tooling import classFactory
from ag_tech_tooling import simple_view


class Interface:
    def __init__(self):
        self.window = QMainWindow()
        self.window.setObjectName("test_qgis_window")
        self.pages = QStackedWidget(self.window)
        self.welcome = QLabel("Welcome, news and templates")
        self.canvas = QWidget()
        self.pages.addWidget(self.welcome)
        self.pages.addWidget(self.canvas)
        self.window.setCentralWidget(self.pages)
        self.file_bar = self.window.addToolBar("Project")
        self.file_bar.setObjectName("mFileToolBar")
        self.nav_bar = self.window.addToolBar("Navigation")
        self.nav_bar.setObjectName("mMapNavToolBar")
        self.advanced_bar = self.window.addToolBar("Digitizing")
        self.advanced_bar.setObjectName("mDigitizeToolBar")
        self.layers = self.make_dock("Layers")
        self.browser = self.make_dock("Browser")
        self.advanced_dock = self.make_dock("Advanced")
        self.browser.hide()
        self.menu_actions = []
        self.toolbar_actions = []
        self.messages = []
        self.native_actions = {name: QAction(name, self.window) for name in ("new", "open", "save", "pan", "in", "out", "full")}
        self.native_calls = []
        for name, action in self.native_actions.items():
            action.triggered.connect(lambda checked=False, key=name: self.native_calls.append(key))

    def addToolBar(self, name):
        return self.window.addToolBar(name)

    def actionSaveProject(self):
        return self.native_actions["save"]

    def actionNewProject(self):
        return self.native_actions["new"]

    def actionOpenProject(self):
        return self.native_actions["open"]

    def actionPan(self):
        return self.native_actions["pan"]

    def actionZoomIn(self):
        return self.native_actions["in"]

    def actionZoomOut(self):
        return self.native_actions["out"]

    def actionZoomFullExtent(self):
        return self.native_actions["full"]

    def make_dock(self, name):
        dock = QDockWidget(name, self.window)
        dock.setObjectName(name)
        dock.setWidget(QLabel(name))
        self.window.addDockWidget(Qt.LeftDockWidgetArea, dock)
        return dock

    def fileToolBar(self):
        return self.file_bar

    def mapNavToolToolBar(self):
        return self.nav_bar

    def mapCanvas(self):
        return self.canvas

    def mainWindow(self):
        return self.window

    def addPluginToMenu(self, menu, action):
        self.menu_actions.append(action)

    def addToolBarIcon(self, action):
        self.toolbar_actions.append(action)

    def removePluginMenu(self, menu, action):
        self.menu_actions.remove(action)

    def removeToolBarIcon(self, action):
        self.toolbar_actions.remove(action)

    def messageBar(self):
        return self

    def pushMessage(self, *args, **kwargs):
        self.messages.append((args, kwargs))


app = QgsApplication([], False)
app.initQgis()
test_settings = tempfile.TemporaryDirectory(prefix="ag-tech-tooling-test-")
simple_view.QgsSettings = lambda: QSettings(str(Path(test_settings.name) / "test.ini"), QSettings.IniFormat)
iface = Interface()
iface.window.show()
app.processEvents()
plugin = classFactory(iface)
plugin.initGui()
plugin.initGui()
assert len(iface.menu_actions) == 7 and not iface.toolbar_actions
toolbar = plugin.toolbar
assert iface.window.toolBarArea(toolbar) == Qt.TopToolBarArea
assert not toolbar.isMovable() and not toolbar.isFloatable()
buttons = {button.text(): button for button in toolbar.findChildren(QToolButton) if button.defaultAction()}
assert set(buttons) == {"New Project", "Open Project", "Manage Data", "Data In", "Save Map", "Move Map", "Zoom In", "Zoom Out", "Whole Map"}
buttons["Data In"].click()
assert plugin.imports.dialog.isVisible()
assert plugin.imports.dialog.windowTitle() == "Data In"
plugin.imports.dialog.reject()
assert buttons["Save Map"].defaultAction() is iface.actionSaveProject()
buttons["Save Map"].click()
assert iface.native_calls == ["save"]
assert iface.actionSaveProject().text() == "save", "Do not relabel the native action elsewhere"
iface.actionSaveProject().setText("Save Project")
assert buttons["Save Map"].text() == "Save Map", "Keep plain-language labels when QGIS actions change"
plugin.action.trigger()
assert len(iface.messages) == 1
assert "Project layers: 0" in iface.messages[0][0][1]
controller = plugin.simple_view
assert controller.container.parentWidget() is iface.window.statusBar()
assert not controller.switch.isChecked()
controller.switch.setChecked(True)
assert iface.advanced_bar.isHidden() and iface.advanced_dock.isHidden()
assert iface.file_bar.isHidden() and iface.nav_bar.isHidden()
assert not toolbar.isHidden()
toolbar.hide()
app.processEvents()
assert not toolbar.isHidden(), "Farm toolbar must remain available in Simple view"
iface.file_bar.show()
iface.nav_bar.show()
assert iface.file_bar.isHidden() and iface.nav_bar.isHidden(), "Native startup restoration must not reopen toolbars"
late_bar = iface.window.addToolBar("Late plugin toolbar")
late_bar.setObjectName("LatePluginToolbar")
app.processEvents()
assert late_bar.isHidden(), "New plugin toolbars must be hidden in Simple view"
assert not iface.layers.isHidden() and iface.browser.isHidden()
iface.layers.hide()
app.processEvents()
assert not iface.layers.isHidden(), "Layers must remain available in Simple view"
assert iface.pages.currentWidget() is iface.canvas
iface.pages.setCurrentWidget(iface.welcome)
assert iface.pages.currentWidget() is iface.canvas, "Welcome page must stay hidden in Simple view"
iface.browser.show()
app.processEvents()
assert iface.browser.isHidden(), "Browser must not reopen in Simple view"
late_panel = iface.make_dock("Late plugin panel")
app.processEvents()
assert late_panel.isHidden(), "New panels must also be hidden"
controller.switch.setChecked(False)
assert iface.pages.currentWidget() is iface.welcome
assert not iface.advanced_bar.isHidden() and not iface.advanced_dock.isHidden()
assert iface.browser.isHidden(), "Original hidden Browser state must be restored"
controller.switch.setChecked(True)
plugin.unload()
plugin.unload()
assert not iface.menu_actions and not iface.toolbar_actions
assert not iface.advanced_bar.isHidden() and not iface.advanced_dock.isHidden()
assert controller.container.isHidden()
assert toolbar.isHidden() and iface.window.toolBarArea(toolbar) == Qt.NoToolBarArea
plugin = classFactory(iface)
plugin.initGui()
app.processEvents()
assert plugin.simple_view.switch.isChecked(), "Simple-view preference must survive reload"
assert not plugin.toolbar.isHidden()
assert len([bar for bar in plugin.simple_view.managed_toolbars() if bar.objectName() == "ag_tech_tooling_toolbar"]) == 1
plugin.simple_view.switch.setChecked(False)
plugin.unload()
assert iface.browser.isHidden()
assert iface.pages.currentWidget() is iface.welcome
plugin = classFactory(iface)
plugin.initGui()
plugin.simple_view.switch.setChecked(True)
QgsProject.instance().setFileName("new-map.qgz")
plugin.simple_view.switch.setChecked(False)
assert iface.pages.currentWidget() is iface.canvas, "Do not return to welcome after the project changes"
plugin.unload()
QgsProject.instance().setFileName("")
print("QGIS plugin action, simple-view restoration and reload checks passed")
iface.window.close()
app.exitQgis()
test_settings.cleanup()
