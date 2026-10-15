# SPDX-License-Identifier: GPL-2.0-or-later
"""A reversible, profile-specific switch for reducing QGIS interface clutter."""
from qgis.PyQt.QtCore import QByteArray, Qt, QTimer, QObject, QEvent
from qgis.PyQt.QtWidgets import QCheckBox, QDockWidget, QToolBar, QWidget, QHBoxLayout, QStackedWidget
from qgis.core import QgsSettings, QgsProject
from .ui_icons import icon


class SimpleView(QObject):
    ENABLED_KEY = "AgTechTooling/simple_view/enabled"
    STATE_KEY = "AgTechTooling/simple_view/full_layout"

    def __init__(self, iface, primary_toolbar=None):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.window = iface.mainWindow()
        self.primary_toolbar = primary_toolbar
        self.settings = QgsSettings()
        self.saved_state = None
        self.closed = False
        self.tracked_docks = {}
        self.tracked_toolbars = {}
        self.map_stack, self.map_page = self._find_map_page()
        self.previous_page = None
        self.project_before = None
        self.container = QWidget(self.window)
        self.container.setObjectName("ag_tech_tooling_simple_view_control")
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 0, 10, 0)
        self.switch = QCheckBox("Simple view", self.container)
        self.switch.setObjectName("ag_tech_tooling_simple_view_switch")
        self.switch.setAccessibleName("Simple view")
        self.switch.setIcon(icon("whole"))
        self.switch.setToolTip("Show only the map and Layers. Turn off to restore your previous QGIS layout.")
        layout.addWidget(self.switch)
        self.window.statusBar().addPermanentWidget(self.container)
        self.switch.toggled.connect(self.set_enabled)
        self.window.installEventFilter(self)
        self._register_docks()
        self._register_toolbars()
        if self.map_stack is not None:
            self.map_stack.currentChanged.connect(self._ensure_map_page)
        if self.settings.value(self.ENABLED_KEY, False, type=bool):
            QTimer.singleShot(0, self._apply_saved_preference)

    def _apply_saved_preference(self):
        if not self.closed:
            self.switch.setChecked(True)

    def managed_toolbars(self):
        return [bar for bar in self.window.findChildren(QToolBar)
                if self.window.toolBarArea(bar) != Qt.NoToolBarArea]

    def _essential_toolbars(self):
        return ({self.primary_toolbar} if self.primary_toolbar is not None
                else {self.iface.fileToolBar(), self.iface.mapNavToolToolBar()})

    def _register_toolbars(self):
        if self.closed:
            return
        for toolbar in self.managed_toolbars():
            if toolbar not in self.tracked_toolbars:
                callback = lambda visible, bar=toolbar: self._guard_toolbar(bar, visible)
                toolbar.visibilityChanged.connect(callback)
                self.tracked_toolbars[toolbar] = callback
            if self.switch.isChecked():
                self._guard_toolbar(toolbar)

    def _guard_toolbar(self, toolbar, visible=None):
        if self.closed or not self.switch.isChecked():
            return
        essential = toolbar in self._essential_toolbars()
        if essential and toolbar.isHidden():
            toolbar.show()
        elif not essential and not toolbar.isHidden():
            toolbar.hide()

    def managed_docks(self):
        return [dock for dock in self.window.findChildren(QDockWidget)
                if self.window.dockWidgetArea(dock) != Qt.NoDockWidgetArea]

    def _find_map_page(self):
        page = self.iface.mapCanvas()
        parent = page.parentWidget()
        while parent is not None:
            if isinstance(parent, QStackedWidget) and parent.indexOf(page) >= 0:
                return parent, page
            page, parent = parent, parent.parentWidget()
        return None, None

    def _project_signature(self):
        project = QgsProject.instance()
        return project.fileName(), tuple(sorted(project.mapLayers())), project.isDirty()

    def _register_docks(self):
        if self.closed:
            return
        for dock in self.managed_docks():
            if dock not in self.tracked_docks:
                callback = lambda visible, panel=dock: self._guard_dock(panel, visible)
                dock.visibilityChanged.connect(callback)
                self.tracked_docks[dock] = callback
            if self.switch.isChecked() and dock.objectName() != "Layers":
                dock.hide()

    def _guard_dock(self, dock, visible):
        if self.closed or not self.switch.isChecked():
            return
        if dock.objectName() == "Layers":
            if dock.isHidden():
                dock.show()
        elif not dock.isHidden():
            dock.hide()

    def eventFilter(self, watched, event):
        if not self.closed and event.type() == QEvent.ChildAdded:
            QTimer.singleShot(0, self._register_docks)
            QTimer.singleShot(0, self._register_toolbars)
        return False

    def _ensure_map_page(self, index=None):
        if not self.closed and self.switch.isChecked() and self.map_stack is not None:
            if self.map_stack.currentWidget() is not self.map_page:
                self.map_stack.setCurrentWidget(self.map_page)

    def _restore_page(self):
        if self.map_stack is not None and self.previous_page is not None:
            # Do not return to an old welcome page after the user has opened or
            # changed a project while using Simple view.
            if self._project_signature() == self.project_before:
                try:
                    if self.map_stack.indexOf(self.previous_page) >= 0:
                        self.map_stack.setCurrentWidget(self.previous_page)
                except RuntimeError:
                    pass
        self.previous_page = None

    def set_enabled(self, enabled):
        if self.closed:
            return
        if enabled:
            if self.saved_state is None:
                previous = self.settings.value(self.STATE_KEY, QByteArray(), type=QByteArray)
                self.saved_state = previous if previous else self.window.saveState()
                self.settings.setValue(self.STATE_KEY, self.saved_state)
                if self.map_stack is not None:
                    self.previous_page = self.map_stack.currentWidget()
                    self.project_before = self._project_signature()
            essential = self._essential_toolbars()
            for toolbar in self.managed_toolbars():
                toolbar.setVisible(toolbar in essential)
            for dock in self.managed_docks():
                dock.setVisible(dock.objectName() == "Layers")
                if dock.objectName() == "Layers":
                    dock.raise_()
            self._ensure_map_page()
            self._register_docks()
            self._register_toolbars()
        elif self.saved_state is not None:
            if not self.window.restoreState(self.saved_state):
                raise RuntimeError("QGIS could not restore the saved full layout")
            self.saved_state = None
            self.settings.remove(self.STATE_KEY)
            self._restore_page()
        self.settings.setValue(self.ENABLED_KEY, bool(enabled))
        self.settings.sync()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.window.removeEventFilter(self)
        if self.map_stack is not None:
            self.map_stack.currentChanged.disconnect(self._ensure_map_page)
        for dock, callback in self.tracked_docks.items():
            try:
                dock.visibilityChanged.disconnect(callback)
            except (RuntimeError, TypeError):
                pass
        self.tracked_docks.clear()
        for toolbar, callback in self.tracked_toolbars.items():
            try:
                toolbar.visibilityChanged.disconnect(callback)
            except (RuntimeError, TypeError):
                pass
        self.tracked_toolbars.clear()
        # Restore the UI on plugin disable/reload; retain the user's mode preference
        # and full-layout snapshot so a restart cannot snapshot a simplified UI.
        if self.saved_state is not None:
            self.window.restoreState(self.saved_state)
        self._restore_page()
        self.switch.toggled.disconnect(self.set_enabled)
        self.window.statusBar().removeWidget(self.container)
        self.container.hide()
        self.container.deleteLater()
        self.deleteLater()
