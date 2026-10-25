"""Exercise the starter action with real QGIS/Qt and a small interface adapter."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from importlib.abc import MetaPathFinder


class UnsupportedAuthenticationGuard(MetaPathFinder):
    """Local startup must not load the unsupported plaintext-token prototype."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "ag_tech_tooling.feedback_submission":
            raise AssertionError("Local startup must not import unsupported token authentication")
        return None


sys.meta_path.insert(0, UnsupportedAuthenticationGuard())

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsProject
from qgis.PyQt.QtWidgets import QMainWindow, QApplication, QPushButton
from qgis.PyQt.QtWidgets import QDockWidget, QToolBar, QLabel, QStackedWidget, QWidget
from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QAction, QToolButton
from ag_tech_tooling import classFactory
from ag_tech_tooling import simple_view
from ag_tech_tooling import plugin as plugin_module, updates, feedback


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
update_network = Mock()
update_network.get.side_effect = AssertionError("Default lifecycle must not contact the update service")
plugin_module.UpdateActions = lambda iface: updates.UpdateActions(
    iface, settings=QSettings(str(Path(test_settings.name) / "updates.ini"), QSettings.IniFormat),
    network=update_network, cache_root=Path(test_settings.name) / "cache",
    recovery_root=Path(test_settings.name) / "recovery")
iface = Interface()
iface.window.resize(1600, 900)  # Keep toolbar child visibility separate from overflow.
iface.window.show()
app.processEvents()
plugin = classFactory(iface)
plugin.initGui()
plugin.initGui()
assert hasattr(plugin, "updates"), "Updates must have one lifecycle-owned controller"
update_controller = plugin.updates
assert update_controller is not None
assert hasattr(plugin, 'github') and plugin.github is not None, 'One production GitHub controller must own the dialog lifecycle'
github_controller = plugin.github
github_actions = [a for a in iface.menu_actions if a.text() == 'GitHub Connection…']
assert len(github_actions) == 1
github_actions[0].trigger()
app.processEvents()
assert github_controller.dialog.isVisible() and not github_controller.dialog.connect_button.isEnabled()
assert github_controller._fixture_factory is None and github_controller.flow is None
assert 'ag_tech_tooling.github_transport' not in sys.modules
github_controller.dialog.close()
assert len(iface.menu_actions) == len(plugin.farm_actions) + 1 and not iface.toolbar_actions
assert len({id(action) for action in iface.menu_actions}) == len(iface.menu_actions)
toolbar = plugin.toolbar
assert iface.window.toolBarArea(toolbar) == Qt.TopToolBarArea
assert not toolbar.isMovable() and not toolbar.isFloatable()
buttons = {button.text(): button for button in toolbar.findChildren(QToolButton) if button.defaultAction()}
assert set(buttons) == {"New Project", "Open Project", "Manage Data", "Data In", "Filter Data", "Save Map", "Move Map", "Zoom In", "Zoom Out", "Whole Map", "View Settings", "Feedback"}
with patch.object(feedback.QDesktopServices, "openUrl", return_value=False) as external, patch.object(
        feedback.Path, "home", side_effect=AssertionError("Local feedback must not resolve account files")):
    buttons["Feedback"].click()
    dialog = plugin.feedback.dialog
    assert dialog.isVisible()
    controls = {button.text(): button for button in dialog.findChildren(QPushButton)}
    dialog.tabs.setCurrentIndex(2)
    controls["Copy agent instructions"].click()
    assert QApplication.clipboard().text() == dialog.agent_guide.toPlainText()
    assert "START HERE" in QApplication.clipboard().text()
    dialog.title.setText("Offline synthetic draft")
    dialog.details.setPlainText("A synthetic report kept locally; no farm data.")
    dialog.include_versions.setChecked(False)
    report = dialog.body()
    controls["Copy report"].click()
    assert QApplication.clipboard().text() == report
    draft = Path(test_settings.name) / "offline-report.md"
    with patch.object(feedback.QFileDialog, "getSaveFileName", return_value=("", "")):
        controls["Save report…"].click()
    assert not draft.exists() and dialog.body() == report
    with patch.object(feedback.QFileDialog, "getSaveFileName", return_value=(str(draft), "Report (*.md)")):
        controls["Save report…"].click()
    assert draft.read_text(encoding="utf-8") == report
    external.assert_not_called()  # Local copy/save/cancel are not connected submissions.
    controls["Open GitHub form…"].click()
    assert external.call_count == 1
    assert external.call_args.args[0].host() == "github.com"
    assert "Could not open" in dialog.status.text() and dialog.body() == report
    controls["Close"].click()
    assert not dialog.isVisible()
    buttons["Feedback"].click()
    assert plugin.feedback.dialog is dialog and dialog.body() == report
    assert draft.read_text(encoding="utf-8") == report
    controls["Close"].click()
assert "ag_tech_tooling.feedback_submission" not in sys.modules
buttons["Data In"].click()
assert plugin.imports.dialog.isVisible()
assert plugin.imports.dialog.windowTitle() == "Ag-GIS — Data In"
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
assert buttons["Save Map"].isVisible(), "Native Save Map child must survive toolbar hide/restore"
for _ in range(3):
    toolbar.hide()
    app.processEvents()
    assert toolbar.isVisible() and buttons["Save Map"].isVisible(), "Repeated restoration must preserve native child visibility"
iface.file_bar.show()
iface.nav_bar.show()
app.processEvents()  # Visibility policy runs after native child propagation.
assert iface.file_bar.isHidden() and iface.nav_bar.isHidden(), "Native startup restoration must not reopen toolbars"
late_bar = iface.window.addToolBar("Late plugin toolbar")
late_bar.setObjectName("LatePluginToolbar")
QTest.qWait(20)  # ChildAdded registration and queued visibility policy need event turns.
app.processEvents()
assert late_bar.isHidden(), "New plugin toolbars must be hidden in Simple view"
assert not iface.layers.isHidden() and iface.browser.isHidden()
iface.layers.hide()
app.processEvents()
assert not iface.layers.isHidden(), "Layers must remain available in Simple view"
assert iface.layers.widget().isVisible(), "Native Layers contents must remain visible after dock hide/restore"
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
from ag_tech_tooling.github_session import SessionDeviceFlow
import time
github_controller.flow = SessionDeviceFlow(time.monotonic)
github_controller.flow.start('SYNTHETIC-UNLOAD-CLIENT')
unload_flow = github_controller.flow
github_controller.timer.start()
plugin.unload()
plugin.unload()
assert plugin.github is None and github_controller.closed
assert github_controller.dialog is None and not github_controller.timer.isActive()
assert unload_flow.state == 'cancelled' and unload_flow.access_token() is None
assert plugin.updates is None, "Unload must dispose of the update controller"
assert update_controller.closed and update_controller.dialog is None
assert not update_controller.daily_timer.isActive() and not update_controller.startup_timer.isActive()
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
update_network.get.assert_not_called()
iface.window.close()
app.exitQgis()
test_settings.cleanup()
