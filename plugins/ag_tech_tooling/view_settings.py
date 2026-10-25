# SPDX-License-Identifier: GPL-2.0-or-later
from .branding import brand_dialog
"""Starting preferences with explicit per-map and future-project overrides."""
from qgis.core import QgsProject, QgsSettings
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QCheckBox,
    QComboBox, QLabel, QDialogButtonBox)
from .ui_icons import icon, decorate_buttons

DEFAULTS = dict(focus=True, zoom=True, labels=True, styling=True, background="osm")
LABELS = dict(focus="Open single-choice farm paths without closing other branches", zoom="Zoom when selecting a field or dataset",
              labels="Start imported data with short, readable names", styling="Start plain data with readable map symbols")


def preference(key, project=None):
    project = project or QgsProject.instance()
    default = DEFAULTS[key]
    fallback = QgsSettings().value("AgTechTooling/view/" + key, default, type=type(default))
    if isinstance(default, bool):
        return project.readBoolEntry("AgTechTooling", "view/" + key, fallback)[0]
    return project.readEntry("AgTechTooling", "view/" + key, fallback)[0]


def initialise(project):
    for key in DEFAULTS:
        project.writeEntry("AgTechTooling", "view/" + key, preference(key, project))


class ViewSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map & Browser Settings")
        brand_dialog(self)
        layout = QVBoxLayout(self)
        note = QLabel("Choose how this map opens. Existing names and custom styles stay editable. Background maps need internet access.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.controls = {}
        for key, label in LABELS.items():
            control = QCheckBox(label)
            control.setChecked(preference(key))
            control.setIcon(icon("field" if key in {"focus", "zoom"} else "edit"))
            layout.addWidget(control)
            self.controls[key] = control
        form = QFormLayout()
        self.background = QComboBox()
        from .background_maps import PROVIDERS
        for key, specification in PROVIDERS.items():
            self.background.addItem(icon("background" if key == "osm" else "terrain"), specification["name"], key)
            self.background.setItemData(self.background.count() - 1, specification["description"], Qt.ToolTipRole)
        self.background.addItem(icon("cancel"), "No automatic background — use my own layers", "none")
        self.background.setCurrentIndex(max(0, self.background.findData(preference("background"))))
        form.addRow("Background", self.background)
        layout.addLayout(form)
        self.future = QCheckBox("Also use these defaults for new projects")
        layout.addWidget(self.future)
        note = QLabel('Switch backgrounds with the checkboxes under Background on the left. Esri World Imagery provides aerial/satellite imagery with varying detail and dates; Esri terms apply. The 10–30 m composites are overview imagery. Online services receive requests for visible map tiles; no bulk/offline imagery download is provided. Google imagery needs separate API access.')
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        decorate_buttons(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        values = {key: control.isChecked() for key, control in self.controls.items()}
        values["background"] = self.background.currentData()
        for key, value in values.items():
            QgsProject.instance().writeEntry("AgTechTooling", "view/" + key, value)
            if self.future.isChecked():
                QgsSettings().setValue("AgTechTooling/view/" + key, value)
        QgsSettings().sync()
        super().accept()
