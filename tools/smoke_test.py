"""Exercise the starter action with real QGIS/Qt and a small interface adapter."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins"))
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMainWindow
from qgis_plugin_work import classFactory


class Interface:
    def __init__(self):
        self.window = QMainWindow()
        self.menu_actions = []
        self.toolbar_actions = []
        self.messages = []

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
iface = Interface()
plugin = classFactory(iface)
plugin.initGui()
plugin.initGui()
assert len(iface.menu_actions) == len(iface.toolbar_actions) == 1
plugin.action.trigger()
assert len(iface.messages) == 1
assert "Project layers: 0" in iface.messages[0][0][1]
plugin.unload()
plugin.unload()
assert not iface.menu_actions and not iface.toolbar_actions
print("QGIS plugin load/action/unload smoke check passed")
iface.window.close()
app.exitQgis()
