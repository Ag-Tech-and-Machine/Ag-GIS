# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

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

    from .branding import Branding

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtSvg import QSvgWidget
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this module

from .simple_view import SimpleView

from .farm_dialog import FarmActions

from .ui_icons import icon as ui_icon

from .farm_browser import FarmBrowser

from .import_dialog import ImportActions

from .data_filter import FilterActions

from .updates import UpdateActions

from .feedback import FeedbackActions

from .background_maps import BackgroundMaps

from .view_settings import ViewSettingsDialog





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

        self.filters = FilterActions(iface)

        self.feedback = FeedbackActions(iface)

        self.toolbar = None

        self.browser = None

        self.backgrounds = None

        self.branding = None

        self.updates = None

        self.github = None



    def initGui(self):

        if self.action is not None:

            return

        self.branding = Branding(self.iface.mainWindow())

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

        brand = QSvgWidget(str(Path(__file__).with_name("brand_lockup.svg")), self.toolbar)

        brand.setFixedSize(165, 48)

        brand.setAccessibleName("Ag-GIS — Farming in view")

        brand.setToolTip("Ag-GIS — built on open source tools. About Ag-GIS is in the Plugins menu.")

        self.toolbar.addWidget(brand)

        about = QAction(icon, "About Ag-GIS…", self.iface.mainWindow())

        about.triggered.connect(self.branding.about)

        self.iface.addPluginToMenu(self.menu, about)

        self.farm_actions.append((about, self.branding.about))

        for title, label, action_icon, callback in (

                ("New Project…", "New Project", self.iface.actionNewProject().icon(), self.farms.new),

                ("Open Project…", "Open Project", self.iface.actionOpenProject().icon(), self.farms.open),

                ("Manage Farm Data…", "Manage Data", ui_icon("organisation"), self.farms.manage),

                ("Data In…", "Data In", ui_icon("import"), self.imports.open),

                ("Filter Data…", "Filter Data", ui_icon("filter"), self.filters.open)):

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

                (self.iface.actionZoomOut(), "Zoom Out")):

            self._add_button(action, label)

        whole = QAction(self.iface.actionZoomFullExtent().icon(), "Whole Map", self.iface.mainWindow())

        whole.triggered.connect(self.whole_map)

        self.iface.addPluginToMenu(self.menu, whole)

        self.farm_actions.append((whole, self.whole_map))

        self._add_button(whole, "Whole Map")

        self.simple_view = SimpleView(self.iface, self.toolbar)

        options = QAction(ui_icon("name"), "New Project with Options…", self.iface.mainWindow())

        options.triggered.connect(self.farms.new_with_options)

        self.iface.addPluginToMenu(self.menu, options)

        self.farm_actions.append((options, self.farms.new_with_options))

        update_action = QAction(icon, 'Check for Updates…', self.iface.mainWindow())

        update_action.triggered.connect(self.check_updates)

        self.iface.addPluginToMenu(self.menu, update_action)

        self.farm_actions.append((update_action, self.check_updates))

        feedback_action = QAction(QIcon.fromTheme("help-about", icon), "Feedback and Help…", self.iface.mainWindow())

        feedback_action.triggered.connect(self.feedback.open)

        self.iface.addPluginToMenu(self.menu, feedback_action)

        self.farm_actions.append((feedback_action, self.feedback.open))

        self.toolbar.addSeparator()

        self._add_button(feedback_action, "Feedback")

        self.farms.attach()

        self.browser = FarmBrowser(self.iface)

        self.backgrounds = BackgroundMaps(self.iface)

        settings = QAction(ui_icon("settings"), "Map & Browser Settings…", self.iface.mainWindow())

        settings.triggered.connect(self.view_settings)

        self.iface.addPluginToMenu(self.menu, settings)

        self.farm_actions.append((settings, self.view_settings))

        self._add_button(settings, "View Settings")

        self.updates = UpdateActions(self.iface)

        self.updates.start()

        from .github_connection import GitHubConnection

        self.github = GitHubConnection(self.iface.mainWindow())

        github_action = QAction(icon, 'GitHub Connection…', self.iface.mainWindow())

        github_action.triggered.connect(self.github.open)

        self.iface.addPluginToMenu(self.menu, github_action)

        self.farm_actions.append((github_action, self.github.open))



    def view_settings(self):

        dialog = ViewSettingsDialog(self.iface.mainWindow())

        if dialog.exec() == dialog.Accepted:

            from .view_settings import preference

            self.backgrounds.choose(preference("background"))

            if self.browser:

                self.browser.refresh_presentation()



    def whole_map(self):

        from .map_presentation import zoom_layers

        project = QgsProject.instance()

        if project.readNumEntry("AgTechTooling", "schema_version")[0] != 2:

            self.iface.actionZoomFullExtent().trigger()

            return

        layers = [node.layer() for node in project.layerTreeRoot().findLayers()

                  if node.layer() and node.isVisible() and not node.layer().customProperty("AgTechTooling/background")]

        if not zoom_layers(self.iface, layers):

            self.iface.messageBar().pushMessage("Whole Map", "There is no mapped farm data to zoom to yet.", duration=5)



    def _add_button(self, action, label):

        # Reuse the native QAction without changing its labels elsewhere in QGIS.

        button = FarmToolButton(action, label, self.toolbar)

        self.toolbar.addWidget(button)



    def check_updates(self):

        if self.updates is not None:

            self.updates.open()



    def run(self):

        layer_count = len(QgsProject.instance().mapLayers())

        self.iface.messageBar().pushMessage(

            "Ag-GIS",

            f"Farming workflows are ready. Project layers: {layer_count}.",

            level=Qgis.Info,

            duration=5,

        )



    def unload(self):

        if self.action is None:

            return

        self.farms.detach()

        if self.github is not None:

            self.github.close()

            self.github.deleteLater()

            self.github = None

        if self.updates is not None:

            self.updates.close()

            self.updates = None

        if self.backgrounds is not None:

            self.backgrounds.close()

            self.backgrounds = None

        if self.browser is not None:

            self.browser.close()

            self.browser = None

        self.imports.close()

        self.filters.close()

        self.feedback.close()

        if self.simple_view is not None:

            self.simple_view.close()

            self.simple_view = None

        for action, callback in self.farm_actions:

            self.iface.removePluginMenu(self.menu, action)

            action.triggered.disconnect(callback)

            action.deleteLater()

        self.farm_actions.clear()

        if self.branding is not None:

            self.branding.close()

            self.branding = None

        self.iface.removePluginMenu(self.menu, self.action)

        self.iface.mainWindow().removeToolBar(self.toolbar)

        self.toolbar.hide()

        self.toolbar.deleteLater()

        self.toolbar = None

        self.action.triggered.disconnect(self.run)

        self.action.deleteLater()

        self.action = None


