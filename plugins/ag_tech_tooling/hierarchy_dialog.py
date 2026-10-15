# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import sqlite3
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)
from qgis.core import QgsDefaultValue, QgsLayerTreeGroup, QgsProject, QgsVectorLayer
from . import hierarchy as store
from .ui_icons import icon, decorate_input, decorate_buttons


class NameDialog(QDialog):
    def __init__(self, kind, parent, value=""):
        super().__init__(parent)
        self.kind, self.renaming = kind, bool(value)
        self.setWindowTitle(("Rename " if value else "Add ") + kind.title())
        self.setWindowIcon(icon(kind))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(value)
        decorate_input(self.name, kind)
        form.addRow(kind.title() + " name", self.name)
        self.start, self.end = QLineEdit(self), QLineEdit(self)
        if kind == "season" and not value:
            for label, control in (("Start date (optional)", self.start), ("End date (optional)", self.end)):
                control.setPlaceholderText("YYYY-MM-DD")
                decorate_input(control, "season")
                form.addRow(label, control)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        decorate_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        try:
            store.text(self.name.text())
            if self.kind == "season" and not self.renaming:
                store.validate_dates(self.start.text().strip(), self.end.text().strip())
        except ValueError as error:
            QMessageBox.warning(self, "Check details", str(error))
            return
        super().accept()


class HierarchyDialog(QDialog):
    def __init__(self, root, iface):
        super().__init__(iface.mainWindow())
        self.root, self.iface = Path(root), iface
        self.setWindowTitle("Manage Farm Data")
        self.setWindowIcon(icon("organisation"))
        self.resize(820, 650)
        layout = QVBoxLayout(self)
        hint = QLabel("Select a parent, then add a client, farm, field, season or crop. Select a field or its data to show it on the map.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        row = QHBoxLayout()
        self.add_buttons = {}
        for kind in store.ENTITIES:
            button = QPushButton(icon(kind), "+ " + kind.title())
            button.clicked.connect(lambda checked=False, entity=kind: self.add(entity))
            row.addWidget(button)
            self.add_buttons[kind] = button
        layout.addLayout(row)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Farm Data", "Type"])
        self.tree.headerItem().setIcon(0, icon("organisation"))
        self.tree.headerItem().setIcon(1, icon("whole"))
        self.tree.setColumnWidth(0, 480)
        self.tree.currentItemChanged.connect(self.selection_changed)
        layout.addWidget(self.tree)
        self.status = QLabel("Adds and renames save immediately to GeoPackage. Whole Field references remain separate from dated crop/season work.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        footer = QHBoxLayout()
        self.rename_button = QPushButton(icon("edit"), "Rename")
        self.rename_button.clicked.connect(self.rename)
        self.show_button = QPushButton(icon("field"), "Show Field on Map")
        self.show_button.clicked.connect(self.show_selected)
        close = QPushButton(icon("cancel"), "Close")
        close.clicked.connect(self.reject)
        footer.addWidget(self.rename_button)
        footer.addStretch()
        footer.addWidget(self.show_button)
        footer.addWidget(close)
        layout.addLayout(footer)
        self.reload()

    def reload(self, selected_id=None):
        self.tree.clear()
        self.rows = store.records(self.root)
        nodes = {}
        for kind in store.ENTITIES:
            parent_key = store.ENTITIES[kind][2]
            for row in self.rows[kind]:
                parent = nodes.get(row.get(parent_key)) if parent_key else self.tree.invisibleRootItem()
                if parent is None:
                    continue
                if kind == "season":
                    parent = parent.data(0, Qt.UserRole + 1)
                item = QTreeWidgetItem(parent, [row["name"], kind.title()])
                item.setIcon(0, icon(kind))
                item.setIcon(1, icon(kind))
                item.setData(0, Qt.UserRole, (kind, row["id"]))
                nodes[row["id"]] = item
                if kind == "field":
                    whole = self.branch(item, "Whole Field", "whole", "Reusable references")
                    for title, key in (("Boundaries", "field"), ("Guidance Lines", "guidance"),
                                       ("Terrain & Drainage", "terrain"), ("Infrastructure", "asset")):
                        self.branch(whole, title, key, "Reference data")
                    seasons = self.branch(item, "Seasons", "season", "Crop cycles and dated work")
                    item.setData(0, Qt.UserRole + 1, seasons)
                elif kind in {"season", "crop"}:
                    for title, key in (("Plans & Prescriptions", "plan"), ("Operations & Jobs", "job"),
                                       ("Observations & Results", "result")):
                        self.branch(item, title, key, "No imported data yet")
        self.tree.expandAll()
        if selected_id in nodes:
            self.tree.setCurrentItem(nodes[selected_id])
        elif self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))
        self.selection_changed()

    def branch(self, parent, title, key, scope):
        item = QTreeWidgetItem(parent, [title, scope])
        item.setIcon(0, icon(key))
        item.setIcon(1, icon(key))
        return item

    def ancestor(self, kind):
        item = self.tree.currentItem()
        while item:
            data = item.data(0, Qt.UserRole)
            if data and data[0] == kind:
                return data[1]
            item = item.parent()
        return None

    def selection_changed(self, *args):
        current = self.tree.currentItem()
        for kind, button in self.add_buttons.items():
            parent_kind = store.ENTITIES[kind][1]
            button.setEnabled(parent_kind is None or self.ancestor(parent_kind) is not None)
        self.rename_button.setEnabled(current is not None and bool(current.data(0, Qt.UserRole)))
        self.show_button.setEnabled(self.ancestor("field") is not None)

    def add(self, kind):
        parent_kind = store.ENTITIES[kind][1]
        parent_id = self.ancestor(parent_kind) if parent_kind else None
        dialog = NameDialog(kind, self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            record_id = store.add_record(self.root, kind, dialog.name.text(), parent_id,
                                         start=dialog.start.text().strip(), end=dialog.end.text().strip())
            self.reload(record_id)
            refresh_tree(self.root)
        except (ValueError, RuntimeError, OSError, sqlite3.Error) as error:
            QMessageBox.warning(self, "Could not add " + kind, str(error))

    def rename(self):
        item = self.tree.currentItem()
        if not item or not item.data(0, Qt.UserRole):
            return
        kind, record_id = item.data(0, Qt.UserRole)
        dialog = NameDialog(kind, self, item.text(0))
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            store.rename_record(self.root, kind, record_id, dialog.name.text())
            self.reload(record_id)
            refresh_tree(self.root)
        except (ValueError, RuntimeError, OSError, sqlite3.Error) as error:
            QMessageBox.warning(self, "Could not rename", str(error))

    def show_selected(self):
        field_id = self.ancestor("field")
        if field_id:
            try:
                show_field(self.root, field_id)
                self.accept()
            except (ValueError, RuntimeError, sqlite3.Error) as error:
                QMessageBox.warning(self, "Could not show field", str(error))


def sync_tree(root, project=None):
    """Mirror every stored hierarchy row with short, stable native QGIS groups."""
    project = project or QgsProject.instance()
    rows, key = store.records(root), store.workspace_id(root)
    tree = project.layerTreeRoot()
    group = next((node for node in tree.children() if isinstance(node, QgsLayerTreeGroup)
                  and node.customProperty("AgTechTooling/workspace") == key), None)
    if group is None:
        group = tree.addGroup("Farm Data")
        group.setCustomProperty("AgTechTooling/workspace", key)
    group.setName("Farm Data")
    groups = {}

    def child(parent, name, kind, identifier, field_id=""):
        node_key = kind + ":" + identifier
        node = next((node for node in parent.children() if isinstance(node, QgsLayerTreeGroup)
                     and node.customProperty("AgTechTooling/node") == node_key), None)
        if node is None:
            node = parent.addGroup(name)
        node.setName(name)
        node.setCustomProperty("AgTechTooling/node", node_key)
        node.setCustomProperty("AgTechTooling/kind", kind)
        node.setCustomProperty("AgTechTooling/field", field_id)
        return node

    for kind, (_, parent_kind, parent_key) in store.ENTITIES.items():
        for row in rows[kind]:
            parent = groups.get(row.get(parent_key)) if parent_kind else group
            if parent is None:
                continue
            if kind == "season":
                parent = groups["seasons:" + row[parent_key]]
            field_id = row["id"] if kind == "field" else parent.customProperty("AgTechTooling/field", "")
            node = child(parent, row["name"], kind, row["id"], field_id)
            groups[row["id"]] = node
            if kind == "field":
                groups["whole:" + row["id"]] = child(node, "Whole Field", "whole", row["id"], row["id"])
                groups["seasons:" + row["id"]] = child(node, "Seasons", "seasons", row["id"], row["id"])
            elif kind in {"season", "crop"}:
                for title in ("Plans", "Operations", "Results"):
                    child(node, title, title.lower(), row["id"], field_id)
    return group, groups


def refresh_tree(root):
    project = QgsProject.instance()
    if project.readEntry("AgTechTooling", "farm_id")[0] == store.workspace_id(root):
        sync_tree(root, project)
        project.setDirty(True)


def show_field(root, field_id, project=None):
    """Display shared native layers for one field; retain unrelated project data."""
    project = project or QgsProject.instance()
    if any(getattr(layer, "isEditable", lambda: False)() for layer in project.mapLayers().values()):
        raise ValueError("Finish layer edits before changing field context.")
    rows = store.validate(root)
    field = next((row for row in rows["field"] if row["id"] == field_id), None)
    if not field:
        raise ValueError("Select a valid field.")
    key = store.workspace_id(root)
    group, groups = sync_tree(root, project)
    whole = groups["whole:" + field_id]
    prepared = []
    for title, (table, geometry) in store.SPATIAL.items():
        existing = next((layer for layer in project.mapLayers().values()
                         if layer.customProperty("AgTechTooling/workspace") == key
                         and layer.customProperty("AgTechTooling/table") == table), None)
        layer = existing or QgsVectorLayer(
            store.layer_uri(root, table, f'"field_id" = \'{field_id}\''), title, "ogr")
        if not layer.isValid():
            raise ValueError("Could not read " + title)
        prepared.append((layer, existing, table))
    for layer, existing, table in prepared:
        expression = f'"field_id" = \'{field_id}\''
        if not layer.setSubsetString(expression):
            raise ValueError("QGIS could not filter the selected field.")
        for name, expression in (("id", "uuid()"), ("field_id", f"'{field_id}'"), ("revision", "'1'")):
            layer.setDefaultValueDefinition(layer.fields().indexFromName(name), QgsDefaultValue(expression))
        layer.setCustomProperty("AgTechTooling/workspace", key)
        layer.setCustomProperty("AgTechTooling/table", table)
        if not existing:
            project.addMapLayer(layer, False)
            whole.addLayer(layer)
        else:
            node = project.layerTreeRoot().findLayer(layer.id())
            if node is not None and node.parent() is not whole:
                whole.addChildNode(node.clone())
                node.parent().removeChildNode(node)
    # Retire empty legacy flat groups from 0.5; preserve any unrelated user content.
    for node in list(group.children()):
        if isinstance(node, QgsLayerTreeGroup) and not node.customProperty("AgTechTooling/node"):
            if node.name() in {"Whole Field", "Seasons"} and not node.children():
                group.removeChildNode(node)
    project.writeEntry("AgTechTooling", "selected_field", field_id)
    project.setDirty(True)
