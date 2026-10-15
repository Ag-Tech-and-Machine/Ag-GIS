# SPDX-License-Identifier: GPL-2.0-or-later
"""One source selector and an automatic, cancellable local-data preview."""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QProgressBar)
from qgis.core import (QgsApplication, QgsFeedback, QgsTask, QgsProject,
                       QgsVectorLayer, QgsRasterLayer)
from .import_sources import scan_local, ScanCancelled
from .ui_icons import icon, decorate_input
from . import import_placement as placement
from .import_destination import DestinationDialog


class ScanTask(QgsTask):
    def __init__(self, path, complete):
        super().__init__("Find farm data", QgsTask.CanCancel)
        self.path, self.complete = path, complete
        self.feedback = QgsFeedback()
        self.result, self.error = None, ""

    def cancel(self):
        self.feedback.cancel()
        super().cancel()

    def run(self):
        try:
            self.result = scan_local(self.path, self.feedback)
            return True
        except ScanCancelled:
            return False
        except Exception as error:
            self.error = str(error)
            return False

    def finished(self, success):
        callback, self.complete = self.complete, None
        if callback:
            callback(self.result if success else None, self.error)


class ImportDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface, self.task = iface, None
        self.setWindowTitle("Data In")
        self.setWindowIcon(icon("import"))
        self.resize(800, 480)
        layout = QVBoxLayout(self)
        intro = QLabel("Choose a file or folder. We’ll look inside and find the data for you.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        source = QHBoxLayout()
        self.path = QLineEdit()
        self.path.setPlaceholderText("File or folder on this computer or network")
        self.path.setAccessibleName("Import source")
        decorate_input(self.path, "open")
        self.path.returnPressed.connect(self.start_scan)
        source.addWidget(self.path, 1)
        self.file_button = self.button("Choose File…", "open", self.choose_file)
        self.folder_button = self.button("Choose Folder…", "folder", self.choose_folder)
        self.scan_button = self.button("Scan", "search", self.start_scan)
        for button in (self.file_button, self.folder_button, self.scan_button):
            source.addWidget(button)
        layout.addLayout(source)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.status = QLabel("Nothing has been scanned yet.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Data", "Type", "Result"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 150)
        self.tree.itemChanged.connect(self.update_add)
        layout.addWidget(self.tree, 1)
        note = QLabel("Import places data under its field. Existing boundaries help find the destination; "
                      "otherwise you can choose or create a field. Keep the original source files in place.")
        note.setWordWrap(True)
        layout.addWidget(note)
        footer = QHBoxLayout()
        self.stop_button = self.button("Stop Scan", "cancel", self.stop_scan)
        self.stop_button.setEnabled(False)
        footer.addWidget(self.stop_button)
        footer.addStretch()
        self.add_button = self.button("Import to Field", "add", self.add_selected)
        self.add_button.setEnabled(False)
        footer.addWidget(self.add_button)
        footer.addWidget(self.button("Close", "cancel", self.reject))
        layout.addLayout(footer)

    def button(self, text, kind, callback):
        button = QPushButton(icon(kind), text, self)
        button.setAutoDefault(False)
        button.clicked.connect(callback)
        return button

    def choose_file(self):
        selected, _ = QFileDialog.getOpenFileName(self, "Choose data file", self.path.text(), "All files (*)")
        if selected:
            self.path.setText(selected)
            self.start_scan()

    def choose_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Choose data folder", self.path.text())
        if selected:
            self.path.setText(selected)
            self.start_scan()

    def start_scan(self):
        if self.task:
            return
        path = self.path.text().strip().strip('"')
        if not path:
            self.status.setText("Choose a file or folder to start.")
            return
        self.tree.clear()
        self.add_button.setEnabled(False)
        self.status.setText("Looking for data… You can stop the scan at any time.")
        self.busy(True)
        self.task = ScanTask(path, self.scanned)
        QgsApplication.taskManager().addTask(self.task)

    def busy(self, scanning):
        self.progress.setVisible(scanning)
        self.stop_button.setEnabled(scanning)
        for control in (self.path, self.file_button, self.folder_button, self.scan_button):
            control.setEnabled(not scanning)

    def stop_scan(self):
        if self.task:
            self.task.cancel()
            self.status.setText("Stopping scan…")

    def scanned(self, result, error):
        self.task = None
        self.busy(False)
        if result is None:
            self.status.setText(f"Could not scan: {error}" if error else "Scan stopped. No data was added.")
            return
        self.show_result(result)

    def show_result(self, result):
        self.tree.clear()
        for record in result["items"]:
            row = QTreeWidgetItem(self.tree, [record["name"], record["format"], record["status"]])
            row.setToolTip(0, record["source"])
            row.setIcon(0, icon("import"))
            if record["kind"] == "layer":
                row.setData(0, Qt.UserRole, record)
                row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
                row.setCheckState(0, Qt.Checked)
                row.setIcon(0, icon("terrain" if record["layer_type"] == "raster" else "field"))
            elif record["kind"] == "deere":
                metadata = record["metadata"]
                nodes = {}
                for entity in metadata["entities"]:
                    parent = nodes.get((entity["profile"], entity["parent_id"].casefold()), row)
                    child = QTreeWidgetItem(parent, [entity["name"], entity["kind"].title(), "Identified"])
                    child.setIcon(0, icon(entity["kind"]))
                    nodes[(entity["profile"], entity["id"].casefold())] = child
                for item in metadata["spatial_items"]:
                    parent = nodes.get((item["profile"], item["field_id"].casefold()), row)
                    kind = {"CurvedTrackLine": "Curved guidance", "StraightTrackLine": "Straight guidance",
                            "Boundary": "Boundary"}.get(item["kind"], "Machine data")
                    child = QTreeWidgetItem(parent, [item["name"], kind, "Decoder needed"])
                    child.setIcon(0, icon("guidance"))
        for warning in result["warnings"]:
            row = QTreeWidgetItem(self.tree, ["Check source", "Notice", warning])
            row.setIcon(0, icon("notice"))
            row.setToolTip(2, warning)
        self.tree.expandAll()
        count = sum(item["kind"] == "layer" for item in result["items"])
        machine_count = sum(item["kind"] != "layer" for item in result["items"])
        self.status.setText(f"Checked {result['files_scanned']} files. {count} map layers ready."
                            + (f" {machine_count} machine exports identified." if machine_count else "")
                            + (" Review the results below." if result["items"] or result["warnings"]
                               else " No recognised data found. Try the complete export folder."))
        self.update_add()

    def update_add(self):
        self.add_button.setEnabled(any(row.checkState(0) == Qt.Checked and row.data(0, Qt.UserRole)
            for row in (self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount()))))

    def add_selected(self):
        project = QgsProject.instance()
        try:
            root = placement.workspace(project)
        except Exception as error:
            self.status.setText(str(error))
            return
        existing = {(layer.providerType(), layer.source()): layer for layer in project.mapLayers().values()}
        plans, failed, skipped = [], [], 0
        for index in range(self.tree.topLevelItemCount()):
            row = self.tree.topLevelItem(index)
            record = row.data(0, Qt.UserRole)
            if not record or row.checkState(0) != Qt.Checked:
                continue
            key = (record["provider"], record["uri"])
            previous = existing.get(key)
            if previous and previous.customProperty("AgTechTooling/import_field"):
                row.setText(2, "Already assigned to a field")
                row.setCheckState(0, Qt.Unchecked)
                skipped += 1
                continue
            factory = QgsVectorLayer if record["layer_type"] == "vector" else QgsRasterLayer
            layer = previous or factory(record["uri"], record["name"], record["provider"])
            if not layer.isValid():
                failed.append(record["name"])
                row.setText(2, "Could not open — check source files")
                continue
            match = placement.match_field(root, layer, project)
            if match["field_id"]:
                plan = {"field_id": match["field_id"], "role": "data"}
            else:
                dialog = DestinationDialog(root, layer, match["reason"], self)
                if dialog.exec() != QDialog.Accepted:
                    self.status.setText("Import cancelled. No layers or field records were added.")
                    return
                plan = {"names": dialog.names, "role": dialog.destination_role, "crs": dialog.crs.crs()}
            plans.append((row, layer, plan))
        added = []
        try:
            if placement.workspace(project) != root:
                raise ValueError("The project changed. Import again in the correct workspace.")
        except Exception as error:
            self.status.setText(str(error))
            return
        for row, layer, plan in plans:
            try:
                field_id = plan.get("field_id") or placement.ensure_field(root, plan["names"])
                if "crs" in plan and plan["crs"].isValid():
                    layer.setCrs(plan["crs"])
                placement.place_layer(root, layer, field_id, plan["role"], project)
            except Exception as error:
                failed.append(layer.name())
                row.setText(2, str(error))
                continue
            added.append(layer)
            row.setCheckState(0, Qt.Unchecked)
            names = placement.field_path(root, field_id)
            row.setText(2, "Placed: " + " / ".join(names[kind] for kind in placement.KINDS))
        if added:
            self.iface.mapCanvas().refresh()
            self.iface.mapCanvas().zoomToFullExtent()
        self.status.setText(f"{len(added)} layers placed under fields. {skipped} already assigned. {len(failed)} could not import. "
                            "Save your project to keep these source links.")
        self.update_add()

    def done(self, result):
        if self.task:
            self.task.complete = None
            self.task.cancel()
            self.task = None
            self.busy(False)
            self.status.setText("Scan stopped. No data was added.")
        super().done(result)


class ImportActions:
    def __init__(self, iface):
        self.iface, self.dialog = iface, None

    def open(self):
        if self.dialog is None:
            self.dialog = ImportDialog(self.iface)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def close(self):
        if self.dialog is not None:
            self.dialog.reject()
            self.dialog.deleteLater()
            self.dialog = None
