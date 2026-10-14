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
assert len(iface.menu_actions) == 3 and len(iface.toolbar_actions) == 1
plugin.action.trigger()
assert len(iface.messages) == 1
assert "Project layers: 0" in iface.messages[0][0][1]
controller = plugin.simple_view
assert controller.container.parentWidget() is iface.window.statusBar()
assert not controller.switch.isChecked()
controller.switch.setChecked(True)
assert iface.advanced_bar.isHidden() and iface.advanced_dock.isHidden()
assert not iface.file_bar.isHidden() and not iface.nav_bar.isHidden()
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
plugin = classFactory(iface)
plugin.initGui()
app.processEvents()
assert plugin.simple_view.switch.isChecked(), "Simple-view preference must survive reload"
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
