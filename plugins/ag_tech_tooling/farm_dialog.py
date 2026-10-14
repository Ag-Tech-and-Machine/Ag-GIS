# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path

from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)
from qgis.core import QgsProject
from qgis.gui import QgsProjectionSelectionWidget

from .farm_project import create_farm, validate_farm


class NewFarmDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("New Farm Project")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Create a farm GeoPackage and its map in a new folder."))
        form = QFormLayout()
        self.name = QLineEdit()
        self.location = QLineEdit()
        row = QHBoxLayout()
        row.addWidget(self.location)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        self.crs = QgsProjectionSelectionWidget()
        self.crs.setCrs(QgsProject.instance().crs())
        form.addRow("Farm name", self.name)
        form.addRow("Save inside", row)
        form.addRow("Farm coordinate system", self.crs)
        layout.addLayout(form)
        note = QLabel("Choose a local folder and confirm the coordinate system for your location. "
                      "Paddock layers, imports and exports will be added in later development.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Create Farm")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse(self):
        location = QFileDialog.getExistingDirectory(self, "Choose a local parent folder")
        if location:
            self.location.setText(location)


class FarmActions:
    def __init__(self, iface):
        self.iface = iface

    def can_replace_project(self):
        project = QgsProject.instance()
        if any(getattr(layer, "isEditable", lambda: False)() for layer in project.mapLayers().values()):
            QMessageBox.information(self.iface.mainWindow(), "Finish layer edits",
                                    "Save or discard layer edits and leave editing mode before switching farms.")
            return False
        if not project.isDirty():
            return True
        answer = QMessageBox.question(
            self.iface.mainWindow(), "Save current map?", "Save changes before switching farms?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)
        if answer == QMessageBox.Cancel:
            return False
        if answer == QMessageBox.Discard:
            return True
        if not project.fileName():
            path, _ = QFileDialog.getSaveFileName(self.iface.mainWindow(), "Save current map", "", "QGIS project (*.qgz)")
            if not path:
                return False
            return project.write(path)
        return project.write()

    def open_root(self, root):
        info = validate_farm(root)
        if not self.can_replace_project():
            return False
        if not self.iface.addProject(info["project"]):
            raise ValueError("QGIS could not open the farm map. The farm files have been retained.")
        self.iface.messageBar().pushMessage("Farm Project", f"Opened {info['name']} — {info['crs']}", duration=6)
        return True

    def new(self):
        dialog = NewFarmDialog(self.iface.mainWindow())
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            if not dialog.location.text().strip():
                raise ValueError("Choose an existing local folder for the farm.")
            root = create_farm(dialog.location.text(), dialog.name.text(), dialog.crs.crs())
            if not self.open_root(root):
                QMessageBox.information(self.iface.mainWindow(), "Farm created",
                                        f"The farm was created at {root}. Your current map remains open.")
        except (ValueError, OSError, RuntimeError) as error:
            QMessageBox.warning(self.iface.mainWindow(), "Farm Project", str(error))

    def open(self):
        path, _ = QFileDialog.getOpenFileName(self.iface.mainWindow(), "Open farm GeoPackage", "", "GeoPackage (*.gpkg)")
        if not path:
            return
        try:
            selected = Path(path).resolve()
            root = selected.parent.parent
            if selected != root / "Data" / "farm.gpkg":
                raise ValueError("Select Data/farm.gpkg inside an Ag Tech farm folder. General GeoPackage import is not available yet.")
            self.open_root(root)
        except (ValueError, OSError, RuntimeError) as error:
            QMessageBox.warning(self.iface.mainWindow(), "Farm Project", str(error))
