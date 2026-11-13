# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import sqlite3
from qgis.PyQt.QtCore import QItemSelectionModel, QTimer

from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)
from qgis.core import QgsProject
from qgis.gui import QgsProjectionSelectionWidget

from .farm_project import create_farm, validate_farm, upgrade_copy, validate_name
from .ui_icons import icon, decorate_input, decorate_buttons


class NewFarmDialog(QDialog):
    def __init__(self, parent, upgrade=False):
        super().__init__(parent)
        self.upgrade = upgrade
        self.setWindowTitle("Upgrade Project Copy" if upgrade else "New Farm Project")
        self.setWindowIcon(icon("organisation"))
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Create an upgraded copy; the original is retained." if upgrade
                                else "Create an Organisation / Client / Farm / Field workspace."))
        form = QFormLayout()
        self.name = QLineEdit("My Farm Data" if not upgrade else "")
        self.organisation, self.client, self.farm_name, self.field = (QLineEdit() for _ in range(4))
        from .workspace_defaults import projects_directory
        try:
            initial_location = str(projects_directory())
        except ValueError:
            initial_location = ""
        self.location = QLineEdit(initial_location)
        row = QHBoxLayout()
        row.addWidget(self.location)
        browse = QPushButton("Browse…")
        browse.setIcon(icon("open"))
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        self.crs = QgsProjectionSelectionWidget()
        self.crs.setCrs(QgsProject.instance().crs())
        for label, control, kind in (("Project name", self.name, "name"),
                                     ("Organisation", self.organisation, "organisation"),
                                     ("Client / Grower", self.client, "client")):
            decorate_input(control, kind)
            form.addRow(label, control)
        if not upgrade:
            for label, control, kind in (("First farm", self.farm_name, "farm"),
                                         ("First field (optional)", self.field, "field")):
                decorate_input(control, kind)
                form.addRow(label, control)
        decorate_input(self.location, "open")
        form.addRow("Save inside", row)
        form.addRow("Farm coordinate system", self.crs)
        layout.addLayout(form)
        note = QLabel("Choose a local folder and confirm the coordinate system. "
                      "Manage Data adds more clients, farms, fields, seasons and crops. "
                      "Imports, exports and conversion workflows are still under development.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Create Upgrade Copy" if upgrade else "Create Project")
        decorate_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        from .hierarchy import text
        try:
            validate_name(self.name.text())
            text(self.organisation.text())
            text(self.client.text())
            if not self.upgrade:
                text(self.farm_name.text())
                if self.field.text().strip():
                    text(self.field.text())
            if not self.location.text().strip():
                raise ValueError("Choose a parent folder.")
            if not self.crs.crs().isValid() or not self.crs.crs().authid():
                raise ValueError("Choose a recognised coordinate system.")
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, "Check project details", str(error))
            return
        super().accept()

    def browse(self):
        location = QFileDialog.getExistingDirectory(self, "Choose a local parent folder")
        if location:
            self.location.setText(location)


class FarmActions:
    def __init__(self, iface):
        self.iface = iface
        self.attached = False
        self.busy = False
        self.view = None

    def attach(self):
        if self.attached or not hasattr(self.iface, "layerTreeView"):
            return
        self.view = self.iface.layerTreeView()
        self.view.selectionModel().currentChanged.connect(self.field_selected)
        self.iface.projectRead.connect(self.project_read)
        self.attached = True
        QTimer.singleShot(0, self.refresh_current)

    def detach(self):
        if self.attached:
            self.view.selectionModel().currentChanged.disconnect(self.field_selected)
            self.iface.projectRead.disconnect(self.project_read)
        self.attached = False
        self.view = None

    def project_read(self):
        QTimer.singleShot(0, self.refresh_current)

    def refresh_current(self):
        if not self.attached or self.busy:
            return
        project = QgsProject.instance()
        if not project.fileName() or project.readNumEntry("AgTechTooling", "schema_version")[0] != 2:
            return
        self.busy = True
        try:
            from .hierarchy_dialog import sync_tree
            _, nodes = sync_tree(Path(project.fileName()).resolve().parent)
            selected = project.readEntry("AgTechTooling", "selected_field")[0]
            if selected in nodes:
                self.view.setCurrentNode(nodes[selected])
        except (ValueError, OSError, sqlite3.Error) as error:
            self.iface.messageBar().pushMessage("Farm Data", str(error), duration=8)
        finally:
            self.busy = False

    def field_selected(self, current, previous):
        if not self.attached or self.busy:
            return
        node = self.view.index2node(current)
        field_id = ""
        while node is not None:
            field_id = node.customProperty("AgTechTooling/field", "")
            if field_id:
                break
            node = node.parent()
        project = QgsProject.instance()
        if not field_id or project.readEntry("AgTechTooling", "selected_field")[0] == field_id:
            return
        if not project.fileName():
            return
        self.busy = True
        try:
            from .hierarchy_dialog import show_field
            show_field(Path(project.fileName()).resolve().parent, field_id)
        except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
            if previous.isValid():
                self.view.selectionModel().setCurrentIndex(previous, QItemSelectionModel.ClearAndSelect)
            self.iface.messageBar().pushMessage("Farm Data", str(error), duration=8)
        finally:
            self.busy = False

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

    def open_root(self, root, prompt=True):
        info = validate_farm(root)
        if prompt and not self.can_replace_project():
            return False
        if not self.iface.addProject(info["project"]):
            raise ValueError("QGIS could not open the farm map. The farm files have been retained.")
        self.iface.messageBar().pushMessage("Farm Project", f"Opened {info['name']} — {info['crs']}", duration=6)
        return True

    def new(self):
        try:
            if not self.can_replace_project():
                return
            from .workspace_defaults import create_default
            root = create_default()
            self.open_root(root, prompt=False)
            self.iface.messageBar().pushMessage("Farm Data", f"Ready. Saved in {root}. Rename or add items with Manage Data.", duration=12)
        except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
            QMessageBox.warning(self.iface.mainWindow(), "Could not create project", str(error))

    def new_with_options(self):
        dialog = NewFarmDialog(self.iface.mainWindow())
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            if not dialog.location.text().strip():
                raise ValueError("Choose an existing local folder for the farm.")
            Path(dialog.location.text()).mkdir(parents=True, exist_ok=True)
            root = create_farm(dialog.location.text(), dialog.name.text(), dialog.crs.crs(),
                               organisation=dialog.organisation.text(), client=dialog.client.text(),
                               farm=dialog.farm_name.text(), field=dialog.field.text(), build_tree=True)
            if not self.open_root(root):
                QMessageBox.information(self.iface.mainWindow(), "Farm created",
                                        f"The farm was created at {root}. Your current map remains open.")
            else:
                self.manage()
        except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
            QMessageBox.warning(self.iface.mainWindow(), "Farm Project", str(error))

    def manage(self):
        from .hierarchy_dialog import HierarchyDialog
        try:
            project = QgsProject.instance()
            if not project.fileName() or not Path(project.fileName()).is_file():
                raise ValueError("Create or open an Ag Tech project first.")
            root = Path(project.fileName()).resolve().parent
            info = validate_farm(root)
            if project.readEntry("AgTechTooling", "farm_id")[0] != info["farm_id"]:
                raise ValueError("Open this workspace's map with Open Project before managing its data.")
            if any(getattr(layer, "isEditable", lambda: False)() for layer in project.mapLayers().values()):
                raise ValueError("Finish layer edits before managing the hierarchy.")
            if info["version"] == 1:
                dialog = NewFarmDialog(self.iface.mainWindow(), upgrade=True)
                dialog.name.setText(root.name + " Upgraded")
                dialog.location.setText(str(root.parent))
                dialog.crs.setCrs(project.crs())
                dialog.crs.setEnabled(False)
                if dialog.exec() != QDialog.Accepted:
                    return
                if not self.can_replace_project():
                    return
                Path(dialog.location.text()).mkdir(parents=True, exist_ok=True)
                root = upgrade_copy(root, dialog.location.text(), dialog.name.text(),
                                    dialog.organisation.text(), dialog.client.text())
                if not self.open_root(root, prompt=False):
                    QMessageBox.information(self.iface.mainWindow(), "Upgrade copy created", str(root))
                    return
            HierarchyDialog(root, self.iface).exec()
        except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
            QMessageBox.warning(self.iface.mainWindow(), "Manage Farm Data", str(error))

    def open(self):
        from .workspace_defaults import projects_directory
        path, _ = QFileDialog.getOpenFileName(self.iface.mainWindow(), "Open farm GeoPackage", str(projects_directory()), "GeoPackage (*.gpkg)")
        if not path:
            return
        try:
            selected = Path(path).resolve()
            root = selected.parent.parent
            if selected != root / "Data" / "farm.gpkg":
                raise ValueError("Select Data/farm.gpkg inside an Ag Tech farm folder. General GeoPackage import is not available yet.")
            self.open_root(root)
        except (ValueError, OSError, RuntimeError, sqlite3.Error) as error:
            QMessageBox.warning(self.iface.mainWindow(), "Farm Project", str(error))
