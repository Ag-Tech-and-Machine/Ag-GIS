# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    # SPDX-License-Identifier: GPL-2.0-or-later

    from .branding import brand_dialog

    """Explicit existing/new field setup; acceptance returns a plan without writes."""

    from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,

        QComboBox, QDialogButtonBox, QWidget, QGridLayout)

    from qgis.core import QgsVectorLayer, QgsWkbTypes

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.gui import QgsProjectionSelectionWidget
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this module

from . import hierarchy as store

from .import_placement import KINDS

from .ui_icons import icon, decorate_buttons

from . import data_types





class DestinationEditor(QWidget):

    """Reusable field planner. Editing never writes hierarchy records."""

    def __init__(self, root, layer, reason, parent=None, compact=False):

        super().__init__(parent)

        self.setWindowTitle("Where does this data belong?")

        brand_dialog(self)

        self.setMinimumWidth(540)

        self.root, self.rows = root, store.records(root)

        self.spatial = not (isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.NullGeometry)

        layout = QVBoxLayout(self)

        intro = QLabel(f"{layer.name()}\n{reason}\nChoose existing names or type new ones. New records are created only when you import.")

        intro.setWordWrap(True)

        layout.addWidget(intro)

        form = QFormLayout()

        hierarchy = QGridLayout()

        self.combos = {}

        for column, kind in enumerate(KINDS):

            combo = QComboBox()

            combo.setEditable(True)

            combo.setInsertPolicy(QComboBox.NoInsert)

            combo.setAccessibleName(kind.title())

            hierarchy.addWidget(QLabel(kind.title()), 0, column)

            hierarchy.addWidget(combo, 1, column)

            hierarchy.setColumnStretch(column, 1)

            self.combos[kind] = combo

            combo.editTextChanged.connect(lambda text, k=kind: self.parent_changed(k))

        self.populate("organisation")

        layout.addLayout(hierarchy)

        self.role = QComboBox()

        for key in data_types.allowed(data_types.representation(layer)):

            name, image, _ = data_types.TYPES[key]

            self.role.addItem(icon(image), name, key)

        if not compact:

            form.addRow("Data type", self.role)

        else:

            self.role.hide()

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



    def plan(self):

        names = {kind: store.text(combo.currentText()) for kind, combo in self.combos.items()}

        if self.spatial and not self.crs.crs().isValid():

            raise ValueError("Select the file's actual coordinate system before importing.")

        return {"names": names, "crs": self.crs.crs()}



    def set_names(self, names):

        for kind in KINDS:

            self.combos[kind].setEditText(names.get(kind, ""))





class DestinationDialog(QDialog):

    """Compatibility wrapper; Data In embeds DestinationEditor directly."""

    def __init__(self, root, layer, reason, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Where does this data belong?")

        brand_dialog(self)

        layout = QVBoxLayout(self)

        self.editor = DestinationEditor(root, layer, reason, self)

        layout.addWidget(self.editor)

        self.combos, self.role, self.crs = self.editor.combos, self.editor.role, self.editor.crs

        self.error = self.editor.error

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons.button(QDialogButtonBox.Ok).setText("Use This Field")

        decorate_buttons(buttons)

        buttons.accepted.connect(self.accept)

        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)



    def accept(self):

        try:

            self.names = self.editor.plan()["names"]

            self.destination_role = self.role.currentData()

        except ValueError as error:

            self.error.setText(str(error))

            return

        super().accept()


