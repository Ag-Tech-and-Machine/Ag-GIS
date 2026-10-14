"""Exercise the starter action with real QGIS/Qt and a small interface adapter."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins"))
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMainWindow
from qgis.PyQt.QtWidgets import QDockWidget, QToolBar, QLabel
from qgis.PyQt.QtCore import Qt, QSettings
from ag_tech_tooling import classFactory
from ag_tech_tooling import simple_view


class Interface:
    def __init__(self):
        self.window = QMainWindow()
        self.window.setObjectName("test_qgis_window")
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
plugin = classFactory(iface)
plugin.initGui()
plugin.initGui()
assert len(iface.menu_actions) == len(iface.toolbar_actions) == 1
plugin.action.trigger()
assert len(iface.messages) == 1
assert "Project layers: 0" in iface.messages[0][0][1]
controller = plugin.simple_view
assert controller.container.parentWidget() is iface.window.statusBar()
assert not controller.switch.isChecked()
controller.switch.setChecked(True)
assert iface.advanced_bar.isHidden() and iface.advanced_dock.isHidden()
assert not iface.file_bar.isHidden() and not iface.nav_bar.isHidden()
assert not iface.layers.isHidden() and not iface.browser.isHidden()
controller.switch.setChecked(False)
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
print("QGIS plugin action, simple-view restoration and reload checks passed")
iface.window.close()
app.exitQgis()
test_settings.cleanup()
