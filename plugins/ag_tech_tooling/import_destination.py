# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit existing/new field setup; acceptance returns a plan without writes."""
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,
    QComboBox, QDialogButtonBox)
from qgis.core import QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgsProjectionSelectionWidget
from . import hierarchy as store
from .import_placement import KINDS
from .ui_icons import icon, decorate_buttons


class DestinationDialog(QDialog):
    def __init__(self, root, layer, reason, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Where does this data belong?")
        self.setWindowIcon(icon("field"))
        self.setMinimumWidth(540)
        self.root, self.layer, self.rows = root, layer, store.records(root)
        self.spatial = not (isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.NullGeometry)
        layout = QVBoxLayout(self)
        intro = QLabel(f"{layer.name()}\n{reason}\nChoose existing names or type new ones. New records are created only when you import.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        self.combos = {}
        for kind in KINDS:
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.setAccessibleName(kind.title())
            form.addRow(kind.title(), combo)
            self.combos[kind] = combo
            combo.editTextChanged.connect(lambda text, k=kind: self.parent_changed(k))
        self.populate("organisation")
        self.role = QComboBox()
        self.role.addItem(icon("whole"), "Other field data", "data")
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            self.role.addItem(icon("field"), "Field boundary — use to locate future imports", "boundary")
        form.addRow("Data type", self.role)
        self.crs = QgsProjectionSelectionWidget()
        self.crs.setCrs(layer.crs())
        if self.spatial and not layer.crs().isValid():
            form.addRow("File coordinate system", self.crs)
        else:
            self.crs.hide()
        layout.addLayout(form)
        self.error = QLabel()
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Use This Field")
        decorate_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.combos["field"].setEditText(layer.name())

    def selected_id(self, kind):
        combo = self.combos[kind]
        if combo.currentIndex() >= 0 and combo.currentText() == combo.itemText(combo.currentIndex()):
            return combo.currentData()
        return None

    def populate(self, kind):
        combo = self.combos[kind]
        parent_kind, parent_key = store.ENTITIES[kind][1:]
        parent_id = self.selected_id(parent_kind) if parent_kind else None
        combo.blockSignals(True)
        combo.clear()
        for row in self.rows[kind]:
            if not parent_key or row[parent_key] == parent_id:
                combo.addItem(icon(kind), row["name"], row["id"])
        if not combo.count():
            combo.addItem(icon(kind), "", None)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)
        self.parent_changed(kind)

    def parent_changed(self, kind):
        index = KINDS.index(kind)
        if index + 1 < len(KINDS):
            self.populate(KINDS[index + 1])

    def accept(self):
        try:
            self.names = {kind: store.text(combo.currentText()) for kind, combo in self.combos.items()}
            if self.spatial and not self.crs.crs().isValid():
                raise ValueError("Select the file's actual coordinate system before importing.")
            self.destination_role = self.role.currentData()
        except ValueError as error:
            self.error.setText(str(error))
            return
        super().accept()
