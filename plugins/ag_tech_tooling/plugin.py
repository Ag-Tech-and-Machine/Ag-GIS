from qgis.PyQt.QtGui import QIcon
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction
from pathlib import Path
from qgis.core import Qgis, QgsProject


class AgTechTooling:
    """Minimal plugin with a clean menu/toolbar lifecycle."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.menu = "Ag Tech Tooling"

    def initGui(self):
        if self.action is not None:
            return
        icon = QIcon(str(Path(__file__).with_name("icon.svg")))
        self.action = QAction(icon, "Ag Tech Tooling", self.iface.mainWindow())
        self.action.setObjectName("ag_tech_tooling_action")
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.iface.addToolBarIcon(self.action)

    def run(self):
        layer_count = len(QgsProject.instance().mapLayers())
        self.iface.messageBar().pushMessage(
            "Ag Tech Tooling",
            f"Starter plugin is running. Project layers: {layer_count}.",
            level=Qgis.Info,
            duration=5,
        )

    def unload(self):
        if self.action is None:
            return
        self.iface.removePluginMenu(self.menu, self.action)
        self.iface.removeToolBarIcon(self.action)
        self.action.triggered.disconnect(self.run)
        self.action.deleteLater()
        self.action = None
