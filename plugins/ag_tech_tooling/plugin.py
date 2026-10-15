# SPDX-License-Identifier: GPL-2.0-or-later
from qgis.PyQt.QtGui import QIcon
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction
from pathlib import Path
from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtWidgets import QLabel, QToolButton
from qgis.core import Qgis, QgsProject
from .simple_view import SimpleView
from .farm_dialog import FarmActions
from .ui_icons import icon as ui_icon
from .farm_browser import FarmBrowser
from .import_dialog import ImportActions
from .updates import run_updates


class FarmToolButton(QToolButton):
    """Keep a plain-language label while a shared native action changes state."""

    def __init__(self, action, label, parent):
        super().__init__(parent)
        self.label = label
        self.setDefaultAction(action)
        self.setText(label)
        self.setAccessibleName(label)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(28, 28))

    def actionEvent(self, event):
        super().actionEvent(event)
        self.setText(self.label)


class AgTechTooling:
    """Farmer-friendly interface foundation with a clean plugin lifecycle."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.menu = "Ag-GIS"
        self.simple_view = None
        self.farm_actions = []
        self.farms = FarmActions(iface)
        self.imports = ImportActions(iface)
        self.toolbar = None
        self.browser = None

    def initGui(self):
        if self.action is not None:
            return
        icon = QIcon(str(Path(__file__).with_name("icon.svg")))
        self.action = QAction(icon, "Ag-GIS", self.iface.mainWindow())
        self.action.setObjectName("ag_tech_tooling_action")
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.toolbar = self.iface.addToolBar("Ag-GIS")
        self.toolbar.setObjectName("ag_tech_tooling_toolbar")
        self.iface.mainWindow().addToolBar(Qt.TopToolBarArea, self.toolbar)
        if self.iface.mainWindow().toolBarArea(self.iface.fileToolBar()) == Qt.TopToolBarArea:
            self.iface.mainWindow().insertToolBar(self.iface.fileToolBar(), self.toolbar)
            self.iface.mainWindow().insertToolBarBreak(self.iface.fileToolBar())
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        brand = QLabel("  Ag-GIS  ", self.toolbar)
        self.toolbar.addWidget(brand)
        for title, label, action_icon, callback in (
                ("New Project…", "New Project", self.iface.actionNewProject().icon(), self.farms.new),
                ("Open Project…", "Open Project", self.iface.actionOpenProject().icon(), self.farms.open),
                ("Manage Farm Data…", "Manage Data", ui_icon("organisation"), self.farms.manage),
                ("Data In…", "Data In", ui_icon("import"), self.imports.open)):
            action = QAction(action_icon, title, self.iface.mainWindow())
            action.triggered.connect(callback)
            self.iface.addPluginToMenu(self.menu, action)
            self.farm_actions.append((action, callback))
            self._add_button(action, label)
        self._add_button(self.iface.actionSaveProject(), "Save Map")
        self.toolbar.addSeparator()
        for action, label in (
                (self.iface.actionPan(), "Move Map"),
                (self.iface.actionZoomIn(), "Zoom In"),
                (self.iface.actionZoomOut(), "Zoom Out"),
                (self.iface.actionZoomFullExtent(), "Whole Map")):
            self._add_button(action, label)
        self.simple_view = SimpleView(self.iface, self.toolbar)
        options = QAction(ui_icon("name"), "New Project with Options…", self.iface.mainWindow())
        options.triggered.connect(self.farms.new_with_options)
        self.iface.addPluginToMenu(self.menu, options)
        self.farm_actions.append((options, self.farms.new_with_options))
        update_action = QAction(icon, 'Check for Updates…', self.iface.mainWindow())
        update_action.triggered.connect(self.check_updates)
        self.iface.addPluginToMenu(self.menu, update_action)
        self.farm_actions.append((update_action, self.check_updates))
        self.farms.attach()
        self.browser = FarmBrowser(self.iface)

    def _add_button(self, action, label):
        # Reuse the native QAction without changing its labels elsewhere in QGIS.
        button = FarmToolButton(action, label, self.toolbar)
        self.toolbar.addWidget(button)

    def check_updates(self):
        run_updates(self.iface)

    def run(self):
        layer_count = len(QgsProject.instance().mapLayers())
        self.iface.messageBar().pushMessage(
            "Ag-GIS",
            f"Starter plugin is running. Project layers: {layer_count}.",
            level=Qgis.Info,
            duration=5,
        )

    def unload(self):
        if self.action is None:
            return
        self.farms.detach()
        if self.browser is not None:
            self.browser.close()
            self.browser = None
        self.imports.close()
        if self.simple_view is not None:
            self.simple_view.close()
            self.simple_view = None
        for action, callback in self.farm_actions:
            self.iface.removePluginMenu(self.menu, action)
            action.triggered.disconnect(callback)
            action.deleteLater()
        self.farm_actions.clear()
        self.iface.removePluginMenu(self.menu, self.action)
        self.iface.mainWindow().removeToolBar(self.toolbar)
        self.toolbar.hide()
        self.toolbar.deleteLater()
        self.toolbar = None
        self.action.triggered.disconnect(self.run)
        self.action.deleteLater()
        self.action = None
