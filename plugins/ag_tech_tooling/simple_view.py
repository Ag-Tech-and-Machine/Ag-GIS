# SPDX-License-Identifier: GPL-2.0-or-later
"""A reversible, profile-specific switch for reducing QGIS interface clutter."""
from qgis.PyQt.QtCore import QByteArray, Qt, QTimer
from qgis.PyQt.QtWidgets import QCheckBox, QDockWidget, QToolBar, QWidget, QHBoxLayout
from qgis.core import QgsSettings


class SimpleView:
    ENABLED_KEY = "AgTechTooling/simple_view/enabled"
    STATE_KEY = "AgTechTooling/simple_view/full_layout"

    def __init__(self, iface):
        self.iface = iface
        self.window = iface.mainWindow()
        self.settings = QgsSettings()
        self.saved_state = None
        self.closed = False
        self.container = QWidget(self.window)
        self.container.setObjectName("ag_tech_tooling_simple_view_control")
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 0, 10, 0)
        self.switch = QCheckBox("Simple view", self.container)
        self.switch.setObjectName("ag_tech_tooling_simple_view_switch")
        self.switch.setAccessibleName("Simple view")
        self.switch.setToolTip("Show basic map controls. Turn off to restore your previous QGIS layout.")
        layout.addWidget(self.switch)
        self.window.statusBar().addPermanentWidget(self.container)
        self.switch.toggled.connect(self.set_enabled)
        if self.settings.value(self.ENABLED_KEY, False, type=bool):
            QTimer.singleShot(0, self._apply_saved_preference)

    def _apply_saved_preference(self):
        if not self.closed:
            self.switch.setChecked(True)

    def managed_toolbars(self):
        return [bar for bar in self.window.findChildren(QToolBar)
                if self.window.toolBarArea(bar) != Qt.NoToolBarArea]

    def managed_docks(self):
        return [dock for dock in self.window.findChildren(QDockWidget)
                if self.window.dockWidgetArea(dock) != Qt.NoDockWidgetArea]

    def set_enabled(self, enabled):
        if self.closed:
            return
        if enabled:
            if self.saved_state is None:
                previous = self.settings.value(self.STATE_KEY, QByteArray(), type=QByteArray)
                self.saved_state = previous if previous else self.window.saveState()
                self.settings.setValue(self.STATE_KEY, self.saved_state)
            essential = {self.iface.fileToolBar(), self.iface.mapNavToolToolBar()}
            for toolbar in self.managed_toolbars():
                toolbar.setVisible(toolbar in essential)
            for dock in self.managed_docks():
                dock.setVisible(dock.objectName() in {"Layers", "Browser"})
        elif self.saved_state is not None:
            if not self.window.restoreState(self.saved_state):
                raise RuntimeError("QGIS could not restore the saved full layout")
            self.saved_state = None
            self.settings.remove(self.STATE_KEY)
        self.settings.setValue(self.ENABLED_KEY, bool(enabled))
        self.settings.sync()

    def close(self):
        if self.closed:
            return
        # Restore the UI on plugin disable/reload; retain the user's mode preference
        # and full-layout snapshot so a restart cannot snapshot a simplified UI.
        if self.saved_state is not None:
            self.window.restoreState(self.saved_state)
        self.closed = True
        self.switch.toggled.disconnect(self.set_enabled)
        self.window.statusBar().removeWidget(self.container)
        self.container.hide()
        self.container.deleteLater()
