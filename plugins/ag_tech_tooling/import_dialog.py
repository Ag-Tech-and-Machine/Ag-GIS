# SPDX-License-Identifier: GPL-2.0-or-later
from .branding import brand_dialog
"""One source selector and an automatic, cancellable local-data preview."""
from qgis.PyQt.QtCore import Qt, QModelIndex
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QProgressBar, QComboBox, QProgressDialog,
    QFormLayout, QPlainTextEdit, QDialogButtonBox)
from qgis.core import (QgsApplication, QgsFeedback, QgsTask, QgsProject,
                       QgsVectorLayer, QgsRasterLayer, QgsRasterBlockFeedback)
from .import_sources import scan_local, ScanCancelled
from .ui_icons import icon, decorate_input
from . import import_placement as placement
from .import_destination import DestinationEditor
from . import managed_data, data_types


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


class SeasonPreviewDialog(QDialog):
    """Preview or explicitly stage one whole-dataset job; no writes in this modal."""
    def __init__(self, root, field_id, record, layer, parent=None):
        super().__init__(parent)
        self.root, self.field_id, self.review = root, field_id, None
        self.layer, self.accepted_review = layer, None
        self.initial_source_hash = managed_data.source_hash(layer)
        self.setWindowTitle("Ag-GIS — Preview Job Season")
        brand_dialog(self)
        self.resize(760, 600)
        layout = QVBoxLayout(self)
        self.notice = QLabel("Preview only until Use for Import — Close saves nothing. "
                             "One job date/type applies to this entire dataset. Mixed jobs must be separated first. "
                             "Use the recorded job date, not the import date. Unknown source types need review.")
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        form = QFormLayout()
        self.source = QLabel(record["uri"])
        self.source.setTextFormat(Qt.PlainText)
        self.source.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.source.setWordWrap(True)
        form.addRow("Original source", self.source)
        names = placement.field_path(root, field_id)
        field_label = QLabel(" / ".join(names[kind] for kind in placement.KINDS))
        field_label.setTextFormat(Qt.PlainText)
        field_label.setWordWrap(True)
        form.addRow("Reviewed field", field_label)
        self.job_date = QLineEdit()
        self.job_date.setPlaceholderText("YYYY-MM-DD — recorded job date")
        self.job_date.setAccessibleName("Recorded job date for season review")
        form.addRow("Job date", self.job_date)
        self.operation = QComboBox()
        self.operation.setAccessibleName("Job type for season review")
        self.operation.addItem("Unknown — please review", "unknown")
        from .classification import OPERATION_FAMILIES
        for key in OPERATION_FAMILIES:
            self.operation.addItem(key.title(), key)
        form.addRow("Job type (explicit selection)", self.operation)
        layout.addLayout(form)
        self.attributes = QPlainTextEdit()
        self.attributes.setReadOnly(True)
        self.attributes.setAccessibleName("Original source attribute sample, not decoded job metadata")
        self.attributes.setMaximumHeight(140)
        if isinstance(layer, QgsVectorLayer):
            # Bounded provider reads; no scan for guessed date/type column names.
            from qgis.core import QgsFeatureRequest
            import json
            request = QgsFeatureRequest().setLimit(5).setFlags(QgsFeatureRequest.NoGeometry)
            sample = [{field.name(): feature[index] for index, field in enumerate(layer.fields())}
                      for feature in layer.getFeatures(request)]
            self.attributes.setPlainText("Original attributes — first 5 features at most; no automatic interpretation:\n"
                                         + json.dumps(sample, ensure_ascii=False, default=str, indent=2))
        else:
            self.attributes.setPlainText("Raster source: no decoded job date or operation type is supplied. "
                                         "Do not infer these from pixels or the filename.")
        layout.addWidget(self.attributes)
        self.result = QLabel()
        self.result.setTextFormat(Qt.PlainText)
        self.result.setWordWrap(True)
        layout.addWidget(self.result)
        self.timeline = QTreeWidget()
        self.timeline.setHeaderLabels(["Season", "First day (included)", "Last day (included)"])
        layout.addWidget(self.timeline, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        self.use_button = buttons.addButton("Use for Import", QDialogButtonBox.ActionRole)
        self.use_button.clicked.connect(self.use_for_import)
        self.clear_button = buttons.addButton("Keep Whole Field", QDialogButtonBox.ActionRole)
        self.clear_button.clicked.connect(self.keep_whole_field)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.job_date.textChanged.connect(self.refresh_preview)
        self.operation.currentIndexChanged.connect(self.refresh_preview)
        self.refresh_preview()

    def refresh_preview(self, *args):
        self.review = None
        self.use_button.setEnabled(False)
        self.timeline.clear()
        try:
            review = placement.review_job_season(self.root, self.field_id, self.job_date.text(), self.operation.currentData())
        except ValueError as error:
            self.result.setText(str(error))
            return
        self.review = review
        self.use_button.setEnabled(True)
        for season in review["timeline"]:
            item = QTreeWidgetItem(self.timeline, [season["name"], season["start_date"], season["end_date"]])
            if season["id"] == review["season_id"]:
                item.setSelected(True)
        self.result.setText("Preview match: " + review["season_name"] + ". Nothing has been assigned or saved.")


    def use_for_import(self):
        from .reviewed_import import prepare_review
        try:
            if managed_data.source_hash(self.layer) != self.initial_source_hash:
                raise ValueError("Source changed since this preview opened. Close, rescan and review again.")
            self.accepted_review = prepare_review(self.root, self.layer, self.review)
        except (ValueError, TypeError) as error:
            self.accepted_review = None
            self.result.setText(str(error))
            self.use_button.setEnabled(False)
            return
        self.accept()

    def keep_whole_field(self):
        self.accepted_review = None
        self.accept()


class ImportDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface, self.task = iface, None
        self.setWindowTitle("Data In")
        brand_dialog(self)
        self.resize(1080, 640)
        self.preview_root, self.editor, self.editor_row = None, None, None
        self.field_options = []
        self.drafts_dirty = False
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
        self.tree.setHeaderLabels(["Data", "Type", "Destination", "Status"])
        self.tree.setColumnWidth(0, 240)
        self.tree.setColumnWidth(1, 190)
        self.tree.setColumnWidth(2, 330)
        self.tree.itemChanged.connect(self.update_add)
        self.tree.currentItemChanged.connect(self.edit_destination)
        layout.addWidget(self.tree, 1)
        self.editor_layout = QVBoxLayout()
        layout.addLayout(self.editor_layout)
        apply_bar = QHBoxLayout()
        self.apply_row = self.button("Use for This File", "field", self.apply_destination)
        self.apply_checked = self.button("Apply to Checked Files", "field", lambda: self.apply_destination(True))
        for button in (self.apply_row, self.apply_checked):
            button.setEnabled(False)
            apply_bar.addWidget(button)
        self.season_preview_button = self.button("Preview Job Season…", "season", self.preview_job_season)
        self.season_preview_button.setEnabled(False)
        apply_bar.addWidget(self.season_preview_button)
        apply_bar.addStretch()
        layout.addLayout(apply_bar)
        note = QLabel("Import places data under its field. Existing boundaries help find the destination; "
                      "otherwise choose or create a field. Imports are saved inside your farm workspace.")
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
        self.clear_editor()
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
        self.clear_editor()
        self.tree.clear()
        try:
            self.preview_root = placement.workspace(QgsProject.instance())
        except ValueError:
            self.preview_root = None
        self.load_field_options()
        known_roles = {layer.customProperty("AgTechTooling/import_source", layer.source()):
                       layer.customProperty("AgTechTooling/import_role", "data")
                       for layer in QgsProject.instance().mapLayers().values()}
        for record in result["items"]:
            row = QTreeWidgetItem(self.tree, [record["name"], record["format"], "", record["status"]])
            row.setToolTip(0, record["source"])
            row.setIcon(0, icon("import"))
            if record["kind"] == "layer":
                row.setData(0, Qt.UserRole, record)
                row.setFlags(row.flags() | Qt.ItemIsUserCheckable)
                row.setCheckState(0, Qt.Checked)
                row.setIcon(0, icon("terrain" if record["layer_type"] == "raster" else "field"))
                choices = QComboBox(self.tree)
                for key in data_types.allowed(record.get("representation", "raster" if record["layer_type"] == "raster" else "unknown")):
                    name, image, _ = data_types.TYPES[key]
                    choices.addItem(icon(image), name, key)
                previous = choices.findData(known_roles.get(record["uri"], "data"))
                choices.setCurrentIndex(max(previous, 0))
                self.tree.setItemWidget(row, 1, choices)
                self.detect_destination(row)
                self.populate_selector(row)
            elif record["kind"] == "pctgdp":
                for layer in record["metadata"]["layers"]:
                    kind = {"ElevationLayerVariables": "Elevation surface",
                            "BoundaryLayerVariables": "Boundary",
                            "RegionLayerVariables": "Region",
                            "PolygonOverlay": "Polygon overlay"}.get(layer["type"], layer["type"])
                    child = QTreeWidgetItem(row, [layer["name"], kind, "", "Decoder verification needed"])
                    child.setIcon(0, icon("terrain" if layer["type"] == "ElevationLayerVariables" else "field"))
                    details = [f"UTM zone: {layer.get('utm_zone', 'unknown')} {layer.get('hemisphere', '')}",
                               f"Units: {layer.get('units', 'not recorded')}"]
                    if layer.get("pixel_size"):
                        details.append(f"Grid spacing: {layer['pixel_size']}")
                    details.extend(record["metadata"]["limitations"])
                    child.setToolTip(3, "\n".join(details))
            elif record["kind"] == "deere":
                metadata = record["metadata"]
                nodes = {}
                for entity in metadata["entities"]:
                    parent = nodes.get((entity["profile"], entity["parent_id"].casefold()), row)
                    child = QTreeWidgetItem(parent, [entity["name"], entity["kind"].title(), "", "Identified"])
                    child.setIcon(0, icon(entity["kind"]))
                    nodes[(entity["profile"], entity["id"].casefold())] = child
                for item in metadata["spatial_items"]:
                    parent = nodes.get((item["profile"], item["field_id"].casefold()), row)
                    kind = {"CurvedTrackLine": "Curved guidance", "StraightTrackLine": "Straight guidance",
                            "Boundary": "Boundary"}.get(item["kind"], "Machine data")
                    child = QTreeWidgetItem(parent, [item["name"], kind, "", "Decoder needed"])
                    child.setIcon(0, icon("guidance"))
        for warning in result["warnings"]:
            row = QTreeWidgetItem(self.tree, ["Check source", "Notice", "", warning])
            row.setIcon(0, icon("notice"))
            row.setToolTip(3, warning)
        self.tree.expandAll()
        count = sum(item["kind"] == "layer" for item in result["items"])
        machine_count = sum(item["kind"] != "layer" for item in result["items"])
        missing = sum(not row.data(0, Qt.UserRole + 1) for row in self.rows())
        self.status.setText(f"Checked {result['files_scanned']} files. {count} map layers found. {missing} need a destination."
                            + (f" {machine_count} project/machine containers identified." if machine_count else "")
                            + (" Review the results below." if result["items"] or result["warnings"]
                               else " No recognised data found. Try the complete export folder."))
        self.update_add()
        first = next((row for row in self.rows() if not row.data(0, Qt.UserRole + 1)), None)
        if first:
            self.tree.setCurrentItem(first)

    def rows(self):
        return [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())
                if self.tree.topLevelItem(i).data(0, Qt.UserRole)]

    def open_layer(self, row):
        record = row.data(0, Qt.UserRole)
        previous = next((layer for layer in QgsProject.instance().mapLayers().values()
                         if (layer.providerType(), layer.source()) == (record["provider"], record["uri"])), None)
        factory = QgsVectorLayer if record["layer_type"] == "vector" else QgsRasterLayer
        return previous or factory(record["uri"], record["name"], record["provider"])

    def set_plan(self, row, plan, status):
        row.setData(0, Qt.UserRole + 3, None)
        row.setData(0, Qt.UserRole + 1, plan)
        names = (placement.field_path(self.preview_root, plan["field_id"])
                 if plan.get("field_id") else plan["names"])
        destination = " / ".join(names[kind] for kind in placement.KINDS)
        row.setText(2, destination)
        row.setToolTip(2, destination)
        row.setIcon(2, icon("field"))
        row.setText(3, status)
        self.populate_selector(row)

    def load_field_options(self):
        """Read hierarchy once per refresh, retaining IDs for same-name fields."""
        self.field_options = []
        if not self.preview_root:
            return
        records = placement.store.records(self.preview_root)
        lookup = {kind: {row["id"]: row for row in records[kind]} for kind in placement.KINDS}
        for field in records["field"]:
            names, selected = {}, field["id"]
            for kind in reversed(placement.KINDS):
                entry = lookup[kind][selected]
                names[kind] = entry["name"]
                selected = entry.get(placement.store.ENTITIES[kind][2])
            self.field_options.append((" / ".join(names[kind] for kind in placement.KINDS),
                                       {"field_id": field["id"]}))
        self.field_options.sort(key=lambda entry: entry[0].casefold())

    def populate_selector(self, row):
        row.setIcon(2, QIcon())  # The selector supplies the destination icon.
        selector = self.tree.itemWidget(row, 2)
        if selector is None:
            selector = QComboBox(self.tree)
            selector.setAccessibleName("Destination for " + row.text(0))
            selector.setMinimumWidth(180)
            self.tree.setItemWidget(row, 2, selector)
            selector.activated.connect(lambda index, item=row: self.choose_destination(item))
        selector.blockSignals(True)
        selector.clear()
        selector.addItem(icon("notice"), "Please choose field…", None)
        options = list(self.field_options)
        # Pending new fields are also selectable by other files before saving.
        labels = {label.casefold() for label, _ in options}
        for candidate in self.rows():
            plan = candidate.data(0, Qt.UserRole + 1)
            if plan and plan.get("names"):
                label = " / ".join(plan["names"][kind] for kind in placement.KINDS)
                if label.casefold() not in labels:
                    options.append((label, {"names": plan["names"]}))
                    labels.add(label.casefold())
        plan = row.data(0, Qt.UserRole + 1)
        selected = 0
        for label, option in options:
            selector.addItem(icon("field"), label, option)
            if plan and ((plan.get("field_id") and plan.get("field_id") == option.get("field_id"))
                         or (plan.get("names") and label.casefold() == row.text(2).casefold())):
                selected = selector.count() - 1
        selector.insertSeparator(selector.count())
        selector.addItem(icon("add"), "Add new field…", "add")
        selector.setCurrentIndex(selected)
        selector.setToolTip(row.toolTip(2) or "Choose an existing field or Add new field…")
        selector.setEnabled(self.preview_root is not None)
        selector.blockSignals(False)

    def choose_destination(self, row):
        row.setData(0, Qt.UserRole + 3, None)
        choice = self.tree.itemWidget(row, 2).currentData()
        old_plan = row.data(0, Qt.UserRole + 1) or {}
        self.tree.setCurrentItem(row)
        layer = self.open_layer(row)
        own_crs = old_plan.get("crs", layer.crs())
        if choice == "add":
            names = {kind: combo.currentText() for kind, combo in self.editor.combos.items()} if self.editor else {}
            names["field"] = ""
            self.clear_editor()
            row.setData(0, Qt.UserRole + 1, None)
            row.setData(0, Qt.UserRole + 2, {"names": names, "crs": own_crs})
            row.setText(2, "Add new field…")
            row.setText(3, "Please set")
            self.edit_destination(row)
            if self.editor:
                self.editor.combos["field"].setFocus()
            return
        self.clear_editor()
        row.setData(0, Qt.UserRole + 2, None)
        if not choice:
            row.setData(0, Qt.UserRole + 1, None)
            row.setText(2, "Please choose field…")
            row.setText(3, "Please set")
        elif not own_crs.isValid() and data_types.representation(layer) != "table":
            names = (placement.field_path(self.preview_root, choice["field_id"])
                     if choice.get("field_id") else choice["names"])
            row.setData(0, Qt.UserRole + 1, None)
            row.setData(0, Qt.UserRole + 2, {"names": names, "crs": own_crs})
            row.setText(3, "Please set coordinate system")
        else:
            self.set_plan(row, dict(choice, crs=own_crs), "Ready")
        self.edit_destination(row)
        self.update_add()

    def detect_destination(self, row):
        row.setData(0, Qt.UserRole + 1, None)
        row.setText(2, "Please set destination")
        row.setIcon(2, icon("notice"))
        if not self.preview_root:
            row.setText(3, "Create or open a farm workspace first")
            return
        layer = self.open_layer(row)
        if not layer.isValid():
            row.setText(3, "Could not open source")
            return
        field_id = layer.customProperty("AgTechTooling/import_field", "")
        if not (field_id and layer.customProperty("AgTechTooling/workspace") == placement.store.workspace_id(self.preview_root)):
            match = placement.match_field(self.preview_root, layer, QgsProject.instance())
            field_id = match["field_id"]
            row.setToolTip(3, match["reason"])
        if field_id and layer.crs().isValid():
            self.set_plan(row, {"field_id": field_id}, "Detected")
        else:
            row.setText(3, "Please set")

    def clear_editor(self):
        self.season_preview_button.setEnabled(False)
        if self.editor is not None:
            self.editor_layout.removeWidget(self.editor)
            self.editor.hide()
            self.editor.deleteLater()
        self.editor, self.editor_row, self.drafts_dirty = None, None, False
        for button in (self.apply_row, self.apply_checked):
            button.setEnabled(False)

    def edit_destination(self, row, previous=None):
        # Keep every draft on its row when browsing a batch, without creating data.
        if self.editor and self.editor_row and self.drafts_dirty:
            self.editor_row.setData(0, Qt.UserRole + 2,
                {"names": {kind: combo.currentText() for kind, combo in self.editor.combos.items()},
                 "crs": self.editor.crs.crs()})
        self.clear_editor()
        if not row or not row.data(0, Qt.UserRole) or not self.preview_root:
            return
        layer = self.open_layer(row)
        if not layer.isValid():
            return
        self.editor_row = row
        self.editor = DestinationEditor(self.preview_root, layer,
            "Set the destination here, then use it for this file or all checked files.", self, compact=True)
        plan = row.data(0, Qt.UserRole + 1)
        draft = row.data(0, Qt.UserRole + 2)
        if draft:
            self.editor.set_names(draft["names"])
            self.editor.crs.setCrs(draft["crs"])
            self.drafts_dirty = True
        elif plan:
            names = placement.field_path(self.preview_root, plan["field_id"]) if plan.get("field_id") else plan["names"]
            self.editor.set_names(names)
            if plan.get("crs"):
                self.editor.crs.setCrs(plan["crs"])
        self.editor_layout.addWidget(self.editor)
        for combo in self.editor.combos.values():
            combo.editTextChanged.connect(self.destination_changed)
        self.editor.crs.crsChanged.connect(self.destination_changed)
        for button in (self.apply_row, self.apply_checked):
            button.setEnabled(True)
        self.update_add()

    def destination_changed(self, *args):
        self.drafts_dirty = True
        self.editor_row.setData(0, Qt.UserRole + 3, None)
        self.editor_row.setData(0, Qt.UserRole + 1, None)
        self.editor_row.setText(2, "Please set destination")
        self.editor_row.setText(3, "Please apply destination")
        selector = self.tree.itemWidget(self.editor_row, 2)
        if selector:
            selector.setCurrentIndex(0)
        self.update_add()

    def apply_destination(self, checked=False):
        if self.editor is None:
            return
        try:
            plan = self.editor.plan()
            targets = [row for row in self.rows() if row.checkState(0) == Qt.Checked] if checked else [self.editor_row]
            prepared = []
            for row in targets:
                layer = self.open_layer(row)
                if not layer.isValid():
                    raise ValueError("Could not open " + layer.name())
                # Never copy a coordinate-system assumption between different files.
                if row is not self.editor_row and not layer.crs().isValid() and data_types.representation(layer) != "table":
                    raise ValueError("Set the file coordinate system individually for " + layer.name())
                entry = {"names": plan["names"]}
                if row is self.editor_row:
                    entry["crs"] = plan["crs"]
                prepared.append((row, entry))
            for row, entry in prepared:
                row.setData(0, Qt.UserRole + 2, None)
                self.set_plan(row, entry, "Ready")
            self.drafts_dirty = False
            self.editor.error.clear()
            for row in self.rows():
                self.populate_selector(row)
            self.update_add()
            checked_rows = [row for row in self.rows() if row.checkState(0) == Qt.Checked]
            missing = sum(not row.data(0, Qt.UserRole + 1) for row in checked_rows)
            self.status.setText(f"{len(checked_rows) - missing} checked files ready. {missing} need a destination. "
                                "Review destinations, then Import to Field.")
        except ValueError as error:
            self.editor.error.setText(str(error))

    def create_season_preview(self):
        row = self.tree.currentItem()
        plan = row.data(0, Qt.UserRole + 1) if row else None
        if not self.preview_root or not plan or not plan.get("field_id"):
            self.status.setText("Choose an existing field destination to preview job seasons. No data was changed.")
            return None
        try:
            if placement.workspace(QgsProject.instance()) != self.preview_root:
                raise ValueError("Workspace changed. Rescan before previewing a job season.")
            layer = self.open_layer(row)
            if not layer.isValid():
                raise ValueError("Could not open the source. Rescan before previewing.")
            return SeasonPreviewDialog(self.preview_root, plan["field_id"], row.data(0, Qt.UserRole), layer, self)
        except ValueError as error:
            self.status.setText(str(error))
            return None

    def preview_job_season(self):
        preview = self.create_season_preview()
        if preview is not None:
            if preview.exec() == QDialog.Accepted:
                row = self.tree.currentItem()
                row.setData(0, Qt.UserRole + 3, preview.accepted_review)
                row.setText(3, ("Job reviewed: " + preview.accepted_review["season_name"]
                               if preview.accepted_review else "Whole Field — no job binding"))
            preview.deleteLater()

    def update_add(self):
        current = self.tree.currentItem()
        plan = current.data(0, Qt.UserRole + 1) if current else None
        self.season_preview_button.setEnabled(bool(self.preview_root and plan and plan.get("field_id")))
        checked = [row for row in self.rows() if row.checkState(0) == Qt.Checked]
        self.add_button.setEnabled(bool(checked) and all(row.data(0, Qt.UserRole + 1) for row in checked)
                                   and not (self.drafts_dirty and self.editor_row in checked))
        if hasattr(self, "add_button"):
            missing = sum(not row.data(0, Qt.UserRole + 1) for row in checked)
            self.add_button.setToolTip(f"{missing} checked files need a destination. Select a row to set it below."
                                      if missing else "Save checked files to their displayed destinations")

    def add_selected(self):
        project = QgsProject.instance()
        try:
            root = placement.workspace(project)
        except Exception as error:
            self.status.setText(str(error))
            return
        if root != self.preview_root:
            self.preview_root = root
            self.load_field_options()
            self.clear_editor()
            for row in self.rows():
                self.detect_destination(row)
            self.status.setText("Workspace changed. Review destinations before importing.")
            self.update_add()
            return
        checked = [row for row in self.rows() if row.checkState(0) == Qt.Checked]
        if (self.drafts_dirty and self.editor_row in checked) or any(not row.data(0, Qt.UserRole + 1) for row in checked):
            self.status.setText("Please set and apply a destination for every checked file, or untick it.")
            return
        plans, failed, skipped = [], [], 0
        for row in checked:
            layer = self.open_layer(row)
            if not layer.isValid():
                self.status.setText("Could not open source. Rescan and review the batch.")
                row.setText(3, "Could not open source")
                return
            plan = dict(row.data(0, Qt.UserRole + 1))
            if plan.get("field_id"):
                try:
                    placement.field_path(root, plan["field_id"])
                except ValueError:
                    row.setData(0, Qt.UserRole + 1, None)
                    row.setText(3, "Please set destination again")
                    self.update_add()
                    return
            choices = self.tree.itemWidget(row, 1)
            plan["role"] = choices.currentData() if choices else "data"
            plan["review"] = row.data(0, Qt.UserRole + 3)
            plans.append((row, layer, plan))
        added, added_fields = [], set()
        try:
            if placement.workspace(project) != root:
                raise ValueError("The project changed. Import again in the correct workspace.")
        except Exception as error:
            self.status.setText(str(error))
            return
        progress = QProgressDialog("Saving imported data…", "Stop", 0, 0, self)
        progress.setWindowTitle("Ag-GIS — Data In")
        brand_dialog(progress)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        for button in progress.findChildren(QPushButton):
            button.setIcon(icon("cancel"))
        feedback = QgsRasterBlockFeedback()
        progress.canceled.connect(feedback.cancel)
        def advance(value):
            progress.setRange(0, 100)
            progress.setValue(min(99, int(value)))
            QgsApplication.processEvents()
        feedback.progressChanged.connect(advance)
        for row, layer, plan in plans:
            if feedback.isCanceled():
                break
            try:
                field_id = plan.get("field_id") or placement.ensure_field(root, plan["names"])
                if "crs" in plan and plan["crs"].isValid():
                    layer.setCrs(plan["crs"])
                record, saved, created = managed_data.save_dataset(root, layer, field_id, plan["role"], feedback, review=plan["review"])
                existing_saved = next((candidate for candidate in project.mapLayers().values()
                    if candidate.customProperty("AgTechTooling/dataset_id") == record["id"]), None)
                if existing_saved and not created:
                    skipped += 1
                    row.setCheckState(0, Qt.Unchecked)
                    row.setText(3, "Already saved")
                    continue
                saved = existing_saved or saved
                placement.place_layer(root, saved, field_id, plan["role"], project)
                if layer.id() in project.mapLayers() and layer.id() != saved.id():
                    project.removeMapLayer(layer.id())
            except Exception as error:
                failed.append(layer.name())
                row.setText(3, str(error))
                continue
            added.append(saved)
            added_fields.add(field_id)
            node = project.layerTreeRoot().findLayer(saved.id())
            if node is not None:
                node.setItemVisibilityCheckedParentRecursive(True)
            row.setCheckState(0, Qt.Unchecked)
            names = placement.field_path(root, field_id)
            row.setText(2, " / ".join(names[kind] for kind in placement.KINDS))
            row.setText(3, "Saved")
        # Native close emits canceled too: cleanup must not cancel completed work.
        # A real Stop has already reached feedback during the writer/event loop.
        progress.canceled.disconnect(feedback.cancel)
        progress.close()
        progress.deleteLater()
        self.load_field_options()
        for row in self.rows():
            self.populate_selector(row)
        if added:
            shown_field = next(iter(added_fields)) if len(added_fields) == 1 else "*"
            managed_data.apply_filters(root, shown_field, "*", project)
            if hasattr(self.iface, "layerTreeView"):
                view = self.iface.layerTreeView()
                if shown_field == "*":
                    view.setCurrentIndex(QModelIndex())
                else:
                    _, nodes = placement.sync_tree(root, project)
                    view.setCurrentNode(nodes[shown_field])
            from .map_presentation import zoom_layers
            zoom_layers(self.iface, added)
            if not hasattr(self.iface.mapCanvas(), "mapSettings"):
                self.iface.mapCanvas().refresh()
                self.iface.mapCanvas().zoomToFullExtent()
        saved_map = self.save_map(project) if added else True
        self.status.setText(f"{len(added)} datasets saved. {skipped} already saved. {len(failed)} could not import. "
                            + ("Map saved." if added and saved_map else "Save Map to keep this view."))
        if added and not saved_map:
            self.status.setText(self.status.text() + " Data is saved; the map could not be written. Reopen the workspace to recover it.")
        if feedback.isCanceled():
            self.status.setText("Import stopped. " + self.status.text())
        self.update_add()

    def save_map(self, project):
        """Use desktop Save Map so its external-change tracking stays current."""
        if not hasattr(self.iface, "actionSaveProject"):
            # API-only test/embedding adapters have no native desktop save action.
            return project.write()
        saved = []
        def on_saved():
            saved.append(True)
        project.projectSaved.connect(on_saved)
        try:
            self.iface.actionSaveProject().trigger()
        finally:
            project.projectSaved.disconnect(on_saved)
        # A cancelled warning or failed write must not be reported as saved.
        return bool(saved)

    def done(self, result):
        self.edit_destination(None)
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
        if self.dialog.editor is None:
            self.dialog.edit_destination(self.dialog.tree.currentItem())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def close(self):
        if self.dialog is not None:
            self.dialog.reject()
            self.dialog.deleteLater()
            self.dialog = None
