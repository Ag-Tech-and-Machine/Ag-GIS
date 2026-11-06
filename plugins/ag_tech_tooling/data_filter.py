# SPDX-License-Identifier: GPL-2.0-or-later
from .branding import brand_dialog
"""Simple field/type filters over native managed layers; no data is removed."""
from qgis.PyQt.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox, QLabel, QVBoxLayout
from qgis.PyQt.QtCore import QModelIndex
from qgis.core import QgsProject
from . import hierarchy as store, managed_data, data_types
from .import_placement import workspace, field_path
from .ui_icons import icon, decorate_buttons


class DataFilterDialog(QDialog):
    def __init__(self, root, parent=None, iface=None):
        super().__init__(parent)
        self.root = root
        self.iface = iface
        self.setWindowTitle("Filter Data")
        brand_dialog(self)
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        label = QLabel("Show farm data for a field and data type. Filtering does not crop or delete data.")
        label.setWordWrap(True)
        layout.addWidget(label)
        form = QFormLayout()
        self.field = QComboBox()
        self.field.addItem(icon("organisation"), "All fields", "*")
        for row in store.records(root)["field"]:
            path = field_path(root, row["id"])
            self.field.addItem(icon("field"), " / ".join(path[k] for k in ("organisation", "client", "farm", "field")), row["id"])
        self.role = QComboBox()
        self.role.addItem(icon("whole"), "All data types", "*")
        for key, (name, image, _) in data_types.TYPES.items():
            self.role.addItem(icon(image), name, key)
        project = QgsProject.instance()
        for control, entry in ((self.field, "data_filter_field"), (self.role, "data_filter_role")):
            index = control.findData(project.readEntry("AgTechTooling", entry, "*")[0])
            control.setCurrentIndex(max(index, 0))
        form.addRow("Field", self.field)
        form.addRow("Data type", self.role)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        decorate_buttons(buttons)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def apply(self):
        try:
            managed_data.apply_filters(self.root, self.field.currentData(), self.role.currentData())
            if self.iface and hasattr(self.iface, "layerTreeView"):
                view = self.iface.layerTreeView()
                if self.field.currentData() == "*":
                    view.setCurrentIndex(QModelIndex())
                else:
                    from .hierarchy_dialog import sync_tree
                    _, nodes = sync_tree(self.root)
                    view.setCurrentNode(nodes[self.field.currentData()])
            self.status.setText("Filter applied. Save Map to keep this view.")
        except (ValueError, OSError, RuntimeError) as error:
            self.status.setText(str(error))


class FilterActions:
    def __init__(self, iface):
        self.iface, self.dialog = iface, None

    def open(self):
        try:
            root = workspace()
        except Exception as error:
            self.iface.messageBar().pushMessage("Filter Data", str(error), duration=8)
            return
        self.close()
        self.dialog = DataFilterDialog(root, self.iface.mainWindow(), self.iface)
        self.dialog.show()

    def close(self):
        if self.dialog is not None:
            self.dialog.reject()
            self.dialog.deleteLater()
            self.dialog = None
