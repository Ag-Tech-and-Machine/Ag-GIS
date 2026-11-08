# SPDX-License-Identifier: GPL-2.0-or-later
"""Farm-specific presentation on the existing native QGIS Layers view."""
from html import escape
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
import hashlib
from qgis.PyQt.QtCore import QSize, QObject, QEvent, QTimer, Qt
from qgis.PyQt.QtWidgets import (QAction, QDockWidget, QStyle, QStyledItemDelegate, QStyleOptionViewItem,
    QToolTip, QToolBar, QToolButton, QMenu, QDialog, QMessageBox)
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject, QgsVectorLayer
from .ui_icons import icon
from .view_settings import preference


KINDS = {
    "workspace": ("folder", "Farm Data"),
    "organisation": ("organisation", "Organisation"),
    "client": ("client", "Client"),
    "farm": ("farm", "Farm"),
    "field": ("field", "Field"),
    "whole": ("whole", "Whole Field"),
    "seasons": ("season", "Seasons"),
    "season": ("season", "Season"),
    "crop": ("crop", "Crop"),
    "plans": ("plan", "Plans"),
    "operations": ("job", "Operations"),
    "results": ("result", "Results"),
}


class FarmTreeDelegate(QStyledItemDelegate):
    """Decorate managed groups; forward native layer/legend/editor behaviour."""

    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.native = view.itemDelegate()
        self.connections = ((self.native.commitData, self.commitData.emit),
                            (self.native.closeEditor, self.closeEditor.emit),
                            (self.native.sizeHintChanged, self.sizeHintChanged.emit))
        for signal, callback in self.connections:
            signal.connect(callback)

    def kind(self, index):
        node = self.view.index2node(index)
        if not isinstance(node, QgsLayerTreeGroup):
            return None
        kind = node.customProperty("AgTechTooling/kind", "")
        if not kind and node.customProperty("AgTechTooling/workspace", ""):
            kind = "workspace"
        return kind if isinstance(kind, str) and kind in KINDS else None

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        kind = self.kind(index)
        if kind:
            option.icon = icon(KINDS[kind][0])
            option.decorationSize = QSize(20, 20)
            if kind in {"workspace", "organisation"}:
                option.font.setBold(True)

    def paint(self, painter, option, index):
        if not self.kind(index):
            return self.native.paint(painter, option, index)
        decorated = QStyleOptionViewItem(option)
        self.initStyleOption(decorated, index)
        style = decorated.widget.style() if decorated.widget else self.view.style()
        style.drawControl(QStyle.CE_ItemViewItem, decorated, painter, decorated.widget)

    def sizeHint(self, option, index):
        size = self.native.sizeHint(option, index)
        return QSize(size.width(), max(26, size.height())) if self.kind(index) else size

    def helpEvent(self, event, view, option, index):
        kind = self.kind(index)
        if not kind:
            node = self.view.index2node(index)
            if isinstance(node, QgsLayerTreeLayer) and node.layer().customProperty("AgTechTooling/original_name"):
                QToolTip.showText(event.globalPos(), escape(node.layer().customProperty("AgTechTooling/original_name")), view)
                return True
            return self.native.helpEvent(event, view, option, index)
        node = self.view.index2node(index)
        QToolTip.showText(event.globalPos(), f"<b>{KINDS[kind][1]}</b><br>{escape(node.name())}", view)
        return True

    def editorEvent(self, event, model, option, index):
        return self.native.editorEvent(event, model, option, index)

    def createEditor(self, parent, option, index):
        return self.native.createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        self.native.setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        node = self.view.index2node(index)
        kind = self.kind(index)
        from . import hierarchy as store
        if kind in store.ENTITIES:
            try:
                root = workspace_root()
                identity = node.customProperty("AgTechTooling/node").split(":", 1)[1]
                editor.setText(store.text(editor.text()))
                store.rename_record(root, kind, identity, editor.text())
            except (ValueError, RuntimeError, OSError, sqlite3.Error) as error:
                QMessageBox.warning(self.view, "Could not rename", str(error))
                return
        elif kind:
            return  # Fixed structural headings do not rename the underlying data.
        elif isinstance(node, QgsLayerTreeLayer) and node.layer().customProperty("AgTechTooling/dataset_id"):
            try:
                from .map_presentation import rename_dataset
                editor.setText(store.text(editor.text()))
                rename_dataset(workspace_root(), node.layer().customProperty("AgTechTooling/dataset_id"), editor.text())
            except (ValueError, RuntimeError, OSError, sqlite3.Error) as error:
                QMessageBox.warning(self.view, "Could not rename dataset", str(error))
                return
        self.native.setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        self.native.updateEditorGeometry(editor, option, index)

    def destroyEditor(self, editor, index):
        self.native.destroyEditor(editor, index)

    def close(self):
        for signal, callback in self.connections:
            signal.disconnect(callback)


class FarmBrowser(QObject):
    """Install and fully restore the presentation without replacing the model."""

    def __init__(self, iface):
        super().__init__()
        self.closed = False
        self.iface = iface
        self.buttons = []
        self.selection_busy = False
        self.restoring = False
        self.selection_generation = 0
        self.visibility_pending = False
        self.read_expansion = []
        self.contents = None
        self.view = iface.layerTreeView() if hasattr(iface, "layerTreeView") else None
        self.delegate = None
        self.dock = None
        self._saved_styles = None  # Track SavedStyles instance
        if self.view is None:
            return
        self.indentation = self.view.indentation()
        self.icon_size = self.view.iconSize()
        self.delegate = FarmTreeDelegate(self.view)
        self.view.setItemDelegate(self.delegate)
        self.view.setIndentation(14)
        self.view.setIconSize(QSize(20, 20))
        parent = self.view.parentWidget()
        while parent is not None and not isinstance(parent, QDockWidget):
            parent = parent.parentWidget()
        self.dock = parent
        if self.dock is not None:
            self.contents = self.dock.widget()
            self.contents.installEventFilter(self)
            self._fit_contents()
        self.dock_title = self.dock.windowTitle() if self.dock else ""
        QgsProject.instance().readProject.connect(self.refresh_title)
        QgsProject.instance().cleared.connect(self.refresh_title)
        QgsProject.instance().layersAdded.connect(self.layers_added)
        QgsProject.instance().aboutToBeCleared.connect(self.begin_restore)
        QgsProject.instance().readProject.connect(self.capture_read_expansion)
        # The desktop emits projectRead after its native current-layer restore.
        # Standalone native-view tests have only the project read signal.
        self.read_finished = getattr(iface, "projectRead", QgsProject.instance().readProject)
        self.read_finished.connect(self.project_read)
        self.view.selectionModel().currentChanged.connect(self.selection_changed)
        # A name click on the current row does not emit currentChanged.
        self.view.clicked.connect(self.selection_changed)
        QgsProject.instance().layerTreeRoot().visibilityChanged.connect(self.visibility_changed)
        self.install_controls()
        self.refresh_title()

    def install_controls(self):
        if self.contents is None:
            return
        toolbar = self.contents.findChild(QToolBar)
        if toolbar is None:
            return
        self.add_menu = QMenu(self.view)
        from . import hierarchy as store
        self.add_actions = {}
        for kind in store.ENTITIES:
            action = self.add_menu.addAction(icon(kind), "Add " + kind.title() + "…")
            action.triggered.connect(lambda checked=False, entity=kind: self.add_entity(entity))
            self.add_actions[kind] = action
        add = QToolButton(toolbar)
        add.setIcon(icon("add"))
        add.setText("Add farm item")
        add.setToolTip("Add an organisation, client, farm, field, season or crop")
        add.setPopupMode(QToolButton.InstantPopup)
        add.setMenu(self.add_menu)
        self.buttons.append((toolbar, toolbar.addWidget(add), add))
        rename = QToolButton(toolbar)
        rename.setIcon(icon("edit"))
        rename.setText("Rename")
        rename.setToolTip("Rename the selected farm item or dataset")
        rename.clicked.connect(self.rename_selected)
        self.rename_button = rename
        self.buttons.append((toolbar, toolbar.addWidget(rename), rename))
        # Let QToolBar own an ordinary QAction: custom addWidget controls have
        # no usable representation in its native extension popup at narrow widths.
        style_action = QAction(icon("style"), "Edit Style…", toolbar)
        style_action.setToolTip("Open Layer Properties to edit or save style")
        style_action.triggered.connect(self.edit_style)
        style_menu = QMenu(toolbar)
        # The extension presents an action with a menu as a submenu. Include the
        # primary command there too, rather than losing editing to Reset/Save.
        edit = style_menu.addAction(icon("style"), "Edit Style…")
        edit.triggered.connect(self.edit_style)
        style_menu.addSeparator()
        reset = style_menu.addAction("Reset to Classification Style…")
        reset.triggered.connect(lambda checked=False: self._style_action(self._reset_style))
        save = style_menu.addAction("Save Style…")
        save.triggered.connect(lambda checked=False: self._style_action(self._save_style))
        style_action.setMenu(style_menu)
        toolbar.addAction(style_action)
        style = toolbar.widgetForAction(style_action)
        style_menu.setParent(style, style_menu.windowFlags())
        style.setPopupMode(QToolButton.MenuButtonPopup)
        self.buttons.append((toolbar, style_action, style))
        self.update_controls()

    def ancestor(self, kind):
        node = self.view.currentNode()
        while node is not None:
            if node.customProperty("AgTechTooling/kind", "") == kind:
                return node
            node = node.parent()
        return None

    def update_controls(self):
        if not self.buttons:
            return
        from . import hierarchy as store
        farm = QgsProject.instance().readNumEntry("AgTechTooling", "schema_version")[0] == 2
        for kind, action in self.add_actions.items():
            parent_kind = store.ENTITIES[kind][1]
            action.setEnabled(farm and (not parent_kind or self.ancestor(parent_kind) is not None))
        node = self.view.currentNode()
        kind = node.customProperty("AgTechTooling/kind", "") if node else ""
        self.rename_button.setEnabled(farm and (kind in store.ENTITIES or isinstance(node, QgsLayerTreeLayer)))

    def add_entity(self, kind):
        from . import hierarchy as store
        from .hierarchy_dialog import NameDialog, sync_tree
        try:
            root = workspace_root()
            parent_kind = store.ENTITIES[kind][1]
            parent = self.ancestor(parent_kind) if parent_kind else None
            parent_id = parent.customProperty("AgTechTooling/node").split(":", 1)[1] if parent else None
            if parent_kind and not parent_id:
                raise ValueError("Select a " + parent_kind + " first.")
            dialog = NameDialog(kind, self.view)
            if dialog.exec() != QDialog.Accepted:
                return
            identity = store.add_record(root, kind, dialog.name.text(), parent_id,
                                        start=dialog.start.text().strip(), end=dialog.end.text().strip())
            _, nodes = sync_tree(root)
            self.view.setCurrentNode(nodes[identity])
            self.focus_node(nodes[identity])
            QgsProject.instance().setDirty(True)
        except (ValueError, RuntimeError, OSError, sqlite3.Error) as error:
            QMessageBox.warning(self.view, "Could not add " + kind, str(error))

    def rename_selected(self):
        node = self.view.currentNode()
        if node:
            self.view.edit(self.view.node2index(node))

    def edit_style(self):
        """Open native Layer Properties at Symbology for the selected vector."""
        self._style_action(self._open_style_dialog)

    def _style_action(self, action):
        """Resolve selection at activation time for all existing style controls."""
        node = self.view.currentNode()
        if not node:
            return
        if not isinstance(node, QgsLayerTreeLayer):
            return
        layer = node.layer()
        if not layer:
            return
        # Check if it's a vector layer that can have symbology
        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.information(self.view, "Style", "Symbology editing is only available for vector layers.", QMessageBox.Ok)
            return
        action(layer)

    def _open_style_dialog(self, layer):
        """Run QGIS's modal properties dialog; its return is not a widget."""
        self.iface.showLayerProperties(layer, "mOptsPage_Style")

    def _reset_style(self, layer):
        """Reset layer style to classification-based style."""
        from . import operation_style
        if operation_style.apply_operation_style(layer, reset=True):
            layer.triggerRepaint()
            QMessageBox.information(self.view, "Style Reset", "Layer style has been reset to classification-based style.", QMessageBox.Ok)
        else:
            QMessageBox.warning(self.view, "Style Reset", "Could not apply classification-based style. Check that the layer has a valid operation classification.", QMessageBox.Ok)

    def _save_style(self, layer):
        """Save current layer style to the style catalogue via SavedStyles."""
        from . import dataset_styles
        from qgis.core import QgsVectorLayer
        
        # Verify this is a vector layer with symbology
        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.warning(self.view, "Save Style", "Can only save styles for vector layers.", QMessageBox.Ok)
            return
        
        # Get dataset_id from layer custom properties
        dataset_id = layer.customProperty("AgTechTooling/dataset_id")
        if not dataset_id:
            QMessageBox.warning(self.view, "Save Style", "This layer is not associated with a dataset. Styles can only be saved for known datasets.", QMessageBox.Ok)
            return
        
        # Check if dataset exists in catalogue
        try:
            from .managed_data import records
            root = None
            project = QgsProject.instance()
            project_path = project.fileName()
            if project.fileName() and Path(project.fileName()).name == 'Farm.qgz':
                root = Path(project.fileName()).resolve().parent
            
            if root is None:
                QMessageBox.warning(self.view, "Save Style", "Could not determine workspace. Ensure you have Farm.qgz open.", QMessageBox.Ok)
                return
            
            catalogue = {row['id']: row for row in records(root)}
            if dataset_id not in catalogue:
                QMessageBox.warning(self.view, "Save Style", "Dataset not found in catalogue. Cannot save style.", QMessageBox.Ok)
                return
        except Exception as error:
            QMessageBox.critical(self.view, "Save Style Error", f"Could not check dataset: {str(error)}")
            return
        
        # Initialize SavedStyles to ensure it's observing the project
        # This will capture the layer's style when the project is saved
        if self._saved_styles is None:
            try:
                self._saved_styles = dataset_styles.SavedStyles(
                    warning=lambda msg: QMessageBox.critical(self.view, "Save Style Error", msg),
                    project=QgsProject.instance()
                )
            except Exception as error:
                QMessageBox.critical(self.view, "Save Style Error", f"Could not initialize style save: {str(error)}")
                return
        
        # Clear any previous save pending marker
        layer.setCustomProperty("AgTechTooling/save_style_pending", dataset_id)
        
        # Trigger project write to capture the style
        QMessageBox.information(self.view, "Save Style", "Layer style will be saved when project is saved. Please save the project.", QMessageBox.Ok)

    def layers_added(self, *args):
        QTimer.singleShot(0, self.refresh_presentation)

    def refresh_presentation(self):
        if self.closed:
            return
        from .map_presentation import prepare_layer
        project = QgsProject.instance()
        if project.readNumEntry("AgTechTooling", "schema_version")[0] != 2:
            self.update_controls()
            return
        for layer in project.mapLayers().values():
            prepare_layer(layer, project)
        # Presentation refresh is not a navigation gesture. Native tree expansion
        # (including deliberately collapsed branches) is already project state.
        self.update_controls()

    def focus_node(self, node):
        if not preference("focus"):
            return
        chain = []
        parent = node
        while parent is not None:
            chain.append(parent)
            parent = parent.parent()
        if not any(n.customProperty("AgTechTooling/kind", "") for n in chain):
            return
        # Never collapse siblings: several fields may be open for comparison.
        for parent in chain:
            if not parent.isExpanded():
                parent.setExpanded(True)
        # Reveal the choices at the first fork, without choosing one or changing
        # selection/visibility. Layer leaves retain their native legend behaviour.
        current = node
        while isinstance(current, QgsLayerTreeGroup):
            current.setExpanded(True)
            children = current.children()
            if len(children) != 1:
                break
            current = children[0]
        self.view.scrollTo(self.view.node2index(node))

    def begin_restore(self):
        self.restoring = True
        self.selection_generation += 1
        self.read_expansion = []

    def capture_read_expansion(self, *args):
        project = QgsProject.instance()
        if project.readNumEntry("AgTechTooling", "schema_version")[0] == 2:
            root = project.layerTreeRoot()
            # Capture native deserialized state before QgisApp selects its first
            # layer (which scrolls open collapsed parents). No new persistence.
            self.read_expansion = [(node, node.isExpanded()) for node in
                                   root.findGroups(True) + root.findLayers()]

    def project_read(self, *args):
        generation = self.selection_generation
        QTimer.singleShot(0, lambda: self.end_restore()
                          if generation == self.selection_generation else None)
        # Rebuild the layer tree hierarchy after project load (Issue #3 fix)
        try:
            from . import hierarchy_dialog
            root = workspace_root()
            hierarchy_dialog.refresh_tree(root)
        except Exception:
            # If workspace is not ready, ignore - will be called on next interaction
            pass

    def end_restore(self):
        if not self.closed:
            from qgis.PyQt import sip
            for node, expanded in self.read_expansion:
                if not sip.isdeleted(node):
                    node.setExpanded(expanded)
            self.read_expansion = []
            self.restoring = False
            self.update_controls()

    def visibility_changed(self, *args):
        if self.closed or self.restoring:
            return
        # A native checkbox gesture may also emit clicked/currentChanged. Cancel
        # its queued navigation, but leave ordinary subsequent name clicks alone.
        self.selection_generation += 1
        if not self.visibility_pending:
            self.visibility_pending = True
            QTimer.singleShot(0, self.finish_visibility_change)

    def finish_visibility_change(self):
        self.visibility_pending = False
        if self.closed or self.restoring:
            return
        from .managed_data import sync_reference_visibility
        try:
            sync_reference_visibility()
        except ValueError as error:
            if hasattr(self.iface, "messageBar"):
                self.iface.messageBar().pushMessage("Field visibility", str(error), duration=8)

    def selection_changed(self, *args):
        # Complete the native click/checkbox/editor event before moving rows.
        if self.restoring or self.visibility_pending:
            return
        generation = self.selection_generation
        QTimer.singleShot(0, lambda: self.apply_selection()
                          if generation == self.selection_generation else None)

    def apply_selection(self):
        if self.closed or self.selection_busy or self.restoring:
            return
        self.update_controls()
        node = self.view.currentNode()
        if node is None:
            return
        self.focus_node(node)
        if not preference("zoom") or not hasattr(self.iface, "mapCanvas"):
            return
        from .map_presentation import zoom_layers
        self.selection_busy = True
        try:
            if isinstance(node, QgsLayerTreeLayer):
                layer = node.layer()
                # Navigation must never enable a layer or replace a deliberate
                # Filter Data choice. Only zoom an already-visible layer.
                if layer and node.isVisible() and not layer.customProperty("AgTechTooling/background"):
                    if hasattr(self.iface, "setActiveLayer"):
                        self.iface.setActiveLayer(layer)
                    zoom_layers(self.iface, [layer])
            elif node.customProperty("AgTechTooling/kind", "") == "field":
                field_id = node.customProperty("AgTechTooling/field", "")
                layers = [n.layer() for n in node.findLayers() if n.layer() and not n.customProperty("AgTechTooling/filter_hidden", False)]
                if not zoom_layers(self.iface, layers) and hasattr(self.iface, "messageBar"):
                    self.iface.messageBar().pushMessage("Field", "This field has no mapped data yet. Import data or add a boundary to locate it.", duration=5)
        finally:
            self.selection_busy = False

    def eventFilter(self, watched, event):
        if not self.closed and watched is self.contents and event.type() == QEvent.Paint:
            # Native dock restoration can overwrite geometry after queued resize
            # callbacks. Repair a stale rectangle before drawing the contents.
            self._fit_contents()
        if not self.closed and watched is self.contents and event.type() in {QEvent.Resize, QEvent.Show}:
            # A restored/maximised dock can retain its earlier child geometry.
            # Let Qt finish the dock resize, then relayout the existing native
            # toolbar and tree together, without changing their ownership.
            QTimer.singleShot(0, self._fit_contents)
        return False

    def _fit_contents(self):
        if self.closed or self.contents is None:
            return
        layout = self.contents.layout()
        if layout is not None and layout.geometry() != self.contents.contentsRect():
            layout.invalidate()
            layout.setGeometry(self.contents.contentsRect())

    def refresh_title(self, *args):
        if self.dock is not None:
            farm = QgsProject.instance().readNumEntry("AgTechTooling", "schema_version")[0] == 2
            self.dock.setWindowTitle("Farm Data" if farm else self.dock_title)
        QTimer.singleShot(0, self.refresh_presentation)

    def close(self):
        self.closed = True
        if self.contents is not None:
            self.contents.removeEventFilter(self)
        if self.delegate is None:
            return
        if self.view.itemDelegate() is self.delegate:
            self.view.setItemDelegate(self.delegate.native)
        self.view.setIndentation(self.indentation)
        self.view.setIconSize(self.icon_size)
        QgsProject.instance().readProject.disconnect(self.refresh_title)
        QgsProject.instance().cleared.disconnect(self.refresh_title)
        QgsProject.instance().layersAdded.disconnect(self.layers_added)
        QgsProject.instance().aboutToBeCleared.disconnect(self.begin_restore)
        QgsProject.instance().readProject.disconnect(self.capture_read_expansion)
        self.read_finished.disconnect(self.project_read)
        self.view.selectionModel().currentChanged.disconnect(self.selection_changed)
        self.view.clicked.disconnect(self.selection_changed)
        QgsProject.instance().layerTreeRoot().visibilityChanged.disconnect(self.visibility_changed)
        for toolbar, action, button in self.buttons:
            toolbar.removeAction(action)
            button.deleteLater()
            action.deleteLater()
        self.buttons.clear()
        if hasattr(self, "add_menu"):
            self.add_menu.deleteLater()
        if self.dock is not None:
            self.dock.setWindowTitle(self.dock_title)
        self.delegate.close()
        self.delegate.deleteLater()
        self.delegate = None
        # Clean up SavedStyles instance
        if self._saved_styles is not None:
            self._saved_styles.close()
            self._saved_styles = None

def workspace_root():
    from .import_placement import workspace
    return workspace()
